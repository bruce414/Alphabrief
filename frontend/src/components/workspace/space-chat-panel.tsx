import { useCallback, useEffect, useMemo, useRef } from "react";
import useSWR from "swr";
import { useSWRConfig } from "swr";

import {
  ChatInputBar,
  type ApiResearchMode,
} from "@/components/workspace/chat-input-bar";
import { Icon } from "@/components/workspace/icons";
import { useChats } from "@/hooks/useChats";
import { ApiError } from "@/lib/api";
import { createChat, listChatTurns, sendChatMessage } from "@/lib/workspaceApi";
import { T } from "@/styles/tokens";
import type { Chat, ChatTurn } from "@/types/workspace";

function hasPendingTurn(turns: ChatTurn[] | undefined) {
  if (!turns || turns.length === 0) return false;
  return turns.some((t) => t.status === "QUEUED" || t.status === "RUNNING");
}

function paragraphs(md: string | null | undefined) {
  const raw = md?.trim() ?? "";
  if (!raw) return [];
  return raw.split("\n\n").map((p) => p.trim()).filter(Boolean);
}

function extractCreatedSourceIds(turn: ChatTurn): string[] {
  const cj = (turn.contentJson ?? {}) as Record<string, unknown>;
  const direct = cj.createdSourceIds;
  if (Array.isArray(direct)) return direct.filter((x): x is string => typeof x === "string");
  const meta = cj.metadata;
  if (meta && typeof meta === "object") {
    const ids = (meta as Record<string, unknown>).createdSourceIds;
    if (Array.isArray(ids)) return ids.filter((x): x is string => typeof x === "string");
  }
  return [];
}

