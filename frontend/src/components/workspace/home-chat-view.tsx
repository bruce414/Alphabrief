import { useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import remarkGfm from "remark-gfm";

import {
  ChatInputBar,
  type ApiResearchMode,
} from "@/components/workspace/chat-input-bar";
import { FollowUpQuestionsBlock } from "@/components/workspace/follow-up-questions";
import { Icon } from "@/components/workspace/icons";
import {
  CanvasInsightSuggestions,
  MentionedEntitiesBlock,
} from "@/components/workspace/reply-tail-blocks";
import { ResearchProgress } from "@/components/workspace/research-progress";
import { T } from "@/styles/tokens";
import type { SuggestedCanvasInsight } from "@/lib/followUpQuestions";
import type { ResearchEvent, Source } from "@/types/workspace";

export type HomeChatTab = "chat" | "sources";

export type ChatMessage = {
  id: string;
  role: "user" | "ai";
  text: string;
  sources?: string[];
  loading?: boolean;
  events?: ResearchEvent[];
  mentionedEntities?: string[];
  suggestedCanvasInsights?: SuggestedCanvasInsight[];
  followUpQuestions?: string[];
};

export type HomeChatViewProps = {
  chatTitle: string;
  messages: ChatMessage[];
  onSend: (text: string, researchMode: ApiResearchMode) => void;
  onFollowUpQuestion: (text: string) => void;
  inputDisabled?: boolean;
  /** While the assistant is generating a reply (including after Regenerate). */
  awaitingReply?: boolean;
  onStopGeneration?: () => void;
  onRegenerateAssistant?: (assistantTurnId: string) => void;
  activeTab: HomeChatTab;
  onTabChange: (tab: HomeChatTab) => void;
  sources: Source[];
  sourcesLoading: boolean;
  /** Catch-all project canvas; when set, "Add to canvas" is enabled for insight cards. */
  canvasId?: string | null;
};

const TABS: { id: HomeChatTab; label: string }[] = [
  { id: "chat", label: "Chat" },
  { id: "sources", label: "Sources" },
];

function hostnameOf(url: string | null | undefined): string {
  if (!url) return "";
  try {
    return new URL(url).hostname.replace(/^www\./i, "");
  } catch {
    return url.replace(/^https?:\/\//i, "").split("/")[0] ?? "";
  }
}

function SourceListPanel({
  sources,
  loading,
}: {
  sources: Source[];
  loading: boolean;
}) {
  const userSources = sources.filter((s) => s.origin !== "ai_web_search");
  const aiSources = sources.filter((s) => s.origin === "ai_web_search");

  return (
    <div
      style={{
        flex: 1,
        overflowY: "auto",
        padding: "28px 60px 60px",
        minHeight: 0,
        background: T.white,
      }}
    >
      <h2
        style={{
          fontSize: 15,
          fontWeight: 600,
          color: T.black,
          margin: "0 0 6px",
          letterSpacing: "-0.01em",
        }}
      >
        Sources
      </h2>
      <p
        style={{
          fontSize: 12,
          color: T.gray500,
          margin: "0 0 22px",
          lineHeight: 1.5,
        }}
      >
        Every URL you've shared or that the assistant researched while answering you in this chat.
      </p>

      {loading ? (
        <div style={{ fontSize: 13, color: T.gray400 }}>Loading sources…</div>
      ) : sources.length === 0 ? (
        <div
          style={{
            fontSize: 13,
            color: T.gray400,
            padding: "12px 14px",
            border: `1px dashed ${T.border}`,
            borderRadius: 10,
            background: T.white,
          }}
        >
          No sources yet. Paste a URL or ask a research question and the
          assistant will surface what it consulted here.
        </div>
      ) : (
        <>
          {userSources.length > 0 ? (
            <SourceSection
              title="Shared by you"
              caption={`${userSources.length} item${userSources.length === 1 ? "" : "s"}`}
              items={userSources}
            />
          ) : null}
          {aiSources.length > 0 ? (
            <SourceSection
              title="Researched by AI"
              caption={`${aiSources.length} item${aiSources.length === 1 ? "" : "s"}`}
              items={aiSources}
            />
          ) : null}
        </>
      )}
    </div>
  );
}

function SourceSection({
  title,
  caption,
  items,
}: {
  title: string;
  caption: string;
  items: Source[];
}) {
  return (
    <section style={{ marginBottom: 28 }}>
      <div
        style={{
          display: "flex",
          alignItems: "baseline",
          justifyContent: "space-between",
          marginBottom: 10,
        }}
      >
        <h3
          style={{
            fontSize: 11,
            fontWeight: 700,
            color: T.gray600,
            letterSpacing: "0.06em",
            textTransform: "uppercase",
            margin: 0,
          }}
        >
          {title}
        </h3>
        <span style={{ fontSize: 11, color: T.gray400 }}>{caption}</span>
      </div>
      <div
        style={{
          background: T.white,
          border: `1px solid ${T.border}`,
          borderRadius: 10,
          overflow: "hidden",
        }}
      >
        {items.map((s, i) => {
          const url = s.normalizedUrl ?? "";
          const host = hostnameOf(url);
          const label = (s.title?.trim() || s.publisher?.trim() || host || "Untitled source");
          return (
            <a
              key={s.id}
              href={url || undefined}
              target={url ? "_blank" : undefined}
              rel={url ? "noreferrer" : undefined}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
                padding: "12px 14px",
                borderTop: i === 0 ? "none" : `1px solid ${T.border}`,
                textDecoration: "none",
                color: T.black,
                background: T.white,
              }}
            >
              <Icon.Sources style={{ color: T.gray400, flexShrink: 0 }} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div
                  style={{
                    fontSize: 13,
                    color: T.black,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                  title={label}
                >
                  {label}
                </div>
                <div
                  style={{
                    fontSize: 11,
                    color: T.gray500,
                    marginTop: 2,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                  title={url}
                >
                  {host || s.sourceType}
                </div>
              </div>
              {url ? (
                <Icon.ArrowUpRight
                  width={14}
                  height={14}
                  style={{ color: T.gray400, flexShrink: 0 }}
                />
              ) : null}
            </a>
          );
        })}
      </div>
    </section>
  );
}

export function HomeChatView({
  chatTitle,
  messages,
  onSend,
  onFollowUpQuestion,
  inputDisabled = false,
  awaitingReply = false,
  onStopGeneration,
  onRegenerateAssistant,
  activeTab,
  onTabChange,
  sources,
  sourcesLoading,
  canvasId = null,
}: HomeChatViewProps) {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (activeTab !== "chat") return;
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, activeTab]);

  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        background: T.white,
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
          background: T.white,
          flexShrink: 0,
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 14,
            fontSize: 13,
            minWidth: 0,
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              minWidth: 0,
              maxWidth: 280,
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
          <div
            role="tablist"
            style={{
              display: "flex",
              gap: 0,
              background: T.white,
              border: `1px solid ${T.border}`,
              borderRadius: 8,
              padding: 2,
              flexShrink: 0,
            }}
          >
            {TABS.map((tab) => {
              const active = tab.id === activeTab;
              return (
                <button
                  key={tab.id}
                  type="button"
                  role="tab"
                  aria-selected={active}
                  onClick={() => onTabChange(tab.id)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                    padding: "5px 12px",
                    background: active ? T.gray100 : "transparent",
                    border: "none",
                    borderRadius: 6,
                    cursor: "pointer",
                    fontFamily: T.fontSans,
                    fontSize: 12,
                    fontWeight: active ? 600 : 500,
                    color: active ? T.black : T.gray500,
                  }}
                >
                  {tab.id === "sources" ? (
                    <Icon.Sources style={{ width: 14, height: 14 }} />
                  ) : (
                    <Icon.Chat style={{ width: 14, height: 14 }} />
                  )}
                  {tab.label}
                  {tab.id === "sources" && sources.length > 0 ? (
                    <span
                      style={{
                        fontSize: 11,
                        fontWeight: 600,
                        color: active ? T.black : T.gray500,
                        background: active ? T.white : T.gray100,
                        padding: "1px 6px",
                        borderRadius: 999,
                        marginLeft: 2,
                      }}
                    >
                      {sources.length}
                    </span>
                  ) : null}
                </button>
              );
            })}
          </div>
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

      {activeTab === "sources" ? (
        <SourceListPanel sources={sources} loading={sourcesLoading} />
      ) : (
        <>
          <div
            style={{
              flex: 1,
              overflowY: "auto",
              padding: "32px 60px",
              minHeight: 0,
            }}
          >
            <style>{`
              .home-ai-markdown {
                font-size: 14px;
                line-height: 1.7;
                color: ${T.black};
                word-break: break-word;
              }
              .home-ai-markdown > *:first-child { margin-top: 0; }
              .home-ai-markdown > *:last-child { margin-bottom: 0; }
              .home-ai-markdown p { margin: 0 0 0.85em; }
              .home-ai-markdown h1,
              .home-ai-markdown h2,
              .home-ai-markdown h3,
              .home-ai-markdown h4 {
                font-weight: 700;
                line-height: 1.3;
                margin: 1.1em 0 0.5em;
              }
              .home-ai-markdown h1 { font-size: 20px; }
              .home-ai-markdown h2 { font-size: 16px; }
              .home-ai-markdown h3 { font-size: 14px; }
              .home-ai-markdown ul,
              .home-ai-markdown ol {
                margin: 0 0 0.85em;
                padding-left: 1.4em;
              }
              .home-ai-markdown li { margin: 0.2em 0; }
              .home-ai-markdown li > p { margin: 0 0 0.35em; }
              .home-ai-markdown strong { font-weight: 700; }
              .home-ai-markdown em { font-style: italic; }
              .home-ai-markdown a {
                color: ${T.black};
                text-decoration: underline;
                text-underline-offset: 2px;
              }
              .home-ai-markdown blockquote {
                margin: 0.6em 0 0.85em;
                padding: 0.2em 0 0.2em 14px;
                border-left: 3px solid ${T.gray200};
                color: ${T.gray600};
              }
              .home-ai-markdown code {
                font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
                font-size: 0.92em;
                background: ${T.gray100};
                border: 1px solid ${T.border};
                border-radius: 4px;
                padding: 1px 5px;
              }
              .home-ai-markdown pre {
                margin: 0.6em 0 0.85em;
                padding: 12px 14px;
                background: ${T.gray100};
                border: 1px solid ${T.border};
                border-radius: 8px;
                overflow-x: auto;
              }
              .home-ai-markdown pre code {
                background: transparent;
                border: none;
                padding: 0;
              }
              .home-ai-markdown table {
                border-collapse: collapse;
                margin: 0.6em 0 0.85em;
                font-size: 13px;
                width: 100%;
              }
              .home-ai-markdown th,
              .home-ai-markdown td {
                border: 1px solid ${T.border};
                padding: 6px 10px;
                text-align: left;
                vertical-align: top;
              }
              .home-ai-markdown th {
                background: ${T.gray100};
                font-weight: 600;
              }
              @keyframes pulse {
                0% { transform: scale(1); opacity: 0.6; }
                50% { transform: scale(1.45); opacity: 1; }
                100% { transform: scale(1); opacity: 0.6; }
              }
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
                      whiteSpace: "pre-wrap",
                    }}
                  >
                    {m.text}
                  </div>
                ) : (
                  <div style={{ maxWidth: "80%", width: "100%" }}>
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
                        fontFamily: T.fontSans,
                        fontSize: 14,
                        color: T.black,
                        lineHeight: 1.7,
                      }}
                    >
                      <ResearchProgress
                        events={m.events ?? []}
                        loading={Boolean(m.loading)}
                      />
                      {m.loading &&
                      (m.events?.length ?? 0) === 0 &&
                      !m.text ? (
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
                          Thinking…
                        </div>
                      ) : null}
                      {!m.loading && m.text ? (
                        <>
                          <div className="home-ai-markdown">
                            <ReactMarkdown
                              remarkPlugins={[remarkGfm]}
                              rehypePlugins={[rehypeSanitize]}
                            >
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
                          {m.mentionedEntities &&
                          m.mentionedEntities.length > 0 ? (
                            <MentionedEntitiesBlock entities={m.mentionedEntities} />
                          ) : null}
                          {m.suggestedCanvasInsights &&
                          m.suggestedCanvasInsights.length > 0 ? (
                            <CanvasInsightSuggestions
                              insights={m.suggestedCanvasInsights}
                              canvasId={canvasId}
                              disabled={inputDisabled || awaitingReply}
                            />
                          ) : null}
                          {m.followUpQuestions && m.followUpQuestions.length > 0 ? (
                            <FollowUpQuestionsBlock
                              questions={m.followUpQuestions}
                              onSelect={onFollowUpQuestion}
                              disabled={inputDisabled || awaitingReply}
                            />
                          ) : null}
                          {onRegenerateAssistant ? (
                            <div style={{ marginTop: 12 }}>
                              <button
                                type="button"
                                disabled={inputDisabled || awaitingReply}
                                onClick={() =>
                                  void onRegenerateAssistant(m.id)
                                }
                                style={{
                                  border: "none",
                                  background: "transparent",
                                  padding: 0,
                                  cursor:
                                    inputDisabled || awaitingReply
                                      ? "not-allowed"
                                      : "pointer",
                                  fontFamily: T.fontSans,
                                  fontSize: 12,
                                  fontWeight: 600,
                                  color: T.gray500,
                                  textDecoration: "underline",
                                  textUnderlineOffset: 3,
                                }}
                              >
                                Regenerate response
                              </button>
                            </div>
                          ) : null}
                        </>
                      ) : null}
                    </div>
                  </div>
                )}
              </div>
            ))}
            <div ref={bottomRef} />
          </div>

          <ChatInputBar
            onSend={onSend}
            isGenerating={awaitingReply}
            onStop={onStopGeneration}
            disabled={inputDisabled}
            containerBackground={T.white}
          />
        </>
      )}
    </div>
  );
}
