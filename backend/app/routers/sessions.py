import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import FormSession, SessionStatus, dumps_answers, get_db, loads_answers
from app.models import (
    DocumentScanRequest,
    DocumentScanResponse,
    EmailSendResponse,
    FormProgressResponse,
    LiveTokenResponse,
    ProviderLookupRequest,
    ProviderLookupResponse,
    SelectFormRequest,
    SelectFormResponse,
    SessionCreate,
    SessionResponse,
    SessionUpdateAnswers,
    VoiceConfigResponse,
)
from app.services.field_prefill import apply_field_prefill
from app.services.document_scan import extract_fields_from_document_image, merge_extracted_into_answers
from app.services.email_service import send_pdf_email
from app.services.email_templates import build_pdf_email_body, build_pdf_email_subject
from app.services.form_registry import (
    build_voice_system_instruction,
    get_form_progress_with_hint,
    get_schema_or_raise,
    normalize_answers,
    preferred_voice_language,
    validate_answers,
)
from app.services.form_selector import (
    TRIAGE_FORM_ID,
    initial_answers_from_triage_dob,
    resolve_registration_form_id,
)
from app.services.gemini_live import create_live_ephemeral_token
from app.services.n8n_email import send_pdf_via_n8n
from app.services.pdf_generator import generate_filled_pdf
from app.services.pharmacy_suggestions import parse_pharmacy_list
from app.services.provider_lookup import lookup_provider_facility
from app.services.settings_store import get_all_settings
from app.services.triage_voice import build_triage_system_instruction

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _pharmacy_list_from_settings(db: Session):
    cfg = get_all_settings(db)
    return parse_pharmacy_list(cfg.get("pharmacy_list"))


def _to_response(
    row: FormSession,
    email_sent: bool | None = None,
    email_error: str | None = None,
) -> SessionResponse:
    pdf_url = None
    if row.filled_pdf_path:
        pdf_url = f"/api/sessions/{row.id}/pdf"
    return SessionResponse(
        id=row.id,
        form_id=row.form_id,
        status=row.status,
        language=row.language,
        answers=loads_answers(row.answers_json),
        filled_pdf_url=pdf_url,
        created_at=row.created_at.isoformat(),
        updated_at=row.updated_at.isoformat(),
        submitted_at=row.submitted_at.isoformat() if row.submitted_at else None,
        email_sent=email_sent,
        email_error=email_error,
    )


@router.post("", response_model=SessionResponse)
def create_session(payload: SessionCreate, db: Session = Depends(get_db)):
    try:
        get_schema_or_raise(payload.form_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    row = FormSession(
        id=str(uuid.uuid4()),
        form_id=payload.form_id,
        language=payload.language,
        answers_json="{}",
        status=SessionStatus.DRAFT.value,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_response(row)


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: str, db: Session = Depends(get_db)):
    row = db.get(FormSession, session_id)
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    return _to_response(row)


@router.patch("/{session_id}/answers", response_model=SessionResponse)
def update_answers(
    session_id: str,
    payload: SessionUpdateAnswers,
    db: Session = Depends(get_db),
):
    row = db.get(FormSession, session_id)
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")

    current = loads_answers(row.answers_json)
    if payload.merge:
        current.update(payload.answers)
    else:
        current = payload.answers

    schema = get_schema_or_raise(row.form_id)
    current = apply_field_prefill(current, row.form_id)
    current = normalize_answers(schema, current)

    row.answers_json = dumps_answers(current)
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return _to_response(row)


@router.post("/{session_id}/scan-document", response_model=DocumentScanResponse)
def scan_document(
    session_id: str,
    payload: DocumentScanRequest,
    db: Session = Depends(get_db),
):
    row = db.get(FormSession, session_id)
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")

    schema = get_schema_or_raise(row.form_id)
    result = extract_fields_from_document_image(
        schema,
        payload.image,
        doc_type=payload.doc_type,
        language=row.language,
    )
    extracted = result["extracted_fields"]
    session_response: SessionResponse | None = None

    if payload.merge and extracted:
        current = loads_answers(row.answers_json)
        merged = merge_extracted_into_answers(schema, current, extracted)
        merged = apply_field_prefill(merged, row.form_id)
        merged = normalize_answers(schema, merged)
        row.answers_json = dumps_answers(merged)
        row.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(row)
        session_response = _to_response(row)

    return DocumentScanResponse(
        detected_document=str(result["detected_document"]),
        extracted_fields=extracted,
        applied_fields=extracted if payload.merge else {},
        filled_count=len(extracted),
        session=session_response,
    )


@router.post("/{session_id}/save", response_model=SessionResponse)
def save_session(session_id: str, db: Session = Depends(get_db)):
    row = db.get(FormSession, session_id)
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")

    row.status = SessionStatus.DRAFT.value
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return _to_response(row)


@router.post("/{session_id}/submit", response_model=SessionResponse)
def submit_session(session_id: str, db: Session = Depends(get_db)):
    row = db.get(FormSession, session_id)
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    if row.form_id == TRIAGE_FORM_ID:
        raise HTTPException(status_code=400, detail="Complete date-of-birth triage before submitting")

    schema = get_schema_or_raise(row.form_id)
    answers = apply_field_prefill(loads_answers(row.answers_json), row.form_id)
    errors = validate_answers(schema, answers)
    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})

    pdf_path = generate_filled_pdf(row.form_id, schema, answers, row.id, row.language)
    row.filled_pdf_path = str(pdf_path)
    row.status = SessionStatus.SUBMITTED.value
    row.submitted_at = datetime.now(timezone.utc)
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)

    email_sent: bool | None = None
    email_error: str | None = None
    try:
        if send_pdf_email(db, pdf_path, row.form_id, row.id):
            email_sent = True
    except ValueError as exc:
        email_sent = False
        email_error = str(exc)
    except Exception as exc:
        email_sent = False
        email_error = str(exc)

    return _to_response(row, email_sent=email_sent, email_error=email_error)


