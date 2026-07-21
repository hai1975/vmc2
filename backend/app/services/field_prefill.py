"""Auto-fill repeated patient info fields across all PDF pages from data already collected."""

from app.models import FormSchema
from app.services.medical_history_voice import (
    apply_medical_history_cascades,
    migrate_legacy_medical_conditions,
)

# Target field -> canonical source field (copy when target empty and source has value).
SIMPLE_PREFILL_SOURCES: dict[str, str] = {
    # Page 2 — BỆNH LÝ / medical history header
    "medical_history_patient_name": "patient_name",
    "medical_history_dob": "birthday",
    # Page 4 — authorization for release
    "authorization_patient_name": "patient_name",
    "authorization_dob": "birthday",
    "release_authorization_name": "patient_name",
}

AUTO_PREFILL_FIELDS = frozenset(SIMPLE_PREFILL_SOURCES.keys()) | frozenset({"consent_signer_name"})

# Do not ask via voice — destination is fixed on the PDF (VM Medical Group). Leave blank on fill.
# Authorization header fields are auto-copied; records/purpose defaulted — voice only reads 2 consents.
VOICE_SKIP_FIELDS = frozenset(
    {
        "provider_facility_name",
        "provider_phone",
        "provider_fax",
        "medical_history_patient_name",
        "medical_history_dob",
        "authorization_patient_name",
        "authorization_dob",
        "release_authorization_name",
        "records_to_release",
        "disclosure_purpose",
    }
)

BLANK_VALUE = "__blank__"
SKIPPED_VALUE = "__skipped__"

# Defaults for authorization checkboxes (not asked by voice).
AUTHORIZATION_DEFAULTS: dict[str, object] = {
    "records_to_release": ["complete_record"],
    "disclosure_purpose": ["continuation_of_care"],
}

# Backward-compatible alias used by authorization module consumers.
AUTHORIZATION_PREFILL_SOURCES = {
    k: v
    for k, v in SIMPLE_PREFILL_SOURCES.items()
    if k.startswith("authorization_") or k == "release_authorization_name"
}
AUTHORIZATION_AUTO_FIELDS = frozenset(AUTHORIZATION_PREFILL_SOURCES.keys())


def _is_blank(value: object) -> bool:
    return value is None or value == "" or value == []


def _resolve_consent_signer_name(answers: dict, form_id: str = "") -> object | None:
    """Page 3 signature line: patient name, or guardian for pediatric forms."""
    if "child" in form_id:
        guardian = answers.get("guardian_1_name")
        if not _is_blank(guardian):
            return guardian
    patient = answers.get("patient_name")
    return patient if not _is_blank(patient) else None


def apply_field_prefill(answers: dict, form_id: str = "") -> dict:
    """Copy name, DOB, and signer fields into duplicate slots when still empty."""
    merged = migrate_legacy_medical_conditions(dict(answers))
    for target, source in SIMPLE_PREFILL_SOURCES.items():
        if not _is_blank(merged.get(target)) or _is_blank(merged.get(source)):
            continue
        merged[target] = merged[source]

    signer = _resolve_consent_signer_name(merged, form_id)
    if signer is not None and _is_blank(merged.get("consent_signer_name")):
        merged["consent_signer_name"] = signer

    # Provider lookup removed — leave these empty on the PDF unless already set.
    for field_id in ("provider_facility_name", "provider_phone", "provider_fax"):
        if _is_blank(merged.get(field_id)):
            merged[field_id] = BLANK_VALUE

    # Authorization page: auto name/DOB already copied; default release checkboxes.
    for field_id, default in AUTHORIZATION_DEFAULTS.items():
        if _is_blank(merged.get(field_id)):
            merged[field_id] = default

    return apply_medical_history_cascades(merged)


def apply_authorization_prefill(answers: dict, form_id: str = "") -> dict:
    """Backward-compatible entry point — applies all cross-page prefills."""
    return apply_field_prefill(answers, form_id)


def _prefilled_in_schema(schema: FormSchema, answers: dict, form_id: str = "") -> list[str]:
    merged = apply_field_prefill(answers, form_id)
    field_ids = {f.id for f in schema.fields}
    return [
        field_id
        for field_id in AUTO_PREFILL_FIELDS
        if field_id in field_ids and not _is_blank(merged.get(field_id))
    ]


def field_prefill_voice_hint(
    schema: FormSchema,
    answers: dict,
    session_language: str = "en",
    form_id: str = "",
) -> str:
    filled = _prefilled_in_schema(schema, answers, form_id)
    if not filled:
        return ""

    names = ", ".join(filled)
    if session_language == "vi":
        return (
            f"AUTO-FILL: {names} đã được điền từ thông tin đã thu thập — KHÔNG hỏi lại các trường này."
        )
    return (
        f"AUTO-FILL: {names} already copied from collected info — do NOT ask for these fields again."
    )


def apply_field_prefill_voice_hints(
    progress: dict,
    schema: FormSchema,
    answers: dict,
    session_language: str = "en",
    form_id: str = "",
) -> dict:
    hint = field_prefill_voice_hint(schema, answers, session_language, form_id)
    if hint:
        progress["voice_instruction"] = f"{progress.get('voice_instruction', '')} {hint}".strip()

    next_id = progress.get("next_field_id")
    if next_id in AUTO_PREFILL_FIELDS or next_id in VOICE_SKIP_FIELDS:
        skip_hint = (
            f"SKIP {next_id}: already auto-filled or not asked — advance to the next unfilled field."
        )
        progress["voice_instruction"] = f"{progress.get('voice_instruction', '')} {skip_hint}".strip()
    return progress


def build_field_prefill_voice_section() -> str:
    return "\n".join(
        [
            "=== AUTO-FILL ACROSS PAGES (never re-ask) ===",
            "• When patient_name, birthday, or guardian_1_name are already saved, copy into duplicate",
            "  fields on later pages — do NOT ask the patient again:",
            "  - medical_history_patient_name, medical_history_dob (page 2 BỆNH LÝ header)",
            "  - consent_signer_name (page 3 signature — guardian for child forms, else patient)",
            "  - authorization_patient_name, authorization_dob, release_authorization_name (authorization)",
            "• NEVER ask provider_facility_name, provider_phone, or provider_fax —",
            "  records release destination is printed on the form (VM Medical Group). Skip those fields.",
            "• NEVER ask records_to_release or disclosure_purpose — they default automatically.",
            "• Do NOT call lookup_provider_facility.",
            "• Continue with the next field that still needs a real answer.",
            "",
            "=== AUTHORIZATION FOR RELEASE OF INFORMATION ===",
            "• On this section, ONLY collect release_consent_acknowledgement.",
            "• Read the TWO consent paragraphs one-by-one (see CONSENT SECTIONS), then save true.",
            "• Do NOT ask patient name, DOB, provider, records types, or disclosure purpose on this page.",
            "",
            "=== TOBACCO / ALCOHOL / DRUGS ===",
            "• If tobacco_use=no, do NOT ask tobacco_frequency (auto-skipped).",
            "• If alcohol_use=no, do NOT ask alcohol_frequency (auto-skipped).",
            "• If recreational_drugs=no, do NOT ask recreational_drugs_list (auto-skipped).",
        ]
    )


# Backward-compatible names
authorization_prefill_voice_hint = field_prefill_voice_hint
apply_authorization_voice_hints = apply_field_prefill_voice_hints
build_authorization_voice_section = build_field_prefill_voice_section
