"""Patch child/adult schema page-1 (and related) PDF coordinates to measured positions."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"

# reportlab y (origin bottom-left), measured on Child_en.pdf / adult_en.pdf
CHILD_EN = {
    "patient_name": {"x": 175, "y": 671.0},
    "birthday": {"x": 110, "y": 649.0},
    "ssn": {"x": 410, "y": 649.0},
    "guardian_1_name": {"x": 180, "y": 627.0},
    "guardian_1_relationship": {"x": 420, "y": 627.0},
    "guardian_2_name": {"x": 180, "y": 603.0},
    "guardian_2_relationship": {"x": 420, "y": 603.0},
    "home_address": {"x": 130, "y": 580.0},
    "phone": {"x": 145, "y": 558.0},
    "email": {"x": 375, "y": 558.0},
    # Page 2 medical history header
    "medical_history_patient_name": {"x": 125, "y": 661.0},
    "medical_history_dob": {"x": 480, "y": 661.0},
    # Page 3/4 electronic consent signature line (child form page 4 in 5-page PDF;
    # remote schema may use page 3 for adult-like layout — keep y for signature line)
    "consent_signer_name": {"x": 295, "y": 95.0},
}

CHILD_VN = {
    **CHILD_EN,
    "patient_name": {"x": 200, "y": 671.0},
    "birthday": {"x": 120, "y": 649.0},
    "ssn": {"x": 430, "y": 649.0},
    "guardian_1_name": {"x": 255, "y": 627.0},
    "guardian_1_relationship": {"x": 470, "y": 627.0},
    "guardian_2_name": {"x": 255, "y": 603.0},
    "guardian_2_relationship": {"x": 470, "y": 603.0},
    "home_address": {"x": 120, "y": 580.0},
    "phone": {"x": 160, "y": 558.0},
    "email": {"x": 340, "y": 558.0},
}

ADULT_EN = {
    "patient_name": {"x": 175, "y": 670.5},
    "birthday": {"x": 110, "y": 646.5},
    "ssn": {"x": 360, "y": 646.5},
    "home_address": {"x": 130, "y": 624.5},
    "phone": {"x": 145, "y": 602.5},
    "email": {"x": 440, "y": 602.5},
    "home_phone": {"x": 145, "y": 602.5},
    "cell_phone": {"x": 300, "y": 602.5},
    "medical_history_patient_name": {"x": 125, "y": 670.0},
    "medical_history_dob": {"x": 480, "y": 670.0},
    "consent_signer_name": {"x": 220, "y": 85.0},
}

ADULT_VN = {
    **ADULT_EN,
    "patient_name": {"x": 200, "y": 670.5},
    "birthday": {"x": 120, "y": 646.5},
    "ssn": {"x": 420, "y": 646.5},
    "home_address": {"x": 120, "y": 624.5},
    "phone": {"x": 160, "y": 602.5},
    "email": {"x": 480, "y": 602.5},
    "home_phone": {"x": 160, "y": 602.5},
    "cell_phone": {"x": 340, "y": 602.5},
}

PATCHES = {
    "child_en": CHILD_EN,
    "child_vn": CHILD_VN,
    "adult_en": ADULT_EN,
    "adult_vn": ADULT_VN,
}


def patch_schema(name: str, coords: dict) -> None:
    path = SCHEMA_DIR / f"{name}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    is_child = name.startswith("child")
    consent_page = 4 if is_child else 3
    updated = 0
    for field in data["fields"]:
        fid = field["id"]
        if fid in coords:
            val = field.setdefault("validation", {})
            val["x"] = coords[fid]["x"]
            val["y"] = coords[fid]["y"]
            updated += 1
        # Stop drawing X over electronic consent body text; page must match PDF.
        if fid == "electronic_communication_consent":
            field["page"] = consent_page
            field["validation"] = {}
            updated += 1
        if fid == "consent_signer_name":
            field["page"] = consent_page
            updated += 1
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"patched {path.name}: {updated} fields")


def main() -> None:
    for name, coords in PATCHES.items():
        patch_schema(name, coords)


if __name__ == "__main__":
    main()
