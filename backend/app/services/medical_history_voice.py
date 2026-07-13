"""Ask each medical condition one at a time in the BỆNH LÝ section."""

from typing import TypedDict


class MedicalConditionPrompt(TypedDict):
    value: str
    label_en: str
    label_vi: str
    ask_en: str
    ask_vi: str


MEDICAL_CONDITION_FIELDS: list[MedicalConditionPrompt] = [
    {
        "value": "diabetes",
        "label_en": "Diabetes",
        "label_vi": "Tiểu đường",
        "ask_en": "Have you ever been diagnosed with diabetes? Yes or no.",
        "ask_vi": "Bạn có từng được chẩn đoán tiểu đường không? Có hay không?",
    },
    {
        "value": "high_blood_pressure",
        "label_en": "High blood pressure",
        "label_vi": "Cao huyết áp",
        "ask_en": "Have you ever been diagnosed with high blood pressure? Yes or no.",
        "ask_vi": "Bạn có từng được chẩn đoán cao huyết áp không? Có hay không?",
    },
    {
        "value": "high_cholesterol",
        "label_en": "High cholesterol",
        "label_vi": "Cao mỡ máu",
        "ask_en": "Have you ever been diagnosed with high cholesterol? Yes or no.",
        "ask_vi": "Bạn có từng được chẩn đoán cao mỡ máu không? Có hay không?",
    },
    {
        "value": "heart_disease",
        "label_en": "Heart disease",
        "label_vi": "Bệnh tim",
        "ask_en": "Have you ever been diagnosed with heart disease? Yes or no.",
        "ask_vi": "Bạn có từng được chẩn đoán bệnh tim không? Có hay không?",
    },
    {
        "value": "asthma",
        "label_en": "Asthma",
        "label_vi": "Hen suyễn",
        "ask_en": "Have you ever been diagnosed with asthma? Yes or no.",
        "ask_vi": "Bạn có từng được chẩn đoán hen suyễn không? Có hay không?",
    },
    {
        "value": "stroke",
        "label_en": "Stroke",
        "label_vi": "Đột quỵ",
        "ask_en": "Have you ever had a stroke? Yes or no.",
        "ask_vi": "Bạn có từng bị đột quỵ không? Có hay không?",
    },
    {
        "value": "kidney_disease",
        "label_en": "Kidney disease",
        "label_vi": "Bệnh thận",
        "ask_en": "Have you ever been diagnosed with kidney disease? Yes or no.",
        "ask_vi": "Bạn có từng được chẩn đoán bệnh thận không? Có hay không?",
    },
    {
        "value": "liver_disease",
        "label_en": "Liver disease",
        "label_vi": "Bệnh gan",
        "ask_en": "Have you ever been diagnosed with liver disease? Yes or no.",
        "ask_vi": "Bạn có từng được chẩn đoán bệnh gan không? Có hay không?",
    },
    {
        "value": "seizures",
        "label_en": "Seizures / epilepsy",
        "label_vi": "Động kinh",
        "ask_en": "Have you ever been diagnosed with seizures or epilepsy? Yes or no.",
        "ask_vi": "Bạn có từng được chẩn đoán động kinh không? Có hay không?",
    },
    {
        "value": "cancer",
        "label_en": "Cancer",
        "label_vi": "Ung thư",
        "ask_en": "Have you ever been diagnosed with cancer? Yes or no.",
        "ask_vi": "Bạn có từng được chẩn đoán ung thư không? Có hay không?",
    },
    {
        "value": "mental_health",
        "label_en": "Mental health conditions",
        "label_vi": "Bệnh lý tâm thần",
        "ask_en": (
            "Have you ever been diagnosed with a mental health condition "
            "such as depression or anxiety? Yes or no."
        ),
        "ask_vi": (
            "Bạn có từng được chẩn đoán bệnh lý tâm thần "
            "(ví dụ trầm cảm, lo âu) không? Có hay không?"
        ),
    },
]

