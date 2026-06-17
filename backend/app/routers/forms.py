from fastapi import APIRouter, HTTPException

from app.models import FormSchema, FormSummary
from app.services.form_registry import get_schema_or_raise, list_pdf_forms, load_schema

router = APIRouter(prefix="/forms", tags=["forms"])


@router.get("", response_model=list[FormSummary])
def get_forms():
    return list_pdf_forms()


@router.get("/{form_id}/schema", response_model=FormSchema)
def get_form_schema(form_id: str):
    try:
        return get_schema_or_raise(form_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{form_id}/exists")
def form_exists(form_id: str):
    schema = load_schema(form_id)
    return {"exists": schema is not None, "form_id": form_id}
