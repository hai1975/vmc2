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


def page1_fields() -> list[dict]:
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
    return [
        field("patient_name", "text", "Patient Name", "Họ và tên bệnh nhân",
              "What is your full legal name?", "Xin cho biết họ và tên đầy đủ của bạn?",
              1, "personal", True, validation=txt(118, 175, maxLength=100)),
        field("birthday", "date", "Birthday", "Ngày sinh",
              "What is your date of birth?", "Ngày sinh của bạn là ngày nào?",
              1, "personal", True, validation=txt(140, 100)),
        field("ssn", "ssn", "SSN", "Số SSN",
              "What is your Social Security Number? Say none if you don't have one.",
              "Số SSN của bạn là gì? Nếu không có, nói không có.",
              1, "personal", False, validation=txt(140, 410)),
        field("guardian_1_name", "text", "Legal Guardian 1", "Người giám hộ 1",
              "Who is your first legal guardian? Say none if not applicable.",
              "Tên người giám hộ hợp pháp thứ nhất? Nếu không có, nói không có.",
              1, "personal", False, validation=txt(162, 255)),
        field("guardian_1_relationship", "text", "Relationship (Guardian 1)", "Mối quan hệ (giám hộ 1)",
              "What is your relationship to the first guardian?",
              "Mối quan hệ với người giám hộ thứ nhất?",
              1, "personal", False, validation=txt(162, 470)),
        field("guardian_2_name", "text", "Legal Guardian 2", "Người giám hộ 2",
              "Who is your second legal guardian? Say none if not applicable.",
              "Tên người giám hộ hợp pháp thứ hai? Nếu không có, nói không có.",
              1, "personal", False, validation=txt(186, 255)),
        field("guardian_2_relationship", "text", "Relationship (Guardian 2)", "Mối quan hệ (giám hộ 2)",
              "What is your relationship to the second guardian?",
              "Mối quan hệ với người giám hộ thứ hai?",
              1, "personal", False, validation=txt(186, 470)),
        field("home_address", "textarea", "Home Address", "Địa chỉ nhà",
              "What is your home address?", "Địa chỉ nhà của bạn là gì?",
              1, "personal", True, validation=txt(210, 105)),
        field("phone", "phone", "Phone Number", "Số điện thoại",
              "What is your phone number?", "Số điện thoại liên lạc của bạn là gì?",
              1, "personal", True, validation=txt(232, 110)),
        field("email", "email", "Email", "Email",
              "What is your email address? Say none if you don't have one.",
              "Địa chỉ email của bạn? Nếu không có, nói không có.",
              1, "personal", False, validation=txt(232, 330)),
        field("insurance", "select", "Insurance", "Bảo hiểm",
              "What insurance do you have? Medi-Cal, PPO, HMO, or uninsured?",
              "Bạn có loại bảo hiểm nào? Medi-Cal, PPO, HMO, hay không có bảo hiểm?",
              1, "insurance", True, ins_opts, validation={
                  "checkbox_positions": {
                      "medi_cal": cb(255, 108), "ppo": cb(255, 216),
                      "hmo": cb(255, 324), "uninsured": cb(255, 432),
                  }
              }),
        field("race", "multiselect", "Race", "Chủng tộc",
              "What is your race? You may select multiple: Asian, White, African American, Native American, Pacific Islander, or other.",
              "Chủng tộc của bạn? Có thể chọn nhiều: Châu Á, Da trắng, Người Mỹ gốc Phi, và các lựa chọn khác.",
              1, "demographics", False, race_opts, validation={
                  "checkbox_positions": {
                      "asian": cb(285, 108), "white": cb(285, 216), "african_american": cb(285, 324),
                      "native_american": cb(301, 108), "pacific_islander": cb(317, 108), "other": cb(301, 360),
                  }
              }),
        field("race_other_specify", "text", "Other race (specify)", "Chủng tộc khác (ghi rõ)",
              "If you selected other race, please specify. Say none if not applicable.",
              "Nếu chọn chủng tộc khác, xin ghi rõ. Nếu không, nói không có.",
              1, "demographics", False, validation=txt(301, 400)),
        field("ethnicity", "select", "Ethnicity", "Dân tộc",
              "What is your ethnicity? Hispanic or Latino, Not Hispanic or Latino, or Unknown?",
              "Dân tộc: Gốc Tây Ban Nha/La-tinh, không gốc Tây Ban Nha, hay không rõ?",
              1, "demographics", False, eth_opts, validation={
                  "checkbox_positions": {
                      "hispanic": cb(347, 108), "not_hispanic": cb(347, 288), "unknown": cb(347, 504),
                  }
              }),
        field("gender_identity", "select", "Gender Identity", "Giới tính",
              "What is your gender identity? Male, Female, prefer not to say, Other, FTM, MTF, or Genderqueer?",
              "Giới tính của bạn? Nam, Nữ, không tiết lộ, Khác, FTM, MTF, hay Genderqueer?",
              1, "demographics", False, gender_opts, validation={
                  "checkbox_positions": {
                      "male": cb(377, 108), "female": cb(377, 180), "not_disclose": cb(377, 252),
                      "other": cb(377, 396), "ftm": cb(393, 36), "mtf": cb(408, 36), "genderqueer": cb(424, 36),
                  }
              }),
        field("sexual_orientation", "select", "Sexual Orientation", "Xu hướng tình dục",
              "What is your sexual orientation? Gay or lesbian, straight, bisexual, don't know, prefer not to say, or other?",
              "Xu hướng tình dục? Đồng tính, dị tính, song tính, không biết, không tiết lộ, hay khác?",
              1, "demographics", False, orient_opts, validation={
                  "checkbox_positions": {
                      "gay_lesbian": cb(454, 144), "straight": cb(454, 432), "bisexual": cb(470, 36),
                      "unknown": cb(470, 144), "not_disclose": cb(470, 252), "other": cb(470, 432),
                  }
              }),
        field("pharmacy_name", "text", "Preferred Pharmacy", "Nhà thuốc ưa thích",
              "What is your preferred pharmacy name? Say none if you don't have one.",
              "Nhà thuốc ưa thích tên gì? Nếu không có, nói không có.",
              1, "pharmacy", False, validation=txt(498, 120)),
        field("pharmacy_phone", "phone", "Pharmacy Phone", "SĐT nhà thuốc",
              "What is the pharmacy phone number? Say none if you don't have one.",
              "Số điện thoại nhà thuốc? Nếu không có, nói không có.",
              1, "pharmacy", False, validation=txt(498, 420)),
        field("treatment_consent", "boolean", "Treatment Consent", "Đồng ý điều trị",
              "Do you consent to VM Clinic evaluating and treating you?",
              "Bạn có đồng ý cho VM Clinic đánh giá và điều trị không?",
              1, "consent", True, validation={**cb(526, 36), "render_as_check": True}),
    ]


