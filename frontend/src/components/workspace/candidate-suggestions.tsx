import { useMemo, useState } from "react";
import { useSWRConfig } from "swr";

import { useCandidates } from "@/hooks/useCandidates";
import { T } from "@/styles/tokens";
import type { CandidateElement } from "@/types/workspace";

function candidateLabel(c: CandidateElement) {
  const title = (c.title ?? "").trim();
  if (title) return title;
  const md = (c.contentMarkdown ?? "").replace(/\s+/g, " ").trim();
  if (!md) return "Suggestion";
  return md.slice(0, 60) + (md.length > 60 ? "…" : "");
}

function isFiniteNumber(x: unknown): x is number {
  return typeof x === "number" && Number.isFinite(x);
}

function stableIntHash(input: string) {
  // Small deterministic hash for layout jittering (not crypto).
  let h = 0;
  for (let i = 0; i < input.length; i++) {
    h = (h * 31 + input.charCodeAt(i)) | 0;
  }
  return Math.abs(h);
}

function extractSuggestedPosition(c: CandidateElement): {
  x: number;
  y: number;
  width: number | null;
  height: number | null;
} {
  const raw = (c.contentJson as { suggested_position?: unknown } | null | undefined)
    ?.suggested_position;
  if (!raw || typeof raw !== "object") {
    const h = stableIntHash(c.id);
    const dx = (h % 5) * 28;
    const dy = (Math.floor(h / 5) % 5) * 22;
    return { x: 320 + dx, y: 240 + dy, width: 320, height: 180 };
  }
  const r = raw as Record<string, unknown>;
  const x = isFiniteNumber(r.x) ? r.x : 320;
  const y = isFiniteNumber(r.y) ? r.y : 240;
  const width = isFiniteNumber(r.width) ? r.width : 320;
  const height = isFiniteNumber(r.height) ? r.height : 180;
  return { x, y, width, height };
}

export function CandidateSuggestions({
  assistantTurnId,
  canvasId,
}: {
  assistantTurnId: string;
  canvasId: string;
}) {
  const { mutate } = useSWRConfig();
  const { candidates, isLoading, promote, dismiss } = useCandidates(assistantTurnId);
  const [busyIds, setBusyIds] = useState<Record<string, "promote" | "dismiss">>(
    {},
  );

  const pending = useMemo(
    () => candidates.filter((c) => String(c.status).toUpperCase() === "PENDING"),
    [candidates],
  );

  if (!isLoading && pending.length === 0) return null;

  return (
    <div style={{ marginTop: 10 }}>
      <div
        style={{
          fontSize: 10,
          fontWeight: 800,
          color: T.gray400,
          textTransform: "uppercase",
          letterSpacing: "0.1em",
          marginBottom: 8,
          fontFamily: T.fontSans,
        }}
      >
        Suggestions
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {pending.map((c) => {
          const label = candidateLabel(c);
          const isBusy = Boolean(busyIds[c.id]);
          const pos = extractSuggestedPosition(c);
          return (
            <div
              key={c.id}
              style={{
                border: `1px solid ${T.border}`,
                background: T.white,
                borderRadius: 10,
                padding: "10px 12px",
                display: "flex",
                alignItems: "flex-start",
                justifyContent: "space-between",
                gap: 10,
              }}
            >
              <div style={{ minWidth: 0 }}>
                <div
                  style={{
                    fontFamily: T.fontSans,
                    fontSize: 12,
                    fontWeight: 600,
                    color: T.black,
                    lineHeight: 1.35,
                    wordBreak: "break-word",
                  }}
                >
                  {label}
                </div>
                <div
                  style={{
                    marginTop: 4,
                    fontFamily: T.fontSans,
                    fontSize: 11,
                    color: T.gray500,
                    textTransform: "uppercase",
                    letterSpacing: "0.06em",
                    fontWeight: 700,
                  }}
                >
                  {String(c.suggestedElementType ?? "").replace(/_/g, " ")}
                </div>
              </div>

              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  flexShrink: 0,
                }}
              >
                <button
                  type="button"
                  disabled={isBusy}
                  onClick={() => {
                    setBusyIds((cur) => ({ ...cur, [c.id]: "promote" }));
                    void promote(c.id, {
                      canvasId,
                      elementType: c.suggestedElementType,
                      title: c.title,
                      contentMarkdown: c.contentMarkdown ?? "",
                      x: pos.x,
                      y: pos.y,
                      width: pos.width,
                      height: pos.height,
                    })
                      .then(async () => {
                        // Remove locally and refresh canvas elements.
                        await Promise.all([
                          mutate(["canvasElements", canvasId]),
                          mutate(["canvasConnections", canvasId]),
                        ]);
                      })
                      .finally(() => {
                        setBusyIds((cur) => {
                          const next = { ...cur };
                          delete next[c.id];
                          return next;
                        });
                      });
                  }}
                  style={{
                    height: 28,
                    padding: "0 10px",
                    borderRadius: 8,
                    border: `1px solid ${T.border}`,
                    background: T.gray100,
                    fontFamily: T.fontSans,
                    fontSize: 12,
                    fontWeight: 700,
                    color: T.black,
                    cursor: isBusy ? "not-allowed" : "pointer",
                    opacity: isBusy ? 0.55 : 1,
                    whiteSpace: "nowrap",
                  }}
                >
                  + Add to canvas
                </button>
                <button
                  type="button"
                  disabled={isBusy}
                  onClick={() => {
                    setBusyIds((cur) => ({ ...cur, [c.id]: "dismiss" }));
                    void dismiss(c.id).finally(() => {
                      setBusyIds((cur) => {
                        const next = { ...cur };
                        delete next[c.id];
                        return next;
                      });
                    });
                  }}
                  style={{
                    height: 28,
                    padding: "0 10px",
                    borderRadius: 8,
                    border: `1px solid ${T.border}`,
                    background: "transparent",
                    fontFamily: T.fontSans,
                    fontSize: 12,
                    fontWeight: 700,
                    color: T.gray500,
                    cursor: isBusy ? "not-allowed" : "pointer",
                    opacity: isBusy ? 0.55 : 1,
                    whiteSpace: "nowrap",
                  }}
                >
                  Dismiss
                </button>
              </div>
            </div>
          );
        })}

        {isLoading ? (
          <div
            style={{
              fontFamily: T.fontSans,
              fontSize: 12,
              color: T.gray400,
              padding: "2px 2px 0",
            }}
          >
            Checking for suggestions…
          </div>
        ) : null}
      </div>
    </div>
  );
}

