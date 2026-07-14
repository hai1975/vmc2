"""Calibrate page-1 field coordinates from PDF label positions."""
from __future__ import annotations

import fitz

PAGE_H = 792.0


def y(top: float) -> float:
    return round(PAGE_H - top, 1)


def line_pos(label_bottom: float, x: float, drop: float = 14.0) -> dict:
    top = label_bottom + drop
    return {"x": x, "y": y(top)}


def find_label(page, *needles: str) -> tuple[float, float, float, float] | None:
    for w in page.get_text("words"):
        text = w[4]
        if any(n in text for n in needles):
            return w[0], w[1], w[2], w[3]
    return None


def calibrate_page1(pdf_path: str, pediatric: bool) -> dict:
    page = fitz.open(pdf_path)[0]
    out: dict = {}

    name = find_label(page, "Họ", "Patient")
    if name:
        out["patient_name"] = line_pos(name[3], 175)

    dob = find_label(page, "Ngày", "Birthday", "DOB")
    ssn = find_label(page, "SSN")
    if dob:
        out["birthday"] = line_pos(dob[3], 100)
    if ssn:
        out["ssn"] = line_pos(ssn[3], 410)

    if pediatric:
        g1 = find_label(page, "giám")
        # second giám row
        words = [w for w in page.get_text("words") if "giám" in w[4]]
        if words:
            w = words[0]
            out["guardian_1_name"] = line_pos(w[3], 255)
            out["guardian_1_relationship"] = line_pos(w[3], 470)
        if len(words) > 1:
            w = words[1]
            out["guardian_2_name"] = line_pos(w[3], 255)
            out["guardian_2_relationship"] = line_pos(w[3], 470)

    addr = find_label(page, "Địa chỉ", "Address", "địa chỉ", "chỉ nhà")
    if not addr:
        for w in page.get_text("words"):
            if "chỉ" in w[4] and "nhà" in page.get_text("text")[max(0, page.get_text("text").find(w[4]) - 20): page.get_text("text").find(w[4]) + 20]:
                addr = w
                break
    if not addr:
        for w in page.get_text("words"):
            if w[4].startswith("Địa") or w[4].startswith("Address"):
                addr = w
                break
    if addr:
        out["home_address"] = line_pos(addr[3], 130)

  # phone row - label contains điện thoại or Phone
    phone = None
    for w in page.get_text("words"):
        t = w[4].lower()
        if "điện" in t or t == "phone":
            phone = w
            break
    if phone:
        out["phone"] = line_pos(phone[3], 145)

    email = find_label(page, "Email")
    if email:
        out["email"] = line_pos(email[3], 330 if pediatric else 375)

    return out


if __name__ == "__main__":
    for pdf, ped in [("Form/adult_vn.pdf", False), ("Form/Child_vn.pdf", True)]:
        print(pdf, calibrate_page1(pdf, ped))
