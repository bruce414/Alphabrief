from __future__ import annotations

from app.clients.edgar_form_categories import (
    CATEGORY_VALUES,
    FORM_TO_CATEGORY,
    categorize_form,
)


def test_all_known_forms_map_to_known_category_value():
    allowed = set(CATEGORY_VALUES)
    for form, category in FORM_TO_CATEGORY.items():
        assert isinstance(form, str)
        assert category in allowed


def test_unknown_form_defaults_to_other():
    assert categorize_form("NOT_A_FORM") == "OTHER"


def test_whitespace_is_tolerated():
    assert categorize_form("  10-Q  ") == "PERIODIC"

