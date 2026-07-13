"""Backward-compatible re-exports — use field_prefill for new code."""

from app.services.medical_history_voice import migrate_legacy_medical_conditions  # noqa: F401
from app.services.field_prefill import (  # noqa: F401
    AUTHORIZATION_AUTO_FIELDS,
    AUTHORIZATION_PREFILL_SOURCES,
    apply_authorization_prefill,
    apply_authorization_voice_hints,
    apply_field_prefill,
    authorization_prefill_voice_hint,
    build_authorization_voice_section,
)
