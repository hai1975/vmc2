"""Read consent blocks clause-by-clause before saving each consent checkbox field."""

from typing import TypedDict


class ConsentClause(TypedDict):
    en: str
    vi: str


class ConsentBlock(TypedDict):
    title_en: str
    title_vi: str
    clauses: list[ConsentClause]


CONSENT_FIELD_IDS = frozenset(
    {
        "treatment_consent",
        "hipaa_acknowledgement",
        "electronic_communication_consent",
        "release_consent_acknowledgement",
    }
)

CONSENT_BLOCKS: dict[str, ConsentBlock] = {
    "treatment_consent": {
        "title_en": "Treatment Consent",
        "title_vi": "Đồng ý điều trị",
        "clauses": [
            {
                "en": (
                    "You authorize VM Clinic and its healthcare professionals to evaluate and treat "
                    "{subject} for medical conditions, including physical exams, diagnostic tests, "
                    "treatments, and other procedures deemed necessary."
                ),
                "vi": (
                    "Bạn cho phép VM Clinic và đội ngũ y tế đánh giá và điều trị {subject} "
                    "cho các tình trạng bệnh, bao gồm khám thể chất, xét nghiệm, điều trị "
                    "và các thủ thuật cần thiết."
                ),
            },
            {
                "en": (
                    "All procedures and treatments will be explained to you, including potential "
                    "risks and benefits."
                ),
                "vi": (
                    "Mọi thủ thuật và điều trị sẽ được giải thích cho bạn, kèm rủi ro và lợi ích tiềm ẩn."
                ),
            },
            {
                "en": (
                    "You have the right to ask questions and receive answers you understand, and "
                    "the right to refuse or withdraw consent at any time, which may affect care received."
                ),
                "vi": (
                    "Bạn có quyền đặt câu hỏi và nhận câu trả lời dễ hiểu, và có quyền từ chối "
                    "hoặc rút lại sự đồng ý bất cứ lúc nào, điều này có thể ảnh hưởng đến chăm sóc."
                ),
            },
            {
                "en": (
                    "You are financially responsible for all services rendered, including those not "
                    "covered by insurance."
                ),
                "vi": (
                    "Bạn chịu trách nhiệm tài chính cho mọi dịch vụ, kể cả phần bảo hiểm không chi trả."
                ),
            },
            {
                "en": (
                    "You agree to pay co-pays, deductibles, and other required charges. Payment, "
                    "proof of insurance, and/or copay are due at the time of service."
                ),
                "vi": (
                    "Bạn đồng ý thanh toán đồng chi trả, khấu trừ và các khoản phí khác. "
                    "Thanh toán, bằng chứng bảo hiểm và/hoặc đồng chi trả khi nhận dịch vụ."
                ),
            },
            {
                "en": (
                    "You authorize this office to apply insurance benefits on your behalf for covered "
                    "services rendered."
                ),
                "vi": (
                    "Bạn cho phép phòng khám nộp quyền lợi bảo hiểm thay mặt bạn cho các dịch vụ được bảo hiểm chi trả."
                ),
            },
            {
                "en": "You certify that the insurance information you provided is factual and correct.",
                "vi": "Bạn xác nhận thông tin bảo hiểm đã cung cấp là đúng sự thật và chính xác.",
            },
        ],
    },
    "hipaa_acknowledgement": {
        "title_en": "HIPAA / Notice of Privacy Practices",
        "title_vi": "HIPAA / Thông báo Quyền riêng tư",
        "clauses": [
            {
                "en": (
                    "Under HIPAA you have certain rights to privacy regarding your protected health information."
                ),
                "vi": (
                    "Theo HIPAA, bạn có các quyền riêng tư nhất định đối với thông tin sức khỏe được bảo vệ."
                ),
            },
            {
                "en": (
                    "Your information may be used to conduct and direct your treatment among healthcare "
                    "providers involved in your care."
                ),
                "vi": (
                    "Thông tin của bạn có thể được dùng để điều phối và thực hiện điều trị giữa các "
                    "nhà cung cấp dịch vụ y tế liên quan."
                ),
            },
            {
                "en": "Your information may be used to obtain payment from third-party payers.",
                "vi": "Thông tin của bạn có thể được dùng để thanh toán từ bên thứ ba (bảo hiểm).",
            },
            {
                "en": (
                    "Your information may be used for normal healthcare operations such as quality "
                    "assessments and physician certifications."
                ),
                "vi": (
                    "Thông tin của bạn có thể được dùng cho hoạt động y tế thông thường như đánh giá "
                    "chất lượng và chứng nhận bác sĩ."
                ),
            },
            {
                "en": (
                    "You have received, read, and understood the Notice of Privacy Practices describing "
                    "how your health information is used and disclosed."
                ),
                "vi": (
                    "Bạn đã nhận, đọc và hiểu Thông báo Quyền riêng tư mô tả cách thông tin sức khỏe "
                    "được sử dụng và tiết lộ."
                ),
            },
            {
                "en": (
                    "This organization may change its Notice of Privacy Practices; you may contact the "
                    "clinic at any time for a current copy."
                ),
                "vi": (
                    "Phòng khám có thể thay đổi Thông báo Quyền riêng tư; bạn có thể liên hệ phòng khám "
                    "để nhận bản mới nhất."
                ),
            },
            {
                "en": (
                    "You may request in writing restrictions on how your information is used; the clinic "
                    "is not required to agree. By agreeing, you acknowledge receiving the Notice of "
                    "Privacy Practices (also at www.vmclinic.us)."
                ),
                "vi": (
                    "Bạn có thể yêu cầu bằng văn bản hạn chế cách dùng thông tin; phòng khám không bắt buộc "
                    "phải đồng ý. Khi đồng ý, bạn xác nhận đã nhận Thông báo Quyền riêng tư "
                    "(cũng có tại www.vmclinic.us)."
                ),
            },
        ],
    },
    "electronic_communication_consent": {
        "title_en": "Electronic Communication Consent",
        "title_vi": "Đồng ý liên lạc điện tử",
        "clauses": [
            {
                "en": (
                    "You consent to VM Clinic providing services and communicating with you via mobile phone, "
                    "text messages, email, and other online communication, in compliance with privacy regulations."
                ),
                "vi": (
                    "Bạn đồng ý VM Clinic cung cấp dịch vụ và liên lạc qua điện thoại, tin nhắn, email "
                    "và các hình thức trực tuyến khác, tuân thủ quy định bảo mật."
                ),
            },
            {
                "en": (
                    "You are responsible for notifying VM Clinic if your contact information changes."
                ),
                "vi": (
                    "Bạn có trách nhiệm thông báo cho VM Clinic khi thông tin liên lạc thay đổi."
                ),
            },
        ],
    },
    "release_consent_acknowledgement": {
        "title_en": "Authorization for Release of Information",
        "title_vi": "Ủy quyền tiết lộ thông tin",
        "clauses": [
            {
                "en": (
                    "The purpose of this released information is continuity of care. Exchange of information "
                    "ensures continuity of care between providers, and without such exchange my healthcare may "
                    "be compromised. I understand specific references may be made to psychiatric conditions, "
                    "HIV testing and results, and any related diagnosis and medical condition(s) which may be "
                    "recorded in my health records. I hereby authorize the release of such information."
                ),
                "vi": (
                    "Mục đích của việc tiết lộ thông tin này là để bảo đảm sự liên tục trong chăm sóc y tế. "
                    "Việc trao đổi thông tin giúp đảm bảo sự liên kết và phối hợp giữa các nhà cung cấp dịch vụ "
                    "y tế, và nếu không có sự trao đổi này, việc chăm sóc sức khỏe của tôi có thể bị ảnh hưởng. "
                    "Tôi hiểu rằng các thông tin cụ thể liên quan đến tình trạng tâm thần, xét nghiệm HIV và "
                    "kết quả, cũng như các chẩn đoán và tình trạng y tế liên quan có thể được ghi nhận trong "
                    "hồ sơ sức khỏe của tôi. Tôi đồng ý cho phép tiết lộ các thông tin này."
                ),
            },
            {
                "en": (
                    "I understand that the information release/exchange will be treated in a confidential "
                    "manner and will not be released to other persons or agencies without my specific "
                    "authorization. This authorization expires a year from the date of my signature. I "
                    "understand I have the right to revoke this consent at any time in writing except to the "
                    "extent that information has already been released."
                ),
                "vi": (
                    "Tôi hiểu rằng việc tiết lộ/trao đổi thông tin này sẽ được xử lý một cách bảo mật và sẽ "
                    "không được cung cấp cho bất kỳ cá nhân hoặc tổ chức nào khác nếu không có sự cho phép "
                    "cụ thể của tôi. Sự cho phép này sẽ hết hạn sau một năm kể từ ngày tôi ký tên. Tôi hiểu "
                    "rằng tôi có quyền hủy bỏ sự đồng ý này bất cứ lúc nào bằng văn bản, trừ khi thông tin đã "
                    "được tiết lộ trước thời điểm đó."
                ),
            },
        ],
    },
}