export function useSpaceChat(projectId: string, chatId: string | null) {
  const { chats, isLoading: chatsLoading } = useChats(projectId);
  const { mutate: mutateGlobal } = useSWRConfig();

  const resolvedChatId = useMemo(() => {
    return chatId ?? chats[0]?.id ?? null;
  }, [chatId, chats]);

  const chat: Chat | null = useMemo(() => {
    if (!resolvedChatId) return null;
    return chats.find((c) => c.id === resolvedChatId) ?? null;
  }, [chats, resolvedChatId]);

  const {
    data: turnsRes,
    isLoading: turnsLoading,
    mutate: mutateTurns,
  } = useSWR<{ items: ChatTurn[] }>(
    resolvedChatId ? (["turns", resolvedChatId] as const) : null,
    () => listChatTurns(resolvedChatId as string),
    {
      refreshInterval: (latest) => (hasPendingTurn(latest?.items) ? 1500 : 0),
    },
  );

  const turns = turnsRes?.items ?? [];

  const sendingRef = useRef(false);

  const onSend = useCallback(
    async (text: string, researchMode: ApiResearchMode) => {
      const trimmed = text.trim();
      if (!trimmed || sendingRef.current) return;
      sendingRef.current = true;

      let effectiveChatId = resolvedChatId;
      try {
        if (!effectiveChatId) {
          const newChat = await createChat(projectId, { title: "New chat" });
          effectiveChatId = newChat.id;
          mutateGlobal(
            ["chats", projectId],
            (cur: { items?: Chat[] } | undefined) => ({
              items: [newChat, ...((cur?.items ?? []).filter((c) => c.id !== newChat.id))],
            }),
            { revalidate: false },
          );
        }

        const nowIso = new Date().toISOString();
        const maxIdx = turns.reduce((m, t) => Math.max(m, t.turnIndex ?? 0), 0);
        const optimisticUserId = crypto.randomUUID();
        const optimisticAssistantId = crypto.randomUUID();

        const optimisticUserTurn: ChatTurn = {
          id: optimisticUserId,
          chatId: effectiveChatId,
          turnIndex: maxIdx + 1,
          role: "USER",
          status: "COMPLETED",
          intentType: null,
          detectedInputType: null,
          contentMarkdown: trimmed,
          contentJson: null,
          errorCode: null,
          errorMessage: null,
          modelProvider: null,
          modelName: null,
          createdAt: nowIso,
          updatedAt: nowIso,
        };

        const optimisticAssistantTurn: ChatTurn = {
          id: optimisticAssistantId,
          chatId: effectiveChatId,
          turnIndex: maxIdx + 2,
          role: "ASSISTANT",
          status: "QUEUED",
          intentType: null,
          detectedInputType: null,
          contentMarkdown: "Analyzing...",
          contentJson: null,
          errorCode: null,
          errorMessage: null,
          modelProvider: null,
          modelName: null,
          createdAt: nowIso,
          updatedAt: nowIso,
        };

        await mutateTurns(
          (cur) => ({
            items: [...(cur?.items ?? turns), optimisticUserTurn, optimisticAssistantTurn],
          }),
          { revalidate: false },
        );

        const sendRes = await sendChatMessage(effectiveChatId, {
          content: trimmed,
          researchMode,
        });

        const assistantTurnId = sendRes.assistantTurnId;
        const createdSourceIds = sendRes.createdSourceIds ?? [];

        // Poll the list endpoint; it's cheap and keeps ordering consistent.
        const deadline = Date.now() + 60_000;
        while (Date.now() < deadline) {
          const latest = await mutateTurns();
          const found = latest?.items?.find((t) => t.id === assistantTurnId);
          const status = found?.status;
          if (status === "COMPLETED" || status === "FAILED") {
            if (found && createdSourceIds.length > 0) {
              await mutateTurns(
                (cur) => ({
                  items: (cur?.items ?? []).map((t) =>
                    t.id === assistantTurnId
                      ? {
                          ...t,
                          contentJson: {
                            ...(t.contentJson ?? {}),
                            createdSourceIds,
                          },
                        }
                      : t,
                  ),
                }),
                { revalidate: false },
              );
            }
            break;
          }
          // Keep the optimistic placeholder visible until the real assistant turn exists.
          if (!found) {
            await mutateTurns(
              (cur) => ({
                items: (cur?.items ?? []).map((t) =>
                  t.id === optimisticAssistantId
                    ? { ...t, status: "RUNNING" }
                    : t,
                ),
              }),
              { revalidate: false },
            );
          } else {
            await mutateTurns(
              (cur) => ({
                items: (cur?.items ?? []).filter((t) => t.id !== optimisticAssistantId),
              }),
              { revalidate: false },
            );
          }
          await new Promise((r) => setTimeout(r, 1500));
        }
      } catch (e) {
        const msg = e instanceof ApiError ? e.message : "Could not send message.";
        await mutateTurns(
          (cur) => ({
            items: (cur?.items ?? turns).map((t) =>
              t.role === "ASSISTANT" && (t.status === "QUEUED" || t.status === "RUNNING")
                ? { ...t, status: "FAILED", contentMarkdown: msg }
                : t,
            ),
          }),
          { revalidate: false },
        );
      } finally {
        sendingRef.current = false;
      }
    },
    [mutateTurns, projectId, resolvedChatId, turns],
  );

  return {
    chat,
    turns,
    isLoading: chatsLoading || turnsLoading,
    resolvedChatId,
    onSend,
  };
}

