from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.services import azure_speech
from app.services.mc_prompts import (
    Gender,
    Lang,
    azure_locale,
    azure_voice,
    build_opening_prompt,
    build_system_instruction,
)

router = APIRouter(prefix="/mc/azure", tags=["mc-azure"])


class AzureIssueTokenRequest(BaseModel):
    speech_key: str
    region: str


class AzureIssueTokenResponse(BaseModel):
    speech_token: str
    token_expires_at: int


class AzureLiveConfigRequest(BaseModel):
    number: int
    performer: str
    piece: str
    is_duet: bool = False
    lang: Lang = "en"
    gender: Gender = "female"
    custom_instructions: str = ""


class AzureLiveConfigResponse(BaseModel):
    speech_token: str
    token_expires_at: int
    endpoint: str
    region: str
    model: str
    voice_name: str
    locale: str
    instructions: str
    opening_prompt: str


@router.get("/status")
def azure_status():
    return {
        "configured": azure_speech.azure_configured(),
        "region": settings.azure_speech_region or None,
        "model": settings.azure_voicelive_model,
    }


@router.post("/issue-token", response_model=AzureIssueTokenResponse)
async def azure_issue_token(req: AzureIssueTokenRequest) -> AzureIssueTokenResponse:
    """Mint STS token from client-supplied key (local dev — tránh CORS / api-key trên WebSocket URL)."""
    speech_token, expires_at = await azure_speech.issue_speech_token_for(req.speech_key, req.region)
    return AzureIssueTokenResponse(speech_token=speech_token, token_expires_at=expires_at)


@router.post("/live-config", response_model=AzureLiveConfigResponse)
async def azure_live_config(req: AzureLiveConfigRequest) -> AzureLiveConfigResponse:
    if not azure_speech.azure_configured():
        raise HTTPException(status_code=503, detail="Azure Speech chưa cấu hình trên server")

    speech_token, expires_at = await azure_speech.issue_speech_token()
    instructions = build_system_instruction(req.lang, req.gender)
    opening_prompt = build_opening_prompt(
        req.lang,
        number=req.number,
        performer=req.performer,
        piece=req.piece,
        is_duet=req.is_duet,
        custom_instructions=req.custom_instructions,
    )

    return AzureLiveConfigResponse(
        speech_token=speech_token,
        token_expires_at=expires_at,
        endpoint=azure_speech.azure_endpoint(),
        region=settings.azure_speech_region.strip(),
        model=settings.azure_voicelive_model,
        voice_name=azure_voice(req.lang, req.gender),
        locale=azure_locale(req.lang),
        instructions=instructions,
        opening_prompt=opening_prompt,
    )