MED_COND_FIELD_IDS = frozenset(f"med_cond_{item['value']}" for item in MEDICAL_CONDITION_FIELDS)

LEGACY_CONDITION_TO_FIELD = {
    item["value"]: f"med_cond_{item['value']}" for item in MEDICAL_CONDITION_FIELDS
}


def med_cond_field_id(condition_value: str) -> str:
    return f"med_cond_{condition_value}"


def build_medical_history_voice_section() -> str:
    total = len(MEDICAL_CONDITION_FIELDS)
    lines = [
        "=== MEDICAL HISTORY / BỆNH LÝ (one disease per question — mandatory) ===",
        f"Ask each of the {total} conditions separately — ONE yes/no question at a time.",
        "• Do NOT list all diseases in one question.",
        "• Save each answer immediately with update_form_field(field_id, true|false).",
        "• Field ids: med_cond_diabetes, med_cond_high_blood_pressure, med_cond_high_cholesterol,",
        "  med_cond_heart_disease, med_cond_asthma, med_cond_stroke, med_cond_kidney_disease,",
        "  med_cond_liver_disease, med_cond_seizures, med_cond_cancer, med_cond_mental_health.",
        "• After med_cond_cancer=yes, ask cancer_type for the cancer type. If cancer=no, save",
        "  cancer_type as __skipped__.",
        "• Then ask other_medical_conditions for any other diseases not listed.",
        "• Brief intro once: \"I'll ask about each condition one by one.\"",
    ]
    for index, item in enumerate(MEDICAL_CONDITION_FIELDS, start=1):
        lines.append(f"  {index}/{total} {item['value']}: {item['ask_en']}")
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

        index = MEDICAL_CONDITION_FIELDS.index(condition) + 1
        total = len(MEDICAL_CONDITION_FIELDS)
        ask = condition["ask_vi"] if lang == "vi" else condition["ask_en"]
        label = condition["label_vi"] if lang == "vi" else condition["label_en"]

        if lang == "vi":
            intro = f"Bệnh {index}/{total} — {label}: {ask}"
            instruction = (
                f"MEDICAL HISTORY {index}/{total}: hỏi MỘT bệnh — {label}. "
                f"Lưu {field_id}=true nếu có, false nếu không. Không liệt kê tất cả bệnh cùng lúc."
            )
        else:
            intro = f"Condition {index} of {total} — {label}: {ask}"
            instruction = (
                f"MEDICAL HISTORY {index}/{total}: ask ONE condition — {label}. "
                f"Save {field_id}=true if yes, false if no. Do NOT list all conditions at once."
            )

        progress["next_field_ask_en"] = condition["ask_en"]
        progress["next_field_ask_vi"] = condition["ask_vi"]
        progress["say_next_en"] = condition["ask_en"]
        progress["say_next_vi"] = condition["ask_vi"]
        progress["say_next"] = intro
        progress["voice_instruction"] = f"{progress.get('voice_instruction', '')} {instruction}".strip()
        return progress

    if field_id == "cancer_type":
        if lang == "vi":
            ask = "Nếu có ung thư, loại ung thư là gì?"
            instruction = (
                "CANCER TYPE: chỉ hỏi khi med_cond_cancer=true. "
                "Nếu bệnh nhân nói không có ung thư, lưu __skipped__."
            )
        else:
            ask = "If you had cancer, what type of cancer was it?"
            instruction = (
                "CANCER TYPE: ask only when med_cond_cancer=true. "
                "If patient has no cancer, save __skipped__."
            )
        progress["next_field_ask_en"] = ask
        progress["next_field_ask_vi"] = ask if lang == "vi" else progress.get("next_field_ask_vi")
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
    """Skip cancer_type when patient has no cancer."""
    merged = dict(answers)
    if merged.get("med_cond_cancer") is False and merged.get("cancer_type") is None:
        merged["cancer_type"] = "__skipped__"
    return merged
