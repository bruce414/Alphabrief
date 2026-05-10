import { useState } from "react";

import { Icon } from "@/components/workspace/icons";
import { T } from "@/styles/tokens";

export type ApiResearchMode = "QUICK" | "STANDARD" | "DEEP";

const MODE_LABELS = [
  "Standard research",
  "Quick research",
  "Deep research",
] as const;

const MODE_VALUES: ApiResearchMode[] = ["STANDARD", "QUICK", "DEEP"];

export type ChatInputBarProps = {
  onSend: (text: string, researchMode: ApiResearchMode) => void;
  placeholder?: string;
  disabled?: boolean;
};

export function ChatInputBar({
  onSend,
  placeholder = "Ask, or paste a URL to research...",
  disabled = false,
}: ChatInputBarProps) {
  const [val, setVal] = useState("");
  const [modeIndex, setModeIndex] = useState(0);
  const modeLabel = MODE_LABELS[modeIndex];
  const researchMode = MODE_VALUES[modeIndex];

  const trimmed = val.trim();
  const canSend = trimmed.length > 0 && !disabled;

  function handleSend() {
    if (!canSend) return;
    onSend(trimmed, researchMode);
    setVal("");
  }

  return (
    <div
      style={{
        padding: "16px 24px 20px",
        background: T.bgPanel,
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
        <textarea
          value={val}
          disabled={disabled}
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
              cursor: disabled ? "not-allowed" : "pointer",
              fontFamily: T.fontSans,
              fontSize: 12,
              fontWeight: 500,
              color: T.black,
            }}
          >
            {modeLabel}
            <Icon.ChevronDown />
          </button>
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
            }}
          >
            <Icon.Send />
          </button>
        </div>
      </div>
    </div>
  );
}