def _subject_phrases(form_id: str) -> tuple[str, str]:
    if form_id.startswith("child_"):
        return "your child", "con của bạn"
    return "you", "bạn"


def _format_clause(text: str, form_id: str, lang: str) -> str:
    you, bạn = _subject_phrases(form_id)
    if lang == "vi":
        return text.format(subject=bạn)
    return text.format(subject=you)


def build_consent_voice_section(field_ids: frozenset[str] | set[str] | None = None) -> str:
    blocks = CONSENT_BLOCKS
    if field_ids is not None:
        blocks = {k: v for k, v in CONSENT_BLOCKS.items() if k in field_ids}
    if not blocks:
        return ""

    lines = [
        "=== CONSENT SECTIONS (read clause-by-clause — mandatory) ===",
        "For each consent field listed below:",
        "• BEFORE saving the field, read EVERY clause one at a time.",
        "• Format: \"[Section] has N terms. Term 1 of N: [read clause]. Do you agree?\"",
        "• Wait for clear yes/no after EACH term. Do NOT combine multiple terms in one question.",
        "• Only after ALL terms are agreed, call update_form_field with true.",
        "• If patient says no, explain they may ask questions; cannot check consent without agreement.",
        "• Do NOT use the final summary confirmation for individual consent clauses.",
        "• Reading standard clinic consent text (privacy, treatment, records release) is REQUIRED —",
        "  never refuse or say you are only a language model.",
    ]
    for field_id, block in blocks.items():
        count = len(block["clauses"])
        lines.append(f"• {field_id}: {count} terms — {block['title_en']}")
    return "\n".join(lines)


