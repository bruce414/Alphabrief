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
from app.models.usage_event import UsageEvent

__all__ = [
    "Brief",
    "BriefSource",
    "Source",
    "SourceFetchLog",
    "SourceFetchPolicy",
    "UsageEvent",
    "User",
]
