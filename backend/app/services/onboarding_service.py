from __future__ import annotations

import hashlib
import math
import re
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.enums import CanvasElementType, ProvenanceKind
from app.models.canvas_element import CanvasElement
from app.models.project import Project
from app.repositories.canvas_element_repository import CanvasElementRepository
from app.repositories.canvas_repository import CanvasRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.onboarding import ResearchDirection
from app.services.canvas_service import CanvasService

_DIRECTION_X = Decimal("400")
_DIRECTION_Y = Decimal("300")
_DIRECTION_W = Decimal("280")
_DIRECTION_H = Decimal("100")
_STICKY_W = Decimal("200")
_STICKY_H = Decimal("110")
_RADIAL_RADIUS = Decimal("320")
_ANGLE_OFFSET = math.pi / 8


def _use_onboarding_mock() -> bool:
    settings = get_settings()
    if settings.onboarding_use_mock:
        return True
    return not bool(settings.anthropic_api_key.strip())


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (slug[:60] or "direction").strip("-")


def _direction_center() -> tuple[Decimal, Decimal]:
    cx = _DIRECTION_X + _DIRECTION_W / 2
    cy = _DIRECTION_Y + _DIRECTION_H / 2
    return cx, cy


def _radial_sticky_xy(*, index: int, total: int) -> tuple[Decimal, Decimal]:
    cx, cy = _direction_center()
    angle = (2 * math.pi * index / total) + _ANGLE_OFFSET
    px = cx + _RADIAL_RADIUS * Decimal(str(math.cos(angle)))
    py = cy + _RADIAL_RADIUS * Decimal(str(math.sin(angle)))
    x = px - _STICKY_W / 2
    y = py - _STICKY_H / 2
    return x, y


def _mock_starter_elements(*, prefix: str) -> list[dict[str, Any]]:
    return [
        {
            "elementType": "STICKY_NOTE",
            "provenanceKind": "AI_ONBOARDING",
            "kind": "CLAIM",
            "title": f"{prefix}: core thesis",
            "body": f"Map how {prefix.lower()} could reshape margins and competitive positioning over the next 12–18 months.",
        },
        {
            "elementType": "STICKY_NOTE",
            "provenanceKind": "AI_ONBOARDING",
            "kind": "RISK",
            "title": f"{prefix}: key risk",
            "body": "List the top regulatory, demand, or funding risks that could invalidate the base case.",
        },
        {
            "elementType": "STICKY_NOTE",
            "provenanceKind": "AI_ONBOARDING",
            "kind": "EVIDENCE",
            "title": f"{prefix}: evidence to gather",
            "body": "Collect filings, earnings commentary, and third-party datasets that support or refute the thesis.",
        },
        {
            "elementType": "STICKY_NOTE",
            "provenanceKind": "AI_ONBOARDING",
            "kind": "QUESTION",
            "title": f"{prefix}: open question",
            "body": "What metric or catalyst would change your conviction if it moved materially?",
        },
    ]


