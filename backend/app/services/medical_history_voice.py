"""Ask each medical condition one at a time in the BỆNH LÝ section."""

from typing import TypedDict

SKIPPED_VALUE = "__skipped__"


class MedicalConditionPrompt(TypedDict):
    value: str
    label_en: str
    label_vi: str
    ask_en: str
    ask_vi: str


# Short prompts: disease name only — no "Have you ever..." and no "Yes or no".
MEDICAL_CONDITION_FIELDS: list[MedicalConditionPrompt] = [
    {
        "value": "diabetes",
        "label_en": "Diabetes",
        "label_vi": "Tiểu đường",
        "ask_en": "Diabetes?",
        "ask_vi": "Tiểu đường?",
    },
    {
        "value": "high_blood_pressure",
        "label_en": "High blood pressure",
        "label_vi": "Cao huyết áp",
        "ask_en": "High blood pressure?",
        "ask_vi": "Cao huyết áp?",
    },
    {
        "value": "high_cholesterol",
        "label_en": "High cholesterol",
        "label_vi": "Cao mỡ máu",
        "ask_en": "High cholesterol?",
        "ask_vi": "Cao mỡ máu?",
    },
    {
        "value": "heart_disease",
        "label_en": "Heart disease",
        "label_vi": "Bệnh tim",
        "ask_en": "Heart disease?",
        "ask_vi": "Bệnh tim?",
    },
    {
        "value": "asthma",
        "label_en": "Asthma",
        "label_vi": "Hen suyễn",
        "ask_en": "Asthma?",
        "ask_vi": "Hen suyễn?",
    },
    {
        "value": "stroke",
        "label_en": "Stroke",
        "label_vi": "Đột quỵ",
        "ask_en": "Stroke?",
        "ask_vi": "Đột quỵ?",
    },
    {
        "value": "kidney_disease",
        "label_en": "Kidney disease",
        "label_vi": "Bệnh thận",
        "ask_en": "Kidney disease?",
        "ask_vi": "Bệnh thận?",
    },
    {
        "value": "liver_disease",
        "label_en": "Liver disease",
        "label_vi": "Bệnh gan",
        "ask_en": "Liver disease?",
        "ask_vi": "Bệnh gan?",
    },
    {
        "value": "seizures",
        "label_en": "Seizures / epilepsy",
        "label_vi": "Động kinh",
        "ask_en": "Seizures or epilepsy?",
        "ask_vi": "Động kinh?",
    },
    {
        "value": "cancer",
        "label_en": "Cancer",
        "label_vi": "Ung thư",
        "ask_en": "Cancer?",
        "ask_vi": "Ung thư?",
    },
    {
        "value": "mental_health",
        "label_en": "Mental health conditions",
        "label_vi": "Bệnh lý tâm thần",
        "ask_en": "Mental health conditions (depression, anxiety)?",
        "ask_vi": "Bệnh lý tâm thần (trầm cảm, lo âu)?",
    },
]

MED_COND_FIELD_IDS = frozenset(f"med_cond_{item['value']}" for item in MEDICAL_CONDITION_FIELDS)

LEGACY_CONDITION_TO_FIELD = {
    item["value"]: f"med_cond_{item['value']}" for item in MEDICAL_CONDITION_FIELDS
}

_NEGATIVE_SELECT = frozenset({"no", "false", "0", "n", "không", "khong"})


def med_cond_field_id(condition_value: str) -> str:
    return f"med_cond_{condition_value}"


def _is_negative(value: object) -> bool:
    if value is False:
        return True
    if value is None or value == "" or value == []:
        return False
    return str(value).strip().lower() in _NEGATIVE_SELECT


def build_medical_history_voice_section() -> str:
    total = len(MEDICAL_CONDITION_FIELDS)
    lines = [
        "=== MEDICAL HISTORY / BỆNH LÝ (short names only — mandatory) ===",
        f"Ask each of the {total} conditions separately — say ONLY the condition name, then wait.",
        "• Example EN: \"Diabetes?\" then wait. Example VI: \"Tiểu đường?\" then wait.",
        "• Do NOT say \"Have you ever been diagnosed with...\".",
        "• Do NOT say \"Yes or no\" / \"Có hoặc không\" / numbered progress like one of eleven.",
        "• Do NOT list all diseases in one question.",
        "• Save each answer immediately with update_form_field(field_id, true|false).",
        "• Field ids: med_cond_diabetes, med_cond_high_blood_pressure, med_cond_high_cholesterol,",
        "  med_cond_heart_disease, med_cond_asthma, med_cond_stroke, med_cond_kidney_disease,",
        "  med_cond_liver_disease, med_cond_seizures, med_cond_cancer, med_cond_mental_health.",
        "• After med_cond_cancer=yes, ask cancer_type. If cancer=no, save cancer_type as __skipped__.",
        "• Then ask other_medical_conditions for any other diseases not listed.",
        "• Intro once only: \"I'll go through each condition by name.\"",
    ]
    for item in MEDICAL_CONDITION_FIELDS:
        lines.append(f"  - {item['value']}: say \"{item['ask_en']}\" / \"{item['ask_vi']}\"")
    return "\n".join(lines)


