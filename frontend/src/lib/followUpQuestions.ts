import { clampAssistantMarkdownForDisplay } from "@/lib/chatLimits";
import type { ChatTurn } from "@/types/workspace";

/** Must match backend `reply_tail_sections._ALLOWED_CANVAS_TYPES`. */
export const ALLOWED_REPLY_TAIL_CANVAS_TYPES = new Set<string>([
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
]);

export function normalizeReplyTailCanvasElementType(
  raw: string,
): string | null {
  const et = raw.trim().toUpperCase().replace(/\s+/g, "_");
  return ALLOWED_REPLY_TAIL_CANVAS_TYPES.has(et) ? et : null;
}

const HEADER_ENTITIES = /^#{1,6}\s*Key entities\s*$/i;
const HEADER_CANVAS = /^#{1,6}\s*Canvas insight cards\s*$/i;
const HEADER_FOLLOW = /^#{1,6}\s*Follow[- ]up questions?\s*$/i;
const BULLET_LINE = /^\s*(?:[-*]|\d+\.)\s+(.+)$/;
const HR_ONLY_LINE = /^---\s*$/;

/** Same delimiter semantics as backend `reply_tail_sections` (`^---\\s*$` per line). */
function splitMarkdownOnHrLines(markdown: string): string[] {
  const lines = markdown.split(/\r?\n/);
  const parts: string[] = [];
  let cur: string[] = [];
  for (const line of lines) {
    if (HR_ONLY_LINE.test(line)) {
      parts.push(cur.join("\n"));
      cur = [];
    } else {
      cur.push(line);
    }
  }
  parts.push(cur.join("\n"));
  return parts;
}

export type SuggestedCanvasInsight = {
  elementType: string;
  title: string;
  contentMarkdown: string;
};

export type ParsedAssistantReply = {
  body: string;
  mentionedEntities: string[];
  suggestedCanvasInsights: SuggestedCanvasInsight[];
  followUpQuestions: string[];
};

function readStringArray(raw: unknown): string[] {
  if (!Array.isArray(raw)) return [];
  return raw
    .filter((x): x is string => typeof x === "string" && x.trim().length > 0)
    .map((s) => s.trim());
}

function readCanvasInsights(raw: unknown): SuggestedCanvasInsight[] {
  if (!Array.isArray(raw)) return [];
  const out: SuggestedCanvasInsight[] = [];
  for (const item of raw) {
    if (!item || typeof item !== "object") continue;
    const o = item as Record<string, unknown>;
    const etRaw = String(o.elementType ?? o.element_type ?? "").trim();
    const elementType = normalizeReplyTailCanvasElementType(etRaw);
    const title = String(o.title ?? "").trim();
    const contentMarkdown = String(
      o.contentMarkdown ?? o.content_markdown ?? "",
    ).trim();
    if (!elementType || !contentMarkdown) continue;
    out.push({ elementType, title, contentMarkdown });
  }
  return out.slice(0, 8);
}

/** Backend stores parsed follow-ups under camelCase in contentJson. */
export function readFollowUpQuestionsFromTurn(
  turn: ChatTurn | null | undefined,
): string[] {
  const cj = turn?.contentJson as Record<string, unknown> | null | undefined;
  return readStringArray(cj?.followUpQuestions);
}

