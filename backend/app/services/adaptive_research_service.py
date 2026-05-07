"""Orchestrates segmented adaptive analysis runs (PR #8b).

Retention caveat: when ``raw_text_retention`` is NOT_STORED or EPHEMERAL, completed runs
purge ``sources.extracted_text``. A later analysis on the same source would require
re-extraction (out of scope for v0.3 until re-run UX exists).
"""

from __future__ import annotations

import logging
import math
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.ai_provider_client import (
    AiProviderClient,
    MockAiProviderClient,
    SegmentAnalysisResult,
)
from app.core.enums import (
    AnalysisIntent,
    AnalysisMode,
    CompletionStrategy,
    ResearchMode,
    ResearchScope,
)
from app.models.analysis_run import AnalysisRun
from app.models.analysis_segment import AnalysisSegment
from app.models.generation_job import GenerationJob
from app.models.research_item import ResearchItem
from app.models.source import Source
from app.models.source_scan import SourceScan
from app.models.source_segment import SourceSegment
from app.services import ai_output_validation_service
from app.services.prompt_builder import (
    build_segment_prompt,
    filter_enrichments_by_intent,
)
from app.services.usage_tracking_service import record_segment_analysis_usage

logger = logging.getLogger(__name__)

OPTIMIZE_DEEP_RATIO = 0.4
OPTIMIZE_STANDARD_RATIO = 0.4
MID_RUN_BUDGET_BUFFER = Decimal("1.2")

# Relative token/allowance weight by depth (for mid-run budget + actual % split).
DEPTH_COST_WEIGHT: dict[ResearchMode, Decimal] = {
    ResearchMode.QUICK: Decimal("0.75"),
    ResearchMode.STANDARD: Decimal("1.0"),
    ResearchMode.DEEP: Decimal("1.35"),
}

INTENT_KEYWORDS: dict[AnalysisIntent, set[str]] = {
    AnalysisIntent.QUICK_SUMMARY: {"summary", "overview", "highlights"},
    AnalysisIntent.MARKET_IMPACT: {"price", "stock", "shares", "market", "guidance"},
    AnalysisIntent.COMPANY_ANALYSIS: {
        "earnings",
        "revenue",
        "guidance",
        "segment",
        "margin",
    },
    AnalysisIntent.LEARNING_MODE: {"explain", "definition", "how", "why"},
    AnalysisIntent.STRUCTURED_BRIEF: {
        "price",
        "stock",
        "shares",
        "market",
        "guidance",
        "earnings",
        "revenue",
        "segment",
        "margin",
    },
    AnalysisIntent.INSIDER_ACTIVITY: {
        "insider",
        "executive",
        "board",
        "compensation",
        "stake",
        "holder",
    },
}


def _relevance_to_float(raw: str | None) -> float:
    if raw is None:
        return 0.0
    try:
        return float(raw)
    except ValueError:
        pass
    u = str(raw).upper()
    if u == "HIGH":
        return 1.0
    if u == "MEDIUM":
        return 0.6
    if u == "LOW":
        return 0.3
    return 0.0


def _entity_match_selected(
    selected_ids: set[uuid.UUID], detected_entities: list[Any]
) -> bool:
    sel_str = {str(s) for s in selected_ids}
    for e in detected_entities or []:
        if isinstance(e, dict):
            for key in ("id", "ticker", "name"):
                v = e.get(key)
                if v is not None and str(v) in sel_str:
                    return True
        elif str(e) in sel_str:
            return True
    return False


def keyword_overlap(topics: list[Any], keywords: set[str]) -> float:
    if not topics:
        return 0.0
    hits = 0
    for t in topics:
        tl = str(t).lower()
        if any(k in tl for k in keywords):
            hits += 1
    return hits / len(topics)


def score_segment(
    seg: SourceSegment,
    intent: AnalysisIntent,
    selected_entity_ids: list[uuid.UUID],
) -> float:
    kw = INTENT_KEYWORDS.get(intent, set())
    entity_part = (
        1.0
        if _entity_match_selected(set(selected_entity_ids), seg.detected_entities or [])
        else 0.0
    )
    topic_part = keyword_overlap(seg.detected_topics or [], kw)
    rel = _relevance_to_float(seg.relevance_to_intent)
    return float(entity_part + 0.6 * topic_part + 0.4 * rel)


