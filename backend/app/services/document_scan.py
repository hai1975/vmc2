import base64
import json
import re

from fastapi import HTTPException
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.config import settings
from app.models import FormSchema
from app.services.form_registry import normalize_answers, normalize_field_value

_DOC_HINTS = {
    "auto": "Detect document type automatically (ID, passport, driver license, insurance card, etc.).",
    "id": "National ID / state ID card.",
    "passport": "Passport.",
    "license": "Driver license.",
    "insurance": "Health insurance / Medi-Cal / insurance card.",
}


def _decode_image(data_url: str) -> tuple[bytes, str]:
    if not data_url:
        raise HTTPException(status_code=400, detail="Image is required")
    mime = "image/jpeg"
    payload = data_url
    if data_url.startswith("data:"):
        header, _, payload = data_url.partition(",")
        if ";" in header:
            mime = header.split(";")[0].replace("data:", "") or mime
    try:
        return base64.b64decode(payload), mime
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid image data") from exc


def _schema_prompt(schema: FormSchema) -> str:
    lines = ["Form fields (use exact field_id as JSON keys):"]
    for field in schema.fields:
        if field.id.startswith("_"):
            continue
        req = "required" if field.required else "optional"
        line = f"- {field.id} ({field.type}, {req})"
        if field.options:
            opts = ", ".join(o.value for o in field.options)
            line += f" allowed: [{opts}]"
        lines.append(line)
    return "\n".join(lines)


def _parse_json_object(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail="Gemini returned invalid JSON") from exc
    if not isinstance(parsed, dict):
        raise HTTPException(status_code=502, detail="Gemini response must be a JSON object")
    return parsed


def _coerce_fields(raw: dict) -> dict[str, object]:
    if "fields" in raw and isinstance(raw["fields"], dict):
        return raw["fields"]
    skip = {"detected_document", "document_type", "notes", "confidence"}
    return {k: v for k, v in raw.items() if k not in skip and not k.startswith("_")}


def extract_fields_from_document_image(
    schema: FormSchema,
    image_data_url: str,
    doc_type: str = "auto",
    language: str = "en",
) -> dict:
    if not settings.gemini_api_key:
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY is not configured")

    image_bytes, mime_type = _decode_image(image_data_url)
    doc_hint = _DOC_HINTS.get(doc_type, _DOC_HINTS["auto"])
    lang_note = (
        "Prefer Vietnamese labels if visible; still use English allowed_values for selects."
        if language.startswith("vi")
        else "Use English labels and allowed_values for selects."
    )

    prompt = f"""You are an OCR assistant for a medical clinic registration form.
The photo shows a document: {doc_hint}
{lang_note}

Extract ALL visible information that maps to the form fields below.
Return ONLY JSON (no markdown) in this shape:
{{
  "detected_document": "id|passport|license|insurance|other",
  "fields": {{
    "field_id": "value"
  }}
}}

Rules:
- Use exact field_id keys from the schema.
- For select/multiselect use exact allowed_values (e.g. medi_cal, uninsured, male).
- Dates: YYYY-MM-DD or MM/DD/YYYY.
- Phone/email/address as printed.
- Omit fields not visible — do not guess.
- Boolean fields: true/false only.

{_schema_prompt(schema)}
"""

    client = genai.Client(api_key=settings.gemini_api_key)
    model = settings.gemini_vision_model

    try:
        response = client.models.generate_content(
            model=model,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                        types.Part.from_text(text=prompt),
                    ],
                )
            ],
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )
    except genai_errors.ClientError as exc:
        raise HTTPException(status_code=502, detail=f"Gemini vision error: {exc}") from exc

    raw_text = (response.text or "").strip()
    if not raw_text:
        raise HTTPException(status_code=502, detail="Gemini returned empty response")

    parsed = _parse_json_object(raw_text)
    detected = str(parsed.get("detected_document") or parsed.get("document_type") or "unknown")
    raw_fields = _coerce_fields(parsed)

    field_map = {f.id: f for f in schema.fields}
    extracted: dict[str, object] = {}
    for field_id, value in raw_fields.items():
        field = field_map.get(field_id)
        if not field or value is None or value == "":
            continue
        cleaned = normalize_field_value(field, value)
        if cleaned is not None and cleaned != "" and cleaned != []:
            extracted[field_id] = cleaned

    return {
        "detected_document": detected,
        "extracted_fields": extracted,
        "raw_field_count": len(raw_fields),
    }


def merge_extracted_into_answers(schema: FormSchema, current: dict, extracted: dict) -> dict:
    merged = dict(current)
    merged.update(extracted)
    return normalize_answers(schema, merged)