_MOCK_TEMPLATES: list[dict[str, Any]] = [
    {
        "key": "ai-infra-2026",
        "title": "AI infrastructure capex cycle",
        "summary": "Track hyperscaler and chip supply dynamics shaping the next leg of AI buildout.",
        "researchGoal": "Understand who captures value in AI infrastructure spend through 2026.",
        "includedTopics": ["GPUs", "data centers", "cloud capex"],
        "excludedTopics": ["consumer apps"],
        "targetEntities": ["NVDA", "MSFT", "GOOGL", "AMZN"],
        "timeHorizon": "12-18 months",
    },
    {
        "key": "rates-credit-2026",
        "title": "Rates path and credit spreads",
        "summary": "Connect Fed policy signals to IG/HY spread behavior and refinancing risk.",
        "researchGoal": "Assess how rate volatility flows into credit and refinancing conditions.",
        "includedTopics": ["Fed policy", "IG spreads", "HY spreads"],
        "excludedTopics": ["FX carry"],
        "targetEntities": ["LQD", "HYG", "JPM"],
        "timeHorizon": "6-12 months",
    },
    {
        "key": "energy-transition",
        "title": "Energy transition supply chain",
        "summary": "Compare grid, storage, and upstream inputs for the electrification build cycle.",
        "researchGoal": "Map bottlenecks and margin pools across the energy transition stack.",
        "includedTopics": ["grid equipment", "battery metals", "utilities"],
        "excludedTopics": ["crypto mining"],
        "targetEntities": ["NEE", "ENPH", "CATL"],
        "timeHorizon": "2-3 years",
    },
    {
        "key": "biotech-pipeline",
        "title": "Biotech pipeline read-throughs",
        "summary": "Focus on late-stage readouts and payer uptake for select therapeutic areas.",
        "researchGoal": "Evaluate pipeline catalysts and commercialization risk for targeted biotech names.",
        "includedTopics": ["clinical trials", "FDA decisions", "payer coverage"],
        "excludedTopics": ["medical devices"],
        "targetEntities": ["MRNA", "REGN", "VRTX"],
        "timeHorizon": "12 months",
    },
    {
        "key": "em-consumer-2026",
        "title": "Emerging markets consumer recovery",
        "summary": "Contrast macro headwinds with category winners in EM consumer and fintech.",
        "researchGoal": "Identify durable EM consumer growth pockets despite macro volatility.",
        "includedTopics": ["EM FX", "consumer credit", "e-commerce"],
        "excludedTopics": ["commodities exporters"],
        "targetEntities": ["MELI", "SE", "BABA"],
        "timeHorizon": "18 months",
    },
]


def _mock_suggest_research_directions(description: str) -> list[dict[str, Any]]:
    # TODO: replace with real LLM call when ANTHROPIC_API_KEY is configured.
    seed = int(hashlib.sha256(description.encode()).hexdigest(), 16)
    start = seed % len(_MOCK_TEMPLATES)
    snippet = description.strip()[:48] or "your topic"
    directions: list[dict[str, Any]] = []
    for offset in range(3):
        template = dict(_MOCK_TEMPLATES[(start + offset) % len(_MOCK_TEMPLATES)])
        prefix = template["title"].split()[0]
        template["key"] = _slugify(f"{template['key']}-{snippet}")
        template["summary"] = (
            f"{template['summary']} Tailored to: {snippet}."
            if offset == 0
            else template["summary"]
        )
        template["starterElements"] = _mock_starter_elements(prefix=prefix)
        directions.append(template)
    return directions


def _normalize_direction(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "key": str(raw.get("key", "")).strip(),
        "title": str(raw.get("title", "")).strip()[:70],
        "summary": str(raw.get("summary", "")).strip(),
        "researchGoal": str(raw.get("researchGoal", raw.get("research_goal", ""))).strip(),
        "includedTopics": [
            str(x).strip() for x in (raw.get("includedTopics") or raw.get("included_topics") or []) if str(x).strip()
        ],
        "excludedTopics": [
            str(x).strip() for x in (raw.get("excludedTopics") or raw.get("excluded_topics") or []) if str(x).strip()
        ],
        "targetEntities": [
            str(x).strip() for x in (raw.get("targetEntities") or raw.get("target_entities") or []) if str(x).strip()
        ],
        "timeHorizon": raw.get("timeHorizon", raw.get("time_horizon")),
        "starterElements": raw.get("starterElements") or raw.get("starter_elements") or [],
    }