@router.get("/{session_id}/pdf")
def download_pdf(session_id: str, db: Session = Depends(get_db)):
    row = db.get(FormSession, session_id)
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")

    schema = get_schema_or_raise(row.form_id)
    answers = apply_field_prefill(loads_answers(row.answers_json), row.form_id)

    path = settings.output_pdf_dir / f"{session_id}_{row.form_id}.pdf"
    try:
        pdf_path = generate_filled_pdf(row.form_id, schema, answers, row.id, row.language)
        row.filled_pdf_path = str(pdf_path)
        row.updated_at = datetime.now(timezone.utc)
        db.commit()
        path = pdf_path
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if not path.exists():
        raise HTTPException(status_code=404, detail="PDF file missing on disk")

    return FileResponse(
        path,
        media_type="application/pdf",
        filename=f"{row.form_id}_{session_id}.pdf",
    )


@router.post("/{session_id}/send-email", response_model=EmailSendResponse)
def send_session_email(session_id: str, db: Session = Depends(get_db)):
    row = db.get(FormSession, session_id)
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")

    cfg = get_all_settings(db)
    to_addr = (cfg.get("email_to") or "").strip()
    if not to_addr:
        raise HTTPException(
            status_code=400,
            detail="Recipient email is empty. Open Settings and enter the recipient email.",
        )

    schema = get_schema_or_raise(row.form_id)
    answers = apply_field_prefill(loads_answers(row.answers_json), row.form_id)

    try:
        pdf_path = generate_filled_pdf(row.form_id, schema, answers, row.id, row.language)
        row.filled_pdf_path = str(pdf_path)
        row.updated_at = datetime.now(timezone.utc)
        db.commit()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    subject = build_pdf_email_subject(schema, row.language, answers)
    body = build_pdf_email_body(schema, row.id, row.language, answers)
    send_pdf_via_n8n(to_addr, subject, body, pdf_path)

    return EmailSendResponse(ok=True, to=to_addr, subject=subject, message=body)