def apply_medical_history_voice_hints(progress: dict, session_language: str = "en") -> dict:
    field_id = progress.get("next_field_id")
    if not field_id:
        return progress

    lang = session_language if session_language in ("vi", "en") else "en"

    if field_id in MED_COND_FIELD_IDS:
        condition = next(
            (item for item in MEDICAL_CONDITION_FIELDS if med_cond_field_id(item["value"]) == field_id),
            None,
        )
        if not condition:
            return progress

        ask_en = condition["ask_en"]
        ask_vi = condition["ask_vi"]
        ask = ask_vi if lang == "vi" else ask_en
        label = condition["label_vi"] if lang == "vi" else condition["label_en"]

        if lang == "vi":
            instruction = (
                f"MEDICAL HISTORY: chỉ nói tên bệnh — \"{ask_vi}\". "
                f"KHÔNG nói Have you ever / Có hoặc không / số thứ tự. "
                f"Lưu {field_id}=true nếu có, false nếu không."
            )
        else:
            instruction = (
                f"MEDICAL HISTORY: say ONLY \"{ask_en}\". "
                f"Do NOT say Have you ever / Yes or no / 1 of N. "
                f"Save {field_id}=true if yes, false if no."
            )

        progress["next_field_ask_en"] = ask_en
        progress["next_field_ask_vi"] = ask_vi
        progress["say_next_en"] = ask_en
        progress["say_next_vi"] = ask_vi
        progress["say_next"] = ask
        progress["voice_instruction"] = f"{progress.get('voice_instruction', '')} {instruction}".strip()
        return progress

    if field_id == "cancer_type":
        if lang == "vi":
            ask = "Loại ung thư là gì?"
            instruction = (
                "CANCER TYPE: chỉ hỏi khi med_cond_cancer=true. "
                "Nếu không có ung thư, lưu __skipped__."
            )
        else:
            ask = "What type of cancer?"
            instruction = (
                "CANCER TYPE: ask only when med_cond_cancer=true. "
                "If no cancer, save __skipped__."
            )
        progress["next_field_ask_en"] = ask if lang == "en" else "What type of cancer?"
        progress["next_field_ask_vi"] = ask if lang == "vi" else "Loại ung thư là gì?"
        progress["say_next"] = ask
        progress["voice_instruction"] = f"{progress.get('voice_instruction', '')} {instruction}".strip()

    return progress


def migrate_legacy_medical_conditions(answers: dict) -> dict:
    """Map old medical_conditions multiselect array to per-condition booleans."""
    legacy = answers.get("medical_conditions")
    if not isinstance(legacy, list) or not legacy:
        return answers

    merged = dict(answers)
    for value in legacy:
        field_id = LEGACY_CONDITION_TO_FIELD.get(str(value))
        if field_id:
            merged[field_id] = True
    return merged


def apply_medical_history_cascades(answers: dict) -> dict:
    """Skip follow-ups when parent answer is no / false."""
    merged = dict(answers)
    if merged.get("med_cond_cancer") is False and merged.get("cancer_type") in (None, ""):
        merged["cancer_type"] = SKIPPED_VALUE

    # Tobacco / alcohol / drugs — if no, do not ask amount/list
    if _is_negative(merged.get("tobacco_use")) and merged.get("tobacco_frequency") in (None, ""):
        merged["tobacco_frequency"] = SKIPPED_VALUE
    if _is_negative(merged.get("alcohol_use")) and merged.get("alcohol_frequency") in (None, ""):
        merged["alcohol_frequency"] = SKIPPED_VALUE
    if _is_negative(merged.get("recreational_drugs")) and merged.get("recreational_drugs_list") in (
        None,
        "",
    ):
        merged["recreational_drugs_list"] = SKIPPED_VALUE

    return merged
