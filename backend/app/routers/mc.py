from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, HTTPException
from google import genai
from google.genai import errors as genai_errors
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/mc", tags=["mc"])

Lang = Literal["vi", "en", "nl"]
Gender = Literal["female", "male"]

# BCP-47 — only used on cascaded (non-native-audio) Live models
_LANG_CODE: dict[str, str] = {
    "vi": "vi-VN",
    "en": "en-US",
    "nl": "nl-NL",
}

# Gemini has 30 style-based voices (NOT nationality-based). No "Dutch native" voice exists.
# Best NL pairing: calm/clear voices + Director's Notes accent steering + nl-NL model path.
_VOICE_MAP: dict[str, dict[str, str]] = {
    "vi": {"female": "Aoede", "male": "Fenrir"},
    "en": {"female": "Aoede", "male": "Fenrir"},
    "nl": {"female": "Despina", "male": "Iapetus"},
}

# Native-audio models ignore language_code; accent comes from system instructions.
_NATIVE_AUDIO_MARKERS = (
    "native-audio",
    "flash-live-preview",
    "flash-live",
    "3.1-flash-live",
)

_NL_DIRECTOR_NOTES = (
    "DIRECTOR'S NOTES (Audio Performance):\n"
    "- Accent: Standaard Nederlands (Nederland), zoals een professionele presentator op NPO Radio "
    "in Hilversum — NIET Vlaams/Belgisch, NIET Duits of Engels accent.\n"
    "- Tempo: Langzaam, stabiel, warm. Geen op-en-neer zang-achtige intonatie.\n"
    "- Taal: 100% Nederlands (nl-NL). Alleen Nederlandse woorden en natuurlijke zinsbouw.\n"
    "- Persona: Vriendelijke Nederlandse MC voor een pianorecital met gezinnen en kinderen."
)

_LANG_LOCK: dict[str, str] = {
    "vi": "BẮT BUỘC trả lời bằng tiếng Việt chuẩn Việt Nam. PHẢI nói tiếng Việt tự nhiên, rõ ràng.",
    "en": "RESPOND IN English (US). YOU MUST RESPOND UNMISTAKABLY IN English.",
    "nl": (
        "ANTWOORD IN het Nederlands (Nederland). JE MOET ONMISKENBAAR IN HET NEDERLANDS (nl-NL) SPREKEN. "
        "Gebruik standaard Nederlandse uitspraak en intonatie zoals een Nederlandse presentator op radio/TV. "
        "Geen Vlaams, geen Belgisch-Nederlands, geen Engels of Duits accent. "
        "Gebruik natuurlijke Nederlandse woordvolgorde en gangbare Nederlandse uitdrukkingen.\n\n"
        f"{_NL_DIRECTOR_NOTES}"
    ),
}

_SYSTEM_INTRO: dict[str, dict[str, str]] = {
    "vi": {
        "female": (
            "Bạn là MC nữ vui tươi, hào hứng cho buổi Piano Recital của Maria Le Piano Studio. "
            "Giọng điệu ấm áp, truyền cảm hứng, năng lượng cao. "
            "Khi nhận tín hiệu, giới thiệu tiết mục ngay bằng tiếng Việt — sinh động, hào hứng, "
            "kể điều thú vị về tác phẩm nếu có, kết bằng lời mời vỗ tay nồng nhiệt."
        ),
        "male": (
            "Bạn là MC nam năng động, cuốn hút cho buổi Piano Recital của Maria Le Piano Studio. "
            "Giọng điệu mạnh mẽ, đầy năng lượng và cảm hứng. "
            "Khi nhận tín hiệu, giới thiệu tiết mục ngay bằng tiếng Việt — hào hứng, "
            "kể điều thú vị về tác phẩm nếu có, kết bằng lời mời vỗ tay nồng nhiệt."
        ),
    },
    "en": {
        "female": (
            "You are a cheerful, warm female MC for the Piano Recital of Maria Le Piano Studio. "
            "Upbeat, captivating, high-energy. On signal, introduce the piece immediately in English — "
            "vivid language, share a fascinating fact if possible, end with enthusiastic applause invitation."
        ),
        "male": (
            "You are an energetic, dynamic male MC for the Piano Recital of Maria Le Piano Studio. "
            "Bold, inspiring, high-energy. On signal, introduce the piece immediately in English — "
            "vivid language, share a fascinating fact if possible, end with enthusiastic applause invitation."
        ),
    },
    "nl": {
        "female": (
            "Je bent een vrolijke, warme vrouwelijke MC voor het Piano Recital van Maria Le Piano Studio. "
            "Enthousiast, meeslepend, vol energie. Op het signaal, introduceer het stuk onmiddellijk in het Nederlands — "
            "levendig taalgebruik, deel een interessant weetje indien mogelijk, sluit af met warm applaus-uitnodiging. "
            "Spreek langzaam en duidelijk. Gebruik eenvoudige woorden die kinderen begrijpen. "
            "Noem de naam van de uitvoerder twee keer. Vermijd een op-en-neer tempo."
        ),
        "male": (
            "Je bent een energieke, dynamische mannelijke MC voor het Piano Recital van Maria Le Piano Studio. "
            "Krachtig, inspirerend, vol energie. Op het signaal, introduceer het stuk onmiddellijk in het Nederlands — "
            "levendig taalgebruik, deel een interessant weetje indien mogelijk, sluit af met warm applaus-uitnodiging. "
            "Spreek langzaam en duidelijk. Gebruik eenvoudige woorden die kinderen begrijpen. "
            "Noem de naam van de uitvoerder twee keer. Vermijd een op-en-neer tempo."
        ),
    },
}

