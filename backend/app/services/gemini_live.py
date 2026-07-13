from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.config import settings


def _build_form_tool(include_form_selection: bool = False) -> types.Tool:
    declarations = [
        types.FunctionDeclaration(
            name="update_form_field",
                description=(
                    "Persist one form field from the patient's spoken answer. "
                    "Save immediately when clear — NEVER confirm per field. "
                    "TOOL-FIRST: call this function SILENTLY before speaking. "
                    "After saving, speak say_next naturally — vary brief acks or skip ack, then next question. "
                    "then the next question. NEVER ask is that correct per field. "
                    "Only confirm once at the end when all_fields_collected is true. "
                    "Use exact field_id from schema. Encode value as JSON string "
                    '(e.g. "John", true, ["asian"], "medi_cal"). '
                    "For insurance use field_id=insurance with value uninsured|medi_cal|ppo|hmo. "
                    "For optional fields declined/none/không có, use value __skipped__. "
                    "For optional fields that should stay empty on the PDF, use __blank__. "
                    "The response includes say_next, voice_instruction, next_field_id, filled_count."
                ),
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "field_id": types.Schema(
                            type=types.Type.STRING,
                            description="Schema field id",
                        ),
                        "value": types.Schema(
                            type=types.Type.STRING,
                            description="JSON-encoded field value",
                        ),
                    },
                    required=["field_id", "value"],
                ),
            ),
            types.FunctionDeclaration(
                name="scan_document_fields",
                description=(
                    "Read ID, passport, driver license, or insurance card from the LIVE webcam "
                    "and save all visible form fields at once. Call when the patient shows a document "
                    "on camera or asks you to look at their ID/insurance. "
                    "Use exact field_id keys and allowed_values from schema. Omit fields not visible."
                ),
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "fields_json": types.Schema(
                            type=types.Type.STRING,
                            description=(
                                'JSON object mapping field_id to value, e.g. '
                                '{"patient_name":"Maria Garcia","dob":"1990-05-12","insurance":"medi_cal"}'
                            ),
                        ),
                    },
                    required=["fields_json"],
                ),
            ),
            types.FunctionDeclaration(
                name="lookup_provider_facility",
                description=(
                    "Search for a doctor or clinic when the patient gives a partial name or address "
                    "for provider_facility_name on the records release authorization section. "
                    "Returns name, address, phone, fax candidates. Read results to the patient and "
                    "confirm before saving with update_form_field."
                ),
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "query": types.Schema(
                            type=types.Type.STRING,
                            description="Partial doctor/clinic name, city, or address to search",
                        ),
                    },
                    required=["query"],
                ),
            ),
        ]

    if include_form_selection:
        declarations.append(
            types.FunctionDeclaration(
                name="select_registration_form",
                description=(
                    "TRIAGE ONLY: call once you have the patient's date of birth and detected language. "
                    "Selects pediatric vs adult and Vietnamese vs English PDF form. "
                    "voice_language must be 'vi' if patient speaks Vietnamese, 'en' for any other language."
                ),
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "dob": types.Schema(
                            type=types.Type.STRING,
                            description="Date of birth (MM/DD/YYYY or YYYY-MM-DD)",
                        ),
                        "voice_language": types.Schema(
                            type=types.Type.STRING,
                            description="vi if patient speaks Vietnamese, en otherwise",
                        ),
                    },
                    required=["dob", "voice_language"],
                ),
            )
        )

    return types.Tool(function_declarations=declarations)


def create_live_ephemeral_token(
    system_instruction: str,
    include_form_selection: bool = False,
) -> dict:
    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY is not configured on the server",
        )

    now = datetime.now(timezone.utc)
    model = settings.gemini_live_model

    live_config = {
        "response_modalities": ["AUDIO"],
        "system_instruction": system_instruction,
        "thinking_config": {"thinking_level": "MINIMAL"},
        "media_resolution": types.MediaResolution.MEDIA_RESOLUTION_MEDIUM,
        "speech_config": {
            "voice_config": {
                "prebuilt_voice_config": {"voice_name": "Aoede"},
            }
        },
        "tools": [_build_form_tool(include_form_selection)],
        "input_audio_transcription": {},
        "output_audio_transcription": {},
    }

    client = genai.Client(
        api_key=settings.gemini_api_key,
        http_options={"api_version": "v1alpha"},
    )

    try:
        token = client.auth_tokens.create(
            config={
                "uses": 1,
                "expire_time": (now + timedelta(minutes=30)).isoformat(),
                "new_session_expire_time": (now + timedelta(minutes=2)).isoformat(),
                "live_connect_constraints": {
                    "model": model,
                    "config": live_config,
                },
                "http_options": {"api_version": "v1alpha"},
            }
        )
    except genai_errors.ClientError as exc:
        message = str(exc)
        if "suspended" in message.lower():
            detail = "Gemini API key bị suspend. Tạo key mới tại https://aistudio.google.com/apikey"
        elif "PERMISSION_DENIED" in message:
            detail = "Gemini API key không có quyền. Kiểm tra key và bật Generative Language API."
        else:
            detail = f"Gemini API error: {message}"
        raise HTTPException(status_code=502, detail=detail) from exc

    return {
        "token": token.name,
        "model": model,
        "expires_at": (now + timedelta(minutes=30)).isoformat(),
    }
