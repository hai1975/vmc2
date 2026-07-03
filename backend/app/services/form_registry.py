import json
from pathlib import Path

from app.config import settings
from app.models import FormField, FormSchema, FormSummary

SKIPPED_VALUE = "__skipped__"
INTERNAL_ANSWER_KEYS = frozenset({"_signature", "_selfie"})
VOICE_ACK_EN = "Got it, I'll record that."
VOICE_ACK_VI = "Vâng, tôi sẽ ghi vào."


def skipped_pdf_label(language: str = "en") -> str:
    return "Không có" if language == "vi" else "None"

SKIP_CASCADES: dict[str, list[str]] = {
    "guardian_1_name": ["guardian_1_relationship"],
    "guardian_2_name": ["guardian_2_relationship"],
}

DECLINED_PHRASES = frozenset({
    "none",
    "n/a",
    "na",
    "skip",
    "skipped",
    "no",
    "nope",
    "không",
    "khong",
    "không có",
    "khong co",
    "decline",
    "declined",
    "not applicable",
    "don't have",
    "dont have",
    "do not have",
    "bỏ qua",
    "bo qua",
    SKIPPED_VALUE,
})


def _schema_id_from_filename(filename: str) -> str:
    return Path(filename).stem


def list_pdf_forms() -> list[FormSummary]:
    forms: list[FormSummary] = []
    if not settings.form_dir.exists():
        return forms

    for pdf in sorted(settings.form_dir.glob("*.pdf")):
        schema = load_schema(_schema_id_from_filename(pdf.name))
        forms.append(
            FormSummary(
                id=schema.id if schema else _schema_id_from_filename(pdf.name),
                filename=pdf.name,
                title=schema.title if schema else {"vi": pdf.stem, "en": pdf.stem},
                default=schema.default if schema else pdf.name == "form_en.pdf",
            )
        )
    return forms


def load_schema(form_id: str) -> FormSchema | None:
    schema_path = settings.schema_dir / f"{form_id}.json"
    if not schema_path.exists():
        return None
    data = json.loads(schema_path.read_text(encoding="utf-8"))
    return FormSchema.model_validate(data)


def get_schema_or_raise(form_id: str) -> FormSchema:
    schema = load_schema(form_id)
    if not schema:
        raise FileNotFoundError(f"Schema not found for form: {form_id}")
    return schema


def _is_empty(value: object | None) -> bool:
    if value == SKIPPED_VALUE:
        return False
    return value is None or value == "" or value == []


def _is_declined_answer(value: object) -> bool:
    if value == SKIPPED_VALUE:
        return True
    text = str(value).strip().lower()
    return text in DECLINED_PHRASES


def apply_skip_cascades(schema: FormSchema, answers: dict) -> dict:
    field_ids = {field.id for field in schema.fields}
    merged = dict(answers)
    for parent_id, child_ids in SKIP_CASCADES.items():
        if merged.get(parent_id) != SKIPPED_VALUE:
            continue
        for child_id in child_ids:
            if child_id in field_ids and child_id not in merged:
                merged[child_id] = SKIPPED_VALUE
    return merged