async def _has_direction_element(*, db: AsyncSession, project_id: UUID) -> bool:
    result = await db.execute(
        select(CanvasElement.id)
        .where(
            CanvasElement.project_id == project_id,
            CanvasElement.element_type == CanvasElementType.DIRECTION.value,
            CanvasElement.archived_at.is_(None),
        )
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def _create_direction_element(
    *,
    db: AsyncSession,
    canvas_id: UUID,
    project_id: UUID,
    user_id: UUID,
    title: str,
    content_markdown: str | None,
    provenance_kind: ProvenanceKind,
) -> CanvasElement:
    element_repo = CanvasElementRepository(db)
    direction = CanvasElement(
        canvas_id=canvas_id,
        project_id=project_id,
        user_id=user_id,
        element_type=CanvasElementType.DIRECTION.value,
        title=title,
        content_markdown=content_markdown,
        content_json={},
        x=_DIRECTION_X,
        y=_DIRECTION_Y,
        width=_DIRECTION_W,
        height=_DIRECTION_H,
        z_index=0,
        style_json=None,
        provenance_kind=provenance_kind.value,
        provenance_chat_turn_id=None,
        provenance_source_id=None,
        confidence_label=None,
        archived_at=None,
    )
    return await element_repo.create(direction)


async def ensure_direction_for_canvas(
    db: AsyncSession,
    project_id: UUID,
    fallback_title: str,
) -> None:
    if await _has_direction_element(db=db, project_id=project_id):
        return

    project_repo = ProjectRepository(db)
    project = await project_repo.get_by_id(project_id)
    if project is None:
        return

    canvas_svc = CanvasService(
        db=db,
        canvas_repo=CanvasRepository(db),
        project_repo=project_repo,
    )
    canvas = await canvas_svc.get_or_create_for_project(user_id=project.user_id, project_id=project_id)
    title = (fallback_title or "").strip()[:80] or "Research direction"
    await _create_direction_element(
        db=db,
        canvas_id=canvas.id,
        project_id=project.id,
        user_id=project.user_id,
        title=title,
        content_markdown="",
        provenance_kind=ProvenanceKind.AI_AUTO_DIRECTION,
    )


class OnboardingService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._project_repo = ProjectRepository(db)
        self._canvas_repo = CanvasRepository(db)
        self._element_repo = CanvasElementRepository(db)

    async def suggest_directions(self, *, project_id: UUID, description: str) -> dict[str, Any]:
        _ = project_id
        if _use_onboarding_mock():
            raw_directions = _mock_suggest_research_directions(description)
        else:
            from app.clients.anthropic_client import AnthropicClient

            client = AnthropicClient()
            raw_directions = await client.suggest_research_directions(description)

        directions = [ResearchDirection.model_validate(_normalize_direction(d)) for d in raw_directions]
        return {
            "suggestionId": uuid4(),
            "directions": [d.model_dump(by_alias=True) for d in directions],
        }

    async def apply_direction(
        self,
        *,
        user_id: UUID,
        project_id: UUID,
        direction: ResearchDirection,
    ) -> Project:
        project = await self._project_repo.get_by_id_for_user(project_id=project_id, user_id=user_id)
        if project is None:
            from fastapi import status

            from app.core.errors import AppError

            raise AppError(
                error_code="NOT_FOUND",
                message="Project not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        project.research_goal = direction.research_goal
        project.included_topics = direction.included_topics
        project.excluded_topics = direction.excluded_topics
        project.target_entities = direction.target_entities
        project.time_horizon = direction.time_horizon
        project = await self._project_repo.update(project)

        canvas_svc = CanvasService(
            db=self._db,
            canvas_repo=self._canvas_repo,
            project_repo=self._project_repo,
        )
        canvas = await canvas_svc.get_or_create_for_project(user_id=user_id, project_id=project_id)

        await _create_direction_element(
            db=self._db,
            canvas_id=canvas.id,
            project_id=project.id,
            user_id=user_id,
            title=direction.title,
            content_markdown=direction.summary,
            provenance_kind=ProvenanceKind.AI_ONBOARDING,
        )

        starters = direction.starter_elements
        total = len(starters)
        for index, starter in enumerate(starters):
            x, y = _radial_sticky_xy(index=index, total=total)
            sticky = CanvasElement(
                canvas_id=canvas.id,
                project_id=project.id,
                user_id=user_id,
                element_type=CanvasElementType.STICKY_NOTE.value,
                title=starter.title,
                content_markdown=starter.body,
                content_json={"kind": starter.kind},
                x=x,
                y=y,
                width=_STICKY_W,
                height=_STICKY_H,
                z_index=0,
                style_json=None,
                provenance_kind=ProvenanceKind.AI_ONBOARDING.value,
                provenance_chat_turn_id=None,
                provenance_source_id=None,
                confidence_label=None,
                archived_at=None,
            )
            await self._element_repo.create(sticky)

        return project
