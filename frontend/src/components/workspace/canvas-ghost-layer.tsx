import { useState } from "react";
import { useSWRConfig } from "swr";

import { usePendingCanvasCandidates } from "@/hooks/usePendingCanvasCandidates";
import { dismissCandidate, promoteCandidate } from "@/lib/workspaceApi";
import { T } from "@/styles/tokens";
import type { CandidateElement } from "@/types/workspace";

const GHOST_WIDTH = 280;
const GHOST_CARD_STEP = 168;

function isFiniteNumber(x: unknown): x is number {
  return typeof x === "number" && Number.isFinite(x);
}

function extractSuggestedPosition(c: CandidateElement): {
  width: number | null;
  height: number | null;
} {
  const raw = (c.contentJson as { suggested_position?: unknown } | null | undefined)
    ?.suggested_position;
  if (!raw || typeof raw !== "object") {
    return { width: GHOST_WIDTH, height: 140 };
  }
  const r = raw as Record<string, unknown>;
  return {
    width: isFiniteNumber(r.width) ? r.width : GHOST_WIDTH,
    height: isFiniteNumber(r.height) ? r.height : 140,
  };
}

function ghostStackPosition(
  index: number,
  pan: { x: number; y: number },
  zoom: number,
  viewport: { w: number; h: number },
) {
  const x = (viewport.w - pan.x) / zoom - GHOST_WIDTH - 24;
  const y = (48 - pan.y) / zoom + index * GHOST_CARD_STEP;
  return { x, y };
}

function KindBadge({ kind }: { kind: string }) {
  const type = kind.toUpperCase();
  if (type === "CLAIM") {
    return (
      <span
        style={{
          fontSize: 9,
          fontWeight: 800,
          color: T.black,
          background: T.gray100,
          textTransform: "uppercase",
          letterSpacing: "0.06em",
          padding: "3px 7px",
          borderRadius: 4,
        }}
      >
        Claim
      </span>
    );
  }
  if (type === "EVIDENCE") {
    return (
      <span
        style={{
          fontSize: 9,
          fontWeight: 800,
          color: T.black,
          background: T.gray100,
          textTransform: "uppercase",
          letterSpacing: "0.06em",
          padding: "3px 7px",
          borderRadius: 4,
        }}
      >
        Evidence
      </span>
    );
  }
  if (type === "QUESTION") {
    return (
      <span
        style={{
          fontSize: 9,
          fontWeight: 800,
          color: T.white,
          background: T.black,
          textTransform: "uppercase",
          letterSpacing: "0.06em",
          padding: "3px 7px",
          borderRadius: 4,
        }}
      >
        ?
      </span>
    );
  }
  if (type === "RISK") {
    return (
      <span
        style={{
          fontSize: 9,
          fontWeight: 800,
          color: T.red500,
          background: `${T.red500}22`,
          textTransform: "uppercase",
          letterSpacing: "0.06em",
          padding: "3px 7px",
          borderRadius: 4,
        }}
      >
        Risk
      </span>
    );
  }
  return (
    <span
      style={{
        fontSize: 9,
        fontWeight: 800,
        color: T.gray500,
        background: T.gray100,
        textTransform: "uppercase",
        letterSpacing: "0.06em",
        padding: "3px 7px",
        borderRadius: 4,
      }}
    >
      {type.replace(/_/g, " ")}
    </span>
  );
}

