import json
import re
from typing import TypedDict


class PharmacyEntry(TypedDict):
    name: str
    address: str


DEFAULT_PHARMACIES: list[PharmacyEntry] = [
    {
        "name": "Lavina pharmacy",
        "address": "8251 Westminster Blvd, Ste 100. Westminster CA 92683",
    },
    {
        "name": "Professional pharmacy",
        "address": "7631 Westminster Blvd, Ste D. Westminster CA 92683",
    },
    {
        "name": "Q pharmacy",
        "address": "8401 Westminster Blvd. Westminster CA 92683",
    },
    {
        "name": "Walgreen pharmacy",
        "address": "8052 Westminster Blvd Westminster CA 9283",
    },
    {
        "name": "Hong pharmacy",
        "address": "8883 Westminster Blvd Garden Grove CA 92844",
    },
]


def default_pharmacy_list_json() -> str:
    return json.dumps(DEFAULT_PHARMACIES, ensure_ascii=False)


def format_pharmacy_line(entry: PharmacyEntry) -> str:
    return f"{entry['name']}: {entry['address']}"


def parse_pharmacy_list(raw: str | None) -> list[PharmacyEntry]:
    text = (raw or "").strip()
    if not text:
        return list(DEFAULT_PHARMACIES)

    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return _normalize_entries(parsed)
    except json.JSONDecodeError:
        pass

    entries: list[PharmacyEntry] = []
    for line in text.splitlines():
        cleaned = re.sub(r"^\s*\d+\s*[/.)-]\s*", "", line.strip())
        if not cleaned:
            continue
        if "|" in cleaned:
            name, address = cleaned.split("|", 1)
        elif ":" in cleaned:
            name, address = cleaned.split(":", 1)
        else:
            continue
        name = name.strip()
        address = address.strip()
        if name and address:
            entries.append({"name": name, "address": address})

    return entries or list(DEFAULT_PHARMACIES)


def _normalize_entries(items: list) -> list[PharmacyEntry]:
    entries: list[PharmacyEntry] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        address = str(item.get("address") or "").strip()
        if name and address:
            entries.append({"name": name, "address": address})
    return entries or list(DEFAULT_PHARMACIES)


def build_pharmacy_voice_section(pharmacies: list[PharmacyEntry]) -> str:
    if not pharmacies:
        return ""

    numbered = "\n".join(
        f"  {index + 1}. {format_pharmacy_line(entry)}"
        for index, entry in enumerate(pharmacies[:10])
    )
    first = format_pharmacy_line(pharmacies[0])
    alts = [format_pharmacy_line(p) for p in pharmacies[1:3]]
    alt_text = "; ".join(alts) if alts else ""

    return "\n".join(
        [
            "=== PHARMACY SUGGESTIONS (clinic default list) ===",
            "When you reach pharmacy_name:",
            "• Ask preferred pharmacy first (normal question).",
            "• If patient does NOT know, has none, or asks for help",
            "  (none / don't know / không biết / chưa có / không có nhà thuốc / gợi ý giúp):",
            f"  → Suggest option 1 first: {first}. Ask if they want to use it.",
            f"• If they decline, offer 1–2 alternatives: {alt_text or 'next items on the list'}.",
            "• If they accept a suggestion, save pharmacy_name with the pharmacy NAME.",
            "  Include address after a comma in pharmacy_name when helpful for the PDF.",
            "• For pharmacy_phone after a clinic suggestion with no phone on file, save __skipped__",
            "  unless the patient gives a number.",
            "• If they reject all suggestions, save pharmacy_name as __skipped__.",
            "Clinic pharmacy list:",
            numbered,
        ]
    )


def build_pharmacy_field_hint(
    pharmacies: list[PharmacyEntry],
    next_field_id: str | None,
    session_language: str = "en",
) -> str:
    if not pharmacies or next_field_id not in {"pharmacy_name", "pharmacy_phone"}:
        return ""

    first = format_pharmacy_line(pharmacies[0])
    alts = "; ".join(format_pharmacy_line(p) for p in pharmacies[1:3])

    if next_field_id == "pharmacy_phone":
        if session_language == "vi":
            return (
                "Nếu nhà thuốc vừa chọn từ danh sách phòng khám và bệnh nhân không có SĐT, "
                "lưu pharmacy_phone = __skipped__."
            )
        return (
            "If pharmacy was chosen from the clinic list and patient has no phone number, "
            "save pharmacy_phone = __skipped__."
        )

    if session_language == "vi":
        return (
            "Hỏi nhà thuốc ưa thích. Nếu bệnh nhân không biết/chưa có/không có nhà thuốc, "
            f"gợi ý ngay: {first}. Không đồng ý thì gợi ý thêm: {alts}. "
            "Đồng ý thì lưu tên (và địa chỉ sau dấu phẩy nếu cần)."
        )
    return (
        "Ask preferred pharmacy. If patient doesn't know or has none, "
        f"suggest first: {first}. If they decline, offer: {alts}. "
        "If they accept, save the name (and address after a comma if helpful)."
    )
