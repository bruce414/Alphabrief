from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, getcontext
from uuid import UUID

from fastapi import status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import CanvasBlockType, ProjectKind, ProvenanceKind
from app.core.errors import AppError
from app.models.canvas_block import CanvasBlock
from app.models.chat import Chat
from app.models.chat_turn import ChatTurn
from app.models.project import Project
from app.models.source import Source
from app.repositories.canvas_block_repository import CanvasBlockRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.source_repository import SourceRepository


getcontext().prec = 28

REBAlANCE_GAP_THRESHOLD = Decimal("0.000001")  # 1e-6


def _now_utc() -> datetime:
    return datetime.now(UTC)


class CanvasBlockService:
    def __init__(
        self,
        *,
        db: AsyncSession,
        repo: CanvasBlockRepository,
        project_repo: ProjectRepository,
        source_repo: SourceRepository,
    ) -> None:
        self._db = db
        self._repo = repo
        self._project_repo = project_repo
        self._source_repo = source_repo

    async def get_project_or_forbidden(self, *, user_id: UUID, project_id: UUID) -> Project:
        project = await self._project_repo.get_by_id(project_id)
        if project is None:
            raise AppError(
                error_code="NOT_FOUND",
                message="Project not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if project.user_id != user_id:
            raise AppError(
                error_code="FORBIDDEN",
                message="You do not have access to this project",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        return project

    async def should_suggest_project_conversion(self, *, project: Project) -> bool:
        if project.kind != ProjectKind.CATCHALL.value:
            return False

        active_blocks = await self._repo.count_active_for_project(project_id=project.id)
        if active_blocks >= 3:
            return True

        stmt = select(func.count()).select_from(Chat).where(
            Chat.project_id == project.id,
            Chat.status != "ARCHIVED",
        )
        result = await self._db.execute(stmt)
        active_chats = int(result.scalar_one())
        return active_chats >= 3

    async def list_blocks_for_project(
        self,
        *,
        user_id: UUID,
        project_id: UUID,
        include_archived: bool,
    ) -> tuple[list[CanvasBlock], bool]:
        project = await self.get_project_or_forbidden(user_id=user_id, project_id=project_id)

        active = await self._repo.list_active_for_project(project_id=project_id)
        if include_archived:
            all_blocks = await self._repo.list_for_project(project_id=project_id, include_archived=True)
            archived = [b for b in all_blocks if b.archived_at is not None]
            items = [*active, *archived]
        else:
            items = active

        suggest = await self.should_suggest_project_conversion(project=project)
        return items, suggest

    async def create_manual_block(
        self,
        *,
        user_id: UUID,
        project_id: UUID,
        block_type: CanvasBlockType,
        title: str | None,
        content_markdown: str,
        content_json: dict | None,
        position_after: UUID | None,
    ) -> CanvasBlock:
        project = await self.get_project_or_forbidden(user_id=user_id, project_id=project_id)
        position_index = await self._compute_position_index(project_id=project_id, position_after=position_after)

        metadata: dict = {}
        if project.kind == ProjectKind.CATCHALL.value:
            metadata["from_catchall"] = True

        block = CanvasBlock(
            project_id=project_id,
            user_id=user_id,
            block_type=block_type.value,
            title=title,
            content_markdown=content_markdown,
            content_json=content_json or {},
            position_index=position_index,
            provenance_kind=ProvenanceKind.MANUAL.value,
            provenance_chat_turn_id=None,
            provenance_source_id=None,
            confidence_label=None,
            archived_at=None,
            metadata_=metadata,
        )
        created = await self._repo.create(block)
        await self._maybe_rebalance_after_insert(project_id=project_id, inserted=created)
        await self._db.refresh(created)
        return created

    async def create_from_turn(
        self,
        *,
        user_id: UUID,
        project_id: UUID,
        chat_turn_id: UUID,
        block_type: CanvasBlockType,
        title: str | None,
        content_markdown: str | None,
        position_after: UUID | None,
    ) -> CanvasBlock:
        project = await self.get_project_or_forbidden(user_id=user_id, project_id=project_id)

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
        if turn_project_id != project_id:
            raise AppError(
                error_code="INVALID_INPUT",
                message="Chat turn does not belong to this project",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        position_index = await self._compute_position_index(project_id=project_id, position_after=position_after)

        metadata: dict = {}
        if project.kind == ProjectKind.CATCHALL.value:
            metadata["from_catchall"] = True

        block = CanvasBlock(
            project_id=project_id,
            user_id=user_id,
            block_type=block_type.value,
            title=title,
            content_markdown=(content_markdown if content_markdown is not None else (turn.content_markdown or "")),
            content_json={},
            position_index=position_index,
            provenance_kind=ProvenanceKind.CHAT_TURN.value,
            provenance_chat_turn_id=chat_turn_id,
            provenance_source_id=None,
            confidence_label=None,
            archived_at=None,
            metadata_=metadata,
        )
        if not block.content_markdown.strip():
            raise AppError(
                error_code="INVALID_INPUT",
                message="Invalid input",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        created = await self._repo.create(block)
        await self._maybe_rebalance_after_insert(project_id=project_id, inserted=created)
        await self._db.refresh(created)
        return created

    async def create_from_source(
        self,
        *,
        user_id: UUID,
        project_id: UUID,
        source_id: UUID,
        block_type: CanvasBlockType,
        title: str | None,
        content_markdown: str,
        position_after: UUID | None,
    ) -> CanvasBlock:
        project = await self.get_project_or_forbidden(user_id=user_id, project_id=project_id)
        src: Source | None = await self._source_repo.get_by_id_for_user(source_id=source_id, user_id=user_id)
        if src is None:
            raise AppError(
                error_code="NOT_FOUND",
                message="Source not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if block_type not in {CanvasBlockType.QUOTE, CanvasBlockType.SUMMARY, CanvasBlockType.NOTE}:
            raise AppError(
                error_code="INVALID_INPUT",
                message="Invalid input",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        position_index = await self._compute_position_index(project_id=project_id, position_after=position_after)

        metadata: dict = {}
        if project.kind == ProjectKind.CATCHALL.value:
            metadata["from_catchall"] = True

        block = CanvasBlock(
            project_id=project_id,
            user_id=user_id,
            block_type=block_type.value,
            title=title,
            content_markdown=content_markdown,
            content_json={},
            position_index=position_index,
            provenance_kind=ProvenanceKind.SOURCE.value,
            provenance_chat_turn_id=None,
            provenance_source_id=source_id,
            confidence_label=None,
            archived_at=None,
            metadata_=metadata,
        )
        created = await self._repo.create(block)
        await self._maybe_rebalance_after_insert(project_id=project_id, inserted=created)
        await self._db.refresh(created)
        return created

    async def patch_block(
        self,
        *,
        user_id: UUID,
        block_id: UUID,
        block_type: CanvasBlockType | None,
        title: str | None,
        content_markdown: str | None,
        content_json: dict | None,
        archived: bool | None,
        position_after: UUID | None,
        reposition: bool,
    ) -> CanvasBlock:
        block = await self._repo.get_by_id(block_id)
        if block is None:
            raise AppError(
                error_code="CANVAS_BLOCK_NOT_FOUND",
                message="Canvas block not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if block.user_id != user_id:
            raise AppError(
                error_code="FORBIDDEN",
                message="You do not have access to this canvas block",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        if block_type is not None:
            block.block_type = block_type.value
        if title is not None:
            block.title = title
        if content_markdown is not None:
            if not content_markdown.strip():
                raise AppError(
                    error_code="INVALID_INPUT",
                    message="Invalid input",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            block.content_markdown = content_markdown
        if content_json is not None:
            block.content_json = content_json
        if archived is not None:
            block.archived_at = _now_utc() if archived else None

        updated = await self._repo.update(block)

        if reposition:
            updated.position_index = await self._compute_position_index(project_id=updated.project_id, position_after=position_after)
            updated = await self._repo.update(updated)
            await self._maybe_rebalance_after_insert(project_id=updated.project_id, inserted=updated)
            await self._db.refresh(updated)

        return updated

    async def reorder_block(
        self,
        *,
        user_id: UUID,
        block_id: UUID,
        position_after: UUID | None,
    ) -> CanvasBlock:
        block = await self._repo.get_by_id(block_id)
        if block is None:
            raise AppError(
                error_code="CANVAS_BLOCK_NOT_FOUND",
                message="Canvas block not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if block.user_id != user_id:
            raise AppError(
                error_code="FORBIDDEN",
                message="You do not have access to this canvas block",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        block.position_index = await self._compute_position_index(project_id=block.project_id, position_after=position_after)
        updated = await self._repo.update(block)
        await self._maybe_rebalance_after_insert(project_id=block.project_id, inserted=updated)
        await self._db.refresh(updated)
        return updated

    async def delete_block(self, *, user_id: UUID, block_id: UUID) -> None:
        block = await self._repo.get_by_id(block_id)
        if block is None:
            raise AppError(
                error_code="CANVAS_BLOCK_NOT_FOUND",
                message="Canvas block not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if block.user_id != user_id:
            raise AppError(
                error_code="FORBIDDEN",
                message="You do not have access to this canvas block",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        await self._repo.delete(block)

    async def _compute_position_index(self, *, project_id: UUID, position_after: UUID | None) -> Decimal:
        if position_after is None:
            max_pos = await self._repo.get_max_active_position(project_id=project_id)
            return (max_pos + Decimal("1.0")) if max_pos is not None else Decimal("1.0")

        after = await self._repo.get_by_id(position_after)
        if after is None or after.project_id != project_id or after.archived_at is not None:
            raise AppError(
                error_code="INVALID_INPUT",
                message="Invalid positionAfter reference",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        nxt = await self._repo.get_next_active_after(project_id=project_id, position_index=after.position_index)
        if nxt is None:
            return after.position_index + Decimal("1.0")

        new_pos = (after.position_index + nxt.position_index) / Decimal(2)
        left_gap = new_pos - after.position_index
        right_gap = nxt.position_index - new_pos

        # Spec: trigger rebalance if the divide produces a gap < 1e-6 with either neighbor.
        if left_gap < REBAlANCE_GAP_THRESHOLD or right_gap < REBAlANCE_GAP_THRESHOLD:
            await self._repo.rebalance_active_positions(project_id=project_id)
            # Re-read 'after' and 'nxt' since positions have changed.
            after2 = await self._repo.get_by_id(position_after)
            if after2 is None or after2.project_id != project_id or after2.archived_at is not None:
                raise AppError(
                    error_code="INVALID_INPUT",
                    message="Invalid positionAfter reference",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            nxt2 = await self._repo.get_next_active_after(project_id=project_id, position_index=after2.position_index)
            if nxt2 is None:
                return after2.position_index + Decimal("1.0")
            return (after2.position_index + nxt2.position_index) / Decimal(2)

        return new_pos

    async def _maybe_rebalance_after_insert(self, *, project_id: UUID, inserted: CanvasBlock) -> None:
        left = await self._get_left_neighbor(project_id=project_id, pos=inserted.position_index)
        right = await self._repo.get_next_active_after(project_id=project_id, position_index=inserted.position_index)

        if left is not None and (inserted.position_index - left.position_index) < REBAlANCE_GAP_THRESHOLD:
            await self._repo.rebalance_active_positions(project_id=project_id)
            return
        if right is not None and (right.position_index - inserted.position_index) < REBAlANCE_GAP_THRESHOLD:
            await self._repo.rebalance_active_positions(project_id=project_id)
            return

        # Defensive: in practice, repeated inserts between the same neighbors can build up a long
        # run of fractional positions before the <1e-6 condition is observed (DB precision / rounding
        # varies across environments). Once a project has many active blocks, rebalance to keep
        # ordering stable and edit-friendly.
        active_count = await self._repo.count_active_for_project(project_id=project_id)
        if active_count >= 50:
            await self._repo.rebalance_active_positions(project_id=project_id)

    async def _get_left_neighbor(self, *, project_id: UUID, pos: Decimal) -> CanvasBlock | None:
        stmt = (
            select(CanvasBlock)
            .where(
                CanvasBlock.project_id == project_id,
                CanvasBlock.archived_at.is_(None),
                CanvasBlock.position_index < pos,
            )
            .order_by(CanvasBlock.position_index.desc(), CanvasBlock.id.desc())
            .limit(1)
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

