from __future__ import annotations

from enum import Enum


class ProjectKind(str, Enum):
    CATCHALL = "CATCHALL"
    COVERAGE = "COVERAGE"
    THESIS = "THESIS"
    EVENT = "EVENT"
    THEME = "THEME"
    DECISION = "DECISION"


class ResearchScope(str, Enum):
    USER_PROVIDED_ONLY = "USER_PROVIDED_ONLY"
    RECOMMENDED_CONTEXT = "RECOMMENDED_CONTEXT"


class ResearchMode(str, Enum):
    QUICK = "QUICK"
    STANDARD = "STANDARD"
    DEEP = "DEEP"


class CompletionStrategy(str, Enum):
    STRICT_REQUESTED_MODE = "STRICT_REQUESTED_MODE"
    OPTIMIZE_RESEARCH = "OPTIMIZE_RESEARCH"


class CoverageMode(str, Enum):
    FULL_SOURCE = "FULL_SOURCE"
    SELECTED_TOPICS = "SELECTED_TOPICS"
    SELECTED_ENTITIES = "SELECTED_ENTITIES"
    CUSTOM_QUESTION = "CUSTOM_QUESTION"


class AnalysisIntent(str, Enum):
    QUICK_SUMMARY = "QUICK_SUMMARY"
    MARKET_IMPACT = "MARKET_IMPACT"
    COMPANY_ANALYSIS = "COMPANY_ANALYSIS"
    LEARNING_MODE = "LEARNING_MODE"
    STRUCTURED_BRIEF = "STRUCTURED_BRIEF"
    INSIDER_ACTIVITY = "INSIDER_ACTIVITY"


class ResearchItemStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class GenerationJobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AnalysisRunStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AnalysisSegmentStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AnalysisMode(str, Enum):
    SOURCE_BRIEF = "SOURCE_BRIEF"
    CONTEXT_BRIEF = "CONTEXT_BRIEF"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ChatStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class ChatTurnRole(str, Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"


class ChatTurnStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class CanvasBlockType(str, Enum):
    CLAIM = "CLAIM"
    QUOTE = "QUOTE"
    NOTE = "NOTE"
    SUMMARY = "SUMMARY"
    RISK = "RISK"
    QUESTION = "QUESTION"
    METRIC = "METRIC"
    BULL_CASE = "BULL_CASE"
    BEAR_CASE = "BEAR_CASE"


class ProvenanceKind(str, Enum):
    CHAT_TURN = "CHAT_TURN"
    SOURCE = "SOURCE"
    MANUAL = "MANUAL"
    CANDIDATE = "CANDIDATE"


class BriefType(str, Enum):
    COMPANY_RESEARCH = "COMPANY_RESEARCH"
    EARNINGS_BREAKDOWN = "EARNINGS_BREAKDOWN"
    SOURCE_SUMMARY = "SOURCE_SUMMARY"
    MARKET_EVENT_EXPLAINER = "MARKET_EVENT_EXPLAINER"
    THESIS_MEMO = "THESIS_MEMO"


class BriefStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class BriefVersionStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"

