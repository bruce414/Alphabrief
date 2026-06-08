from __future__ import annotations

import json
import re
from typing import Any

_BULLET_RE = re.compile(r"^\s*(?:[-*]|\d+\.)\s+(.+)$")
_HEADER_ENTITIES = re.compile(r"^#{1,6}\s*Key entities\s*$", re.IGNORECASE)
_HEADER_CANVAS = re.compile(r"^#{1,6}\s*Canvas insight cards\s*$", re.IGNORECASE)
_HEADER_FOLLOW = re.compile(r"^#{1,6}\s*Follow[- ]up questions?\s*$", re.IGNORECASE)

_ALLOWED_CANVAS_TYPES = frozenset(
    {
        "TEXT",
        "AI_BLOCK",
        "CLAIM",
        "EVIDENCE",
        "QUOTE",
        "DATA",
        "QUESTION",
        "RISK",
        "CATALYST",
        "MINDMAP_NODE",
        "GROUP",
        "STICKY_NOTE",
    }
)


def _parse_canvas_line(line: str) -> dict[str, str] | None:
    m = _BULLET_RE.match(line)
    if not m:
        return None
    payload = (m.group(1) or "").strip()
    if payload.startswith("{") and payload.endswith("}"):
        try:
            d = json.loads(payload)
        except json.JSONDecodeError:
            return None
        if not isinstance(d, dict):
            return None
        et_raw = str(d.get("elementType") or d.get("element_type") or "").strip().upper()
        title = str(d.get("title") or "").strip()
        md = str(d.get("contentMarkdown") or d.get("content_markdown") or "").strip()
        if not et_raw or not md or et_raw not in _ALLOWED_CANVAS_TYPES:
            return None
        return {"elementType": et_raw, "title": title, "contentMarkdown": md}

    parts = [p.strip() for p in payload.split("::")]
    if len(parts) >= 3:
        et_raw = parts[0].upper().replace(" ", "_")
        title = parts[1]
        body = "::".join(parts[2:]).strip()
        if et_raw in _ALLOWED_CANVAS_TYPES and body:
            return {"elementType": et_raw, "title": title, "contentMarkdown": body}
    return None


def parse_reply_tail_sections(
    content_markdown: str,
) -> tuple[str, list[str], list[dict[str, str]], list[str]]:
    """
    Split optional trailing sections (each introduced by a line ---) after the main answer.

    Recognized section headers (first line of each segment):
    - ### Key entities
    - ### Canvas insight cards
    - ### Follow-up questions

    Segments that do not start with one of these headers are appended back to the main body.
    That way a standalone ``---`` used as a Markdown horizontal rule (or an extra divider)
    does not delete the rest of the answer.
    """
    parts = re.split(r"(?m)^---\s*$", content_markdown)
    if len(parts) < 2:
        return content_markdown.strip(), [], [], []

    main_chunks: list[str] = []
    first = parts[0].strip()
    if first:
        main_chunks.append(first)

    entities: list[str] = []
    canvas: list[dict[str, str]] = []
    followups: list[str] = []

    for raw_seg in parts[1:]:
        seg_lines = [ln for ln in raw_seg.splitlines() if ln.strip() != ""]
        if not seg_lines:
            continue
        hdr = seg_lines[0].strip()
        body = seg_lines[1:]
        if _HEADER_ENTITIES.match(hdr):
            prose_rest: list[str] = []
            for ln in body:
                m = _BULLET_RE.match(ln)
                if m:
                    s = (m.group(1) or "").strip()
                    if s:
                        entities.append(s)
                else:
                    prose_rest.append(ln)
            joined = "\n".join(prose_rest).strip()
            if joined:
                main_chunks.append(joined)
        elif _HEADER_CANVAS.match(hdr):
            prose_rest = []
            for ln in body:
                row = _parse_canvas_line(ln)
                if row is not None:
                    canvas.append(row)
                else:
                    prose_rest.append(ln)
            joined = "\n".join(prose_rest).strip()
            if joined:
                main_chunks.append(joined)
        elif _HEADER_FOLLOW.match(hdr):
            prose_rest = []
            for ln in body:
                m = _BULLET_RE.match(ln)
                if m:
                    s = (m.group(1) or "").strip()
                    if s:
                        followups.append(s)
                else:
                    prose_rest.append(ln)
            joined = "\n".join(prose_rest).strip()
            if joined:
                main_chunks.append(joined)
        else:
            remainder = raw_seg.strip()
            if remainder:
                main_chunks.append(remainder)

    main = "\n\n".join(main_chunks).strip()

    return (
        main,
        entities[:24],
        canvas[:6],
        followups[:8],
    )


def split_follow_up_questions(content_markdown: str) -> tuple[str, list[str]]:
    """Backward-compatible: main body + follow-up questions only."""
    main, _e, _c, fq = parse_reply_tail_sections(content_markdown)
    return main, fq