_OPENING: dict[str, str] = {
    "vi": "Giới thiệu NGAY tiết mục #{number}: {performer} trình bày \"{piece}\". {duet}Hãy thật vui tươi và hào hứng!{custom}",
    "en": "Introduce NOW piece #{number}: {performer} performs \"{piece}\". {duet}Be enthusiastic and captivating!{custom}",
    "nl": (
        "Begin DIRECT in het Nederlands. Introduceer NU stuk #{number}: {performer} speelt \"{piece}\". "
        "{duet}Wees enthousiast en meeslepend!{custom}"
    ),
}

_DUET: dict[str, str] = {
    "vi": "Đặc biệt đây là SONG TẤU — hai tài năng cùng biểu diễn! ",
    "en": "Extra exciting — this is a DUET, two performers together! ",
    "nl": "Extra spannend — dit is een DUET, twee uitvoerders samen! ",
}


def _is_native_audio_model(model: str) -> bool:
    name = model.lower()
    return any(marker in name for marker in _NATIVE_AUDIO_MARKERS)


def _resolve_model(lang: Lang) -> str:
    if lang == "nl" and settings.gemini_live_model_nl.strip():
        return settings.gemini_live_model_nl.strip()
    return settings.gemini_live_model


def _build_speech_config(lang: Lang, gender: Gender, model: str) -> dict:
    voice = _VOICE_MAP[lang][gender]
    speech_config: dict = {
        "voice_config": {"prebuilt_voice_config": {"voice_name": voice}},
    }
    # Native-audio models auto-detect language; language_code can error or be ignored.
    if not _is_native_audio_model(model):
        speech_config["language_code"] = _LANG_CODE[lang]
    return speech_config


class LiveTokenRequest(BaseModel):
    number: int
    performer: str
    piece: str
    is_duet: bool = False
    lang: Lang = "en"
    gender: Gender = "female"
    custom_instructions: str = ""


class LiveTokenResponse(BaseModel):
    token: str
    model: str
    opening_prompt: str


@router.post("/live-token", response_model=LiveTokenResponse)
async def mc_live_token(req: LiveTokenRequest) -> LiveTokenResponse:
    if not settings.gemini_api_key:
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY chưa cấu hình")

    model = _resolve_model(req.lang)
    system_instruction = f"{_LANG_LOCK[req.lang]}\n\n{_SYSTEM_INTRO[req.lang][req.gender]}"
    duet = _DUET.get(req.lang, "") if req.is_duet else ""
    custom = f" Extra: {req.custom_instructions.strip()}" if req.custom_instructions.strip() else ""
    opening_prompt = _OPENING[req.lang].format(
        number=req.number, performer=req.performer, piece=req.piece,
        duet=duet, custom=custom,
    )

    live_config = {
        "response_modalities": ["AUDIO"],
        "system_instruction": system_instruction,
        "speech_config": _build_speech_config(req.lang, req.gender, model),
        "input_audio_transcription": {},
        "output_audio_transcription": {},
    }

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
