"""SQLAlchemy models package.

Import each model module so classes register on ``Base.metadata`` and Alembic
``--autogenerate`` can detect them. Shared column mixins live in ``app.models.base``.
"""

from app.models.user import User
from app.models.brief import Brief
from app.models.brief_source import BriefSource

__all__ = ["Brief", "BriefSource", "User"]