/** Mirrors backend `parse_reply_tail_sections` for legacy turns without contentJson. */
export function parseReplyTailMarkdown(markdown: string): ParsedAssistantReply {
  const segments = splitMarkdownOnHrLines(markdown);
  if (segments.length < 2) {
    const single = (segments[0] ?? "").trim();
    return {
      body: single,
      mentionedEntities: [],
      suggestedCanvasInsights: [],
      followUpQuestions: [],
    };
  }

  const mainChunks: string[] = [];
  const first = (segments[0] ?? "").trim();
  if (first) mainChunks.push(first);

  const mentionedEntities: string[] = [];
  const suggestedCanvasInsights: SuggestedCanvasInsight[] = [];
  const followUpQuestions: string[] = [];

  for (let i = 1; i < segments.length; i++) {
    const rawSeg = segments[i] ?? "";
    const lines = rawSeg.split(/\r?\n/).filter((l) => l.trim() !== "");
    if (!lines.length) continue;
    const hdr = lines[0].trim();
    const body = lines.slice(1);
    if (HEADER_ENTITIES.test(hdr)) {
      const remainderLines: string[] = [];
      for (const ln of body) {
        const m = ln.match(BULLET_LINE);
        if (m?.[1]) {
          const s = m[1].trim();
          if (s) mentionedEntities.push(s);
        } else {
          remainderLines.push(ln);
        }
      }
      const joined = remainderLines.join("\n").trim();
      if (joined) mainChunks.push(joined);
    } else if (HEADER_CANVAS.test(hdr)) {
      const remainderLines: string[] = [];
      for (const ln of body) {
        const m = ln.match(BULLET_LINE);
        if (!m?.[1]) {
          remainderLines.push(ln);
          continue;
        }
        const payload = m[1].trim();
        let parsed = false;
        if (payload.startsWith("{") && payload.endsWith("}")) {
          try {
            const d = JSON.parse(payload) as Record<string, unknown>;
            const etRaw = String(
              d.elementType ?? d.element_type ?? "",
            ).trim();
            const elementType = normalizeReplyTailCanvasElementType(etRaw);
            const title = String(d.title ?? "").trim();
            const contentMarkdown = String(
              d.contentMarkdown ?? d.content_markdown ?? "",
            ).trim();
            if (elementType && contentMarkdown) {
              suggestedCanvasInsights.push({
                elementType,
                title,
                contentMarkdown,
              });
              parsed = true;
            }
          } catch {
            /* skip */
          }
        } else {
          const parts = payload.split("::").map((p) => p.trim());
          if (parts.length >= 3) {
            const elementType = normalizeReplyTailCanvasElementType(parts[0]);
            const title = parts[1];
            const contentMarkdown = parts.slice(2).join("::").trim();
            if (elementType && contentMarkdown) {
              suggestedCanvasInsights.push({
                elementType,
                title,
                contentMarkdown,
              });
              parsed = true;
            }
          }
        }
        if (!parsed) remainderLines.push(ln);
      }
      const joined = remainderLines.join("\n").trim();
      if (joined) mainChunks.push(joined);
    } else if (HEADER_FOLLOW.test(hdr)) {
      const remainderLines: string[] = [];
      for (const ln of body) {
        const m = ln.match(BULLET_LINE);
        if (m?.[1]) {
          const s = m[1].trim();
          if (s) followUpQuestions.push(s);
        } else {
          remainderLines.push(ln);
        }
      }
      const joined = remainderLines.join("\n").trim();
      if (joined) mainChunks.push(joined);
    } else {
      const remainder = rawSeg.trim();
      if (remainder) mainChunks.push(remainder);
    }
  }

  const body = mainChunks.join("\n\n").trim();

  return {
    body,
    mentionedEntities: mentionedEntities.slice(0, 24),
    suggestedCanvasInsights: suggestedCanvasInsights.slice(0, 6),
    followUpQuestions: followUpQuestions.slice(0, 8),
  };
}

/** Prefer server-parsed contentJson; otherwise parse trailing markdown sections. */
export function parseAssistantReplyForDisplay(
  turn: ChatTurn,
  markdown: string,
): ParsedAssistantReply {
  const cj = turn.contentJson as Record<string, unknown> | null | undefined;
  const mentionedEntities = readStringArray(cj?.mentionedEntities);
  const suggestedCanvasInsights = readCanvasInsights(cj?.suggestedCanvasInsights);
  const followUpQuestions = readFollowUpQuestionsFromTurn(turn);
  if (
    mentionedEntities.length > 0 ||
    suggestedCanvasInsights.length > 0 ||
    followUpQuestions.length > 0
  ) {
    return {
      body: clampAssistantMarkdownForDisplay(markdown),
      mentionedEntities,
      suggestedCanvasInsights,
      followUpQuestions,
    };
  }
  const parsed = parseReplyTailMarkdown(markdown);
  return {
    ...parsed,
    body: clampAssistantMarkdownForDisplay(parsed.body),
  };
}

/** @deprecated use parseAssistantReplyForDisplay */
export function bodyAndFollowUpsForAssistantTurn(
  turn: ChatTurn,
  markdown: string,
): { body: string; followUps: string[] } {
  const p = parseAssistantReplyForDisplay(turn, markdown);
  return { body: p.body, followUps: p.followUpQuestions };
}

export function splitFollowUpMarkdown(markdown: string): {
  main: string;
  questions: string[];
} {
  const p = parseReplyTailMarkdown(markdown);
  return { main: p.body, questions: p.followUpQuestions };
}