def assign_depths_optimize(
    segments: list[SourceSegment],
    requested: ResearchMode,
    intent: AnalysisIntent,
    selected_entity_ids: list[uuid.UUID],
) -> dict[uuid.UUID, ResearchMode]:
    if len(segments) < 5:
        return {s.id: requested for s in segments}

    ranked = sorted(
        segments,
        key=lambda s: score_segment(s, intent, selected_entity_ids),
        reverse=True,
    )
    n = len(ranked)
    deep_n = int(math.ceil(n * OPTIMIZE_DEEP_RATIO))
    std_n = int(math.ceil(n * (OPTIMIZE_DEEP_RATIO + OPTIMIZE_STANDARD_RATIO)))
    out: dict[uuid.UUID, ResearchMode] = {}
    for i, seg in enumerate(ranked):
        if i < deep_n:
            out[seg.id] = ResearchMode.DEEP
        elif i < std_n:
            out[seg.id] = ResearchMode.STANDARD
        else:
            out[seg.id] = ResearchMode.QUICK
    return out


def assign_depths(
    segments: list[SourceSegment],
    strategy: CompletionStrategy,
    requested: ResearchMode,
    intent: AnalysisIntent,
    selected_entity_ids: list[uuid.UUID],
) -> dict[uuid.UUID, ResearchMode]:
    if strategy == CompletionStrategy.STRICT_REQUESTED_MODE:
        return {s.id: requested for s in segments}
    return assign_depths_optimize(segments, requested, intent, selected_entity_ids)


def mode_rank(mode: ResearchMode) -> int:
    return {"QUICK": 0, "STANDARD": 1, "DEEP": 2}[mode.value]


def downgrade_mode(mode: ResearchMode) -> ResearchMode:
    return {
        ResearchMode.DEEP: ResearchMode.STANDARD,
        ResearchMode.STANDARD: ResearchMode.QUICK,
        ResearchMode.QUICK: ResearchMode.QUICK,
    }[mode]


def expected_segment_cost_at_depth(
    estimated_total: Decimal | None,
    n_segments: int,
    depth: ResearchMode,
) -> Decimal:
    if estimated_total is None or n_segments <= 0:
        return Decimal("0")
    base = estimated_total / Decimal(n_segments)
    return base * DEPTH_COST_WEIGHT[depth]


def _planned_weight_sum(
    segments: list[SourceSegment], depths: dict[uuid.UUID, ResearchMode]
) -> Decimal:
    total = Decimal("0")
    for s in segments:
        total += DEPTH_COST_WEIGHT[depths[s.id]]
    return total or Decimal("1")


async def execute_run_in_background(run_id: uuid.UUID) -> None:
    from app.db.session import async_session_factory

    async with async_session_factory() as db:
        try:
            await execute_run(run_id, db=db)
        except Exception:
            logger.exception("Run %s failed unhandled", run_id)
            async with async_session_factory() as db2:
                await _mark_run_failed(db2, run_id, "INTERNAL", "Unhandled worker error")


async def _mark_run_failed(
    db: AsyncSession,
    run_id: uuid.UUID,
    error_code: str,
    error_message: str,
) -> None:
    run = await db.get(AnalysisRun, run_id)
    if run is None:
        return
    now = datetime.now(UTC)
    run.status = "FAILED"
    run.error_code = error_code
    run.error_message = error_message
    run.completed_at = now

    if run.generation_job_id:
        job = await db.get(GenerationJob, run.generation_job_id)
        if job:
            job.status = "FAILED"
            job.error_code = error_code
            job.error_message = error_message
            job.completed_at = now

    item = await db.get(ResearchItem, run.research_item_id)
    if item:
        item.status = "FAILED"
        item.error_code = error_code
        item.error_message = error_message

    await db.commit()


def _default_ai_provider() -> AiProviderClient:
    return MockAiProviderClient()


async def execute_run(
    run_id: uuid.UUID,
    *,
    db: AsyncSession,
    ai_provider: AiProviderClient | None = None,
) -> None:
    try:
        await _execute_run_impl(run_id, db=db, ai_provider=ai_provider)
    except Exception:
        logger.exception("Run %s failed inside execute_run", run_id)
        await db.rollback()
        await _mark_run_failed(db, run_id, "INTERNAL", "Analysis run failed")