export function SpaceChatPanel({
  projectId,
  chatId,
  onChatReady,
}: {
  projectId: string;
  chatId: string | null;
  onChatReady: (chatId: string) => void;
}) {
  const { chat, turns, isLoading, resolvedChatId, onSend } = useSpaceChat(
    projectId,
    chatId,
  );

  useEffect(() => {
    if (!chatId && resolvedChatId) onChatReady(resolvedChatId);
  }, [chatId, resolvedChatId, onChatReady]);

  const bottomRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns.length]);

  return (
    <div
      style={{
        width: "100%",
        minWidth: 0,
        background: T.white,
        display: "flex",
        flexDirection: "column",
        fontFamily: T.fontSans,
        minHeight: 0,
        height: "100%",
        flex: 1,
      }}
    >
      <style>{`
        @keyframes pulse {
          0% { transform: scale(1); opacity: 0.6; }
          50% { transform: scale(1.45); opacity: 1; }
          100% { transform: scale(1); opacity: 0.6; }
        }
      `}</style>

      {/* Header */}
      <div
        style={{
          padding: "14px 16px",
          borderBottom: `1px solid ${T.border}`,
          background: T.white,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 10,
          flexShrink: 0,
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            minWidth: 0,
            fontFamily: T.fontSans,
            fontSize: 13,
            fontWeight: 600,
            color: T.black,
          }}
        >
          <Icon.Agent />
          <span
            style={{
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {chat?.title ?? "New chat"}
          </span>
        </div>
        <button
          type="button"
          style={{
            fontSize: 12,
            color: T.gray400,
            background: "transparent",
            border: "none",
            cursor: "pointer",
            padding: 0,
            flexShrink: 0,
            fontFamily: T.fontSans,
          }}
          onClick={() => {
            // no-op for now
          }}
        >
          Clear
        </button>
      </div>

      {/* Messages */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: 16,
          minHeight: 0,
          display: "flex",
          flexDirection: "column",
          background: T.white,
        }}
      >
        {turns.length === 0 ? (
          <div
            style={{
              flex: 1,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: T.gray400,
              fontFamily: T.fontSans,
              fontSize: 13,
              textAlign: "center",
              lineHeight: 1.5,
            }}
          >
            Where should we begin
          </div>
        ) : null}

        {turns.map((t) => {
          const role = String(t.role).toUpperCase();
          const isUser = role === "USER";
          const isAssistant = role === "ASSISTANT";
          if (isUser) {
            return (
              <div
                key={t.id}
                style={{
                  display: "flex",
                  justifyContent: "flex-end",
                  marginBottom: 12,
                }}
              >
                <div
                  style={{
                    background: T.userBubble,
                    color: T.white,
                    padding: "10px 14px",
                    borderRadius: 12,
                    fontFamily: T.fontSans,
                    fontSize: 13,
                    lineHeight: 1.6,
                    marginLeft: 20,
                    maxWidth: "92%",
                    whiteSpace: "pre-wrap",
                  }}
                >
                  {t.contentMarkdown ?? ""}
                </div>
              </div>
            );
          }

          if (isAssistant) {
            const loading = t.status === "QUEUED" || t.status === "RUNNING";
            const srcIds = extractCreatedSourceIds(t);
            const text = t.contentMarkdown ?? "";
            return (
              <div key={t.id} style={{ marginBottom: 14 }}>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                    marginBottom: 8,
                  }}
                >
                  <div
                    style={{
                      width: 18,
                      height: 18,
                      background: T.black,
                      borderRadius: 5,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      flexShrink: 0,
                    }}
                  >
                    <svg
                      width="10"
                      height="10"
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
                      fontSize: 10,
                      fontWeight: 700,
                      color: T.black,
                      textTransform: "uppercase",
                      letterSpacing: "0.06em",
                      fontFamily: T.fontSans,
                    }}
                  >
                    ALPHABRIEF
                  </span>
                </div>

                <div
                  style={{
                    fontFamily: T.fontSans,
                    fontSize: 12.5,
                    color: T.black,
                    lineHeight: 1.7,
                  }}
                >
                  {loading ? (
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 6,
                        color: T.gray400,
                      }}
                    >
                      <div
                        style={{
                          width: 5,
                          height: 5,
                          borderRadius: "50%",
                          background: T.gray300,
                          animation: "pulse 1.2s infinite",
                          flexShrink: 0,
                        }}
                      />
                      {text || "Analyzing..."}
                    </div>
                  ) : (
                    <>
                      {paragraphs(text).map((p, i) => (
                        <p key={i} style={{ margin: i === 0 ? 0 : "0.85em 0 0" }}>
                          {p}
                        </p>
                      ))}
                      {srcIds.length > 0 ? (
                        <div
                          style={{
                            display: "flex",
                            gap: 6,
                            marginTop: 12,
                            flexWrap: "wrap",
                          }}
                        >
                          {srcIds.map((id, j) => (
                            <div
                              key={`${t.id}-src-${id}-${j}`}
                              style={{
                                display: "flex",
                                alignItems: "center",
                                gap: 4,
                                border: `1px solid ${T.border}`,
                                borderRadius: 5,
                                padding: "3px 8px",
                                fontSize: 10,
                                color: T.gray500,
                                fontFamily: T.fontSans,
                              }}
                            >
                              <Icon.Database
                                width={12}
                                height={12}
                                style={{ flexShrink: 0 }}
                              />
                              [{j + 1}] {id.slice(0, 8)}
                            </div>
                          ))}
                        </div>
                      ) : null}
                    </>
                  )}
                </div>
              </div>
            );
          }

          return null;
        })}
        <div ref={bottomRef} />
      </div>

      <ChatInputBar
        onSend={onSend}
        placeholder="Ask, or paste a URL to research..."
        disabled={isLoading}
        containerBackground={T.white}
      />
    </div>
  );
}