@router.post("/{session_id}/select-form", response_model=SelectFormResponse)
def select_registration_form(
    session_id: str,
    payload: SelectFormRequest,
    db: Session = Depends(get_db),
):
    row = db.get(FormSession, session_id)
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    if row.form_id != TRIAGE_FORM_ID:
        raise HTTPException(status_code=400, detail="Form already selected for this session")

    cfg = get_all_settings(db)
    try:
        threshold = int(cfg.get("pediatric_age_threshold") or "18")
    except ValueError as exc:
        raise HTTPException(status_code=500, detail="Invalid pediatric_age_threshold setting") from exc

    try:
        form_id, normalized_dob, age, is_pediatric = resolve_registration_form_id(
            payload.dob,
            payload.voice_language,
            threshold,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    schema = get_schema_or_raise(form_id)
    answers = apply_field_prefill(
        normalize_answers(schema, initial_answers_from_triage_dob(schema, normalized_dob)),
        form_id,
    )
    voice_lang = preferred_voice_language(form_id, payload.voice_language)

    row.form_id = form_id
    row.language = voice_lang
    row.answers_json = dumps_answers(answers)
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)

    return SelectFormResponse(
        form_id=form_id,
        patient_age=age,
        is_pediatric=is_pediatric,
        session=_to_response(row),
    )


@router.get("/{session_id}/form-progress", response_model=FormProgressResponse)
def get_session_form_progress(
    session_id: str,
    saved_field: str | None = Query(default=None, alias="saved_field"),
    db: Session = Depends(get_db),
):
    row = db.get(FormSession, session_id)
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")

    schema = get_schema_or_raise(row.form_id)
    answers = loads_answers(row.answers_json)
    voice_lang = preferred_voice_language(row.form_id, row.language)
    pharmacies = _pharmacy_list_from_settings(db)
    progress = get_form_progress_with_hint(
        schema, answers, saved_field, voice_lang, pharmacies
    )
    return FormProgressResponse(**progress)


@router.post("/{session_id}/lookup-provider", response_model=ProviderLookupResponse)
def lookup_provider(
    session_id: str,
    payload: ProviderLookupRequest,
    db: Session = Depends(get_db),
):
    row = db.get(FormSession, session_id)
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    if row.form_id == TRIAGE_FORM_ID:
        raise HTTPException(status_code=400, detail="Complete form selection before provider lookup")

    result = lookup_provider_facility(payload.query)
    candidates: list[dict[str, str]] = []
    if result.get("name"):
        candidates.append({
            "name": result["name"],
            "address": result.get("address", ""),
            "phone": result.get("phone", ""),
            "fax": result.get("fax", ""),
            "confidence": result.get("confidence", "low"),
        })
    message = result.get("note") or (
        "Could not verify a match — ask the patient for more detail."
        if not candidates
        else "Read this match to the patient and confirm before saving provider_facility_name."
    )
    return ProviderLookupResponse(query=payload.query, candidates=candidates, message=message)


@router.get("/{session_id}/voice-config", response_model=VoiceConfigResponse)
def get_voice_config(session_id: str, db: Session = Depends(get_db)):
    row = db.get(FormSession, session_id)
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")

    schema = get_schema_or_raise(row.form_id)
    answers = loads_answers(row.answers_json)
    voice_lang = preferred_voice_language(row.form_id, row.language)

    if row.form_id == TRIAGE_FORM_ID:
        cfg = get_all_settings(db)
        try:
            threshold = int(cfg.get("pediatric_age_threshold") or "18")
        except ValueError:
            threshold = 18
        system_instruction = build_triage_system_instruction(threshold)
    else:
        pharmacies = _pharmacy_list_from_settings(db)
        system_instruction = build_voice_system_instruction(
            schema, voice_lang, answers, pharmacies
        )

    return VoiceConfigResponse(
        form_id=row.form_id,
        system_instruction=system_instruction,
        fields=schema.fields,
        gemini_model=settings.gemini_live_model,
    )


@router.post("/{session_id}/live-token", response_model=LiveTokenResponse)
def create_live_token(session_id: str, db: Session = Depends(get_db)):
    row = db.get(FormSession, session_id)
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")

    schema = get_schema_or_raise(row.form_id)
    answers = loads_answers(row.answers_json)
    voice_lang = preferred_voice_language(row.form_id, row.language)

    if row.form_id == TRIAGE_FORM_ID:
        cfg = get_all_settings(db)
        try:
            threshold = int(cfg.get("pediatric_age_threshold") or "18")
        except ValueError:
            threshold = 18
        system_instruction = build_triage_system_instruction(threshold)
    else:
        pharmacies = _pharmacy_list_from_settings(db)
        system_instruction = build_voice_system_instruction(
            schema, voice_lang, answers, pharmacies
        )

    return create_live_ephemeral_token(
        system_instruction,
        include_form_selection=row.form_id == TRIAGE_FORM_ID,
    )
