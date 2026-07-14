"""Generate form-en.json and form-vn.json from shared field definitions."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
PAGE_H = 792.0


def y(top: float) -> float:
    return round(PAGE_H - top, 1)


def cb(top: float, left: float = 36.0) -> dict:
    return {"x": left, "y": y(top)}


def txt(top: float, left: float = 120.0, **extra) -> dict:
    meta = {"x": left, "y": y(top)}
    meta.update(extra)
    return meta


def line(label_top: float, x: float, drop: float = 12.0, **extra) -> dict:
    """Blank input line below a label row (fitz top coords from form_en.pdf)."""
    return txt(label_top + drop, x, **extra)


def _page1_personal_coords(*, pediatric: bool) -> dict[str, dict]:
    """Fit-calibrated overlay positions for page-1 personal fields."""
    if pediatric:
        return {
            "patient_name": txt(135, 175, maxLength=100),
            "birthday": txt(155, 100),
            "ssn": txt(155, 410),
            "guardian_1_name": txt(176, 255),
            "guardian_1_relationship": txt(176, 470),
            "guardian_2_name": txt(197, 255),
            "guardian_2_relationship": txt(197, 470),
            "home_address": txt(218, 130),
            "phone": txt(238, 145),
            "email": txt(238, 330),
        }
    return {
        "patient_name": txt(133, 175, maxLength=100),
        "birthday": txt(153, 100),
        "ssn": txt(153, 410),
        "home_address": txt(174, 130),
        "phone": txt(195, 145),
        "email": txt(195, 375),
    }


def _page1_checkbox_layout(*, pediatric: bool) -> dict[str, dict]:
    """Checkbox rows differ on child form (extra guardian rows push content down)."""
    if pediatric:
        return {
            "insurance": {
                "medi_cal": cb(230, 108), "ppo": cb(230, 216),
                "hmo": cb(230, 324), "uninsured": cb(230, 432),
            },
            "race": {
                "asian": cb(260, 108), "white": cb(260, 216), "african_american": cb(260, 324),
                "native_american": cb(276, 108), "pacific_islander": cb(292, 108), "other": cb(276, 360),
            },
            "ethnicity": {
                "hispanic": cb(322, 108), "not_hispanic": cb(322, 288), "unknown": cb(322, 504),
            },
            "gender_identity": {
                "male": cb(352, 108), "female": cb(352, 180), "not_disclose": cb(352, 252),
                "other": cb(352, 396), "ftm": cb(368, 36), "mtf": cb(383, 36), "genderqueer": cb(399, 36),
            },
            "sexual_orientation": {
                "gay_lesbian": cb(429, 144), "straight": cb(429, 432), "bisexual": cb(445, 36),
                "unknown": cb(445, 144), "not_disclose": cb(445, 252), "other": cb(445, 432),
            },
            "pharmacy_name": line(461, 180),
            "pharmacy_phone": line(461, 430),
            "treatment_consent": cb(501, 36),
            "race_other_specify": txt(276, 400),
        }
    return {
        "insurance": {
            "medi_cal": cb(190, 108), "ppo": cb(190, 216),
            "hmo": cb(190, 324), "uninsured": cb(190, 432),
        },
        "race": {
            "asian": cb(206, 108), "white": cb(206, 216), "african_american": cb(206, 324),
            "native_american": cb(222, 108), "pacific_islander": cb(238, 108), "other": cb(222, 360),
        },
        "ethnicity": {
            "hispanic": cb(268, 108), "not_hispanic": cb(268, 288), "unknown": cb(268, 504),
        },
        "gender_identity": {
            "male": cb(285, 108), "female": cb(285, 180), "not_disclose": cb(285, 252),
            "other": cb(285, 396), "ftm": cb(301, 36), "mtf": cb(316, 36), "genderqueer": cb(332, 36),
        },
        "sexual_orientation": {
            "gay_lesbian": cb(362, 144), "straight": cb(362, 432), "bisexual": cb(378, 36),
            "unknown": cb(378, 144), "not_disclose": cb(378, 252), "other": cb(378, 432),
        },
        "pharmacy_name": line(469, 180),
        "pharmacy_phone": line(469, 430),
        "treatment_consent": cb(509, 36),
        "race_other_specify": txt(222, 400),
    }


def field(
    fid: str,
    ftype: str,
    label_en: str,
    label_vi: str,
    ask_en: str,
    ask_vi: str,
    page: int,
    section: str,
    required: bool = False,
    options: list | None = None,
    validation: dict | None = None,
) -> dict:
    f: dict = {
        "id": fid,
        "type": ftype,
        "label": {"en": label_en, "vi": label_vi},
        "voice_prompt": {"en": ask_en, "vi": ask_vi},
        "required": required,
        "page": page,
        "section": section,
    }
    if options:
        f["options"] = options
    if validation:
        f["validation"] = validation
    return f


YES_NO = [
    {"value": "yes", "label": {"en": "Yes", "vi": "Có"}},
    {"value": "no", "label": {"en": "No", "vi": "Không"}},
]

YES_NO_UNSURE = YES_NO + [{"value": "unsure", "label": {"en": "Unsure", "vi": "Không chắc"}}]

TB_RESULT = [
    {"value": "negative", "label": {"en": "Negative", "vi": "Âm tính"}},
    {"value": "positive", "label": {"en": "Positive", "vi": "Dương tính"}},
    {"value": "unsure", "label": {"en": "Unsure", "vi": "Không chắc"}},
]


def page1_fields(*, pediatric: bool = False) -> list[dict]:
    ins_opts = [
        {"value": "medi_cal", "label": {"en": "Medi-Cal", "vi": "Medi-Cal"}},
        {"value": "ppo", "label": {"en": "PPO", "vi": "PPO"}},
        {"value": "hmo", "label": {"en": "HMO", "vi": "HMO"}},
        {"value": "uninsured", "label": {"en": "Uninsured", "vi": "Không có bảo hiểm"}},
    ]
    race_opts = [
        {"value": "asian", "label": {"en": "Asian", "vi": "Châu Á"}},
        {"value": "white", "label": {"en": "White", "vi": "Da trắng"}},
        {"value": "african_american", "label": {"en": "African American", "vi": "Người Mỹ gốc Phi"}},
        {"value": "native_american", "label": {"en": "American Indian or Alaska Native", "vi": "Người da đỏ bản địa"}},
        {"value": "pacific_islander", "label": {"en": "Native Hawaiian or Pacific Islander", "vi": "Người đảo Thái Bình Dương"}},
        {"value": "other", "label": {"en": "Other race", "vi": "Chủng tộc khác"}},
    ]
    eth_opts = [
        {"value": "hispanic", "label": {"en": "Hispanic or Latino", "vi": "Gốc Tây Ban Nha hoặc La-tinh"}},
        {"value": "not_hispanic", "label": {"en": "Not Hispanic or Latino", "vi": "Không gốc Tây Ban Nha"}},
        {"value": "unknown", "label": {"en": "Unknown", "vi": "Không rõ"}},
    ]
    gender_opts = [
        {"value": "male", "label": {"en": "Male", "vi": "Nam"}},
        {"value": "female", "label": {"en": "Female", "vi": "Nữ"}},
        {"value": "not_disclose", "label": {"en": "Choose not to disclose", "vi": "Chọn không tiết lộ"}},
        {"value": "other", "label": {"en": "Other", "vi": "Khác"}},
        {"value": "ftm", "label": {"en": "FTM / Transgender Male", "vi": "Chuyển giới nam (FTM)"}},
        {"value": "mtf", "label": {"en": "MTF / Transgender Female", "vi": "Chuyển giới nữ (MTF)"}},
        {"value": "genderqueer", "label": {"en": "Genderqueer", "vi": "Phi nhị phân giới"}},
    ]
    orient_opts = [
        {"value": "gay_lesbian", "label": {"en": "Gay or lesbian", "vi": "Đồng tính"}},
        {"value": "straight", "label": {"en": "Straight", "vi": "Dị tính"}},
        {"value": "bisexual", "label": {"en": "Bisexual", "vi": "Song tính"}},
        {"value": "unknown", "label": {"en": "Don't know", "vi": "Không biết"}},
        {"value": "not_disclose", "label": {"en": "Choose not to disclose", "vi": "Chọn không tiết lộ"}},
        {"value": "other", "label": {"en": "Other", "vi": "Khác"}},
    ]
    p1 = _page1_personal_coords(pediatric=pediatric)
    p1cb = _page1_checkbox_layout(pediatric=pediatric)
    fields = [
        field("patient_name", "text", "Patient Name", "Họ và tên bệnh nhân",
              "What is your full legal name?" if not pediatric else "What is the patient's full legal name?",
              "Xin cho biết họ và tên đầy đủ của bạn?" if not pediatric else "Xin cho biết họ và tên đầy đủ của bệnh nhân?",
              1, "personal", True, validation=p1["patient_name"]),
        field("birthday", "date", "Birthday", "Ngày sinh",
              "What is your date of birth?" if not pediatric else "What is the patient's date of birth?",
              "Ngày sinh của bạn là ngày nào?" if not pediatric else "Ngày sinh của bệnh nhân là ngày nào?",
              1, "personal", True, validation=p1["birthday"]),
        field("ssn", "ssn", "SSN", "Số SSN",
              "What is your Social Security Number? Say none if you don't have one.",
              "Số SSN của bạn là gì? Nếu không có, nói không có.",
              1, "personal", False, validation=p1["ssn"]),
    ]
    if pediatric:
        fields.extend([
            field("guardian_1_name", "text", "Legal Guardian 1", "Người giám hộ 1",
                  "Who is the patient's first legal guardian?",
                  "Ai là người giám hộ hợp pháp thứ nhất của bệnh nhân?",
                  1, "personal", False, validation=p1["guardian_1_name"]),
            field("guardian_1_relationship", "text", "Relationship (Guardian 1)", "Mối quan hệ (giám hộ 1)",
                  "What is the guardian's relationship to the patient?",
                  "Mối quan hệ của người giám hộ với bệnh nhân?",
                  1, "personal", False, validation=p1["guardian_1_relationship"]),
            field("guardian_2_name", "text", "Legal Guardian 2", "Người giám hộ 2",
                  "Who is the patient's second legal guardian? Say none if not applicable.",
                  "Ai là người giám hộ hợp pháp thứ hai của bệnh nhân? Nếu không có, nói không có.",
                  1, "personal", False, validation=p1["guardian_2_name"]),
            field("guardian_2_relationship", "text", "Relationship (Guardian 2)", "Mối quan hệ (giám hộ 2)",
                  "What is the second guardian's relationship to the patient?",
                  "Mối quan hệ của người giám hộ thứ hai với bệnh nhân?",
                  1, "personal", False, validation=p1["guardian_2_relationship"]),
        ])
    fields.extend([
        field("home_address", "textarea", "Home Address", "Địa chỉ nhà",
              "What is your home address?", "Địa chỉ nhà của bạn là gì?",
              1, "personal", True, validation=p1["home_address"]),
        field("phone", "phone", "Phone Number", "Số điện thoại",
              "What is your phone number?", "Số điện thoại liên lạc của bạn là gì?",
              1, "personal", True, validation=p1["phone"]),
        field("email", "email", "Email", "Email",
              "What is your email address? Say none if you don't have one.",
              "Địa chỉ email của bạn? Nếu không có, nói không có.",
              1, "personal", False, validation=p1["email"]),
        field("insurance", "select", "Insurance", "Bảo hiểm",
              "What insurance do you have? Medi-Cal, PPO, HMO, or uninsured?",
              "Bạn có loại bảo hiểm nào? Medi-Cal, PPO, HMO, hay không có bảo hiểm?",
              1, "insurance", True, ins_opts, validation={
                  "checkbox_positions": p1cb["insurance"]
              }),
        field("race", "multiselect", "Race", "Chủng tộc",
              "What is your race — Asian, White, or something else?",
              "Chủng tộc của bạn là Châu Á, Da trắng hay gì khác?",
              1, "demographics", False, race_opts, validation={
                  "checkbox_positions": p1cb["race"]
              }),
        field("race_other_specify", "text", "Other race (specify)", "Chủng tộc khác (ghi rõ)",
              "If you selected other race, please specify. Say none if not applicable.",
              "Nếu chọn chủng tộc khác, xin ghi rõ. Nếu không, nói không có.",
              1, "demographics", False, validation=p1cb["race_other_specify"]),
        field("ethnicity", "select", "Ethnicity", "Dân tộc",
              "What is your ethnicity — Hispanic or Latino, Not Hispanic or Latino, Unknown, or something else?",
              "Dân tộc của bạn là Gốc Tây Ban Nha/La-tinh, Không gốc Tây Ban Nha, Không rõ, hay gì khác?",
              1, "demographics", False, eth_opts, validation={
                  "checkbox_positions": p1cb["ethnicity"]
              }),
        field("gender_identity", "select", "Gender Identity", "Giới tính",
              "What is your gender identity — Male, Female, prefer not to disclose, or something else?",
              "Giới tính của bạn là Nam, Nữ, Không tiết lộ, hay gì khác?",
              1, "demographics", False, gender_opts, validation={
                  "checkbox_positions": p1cb["gender_identity"]
              }),
        field("sexual_orientation", "select", "Sexual Orientation", "Xu hướng tình dục",
              "What is your sexual orientation — straight, gay or lesbian, prefer not to disclose, or something else?",
              "Xu hướng tình dục của bạn là Dị tính, Đồng tính, Không tiết lộ, hay gì khác?",
              1, "demographics", False, orient_opts, validation={
                  "checkbox_positions": p1cb["sexual_orientation"]
              }),
        field("pharmacy_name", "text", "Preferred Pharmacy", "Nhà thuốc ưa thích",
              "What is your preferred pharmacy name? Say none if you don't have one.",
              "Nhà thuốc ưa thích tên gì? Nếu không có, nói không có.",
              1, "pharmacy", False, validation=p1cb["pharmacy_name"]),
        field("pharmacy_phone", "phone", "Pharmacy Phone", "SĐT nhà thuốc",
              "What is the pharmacy phone number? Say none if you don't have one.",
              "Số điện thoại nhà thuốc? Nếu không có, nói không có.",
              1, "pharmacy", False, validation=p1cb["pharmacy_phone"]),
        field("treatment_consent", "boolean", "Treatment Consent", "Đồng ý điều trị",
              "Treatment consent — read all 7 terms one by one before saving.",
              "Đồng ý điều trị — đọc từng điều khoản trong 7 điều khoản trước khi lưu.",
              1, "consent", True, validation={**p1cb["treatment_consent"], "render_as_check": True}),
    ])
    return fields


def page2_fields(*, pediatric: bool = False) -> list[dict]:
    cond_checkboxes = {
        "diabetes": cb(179, 36),
        "high_blood_pressure": cb(179, 144),
        "high_cholesterol": cb(179, 288),
        "heart_disease": cb(179, 432),
        "asthma": cb(207, 36),
        "stroke": cb(207, 144),
        "kidney_disease": cb(207, 288),
        "liver_disease": cb(207, 432),
        "seizures": cb(234, 36),
        "cancer": cb(234, 200),
        "mental_health": cb(261, 36),
    }
    conditions = [
        ("diabetes", "Diabetes", "Tiểu đường",
         "Have you ever been diagnosed with diabetes? Yes or no.",
         "Bạn có từng được chẩn đoán tiểu đường không? Có hay không?"),
        ("high_blood_pressure", "High blood pressure", "Cao huyết áp",
         "Have you ever been diagnosed with high blood pressure? Yes or no.",
         "Bạn có từng được chẩn đoán cao huyết áp không? Có hay không?"),
        ("high_cholesterol", "High cholesterol", "Cao mỡ máu",
         "Have you ever been diagnosed with high cholesterol? Yes or no.",
         "Bạn có từng được chẩn đoán cao mỡ máu không? Có hay không?"),
        ("heart_disease", "Heart disease", "Bệnh tim",
         "Have you ever been diagnosed with heart disease? Yes or no.",
         "Bạn có từng được chẩn đoán bệnh tim không? Có hay không?"),
        ("asthma", "Asthma", "Hen suyễn",
         "Have you ever been diagnosed with asthma? Yes or no.",
         "Bạn có từng được chẩn đoán hen suyễn không? Có hay không?"),
        ("stroke", "Stroke", "Đột quỵ",
         "Have you ever had a stroke? Yes or no.",
         "Bạn có từng bị đột quỵ không? Có hay không?"),
        ("kidney_disease", "Kidney disease", "Bệnh thận",
         "Have you ever been diagnosed with kidney disease? Yes or no.",
         "Bạn có từng được chẩn đoán bệnh thận không? Có hay không?"),
        ("liver_disease", "Liver disease", "Bệnh gan",
         "Have you ever been diagnosed with liver disease? Yes or no.",
         "Bạn có từng được chẩn đoán bệnh gan không? Có hay không?"),
        ("seizures", "Seizures", "Động kinh",
         "Have you ever been diagnosed with seizures or epilepsy? Yes or no.",
         "Bạn có từng được chẩn đoán động kinh không? Có hay không?"),
        ("cancer", "Cancer", "Ung thư",
         "Have you ever been diagnosed with cancer? Yes or no.",
         "Bạn có từng được chẩn đoán ung thư không? Có hay không?"),
        ("mental_health", "Mental health", "Bệnh lý tâm thần",
         "Have you ever been diagnosed with a mental health condition such as depression or anxiety? Yes or no.",
         "Bạn có từng được chẩn đoán bệnh lý tâm thần (ví dụ trầm cảm, lo âu) không? Có hay không?"),
    ]
    fields = [
        field("medical_history_patient_name", "text", "Patient name (medical history)", "Họ tên bệnh nhân (bệnh lý)",
              "Auto-filled from patient name on the medical history page.",
              "Tự điền từ họ tên bệnh nhân trên trang bệnh lý.",
              2, "medical_history", False, validation=txt(121, 80, maxLength=80)),
        field("medical_history_dob", "date", "DOB (medical history)", "Ngày sinh (bệnh lý)",
              "Auto-filled from date of birth on the medical history page.",
              "Tự điền từ ngày sinh trên trang bệnh lý.",
              2, "medical_history", False, validation=txt(121, 500)),
    ]
    for value, label_en, label_vi, ask_en, ask_vi in conditions:
        fields.append(
            field(
                f"med_cond_{value}", "boolean", label_en, label_vi, ask_en, ask_vi,
                2, "medical_history", False,
                validation={**cond_checkboxes[value], "render_as_check": True},
            )
        )
    fields.extend([
        field("cancer_type", "text", "Cancer (type)", "Ung thư (loại)",
              "What type of cancer? Only if you said yes to cancer. Say none if not applicable.",
              "Loại ung thư là gì? Chỉ khi bạn trả lời có ung thư. Nếu không, nói không có.",
              2, "medical_history", False, validation=txt(234, 280)),
        field("other_medical_conditions", "text", "Other conditions", "Bệnh khác",
              "Any other medical conditions not listed? Say none if not applicable.",
              "Bệnh khác không có trong danh sách? Nếu không, nói không có.",
              2, "medical_history", False, validation=txt(234, 340)),
    ])
    fields.extend([
        field("surgeries", "textarea", "Surgeries", "Phẫu thuật",
              "Please list any surgeries you have had and the year. Say none if none.",
              "Liệt kê các ca phẫu thuật và năm. Nếu không có, nói không có.",
              2, "medical_history", False, validation=txt(300, 120)),
        field("current_medications", "textarea", "Current Medications", "Thuốc đang dùng",
              "List all current medications including prescriptions, over-the-counter, and supplements. Say none if none.",
              "Liệt kê tất cả thuốc đang dùng. Nếu không có, nói không có.",
              2, "medical_history", False, validation=txt(350, 120)),
        field("hospitalized_6_months", "select", "Hospitalized (6 months)", "Nhập viện 6 tháng qua",
              "Have you been hospitalized in the past 6 months? Yes or no.",
              "Bạn có nhập viện trong 6 tháng qua không? Có hay không?",
              2, "medical_history", False, YES_NO, validation={
                  "checkbox_positions": {"yes": cb(380, 432), "no": cb(380, 504)}
              }),
        field("hospitalized_details", "text", "Hospitalization details", "Chi tiết nhập viện",
              "If hospitalized, please specify. Say none if not applicable.",
              "Nếu có nhập viện, xin ghi rõ. Nếu không, nói không có.",
              2, "medical_history", False, validation=txt(420, 120)),
        field("no_known_allergies", "boolean", "No known allergies", "Không dị ứng",
              "Do you have no known allergies?",
              "Bạn có phải là không có dị ứng không?",
              2, "allergies", False, validation={**cb(460, 36), "render_as_check": True}),
        field("medication_allergies", "text", "Medication allergies", "Dị ứng thuốc",
              "Any medication allergies? List them or say none.",
              "Dị ứng thuốc? Liệt kê hoặc nói không có.",
              2, "allergies", False, validation=txt(460, 280)),
        field("food_allergies", "text", "Food allergies", "Dị ứng thực phẩm",
              "Any food allergies? Say none if none.",
              "Dị ứng thực phẩm? Nếu không có, nói không có.",
              2, "allergies", False, validation=txt(486, 120)),
        field("environmental_allergies", "text", "Environmental allergies", "Dị ứng môi trường",
              "Any environmental allergies? Say none if none.",
              "Dị ứng môi trường? Nếu không có, nói không có.",
              2, "allergies", False, validation=txt(486, 300)),
    ])
    if pediatric:
        fields.extend([
        field("main_caretaker", "text", "Main caretaker", "Người chăm sóc chính",
              "Who is the patient's main caretaker? Say none if not applicable.",
              "Ai là người chăm sóc chính của bệnh nhân? Nếu không có, nói không có.",
              2, "social", False, validation=txt(525, 120)),
        field("caretaker_relationship", "text", "Caretaker relationship", "Mối quan hệ người chăm sóc",
              "What is the caretaker's relationship to the patient?",
              "Mối quan hệ của người chăm sóc với bệnh nhân?",
              2, "social", False, validation=txt(525, 400)),
        field("pregnancy_complications", "textarea", "Pregnancy complications", "Biến chứng thai kỳ",
              "Any medications or complications during pregnancy? Say none or not applicable.",
              "Thuốc hoặc biến chứng trong thai kỳ? Nói không có hoặc không áp dụng.",
              2, "pediatric", False, validation=txt(580, 120)),
        field("mother_return_activities", "text", "Mother return to activities", "Mẹ quay lại sinh hoạt",
              "When does mother plan to return to normal activities after birth? Say not applicable if not relevant.",
              "Khi nào mẹ dự định quay lại sinh hoạt sau sinh? Nói không áp dụng nếu không liên quan.",
              2, "pediatric", False, validation=txt(630, 120)),
        field("breastfeeding_or_formula", "text", "Breastfeeding or formula", "Bú mẹ hay sữa công thức",
              "Is the patient breastfeeding or formula fed? Say not applicable if not relevant.",
              "Bệnh nhân bú mẹ hay uống sữa công thức? Nói không áp dụng nếu không liên quan.",
              2, "pediatric", False, validation=txt(670, 120)),
        field("uses_car_seat", "select", "Uses car seat", "Ghế an toàn xe",
              "Is the patient currently using a car seat? Yes, no, or not applicable.",
              "Bệnh nhân có dùng ghế an toàn trên xe không? Có, không, hoặc không áp dụng.",
              2, "pediatric", False, YES_NO, validation={
                  "checkbox_positions": {"yes": cb(698, 432), "no": cb(698, 504)}
              }),
        ])
    return fields


def page3_fields(*, pediatric: bool = False) -> list[dict]:
    fam_opts = [
        {"value": "diabetes", "label": {"en": "Diabetes", "vi": "Tiểu đường"}},
        {"value": "cancer", "label": {"en": "Cancer", "vi": "Ung thư"}},
        {"value": "heart_disease", "label": {"en": "Heart Disease", "vi": "Bệnh tim"}},
        {"value": "high_blood_pressure", "label": {"en": "High Blood Pressure", "vi": "Cao huyết áp"}},
        {"value": "stroke", "label": {"en": "Stroke", "vi": "Đột quỵ"}},
        {"value": "mental_illness", "label": {"en": "Mental Illness", "vi": "Bệnh tâm thần"}},
        {"value": "other", "label": {"en": "Other", "vi": "Khác"}},
    ]
    records_opts = [
        {"value": "complete_record", "label": {"en": "Complete Medical Record", "vi": "Toàn bộ hồ sơ"}},
        {"value": "office_notes", "label": {"en": "Office Visit Notes", "vi": "Bệnh án"}},
        {"value": "lab_reports", "label": {"en": "Lab/Pathology Reports", "vi": "Xét nghiệm"}},
        {"value": "radiology", "label": {"en": "Radiology/Imaging", "vi": "Hình ảnh/X-quang"}},
        {"value": "immunization", "label": {"en": "Immunization Records", "vi": "Tiêm chủng"}},
        {"value": "medication_records", "label": {"en": "Medication Records", "vi": "Hồ sơ thuốc"}},
        {"value": "other", "label": {"en": "Other", "vi": "Khác"}},
    ]
    purpose_opts = [
        {"value": "continuation_of_care", "label": {"en": "Continuation of care", "vi": "Tiếp tục điều trị"}},
        {"value": "personal_use", "label": {"en": "Personal use", "vi": "Sử dụng cá nhân"}},
        {"value": "legal", "label": {"en": "Legal purposes", "vi": "Pháp lý"}},
        {"value": "insurance", "label": {"en": "Insurance", "vi": "Bảo hiểm"}},
        {"value": "post_hospital", "label": {"en": "Post ER/Hospital follow-up", "vi": "Theo dõi sau nhập viện"}},
        {"value": "other", "label": {"en": "Other", "vi": "Khác"}},
    ]
    fields = [
        field("family_history", "multiselect", "Family History", "Tiền sử gia đình",
              "Has anyone in your immediate family had diabetes, cancer, heart disease, high blood pressure, stroke, or mental illness? Say none if none.",
              "Gia đình có ai mắc tiểu đường, ung thư, tim, cao huyết áp, đột quỵ, tâm thần? Nói không có nếu không.",
              3, "family_history", False, fam_opts, validation={
                  "checkbox_positions": {
                      "diabetes": cb(119, 36), "cancer": cb(119, 144), "heart_disease": cb(119, 262),
                      "high_blood_pressure": cb(119, 406), "stroke": cb(147, 36),
                      "mental_illness": cb(147, 144), "other": cb(147, 262),
                  }
              }),
        field("family_history_other", "text", "Family history (other)", "Tiền sử gia đình khác",
              "Any other family history to specify? Say none if not applicable.",
              "Tiền sử gia đình khác? Nếu không, nói không có.",
              3, "family_history", False, validation=txt(147, 300)),
        field("secondhand_smoke", "select", "Secondhand smoke", "Khói thuốc thụ động",
              "Have you been exposed to secondhand smoke at home? Yes or no.",
              "Có tiếp xúc khói thuốc lá thụ động trong nhà không?",
              3, "social_history", False, YES_NO, validation={
                  "checkbox_positions": {"yes": cb(180, 432), "no": cb(180, 504)}
              }),
        field("tobacco_use", "select", "Tobacco use", "Hút thuốc",
              "Do you smoke or use tobacco? Yes or no.",
              "Bạn có hút thuốc hoặc dùng thuốc lá không?",
              3, "social_history", False, YES_NO, validation={
                  "checkbox_positions": {"yes": cb(211, 180), "no": cb(211, 252)}
              }),
        field("tobacco_frequency", "text", "Tobacco frequency", "Tần suất hút thuốc",
              "If you use tobacco, how much and how often? Say none if not applicable.",
              "Nếu hút thuốc, bao nhiêu và bao lâu? Nếu không, nói không có.",
              3, "social_history", False, validation=txt(224, 360)),
        field("alcohol_use", "select", "Alcohol use", "Uống rượu",
              "Do you consume alcohol? Yes or no.",
              "Bạn có uống rượu không?",
              3, "social_history", False, YES_NO, validation={
                  "checkbox_positions": {"yes": cb(252, 180), "no": cb(252, 252)}
              }),
        field("alcohol_frequency", "text", "Alcohol frequency", "Tần suất uống rượu",
              "If you drink alcohol, how much and how often? Say none if not applicable.",
              "Nếu uống rượu, bao nhiêu và bao lâu?",
              3, "social_history", False, validation=txt(265, 360)),
        field("recreational_drugs", "select", "Recreational drugs", "Thuốc gây nghiện",
              "Do you use recreational drugs? Yes or no.",
              "Bạn có dùng thuốc gây nghiện không?",
              3, "social_history", False, YES_NO, validation={
                  "checkbox_positions": {"yes": cb(294, 180), "no": cb(294, 252)}
              }),
        field("recreational_drugs_list", "text", "Recreational drugs (list)", "Thuốc gây nghiện (liệt kê)",
              "If yes, please list recreational drugs used. Say none if not applicable.",
              "Nếu có, liệt kê. Nếu không, nói không có.",
              3, "social_history", False, validation=txt(306, 360)),
    ]
    if pediatric:
        fields.append(
        field("parent_drug_alcohol", "select", "Parent drug/alcohol use", "Cha mẹ dùng chất",
              "Do either parent or guardian use illicit drugs or drink excessively? Yes or no.",
              "Cha mẹ hoặc người giám hộ có dùng ma túy hoặc uống quá mức không?",
              3, "social_history", False, YES_NO, validation={
                  "checkbox_positions": {"yes": cb(335, 432), "no": cb(335, 504)}
              }),
        )
    fields.extend([
        field("feel_safe_home", "select", "Feel safe at home", "An toàn nơi ở",
              "Do you feel safe where you live? Yes or no.",
              "Bạn có cảm thấy an toàn nơi mình sống không?",
              3, "social_history", False, YES_NO, validation={
                  "checkbox_positions": {"yes": cb(376, 432), "no": cb(376, 504)}
              }),
        field("vaccinations_up_to_date", "select", "Vaccinations up to date", "Tiêm chủng đầy đủ",
              "Are your vaccinations up to date? Yes, no, or unsure.",
              "Tiêm chủng đã đầy đủ chưa? Có, không, hay không chắc?",
              3, "social_history", False, YES_NO_UNSURE, validation={
                  "checkbox_positions": {"yes": cb(418, 360), "no": cb(418, 432), "unsure": cb(418, 504)}
              }),
        field("tb_tested", "select", "TB tested", "Xét nghiệm lao",
              "Have you been tested for tuberculosis? Yes, no, or unsure.",
              "Bạn đã xét nghiệm lao chưa?",
              3, "social_history", False, YES_NO_UNSURE, validation={
                  "checkbox_positions": {"yes": cb(459, 360), "no": cb(459, 432), "unsure": cb(459, 504)}
              }),
        field("tb_result", "select", "TB test result", "Kết quả xét nghiệm lao",
              "If tested for TB, what was the result? Negative, positive, unsure, or not applicable.",
              "Kết quả xét nghiệm lao? Âm tính, dương tính, không chắc, hoặc không áp dụng.",
              3, "social_history", False, TB_RESULT, validation={
                  "checkbox_positions": {
                      "negative": cb(500, 360), "positive": cb(500, 432), "unsure": cb(500, 504)
                  }
              }),
        field("communication_requirements", "select", "Communication requirements", "Yêu cầu giao tiếp",
              "Do you have specific communication requirements? Yes or no.",
              "Bạn có yêu cầu đặc biệt về giao tiếp không?",
              3, "social_history", False, YES_NO, validation={
                  "checkbox_positions": {"yes": cb(543, 432), "no": cb(543, 504)}
              }),
        field("communication_details", "text", "Communication details", "Chi tiết giao tiếp",
              "If yes, please specify communication needs. Say none if not applicable.",
              "Nếu có, xin ghi rõ. Nếu không, nói không có.",
              3, "social_history", False, validation=txt(592, 120)),
        field("interpretation_needed", "select", "Interpretation needed", "Cần thông dịch",
              "Do you need interpretation services? Yes or no.",
              "Bạn có cần thông dịch không?",
              3, "social_history", False, YES_NO, validation={
                  "checkbox_positions": {"yes": cb(619, 432), "no": cb(619, 504)}
              }),
        field("interpretation_language", "text", "Interpretation language", "Ngôn ngữ thông dịch",
              "If interpretation is needed, which language? Say none if not applicable.",
              "Nếu cần thông dịch, ngôn ngữ nào?",
              3, "social_history", False, validation=txt(671, 120)),
    ])
    return fields


def page4_fields() -> list[dict]:
    return [
        field("hipaa_acknowledgement", "boolean", "HIPAA Acknowledgement", "Xác nhận HIPAA",
              "HIPAA acknowledgement — read all 7 terms one by one before saving.",
              "Xác nhận HIPAA — đọc từng điều khoản trong 7 điều khoản trước khi lưu.",
              3, "consent", True, validation={**cb(500, 36), "render_as_check": True}),
        field("release_contact_1_name", "text", "Release contact 1 name", "Người được cấp quyền 1",
              "Name of person authorized to access your health information. Say none if not applicable.",
              "Tên người được phép truy cập thông tin sức khỏe. Nếu không có, nói không có.",
              3, "release", False, validation=txt(588, 80)),
        field("release_contact_1_relationship", "text", "Release contact 1 relationship", "Quan hệ (người 1)",
              "Relationship of the first authorized person.",
              "Mối quan hệ với người thứ nhất?",
              3, "release", False, validation=txt(588, 300)),
        field("release_contact_1_phone", "phone", "Release contact 1 phone", "SĐT người 1",
              "Phone number for the first authorized person.",
              "Số điện thoại người thứ nhất?",
              3, "release", False, validation=txt(603, 80)),
        field("release_contact_1_emergency", "select", "Emergency contact 1", "Liên hệ khẩn cấp 1",
              "Is the first person an emergency contact? Yes or no.",
              "Người thứ nhất có phải liên hệ khẩn cấp không?",
              3, "release", False, YES_NO, validation={
                  "checkbox_positions": {"yes": cb(603, 360), "no": cb(603, 432)}
              }),
        field("release_contact_2_name", "text", "Release contact 2 name", "Người được cấp quyền 2",
              "Name of a second person authorized to access your health information. Say none if not applicable.",
              "Tên người thứ hai được phép truy cập. Nếu không có, nói không có.",
              3, "release", False, validation=txt(617, 80)),
        field("release_contact_2_relationship", "text", "Release contact 2 relationship", "Quan hệ (người 2)",
              "Relationship of the second authorized person.",
              "Mối quan hệ với người thứ hai?",
              3, "release", False, validation=txt(617, 300)),
        field("release_contact_2_phone", "phone", "Release contact 2 phone", "SĐT người 2",
              "Phone number for the second authorized person.",
              "Số điện thoại người thứ hai?",
              3, "release", False, validation=txt(632, 80)),
        field("release_contact_2_emergency", "select", "Emergency contact 2", "Liên hệ khẩn cấp 2",
              "Is the second person an emergency contact? Yes or no.",
              "Người thứ hai có phải liên hệ khẩn cấp không?",
              3, "release", False, YES_NO, validation={
                  "checkbox_positions": {"yes": cb(632, 360), "no": cb(632, 432)}
              }),
        field("electronic_communication_consent", "boolean", "Electronic Communication", "Đồng ý liên lạc điện tử",
              "Electronic communication consent — read both terms one by one before saving.",
              "Đồng ý liên lạc điện tử — đọc từng điều khoản trong 2 điều khoản trước khi lưu.",
              3, "consent", True, validation={**cb(668, 36), "render_as_check": True}),
        field("consent_signer_name", "text", "Patient or representative name", "Họ tên bệnh nhân/người đại diện",
              "Auto-filled — patient or guardian name for consent signature line.",
              "Tự điền — họ tên bệnh nhân hoặc người giám hộ trên dòng chữ ký.",
              3, "consent", False, validation=txt(648, 80, maxLength=100)),
    ]


def page5_fields() -> list[dict]:
    records_opts = [
        {"value": "complete_record", "label": {"en": "Complete Medical Record", "vi": "Toàn bộ hồ sơ"}},
        {"value": "office_notes", "label": {"en": "Office Visit Notes", "vi": "Bệnh án"}},
        {"value": "lab_reports", "label": {"en": "Lab/Pathology Reports", "vi": "Xét nghiệm"}},
        {"value": "radiology", "label": {"en": "Radiology/Imaging", "vi": "Hình ảnh/X-quang"}},
        {"value": "immunization", "label": {"en": "Immunization Records", "vi": "Tiêm chủng"}},
        {"value": "medication_records", "label": {"en": "Medication Records", "vi": "Hồ sơ thuốc"}},
        {"value": "other", "label": {"en": "Other", "vi": "Khác"}},
    ]
    purpose_opts = [
        {"value": "continuation_of_care", "label": {"en": "Continuation of care", "vi": "Tiếp tục điều trị"}},
        {"value": "personal_use", "label": {"en": "Personal use", "vi": "Sử dụng cá nhân"}},
        {"value": "legal", "label": {"en": "Legal purposes", "vi": "Pháp lý"}},
        {"value": "insurance", "label": {"en": "Insurance", "vi": "Bảo hiểm"}},
        {"value": "post_hospital", "label": {"en": "Post ER/Hospital follow-up", "vi": "Theo dõi sau nhập viện"}},
        {"value": "other", "label": {"en": "Other", "vi": "Khác"}},
    ]
    return [
        field("authorization_patient_name", "text", "Patient name (authorization)", "Tên bệnh nhân (ủy quyền)",
              "Auto-filled from patient name on authorization page.",
              "Tự điền từ họ tên bệnh nhân trên trang ủy quyền.",
              4, "authorization", False, validation=txt(72, 80)),
        field("authorization_dob", "date", "DOB (authorization)", "Ngày sinh (ủy quyền)",
              "Auto-filled from date of birth on authorization page.",
              "Tự điền từ ngày sinh trên trang ủy quyền.",
              4, "authorization", False, validation=txt(72, 360)),
        field("release_authorization_name", "text", "Authorized person name", "Tên người cho phép",
              "Auto-filled — I authorize release of records (patient full name).",
              "Tự điền — Tôi cho phép tiết lộ hồ sơ (họ tên bệnh nhân).",
              4, "authorization", True, validation=txt(135, 80)),
        field("provider_facility_name", "text", "Provider/Facility", "Bác sĩ/Cơ sở",
              "Name of provider or facility to release records from. Say none if VM Clinic only. "
              "If unsure, give a partial name or address and I can search.",
              "Tên bác sĩ hoặc cơ sở cung cấp hồ sơ? Nếu chỉ gửi về VM Clinic, nói không có. "
              "Nếu không chắc, cho tên hoặc địa chỉ một phần để tôi tra cứu.",
              4, "authorization", False, validation=txt(169, 120)),
        field("provider_phone", "phone", "Provider phone", "SĐT cơ sở",
              "Provider phone number. Say none if not applicable.",
              "Số điện thoại cơ sở? Nếu không có, nói không có.",
              4, "authorization", False, validation=txt(194, 80)),
        field("provider_fax", "text", "Provider fax", "Fax cơ sở",
              "Provider fax number. Say none if not applicable.",
              "Số fax cơ sở? Nếu không có, nói không có.",
              4, "authorization", False, validation=txt(194, 380)),
        field("records_to_release", "multiselect", "Records to release", "Hồ sơ cần cung cấp",
              "What information should be released? Complete record, office notes, lab, radiology, immunization, medication, or other.",
              "Thông tin nào được cung cấp? Toàn bộ hồ sơ, bệnh án, xét nghiệm, X-quang, tiêm chủng, thuốc, hay khác?",
              4, "authorization", False, records_opts, validation={
                  "checkbox_positions": {
                      "complete_record": cb(327, 36), "office_notes": cb(327, 216),
                      "lab_reports": cb(327, 360), "radiology": cb(355, 36),
                      "immunization": cb(355, 216), "medication_records": cb(355, 360),
                      "other": cb(355, 504),
                  }
              }),
        field("disclosure_purpose", "multiselect", "Purpose of disclosure", "Mục đích tiết lộ",
              "Purpose of disclosure: continuation of care, personal use, legal, insurance, post-hospital, or other.",
              "Mục đích: tiếp tục điều trị, cá nhân, pháp lý, bảo hiểm, sau nhập viện, hay khác?",
              4, "authorization", False, purpose_opts, validation={
                  "checkbox_positions": {
                      "continuation_of_care": cb(410, 36), "personal_use": cb(410, 216),
                      "legal": cb(410, 360), "insurance": cb(437, 36),
                      "post_hospital": cb(437, 216), "other": cb(437, 360),
                  }
              }),
        field("release_consent_acknowledgement", "boolean", "Release consent", "Đồng ý tiết lộ hồ sơ",
              "Release authorization consent — read all 3 terms one by one before saving.",
              "Đồng ý tiết lộ hồ sơ — đọc từng điều khoản trong 3 điều khoản trước khi lưu.",
              4, "authorization", True, validation={**cb(497, 36), "render_as_check": True}),
    ]


SECTIONS = [
    {"id": "personal", "title": {"en": "Personal Information", "vi": "Thông tin cá nhân"}, "order": 1},
    {"id": "insurance", "title": {"en": "Insurance", "vi": "Bảo hiểm"}, "order": 2},
    {"id": "demographics", "title": {"en": "Demographics", "vi": "Nhân khẩu học"}, "order": 3},
    {"id": "pharmacy", "title": {"en": "Pharmacy", "vi": "Nhà thuốc"}, "order": 4},
    {"id": "consent", "title": {"en": "Consent", "vi": "Đồng ý"}, "order": 5},
    {"id": "medical_history", "title": {"en": "Medical History", "vi": "Lịch sử bệnh án"}, "order": 6},
    {"id": "allergies", "title": {"en": "Allergies", "vi": "Dị ứng"}, "order": 7},
    {"id": "social", "title": {"en": "Social / Caretaker", "vi": "Xã hội / Người chăm sóc"}, "order": 8},
    {"id": "pediatric", "title": {"en": "Pediatric / Pregnancy", "vi": "Nhi / Thai kỳ"}, "order": 9},
    {"id": "family_history", "title": {"en": "Family History", "vi": "Tiền sử gia đình"}, "order": 10},
    {"id": "social_history", "title": {"en": "Social History", "vi": "Tiền sử xã hội"}, "order": 11},
    {"id": "release", "title": {"en": "Release of Information", "vi": "Cấp quyền thông tin"}, "order": 12},
    {"id": "authorization", "title": {"en": "Authorization", "vi": "Ủy quyền hồ sơ"}, "order": 13},
]


def all_fields(*, pediatric: bool = False) -> list[dict]:
    return (
        page1_fields(pediatric=pediatric)
        + page2_fields(pediatric=pediatric)
        + page3_fields(pediatric=pediatric)
        + page4_fields()
        + page5_fields()
    )


def build_schema(
    form_id: str,
    filename: str,
    title_en: str,
    title_vi: str,
    default: bool,
    fields: list[dict] | None = None,
) -> dict:
    return {
        "id": form_id,
        "filename": filename,
        "title": {"en": title_en, "vi": title_vi},
        "version": "2.1.0",
        "default": default,
        "sections": SECTIONS,
        "fields": fields if fields is not None else all_fields(),
    }


def main() -> None:
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    adult_fields = all_fields(pediatric=False)
    child_fields = all_fields(pediatric=True)
    schemas = [
        build_schema(
            "triage",
            "adult_en.pdf",
            "Registration intake",
            "Tiếp nhận đăng ký",
            default=True,
            fields=[
                field(
                    "dob",
                    "date",
                    "Date of birth",
                    "Ngày sinh",
                    "What is your date of birth?",
                    "Ngày sinh của bạn là gì ạ?",
                    1,
                    "personal",
                    True,
                ),
            ],
        ),
        build_schema(
            "adult_en",
            "adult_en.pdf",
            "Adult Registration (English)",
            "Đăng ký người lớn (Tiếng Anh)",
            default=False,
            fields=adult_fields,
        ),
        build_schema(
            "adult_vn",
            "adult_vn.pdf",
            "Adult Registration (Vietnamese)",
            "Đăng ký người lớn (Tiếng Việt)",
            default=False,
            fields=adult_fields,
        ),
        build_schema(
            "child_en",
            "Child_en.pdf",
            "Pediatric Registration (English)",
            "Đăng ký trẻ em (Tiếng Anh)",
            default=False,
            fields=child_fields,
        ),
        build_schema(
            "child_vn",
            "Child_vn.pdf",
            "Pediatric Registration (Vietnamese)",
            "Đăng ký trẻ em (Tiếng Việt)",
            default=False,
            fields=child_fields,
        ),
    ]
    for schema in schemas:
        path = SCHEMA_DIR / f"{schema['id']}.json"
        path.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {path} ({len(schema['fields'])} fields)")


if __name__ == "__main__":
    main()
