from datetime import datetime, timezone

import httpx
from fastapi import HTTPException

from app.config import settings


def azure_configured() -> bool:
    return bool(settings.azure_speech_key.strip() and settings.azure_speech_region.strip())


def azure_endpoint() -> str:
    if settings.azure_voicelive_endpoint.strip():
        return settings.azure_voicelive_endpoint.strip().rstrip("/")
    region = settings.azure_speech_region.strip()
    return f"https://{region}.api.cognitive.microsoft.com"


async def issue_speech_token_for(speech_key: str, region: str) -> tuple[str, int]:
    key = speech_key.strip()
    reg = region.strip()
    if not key or not reg:
        raise HTTPException(status_code=400, detail="speech_key và region là bắt buộc")

    url = f"https://{reg}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
    headers = {"Ocp-Apim-Subscription-Key": key}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, headers=headers)
            resp.raise_for_status()
            token = resp.text.strip()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Azure Speech token error: {exc}") from exc

    if not token:
        raise HTTPException(status_code=502, detail="Azure Speech token empty")

    # STS tokens are valid ~10 minutes
    expires_at = int(datetime.now(timezone.utc).timestamp()) + 600
    return token, expires_at


async def issue_speech_token() -> tuple[str, int]:
    if not azure_configured():
        raise HTTPException(status_code=503, detail="Azure Speech chưa cấu hình (AZURE_SPEECH_KEY, AZURE_SPEECH_REGION)")
    return await issue_speech_token_for(settings.azure_speech_key, settings.azure_speech_region)
