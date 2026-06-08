from __future__ import annotations

FORM_TO_CATEGORY: dict[str, str] = {
    # PERIODIC — performance, earnings, material events
    "10-K": "PERIODIC",
    "10-K/A": "PERIODIC",
    "10-Q": "PERIODIC",
    "10-Q/A": "PERIODIC",
    "8-K": "PERIODIC",
    "8-K/A": "PERIODIC",
    "20-F": "PERIODIC",
    "40-F": "PERIODIC",
    "6-K": "PERIODIC",

    # GOVERNANCE — proxy, exec comp, board
    "DEF 14A": "GOVERNANCE",
    "PRE 14A": "GOVERNANCE",
    "DEFA14A": "GOVERNANCE",
    "DEFM14A": "GOVERNANCE",

    # INSIDER — Section 16 transactions
    "3": "INSIDER",
    "4": "INSIDER",
    "5": "INSIDER",
    "144": "INSIDER",

    # OWNERSHIP — beneficial ownership / activist stakes
    "SC 13D": "OWNERSHIP",
    "SC 13D/A": "OWNERSHIP",
    "SC 13G": "OWNERSHIP",
    "SC 13G/A": "OWNERSHIP",

    # CAPITAL_RAISE — issuance / registration
    "S-1": "CAPITAL_RAISE",
    "S-1/A": "CAPITAL_RAISE",
    "S-3": "CAPITAL_RAISE",
    "S-3/A": "CAPITAL_RAISE",
    "424B5": "CAPITAL_RAISE",
    "424B2": "CAPITAL_RAISE",
}


def categorize_form(form: str) -> str:
    """Return the research category for an EDGAR form string. Unknown → OTHER."""

    return FORM_TO_CATEGORY.get(form.strip(), "OTHER")


CATEGORY_VALUES = (
    "PERIODIC",
    "GOVERNANCE",
    "INSIDER",
    "OWNERSHIP",
    "CAPITAL_RAISE",
    "OTHER",
)

