"""Adult vs pediatric form field sets — PDFs differ (4 vs 5 pages)."""

PEDIATRIC_ONLY_FIELD_IDS = frozenset(
    {
        "guardian_1_name",
        "guardian_1_relationship",
        "guardian_2_name",
        "guardian_2_relationship",
        "main_caretaker",
        "caretaker_relationship",
        "pregnancy_complications",
        "mother_return_activities",
        "breastfeeding_or_formula",
        "uses_car_seat",
        "parent_drug_alcohol",
    }
)


def is_pediatric_form(form_id: str) -> bool:
    return form_id.startswith("child_")


def field_allowed_for_form(field_id: str, form_id: str) -> bool:
    if field_id in PEDIATRIC_ONLY_FIELD_IDS and not is_pediatric_form(form_id):
        return False
    return True


def build_form_variant_voice_section(form_id: str) -> str:
    if is_pediatric_form(form_id):
        return "\n".join(
            [
                "=== PEDIATRIC FORM (child registration) ===",
                "• Ask about the PATIENT (the child), not the adult speaking.",
                "• REQUIRED early: guardian_1_name and guardian_1_relationship — legal guardian on page 1.",
                "• guardian_2_* only if a second guardian exists; otherwise __skipped__.",
                "• Pediatric-only section: pregnancy_complications, mother_return_activities,",
                "  breastfeeding_or_formula, uses_car_seat, parent_drug_alcohol.",
                "• main_caretaker / caretaker_relationship if someone else cares for the child.",
            ]
        )
    return "\n".join(
        [
            "=== ADULT FORM ===",
            "• Do NOT ask guardian_1_name, guardian_2_name, or any pediatric-only fields —",
            "  they are NOT on the adult PDF.",
            "• Skip: pregnancy, breastfeeding, car seat, parent drug/alcohol questions.",
        ]
    )
