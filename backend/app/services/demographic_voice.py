"""Two-tier voice prompts for demographic fields — ask 2 main options + other first."""

from typing import TypedDict


class DemographicVoiceConfig(TypedDict):
    primary_ask_en: str
    primary_ask_vi: str
    secondary_ask_en: str
    secondary_ask_vi: str
    primary_values: frozenset[str]


DEMOGRAPHIC_FIELD_IDS = frozenset(
    {
        "race",
        "ethnicity",
        "gender_identity",
        "sexual_orientation",
        "marital_status",
        "employment_status",
    }
)

DEMOGRAPHIC_TWO_TIER: dict[str, DemographicVoiceConfig] = {
    "race": {
        "primary_ask_en": (
            "What is your race — Asian, White, or something else? "
            "You may name more than one if needed."
        ),
        "primary_ask_vi": (
            "Chủng tộc của bạn là Châu Á, Da trắng hay gì khác? "
            "Có thể chọn nhiều nếu cần."
        ),
        "secondary_ask_en": (
            "Which applies: African American, American Indian or Alaska Native, "
            "Native Hawaiian or Pacific Islander, or other race?"
        ),
        "secondary_ask_vi": (
            "Bạn thuộc nhóm nào: Người Mỹ gốc Phi, Người da đỏ bản địa, "
            "Người đảo Thái Bình Dương, hay chủng tộc khác?"
        ),
        "primary_values": frozenset({"asian", "white"}),
    },
    "ethnicity": {
        "primary_ask_en": (
            "What is your ethnicity — Hispanic or Latino, Not Hispanic or Latino, or something else?"
        ),
        "primary_ask_vi": (
            "Dân tộc của bạn là Gốc Tây Ban Nha/La-tinh, Không gốc Tây Ban Nha, hay gì khác?"
        ),
        "secondary_ask_en": "Would that be Unknown, or something else?",
        "secondary_ask_vi": "Là Không rõ, hay mục khác?",
        "primary_values": frozenset({"hispanic", "not_hispanic"}),
    },
    "gender_identity": {
        "primary_ask_en": "What is your gender identity — Male, Female, or something else?",
        "primary_ask_vi": "Giới tính của bạn là Nam, Nữ hay gì khác?",
        "secondary_ask_en": (
            "Please choose: prefer not to disclose, FTM/transgender male, "
            "MTF/transgender female, genderqueer, or other."
        ),
        "secondary_ask_vi": (
            "Xin chọn: Không tiết lộ, Chuyển giới nam (FTM), Chuyển giới nữ (MTF), "
            "Phi nhị phân giới, hay Khác."
        ),
        "primary_values": frozenset({"male", "female"}),
    },
    "sexual_orientation": {
        "primary_ask_en": (
            "What is your sexual orientation — straight, gay or lesbian, or something else?"
        ),
        "primary_ask_vi": (
            "Xu hướng tình dục của bạn là Dị tính, Đồng tính hay gì khác?"
        ),
        "secondary_ask_en": (
            "Please choose: bisexual, don't know, prefer not to disclose, or other."
        ),
        "secondary_ask_vi": (
            "Xin chọn: Song tính, Không biết, Không tiết lộ, hay Khác."
        ),
        "primary_values": frozenset({"straight", "gay_lesbian"}),
    },
    "marital_status": {
        "primary_ask_en": "What is your marital status — single, married, or something else?",
        "primary_ask_vi": "Tình trạng hôn nhân của bạn là Độc thân, Đã kết hôn hay gì khác?",
        "secondary_ask_en": (
            "Please choose: widow, domestic partner, divorced, or other."
        ),
        "secondary_ask_vi": (
            "Xin chọn: Góa, Bạn đời, Ly hôn, hay Khác."
        ),
        "primary_values": frozenset({"single", "married"}),
    },
    "employment_status": {
        "primary_ask_en": (
            "What is your employment status — employed full-time, not employed, or something else?"
        ),
        "primary_ask_vi": (
            "Tình trạng việc làm của bạn là Toàn thời gian, Không đi làm hay gì khác?"
        ),
        "secondary_ask_en": (
            "Please choose: part-time, self-employed, retired, active military duty, or other."
        ),
        "secondary_ask_vi": (
            "Xin chọn: Bán thời gian, Tự kinh doanh, Đã nghỉ hưu, Đang phục vụ quân đội, hay Khác."
        ),
        "primary_values": frozenset({"full_time", "not_employed"}),
    },
}


def build_demographic_voice_section() -> str:
    lines = [
        "=== DEMOGRAPHIC QUESTIONS (two-tier — do NOT list all options first) ===",
        "For race, ethnicity, gender_identity, sexual_orientation, marital_status, employment_status:",
        "• STEP 1: Ask ONLY the primary question (2 main choices + or something else/khác).",
        "• If the patient clearly matches a primary option, save immediately with update_form_field.",
        "• STEP 2: ONLY if they say other/khác/something else/gì khác OR none of the two main fit,",
        "  then read the secondary options from voice_instruction — never upfront.",
        "• Do NOT dump the full checkbox list on the first ask.",
        "• For race (multiselect): Asian+White can be saved together; use secondary only for other races.",
    ]
    for field_id, cfg in DEMOGRAPHIC_TWO_TIER.items():
        lines.append(f"• {field_id} primary (EN): {cfg['primary_ask_en']}")
        lines.append(f"  secondary (EN): {cfg['secondary_ask_en']}")
    return "\n".join(lines)


def apply_demographic_voice_hints(progress: dict, session_language: str = "en") -> dict:
    field_id = progress.get("next_field_id")
    if not field_id or field_id not in DEMOGRAPHIC_TWO_TIER:
        return progress

    cfg = DEMOGRAPHIC_TWO_TIER[field_id]
    lang = session_language if session_language in ("vi", "en") else "en"
    primary = cfg["primary_ask_vi"] if lang == "vi" else cfg["primary_ask_en"]
    secondary = cfg["secondary_ask_vi"] if lang == "vi" else cfg["secondary_ask_en"]

    progress["next_field_ask_en"] = cfg["primary_ask_en"]
    progress["next_field_ask_vi"] = cfg["primary_ask_vi"]
    progress["say_next_en"] = cfg["primary_ask_en"]
    progress["say_next_vi"] = cfg["primary_ask_vi"]
    progress["say_next"] = primary

    tier_hint = (
        f"TWO-TIER field {field_id}: ask primary only first. "
        f"Secondary (use ONLY if patient says other/khác or not a primary option): {secondary}"
    )
    existing = progress.get("voice_instruction") or ""
    progress["voice_instruction"] = f"{existing} {tier_hint}".strip()

    return progress
