from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AppSettingsResponse, AppSettingsUpdate
from app.services.settings_store import get_all_settings, update_settings

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=AppSettingsResponse)
def read_settings(db: Session = Depends(get_db)):
    return AppSettingsResponse(**get_all_settings(db))


@router.patch("", response_model=AppSettingsResponse)
def patch_settings(payload: AppSettingsUpdate, db: Session = Depends(get_db)):
    data = payload.model_dump(exclude_none=True)
    return AppSettingsResponse(**update_settings(db, data))