def normalize_field_value(field: FormField, value: object) -> object | None:
    if _is_empty(value):
        return None

    if field.type == "boolean":
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        if text in ("true", "yes", "1", "y", "có", "co", "dong y", "đồng ý", "agree", "ok", "vâng", "vang", "ừ", "uh"):
            return True
        if text in ("false", "no", "0", "n", "không", "khong", "decline", "none"):
            return False
        return value

    if not field.options:
        if _is_declined_answer(value):
            if not field.required:
                return SKIPPED_VALUE
            return None
        text = str(value).strip()
        return text

    allowed = {opt.value: opt for opt in field.options}
    label_map: dict[str, str] = {}
    for opt in field.options:
        label_map[opt.value.lower()] = opt.value
        for label in opt.label.values():
            label_map[label.lower()] = opt.value

    aliases = {
        "medi_cal": ("medi-cal", "medicaid", "medi cal"),
        "ppo": ("p p o",),
        "hmo": (),
        "uninsured": ("none", "no insurance", "no coverage", "khong co", "không có", "un insured"),
        "male": ("man", "nam"),
        "female": ("woman", "nu", "nữ"),
        "not_disclose": ("prefer not to say", "choose not to disclose"),
        "hispanic": ("latino", "latina", "hispanic or latino"),
        "not_hispanic": ("not hispanic", "not latino"),
        "unknown": ("not sure", "dont know", "don't know", "khong biet", "không biết"),
        "yes": ("có", "co", "yeah", "y", "correct", "đúng"),
        "no": ("không", "khong", "nope", "nah"),
        "unsure": ("not sure", "don't know", "dont know", "không chắc", "khong chac"),
        "negative": ("âm tính", "am tinh"),
        "positive": ("dương tính", "duong tinh"),
        "ftm": ("female to male", "trans man", "transgender male"),
        "mtf": ("male to female", "trans woman", "transgender female"),
        "genderqueer": ("non binary", "non-binary", "phi nhị phân"),
        "asian": ("chau a", "châu á"),
        "white": ("caucasian", "da trang", "da trắng"),
        "african_american": ("black", "african american"),
        "bisexual": ("bi", "song tinh", "song tính"),
        "straight": ("heterosexual", "di tinh", "dị tính"),
        "gay_lesbian": ("gay", "lesbian", "lgbtq", "dong tinh", "đồng tính"),
    }

    if field.type == "multiselect":
        items = value if isinstance(value, list) else [value]
        normalized: list[str] = []
        for item in items:
            one = normalize_field_value(
                FormField(
                    id=field.id,
                    type="select",
                    label=field.label,
                    voice_prompt=field.voice_prompt,
                    options=field.options,
                ),
                item,
            )
            if one is not None and one in allowed and one not in normalized:
                normalized.append(str(one))
        return normalized

    raw = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    compact = raw.replace("_", "")
    if raw in label_map:
        return label_map[raw]
    for opt_value in allowed:
        if raw == opt_value.lower() or compact == opt_value.lower().replace("_", ""):
            return opt_value
    for opt_value, alias_list in aliases.items():
        if opt_value in allowed and raw in alias_list:
            return opt_value
    return str(value).strip()


def get_form_progress(schema: FormSchema, answers: dict) -> dict:
    field_map = {field.id: field for field in schema.fields}
    missing_required: list[str] = []
    missing_optional: list[str] = []
    filled: dict[str, object] = {}

    for field in schema.fields:
        value = answers.get(field.id)
        if _is_empty(value):
            if field.required:
                missing_required.append(field.id)
            else:
                missing_optional.append(field.id)
        else:
            filled[field.id] = value

    next_field_id: str | None = None
    for field in schema.fields:
        if field.id in missing_required or field.id in missing_optional:
            next_field_id = field.id
            break

    next_field = field_map.get(next_field_id) if next_field_id else None
    ready_to_submit = len(missing_required) == 0
    all_fields_collected = len(missing_required) == 0 and len(missing_optional) == 0
    total_fields = len(schema.fields)
    filled_count = len(filled)
    remaining_count = len(missing_required) + len(missing_optional)

    result: dict = {
        "filled_fields": filled,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "next_field_id": next_field_id,
        "ready_to_submit": ready_to_submit,
        "all_fields_collected": all_fields_collected,
        "filled_count": filled_count,
        "remaining_count": remaining_count,
        "total_fields": total_fields,
    }
    if next_field:
        result["next_field_required"] = next_field.required
        result["next_field_ask_en"] = next_field.voice_prompt.get("en", next_field.id)
        result["next_field_ask_vi"] = next_field.voice_prompt.get("vi", result["next_field_ask_en"])
        if next_field.options:
            result["next_field_allowed_values"] = [opt.value for opt in next_field.options]
    return result


def build_say_next(progress: dict, session_language: str = "en") -> str | None:
    """Brief ack + next question — never echo the answer or ask is that correct."""
    if progress.get("all_fields_collected"):
        if session_language == "vi":
            return (
                "Tôi xin đọc lại toàn bộ thông tin bạn đã cung cấp. "
                "Tất cả thông tin trên đúng chưa ạ?"
            )
        return "Let me read back all the information you provided. Is everything correct?"
    ask_en = progress.get("next_field_ask_en")
    ask_vi = progress.get("next_field_ask_vi") or ask_en
    if not ask_en:
        return None
    if session_language == "vi" and ask_vi:
        return f"{VOICE_ACK_VI} {ask_vi}"
    return f"{VOICE_ACK_EN} {ask_en}"


