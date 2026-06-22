import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import FormSession, SessionStatus, dumps_answers, get_db, loads_answers
from app.models import (
    FormProgressResponse,
    LiveTokenResponse,
    SessionCreate,
    SessionResponse,
    SessionUpdateAnswers,
    VoiceConfigResponse,
)
from app.services.form_registry import (
    build_voice_system_instruction,
    get_form_progress,
    get_schema_or_raise,
    normalize_answers,
    validate_answers,
)
from app.services.gemini_live import create_live_ephemeral_token
from app.services.pdf_generator import generate_filled_pdf

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _to_response(row: FormSession) -> SessionResponse:
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
    current = normalize_answers(schema, current)

    row.answers_json = dumps_answers(current)
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return _to_response(row)


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

    schema = get_schema_or_raise(row.form_id)
    answers = loads_answers(row.answers_json)
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
    return _to_response(row)


@router.get("/{session_id}/pdf")
def download_pdf(session_id: str, db: Session = Depends(get_db)):
    row = db.get(FormSession, session_id)
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")

    schema = get_schema_or_raise(row.form_id)
    answers = loads_answers(row.answers_json)

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


@router.get("/{session_id}/form-progress", response_model=FormProgressResponse)
def get_session_form_progress(session_id: str, db: Session = Depends(get_db)):
    row = db.get(FormSession, session_id)
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")

    schema = get_schema_or_raise(row.form_id)
    answers = loads_answers(row.answers_json)
    progress = get_form_progress(schema, answers)
    return FormProgressResponse(**progress)


@router.get("/{session_id}/voice-config", response_model=VoiceConfigResponse)
def get_voice_config(session_id: str, db: Session = Depends(get_db)):
    row = db.get(FormSession, session_id)
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")

    schema = get_schema_or_raise(row.form_id)
    answers = loads_answers(row.answers_json)
    return VoiceConfigResponse(
        form_id=row.form_id,
        system_instruction=build_voice_system_instruction(schema, row.language, answers),
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
    system_instruction = build_voice_system_instruction(schema, row.language, answers)
    return create_live_ephemeral_token(system_instruction)
