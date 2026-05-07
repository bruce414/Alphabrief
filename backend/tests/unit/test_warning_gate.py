from __future__ import annotations

from decimal import Decimal

import pytest

from app.core.enums import ResearchMode
from app.core.errors import WarningNotAcknowledgedError
from app.services.warning_gate import validate_warning_acknowledgement


class _DummyScan:
    def __init__(self, *, requires_warning: bool, pct: float, warning_level: str) -> None:
        self.requires_warning = requires_warning
        self.estimated_allowance_impact_percent = Decimal(str(pct))
        self.warning_level = warning_level


def test_requires_warning_true_ack_false_raises():
    scan = _DummyScan(requires_warning=True, pct=55.0, warning_level="HIGH")
    with pytest.raises(WarningNotAcknowledgedError) as excinfo:
        validate_warning_acknowledgement(
            scan, ResearchMode.STANDARD, acknowledged_high_usage_warning=False
        )
    assert excinfo.value.details["estimatedAllowanceImpactPercent"] == 55.0


def test_requires_warning_true_ack_true_ok():
    scan = _DummyScan(requires_warning=True, pct=55.0, warning_level="HIGH")
    validate_warning_acknowledgement(
        scan, ResearchMode.STANDARD, acknowledged_high_usage_warning=True
    )


def test_requires_warning_false_ack_false_ok():
    scan = _DummyScan(requires_warning=False, pct=55.0, warning_level="HIGH")
    validate_warning_acknowledgement(
        scan, ResearchMode.STANDARD, acknowledged_high_usage_warning=False
    )

