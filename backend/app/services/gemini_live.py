from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.config import settings


def _build_form_tool() -> types.Tool:
    return types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="update_form_field",
                description=(
                    "Persist one form field ONLY after the patient explicitly confirmed the value. "
                    "Never call this before confirmation. "
                    "Use exact field_id from schema. Encode value as JSON string "
                    '(e.g. "John", true, ["asian"], "medi_cal"). '
                    "For insurance use field_id=insurance with value uninsured|medi_cal|ppo|hmo. "
                    "The response includes next_field_id, next_field_ask_en/vi, missing_optional, "
                    "ready_to_submit, and all_fields_collected. Always ask next_field_id next. "
                    "Keep asking optional fields even when ready_to_submit is true."
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
            )
        ]
    )


def create_live_ephemeral_token(system_instruction: str) -> dict:
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
        "speech_config": {
            "voice_config": {
                "prebuilt_voice_config": {"voice_name": "Aoede"},
            }
        },
        "tools": [_build_form_tool()],
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
