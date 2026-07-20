import json
from pathlib import Path

from app.config import settings
from app.models import FormField, FormSchema, FormSummary
from app.services.form_selector import ACTIVE_FORM_IDS, TRIAGE_FORM_ID
from app.services.consent_voice import (
    CONSENT_FIELD_IDS,
    apply_consent_voice_hints,
    build_consent_voice_section,
)
from app.services.medical_history_voice import (
    apply_medical_history_cascades,
    apply_medical_history_voice_hints,
    build_medical_history_voice_section,
    migrate_legacy_medical_conditions,
)
from app.services.form_variant import build_form_variant_voice_section
from app.services.voice_language import build_southern_vietnamese_voice_section
from app.services.voice_addressing import (
    apply_addressing_voice_hints,
    build_addressing_voice_section,
    resolve_addressing,
)
from app.services.field_prefill import (
    VOICE_SKIP_FIELDS,
    apply_field_prefill,
    apply_field_prefill_voice_hints,
    build_field_prefill_voice_section,
)
from app.services.demographic_voice import apply_demographic_voice_hints, build_demographic_voice_section
from app.services.pharmacy_suggestions import (
    PharmacyEntry,
    build_pharmacy_field_hint,
    build_pharmacy_voice_section,
)

SKIPPED_VALUE = "__skipped__"
BLANK_VALUE = "__blank__"
INTERNAL_ANSWER_KEYS = frozenset({"_signature", "_selfie"})

# Rotate short acks — empty string = skip ack, ask next question directly (most natural).
VOICE_ACKS_EN = ("", "Thanks.", "Got it.", "Okay,", "Sure,")
VOICE_ACKS_VI = ("", "Dạ.", "Dạ rồi.", "Ừ ạ,", "Dạ em,")


def pick_voice_ack(language: str, filled_count: int) -> str:
    pool = VOICE_ACKS_VI if language == "vi" else VOICE_ACKS_EN
    if not pool:
        return ""
    index = max(filled_count - 1, 0) % len(pool)
    return pool[index]