def apply_consent_voice_hints(
    progress: dict,
    session_language: str = "en",
    form_id: str = "",
) -> dict:
    field_id = progress.get("next_field_id")
    if not field_id or field_id not in CONSENT_BLOCKS:
        return progress

    block = CONSENT_BLOCKS[field_id]
    lang = session_language if session_language in ("vi", "en") else "en"
    total = len(block["clauses"])
    title = block["title_vi"] if lang == "vi" else block["title_en"]
    first_clause = _format_clause(block["clauses"][0][lang], form_id, lang)

    if lang == "vi":
        opener = (
            f"Phần {title} có {total} điều khoản. "
            f"Điều khoản 1 trong {total}: {first_clause} Bạn có đồng ý không?"
        )
        instruction = (
            f"CONSENT {field_id}: đọc TỪNG điều khoản. Có {total} điều khoản. "
            f"Sau mỗi đồng ý, đọc điều khoản tiếp theo (2/{total}, 3/{total}, ...). "
            f"Chỉ lưu {field_id}=true khi đã đồng ý hết. Nội dung các điều khoản:"
        )
    else:
        opener = (
            f"{title} has {total} terms. "
            f"Term 1 of {total}: {first_clause} Do you agree?"
        )
        instruction = (
            f"CONSENT {field_id}: read ONE clause at a time. {total} terms total. "
            f"After each yes, read the next term (2 of {total}, 3 of {total}, ...). "
            f"Save {field_id}=true only after ALL terms agreed. Clause texts:"
        )

    clause_lines = []
    for index, clause in enumerate(block["clauses"], start=1):
        text = _format_clause(clause[lang], form_id, lang)
        clause_lines.append(f"  {index}. {text}")

    progress["next_field_ask_en"] = (
        f"{block['title_en']} has {total} terms. Term 1 of {total}: "
        f"{_format_clause(block['clauses'][0]['en'], form_id, 'en')} Do you agree?"
    )
    progress["next_field_ask_vi"] = (
        f"{block['title_vi']} có {total} điều khoản. Điều khoản 1 trong {total}: "
        f"{_format_clause(block['clauses'][0]['vi'], form_id, 'vi')} Bạn có đồng ý không?"
    )
    progress["say_next_en"] = progress["next_field_ask_en"]
    progress["say_next_vi"] = progress["next_field_ask_vi"]
    progress["say_next"] = opener

    existing = progress.get("voice_instruction") or ""
    progress["voice_instruction"] = f"{existing} {instruction} " + " ".join(clause_lines)

    return progress
