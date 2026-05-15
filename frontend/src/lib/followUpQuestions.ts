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

/**
 * Maps model-only labels (e.g. THEME) to a valid canvas element type for UI + POST /elements.
 */
export function coerceCanvasInsightElementType(raw: string): string {
  const et = raw.trim().toUpperCase().replace(/\s+/g, "_");
  if (ALLOWED_REPLY_TAIL_CANVAS_TYPES.has(et)) return et;
  if (et === "THEME") return "AI_BLOCK";
  return "AI_BLOCK";
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

function parseInsightRecord(
  o: Record<string, unknown>,
): SuggestedCanvasInsight | null {
  const etRaw = String(o.elementType ?? o.element_type ?? "").trim();
  const title = String(o.title ?? "").trim();
  const contentMarkdown = String(
    o.contentMarkdown ?? o.content_markdown ?? "",
  ).trim();
  if (!contentMarkdown) return null;
  const elementType = coerceCanvasInsightElementType(etRaw);
  return { elementType, title, contentMarkdown };
}

function readCanvasInsights(raw: unknown): SuggestedCanvasInsight[] {
  if (!Array.isArray(raw)) return [];
  const out: SuggestedCanvasInsight[] = [];
  for (const item of raw) {
    if (typeof item === "string") {
      const s = item.trim();
      if (!s.startsWith("{")) continue;
      try {
        const parsed = JSON.parse(s) as unknown;
        if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
          const one = parseInsightRecord(parsed as Record<string, unknown>);
          if (one) out.push(one);
        }
      } catch {
        /* skip */
      }
      continue;
    }
    if (!item || typeof item !== "object") continue;
    const one = parseInsightRecord(item as Record<string, unknown>);
    if (one) out.push(one);
  }
  return out.slice(0, 8);
}

/** Removes standalone JSON lines the model emitted as canvas rows (not fenced code). */
function stripStandaloneCanvasInsightJsonLines(markdown: string): string {
  return markdown
    .split("\n")
    .filter((line) => {
      const t = line.trim();
      if (!t.startsWith("{") || !t.endsWith("}")) return true;
      if (!/"elementType"\s*:/.test(t) && !/"element_type"\s*:/.test(t))
        return true;
      try {
        const d = JSON.parse(t) as Record<string, unknown>;
        const md = String(
          d.contentMarkdown ?? d.content_markdown ?? "",
        ).trim();
        return !md;
      } catch {
        return true;
      }
    })
    .join("\n");
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
      body: stripStandaloneCanvasInsightJsonLines(single),
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
            const contentMarkdown = String(
              d.contentMarkdown ?? d.content_markdown ?? "",
            ).trim();
            const title = String(d.title ?? "").trim();
            if (etRaw && contentMarkdown) {
              suggestedCanvasInsights.push({
                elementType: coerceCanvasInsightElementType(etRaw),
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
            const title = parts[1];
            const contentMarkdown = parts.slice(2).join("::").trim();
            if (parts[0] && contentMarkdown) {
              suggestedCanvasInsights.push({
                elementType: coerceCanvasInsightElementType(parts[0]),
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

  let body = mainChunks.join("\n\n").trim();
  if (suggestedCanvasInsights.length > 0) {
    body = stripStandaloneCanvasInsightJsonLines(body);
  }

  return {
    body,
    mentionedEntities: mentionedEntities.slice(0, 24),
    suggestedCanvasInsights: suggestedCanvasInsights.slice(0, 6),
    followUpQuestions: followUpQuestions.slice(0, 8),
  };
}

function harvestInlineCanvasJsonRows(markdown: string): {
  body: string;
  extra: SuggestedCanvasInsight[];
} {
  const lines = markdown.split("\n");
  const kept: string[] = [];
  const extra: SuggestedCanvasInsight[] = [];
  for (const line of lines) {
    const t = line.trim();
    if (
      t.startsWith("{") &&
      t.endsWith("}") &&
      (/"elementType"\s*:/.test(t) || /"element_type"\s*:/.test(t))
    ) {
      try {
        const d = JSON.parse(t) as Record<string, unknown>;
        const one = parseInsightRecord(d);
        if (one) {
          extra.push(one);
          continue;
        }
      } catch {
        /* keep line */
      }
    }
    kept.push(line);
  }
  return { body: kept.join("\n").trim(), extra };
}

/** Pulls pretty-printed `{ ... }` canvas rows embedded in prose. */
function harvestBalancedJsonCanvasObjects(markdown: string): {
  body: string;
  extra: SuggestedCanvasInsight[];
} {
  const extra: SuggestedCanvasInsight[] = [];
  const out: string[] = [];
  let i = 0;
  while (i < markdown.length) {
    const ch = markdown[i];
    if (ch !== "{") {
      out.push(ch);
      i++;
      continue;
    }
    const head = markdown.slice(i, Math.min(markdown.length, i + 500));
    if (!/"elementType"\s*:|"element_type"\s*:/.test(head)) {
      out.push(ch);
      i++;
      continue;
    }
    let depth = 0;
    let k = i;
    let inStr = false;
    let esc = false;
    for (; k < markdown.length; k++) {
      const c = markdown[k];
      if (esc) {
        esc = false;
        continue;
      }
      if (c === "\\" && inStr) {
        esc = true;
        continue;
      }
      if (c === '"' && !esc) {
        inStr = !inStr;
        continue;
      }
      if (!inStr) {
        if (c === "{") depth++;
        else if (c === "}") {
          depth--;
          if (depth === 0) {
            k++;
            break;
          }
        }
      }
    }
    if (depth !== 0 || k <= i) {
      out.push(ch);
      i++;
      continue;
    }
    const blob = markdown.slice(i, k);
    try {
      const d = JSON.parse(blob) as Record<string, unknown>;
      const one = parseInsightRecord(d);
      if (one) {
        extra.push(one);
        i = k;
        while (markdown[i] === "\n" || markdown[i] === "\r") i++;
        continue;
      }
    } catch {
      /* fallthrough */
    }
    out.push(ch);
    i++;
  }
  return {
    body: out.join("").replace(/\n{3,}/g, "\n\n").trim(),
    extra,
  };
}

function mergeCanvasInsights(
  body: string,
  existing: SuggestedCanvasInsight[],
): { body: string; insights: SuggestedCanvasInsight[] } {
  let b = body;
  let list = [...existing];
  const h1 = harvestInlineCanvasJsonRows(b);
  b = h1.body;
  list.push(...h1.extra);
  const h2 = harvestBalancedJsonCanvasObjects(b);
  b = h2.body;
  list.push(...h2.extra);
  if (list.length > 0) {
    b = stripStandaloneCanvasInsightJsonLines(b);
  }
  return { body: b.trim(), insights: list.slice(0, 8) };
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
  let result: ParsedAssistantReply;
  if (
    mentionedEntities.length > 0 ||
    suggestedCanvasInsights.length > 0 ||
    followUpQuestions.length > 0
  ) {
    let body = clampAssistantMarkdownForDisplay(markdown);
    if (suggestedCanvasInsights.length > 0) {
      body = stripStandaloneCanvasInsightJsonLines(body);
    }
    result = {
      body,
      mentionedEntities,
      suggestedCanvasInsights,
      followUpQuestions,
    };
  } else {
    const parsed = parseReplyTailMarkdown(markdown);
    result = {
      ...parsed,
      body: clampAssistantMarkdownForDisplay(parsed.body),
    };
  }

  const merged = mergeCanvasInsights(
    result.body,
    result.suggestedCanvasInsights,
  );
  return {
    ...result,
    body: merged.body,
    suggestedCanvasInsights: merged.insights,
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
