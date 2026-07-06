from pathlib import Path

import requests
from fastapi import HTTPException

from app.config import settings


def send_pdf_via_n8n(
    to_addr: str,
    subject: str,
    message: str,
    pdf_path: Path,
) -> None:
    webhook = (settings.n8n_email_webhook_url or "").strip()
    if not webhook:
        raise HTTPException(
            status_code=503,
            detail="N8N email webhook is not configured (N8N_EMAIL_WEBHOOK_URL)",
        )

    if not to_addr:
        raise HTTPException(status_code=400, detail="Recipient email is not configured in Settings")

    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found")

    try:
        with pdf_path.open("rb") as pdf_file:
            response = requests.post(
                webhook,
                data={
                    "to": to_addr,
                    "subject": subject,
                    "message": message,
                },
                files={
                    "attachment": (pdf_path.name, pdf_file, "application/pdf"),
                },
                timeout=60,
            )
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Email webhook error: {exc}") from exc

    if response.status_code >= 400:
        detail = response.text.strip() or f"Webhook returned HTTP {response.status_code}"
        raise HTTPException(status_code=502, detail=f"Email send failed: {detail}")
