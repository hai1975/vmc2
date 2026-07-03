import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from sqlalchemy.orm import Session

from app.database import AppSetting
from app.services.settings_store import get_all_settings


def send_pdf_email(db: Session, pdf_path: Path, form_id: str, session_id: str) -> bool:
    cfg = get_all_settings(db)
    if cfg.get("email_enabled") != "true":
        return False

    to_addr = (cfg.get("email_to") or "").strip()
    host = (cfg.get("smtp_host") or "").strip()
    user = (cfg.get("smtp_user") or "").strip()
    from_addr = (cfg.get("smtp_from") or user).strip()
    if not to_addr or not host or not from_addr:
        raise ValueError("Email settings incomplete: need email_to, smtp_host, smtp_from")

    port = int(cfg.get("smtp_port") or "587")
    password_row = db.get(AppSetting, "smtp_password")
    password = password_row.value if password_row else ""

    msg = MIMEMultipart()
    msg["Subject"] = f"VM Clinic — Submitted form {form_id}"
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.attach(
        MIMEText(
            f"A patient registration form was submitted.\n\nForm: {form_id}\nSession: {session_id}\n",
            "plain",
            "utf-8",
        )
    )

    with pdf_path.open("rb") as f:
        attachment = MIMEApplication(f.read(), _subtype="pdf")
    attachment.add_header("Content-Disposition", "attachment", filename=pdf_path.name)
    msg.attach(attachment)

    with smtplib.SMTP(host, port, timeout=30) as server:
        server.starttls()
        if user and password:
            server.login(user, password)
        server.sendmail(from_addr, [to_addr], msg.as_string())
    return True
