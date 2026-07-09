from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, HTTPException
from google import genai
from google.genai import errors as genai_errors
from pydantic import BaseModel

from app.config import settings
from app.services.mc_prompts import (
    Lang,
    Gender,
    build_opening_prompt,
    build_program2_gemini_opening_prompt,
    build_program2_gemini_system_instruction,
    build_system_instruction,
    gemini_voice,
    lang_code,
)

router = APIRouter(prefix="/mc", tags=["mc"])

# Bump when MC/Gemini script-mode behavior changes (verify via GET /api/health).
MC_API_VERSION = "2026-07-09-gemini-verbatim-v2"

_NATIVE_AUDIO_MARKERS = (
    "native-audio",
    "flash-live-preview",
    "flash-live",
    "3.1-flash-live",
)


def _is_native_audio_model(model: str) -> bool:
    name = model.lower()
    return any(marker in name for marker in _NATIVE_AUDIO_MARKERS)


def _resolve_model(lang: Lang, *, script_mode: bool = False) -> str:
    if script_mode:
        if settings.gemini_live_model_vi.strip():
            return settings.gemini_live_model_vi.strip()
        # Native-audio model follows verbatim Vietnamese scripts better than flash-live MC models.
        return "gemini-2.5-flash-native-audio-preview-12-2025"
    if lang == "nl" and settings.gemini_live_model_nl.strip():
        return settings.gemini_live_model_nl.strip()
    return settings.gemini_live_model


def _build_speech_config(lang: Lang, gender: Gender, model: str, *, force_language: bool = False) -> dict:
    voice = gemini_voice(lang, gender)
    speech_config: dict = {
        "voice_config": {"prebuilt_voice_config": {"voice_name": voice}},
    }
    if force_language or not _is_native_audio_model(model):
        speech_config["language_code"] = lang_code(lang)
    return speech_config


@router.get("/version")
def mc_version():
    return {
        "mc_api_version": MC_API_VERSION,
        "script_mode_supported": True,
        "gemini_script_model_default": "gemini-2.5-flash-native-audio-preview-12-2025",
    }
    number: int
    performer: str
    piece: str
    is_duet: bool = False
    lang: Lang = "en"
    gender: Gender = "female"
    custom_instructions: str = ""
    mc_script: str | None = None


class LiveTokenResponse(BaseModel):
    token: str
    model: str
    opening_prompt: str


@router.post("/live-token", response_model=LiveTokenResponse)
async def mc_live_token(req: LiveTokenRequest) -> LiveTokenResponse:
    if not settings.gemini_api_key:
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY chưa cấu hình")

    script_mode = bool(req.mc_script and req.mc_script.strip())
    if script_mode:
        mc_script = (req.mc_script or "").strip()
        system_instruction = build_program2_gemini_system_instruction()
        opening_prompt = build_program2_gemini_opening_prompt(mc_script)
        lang: Lang = "vi"
        gender: Gender = "female"
    else:
        system_instruction = build_system_instruction(req.lang, req.gender)
        opening_prompt = build_opening_prompt(
            req.lang,
            number=req.number,
            performer=req.performer,
            piece=req.piece,
            is_duet=req.is_duet,
            custom_instructions=req.custom_instructions,
        )
        lang = req.lang
        gender = req.gender

    model = _resolve_model(lang, script_mode=script_mode)

    live_config: dict = {
        "response_modalities": ["AUDIO"],
        "system_instruction": system_instruction,
        "speech_config": _build_speech_config(lang, gender, model, force_language=script_mode),
        "input_audio_transcription": {},
        "output_audio_transcription": {},
    }
    if script_mode:
        live_config["generation_config"] = {"temperature": 0.1, "top_p": 0.85}
        live_config["thinking_config"] = {"thinking_level": "MINIMAL"}

    client = genai.Client(api_key=settings.gemini_api_key, http_options={"api_version": "v1alpha"})
    now = datetime.now(timezone.utc)
    try:
        token = client.auth_tokens.create(config={
            "uses": 1,
            "expire_time": (now + timedelta(minutes=15)).isoformat(),
            "new_session_expire_time": (now + timedelta(minutes=2)).isoformat(),
            "live_connect_constraints": {"model": model, "config": live_config},
            "http_options": {"api_version": "v1alpha"},
        })
    except genai_errors.ClientError as exc:
        raise HTTPException(status_code=502, detail=f"Gemini error: {exc}") from exc

    return LiveTokenResponse(token=token.name, model=model, opening_prompt=opening_prompt)
