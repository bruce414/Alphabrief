"""SQLAlchemy models package.

Import each model module so classes register on ``Base.metadata`` and Alembic
``--autogenerate`` can detect them. Shared column mixins live in ``app.db.base``.
"""

from app.models.user import User
from app.models.project import Project
from app.models.chat import Chat
from app.models.brief import Brief
from app.models.brief_source import BriefSource
from app.models.source import Source
from app.models.source_fetch_log import SourceFetchLog
from app.models.source_fetch_policy import SourceFetchPolicy
from app.models.source_scan import SourceScan
from app.models.source_segment import SourceSegment
from app.models.usage_event import UsageEvent
from app.models.chat_turn import ChatTurn
from app.models.chat_turn_source import ChatTurnSource
from app.models.canvas_snapshot import CanvasSnapshot
from app.models.brief_version import BriefVersion

# v0.3 freeform Canvas world (DATA_MODEL.md §4.9–§4.13).
from app.models.canvas import Canvas
from app.models.canvas_element import CanvasElement
from app.models.canvas_connection import CanvasConnection
from app.models.candidate_element import CandidateElement
from app.models.project_memory import ProjectMemory

__all__ = [
    "Brief",
    "BriefVersion",
    "BriefSource",
    "Canvas",
    "CanvasConnection",
    "CanvasElement",
    "CanvasSnapshot",
    "CandidateElement",
    "Chat",
    "ChatTurn",
    "ChatTurnSource",
    "Project",
    "ProjectMemory",
    "Source",
    "SourceFetchLog",
    "SourceFetchPolicy",
    "SourceScan",
    "SourceSegment",
    "UsageEvent",
    "User",
]
