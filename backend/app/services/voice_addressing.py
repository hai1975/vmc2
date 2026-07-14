"""Vietnamese xưng hô for voicebot — bot voice gender + patient age/gender."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.models import FormSchema
from app.services.form_selector import calculate_age, parse_date_of_birth
from app.services.form_variant import is_pediatric_form

VoiceGender = Literal["female", "male"]

MALE_GENDERS = frozenset({"male", "ftm"})
FEMALE_GENDERS = frozenset({"female", "mtf"})


@dataclass(frozen=True)
class AddressingProfile:
    voice_gender: VoiceGender
    patient_age: int | None
    is_pediatric_form: bool
    patient_gender: str | None
    listener_title: str
    patient_title: str
    bot_self: str
    examples: tuple[str, ...]


def _normalize_voice_gender(value: str | None) -> VoiceGender:
    if str(value or "").strip().lower() == "male":
        return "male"
    return "female"


def _patient_gender_from_answers(answers: dict) -> str | None:
    raw = answers.get("gender_identity")
    if raw in (None, "", "__skipped__", "__blank__"):
        return None
    return str(raw)


def _listener_title_adult(age: int, gender: str | None) -> str:
    if age < 18:
        return "em"
    if age < 40:
        if gender in MALE_GENDERS:
            return "anh"
        if gender in FEMALE_GENDERS:
            return "chị"
        return "anh/chị"
    if age < 55:
        if gender in MALE_GENDERS:
            return "anh"
        if gender in FEMALE_GENDERS:
            return "chị"
        return "anh/chị"
    if age < 70:
        if gender in MALE_GENDERS:
            return "chú"
        if gender in FEMALE_GENDERS:
            return "cô"
        return "chú/cô"
    return "bác"


def _bot_self(voice_gender: VoiceGender, listener_title: str) -> str:
    if voice_gender == "male":
        # Male bot persona: humble "em" with elders; "em" remains natural in Southern clinics.
        if listener_title in ("bác", "chú", "cô", "chú/cô"):
            return "em"
        return "em"
    return "em"


def resolve_addressing(
    answers: dict,
    form_id: str,
    voice_gender: str | None = "female",
) -> AddressingProfile | None:
    """Return None until date of birth is known."""
    dob_raw = answers.get("birthday") or answers.get("dob")
    if not dob_raw:
        return None

    try:
        patient_age = calculate_age(parse_date_of_birth(str(dob_raw)))
    except ValueError:
        return None

    vg = _normalize_voice_gender(voice_gender)
    pediatric = is_pediatric_form(form_id)
    pg = _patient_gender_from_answers(answers)

    if pediatric:
        # DOB is the child's; the speaker is usually parent/guardian — neutral until we know more.
        listener = "anh/chị"
        patient_title = "bé" if patient_age < 6 else "cháu"
        bot = _bot_self(vg, listener)
        examples = (
            f"Dạ {bot} xin {listener} cho biết thêm về {patient_title} ạ.",
            f"Cảm ơn {listener}. {bot} hỏi tiếp ạ.",
        )
    else:
        listener = _listener_title_adult(patient_age, pg)
        patient_title = listener
        bot = _bot_self(vg, listener)
        examples = (
            f"Dạ {bot} xin {listener} cho biết ạ.",
            f"Cảm ơn {listener}. {bot} hỏi tiếp ạ.",
        )

    return AddressingProfile(
        voice_gender=vg,
        patient_age=patient_age,
        is_pediatric_form=pediatric,
        patient_gender=pg,
        listener_title=listener,
        patient_title=patient_title,
        bot_self=bot,
        examples=examples,
    )


def build_addressing_voice_section(profile: AddressingProfile | None) -> str:
    if profile is None:
        return "\n".join(
            [
                "=== XƯNG HÔ (tiếng Việt — chưa có ngày sinh) ===",
                "• Bot giọng nữ: xưng 'em'. Bot giọng nam: xưng 'em'.",
                "• Gọi người đang nói chuyện: 'anh/chị' (trung tính) cho đến khi có ngày sinh.",
                "• Sau khi biết ngày sinh, áp dụng quy tắc XƯNG HÔ trong section cập nhật từ tool.",
            ]
        )

    voice_label = "nữ" if profile.voice_gender == "female" else "nam"
    age_line = f"{profile.patient_age} tuổi" if profile.patient_age is not None else "không rõ"
    gender_line = profile.patient_gender or "chưa hỏi giới tính"

    if profile.is_pediatric_form:
        target = (
            f"Người đang nói (phụ huynh/người giám hộ): '{profile.listener_title}'. "
            f"Bệnh nhi ({age_line}): gọi '{profile.patient_title}' / 'bệnh nhi' — KHÔNG gọi phụ huynh là em."
        )
    else:
        target = f"Bệnh nhân ({age_line}, giới tính: {gender_line}): gọi '{profile.listener_title}'."

    return "\n".join(
        [
            "=== XƯNG HÔ (tiếng Việt — BẮT BUỘC khi nói tiếng Việt) ===",
            f"• Giọng bot: {voice_label} → bot xưng '{profile.bot_self}'.",
            f"• {target}",
            "• Mọi câu hỏi/ xác nhận tiếng Việt PHẢI dùng đúng xưng hô trên — không dùng 'bạn' chung chung.",
            "• Khi đọc ask_vi từ schema, DIỄN ĐẠT LẠI tự nhiên giọng Nam với xưng hô đúng (giữ nguyên ý nghĩa).",
            "• Ví dụ:",
            *(f"  - {ex}" for ex in profile.examples),
            "• Khi gender_identity được lưu, cập nhật anh/chị/cô/chú/bác theo giới tính nếu trước đó dùng anh/chị.",
        ]
    )


def build_addressing_tool_hint(profile: AddressingProfile | None) -> str:
    if profile is None:
        return ""
    return (
        f"ADDRESSING (vi): bot='{profile.bot_self}', listener='{profile.listener_title}', "
        f"patient='{profile.patient_title}'. Rephrase say_next_vi with correct xưng hô."
    )


def adapt_vi_question(text: str, profile: AddressingProfile | None) -> str:
    """Light touch: swap generic 'bạn' for listener/patient titles when profile known."""
    if not profile or not text:
        return text
    out = text
    listener = profile.listener_title
    if profile.is_pediatric_form:
        out = out.replace("của bạn", f"của {profile.patient_title}")
        out = out.replace("Của bạn", f"Của {profile.patient_title}")
        out = out.replace("bạn có", f"{listener} có")
        out = out.replace("Bạn có", f"{listener} có")
    else:
        out = out.replace("của bạn", f"của {listener}")
        out = out.replace("Của bạn", f"Của {listener}")
        out = out.replace("bạn có", f"{listener} có")
        out = out.replace("Bạn có", f"{listener} có")
        out = out.replace("bạn là", f"{listener} là")
        out = out.replace("Bạn là", f"{listener} là")
    return out


def pick_addressed_ack_vi(profile: AddressingProfile | None, filled_count: int) -> str:
    """Short ack with correct bot self-reference."""
    if not profile:
        pool = ("", "Dạ.", "Dạ rồi.", "Ừ ạ,", "Dạ em,")
    else:
        bot = profile.bot_self
        pool = ("", "Dạ.", "Dạ rồi.", f"Dạ {bot},", f"Ừ ạ,")
    index = max(filled_count - 1, 0) % len(pool)
    return pool[index]


def apply_addressing_voice_hints(
    progress: dict,
    schema: FormSchema,
    answers: dict,
    voice_gender: str | None,
    session_language: str,
    *,
    join_ack_and_question,
) -> dict:
    profile = resolve_addressing(answers, schema.id, voice_gender)
    hint = build_addressing_tool_hint(profile)
    if hint:
        progress["voice_instruction"] = f"{progress.get('voice_instruction', '')} {hint}".strip()

    if profile and progress.get("next_field_ask_vi"):
        progress["next_field_ask_vi"] = adapt_vi_question(progress["next_field_ask_vi"], profile)

    if profile and session_language == "vi":
        filled = int(progress.get("filled_count") or 0)
        if progress.get("all_fields_collected"):
            listener = profile.listener_title
            progress["say_next_vi"] = (
                f"Dạ {profile.bot_self} xin {listener} nghe lại toàn bộ thông tin. "
                f"Tất cả thông tin trên đúng chưa ạ?"
            )
            progress["say_next"] = progress["say_next_vi"]
        else:
            ack = pick_addressed_ack_vi(profile, filled)
            ask_vi = progress.get("next_field_ask_vi") or ""
            if ask_vi:
                progress["say_next_vi"] = join_ack_and_question(ack, ask_vi)
                progress["say_next"] = progress["say_next_vi"]

    if profile:
        progress["addressing"] = {
            "bot_self": profile.bot_self,
            "listener_title": profile.listener_title,
            "patient_title": profile.patient_title,
            "patient_age": profile.patient_age,
        }
    return progress
