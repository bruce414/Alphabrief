from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import CanvasElementType, ConnectionType, ProvenanceKind
from app.models.canvas_connection import CanvasConnection
from app.models.canvas_element import CanvasElement
from app.models.project import Project
from app.models.user import User
from app.repositories.canvas_repository import CanvasRepository
from app.services.graph_context_service import build_graph_context


async def _seed_project(db: AsyncSession) -> tuple[User, Project, UUID]:
    user = User(
        id=uuid4(),
        email=f"{uuid4()}@example.com",
        password_hash="hash",
        display_name="Tester",
    )
    project = Project(
        id=uuid4(),
        user_id=user.id,
        kind="THESIS",
        title="Graph context project",
        description=None,
        archived_at=None,
        metadata_={},
    )
    db.add(user)
    db.add(project)
    await db.flush()
    canvas = await CanvasRepository(db).create_for_project(project_id=project.id, user_id=user.id)
    return user, project, canvas.id


def _element(
    *,
    canvas_id: UUID,
    project_id: UUID,
    user_id: UUID,
    element_type: str,
    title: str,
    content_markdown: str,
) -> CanvasElement:
    return CanvasElement(
        canvas_id=canvas_id,
        project_id=project_id,
        user_id=user_id,
        element_type=element_type,
        title=title,
        content_markdown=content_markdown,
        content_json={},
        x=Decimal("100"),
        y=Decimal("100"),
        width=Decimal("200"),
        height=Decimal("120"),
        z_index=0,
        style_json=None,
        provenance_kind=ProvenanceKind.MANUAL.value,
        provenance_chat_turn_id=None,
        provenance_source_id=None,
        confidence_label=None,
        archived_at=None,
    )


@pytest.mark.asyncio
async def test_empty_project_returns_none(db_session: AsyncSession) -> None:
    _, project, _ = await _seed_project(db_session)
    result = await build_graph_context(db_session, project.id, "supply chain risks")
    assert result.markdown is None
    assert result.node_count is None


@pytest.mark.asyncio
async def test_direction_only_returns_center_with_zero_node_count(db_session: AsyncSession) -> None:
    user, project, canvas_id = await _seed_project(db_session)
    db_session.add(
        _element(
            canvas_id=canvas_id,
            project_id=project.id,
            user_id=user.id,
            element_type=CanvasElementType.DIRECTION.value,
            title="AI chips thesis",
            content_markdown="Track supply constraints and pricing power.",
        )
    )
    await db_session.commit()

    result = await build_graph_context(db_session, project.id, "pricing power")
    assert result.markdown is not None
    assert "**Center:** AI chips thesis" in result.markdown
    assert "Relevant accepted insights" in result.markdown
    assert "(none matched this message)" in result.markdown
    assert result.node_count == 0


@pytest.mark.asyncio
async def test_no_matching_tokens_returns_center_only(db_session: AsyncSession) -> None:
    user, project, canvas_id = await _seed_project(db_session)
    db_session.add(
        _element(
            canvas_id=canvas_id,
            project_id=project.id,
            user_id=user.id,
            element_type=CanvasElementType.DIRECTION.value,
            title="Direction",
            content_markdown="Summary",
        )
    )
    db_session.add(
        _element(
            canvas_id=canvas_id,
            project_id=project.id,
            user_id=user.id,
            element_type=CanvasElementType.CLAIM.value,
            title="Unrelated topic",
            content_markdown="zzzz quantum widgets",
        )
    )
    await db_session.commit()

    result = await build_graph_context(db_session, project.id, "the and for")
    assert result.markdown is not None
    assert "[CLAIM] Unrelated topic" not in result.markdown
    assert result.node_count == 0


