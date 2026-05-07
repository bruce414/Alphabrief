"""SQLAlchemy models package.

Import each model module so classes register on ``Base.metadata`` and Alembic
``--autogenerate`` can detect them. Shared column mixins live in ``app.db.base``.
"""

from app.models.user import User
from app.models.brief import Brief
from app.models.brief_source import BriefSource
from app.models.source import Source
from app.models.source_fetch_log import SourceFetchLog
from app.models.source_fetch_policy import SourceFetchPolicy
from app.models.source_scan import SourceScan
from app.models.source_segment import SourceSegment
from app.models.usage_event import UsageEvent
from app.models.research_item import ResearchItem
from app.models.generation_job import GenerationJob
from app.models.analysis_run import AnalysisRun
from app.models.analysis_segment import AnalysisSegment

__all__ = [
    "AnalysisRun",
    "AnalysisSegment",
    "Brief",
    "BriefSource",
    "GenerationJob",
    "ResearchItem",
    "Source",
    "SourceFetchLog",
    "SourceFetchPolicy",
    "SourceScan",
    "SourceSegment",
    "UsageEvent",
    "User",
]
