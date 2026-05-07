"""Orchestrates the cheap pre-scan flow for a Source (AI_PIPELINE §17.1).

Responsibilities:
  1. Validate the source has scannable content.
  2. Segment the source (article paragraphs / YouTube windows / metadata stub).
  3. Run dumb entity + topic detection on the full text.
  4. Score complexity and estimate per-run impact.
  5. Persist a `source_scans` row + N `source_segments` rows.
  6. Update sources.scan_status / source_complexity / segment_count.

We do NOT generate the final answer here. That's the next PR.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.source import Source
from app.models.source_scan import SourceScan
from app.models.source_segment import SourceSegment
from app.repositories.source_repository import SourceRepository
from app.repositories.source_scan_repository import SourceScanRepository
from app.repositories.source_segment_repository import SourceSegmentRepository
from app.schemas.source_scan import (
    DetectedEntity as DetectedEntitySchema,
    RunSourceScanRequest,
    RunSourceScanResponse,
    SourceSegmentSummary,
)
from app.services.entity_detection_service import (
    DetectedEntity as DetectedEntityRecord,
    detect_entities,
    detect_topics,
)
from app.services.source_complexity_service import (
    SegmentEstimate,
    estimate_impact_percent,
    estimate_segment_tokens,
    recommend_completion_strategy,
    recommend_research_mode,
    score_complexity,
    warning_level_for,
)
from app.services.source_segmentation_service import (
    SegmentDraft,
    captions_from_text_estimate,
    segment_article,
    segment_metadata_only,
    segment_youtube_transcript,
)

if TYPE_CHECKING:
    from app.models.user import User

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _SegmentationResult:
    drafts: list[SegmentDraft]
    estimate_confidence_floor: str | None  # "LOW" forces low confidence for METADATA_ONLY


async def run_source_scan(
    *,
    db: AsyncSession,
    current_user: "User",
    source_id,
    request: RunSourceScanRequest,
) -> RunSourceScanResponse:
    """Run the cheap pre-scan and return the API response."""

    src_repo = SourceRepository(db)
    source = await src_repo.get_by_id(source_id)
    if source is None:
        raise AppError(
            error_code="NOT_FOUND",
            message="Source not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    if source.user_id != current_user.id:
        raise AppError(
            error_code="FORBIDDEN",
            message="You do not have access to this source",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    seg_result = _segment_source(source)
    if not seg_result.drafts:
        raise AppError(
            error_code="SOURCE_NOT_SCANNABLE",
            message=(
                "Source has no extracted text and is not METADATA_ONLY; "
                "cannot run scan."
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    full_text = source.extracted_text or _stitch_drafts(seg_result.drafts)
    entities = detect_entities(full_text)
    topics = detect_topics(full_text)

    word_count = source.extracted_text_word_count or sum(
        d.word_count for d in seg_result.drafts
    )

    complexity = score_complexity(
        word_count=word_count,
        entity_count=len(entities),
        topic_count=len(topics),
    )

    settings = get_settings()
    seg_estimates = [
        SegmentEstimate(
            estimated_tokens=estimate_segment_tokens(d.word_count),
            has_text=d.has_text,
        )
        for d in seg_result.drafts
    ]
    impact_pct, confidence = estimate_impact_percent(
        seg_estimates,
        request.research_mode,
        single_run_token_budget=settings.single_run_token_budget,
    )
    if seg_result.estimate_confidence_floor == "LOW":
        confidence = "LOW"

    warning_level, requires_warning = warning_level_for(impact_pct)
    rec_mode = recommend_research_mode(complexity, request.research_mode, warning_level)
    if seg_result.estimate_confidence_floor == "LOW":
        rec_mode = "QUICK"
    rec_strategy = recommend_completion_strategy(warning_level, complexity)

    scan, segments = await _persist_scan(
        db=db,
        user_id=current_user.id,
        source=source,
        request=request,
        complexity=complexity,
        confidence=confidence,
        impact_pct=impact_pct,
        warning_level=warning_level,
        requires_warning=requires_warning,
        rec_mode=rec_mode,
        rec_strategy=rec_strategy,
        topics=topics,
        entities=entities,
        drafts=seg_result.drafts,
    )

    return _to_response(
        scan=scan,
        segments=segments,
        topics=topics,
        entities=entities,
    )


def _segment_source(source: Source) -> _SegmentationResult:
    """Return drafts + a confidence floor (LOW for metadata-only)."""

    if source.source_access_status == "METADATA_ONLY":
        drafts = segment_metadata_only(
            title=source.title,
            text_hint=(source.metadata_ or {}).get("description"),
        )
        return _SegmentationResult(drafts=drafts, estimate_confidence_floor="LOW")

    if not source.extracted_text or not source.extracted_text.strip():
        return _SegmentationResult(drafts=[], estimate_confidence_floor=None)

    if source.source_type == "YOUTUBE_URL":
        # Without stored caption timing we approximate from joined transcript
        # text (≈ 150 wpm) - the actual heuristic lives in the segmentation
        # service; the LLM-quality timed re-fetch is a future PR.
        captions = captions_from_text_estimate(source.extracted_text)
        drafts = segment_youtube_transcript(captions)
        return _SegmentationResult(drafts=drafts, estimate_confidence_floor=None)

    # ARTICLE_URL or any other text-bearing source.
    drafts = segment_article(source.extracted_text)
    return _SegmentationResult(drafts=drafts, estimate_confidence_floor=None)


async def _persist_scan(
    *,
    db: AsyncSession,
    user_id,
    source: Source,
    request: RunSourceScanRequest,
    complexity: str,
    confidence: str,
    impact_pct: float,
    warning_level: str,
    requires_warning: bool,
    rec_mode: str,
    rec_strategy: str,
    topics: list[str],
    entities: list[DetectedEntityRecord],
    drafts: list[SegmentDraft],
) -> tuple[SourceScan, list[SourceSegment]]:
    scan = SourceScan(
        user_id=user_id,
        source_id=source.id,
        requested_output_mode=request.requested_output_mode,
        analysis_intent=request.analysis_intent,
        requested_research_mode=request.research_mode,
        coverage_mode=request.coverage_mode,
        focus_question=request.focus_question,
        source_complexity=complexity,
        estimate_confidence=confidence,
        estimated_allowance_impact_percent=Decimal(f"{impact_pct:.2f}"),
        requires_warning=requires_warning,
        warning_level=warning_level,
        recommended_research_mode=rec_mode,
        recommended_completion_strategy=rec_strategy,
        detected_topics=list(topics),
        detected_entities=[e.to_dict() for e in entities],
    )
    scan_repo = SourceScanRepository(db)
    await scan_repo.add(scan)

    seg_repo = SourceSegmentRepository(db)
    segments: list[SourceSegment] = []
    for d in drafts:
        seg = SourceSegment(
            source_id=source.id,
            source_scan_id=scan.id,
            segment_index=d.segment_index,
            start_offset_seconds=d.start_offset_seconds,
            end_offset_seconds=d.end_offset_seconds,
            start_char_offset=d.start_char_offset,
            end_char_offset=d.end_char_offset,
            title=d.title,
            topic_summary=None,
            detected_entities=[],
            detected_topics=[],
            estimated_complexity=None,
            relevance_to_intent=None,
            recommended_research_mode=None,
            metadata_=dict(d.metadata),
        )
        segments.append(seg)
    await seg_repo.add_all(segments)

    source.scan_status = "COMPLETED"
    source.source_complexity = complexity
    source.segment_count = len(drafts)
    await db.commit()
    await db.refresh(scan)
    for seg in segments:
        await db.refresh(seg)
    await db.refresh(source)
    return scan, segments


def _stitch_drafts(drafts: list[SegmentDraft]) -> str:
    return "\n\n".join(d.text for d in drafts if d.text)


def _to_response(
    *,
    scan: SourceScan,
    segments: list[SourceSegment],
    topics: list[str],
    entities: list[DetectedEntityRecord],
) -> RunSourceScanResponse:
    return RunSourceScanResponse(
        sourceId=scan.source_id,
        scanId=scan.id,
        sourceComplexity=scan.source_complexity,  # type: ignore[arg-type]
        estimateConfidence=scan.estimate_confidence,  # type: ignore[arg-type]
        estimatedAllowanceImpactPercent=float(scan.estimated_allowance_impact_percent),
        requiresWarning=scan.requires_warning,
        warningLevel=scan.warning_level,  # type: ignore[arg-type]
        recommendedResearchMode=scan.recommended_research_mode,  # type: ignore[arg-type]
        recommendedCompletionStrategy=scan.recommended_completion_strategy,  # type: ignore[arg-type]
        detectedTopics=list(topics),
        detectedEntities=[
            DetectedEntitySchema(name=e.name, ticker=e.ticker, type=e.type)
            for e in entities
        ],
        segments=[
            SourceSegmentSummary(
                segmentId=s.id,
                segmentIndex=s.segment_index,
                startOffsetSeconds=s.start_offset_seconds,
                endOffsetSeconds=s.end_offset_seconds,
                startCharOffset=s.start_char_offset,
                endCharOffset=s.end_char_offset,
                title=s.title,
                topicSummary=s.topic_summary,
                estimatedComplexity=s.estimated_complexity,  # type: ignore[arg-type]
                recommendedDepth=s.recommended_research_mode,  # type: ignore[arg-type]
            )
            for s in segments
        ],
    )
