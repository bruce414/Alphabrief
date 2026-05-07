from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.enums import ResearchMode
from app.core.errors import WarningNotAcknowledgedError

if TYPE_CHECKING:
    from app.models.source_scan import SourceScan


def validate_warning_acknowledgement(
    source_scan: "SourceScan",
    requested_research_mode: ResearchMode,
    acknowledged_high_usage_warning: bool,
) -> None:
    """Raise WarningNotAcknowledgedError if scan requires a warning and user did not acknowledge."""

    _ = requested_research_mode  # reserved for future rule expansion
    if source_scan.requires_warning and not acknowledged_high_usage_warning:
        raise WarningNotAcknowledgedError(
            estimated_pct=float(source_scan.estimated_allowance_impact_percent),
            warning_level=source_scan.warning_level,
        )