@pytest.mark.asyncio
async def test_matching_elements_limited_to_max_nodes_minus_one(db_session: AsyncSession) -> None:
    user, project, canvas_id = await _seed_project(db_session)
    db_session.add(
        _element(
            canvas_id=canvas_id,
            project_id=project.id,
            user_id=user.id,
            element_type=CanvasElementType.DIRECTION.value,
            title="Direction",
            content_markdown="Summary",
        )
    )
    for idx in range(12):
        db_session.add(
            _element(
                canvas_id=canvas_id,
                project_id=project.id,
                user_id=user.id,
                element_type=CanvasElementType.CLAIM.value,
                title=f"Supply claim {idx}",
                content_markdown=f"supply chain detail {idx}",
            )
        )
    await db_session.commit()

    result = await build_graph_context(
        db_session,
        project.id,
        "supply chain",
        max_nodes=5,
    )
    assert result.markdown is not None
    included = [line for line in result.markdown.splitlines() if line.startswith("- [CLAIM]")]
    assert len(included) == 4
    assert result.node_count == 5


@pytest.mark.asyncio
async def test_edges_only_between_selected_elements(db_session: AsyncSession) -> None:
    user, project, canvas_id = await _seed_project(db_session)
    direction = _element(
        canvas_id=canvas_id,
        project_id=project.id,
        user_id=user.id,
        element_type=CanvasElementType.DIRECTION.value,
        title="Direction",
        content_markdown="Summary",
    )
    risk = _element(
        canvas_id=canvas_id,
        project_id=project.id,
        user_id=user.id,
        element_type=CanvasElementType.RISK.value,
        title="Margin compression risk",
        content_markdown="Margins may compress if supply normalizes.",
    )
    claim = _element(
        canvas_id=canvas_id,
        project_id=project.id,
        user_id=user.id,
        element_type=CanvasElementType.CLAIM.value,
        title="Pricing power claim",
        content_markdown="Pricing power remains intact for leaders.",
    )
    outsider = _element(
        canvas_id=canvas_id,
        project_id=project.id,
        user_id=user.id,
        element_type=CanvasElementType.CLAIM.value,
        title="Outside claim",
        content_markdown="unrelated widgets",
    )
    db_session.add_all([direction, risk, claim, outsider])
    await db_session.flush()

    db_session.add(
        CanvasConnection(
            canvas_id=canvas_id,
            project_id=project.id,
            user_id=user.id,
            from_element_id=risk.id,
            to_element_id=claim.id,
            label=None,
            connection_type=ConnectionType.CONTRADICTS.value,
            style_json=None,
        )
    )
    db_session.add(
        CanvasConnection(
            canvas_id=canvas_id,
            project_id=project.id,
            user_id=user.id,
            from_element_id=risk.id,
            to_element_id=outsider.id,
            label=None,
            connection_type=ConnectionType.CONTRADICTS.value,
            style_json=None,
        )
    )
    await db_session.commit()

    result = await build_graph_context(db_session, project.id, "margin pricing")
    assert result.markdown is not None
    assert "contradicts → [Pricing power claim]" in result.markdown
    assert "Outside claim" not in result.markdown


@pytest.mark.asyncio
async def test_token_budget_trims_bottom_insights(db_session: AsyncSession) -> None:
    user, project, canvas_id = await _seed_project(db_session)
    db_session.add(
        _element(
            canvas_id=canvas_id,
            project_id=project.id,
            user_id=user.id,
            element_type=CanvasElementType.DIRECTION.value,
            title="Direction",
            content_markdown="Short center",
        )
    )
    for idx in range(6):
        db_session.add(
            _element(
                canvas_id=canvas_id,
                project_id=project.id,
                user_id=user.id,
                element_type=CanvasElementType.CLAIM.value,
                title=f"Supply claim {idx}",
                content_markdown="supply " + ("x" * 400),
            )
        )
    await db_session.commit()

    result = await build_graph_context(
        db_session,
        project.id,
        "supply",
        max_nodes=10,
        max_tokens=120,
    )
    assert result.markdown is not None
    included = [line for line in result.markdown.splitlines() if line.startswith("- [CLAIM]")]
    assert len(included) < 6
    assert len(result.markdown) // 4 <= 120 + 40