function GhostCard({
  candidate,
  index,
  pan,
  zoom,
  viewport,
  canvasId,
  onMutateCandidates,
}: {
  candidate: CandidateElement;
  index: number;
  pan: { x: number; y: number };
  zoom: number;
  viewport: { w: number; h: number };
  canvasId: string;
  onMutateCandidates: () => Promise<unknown>;
}) {
  const { mutate: mutateGlobal } = useSWRConfig();
  const [busy, setBusy] = useState<"accept" | "dismiss" | null>(null);

  const stackPos = ghostStackPosition(index, pan, zoom, viewport);
  const fallback = extractSuggestedPosition(candidate);
  const title = (candidate.title ?? "").trim() || "Suggestion";
  const body = (candidate.contentMarkdown ?? "").trim();
  const kind = String(candidate.suggestedElementType ?? "CLAIM");
  const isBusy = busy !== null;

  const onAccept = () => {
    setBusy("accept");
    void promoteCandidate(candidate.id, {
      canvasId,
      elementType: kind,
      title: candidate.title,
      contentMarkdown: candidate.contentMarkdown ?? "",
      x: stackPos.x,
      y: stackPos.y,
      width: fallback.width,
      height: fallback.height,
    })
      .then(async () => {
        await Promise.all([
          mutateGlobal(["canvasElements", canvasId]),
          mutateGlobal(["canvasConnections", canvasId]),
          onMutateCandidates(),
        ]);
      })
      .finally(() => setBusy(null));
  };

  const onDismiss = () => {
    setBusy("dismiss");
    void dismissCandidate(candidate.id)
      .then(() => onMutateCandidates())
      .finally(() => setBusy(null));
  };

  return (
    <div
      role="group"
      aria-label={`AI suggestion: ${title}`}
      onMouseDown={(e) => e.stopPropagation()}
      style={{
        position: "absolute",
        left: stackPos.x,
        top: stackPos.y,
        width: GHOST_WIDTH,
        boxSizing: "border-box",
        zIndex: 6,
        border: `1px dashed ${T.gray300}`,
        borderRadius: 10,
        background: "rgba(255, 255, 255, 0.6)",
        padding: "12px 14px",
        fontFamily: T.fontSans,
        display: "flex",
        flexDirection: "column",
        gap: 8,
        pointerEvents: "auto",
        boxShadow: "0 2px 12px rgba(0,0,0,0.06)",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 8,
        }}
      >
        <span
          style={{
            fontSize: 10,
            fontWeight: 600,
            color: T.gray400,
            textTransform: "uppercase",
            letterSpacing: "0.06em",
          }}
        >
          Suggested by AI
        </span>
        <KindBadge kind={kind} />
      </div>

      <GhostCardBody
        title={title}
        body={body}
        isBusy={isBusy}
        busy={busy}
        onAccept={onAccept}
        onDismiss={onDismiss}
      />
    </div>
  );
}

function GhostCardBody({
  title,
  body,
  isBusy,
  busy,
  onAccept,
  onDismiss,
}: {
  title: string;
  body: string;
  isBusy: boolean;
  busy: "accept" | "dismiss" | null;
  onAccept: () => void;
  onDismiss: () => void;
}) {
  return (
    <>
      <div
        style={{
          fontSize: 13,
          fontWeight: 700,
          color: T.black,
          lineHeight: 1.35,
          wordBreak: "break-word",
        }}
      >
        {title}
      </div>

      {body ? (
        <div
          style={{
            fontSize: 12,
            color: T.gray600,
            lineHeight: 1.5,
            display: "-webkit-box",
            WebkitLineClamp: 3,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {body}
        </div>
      ) : null}

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          marginTop: 4,
        }}
      >
        <button
          type="button"
          disabled={isBusy}
          onClick={onAccept}
          style={{
            flex: 1,
            height: 32,
            borderRadius: 8,
            border: "none",
            background: T.black,
            color: T.white,
            fontFamily: T.fontSans,
            fontSize: 12,
            fontWeight: 700,
            cursor: isBusy ? "not-allowed" : "pointer",
            opacity: isBusy && busy !== "accept" ? 0.5 : 1,
          }}
        >
          Accept
        </button>
        <button
          type="button"
          disabled={isBusy}
          onClick={onDismiss}
          style={{
            flex: 1,
            height: 32,
            borderRadius: 8,
            border: `1px solid ${T.border}`,
            background: "transparent",
            color: T.gray400,
            fontFamily: T.fontSans,
            fontSize: 12,
            fontWeight: 600,
            cursor: isBusy ? "not-allowed" : "pointer",
            opacity: isBusy && busy !== "dismiss" ? 0.5 : 1,
          }}
        >
          Dismiss
        </button>
      </div>
    </>
  );
}

export function CandidateGhostLayer({
  projectId,
  chatId,
  canvasId,
  semanticZoomLevel,
  pan,
  zoom,
  viewport,
}: {
  projectId: string;
  chatId: string | null;
  canvasId: string | null;
  semanticZoomLevel: "cluster" | "node";
  pan: { x: number; y: number };
  zoom: number;
  viewport: { w: number; h: number };
}) {
  const { pendingCandidates, mutate } = usePendingCanvasCandidates(
    projectId,
    chatId,
    { refreshInterval: chatId ? 4000 : 0 },
  );

  if (semanticZoomLevel === "cluster" || !canvasId || !chatId) {
    return null;
  }

  if (pendingCandidates.length === 0) {
    return null;
  }

  return (
    <>
      {pendingCandidates.map((c, index) => (
        <GhostCard
          key={c.id}
          candidate={c}
          index={index}
          pan={pan}
          zoom={zoom}
          viewport={viewport}
          canvasId={canvasId}
          onMutateCandidates={mutate}
        />
      ))}
    </>
  );
}
