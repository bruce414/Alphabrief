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

