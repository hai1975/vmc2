import json
from pathlib import Path

from app.config import settings
from app.models import FormField, FormSchema, FormSummary


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
                default=schema.default if schema else pdf.name == "f-patient.pdf",
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
    return value is None or value == "" or value == []


def normalize_field_value(field: FormField, value: object) -> object | None:
    if _is_empty(value):
        return None

    if field.type == "boolean":
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        if text in ("true", "yes", "1", "y", "có", "co", "dong y", "đồng ý", "agree", "ok"):
            return True
        if text in ("false", "no", "0", "n", "không", "khong", "decline", "none"):
            return False
        return value

    if not field.options:
        text = str(value).strip()
        if text.lower() in ("none", "n/a", "na", "skip", "no", "không", "khong"):
            return None
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
        "unknown": ("not sure", "dont know", "don't know"),
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

    result: dict = {
        "filled_fields": filled,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "next_field_id": next_field_id,
        "ready_to_submit": ready_to_submit,
        "all_fields_collected": all_fields_collected,
    }
    if next_field:
        result["next_field_required"] = next_field.required
        result["next_field_ask_en"] = next_field.voice_prompt.get("en", next_field.id)
        result["next_field_ask_vi"] = next_field.voice_prompt.get("vi", result["next_field_ask_en"])
        if next_field.options:
            result["next_field_allowed_values"] = [opt.value for opt in next_field.options]
    return result


def normalize_answers(schema: FormSchema, answers: dict) -> dict:
    field_map = {field.id: field for field in schema.fields}
    normalized: dict = {}
    for field_id, value in answers.items():
        field = field_map.get(field_id)
        if not field:
            continue
        cleaned = normalize_field_value(field, value)
        if not _is_empty(cleaned):
            normalized[field_id] = cleaned
    return normalized


def build_voice_system_instruction(
    schema: FormSchema,
    language: str = "en",
    answers: dict | None = None,
) -> str:
    lang = language if language in ("vi", "en") else "en"
    lines = [
        "You are a friendly patient registration voice assistant for VM Clinic.",
        "Goal: collect all form fields through natural spoken conversation.",
        "Rules:",
        "- YOU ALWAYS SPEAK FIRST. Never wait for the patient to say anything before your first message.",
        "- When the session starts, immediately speak aloud without waiting for silence or user input.",
        "- Ask ONE question at a time.",
        "- Confirm spelling for names, email, and phone when unclear.",
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
        "- After each valid answer, immediately call update_form_field(field_id, value).",
        "- Encode value as JSON string: strings in quotes, booleans as true/false, arrays for multiselect.",
        "- For select/multiselect/boolean fields, ALWAYS use exact allowed_values — never save label text.",
        "- Example: insurance='uninsured' goes to field_id insurance, NOT guardian_1_name.",
        "- Ask about EVERY field in schema order — required AND optional.",
        "- Sections to cover (do not skip): personal info, insurance, demographics (race, ethnicity,",
        "  gender, sexual orientation), pharmacy, treatment consent, emergency contact.",
        "- After each update_form_field call, read next_field_id and ask that question next.",
        "- If the patient declines an optional field, skip it and move to the next field in order.",
        "- ready_to_submit=true only means required fields are done — you MUST keep asking optional",
        "  fields until missing_optional is empty or the patient declines each one.",
        "- Only tell the patient to click Submit when all_fields_collected is true.",
        "- Do NOT stop early after insurance or personal info — continue through demographics and pharmacy.",
        "- When asking a field, use ask_en while still in the English opening phase; after switching to the patient's",
        "  language, use ask_vi for Vietnamese, or translate ask_en naturally for other languages.",
        "- When all_fields_collected is true, tell the patient clearly in THEIR current language:",
        '  English: "You have completed the form. Please click the Submit button on the screen to finish registration."',
        '  Vietnamese: "Bạn đã hoàn thành form. Vui lòng bấm nút Submit trên màn hình để hoàn tất đăng ký."',
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
        lines.append("All fields collected. Tell the patient to click Submit.")
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
