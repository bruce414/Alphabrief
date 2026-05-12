import { useMemo, useState } from "react";

import { UrlPreviewChips } from "@/components/workspace/inline-source-chips";
import { Icon } from "@/components/workspace/icons";
import { MAX_USER_MESSAGE_CHARS } from "@/lib/chatLimits";
import { T } from "@/styles/tokens";

const URL_IN_TEXT = /https?:\/\/[^\s]+/g;

function urlsInText(text: string): string[] {
  const out: string[] = [];
  const seen = new Set<string>();
  for (const m of text.matchAll(URL_IN_TEXT)) {
    const u = m[0];
    if (!seen.has(u)) {
      seen.add(u);
      out.push(u);
    }
  }
  return out;
}

export type ApiResearchMode = "QUICK" | "STANDARD" | "DEEP";

const MODE_LABELS = [
  "Standard research",
  "Quick research",
  "Deep research",
] as const;

const MODE_VALUES: ApiResearchMode[] = ["STANDARD", "QUICK", "DEEP"];

export type ChatInputBarProps = {
  onSend: (text: string, researchMode: ApiResearchMode) => void;
  /** While the assistant is generating, show a stop control instead of send. */
  isGenerating?: boolean;
  onStop?: () => void;
  placeholder?: string;
  disabled?: boolean;
  containerBackground?: string;
};

export function ChatInputBar({
  onSend,
  isGenerating = false,
  onStop,
  placeholder = "Ask, or paste a URL to research...",
  disabled = false,
  containerBackground = T.bgPanel,
}: ChatInputBarProps) {
  const [val, setVal] = useState("");
  const [modeIndex, setModeIndex] = useState(0);
  const modeLabel = MODE_LABELS[modeIndex];
  const researchMode = MODE_VALUES[modeIndex];

  const trimmed = val.trim();
  const canSend = trimmed.length > 0 && !disabled && !isGenerating;
  const showStop = isGenerating && Boolean(onStop);
  const previewUrls = useMemo(() => urlsInText(val), [val]);

  function handleSend() {
    if (!canSend) return;
    onSend(trimmed, researchMode);
    setVal("");
  }

  return (
    <div
      style={{
        padding: "16px 24px 20px",
        background: containerBackground,
      }}
    >
      <div
        style={{
          background: T.white,
          border: `1px solid ${T.border}`,
          borderRadius: 14,
          boxShadow: "0 2px 12px rgba(0,0,0,0.06)",
          overflow: "hidden",
        }}
      >
        <UrlPreviewChips urls={previewUrls} />
        <textarea
          value={val}
          disabled={disabled || isGenerating}
          maxLength={MAX_USER_MESSAGE_CHARS}
          onChange={(e) => setVal(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          placeholder={placeholder}
          rows={1}
          style={{
            width: "100%",
            padding: "14px 16px 8px",
            border: "none",
            outline: "none",
            resize: "none",
            fontFamily: T.fontSans,
            fontSize: 14,
            color: T.black,
            background: "transparent",
            boxSizing: "border-box",
          }}
        />
        <div
          style={{
            display: "flex",
            alignItems: "center",
            padding: "8px 12px 10px",
            gap: 8,
          }}
        >
          <button
            type="button"
            title="Uploads coming soon"
            disabled
            style={{
              background: "none",
              border: "none",
              cursor: "not-allowed",
              color: T.gray400,
              padding: 6,
              borderRadius: 6,
              display: "flex",
              opacity: 0.55,
            }}
          >
            <Icon.Attach />
          </button>
          <button
            type="button"
            aria-label="Web"
            style={{
              background: "none",
              border: "none",
              cursor: disabled ? "not-allowed" : "pointer",
              color: T.gray400,
              padding: 6,
              borderRadius: 6,
              display: "flex",
            }}
          >
            <Icon.Globe />
          </button>
          <button
            type="button"
            aria-label="Sources"
            style={{
              background: "none",
              border: "none",
              cursor: disabled ? "not-allowed" : "pointer",
              color: T.gray400,
              padding: 6,
              borderRadius: 6,
              display: "flex",
            }}
          >
            <Icon.Database />
          </button>
          <div style={{ flex: 1 }} />
          <button
            type="button"
            disabled={disabled}
            onClick={() =>
              setModeIndex((i) => (i + 1) % MODE_LABELS.length)
            }
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              padding: "6px 12px",
              border: `1px solid ${T.border}`,
              borderRadius: 8,
              background: T.white,
              cursor: disabled || isGenerating ? "not-allowed" : "pointer",
              fontFamily: T.fontSans,
              fontSize: 12,
              fontWeight: 500,
              color: T.black,
              flexShrink: 0,
              whiteSpace: "nowrap",
              opacity: isGenerating ? 0.55 : 1,
            }}
          >
            {modeLabel}
            <Icon.ChevronDown />
          </button>
          {showStop ? (
            <button
              type="button"
              aria-label="Stop generation"
              title="Stop generation"
              onClick={() => onStop?.()}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                padding: "8px 12px",
                background: T.black,
                color: T.white,
                border: "none",
                borderRadius: 8,
                cursor: "pointer",
                fontFamily: T.fontSans,
                fontSize: 12,
                fontWeight: 600,
                flexShrink: 0,
              }}
            >
              <Icon.Stop width={14} height={14} />
            </button>
          ) : (
            <button
              type="button"
              disabled={!canSend}
              onClick={handleSend}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                padding: "8px 12px",
                background: canSend ? T.black : T.gray300,
                color: T.white,
                border: "none",
                borderRadius: 8,
                cursor: canSend ? "pointer" : "not-allowed",
                fontFamily: T.fontSans,
                fontSize: 12,
                fontWeight: 600,
                flexShrink: 0,
              }}
            >
              <Icon.Send />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
