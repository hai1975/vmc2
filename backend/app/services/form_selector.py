from datetime import date, datetime

from fastapi import HTTPException

from app.models import FormSchema

ACTIVE_FORM_IDS = frozenset({"adult_en", "adult_vn", "child_en", "child_vn"})
TRIAGE_FORM_ID = "triage"

FORM_FILENAME_BY_ID = {
    "adult_en": "adult_en.pdf",
    "adult_vn": "adult_vn.pdf",
    "child_en": "Child_en.pdf",
    "child_vn": "Child_vn.pdf",
}


def parse_date_of_birth(value: str) -> date:
    text = str(value).strip()
    if not text:
        raise ValueError("Date of birth is required")

    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    raise ValueError(f"Cannot parse date of birth: {value}")


def calculate_age(dob: date, today: date | None = None) -> int:
    ref = today or date.today()
    age = ref.year - dob.year
    if (ref.month, ref.day) < (dob.month, dob.day):
        age -= 1
    return age


def normalize_voice_language(value: str) -> str:
    lang = str(value or "").strip().lower()
    return "vi" if lang.startswith("vi") else "en"


def dob_field_id_for_schema(schema: FormSchema) -> str:
    """Registration forms use `birthday`; triage schema uses `dob`."""
    field_ids = {field.id for field in schema.fields}
    if "birthday" in field_ids:
        return "birthday"
    if "dob" in field_ids:
        return "dob"
    raise HTTPException(status_code=500, detail="Schema has no date-of-birth field")


def initial_answers_from_triage_dob(schema: FormSchema, normalized_dob: str) -> dict:
    return {dob_field_id_for_schema(schema): normalized_dob}


def resolve_registration_form_id(
    dob: str,
    voice_language: str,
    pediatric_threshold: int,
) -> tuple[str, str, int, bool]:
    parsed = parse_date_of_birth(dob)
    age = calculate_age(parsed)
    is_pediatric = age < pediatric_threshold
    lang = normalize_voice_language(voice_language)

    if is_pediatric and lang == "vi":
        form_id = "child_vn"
    elif is_pediatric:
        form_id = "child_en"
    elif lang == "vi":
        form_id = "adult_vn"
    else:
        form_id = "adult_en"

    if form_id not in ACTIVE_FORM_IDS:
        raise HTTPException(status_code=500, detail=f"Unknown form mapping: {form_id}")

    return form_id, parsed.strftime("%m/%d/%Y"), age, is_pediatric
