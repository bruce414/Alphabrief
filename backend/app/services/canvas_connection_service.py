from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ConnectionType
from app.core.errors import AppError
from app.models.canvas import Canvas
from app.models.canvas_connection import CanvasConnection
from app.repositories.canvas_connection_repository import CanvasConnectionRepository
from app.repositories.canvas_element_repository import CanvasElementRepository


_UNSET = object()
ALLOWED_PROPOSAL_EDGE_TYPES = frozenset({"supports", "contradicts", "affects"})
_ALLOWED_PROPOSAL_EDGE_TYPES = ALLOWED_PROPOSAL_EDGE_TYPES


class CanvasConnectionService:
    def __init__(
        self,
        *,
        db: AsyncSession,
        connection_repo: CanvasConnectionRepository,
        element_repo: CanvasElementRepository,
    ) -> None:
        self._db = db
        self._connection_repo = connection_repo
        self._element_repo = element_repo

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
    ) -> list[CanvasConnection]:
        await self._get_canvas_owned(user_id=user_id, canvas_id=canvas_id)
        return await self._connection_repo.list_for_canvas(canvas_id=canvas_id)

    async def create(
        self,
        *,
        user_id: UUID,
        canvas_id: UUID,
        from_element_id: UUID,
        to_element_id: UUID,
        label: str | None,
        connection_type: ConnectionType | str,
        style_json: dict[str, Any] | None,
        commit: bool = True,
    ) -> CanvasConnection:
        canvas = await self._get_canvas_owned(user_id=user_id, canvas_id=canvas_id)

        from_el = await self._element_repo.get_by_id(from_element_id)
        to_el = await self._element_repo.get_by_id(to_element_id)

        if from_el is None or to_el is None:
            raise AppError(
                error_code="CANVAS_ELEMENT_NOT_FOUND",
                message="Canvas element not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if from_el.canvas_id != canvas_id or to_el.canvas_id != canvas_id:
            raise AppError(
                error_code="INVALID_INPUT",
                message="Both endpoints must belong to this canvas",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        ct_value = connection_type.value if isinstance(connection_type, ConnectionType) else str(connection_type)
        self._validate_connection_type(ct_value)

        conn = CanvasConnection(
            canvas_id=canvas.id,
            project_id=canvas.project_id,
            user_id=user_id,
            from_element_id=from_element_id,
            to_element_id=to_element_id,
            label=label,
            connection_type=ct_value,
            style_json=style_json,
        )
        return await self._connection_repo.create(conn, commit=commit)

    async def patch(
        self,
        *,
        user_id: UUID,
        connection_id: UUID,
        label: Any = _UNSET,
        connection_type: Any = _UNSET,
        style_json: Any = _UNSET,
    ) -> CanvasConnection:
        conn = await self._connection_repo.get_by_id(connection_id)
        if conn is None:
            raise AppError(
                error_code="CANVAS_CONNECTION_NOT_FOUND",
                message="Canvas connection not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if conn.user_id != user_id:
            raise AppError(
                error_code="FORBIDDEN",
                message="You do not have access to this canvas connection",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        if label is not _UNSET:
            conn.label = label
        if connection_type is not _UNSET:
            ct_value = (
                connection_type.value
                if isinstance(connection_type, ConnectionType)
                else str(connection_type)
            )
            self._validate_connection_type(ct_value)
            conn.connection_type = ct_value
        if style_json is not _UNSET:
            conn.style_json = style_json

        return await self._connection_repo.update(conn)

    async def delete(self, *, user_id: UUID, connection_id: UUID) -> None:
        conn = await self._connection_repo.get_by_id(connection_id)
        if conn is None:
            raise AppError(
                error_code="CANVAS_CONNECTION_NOT_FOUND",
                message="Canvas connection not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if conn.user_id != user_id:
            raise AppError(
                error_code="FORBIDDEN",
                message="You do not have access to this canvas connection",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        await self._connection_repo.delete(conn)

    @staticmethod
    def _validate_connection_type(value: str) -> None:
        if value in _ALLOWED_PROPOSAL_EDGE_TYPES:
            return
        try:
            ConnectionType(value)
        except ValueError:
            raise AppError(
                error_code="INVALID_INPUT",
                message="Invalid input",
                status_code=status.HTTP_400_BAD_REQUEST,
            ) from None
