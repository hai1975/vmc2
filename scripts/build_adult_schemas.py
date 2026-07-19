"""Build adult_en.json / adult_vn.json from measured PDF label positions."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
PAGE_H = 792.0


def y(top: float) -> float:
    """fitz top/baseline-ish → reportlab y (origin bottom-left)."""
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


def personal_fields(lang: str = "en") -> list[dict]:
    """Coords measured from adult_en.pdf / adult_vn.pdf page 1 (no guardian rows)."""
    # Vietnamese labels are longer → start text further right on some rows.
    name_x = 200 if lang == "vi" else 175
    dob_x = 120 if lang == "vi" else 110
    ssn_x = 420 if lang == "vi" else 360
    addr_x = 120 if lang == "vi" else 130
    home_phone_x = 160 if lang == "vi" else 145
    cell_x = 340 if lang == "vi" else 300
    email_x = 480 if lang == "vi" else 440
    uninsured_key_left = 504
    ins_opts = [
        {"value": "medicare", "label": {"en": "Medicare", "vi": "Medicare"}},
        {"value": "medi_cal", "label": {"en": "Medi-Cal", "vi": "Medi-Cal"}},
        {"value": "ppo", "label": {"en": "PPO", "vi": "PPO"}},
        {"value": "hmo", "label": {"en": "HMO", "vi": "HMO"}},
        {"value": "uninsured", "label": {"en": "Uninsured", "vi": "Không có"}},
    ]
    race_opts = [
        {"value": "asian", "label": {"en": "Asian", "vi": "Châu Á"}},
        {"value": "white", "label": {"en": "White", "vi": "Da trắng"}},
        {"value": "african_american", "label": {"en": "African American", "vi": "Người Mỹ gốc Phi"}},
        {"value": "native_american", "label": {"en": "American Indian / Alaska Native", "vi": "Người da đỏ / Alaska bản địa"}},
        {"value": "pacific_islander", "label": {"en": "Native Hawaiian / Pacific Islander", "vi": "Hawaii / Thái Bình Dương"}},
        {"value": "other", "label": {"en": "Other race", "vi": "Chủng tộc khác"}},
    ]
    eth_opts = [
        {"value": "hispanic", "label": {"en": "Hispanic or Latino", "vi": "Gốc Tây Ban Nha hoặc La-tinh"}},
        {"value": "not_hispanic", "label": {"en": "Not Hispanic or Latino", "vi": "Không gốc Tây Ban Nha"}},
        {"value": "unknown", "label": {"en": "Unknown", "vi": "Không rõ"}},
    ]
    return [
        field(
            "patient_name", "text", "Patient Name", "Họ và tên bệnh nhân",
            "What is your full legal name?", "Xin cho biết họ và tên đầy đủ của bạn?",
            # Sit on underline just below label baseline (adult row gap ~22pt).
            1, "personal", True, validation={
                **txt(121.5, name_x, maxLength=100),
                "also_at": [
                    {"page": 2, "x": 125, "y": 670.0},
                    {"page": 3, "x": 220, "y": 85.0},
                ],
            },
        ),
        field(
            "birthday", "date", "Birthday", "Ngày sinh",
            "What is your date of birth?", "Ngày sinh của bạn là ngày nào?",
            1, "personal", True, validation={
                **txt(145.5, dob_x),
                "also_at": [
                    {"page": 2, "x": 480, "y": 670.0},
                ],
            },
        ),
        field(
            "ssn", "ssn", "SSN", "Số SSN",
            "What is your Social Security Number? Say none if you don't have one.",
            "Số SSN của bạn là gì? Nếu không có, nói không có.",
            1, "personal", False, validation=txt(145.5, ssn_x),
        ),
        field(
            "home_address", "textarea", "Home Address", "Địa chỉ nhà",
            "What is your home address?", "Địa chỉ nhà của bạn là gì?",
            1, "personal", True, validation=txt(167.5, addr_x),
        ),
        field(
            "home_phone", "phone", "Home Phone", "Điện thoại nhà",
            "What is your home phone number? Say none if you don't have one.",
            "Số điện thoại nhà? Nếu không có, nói không có.",
            1, "personal", False, validation=txt(189.5, home_phone_x),
        ),
        field(
            "cell_phone", "phone", "Cell Phone", "Số di động",
            "What is your cell phone number?", "Số điện thoại di động của bạn là gì?",
            1, "personal", True, validation=txt(189.5, cell_x),
        ),
        field(
            "email", "email", "Email", "Email",
            "What is your email address? Say none if you don't have one.",
            "Địa chỉ email của bạn? Nếu không có, nói không có.",
            1, "personal", False, validation=txt(189.5, email_x),
        ),
        field(
            "insurance", "select", "Insurance", "Bảo hiểm",
            "What insurance do you have? Medicare, Medi-Cal, PPO, HMO, or uninsured?",
            "Bạn có loại bảo hiểm nào? Medicare, Medi-Cal, PPO, HMO, hay không có?",
            1, "insurance", True, ins_opts,
            validation={
                "checkbox_positions": {
                    "medicare": cb(210, 108),
                    "medi_cal": cb(210, 216),
                    "ppo": cb(210, 324),
                    "hmo": cb(210, 432),
                    "uninsured": cb(210, uninsured_key_left),
                }
            },
        ),
        field(
            "race", "multiselect", "Race", "Chủng tộc",
            "What is your race? You may select multiple.",
            "Chủng tộc của bạn? Có thể chọn nhiều.",
            1, "demographics", False, race_opts,
            validation={
                "checkbox_positions": {
                    "asian": cb(226, 108),
                    "white": cb(226, 216),
                    "african_american": cb(226, 324),
                    "native_american": cb(242, 108),
                    "other": cb(242, 324),
                    "pacific_islander": cb(258, 108),
                }
            },
        ),
        field(
            "race_other_specify", "text", "Other race (specify)", "Chủng tộc khác (ghi rõ)",
            "If you selected other race, please specify. Say none if not applicable.",
            "Nếu chọn chủng tộc khác, xin ghi rõ. Nếu không, nói không có.",
            1, "demographics", False, validation=txt(242, 430),
        ),
        field(
            "ethnicity", "select", "Ethnicity", "Dân tộc",
            "What is your ethnicity? Hispanic or Latino, Not Hispanic or Latino, or Unknown?",
            "Dân tộc: Gốc Tây Ban Nha/La-tinh, không, hay không rõ?",
            1, "demographics", False, eth_opts,
            validation={
                "checkbox_positions": {
                    "hispanic": cb(274, 108),
                    "not_hispanic": cb(274, 216),
                    "unknown": cb(274, 360),
                }
            },
        ),
    ]


def write_schema(form_id: str, filename: str, title: dict, lang: str, default: bool = False) -> Path:
    sections = [
        {"id": "personal", "title": {"en": "Personal Information", "vi": "Thông tin cá nhân"}, "order": 1},
        {"id": "insurance", "title": {"en": "Insurance", "vi": "Bảo hiểm"}, "order": 2},
        {"id": "demographics", "title": {"en": "Demographics", "vi": "Nhân khẩu học"}, "order": 3},
    ]
    data = {
        "id": form_id,
        "filename": filename,
        "title": title,
        "version": "1.0.0",
        "default": default,
        "sections": sections,
        "fields": personal_fields(lang),
    }
    out = SCHEMA_DIR / f"{form_id}.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("wrote", out, "fields", len(data["fields"]))
    return out


def main() -> None:
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    write_schema(
        "adult_en",
        "adult_en.pdf",
        {"en": "Adult Registration (English)", "vi": "Đơn ghi danh người lớn (Tiếng Anh)"},
        lang="en",
        default=False,
    )
    write_schema(
        "adult_vn",
        "adult_vn.pdf",
        {"en": "Adult Registration (Vietnamese)", "vi": "Đơn ghi danh người lớn (Tiếng Việt)"},
        lang="vi",
        default=False,
    )


if __name__ == "__main__":
    main()
