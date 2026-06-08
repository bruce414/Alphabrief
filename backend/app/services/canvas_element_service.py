from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import CanvasElementType, ProvenanceKind
from app.core.errors import AppError
from app.models.candidate_element import CandidateElement
from app.models.canvas import Canvas
from app.models.canvas_element import CanvasElement
from app.models.chat import Chat
from app.models.chat_turn import ChatTurn
from app.repositories.canvas_element_repository import CanvasElementRepository
from app.repositories.source_repository import SourceRepository


def _now_utc() -> datetime:
    return datetime.now(UTC)


_SOURCE_ELEMENT_TYPES = frozenset(
    {
        CanvasElementType.QUOTE.value,
        CanvasElementType.EVIDENCE.value,
        CanvasElementType.DATA.value,
        CanvasElementType.TEXT.value,
    }
)

_PATCH_KEYS = frozenset(
    {
        "title",
        "content_markdown",
        "content_json",
        "element_type",
        "x",
        "y",
        "width",
        "height",
        "z_index",
        "style_json",
        "archived",
    }
)


class CanvasElementService:
    def __init__(
        self,
        *,
        db: AsyncSession,
        element_repo: CanvasElementRepository,
        source_repo: SourceRepository,
    ) -> None:
        self._db = db
        self._element_repo = element_repo
        self._source_repo = source_repo

    async def _get_canvas_owned(self, *, user_id: UUID, canvas_id: UUID) -> Canvas:
        result = await self._db.execute(select(Canvas).where(Canvas.id == canvas_id))
        canvas = result.scalar_one_or_none()
        if canvas is None:
            raise AppError(
                error_code="CANVAS_NOT_FOUND",
                message="Canvas not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if canvas.user_id != user_id:
            raise AppError(
                error_code="FORBIDDEN",
                message="You do not have access to this canvas",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        return canvas

    async def list_for_canvas(
        self,
        *,
        user_id: UUID,
        canvas_id: UUID,
        include_archived: bool,
    ) -> list[CanvasElement]:
        await self._get_canvas_owned(user_id=user_id, canvas_id=canvas_id)
        return await self._element_repo.list_for_canvas(
            canvas_id=canvas_id,
            include_archived=include_archived,
        )

    async def create_manual(
        self,
        *,
        user_id: UUID,
        canvas_id: UUID,
        element_type: CanvasElementType,
        title: str | None,
        content_markdown: str | None,
        content_json: dict[str, Any] | None,
        x: Decimal,
        y: Decimal,
        width: Decimal | None,
        height: Decimal | None,
        style_json: dict[str, Any] | None,
    ) -> CanvasElement:
        canvas = await self._get_canvas_owned(user_id=user_id, canvas_id=canvas_id)
        element = CanvasElement(
            canvas_id=canvas.id,
            project_id=canvas.project_id,
            user_id=user_id,
            element_type=element_type.value,
            title=title,
            content_markdown=content_markdown,
            content_json=content_json or {},
            x=x,
            y=y,
            width=width,
            height=height,
            z_index=0,
            style_json=style_json,
            provenance_kind=ProvenanceKind.MANUAL.value,
            provenance_chat_turn_id=None,
            provenance_source_id=None,
            confidence_label=None,
            archived_at=None,
        )
        return await self._element_repo.create(element)

    async def create_from_candidate(
        self,
        *,
        user_id: UUID,
        canvas_id: UUID,
        candidate: CandidateElement,
        element_type: CanvasElementType,
        title: str | None,
        content_markdown: str,
        x: Decimal,
        y: Decimal,
        width: Decimal | None,
        height: Decimal | None,
        commit: bool = True,
    ) -> CanvasElement:
        canvas = await self._get_canvas_owned(user_id=user_id, canvas_id=canvas_id)
        if canvas.project_id != candidate.project_id:
            raise AppError(
                error_code="INVALID_INPUT",
                message="Canvas does not belong to this candidate's project",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        element = CanvasElement(
            canvas_id=canvas.id,
            project_id=canvas.project_id,
            user_id=user_id,
            element_type=element_type.value,
            title=title,
            content_markdown=content_markdown,
            content_json=candidate.content_json or {},
            x=x,
            y=y,
            width=width,
            height=height,
            z_index=0,
            style_json=None,
            provenance_kind=ProvenanceKind.CANDIDATE.value,
            provenance_chat_turn_id=candidate.chat_turn_id,
            provenance_source_id=None,
            confidence_label=None,
            archived_at=None,
        )
        return await self._element_repo.create(element, commit=commit)

    async def create_from_turn(
        self,
        *,
        user_id: UUID,
        canvas_id: UUID,
        chat_turn_id: UUID,
        element_type: CanvasElementType,
        title: str | None,
        content_markdown: str | None,
        x: Decimal,
        y: Decimal,
        width: Decimal | None,
        height: Decimal | None,
    ) -> CanvasElement:
        canvas = await self._get_canvas_owned(user_id=user_id, canvas_id=canvas_id)

        stmt = (
            select(ChatTurn, Chat.project_id)
            .join(Chat, Chat.id == ChatTurn.chat_id)
            .where(ChatTurn.id == chat_turn_id)
        )
        row = (await self._db.execute(stmt)).first()
        if row is None:
            raise AppError(
                error_code="NOT_FOUND",
                message="Chat turn not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        turn: ChatTurn = row[0]
        turn_project_id: UUID = row[1]
        if turn.user_id != user_id:
            raise AppError(
                error_code="FORBIDDEN",
                message="You do not have access to this chat turn",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        if turn_project_id != canvas.project_id:
            raise AppError(
                error_code="INVALID_INPUT",
                message="Chat turn does not belong to this project",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        resolved_markdown = content_markdown if content_markdown is not None else (turn.content_markdown or "")

        element = CanvasElement(
            canvas_id=canvas.id,
            project_id=canvas.project_id,
            user_id=user_id,
            element_type=element_type.value,
            title=title,
            content_markdown=resolved_markdown,
            content_json={},
            x=x,
            y=y,
            width=width,
            height=height,
            z_index=0,
            style_json=None,
            provenance_kind=ProvenanceKind.CHAT_TURN.value,
            provenance_chat_turn_id=chat_turn_id,
            provenance_source_id=None,
            confidence_label=None,
            archived_at=None,
        )
        return await self._element_repo.create(element)

    async def create_from_source(
        self,
        *,
        user_id: UUID,
        canvas_id: UUID,
        source_id: UUID,
        element_type: CanvasElementType,
        title: str | None,
        content_markdown: str | None,
        x: Decimal,
        y: Decimal,
        width: Decimal | None,
        height: Decimal | None,
    ) -> CanvasElement:
        canvas = await self._get_canvas_owned(user_id=user_id, canvas_id=canvas_id)

        if element_type.value not in _SOURCE_ELEMENT_TYPES:
            raise AppError(
                error_code="INVALID_INPUT",
                message="Invalid input",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        src = await self._source_repo.get_by_id_for_user(source_id=source_id, user_id=user_id)
        if src is None:
            raise AppError(
                error_code="NOT_FOUND",
                message="Source not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        element = CanvasElement(
            canvas_id=canvas.id,
            project_id=canvas.project_id,
            user_id=user_id,
            element_type=element_type.value,
            title=title,
            content_markdown=content_markdown,
            content_json={},
            x=x,
            y=y,
            width=width,
            height=height,
            z_index=0,
            style_json=None,
            provenance_kind=ProvenanceKind.SOURCE.value,
            provenance_chat_turn_id=None,
            provenance_source_id=source_id,
            confidence_label=None,
            archived_at=None,
        )
        return await self._element_repo.create(element)

    async def patch(
        self,
        *,
        user_id: UUID,
        element_id: UUID,
        **partial: Any,
    ) -> CanvasElement:
        unknown = set(partial.keys()) - _PATCH_KEYS
        if unknown:
            raise AppError(
                error_code="INVALID_INPUT",
                message="Invalid input",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        element = await self._element_repo.get_by_id(element_id)
        if element is None:
            raise AppError(
                error_code="CANVAS_ELEMENT_NOT_FOUND",
                message="Canvas element not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if element.user_id != user_id:
            raise AppError(
                error_code="FORBIDDEN",
                message="You do not have access to this canvas element",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        if "title" in partial:
            element.title = partial["title"]
        if "content_markdown" in partial:
            cm = partial["content_markdown"]
            if cm is not None and isinstance(cm, str) and not cm.strip():
                raise AppError(
                    error_code="INVALID_INPUT",
                    message="Invalid input",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            element.content_markdown = cm
        if "content_json" in partial:
            element.content_json = partial["content_json"] or {}
        if "element_type" in partial:
            raw = partial["element_type"]
            if isinstance(raw, CanvasElementType):
                element.element_type = raw.value
            else:
                try:
                    element.element_type = CanvasElementType(str(raw)).value
                except ValueError:
                    raise AppError(
                        error_code="INVALID_INPUT",
                        message="Invalid input",
                        status_code=status.HTTP_400_BAD_REQUEST,
                    ) from None
        if "x" in partial:
            element.x = self._to_decimal(partial["x"], field="x")
        if "y" in partial:
            element.y = self._to_decimal(partial["y"], field="y")
        if "width" in partial:
            element.width = self._optional_decimal(partial["width"])
        if "height" in partial:
            element.height = self._optional_decimal(partial["height"])
        if "z_index" in partial:
            element.z_index = int(partial["z_index"])
        if "style_json" in partial:
            element.style_json = partial["style_json"]
        if "archived" in partial:
            archived = partial["archived"]
            if archived is True:
                element.archived_at = _now_utc()
            elif archived is False:
                element.archived_at = None
            else:
                raise AppError(
                    error_code="INVALID_INPUT",
                    message="Invalid input",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        return await self._element_repo.update(element)

    async def delete(self, *, user_id: UUID, element_id: UUID) -> None:
        element = await self._element_repo.get_by_id(element_id)
        if element is None:
            raise AppError(
                error_code="CANVAS_ELEMENT_NOT_FOUND",
                message="Canvas element not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if element.user_id != user_id:
            raise AppError(
                error_code="FORBIDDEN",
                message="You do not have access to this canvas element",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        await self._element_repo.delete(element)

    @staticmethod
    def _to_decimal(value: Any, *, field: str) -> Decimal:
        try:
            return Decimal(str(value))
        except Exception:
            raise AppError(
                error_code="INVALID_INPUT",
                message=f"Invalid input for {field}",
                status_code=status.HTTP_400_BAD_REQUEST,
            ) from None

    @staticmethod
    def _optional_decimal(value: Any) -> Decimal | None:
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except Exception:
            raise AppError(
                error_code="INVALID_INPUT",
                message="Invalid input",
                status_code=status.HTTP_400_BAD_REQUEST,
            ) from None