def build_say_next_bilingual(progress: dict) -> dict[str, str | None]:
    if progress.get("all_fields_collected"):
        return {
            "en": "Let me read back all the information you provided. Is everything correct?",
            "vi": "Tôi xin đọc lại toàn bộ thông tin bạn đã cung cấp. Tất cả thông tin trên đúng chưa ạ?",
        }
    ask_en = progress.get("next_field_ask_en")
    ask_vi = progress.get("next_field_ask_vi") or ask_en
    if not ask_en:
        return {"en": None, "vi": None}
    return {
        "en": f"{VOICE_ACK_EN} {ask_en}",
        "vi": f"{VOICE_ACK_VI} {ask_vi}",
    }


def build_voice_tool_hint(progress: dict, saved_field_id: str | None = None) -> str:
    """Short imperative instruction returned after each update_form_field tool call."""
    forbidden = (
        "FORBIDDEN after saving a field: 'I heard', 'is that correct', 'did I get that right', "
        "'just to confirm', 'let me make sure', or echoing the saved value back."
    )
    if progress.get("all_fields_collected"):
        return (
            f"{forbidden} "
            "ALL fields are now collected. Read ONE full summary of everything. "
            "Ask ONCE whether ALL information is correct — this is the ONLY confirmation allowed."
        )
    next_id = progress.get("next_field_id")
    ask_en = progress.get("next_field_ask_en") or next_id or "the next field"
    saved = f" ({saved_field_id} saved)" if saved_field_id else ""
    return (
        f"Field saved{saved}. {forbidden} "
        f"Speak say_next: brief ack ('{VOICE_ACK_EN}' / '{VOICE_ACK_VI}') then the next question. "
        f"Next ({next_id}): {ask_en}"
    )


def preferred_voice_language(form_id: str, session_language: str = "en") -> str:
    if form_id == "form_vn":
        return "vi"
    if form_id == "form_en":
        return "en"
    return session_language if session_language in ("vi", "en") else "en"


def get_form_progress_with_hint(
    schema: FormSchema,
    answers: dict,
    saved_field_id: str | None = None,
    session_language: str = "en",
) -> dict:
    progress = get_form_progress(schema, answers)
    progress["voice_instruction"] = build_voice_tool_hint(progress, saved_field_id)
    bilingual = build_say_next_bilingual(progress)
    progress["say_next"] = build_say_next(progress, session_language)
    progress["say_next_en"] = bilingual["en"]
    progress["say_next_vi"] = bilingual["vi"]
    return progress


def normalize_answers(schema: FormSchema, answers: dict) -> dict:
    field_map = {field.id: field for field in schema.fields}
    internal = {k: v for k, v in answers.items() if k.startswith("_")}
    normalized: dict = {}
    for field_id, value in answers.items():
        if field_id.startswith("_"):
            continue
        field = field_map.get(field_id)
        if not field:
            continue
        cleaned = normalize_field_value(field, value)
        if cleaned == SKIPPED_VALUE or not _is_empty(cleaned):
            normalized[field_id] = cleaned
    merged = apply_skip_cascades(schema, normalized)
    merged.update(internal)
    return merged