def page2_fields() -> list[dict]:
    cond_opts = [
        {"value": "diabetes", "label": {"en": "Diabetes", "vi": "Tiểu đường"}},
        {"value": "high_blood_pressure", "label": {"en": "High Blood Pressure", "vi": "Cao huyết áp"}},
        {"value": "high_cholesterol", "label": {"en": "High Cholesterol", "vi": "Cao mỡ máu"}},
        {"value": "heart_disease", "label": {"en": "Heart Disease", "vi": "Bệnh tim"}},
        {"value": "asthma", "label": {"en": "Asthma", "vi": "Hen suyễn"}},
        {"value": "stroke", "label": {"en": "Stroke", "vi": "Đột quỵ"}},
        {"value": "kidney_disease", "label": {"en": "Kidney Disease", "vi": "Bệnh thận"}},
        {"value": "liver_disease", "label": {"en": "Liver Disease", "vi": "Bệnh gan"}},
        {"value": "seizures", "label": {"en": "Seizures", "vi": "Động kinh"}},
        {"value": "mental_health", "label": {"en": "Mental Health Conditions", "vi": "Bệnh lý tâm thần"}},
    ]
    return [
        field("medical_conditions", "multiselect", "Medical Conditions", "Bệnh đã mắc",
              "Have you ever been diagnosed with any of these? Diabetes, high blood pressure, cholesterol, heart disease, asthma, stroke, kidney or liver disease, seizures, or mental health. Say none if none apply.",
              "Bạn đã từng mắc bệnh nào trong các bệnh: tiểu đường, cao huyết áp, mỡ máu, tim, hen, đột quỵ, thận, gan, động kinh, tâm thần? Nói không có nếu không mắc.",
              2, "medical_history", False, cond_opts, validation={
                  "checkbox_positions": {
                      "diabetes": cb(179, 36), "high_blood_pressure": cb(179, 144),
                      "high_cholesterol": cb(179, 288), "heart_disease": cb(179, 432),
                      "asthma": cb(207, 36), "stroke": cb(207, 144),
                      "kidney_disease": cb(207, 288), "liver_disease": cb(207, 432),
                      "seizures": cb(234, 36), "mental_health": cb(261, 36),
                  }
              }),
        field("cancer_type", "text", "Cancer (type)", "Ung thư (loại)",
              "Have you had cancer? If yes, what type? Say none if not applicable.",
              "Bạn có ung thư không? Nếu có, loại gì? Nếu không, nói không có.",
              2, "medical_history", False, validation=txt(234, 200)),
        field("other_medical_conditions", "text", "Other conditions", "Bệnh khác",
              "Any other medical conditions not listed? Say none if not applicable.",
              "Bệnh khác không có trong danh sách? Nếu không, nói không có.",
              2, "medical_history", False, validation=txt(234, 340)),
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
        field("main_caretaker", "text", "Main caretaker", "Người chăm sóc chính",
              "Who is your main caretaker? Say none if not applicable.",
              "Người chăm sóc chính của bạn? Nếu không có, nói không có.",
              2, "social", False, validation=txt(525, 120)),
        field("caretaker_relationship", "text", "Caretaker relationship", "Mối quan hệ người chăm sóc",
              "What is your relationship to the caretaker?",
              "Mối quan hệ với người chăm sóc?",
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
    ]


def page3_fields() -> list[dict]:
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
    return [
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
        field("parent_drug_alcohol", "select", "Parent drug/alcohol use", "Cha mẹ dùng chất",
              "Do either parent or guardian use illicit drugs or drink excessively? Yes or no.",
              "Cha mẹ hoặc người giám hộ có dùng ma túy hoặc uống quá mức không?",
              3, "social_history", False, YES_NO, validation={
                  "checkbox_positions": {"yes": cb(335, 432), "no": cb(335, 504)}
              }),
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
    ]


def page4_fields() -> list[dict]:
    return [
        field("hipaa_acknowledgement", "boolean", "HIPAA Acknowledgement", "Xác nhận HIPAA",
              "Do you acknowledge receiving the Notice of Privacy Practices?",
              "Bạn xác nhận đã nhận Thông báo Quyền riêng tư chưa?",
              4, "consent", True, validation={**cb(500, 36), "render_as_check": True}),
        field("release_contact_1_name", "text", "Release contact 1 name", "Người được cấp quyền 1",
              "Name of person authorized to access your health information. Say none if not applicable.",
              "Tên người được phép truy cập thông tin sức khỏe. Nếu không có, nói không có.",
              4, "release", False, validation=txt(588, 80)),
        field("release_contact_1_relationship", "text", "Release contact 1 relationship", "Quan hệ (người 1)",
              "Relationship of the first authorized person.",
              "Mối quan hệ với người thứ nhất?",
              4, "release", False, validation=txt(588, 300)),
        field("release_contact_1_phone", "phone", "Release contact 1 phone", "SĐT người 1",
              "Phone number for the first authorized person.",
              "Số điện thoại người thứ nhất?",
              4, "release", False, validation=txt(603, 80)),
        field("release_contact_1_emergency", "select", "Emergency contact 1", "Liên hệ khẩn cấp 1",
              "Is the first person an emergency contact? Yes or no.",
              "Người thứ nhất có phải liên hệ khẩn cấp không?",
              4, "release", False, YES_NO, validation={
                  "checkbox_positions": {"yes": cb(603, 360), "no": cb(603, 432)}
              }),
        field("release_contact_2_name", "text", "Release contact 2 name", "Người được cấp quyền 2",
              "Name of a second person authorized to access your health information. Say none if not applicable.",
              "Tên người thứ hai được phép truy cập. Nếu không có, nói không có.",
              4, "release", False, validation=txt(617, 80)),
        field("release_contact_2_relationship", "text", "Release contact 2 relationship", "Quan hệ (người 2)",
              "Relationship of the second authorized person.",
              "Mối quan hệ với người thứ hai?",
              4, "release", False, validation=txt(617, 300)),
        field("release_contact_2_phone", "phone", "Release contact 2 phone", "SĐT người 2",
              "Phone number for the second authorized person.",
              "Số điện thoại người thứ hai?",
              4, "release", False, validation=txt(632, 80)),
        field("release_contact_2_emergency", "select", "Emergency contact 2", "Liên hệ khẩn cấp 2",
              "Is the second person an emergency contact? Yes or no.",
              "Người thứ hai có phải liên hệ khẩn cấp không?",
              4, "release", False, YES_NO, validation={
                  "checkbox_positions": {"yes": cb(632, 360), "no": cb(632, 432)}
              }),
        field("electronic_communication_consent", "boolean", "Electronic Communication", "Đồng ý liên lạc điện tử",
              "Do you consent to VM Clinic communicating via phone, text, and email?",
              "Bạn đồng ý VM Clinic liên lạc qua điện thoại, tin nhắn và email không?",
              4, "consent", True, validation={**cb(668, 36), "render_as_check": True}),
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
        field("release_authorization_name", "text", "Authorized person name", "Tên người cho phép",
              "I authorize release of records — what is your full name for this authorization?",
              "Tôi cho phép tiết lộ hồ sơ — họ tên đầy đủ của bạn?",
              5, "authorization", True, validation=txt(135, 80)),
        field("provider_facility_name", "text", "Provider/Facility", "Bác sĩ/Cơ sở",
              "Name of provider or facility to release records from. Say none if releasing to VM Clinic only.",
              "Tên bác sĩ hoặc cơ sở cung cấp hồ sơ? Nếu chỉ gửi về VM Clinic, nói không có.",
              5, "authorization", False, validation=txt(169, 120)),
        field("provider_phone", "phone", "Provider phone", "SĐT cơ sở",
              "Provider phone number. Say none if not applicable.",
              "Số điện thoại cơ sở? Nếu không có, nói không có.",
              5, "authorization", False, validation=txt(194, 80)),
        field("provider_fax", "text", "Provider fax", "Fax cơ sở",
              "Provider fax number. Say none if not applicable.",
              "Số fax cơ sở? Nếu không có, nói không có.",
              5, "authorization", False, validation=txt(194, 380)),
        field("records_to_release", "multiselect", "Records to release", "Hồ sơ cần cung cấp",
              "What information should be released? Complete record, office notes, lab, radiology, immunization, medication, or other.",
              "Thông tin nào được cung cấp? Toàn bộ hồ sơ, bệnh án, xét nghiệm, X-quang, tiêm chủng, thuốc, hay khác?",
              5, "authorization", False, records_opts, validation={
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
              5, "authorization", False, purpose_opts, validation={
                  "checkbox_positions": {
                      "continuation_of_care": cb(410, 36), "personal_use": cb(410, 216),
                      "legal": cb(410, 360), "insurance": cb(437, 36),
                      "post_hospital": cb(437, 216), "other": cb(437, 360),
                  }
              }),
        field("release_consent_acknowledgement", "boolean", "Release consent", "Đồng ý tiết lộ hồ sơ",
              "Do you authorize the release of your medical information as described?",
              "Bạn có đồng ý cho phép tiết lộ thông tin y tế như mô tả không?",
              5, "authorization", True, validation={**cb(497, 36), "render_as_check": True}),
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


def all_fields() -> list[dict]:
    return page1_fields() + page2_fields() + page3_fields() + page4_fields() + page5_fields()


def build_schema(form_id: str, filename: str, title_en: str, title_vi: str, default: bool) -> dict:
    return {
        "id": form_id,
        "filename": filename,
        "title": {"en": title_en, "vi": title_vi},
        "version": "2.0.0",
        "default": default,
        "sections": SECTIONS,
        "fields": all_fields(),
    }


def main() -> None:
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    schemas = [
        build_schema(
            "form_en",
            "form_en.pdf",
            "New Patient Registration (English)",
            "Đơn ghi danh bệnh nhân mới (Tiếng Anh)",
            default=True,
        ),
        build_schema(
            "form_vn",
            "form_vn.pdf",
            "New Patient Registration (Vietnamese)",
            "Đơn ghi danh bệnh nhân mới (Tiếng Việt)",
            default=False,
        ),
    ]
    for schema in schemas:
        path = SCHEMA_DIR / f"{schema['id']}.json"
        path.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {path} ({len(schema['fields'])} fields)")


if __name__ == "__main__":
    main()