def join_ack_and_question(ack: str, question: str) -> str:
    if not ack:
        return question
    sep = " " if ack.endswith((",", "—", "–")) else " "
    return f"{ack}{sep}{question}"


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

    for form_id in sorted(ACTIVE_FORM_IDS):
        schema = load_schema(form_id)
        if not schema:
            continue
        forms.append(
            FormSummary(
                id=schema.id,
                filename=schema.filename,
                title=schema.title,
                default=form_id == "adult_en",
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
    if value in (SKIPPED_VALUE, BLANK_VALUE):
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
    if str(value).strip() == BLANK_VALUE:
        return BLANK_VALUE
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


FORM_PAGE_TITLES: dict[int, dict[str, str]] = {
    1: {
        "en": "Personal information, insurance, pharmacy, and treatment consent",
        "vi": "Thông tin cá nhân, bảo hiểm, nhà thuốc và đồng ý điều trị",
    },
    2: {
        "en": "Medical history, surgeries, medications, and allergies",
        "vi": "Tiền sử bệnh, phẫu thuật, thuốc và dị ứng",
    },
    3: {
        "en": "Family history, lifestyle, safety, privacy, and contacts",
        "vi": "Tiền sử gia đình, lối sống, an toàn, quyền riêng tư và liên hệ",
    },
    4: {
        "en": "Authorization for release of information",
        "vi": "Ủy quyền tiết lộ thông tin",
    },
    5: {
        "en": "Signature",
        "vi": "Chữ ký",
    },
}


def _max_form_page(schema: FormSchema) -> int:
    max_page = max((field.page for field in schema.fields), default=1)
    if schema.id.startswith("child"):
        return max(max_page, 5)
    if schema.id.startswith("adult"):
        return max(max_page, 4)
    return max_page


def _voice_fields(schema: FormSchema, page: int | None = None) -> list:
    fields = [f for f in schema.fields if f.id not in VOICE_SKIP_FIELDS]
    if page is None:
        return fields
    return [f for f in fields if f.page == page]


def voice_fields_for_section(schema: FormSchema, page: int | None = None) -> list:
    """Fields the voicebot should collect (excludes provider lookup blanks)."""
    return _voice_fields(schema, page)


def get_form_progress(schema: FormSchema, answers: dict, page: int | None = None) -> dict:
    """Progress for voice/UI. When page is set, next_field is scoped to that section only."""
    field_map = {field.id: field for field in schema.fields}
    scope_fields = _voice_fields(schema, page)
    all_voice_fields = _voice_fields(schema, None)

    missing_required: list[str] = []
    missing_optional: list[str] = []
    filled: dict[str, object] = {}

    for field in scope_fields:
        value = answers.get(field.id)
        if _is_empty(value):
            if field.required:
                missing_required.append(field.id)
            else:
                missing_optional.append(field.id)
        else:
            filled[field.id] = value

    global_missing_required: list[str] = []
    global_missing_optional: list[str] = []
    for field in all_voice_fields:
        value = answers.get(field.id)
        if _is_empty(value):
            if field.required:
                global_missing_required.append(field.id)
            else:
                global_missing_optional.append(field.id)

    next_field_id: str | None = None
    for field in scope_fields:
        if field.id in missing_required or field.id in missing_optional:
            next_field_id = field.id
            break

    next_field = field_map.get(next_field_id) if next_field_id else None
    ready_to_submit = len(global_missing_required) == 0
    all_fields_collected = (
        len(global_missing_required) == 0 and len(global_missing_optional) == 0
    )
    section_complete = page is not None and next_field_id is None
    total_pages = _max_form_page(schema)

    # First unanswered field across the whole form (drives UI page sync even if bot skips navigate).
    global_next_field_id: str | None = None
    for field in all_voice_fields:
        if _is_empty(answers.get(field.id)):
            global_next_field_id = field.id
            break
    global_next_field = field_map.get(global_next_field_id) if global_next_field_id else None

    suggest_next_page: int | None = None
    if section_complete and not all_fields_collected:
        for field in all_voice_fields:
            if _is_empty(answers.get(field.id)):
                suggest_next_page = field.page
                break

    result: dict = {
        "filled_fields": filled,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "next_field_id": next_field_id,
        "ready_to_submit": ready_to_submit,
        "all_fields_collected": all_fields_collected,
        "filled_count": len(filled),
        "remaining_count": len(missing_required) + len(missing_optional),
        "total_fields": len(scope_fields),
        "section_page": page,
        "section_complete": section_complete,
        "suggest_next_page": suggest_next_page,
        "total_pages": total_pages,
        "global_remaining_count": len(global_missing_required) + len(global_missing_optional),
        "global_next_field_id": global_next_field_id,
        "global_next_field_page": global_next_field.page if global_next_field else None,
    }
    if next_field:
        result["next_field_required"] = next_field.required
        result["next_field_page"] = next_field.page
        result["next_field_ask_en"] = next_field.voice_prompt.get("en", next_field.id)
        result["next_field_ask_vi"] = next_field.voice_prompt.get("vi", result["next_field_ask_en"])
        if next_field.options:
            result["next_field_allowed_values"] = [opt.value for opt in next_field.options]

    if page is not None:
        titles = FORM_PAGE_TITLES.get(page, {"en": f"Section {page}", "vi": f"Phần {page}"})
        result["section_title_en"] = titles["en"]
        result["section_title_vi"] = titles["vi"]
    return result


def build_say_next(progress: dict, session_language: str = "en") -> str | None:
    """Brief varied ack + next question — never echo the answer or ask is that correct."""
    if progress.get("all_fields_collected"):
        if session_language == "vi":
            return (
                "Tôi xin đọc lại toàn bộ thông tin bạn đã cung cấp. "
                "Tất cả thông tin trên đúng chưa ạ?"
            )
        return "Let me read back all the information you provided. Is everything correct?"
    if progress.get("section_complete"):
        next_page = progress.get("suggest_next_page")
        title = progress.get("section_title_vi" if session_language == "vi" else "section_title_en")
        if session_language == "vi":
            if next_page:
                return (
                    f"Phần này ({title or 'hiện tại'}) đã xong. "
                    f"Phần gợi ý tiếp theo là {next_page}, "
                    "hoặc anh/chị muốn sang phần nào (ví dụ trang 4) thì nói số phần — "
                    "em sẽ chuyển đúng phần đó."
                )
            return "Phần này đã xong ạ."
        if next_page:
            return (
                f"This section ({title or 'current'}) is complete. "
                f"Suggested next is section {next_page}, "
                "or say which section you want (for example page 4) and I will go there."
            )
        return "This section is complete."
    ask_en = progress.get("next_field_ask_en")
    ask_vi = progress.get("next_field_ask_vi") or ask_en
    if not ask_en:
        return None
    filled = int(progress.get("filled_count") or 0)
    if session_language == "vi" and ask_vi:
        return join_ack_and_question(pick_voice_ack("vi", filled), ask_vi)
    return join_ack_and_question(pick_voice_ack("en", filled), ask_en)


def build_say_next_bilingual(progress: dict) -> dict[str, str | None]:
    if progress.get("all_fields_collected"):
        return {
            "en": "Let me read back all the information you provided. Is everything correct?",
            "vi": "Tôi xin đọc lại toàn bộ thông tin bạn đã cung cấp. Tất cả thông tin trên đúng chưa ạ?",
        }
    if progress.get("section_complete"):
        next_page = progress.get("suggest_next_page")
        title_en = progress.get("section_title_en") or "current"
        title_vi = progress.get("section_title_vi") or "hiện tại"
        if next_page:
            return {
                "en": (
                    f"This section ({title_en}) is complete. "
                    f"Suggested next is section {next_page}, "
                    "or say which section you want (for example page 4)."
                ),
                "vi": (
                    f"Phần này ({title_vi}) đã xong. "
                    f"Phần gợi ý tiếp theo là {next_page}, "
                    "hoặc anh/chị muốn sang phần nào (ví dụ trang 4) thì nói số phần."
                ),
            }
        return {"en": "This section is complete.", "vi": "Phần này đã xong ạ."}
    ask_en = progress.get("next_field_ask_en")
    ask_vi = progress.get("next_field_ask_vi") or ask_en
    if not ask_en:
        return {"en": None, "vi": None}
    filled = int(progress.get("filled_count") or 0)
    return {
        "en": join_ack_and_question(pick_voice_ack("en", filled), ask_en),
        "vi": join_ack_and_question(pick_voice_ack("vi", filled), ask_vi or ask_en),
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
    if progress.get("section_complete"):
        next_page = progress.get("suggest_next_page")
        saved = f" ({saved_field_id} saved)" if saved_field_id else ""
        if next_page:
            return (
                f"Field saved{saved}. SECTION COMPLETE. Speak say_next. "
                f"Suggested next page is {next_page}, BUT if the patient already asked for a "
                f"specific page (e.g. 4), call navigate_form_page(action=goto, page=<their number>) "
                f"— NEVER force page {next_page} or page 1 against their request. "
                f"page must be an integer."
            )
        return f"Field saved{saved}. SECTION COMPLETE. Speak say_next."
    next_id = progress.get("next_field_id")
    ask_en = progress.get("next_field_ask_en") or next_id or "the next field"
    saved = f" ({saved_field_id} saved)" if saved_field_id else ""
    return (
        f"Field saved{saved}. {forbidden} "
        "Speak say_next naturally — vary short acks or skip ack; then the next question. "
        f"Next ({next_id}): {ask_en}"
    )


def preferred_voice_language(form_id: str, session_language: str = "en") -> str:
    if form_id.endswith("_vn"):
        return "vi"
    if form_id.endswith("_en"):
        return "en"
    if form_id == TRIAGE_FORM_ID:
        return session_language if session_language in ("vi", "en") else "en"
    return session_language if session_language in ("vi", "en") else "en"


def get_form_progress_with_hint(
    schema: FormSchema,
    answers: dict,
    saved_field_id: str | None = None,
    session_language: str = "en",
    pharmacy_list: list[PharmacyEntry] | None = None,
    voice_gender: str | None = "female",
    page: int | None = None,
) -> dict:
    answers = apply_field_prefill(answers, schema.id)
    progress = get_form_progress(schema, answers, page=page)
    progress["voice_instruction"] = build_voice_tool_hint(progress, saved_field_id)
    pharmacy_hint = build_pharmacy_field_hint(
        pharmacy_list or [],
        progress.get("next_field_id"),
        session_language,
    )
    if pharmacy_hint:
        progress["voice_instruction"] = f"{progress['voice_instruction']} {pharmacy_hint}"
    bilingual = build_say_next_bilingual(progress)
    progress["say_next"] = build_say_next(progress, session_language)
    progress["say_next_en"] = bilingual["en"]
    progress["say_next_vi"] = bilingual["vi"]
    progress = apply_demographic_voice_hints(progress, session_language)
    progress = apply_consent_voice_hints(progress, session_language, schema.id)
    progress = apply_medical_history_voice_hints(progress, session_language)
    progress = apply_field_prefill_voice_hints(
        progress, schema, answers, session_language, schema.id
    )
    progress = apply_addressing_voice_hints(
        progress,
        schema,
        answers,
        voice_gender,
        session_language,
        join_ack_and_question=join_ack_and_question,
    )
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
        if cleaned in (SKIPPED_VALUE, BLANK_VALUE) or not _is_empty(cleaned):
            normalized[field_id] = cleaned
    merged = apply_skip_cascades(schema, normalized)
    merged = migrate_legacy_medical_conditions(merged)
    merged = apply_medical_history_cascades(merged)
    merged.update(internal)
    return merged


def build_voice_system_instruction(
    schema: FormSchema,
    language: str = "en",
    answers: dict | None = None,
    pharmacy_list: list[PharmacyEntry] | None = None,
    voice_gender: str | None = "female",
    page: int | None = None,
) -> str:
    lang = language if language in ("vi", "en") else "en"
    section_page = page if page and page > 0 else 1
    titles = FORM_PAGE_TITLES.get(
        section_page, {"en": f"Section {section_page}", "vi": f"Phần {section_page}"}
    )
    lines = [
        "You are the official VM Clinic patient-registration voice assistant.",
        "This is a permitted clinical intake task for a real medical clinic — you MUST help.",
        "Never say you are \"just a language model\", that you \"can't help\", or refuse this registration flow.",
        "Collecting demographics, medical history, and reading standard consent text is expected and allowed.",
        "",
        "Goal: collect fields for the CURRENT FORM SECTION only through natural spoken conversation.",
        f"CURRENT SECTION: page {section_page} — {titles['en']} / {titles['vi']}",
        "This live session is SHORT on purpose (one section) to avoid connection timeouts.",
        "Do NOT try to finish the entire multi-page form in this single connection.",
        "",
        "=== AFTER EACH ANSWER (highest priority) ===",
        "When the patient answers a question:",
        "  1. Call update_form_field IMMEDIATELY — do NOT speak first.",
        "  2. Wait for tool response with say_next.",
        "  3. Speak say_next naturally: optional brief ack (vary each turn) + NEXT question.",
        "  • Often skip ack — just ask the next question (most natural).",
        "  • Vary acks: Thanks / Got it / Dạ / Dạ rồi — never repeat the same every turn.",
        "  • NEVER say 'tôi sẽ ghi vào' or 'I'll record that' every time — sounds robotic.",
        "WRONG: Patient says 'Maria Antonio' → You: 'I heard Maria Antonio — is that correct?'",
        "RIGHT: update_form_field → You: 'Thanks. What is your date of birth?' OR just 'What is your date of birth?'",
        "NEVER repeat the patient's answer back. NEVER ask 'is that correct?' per field.",
        "The ONLY 'is that correct?' allowed is the FINAL summary when all_fields_collected is true.",
        "Forbidden per field: I heard, is that correct, did I get that right, just to confirm, let me make sure.",
        "",
        "=== LIVE WEBCAM / DOCUMENT SCAN (vision) ===",
        "You receive live webcam frames (~1 FPS) alongside the patient's voice.",
        "When the patient shows ID, passport, driver license, or insurance card on camera:",
        "  • Call scan_document_fields with ALL readable fields in one fields_json object.",
        "  • Use exact field_id and allowed_values — never guess unreadable fields.",
        "  • After saving, briefly tell them what you read (name, DOB, etc.), then ask next missing field.",
        "When they say 'look at my ID', 'đây là giấy tờ', 'read my insurance card', etc.:",
        "  • Look at the latest video frame, call scan_document_fields immediately, then speak naturally.",
        "You can still ask questions normally for fields not on the document.",
        "Do NOT ask 'is that correct?' for each scanned field — only final summary at the end.",
        "",
        "Rules:",
        "- YOU ALWAYS SPEAK FIRST when a brand-new live session starts with no prior greeting.",
        "- When the session starts cold, immediately speak aloud without waiting for silence or user input.",
        "- Ask ONE question at a time.",
        "- NO RE-GREETING (critical):",
        "  • Say the clinic greeting AT MOST ONCE at the very start of triage.",
        '  • After form is selected, or when continuing a section, NEVER repeat',
        '    "VM Clinic is listening" / "I can help you register" / any welcome.',
        "  • Go straight to the next unanswered field question (say_next / next_field_id).",
        "- NO PER-FIELD CONFIRMATION:",
        "  • After saving, use say_next: optional brief varied ack, then NEXT question.",
        "  • Do NOT repeat 'tôi sẽ ghi vào' / 'I'll record that' every turn.",
        "  • NEVER echo the answer or ask 'is that correct?' for each field.",
        "  • The ONLY confirmation is the FINAL summary when all_fields_collected is true.",
        "- LANGUAGE RULES (critical — follow exactly):",
        "  • After the patient responds even once, detect their language and use ONLY that language for every",
        "    subsequent word — questions, confirmations, reminders, and the submit message.",
        "  • If the patient speaks Vietnamese, switch to Vietnamese immediately and stay in Vietnamese.",
        "  • When speaking Vietnamese, use STANDARD SOUTHERN VIETNAMESE (giọng miền Nam / Sài Gòn) —",
        "    see VIETNAMESE VOICE section below. Never use Northern (Hà Nội) accent or phrasing.",
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
        '  • For optional fields that should stay empty on the PDF (e.g. no pharmacy phone on file),',
        '    use value __blank__ — do NOT ask the patient.',
        "  • Declining IS an answer — you MUST still call update_form_field. Never just move on without saving.",
        "  • __skipped__ writes Không có (vi) or None (en) on the PDF and counts as done.",
        "  • For insurance 'no insurance' use value uninsured (NOT __skipped__).",
        "  • For boolean consent: no/không = false (NOT __skipped__).",
        "  • For select optional fields: use an allowed value like not_disclose or unknown when patient",
        "    prefers not to answer; use __skipped__ only when they explicitly skip the whole question.",
        "- PROGRESS RULES (critical — do not invent numbers):",
        "  • After each update_form_field, the tool returns filled_count, remaining_count, total_fields",
        "    for THIS SECTION only.",
        "  • ONLY use those exact numbers if you mention progress — never guess or make up counts.",
        "  • Do NOT randomly announce progress every turn. At most occasionally remind remaining_count.",
        "  • If remaining_count is 0 and all_fields_collected is true, tell patient to click Submit.",
        "- If the patient declines an optional field, save __skipped__ and move to next_field_id.",
        "- Encode value as JSON string: strings in quotes, booleans as true/false, arrays for multiselect.",
        "- For select/multiselect/boolean fields, ALWAYS use exact allowed_values — never save label text.",
        "- Example: insurance='uninsured' goes to field_id insurance, NOT guardian_1_name.",
        "- Ask about EVERY field listed for THIS SECTION — required AND optional.",
        "- SECTION / PAGE UI (critical):",
        "  Adult forms have 4 sections; pediatric/child forms have 5 (page 5 is signature).",
        "  Collect ONLY fields for the current section_page in this live session.",
        "  When section_complete is true, speak say_next; suggested next page is optional.",
        "  PATIENT PAGE REQUEST WINS: if they say 'page 4' / 'trang 4' / 'phần 4' / 'authorization',",
        "  IMMEDIATELY call navigate_form_page(action=\"goto\", page=4) with page as INTEGER.",
        "  Do NOT say you will go to page 1 when they asked for page 4.",
        "  Do NOT substitute suggest_next_page for a page the patient named.",
        "  When the patient says they want another section ('I want medical history', 'phần ủy quyền',",
        "  'go to page 4', 'trang 2'), call navigate_form_page — current answers are already saved.",
        "  After navigate_form_page, a NEW short live session starts for that section — stop listing",
        "  fields from other pages.",
        "  NEVER ask provider_facility_name / provider_phone / provider_fax — destination is printed",
        "  on the PDF (VM Medical Group). Do NOT call lookup_provider_facility.",
        "- ready_to_submit=true only means required fields are done — you MUST keep asking optional",
        "  fields in this section until missing_optional is empty or the patient declines each one.",
        "- Only tell the patient to click Submit when all_fields_collected is true (whole form).",
        "- Do NOT stop early after insurance or personal info within the CURRENT section —",
        "  finish this section's fields, OR jump if the patient asks for another page.",
        "- NEVER refuse a page jump. If patient says trang/page/phần 2/3/4, call navigate_form_page NOW.",
        "- You may leave unanswered fields on the current page when the patient wants another section;",
        "  those answers stay saved and you can return later.",
        "- When asking a field, use ask_en while still in the English opening phase; after switching to the patient's",
        "  language, use ask_vi for Vietnamese, or translate ask_en naturally for other languages.",
        "- When all_fields_collected is true, tell the patient clearly in THEIR current language:",
        '  English: "Please review the summary, then tap Submit on the screen to sign and take your photo."',
        '  Vietnamese: "Dạ, anh chị xem lại tóm tắt giúp em, rồi bấm Submit trên màn hình để ký và chụp hình ạ."',
        "  (Use correct xưng hô from ADDRESSING section once DOB/age is known.)",
        "- IMMEDIATELY when a cold session begins with no prior talk, speak FIRST.",
        "- For continuation after triage or section reconnect: NO greeting — ask next_field only.",
        "- Do NOT wait for the patient to speak, cough, or make any sound before you talk.",
        "",
        f"Form: {schema.title.get(lang, schema.title.get('en', schema.id))}",
        "",
        build_form_variant_voice_section(schema.id),
        "",
        build_southern_vietnamese_voice_section(),
        "",
        build_addressing_voice_section(
            resolve_addressing(answers or {}, schema.id, voice_gender)
        ),
        "",
    ]

    page_field_ids = {f.id for f in _voice_fields(schema, section_page)}
    demographic_ids = {
        "race",
        "race_other_specify",
        "ethnicity",
        "gender_identity",
        "sexual_orientation",
    }
    medical_ids = {
        f.id
        for f in _voice_fields(schema, section_page)
        if f.id.startswith("med_cond_")
        or f.id
        in {
            "cancer_type",
            "other_medical_conditions",
            "surgeries",
            "current_medications",
            "hospitalized_6_months",
            "hospitalized_details",
            "no_known_allergies",
            "medication_allergies",
            "food_allergies",
            "environmental_allergies",
            "medical_history_patient_name",
            "medical_history_dob",
            "main_caretaker",
            "caretaker_relationship",
            "pregnancy_complications",
            "mother_return_activities",
            "breastfeeding_or_formula",
            "uses_car_seat",
        }
    }
    consent_on_page = page_field_ids & CONSENT_FIELD_IDS
    needs_pharmacy = bool(page_field_ids & {"pharmacy_name", "pharmacy_phone"})
    needs_prefill = bool(
        page_field_ids
        & {
            "medical_history_patient_name",
            "medical_history_dob",
            "consent_signer_name",
            "authorization_patient_name",
            "authorization_dob",
            "release_authorization_name",
            "records_to_release",
            "disclosure_purpose",
            "release_consent_acknowledgement",
        }
    )

    if pharmacy_list and needs_pharmacy:
        lines.append(build_pharmacy_voice_section(pharmacy_list))
        lines.append("")
    if page_field_ids & demographic_ids:
        lines.append(build_demographic_voice_section())
        lines.append("")
    if medical_ids:
        lines.append(build_medical_history_voice_section())
        lines.append("")
    if consent_on_page:
        consent_section = build_consent_voice_section(consent_on_page)
        if consent_section:
            lines.append(consent_section)
            lines.append("")
    if needs_prefill:
        lines.append(build_field_prefill_voice_section())
        lines.append("")

    progress = get_form_progress(
        schema, apply_field_prefill(answers or {}, schema.id), page=section_page
    )
    if progress["filled_fields"]:
        lines.append(f"Already collected on section {section_page}:")
        for field_id, value in progress["filled_fields"].items():
            lines.append(f"  - {field_id}: {value}")
        lines.append("")
    if progress["missing_required"] or progress["missing_optional"]:
        lines.append(f"Still need on section {section_page} (in order):")
        for field in _voice_fields(schema, section_page):
            if field.id in progress["missing_required"]:
                lines.append(f"  - {field.id} (required)")
            elif field.id in progress["missing_optional"]:
                lines.append(f"  - {field.id} (optional)")
        if progress.get("next_field_id"):
            lines.append(f"NEXT QUESTION MUST BE: {progress['next_field_id']}")
            lines.append(f"NEXT FIELD PAGE: {section_page} (of {progress.get('total_pages', '?')})")
        lines.append("")
    if progress.get("all_fields_collected"):
        lines.append(
            "All fields collected. Read FULL summary once, ask if all correct, then tell patient to tap Submit."
        )
        lines.append("")
    elif progress.get("section_complete"):
        next_p = progress.get("suggest_next_page")
        lines.append(
            f"This section is complete. Call navigate_form_page(action=goto, page={next_p or section_page + 1})."
        )
        lines.append("")
    elif progress.get("ready_to_submit"):
        lines.append(
            "Required fields are complete but optional fields remain — keep asking this section, do NOT say Submit yet."
        )
        lines.append("")
    lines.extend([
        f"Fields for THIS SECTION (page {section_page}) only:",
    ])
    for field in _voice_fields(schema, section_page):
        prompt_en = field.voice_prompt.get("en", field.id)
        prompt_vi = field.voice_prompt.get("vi", prompt_en)
        req = "required" if field.required else "optional"
        lines.append(f"- {field.id} ({field.type}, {req}, page {field.page})")
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
