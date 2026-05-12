import { useState } from "react";
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

  if (!insights.length) return null;

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
        {insights.map((ins, idx) => {
          const busyId = `${idx}:${ins.elementType}:${ins.title}`;
          const isBusy = busyKey === busyId;
          const pos = layoutForInsight(ins, idx);
          const mdOneLine = ins.contentMarkdown.replace(/\s+/g, " ").trim();
          const label =
            (ins.title ?? "").trim() ||
            mdOneLine.slice(0, 72) + (mdOneLine.length > 72 ? "…" : "");
          const typeLabel = ins.elementType.replace(/_/g, " ");
          const canAdd = Boolean(canvasId) && !disabled;

          return (
            <div
              key={busyId}
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
                  {typeLabel}
                </div>
              </div>
              <button
                type="button"
                title={!canvasId ? "No canvas available for this chat" : undefined}
                disabled={!canAdd || isBusy}
                onClick={() => {
                  if (!canvasId || !canAdd) return;
                  setBusyKey(busyId);
                  void createManualElement(canvasId, {
                    elementType: ins.elementType,
                    title: (ins.title ?? "").trim() || null,
                    contentMarkdown: ins.contentMarkdown,
                    x: pos.x,
                    y: pos.y,
                    width: pos.width,
                    height: pos.height,
                    provenanceKind: "MANUAL",
                  })
                    .then(async () => {
                      await mutate(["canvasElements", canvasId]);
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
                  flexShrink: 0,
                }}
              >
                + Add to canvas
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