async def _execute_run_impl(
    run_id: uuid.UUID,
    *,
    db: AsyncSession,
    ai_provider: AiProviderClient | None = None,
) -> None:
    provider = ai_provider or _default_ai_provider()

    stmt = select(AnalysisRun).where(AnalysisRun.id == run_id).with_for_update()
    run = await db.scalar(stmt)
    if run is None:
        return
    if run.status != "QUEUED":
        return

    item = await db.get(ResearchItem, run.research_item_id)
    if item is None:
        return

    job = (
        await db.get(GenerationJob, run.generation_job_id)
        if run.generation_job_id
        else None
    )

    source = await db.get(Source, run.source_id) if run.source_id else None
    scan = None
    if run.source_scan_id:
        scan = await db.scalar(
            select(SourceScan)
            .where(SourceScan.id == run.source_scan_id)
            .options(selectinload(SourceScan.segments))
        )

    if source is None or scan is None:
        await db.rollback()
        await _mark_run_failed(db, run_id, "SOURCE_MISSING", "Source or scan missing")
        return

    now = datetime.now(UTC)
    run.status = "RUNNING"
    run.started_at = now
    if job:
        job.status = "RUNNING"
        job.started_at = now
    item.status = "RUNNING"
    await db.commit()

    raw_summary = item.analysis_depth_summary or {}
    opt_ctx = raw_summary.get("_optimizationContext") or {}
    selected_segment_ids = [uuid.UUID(x) for x in opt_ctx.get("selectedSegmentIds", [])]
    selected_entity_ids = [uuid.UUID(x) for x in opt_ctx.get("selectedEntityIds", [])]

    segments = list(scan.segments or [])
    if selected_segment_ids:
        sel = set(selected_segment_ids)
        segments = [s for s in segments if s.id in sel]
    segments.sort(key=lambda s: s.segment_index)

    if not segments:
        await _mark_run_failed(db, run_id, "NO_SEGMENTS", "No segments to analyze")
        return

    strategy = CompletionStrategy(run.completion_strategy)
    requested_mode = ResearchMode(run.requested_research_mode)
    intent = AnalysisIntent(run.analysis_intent)
    analysis_mode = AnalysisMode(item.analysis_mode)
    scope_raw = opt_ctx.get("researchScope", ResearchScope.RECOMMENDED_CONTEXT.value)
    try:
        scope = ResearchScope(scope_raw)
    except ValueError:
        scope = ResearchScope.RECOMMENDED_CONTEXT

    assigned_depths = assign_depths(
        segments,
        strategy,
        requested_mode,
        intent,
        selected_entity_ids,
    )
    downgrade_reason_map: dict[uuid.UUID, str | None] = {s.id: None for s in segments}

    enrichments = filter_enrichments_by_intent(
        list(scan.enrichment_docs or []),
        intent,
    )

    ordered = sorted(segments, key=lambda s: s.segment_index)
    weight_sum = _planned_weight_sum(ordered, assigned_depths)
    est = run.estimated_allowance_impact_percent

    actual_so_far = Decimal("0")
    depth_summary: list[dict[str, Any]] = []
    segment_outputs: list[dict[str, Any]] = []
    failed_count = 0

    for i, seg in enumerate(ordered):
        depth = assigned_depths[seg.id]
        row = AnalysisSegment(
            analysis_run_id=run.id,
            source_segment_id=seg.id,
            segment_index=seg.segment_index,
            title=seg.title,
            start_offset_seconds=seg.start_offset_seconds,
            end_offset_seconds=seg.end_offset_seconds,
            requested_research_mode=requested_mode.value,
            actual_research_mode=depth.value,
            status="RUNNING",
            downgrade_reason=downgrade_reason_map.get(seg.id),
        )
        db.add(row)
        await db.flush()

        prompt = build_segment_prompt(
            segment=seg,
            analysis_intent=intent,
            depth=depth,
            focus_question=run.focus_question,
            source=source,
            enrichment_docs=enrichments,
            research_scope=scope,
            analysis_mode=analysis_mode,
        )

        async def _call_llm(
            p: str, d: ResearchMode = depth
        ) -> SegmentAnalysisResult:
            return await provider.generate_segment_analysis(p, depth=d)

        result = await _call_llm(prompt)
        ok, errors = ai_output_validation_service.validate_segment_output(
            result, analysis_mode=analysis_mode
        )
        if not ok:
            repair = ai_output_validation_service.repair_suffix(errors)
            result = await _call_llm(prompt + repair)
            ok, errors = ai_output_validation_service.validate_segment_output(
                result, analysis_mode=analysis_mode
            )
        if not ok:
            row.status = "FAILED"
            row.analysis_markdown = None
            row.analysis_json = {"validationErrors": errors}
            row.key_entities = []
            row.key_topics = []
            row.can_rerun = True
            failed_count += 1
            await db.commit()
            depth_summary.append(
                {
                    "segmentIndex": seg.segment_index,
                    "title": seg.title,
                    "requestedMode": requested_mode.value,
                    "actualMode": depth.value,
                    "downgradeReason": downgrade_reason_map.get(seg.id),
                }
            )
        else:
            md = ai_output_validation_service.sanitize_analysis_markdown(
                result.analysis_markdown or ""
            )
            row.status = "COMPLETED"
            row.analysis_markdown = md
            row.analysis_json = result.analysis_json
            row.key_entities = list(result.key_entities or [])
            row.key_topics = list(result.key_topics or [])
            row.can_rerun = mode_rank(depth) < mode_rank(requested_mode)

            impact = Decimal("0")
            if est is not None and weight_sum > 0:
                impact = est * DEPTH_COST_WEIGHT[depth] / weight_sum
            actual_so_far += impact

            await record_segment_analysis_usage(
                db,
                user_id=run.user_id,
                research_item_id=run.research_item_id,
                source_id=run.source_id,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                allowance_percent=impact,
            )

            await db.commit()

            depth_summary.append(
                {
                    "segmentIndex": seg.segment_index,
                    "title": seg.title,
                    "requestedMode": requested_mode.value,
                    "actualMode": depth.value,
                    "downgradeReason": downgrade_reason_map.get(seg.id),
                }
            )

            segment_outputs.append(
                {
                    "segmentIndex": seg.segment_index,
                    "title": seg.title,
                    "analysisMarkdown": md,
                    "analysisJson": result.analysis_json,
                    "status": "COMPLETED",
                }
            )

        if (
            strategy == CompletionStrategy.OPTIMIZE_RESEARCH
            and i + 1 < len(ordered)
            and est is not None
        ):
            next_seg = ordered[i + 1]
            remaining_budget = est * MID_RUN_BUDGET_BUFFER - actual_so_far
            next_depth = assigned_depths[next_seg.id]
            expected_next = expected_segment_cost_at_depth(
                est, len(ordered), next_depth
            )
            if remaining_budget < expected_next:
                for j in range(i + 1, len(ordered)):
                    sid = ordered[j].id
                    new_d = downgrade_mode(assigned_depths[sid])
                    assigned_depths[sid] = new_d
                    downgrade_reason_map[sid] = "ALLOWANCE_LIMIT"

    md_parts = [
        s["analysisMarkdown"]
        for s in segment_outputs
        if s.get("analysisMarkdown")
    ]
    output_md = "\n\n---\n\n".join(md_parts)

    run_reload = await db.get(AnalysisRun, run.id)
    item_reload = await db.get(ResearchItem, item.id)
    source_reload = await db.get(Source, source.id)
    job_reload = (
        await db.get(GenerationJob, run.generation_job_id)
        if run.generation_job_id
        else None
    )

    if run_reload and item_reload:
        done = datetime.now(UTC)
        run_reload.status = "COMPLETED"
        run_reload.completed_at = done
        run_reload.actual_allowance_impact_percent = actual_so_far

        if job_reload:
            job_reload.status = "COMPLETED"
            job_reload.completed_at = done

        item_reload.status = "COMPLETED"
        item_reload.generated_at = done
        item_reload.output_markdown = output_md
        item_reload.output_json = {
            "segments": segment_outputs,
            "summary": {
                "segmentCount": len(ordered),
                "failedSegments": failed_count,
            },
        }
        item_reload.analysis_depth_summary = depth_summary
        item_reload.short_summary = (
            output_md[:400] + "…" if len(output_md) > 400 else output_md
        )

        if source_reload and source_reload.raw_text_retention in (
            "NOT_STORED",
            "EPHEMERAL",
        ):
            source_reload.extracted_text = None
            source_reload.extracted_text_word_count = 0

        await db.commit()