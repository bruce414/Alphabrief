from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

MarketMapNodeType = Literal[
    "main_event",
    "company",
    "sector_theme",
    "market_impact",
    "risk_uncertainty",
    "watch_next",
]

MarketMapLinkedSection = Literal[
    "summary",
    "why_it_matters",
    "market_impact",
    "risks_and_uncertainties",
    "watch_next",
]

MarketMapConfidence = Literal["low", "medium", "high"]

ALLOWED_EDGE_LABELS = frozenset(
    {
        "affects",
        "caused by",
        "increases risk for",
        "may benefit",
        "may pressure",
        "may offset",
        "depends on",
        "watch next",
        "linked to",
        "creates uncertainty around",
    }
)


class QuickChatAnalyzeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    source_url: str | None = Field(default=None, alias="sourceUrl")
    source_text: str | None = Field(default=None, alias="sourceText")
    user_query: str | None = Field(default=None, alias="userQuery")

    @model_validator(mode="after")
    def require_at_least_one_input(self) -> QuickChatAnalyzeRequest:
        if not any(
            [
                (self.source_url or "").strip(),
                (self.source_text or "").strip(),
                (self.user_query or "").strip(),
            ]
        ):
            raise ValueError("At least one of source_url, source_text, or user_query is required")
        return self


class QuickChatAnalysisBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    why_it_matters: str
    market_impact: str
    risks_and_uncertainties: str
    watch_next: list[str]


class MarketMapNodeSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: MarketMapNodeType
    label: str
    description: str
    linked_section: MarketMapLinkedSection | None = None
    confidence: MarketMapConfidence | None = None


class MarketMapEdgeSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    source: str
    target: str
    label: str
    description: str | None = None
    confidence: MarketMapConfidence | None = None


class MarketMapBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nodes: list[MarketMapNodeSchema]
    edges: list[MarketMapEdgeSchema]


class QuickChatAnalyzeSuccessResponse(BaseModel):
    """Successful source analysis payload (spec §19)."""

    model_config = ConfigDict(populate_by_name=True)

    analysis: QuickChatAnalysisBlock
    market_map: MarketMapBlock = Field(alias="marketMap")


class QuickChatAnalyzeErrorBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    error_code: str = Field(alias="errorCode")
    message: str


class QuickChatAnalyzeErrorResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    error: QuickChatAnalyzeErrorBody
