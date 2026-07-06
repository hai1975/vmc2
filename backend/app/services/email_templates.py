from datetime import datetime, timezone

from app.models import FormSchema


def _patient_display_name(answers: dict) -> str:
    name = answers.get("patient_name")
    if name and str(name).strip():
        return str(name).strip()
    first = str(answers.get("first_name") or "").strip()
    last = str(answers.get("last_name") or "").strip()
    combined = f"{first} {last}".strip()
    return combined or "—"


def build_pdf_email_subject(schema: FormSchema, language: str, answers: dict) -> str:
    lang = language if language in ("vi", "en") else "en"
    form_title = schema.title.get(lang, schema.title.get("en", schema.id))
    patient = _patient_display_name(answers)

    if lang == "vi":
        if patient and patient != "—":
            return f"VM Clinic — Đơn đăng ký bệnh nhân: {patient}"
        return f"VM Clinic — Đơn đăng ký bệnh nhân ({form_title})"

    if patient and patient != "—":
        return f"VM Clinic — Patient Registration: {patient}"
    return f"VM Clinic — Patient Registration ({form_title})"


def build_pdf_email_body(
    schema: FormSchema,
    session_id: str,
    language: str,
    answers: dict,
) -> str:
    lang = language if language in ("vi", "en") else "en"
    form_title = schema.title.get(lang, schema.title.get("en", schema.id))
    patient = _patient_display_name(answers)
    sent_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    ref = session_id[:8]

    if lang == "vi":
        return f"""Xin chào,

Đính kèm là đơn đăng ký bệnh nhân từ VM Clinic.

Thông tin phiên:
• Biểu mẫu: {form_title}
• Bệnh nhân: {patient}
• Mã phiên: {ref}
• Thời gian: {sent_at}

Tài liệu PDF được tạo bởi hệ thống đăng ký giọng nói VM Clinic.
Vui lòng lưu trữ an toàn theo quy định bảo mật y tế (HIPAA).

Trân trọng,
VM Clinic
"""

    return f"""Hello,

Please find attached the patient registration form from VM Clinic.

Session details:
• Form: {form_title}
• Patient: {patient}
• Session ID: {ref}
• Generated: {sent_at}

This PDF was created by the VM Clinic voice registration system.
Please store it securely in accordance with healthcare privacy requirements.

Best regards,
VM Clinic
"""
