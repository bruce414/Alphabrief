import { useMemo, useState } from "react";
import { useSWRConfig } from "swr";

import type { SuggestedCanvasInsight } from "@/lib/followUpQuestions";
import { createManualElement } from "@/lib/workspaceApi";
import { T } from "@/styles/tokens";

function stableIntHash(input: string) {
  let h = 0;
  for (let i = 0; i < input.length; i++) {
    h = (h * 31 + input.charCodeAt(i)) | 0;
  }
  return Math.abs(h);
}

function layoutForInsight(insight: SuggestedCanvasInsight, index: number) {
  const h = stableIntHash(`${insight.title}:${insight.contentMarkdown}:${index}`);
  const dx = (h % 5) * 28;
  const dy = (Math.floor(h / 5) % 5) * 22;
  return { x: 300 + dx, y: 220 + dy, width: 320, height: 200 };
}

function insightSummary(ins: SuggestedCanvasInsight, maxLen = 140) {
  const raw = (ins.contentMarkdown ?? "").replace(/\s+/g, " ").trim();
  if (!raw) return "";
  return raw.length > maxLen ? `${raw.slice(0, maxLen)}…` : raw;
}

export function MentionedEntitiesBlock({ entities }: { entities: string[] }) {
  if (!entities.length) return null;
  return (
    <div style={{ marginTop: 14 }}>
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
        Key financial entities
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
        {entities.map((e, i) => (
          <div
            key={`${i}-${e.slice(0, 48)}`}
            style={{
              display: "inline-flex",
              alignItems: "center",
              padding: "5px 10px",
              border: `1px solid ${T.border}`,
              borderRadius: 8,
              fontSize: 12,
              fontWeight: 600,
              color: T.black,
              fontFamily: T.fontSans,
              lineHeight: 1.35,
              maxWidth: "100%",
              wordBreak: "break-word",
            }}
          >
            {e}
          </div>
        ))}
      </div>
    </div>
  );
}

export function CanvasInsightSuggestions({
  insights,
  canvasId,
  disabled,
}: {
  insights: SuggestedCanvasInsight[];
  canvasId: string | null | undefined;
  disabled?: boolean;
}) {
  const { mutate } = useSWRConfig();
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [dismissed, setDismissed] = useState<Record<string, true>>({});
  const [addedToCanvas, setAddedToCanvas] = useState<Record<string, true>>({});

  const visible = useMemo(
    () =>
      insights
        .map((ins, idx) => ({ ins, idx, key: `${idx}:${ins.elementType}:${ins.title}:${ins.contentMarkdown.slice(0, 40)}` }))
        .filter(({ key }) => !dismissed[key]),
    [insights, dismissed],
  );

  if (!visible.length) return null;

  return (
    <div style={{ marginTop: 14 }}>
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
        Canvas insight cards
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {visible.map(({ ins, idx, key }) => {
          const busyId = key;
          const isBusy = busyKey === busyId;
          const pos = layoutForInsight(ins, idx);
          const mdOneLine = ins.contentMarkdown.replace(/\s+/g, " ").trim();
          const title =
            (ins.title ?? "").trim() ||
            mdOneLine.slice(0, 72) + (mdOneLine.length > 72 ? "…" : "");
          const typeLabel = ins.elementType.replace(/_/g, " ");
          const summary = insightSummary(ins);
          const canAdd = Boolean(canvasId) && !disabled;
          const isAdded = Boolean(addedToCanvas[key]);

          return (
            <div
              key={key}
              style={{
                border: `1px solid ${T.border}`,
                background: T.white,
                borderRadius: 10,
                padding: "10px 12px",
                display: "flex",
                flexDirection: "column",
                gap: 8,
              }}
            >
              <div
                style={{
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
                    {title}
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
                    {typeLabel}
                  </div>
                  {summary ? (
                    <div
                      style={{
                        marginTop: 6,
                        fontFamily: T.fontSans,
                        fontSize: 11,
                        color: T.gray600,
                        lineHeight: 1.45,
                      }}
                    >
                      {summary}
                    </div>
                  ) : null}
                </div>
              </div>
              <div
                style={{
                  display: "flex",
                  justifyContent: "flex-end",
                  alignItems: "center",
                  gap: 8,
                  flexWrap: "wrap",
                }}
              >
                {isAdded ? (
                  <div
                    title="Added to canvas"
                    style={{
                      height: 28,
                      display: "inline-flex",
                      alignItems: "center",
                      gap: 6,
                      padding: "0 10px",
                      borderRadius: 8,
                      border: "1px solid #bbf7d0",
                      background: "#f0fdf4",
                      fontFamily: T.fontSans,
                      fontSize: 12,
                      fontWeight: 700,
                      color: "#15803d",
                      whiteSpace: "nowrap",
                    }}
                  >
                    <svg
                      width="14"
                      height="14"
                      viewBox="0 0 16 16"
                      fill="none"
                      aria-hidden
                    >
                      <circle cx="8" cy="8" r="8" fill="#22c55e" />
                      <path
                        d="M4.5 8.2 7 10.7 11.5 5.2"
                        stroke="white"
                        strokeWidth="1.6"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                    Added
                  </div>
                ) : (
                  <button
                    type="button"
                    title={
                      !canvasId ? "No canvas available for this chat" : undefined
                    }
                    disabled={!canAdd || isBusy}
                    onClick={() => {
                      if (!canvasId || !canAdd) return;
                      setBusyKey(busyId);
                      void createManualElement(canvasId, {
                        elementType: ins.elementType,
                        title: (ins.title ?? "").trim() || null,
                        contentMarkdown: ins.contentMarkdown,
                        contentJson: {},
                        x: pos.x,
                        y: pos.y,
                        width: pos.width,
                        height: pos.height,
                      })
                        .then(async () => {
                          await mutate(["canvasElements", canvasId]);
                          setAddedToCanvas((a) => ({ ...a, [key]: true }));
                        })
                        .finally(() => setBusyKey(null));
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
                      cursor: !canAdd || isBusy ? "not-allowed" : "pointer",
                      opacity: !canAdd || isBusy ? 0.55 : 1,
                      whiteSpace: "nowrap",
                    }}
                  >
                    + Add to canvas
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => setDismissed((d) => ({ ...d, [key]: true }))}
                  style={{
                    height: 28,
                    padding: "0 10px",
                    borderRadius: 8,
                    border: `1px solid ${T.border}`,
                    background: T.white,
                    fontFamily: T.fontSans,
                    fontSize: 12,
                    fontWeight: 600,
                    color: T.gray600,
                    cursor: "pointer",
                  }}
                >
                  Dismiss
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
