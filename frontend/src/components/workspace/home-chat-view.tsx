import { useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";

import {
  ChatInputBar,
  type ApiResearchMode,
} from "@/components/workspace/chat-input-bar";
import { Icon } from "@/components/workspace/icons";
import { T } from "@/styles/tokens";

export type ChatMessage = {
  id: string;
  role: "user" | "ai";
  text: string;
  sources?: string[];
  loading?: boolean;
};

export type HomeChatViewProps = {
  chatTitle: string;
  messages: ChatMessage[];
  onSend: (text: string, researchMode: ApiResearchMode) => void;
  inputDisabled?: boolean;
};

export function HomeChatView({
  chatTitle,
  messages,
  onSend,
  inputDisabled = false,
}: HomeChatViewProps) {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

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
            minWidth: 0,
          }}
        >
          <Icon.Agent />
          <span style={{ fontWeight: 600, color: T.black }}>Agent</span>
          <span style={{ color: T.gray300, margin: "0 4px" }}>·</span>
          <span
            style={{
              color: T.gray400,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {chatTitle}
          </span>
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
          overflowY: "auto",
          padding: "32px 60px",
          minHeight: 0,
        }}
      >
        <style>{`
          .home-ai-markdown p { margin: 0 0 0.75em; }
          .home-ai-markdown p:last-child { margin-bottom: 0; }
          .home-ai-markdown h2 {
            font-size: 16px;
            font-weight: 700;
            margin: 1em 0 0.5em;
          }
          .home-ai-markdown h2:first-child { margin-top: 0; }
        `}</style>
        {messages.map((m) => (
          <div
            key={m.id}
            style={{
              marginBottom: 24,
              display: "flex",
              flexDirection: "column",
              alignItems: m.role === "user" ? "flex-end" : "flex-start",
            }}
          >
            {m.role === "user" ? (
              <div
                style={{
                  maxWidth: "60%",
                  background: T.userBubble,
                  color: T.white,
                  padding: "12px 18px",
                  borderRadius: 14,
                  fontFamily: T.fontSans,
                  fontSize: 14,
                  lineHeight: 1.6,
                }}
              >
                {m.text}
              </div>
            ) : (
              <div style={{ maxWidth: "80%" }}>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    marginBottom: 10,
                  }}
                >
                  <div
                    style={{
                      width: 22,
                      height: 22,
                      background: T.black,
                      borderRadius: 6,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      flexShrink: 0,
                    }}
                  >
                    <svg
                      width="12"
                      height="12"
                      viewBox="0 0 100 100"
                      fill="none"
                      xmlns="http://www.w3.org/2000/svg"
                      aria-hidden
                    >
                      <path
                        d="M50 15 L78 78 L50 62 L22 78 Z"
                        fill="white"
                      />
                      <path
                        d="M50 62 L22 78 Q35 68 50 72 Q65 68 78 78 Z"
                        fill="rgba(255,255,255,0.35)"
                      />
                    </svg>
                  </div>
                  <span
                    style={{
                      fontFamily: T.fontSans,
                      fontSize: 11,
                      fontWeight: 700,
                      color: T.black,
                      letterSpacing: "0.05em",
                      textTransform: "uppercase",
                    }}
                  >
                    Alphabrief
                  </span>
                </div>
                <div
                  style={{
                    background: T.white,
                    border: `1px solid ${T.border}`,
                    borderRadius: 12,
                    padding: "16px 20px",
                    fontFamily: T.fontSans,
                    fontSize: 14,
                    color: T.black,
                    lineHeight: 1.7,
                  }}
                >
                  {m.loading ? (
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 8,
                        color: T.gray400,
                      }}
                    >
                      <div
                        style={{
                          width: 6,
                          height: 6,
                          borderRadius: "50%",
                          background: T.gray300,
                          animation: "pulse 1.2s ease infinite",
                          flexShrink: 0,
                        }}
                      />
                      {m.text}
                    </div>
                  ) : (
                    <>
                      <div className="home-ai-markdown">
                        <ReactMarkdown rehypePlugins={[rehypeSanitize]}>
                          {m.text}
                        </ReactMarkdown>
                      </div>
                      {m.sources && m.sources.length > 0 ? (
                        <div
                          style={{
                            display: "flex",
                            gap: 8,
                            marginTop: 14,
                            flexWrap: "wrap",
                          }}
                        >
                          {m.sources.map((s, j) => (
                            <div
                              key={`${m.id}-src-${j}`}
                              style={{
                                display: "flex",
                                alignItems: "center",
                                gap: 5,
                                padding: "4px 10px",
                                border: `1px solid ${T.border}`,
                                borderRadius: 6,
                                fontSize: 11,
                                color: T.gray500,
                                fontFamily: T.fontSans,
                              }}
                            >
                              <Icon.Database
                                width={12}
                                height={12}
                                style={{ flexShrink: 0 }}
                              />
                              [{j + 1}] {s}
                            </div>
                          ))}
                        </div>
                      ) : null}
                    </>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <ChatInputBar onSend={onSend} disabled={inputDisabled} />
    </div>
  );
}
