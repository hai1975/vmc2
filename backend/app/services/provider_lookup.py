import json
import re

from fastapi import HTTPException
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.config import settings

_LOOKUP_PROMPT = """You help find a medical provider or clinic for a patient records release form.
The user gives a partial doctor name, clinic name, city, or address in the United States.

Use Google Search to find the most likely match.
Return ONLY valid JSON (no markdown) with keys:
- name: official facility or doctor practice name
- address: full street address if found
- phone: phone number or empty string
- fax: fax number or empty string
- confidence: high|medium|low
- note: one short English sentence for the voice assistant to read to the patient

If nothing reliable is found, return name/address/phone/fax as empty strings, confidence "low",
and note explaining you could not verify a match.

Search hint: {query}
"""


def lookup_provider_facility(query: str) -> dict:
    text = (query or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Search query is required")
    if not settings.gemini_api_key:
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY is not configured")

    client = genai.Client(
        api_key=settings.gemini_api_key,
        http_options={"api_version": "v1alpha"},
    )
    model = settings.gemini_vision_model or "gemini-2.5-flash"

    try:
        response = client.models.generate_content(
            model=model,
            contents=_LOOKUP_PROMPT.format(query=text),
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.2,
            ),
        )
    except genai_errors.ClientError as exc:
        raise HTTPException(status_code=502, detail=f"Provider lookup failed: {exc}") from exc

    raw = (response.text or "").strip()
    parsed = _parse_json_object(raw)
    return {
        "query": text,
        "name": str(parsed.get("name") or "").strip(),
        "address": str(parsed.get("address") or "").strip(),
        "phone": str(parsed.get("phone") or "").strip(),
        "fax": str(parsed.get("fax") or "").strip(),
        "confidence": str(parsed.get("confidence") or "low").strip().lower(),
        "note": str(parsed.get("note") or "").strip(),
    }


def _parse_json_object(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return {}
        try:
            data = json.loads(match.group(0))
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}