def build_voice_system_instruction(
    schema: FormSchema,
    language: str = "en",
    answers: dict | None = None,
) -> str:
    lang = language if language in ("vi", "en") else "en"
    lines = [
        "You are a friendly patient registration voice assistant for VM Clinic.",
        "Goal: collect all form fields through natural spoken conversation.",
        "",
        "=== AFTER EACH ANSWER (highest priority) ===",
        "When the patient answers a question:",
        "  1. Call update_form_field IMMEDIATELY — do NOT speak first.",
        "  2. Wait for tool response with say_next.",
        "  3. Speak say_next: a SHORT ack + the NEXT question. Nothing else.",
        f'  • English ack: "{VOICE_ACK_EN}" then next question.',
        f'  • Vietnamese ack: "{VOICE_ACK_VI}" then next question.',
        "  • Other languages: use the same short ack meaning (I will record that), then next question.",
        "WRONG: Patient says 'Maria Antonio' → You: 'I heard Maria Antonio — is that correct?'",
        f'RIGHT: Patient says Maria Antonio → update_form_field → You: "{VOICE_ACK_EN} What is your date of birth?"',
        "NEVER repeat the patient's answer back. NEVER ask 'is that correct?' per field.",
        "The ONLY 'is that correct?' allowed is the FINAL summary when all_fields_collected is true.",
        "Forbidden per field: I heard, is that correct, did I get that right, just to confirm, let me make sure.",
        "",
        "Rules:",
        "- YOU ALWAYS SPEAK FIRST. Never wait for the patient to say anything before your first message.",
        "- When the session starts, immediately speak aloud without waiting for silence or user input.",
        "- Ask ONE question at a time.",
        "- NO PER-FIELD CONFIRMATION:",
        "  • After saving, say a SHORT ack (I'll record that / tôi sẽ ghi vào) then the NEXT question.",
        "  • NEVER echo the answer or ask 'is that correct?' for each field.",
        "  • The ONLY confirmation is the FINAL summary when all_fields_collected is true.",
        "- LANGUAGE RULES (critical — follow exactly):",
        "  • OPENING ONLY in English: your first greeting and your first form question must be in English.",
        '  • Opening greeting (English only): "VM Clinic is listening. I can help you register."',
        "  • After the patient responds even once, detect their language and use ONLY that language for every",
        "    subsequent word — questions, confirmations, reminders, and the submit message.",
        "  • If the patient speaks Vietnamese, switch to Vietnamese immediately and stay in Vietnamese.",
        "  • If the patient speaks Spanish, Chinese, Korean, French, or any other language, switch immediately",
        "    and stay in that language until they clearly switch again.",
        "  • If the patient asks to change language (e.g. 'speak Vietnamese', 'nói tiếng Việt'), switch immediately.",
        "  • NEVER say you prefer English, default to English, or ask the patient to use English.",
        "  • NEVER say phrases like: 'prefer English', 'I'll continue in English', 'default language is English',",
        "    'you can answer in English if you prefer', or any similar wording.",
        "  • Match the patient's language naturally — do not announce or justify your language choice.",
        "- Form field values (names, addresses, phone, email) must be saved exactly as the patient says them.",
        "- For select/multiselect fields, still save exact allowed_values (English codes like medi_cal, uninsured).",
        "- SAVE RULE (default — save immediately when the answer is clear):",
        "  • Workflow: patient answers clearly → call update_form_field FIRST → then ask next question.",
        "  • NEVER: patient answers → you confirm → then save. Save first, no echo.",
        "  • When the patient gives a CLEAR answer, call update_form_field right away.",
        "  • After the tool returns, speak say_next exactly: ack + next question.",
        "  • Do NOT read back what they said. Do NOT ask if it is correct.",
        "- RE-CONFIRM ONLY at final summary (never per field):",
        "  • Do NOT confirm individual fields — even names, email, phone, or dates.",
        "  • Only re-ask if audio was inaudible: 'Sorry, could you repeat that?' — not 'is that correct?'",
        "  • Patient corrects themselves → update_form_field, then continue to next question.",
        "- After each update_form_field call, read next_field_id and ask that question next.",
        "- FINAL SUMMARY (once — when all_fields_collected becomes true):",
        "  • Read back ALL collected fields in a concise summary (grouped: personal, insurance, etc.).",
        "  • Ask ONCE: 'Is all of this information correct?' / 'Tất cả thông tin trên đúng chưa ạ?'",
        "  • If patient corrects any field, update it, then briefly confirm only the correction.",
        "  • After final yes, tell patient to tap Submit on screen for signature and photo.",
        "- DECLINING / NONE ANSWERS (critical for optional fields):",
        '  • If the patient says none / không có / skip for an OPTIONAL field,',
        '    call update_form_field(field_id, "__skipped__") without extra confirmation if intent is clear.',
        "  • Declining IS an answer — you MUST still call update_form_field. Never just move on without saving.",
        "  • __skipped__ writes Không có (vi) or None (en) on the PDF and counts as done.",
        "  • For insurance 'no insurance' use value uninsured (NOT __skipped__).",
        "  • For boolean consent: no/không = false (NOT __skipped__).",
        "  • For select optional fields: use an allowed value like not_disclose or unknown when patient",
        "    prefers not to answer; use __skipped__ only when they explicitly skip the whole question.",
        "- PROGRESS RULES (critical — do not invent numbers):",
        "  • After each update_form_field, the tool returns filled_count, remaining_count, total_fields.",
        "  • ONLY use those exact numbers if you mention progress — never guess or make up counts.",
        "  • Do NOT randomly announce progress every turn. At most occasionally remind remaining_count.",
        "  • If remaining_count is 0 and all_fields_collected is true, tell patient to click Submit.",
        "- If the patient declines an optional field, save __skipped__ and move to next_field_id.",
        "- Encode value as JSON string: strings in quotes, booleans as true/false, arrays for multiselect.",
        "- For select/multiselect/boolean fields, ALWAYS use exact allowed_values — never save label text.",
        "- Example: insurance='uninsured' goes to field_id insurance, NOT guardian_1_name.",
        "- Ask about EVERY field in schema order — required AND optional.",
        "- Sections to cover (do not skip): page 1 personal/insurance/demographics/pharmacy/consent;",
        "  page 2 medical history, surgeries, medications, allergies, caretaker, pediatric questions;",
        "  page 3 family history, tobacco/alcohol/drugs, safety, vaccinations, TB, interpretation;",
        "  page 4 HIPAA acknowledgement, release contacts, electronic communication consent;",
        "  page 5 medical records authorization and disclosure purpose.",
        "- ready_to_submit=true only means required fields are done — you MUST keep asking optional",
        "  fields until missing_optional is empty or the patient declines each one.",
        "- Only tell the patient to click Submit when all_fields_collected is true.",
        "- Do NOT stop early after insurance or personal info — continue through demographics and pharmacy.",
        "- When asking a field, use ask_en while still in the English opening phase; after switching to the patient's",
        "  language, use ask_vi for Vietnamese, or translate ask_en naturally for other languages.",
        "- When all_fields_collected is true, tell the patient clearly in THEIR current language:",
        '  English: "Please review the summary, then tap Submit on the screen to sign and take your photo."',
        '  Vietnamese: "Vui lòng xem lại tóm tắt, rồi bấm Submit trên màn hình để ký và chụp ảnh."',
        "- IMMEDIATELY when the session begins, speak FIRST without waiting for the patient.",
        "- Do NOT wait for the patient to speak, cough, or make any sound before you talk.",
        "",
        f"Form: {schema.title.get(lang, schema.title.get('en', schema.id))}",
        "",
    ]
    progress = get_form_progress(schema, answers or {})
    if progress["filled_fields"]:
        lines.append("Already collected:")
        for field_id, value in progress["filled_fields"].items():
            lines.append(f"  - {field_id}: {value}")
        lines.append("")
    if progress["missing_required"] or progress["missing_optional"]:
        lines.append("Still need to collect (in order):")
        for field in schema.fields:
            if field.id in progress["missing_required"]:
                lines.append(f"  - {field.id} (required)")
            elif field.id in progress["missing_optional"]:
                lines.append(f"  - {field.id} (optional)")
        if progress.get("next_field_id"):
            lines.append(f"NEXT QUESTION MUST BE: {progress['next_field_id']}")
        lines.append("")
    if progress.get("all_fields_collected"):
        lines.append(
            "All fields collected. Read FULL summary once, ask if all correct, then tell patient to tap Submit."
        )
        lines.append("")
    elif progress.get("ready_to_submit"):
        lines.append(
            "Required fields are complete but optional fields remain — keep asking, do NOT say Submit yet."
        )
        lines.append("")
    lines.extend([
        "Fields:",
    ])
    for field in schema.fields:
        prompt_en = field.voice_prompt.get("en", field.id)
        prompt_vi = field.voice_prompt.get("vi", prompt_en)
        req = "required" if field.required else "optional"
        lines.append(f"- {field.id} ({field.type}, {req})")
        lines.append(f"  ask_en: {prompt_en}")
        lines.append(f"  ask_vi: {prompt_vi}")
        if field.options:
            opts = ", ".join(f"{o.value}" for o in field.options)
            lines.append(f"  allowed_values: {opts}")
    return "\n".join(lines)


def validate_answers(schema: FormSchema, answers: dict) -> list[str]:
    errors: list[str] = []
    field_map = {f.id: f for f in schema.fields}

    for field_id, field in field_map.items():
        value = answers.get(field_id)
        if field.required and (value is None or value == "" or value == []):
            errors.append(f"Missing required field: {field_id}")
            continue
        if value is None or value == "":
            continue
        if field.type == "email" and "@" not in str(value):
            errors.append(f"Invalid email: {field_id}")
        if field.options:
            allowed = {o.value for o in field.options}
            if field.type == "multiselect":
                if not isinstance(value, list) or not all(v in allowed for v in value):
                    errors.append(f"Invalid options for: {field_id}")
            elif str(value) not in allowed:
                errors.append(f"Invalid option for: {field_id}")

    return errors
