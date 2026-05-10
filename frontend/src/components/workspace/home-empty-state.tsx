import { AlphaBriefLogo } from "@/components/workspace/logo";
import {
  ChatInputBar,
  type ApiResearchMode,
} from "@/components/workspace/chat-input-bar";
import { Icon } from "@/components/workspace/icons";
import { T } from "@/styles/tokens";

export type HomeEmptyStateProps = {
  onSend: (text: string, researchMode: ApiResearchMode) => void;
  inputDisabled?: boolean;
};

export function HomeEmptyState({
  onSend,
  inputDisabled = false,
}: HomeEmptyStateProps) {
  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        background: T.bgPanel,
        fontFamily: T.fontSans,
      }}
    >
      <div
        style={{
          height: 52,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 20px",
          borderBottom: `1px solid ${T.border}`,
          background: T.bgPanel,
          flexShrink: 0,
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            fontSize: 13,
            color: T.gray500,
          }}
        >
          <Icon.Agent />
          <span style={{ fontWeight: 600, color: T.black }}>Agent</span>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {(
            [
              { IconBtn: Icon.Pin, label: "Pin" },
              { IconBtn: Icon.Share, label: "Share" },
            ] as const
          ).map(({ IconBtn, label }) => (
            <button
              key={label}
              type="button"
              disabled
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                padding: "5px 12px",
                border: `1px solid ${T.border}`,
                borderRadius: 8,
                background: T.white,
                cursor: "not-allowed",
                fontFamily: T.fontSans,
                fontSize: 12,
                color: T.gray600,
                opacity: 0.7,
              }}
            >
              <IconBtn />
              {label}
            </button>
          ))}
        </div>
      </div>

      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: 40,
          minHeight: 0,
        }}
      >
        <AlphaBriefLogo size={40} showText={false} />
        <div
          style={{
            marginTop: 24,
            fontSize: 22,
            fontWeight: 700,
            color: T.black,
            letterSpacing: "-0.02em",
            textAlign: "center",
          }}
        >
          Ready when you are, Bruce.
        </div>
        <div
          style={{
            marginTop: 8,
            fontSize: 14,
            color: T.gray400,
            textAlign: "center",
          }}
        >
          Ask anything, paste a URL, or drop in a document to get started.
        </div>
      </div>

      <ChatInputBar onSend={onSend} disabled={inputDisabled} />
    </div>
  );
}
