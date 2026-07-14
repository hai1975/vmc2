from sqlalchemy.orm import Session

from app.database import AppSetting

from app.services.pharmacy_suggestions import default_pharmacy_list_json

SETTING_KEYS = (
    "email_enabled",
    "email_to",
    "smtp_host",
    "smtp_port",
    "smtp_user",
    "smtp_password",
    "smtp_from",
    "pediatric_age_threshold",
    "pharmacy_list",
    "voice_gender",
)

DEFAULTS: dict[str, str] = {
    "email_enabled": "false",
    "email_to": "",
    "smtp_host": "",
    "smtp_port": "587",
    "smtp_user": "",
    "smtp_password": "",
    "smtp_from": "",
    "pediatric_age_threshold": "18",
    "pharmacy_list": default_pharmacy_list_json(),
    "voice_gender": "female",
}


def get_all_settings(db: Session) -> dict[str, str]:
    rows = db.query(AppSetting).all()
    stored = {row.key: row.value for row in rows}
    merged = {**DEFAULTS, **stored}
    if merged.get("smtp_password"):
        merged["smtp_password"] = "***"
    return merged


def update_settings(db: Session, payload: dict[str, str]) -> dict[str, str]:
    for key, value in payload.items():
        if key not in SETTING_KEYS:
            continue
        if key == "smtp_password" and (not value or value == "***"):
            continue
        row = db.get(AppSetting, key)
        if row:
            row.value = value
        else:
            db.add(AppSetting(key=key, value=value))
    db.commit()
    return get_all_settings(db)


def seed_missing_settings(db: Session) -> None:
    """Persist code defaults for keys not yet in DB — shared by all users via API."""
    changed = False
    for key, value in DEFAULTS.items():
        if db.get(AppSetting, key) is None:
            db.add(AppSetting(key=key, value=value))
            changed = True
    if changed:
        db.commit()
