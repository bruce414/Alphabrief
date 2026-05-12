import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import remarkGfm from "remark-gfm";
import useSWR from "swr";
import { useSWRConfig } from "swr";

import {
  ChatInputBar,
  type ApiResearchMode,
} from "@/components/workspace/chat-input-bar";
import { MAX_USER_MESSAGE_CHARS } from "@/lib/chatLimits";
import { CandidateSuggestions } from "@/components/workspace/candidate-suggestions";
import { FollowUpQuestionsBlock } from "@/components/workspace/follow-up-questions";
import { Icon } from "@/components/workspace/icons";
import { InlineSourceChipsRow } from "@/components/workspace/inline-source-chips";
import {
  CanvasInsightSuggestions,
  MentionedEntitiesBlock,
} from "@/components/workspace/reply-tail-blocks";
import { ResearchProgress } from "@/components/workspace/research-progress";
import { useChats } from "@/hooks/useChats";
import { ApiError } from "@/lib/api";
import { parseAssistantReplyForDisplay } from "@/lib/followUpQuestions";
import { sortChatsByRecent } from "@/lib/chatSort";
import {
  createChat,
  getChatTurn,
  getProjectCanvas,
  listChatTurns,
  regenerateAssistantTurn,
  sendChatMessage,
  stopChatTurnGeneration,
} from "@/lib/workspaceApi";
import { T } from "@/styles/tokens";
import type { Canvas, Chat, ChatTurn, ResearchEvent } from "@/types/workspace";

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function extractEvents(turn: ChatTurn): ResearchEvent[] {
  const cj = (turn.contentJson ?? {}) as Record<string, unknown>;
  const raw = cj.events;
  if (!Array.isArray(raw)) return [];
  return raw.filter(
    (x): x is ResearchEvent =>
      x !== null && typeof x === "object" && "type" in (x as Record<string, unknown>),
  );
}

function hasPendingTurn(turns: ChatTurn[] | undefined) {
  if (!turns || turns.length === 0) return false;
  return turns.some((t) => t.status === "QUEUED" || t.status === "RUNNING");
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

type UserTurnSourceOverlay = {
  userTurnId: string;
  optimisticUserIds: string[];
  ids: string[];
};

function lastUserSourceIdsBeforeIndex(
  items: ChatTurn[],
  beforeIdx: number,
): string[] {
  for (let j = beforeIdx - 1; j >= 0; j--) {
    if (String(items[j].role).toUpperCase() === "USER") {
      return extractCreatedSourceIds(items[j]);
    }
  }
  return [];
}

function mergeUserSourceOverlay(
  items: ChatTurn[],
  overlay: UserTurnSourceOverlay | null,
): ChatTurn[] {
  if (!overlay?.ids.length) return items;
  return items.map((t) => {
    const role = String(t.role).toUpperCase();
    if (role !== "USER") return t;
    const match =
      t.id === overlay.userTurnId ||
      overlay.optimisticUserIds.includes(t.id);
    if (!match) return t;
    return {
      ...t,
      contentJson: {
        ...(t.contentJson ?? {}),
        createdSourceIds: overlay.ids,
      },
    };
  });
}

function readResearchModeForUserTurn(turn: ChatTurn): ApiResearchMode {
  const rm = (turn.contentJson as { researchMode?: string } | null)
    ?.researchMode;
  if (rm === "QUICK" || rm === "STANDARD" || rm === "DEEP") return rm;
  return "STANDARD";
}

function researchModeBeforeAssistantIndex(
  turns: ChatTurn[],
  asstIdx: number,
): ApiResearchMode {
  for (let j = asstIdx - 1; j >= 0; j--) {
    if (String(turns[j].role).toUpperCase() === "USER") {
      return readResearchModeForUserTurn(turns[j]);
    }
  }
  return "STANDARD";
}

export function useSpaceChat(projectId: string, chatId: string | null) {
  const { chats, isLoading: chatsLoading } = useChats(projectId);
  const { mutate: mutateGlobal } = useSWRConfig();

  const resolvedChatId = useMemo(() => {
    if (chatId) return chatId;
    const sorted = sortChatsByRecent(chats);
    return sorted[0]?.id ?? null;
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

  const apiTurns = turnsRes?.items ?? [];
  const [userTurnSourceOverlay, setUserTurnSourceOverlay] =
    useState<UserTurnSourceOverlay | null>(null);

  const turns = useMemo(
    () => mergeUserSourceOverlay(apiTurns, userTurnSourceOverlay),
    [apiTurns, userTurnSourceOverlay],
  );

  const [isSending, setIsSending] = useState(false);
  const sendingRef = useRef(false);
  const pollAbortRef = useRef(false);
  const pendingAssistantTurnIdRef = useRef<string | null>(null);
  const pendingChatIdRef = useRef<string | null>(null);

  const stopGeneration = useCallback(async () => {
    if (!sendingRef.current) return;
    const tid = pendingAssistantTurnIdRef.current;
    if (!tid) return;
    pollAbortRef.current = true;
    try {
      await stopChatTurnGeneration(tid);
    } catch {
      /* still refresh */
    }
    try {
      await mutateTurns();
      const cid = pendingChatIdRef.current;
      await mutateGlobal(["chats", projectId]);
      await mutateGlobal(["sources", projectId]);
      if (cid) await mutateGlobal(["chat-sources", cid]);
    } catch {
      /* ignore */
    } finally {
      sendingRef.current = false;
      setIsSending(false);
      pendingAssistantTurnIdRef.current = null;
    }
  }, [mutateGlobal, mutateTurns, projectId]);

  const regenerateAssistant = useCallback(
    async (turnId: string) => {
      if (sendingRef.current) return;
      const chatIdForMutate =
        pendingChatIdRef.current ?? resolvedChatId ?? undefined;
      if (!chatIdForMutate) return;

      sendingRef.current = true;
      setIsSending(true);
      pollAbortRef.current = false;
      pendingAssistantTurnIdRef.current = turnId;

      try {
        await regenerateAssistantTurn(turnId);
        const deadline = Date.now() + 120_000;
        let turn = await getChatTurn(turnId);
        while (
          turn.status !== "COMPLETED" &&
          turn.status !== "FAILED" &&
          Date.now() < deadline
        ) {
          if (pollAbortRef.current) break;
          await mutateTurns();
          await sleep(1200);
          if (pollAbortRef.current) break;
          turn = await getChatTurn(turnId);
        }

        if (!pollAbortRef.current) {
          await mutateTurns();
          await mutateGlobal(["chats", projectId]);
          await mutateGlobal(["sources", projectId]);
          await mutateGlobal(["chat-sources", chatIdForMutate]);
        }
      } catch (e) {
        const msg = e instanceof ApiError ? e.message : "Could not regenerate.";
        await mutateTurns(
          (cur) => ({
            items: (cur?.items ?? []).map((t) =>
              t.id === turnId
                ? {
                    ...t,
                    status: "FAILED" as const,
                    contentMarkdown: msg,
                    errorCode: null,
                    errorMessage: msg,
                  }
                : t,
            ),
          }),
          { revalidate: false },
        );
      } finally {
        sendingRef.current = false;
        setIsSending(false);
        pendingAssistantTurnIdRef.current = null;
      }
    },
    [mutateGlobal, mutateTurns, projectId, resolvedChatId],
  );

  const onSend = useCallback(
    async (text: string, researchMode: ApiResearchMode) => {
      const trimmed = text.trim();
      if (!trimmed || sendingRef.current) return;
      if (trimmed.length > MAX_USER_MESSAGE_CHARS) {
        window.alert(
          `Message is too long. Maximum length is ${MAX_USER_MESSAGE_CHARS.toLocaleString()} characters.`,
        );
        return;
      }
      sendingRef.current = true;
      setIsSending(true);

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

        pendingChatIdRef.current = effectiveChatId;

        const nowIso = new Date().toISOString();
        const maxIdx = apiTurns.reduce((m, t) => Math.max(m, t.turnIndex ?? 0), 0);
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
          contentJson: { researchMode },
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
            items: [
              ...(cur?.items ?? apiTurns),
              optimisticUserTurn,
              optimisticAssistantTurn,
            ],
          }),
          { revalidate: false },
        );

        const sendRes = await sendChatMessage(effectiveChatId, {
          content: trimmed,
          researchMode,
        });

        await mutateGlobal(["chats", projectId]);

        const assistantTurnId = sendRes.assistantTurnId;
        const createdSourceIds = sendRes.createdSourceIds ?? [];
        const serverUserTurnId = sendRes.userTurnId;

        await mutateTurns(
          (cur) => ({
            items: (cur?.items ?? []).map((t) => {
              if (t.id === optimisticUserId) return { ...t, id: serverUserTurnId };
              if (t.id === optimisticAssistantId)
                return { ...t, id: assistantTurnId };
              return t;
            }),
          }),
          { revalidate: false },
        );

        if (createdSourceIds.length > 0) {
          setUserTurnSourceOverlay({
            userTurnId: serverUserTurnId,
            optimisticUserIds: [optimisticUserId],
            ids: createdSourceIds,
          });
          await mutateTurns(
            (cur) => ({
              items: (cur?.items ?? []).map((t) =>
                t.id === serverUserTurnId
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

        pollAbortRef.current = false;
        pendingAssistantTurnIdRef.current = assistantTurnId;

        const deadline = Date.now() + 120_000;
        let turn = await getChatTurn(assistantTurnId);
        while (
          turn.status !== "COMPLETED" &&
          turn.status !== "FAILED" &&
          Date.now() < deadline
        ) {
          if (pollAbortRef.current) break;
          await mutateTurns();
          if (pollAbortRef.current) break;
          await sleep(1200);
          if (pollAbortRef.current) break;
          turn = await getChatTurn(assistantTurnId);
        }

        if (pollAbortRef.current) {
          await mutateTurns();
          return;
        }

        await mutateTurns();
        await mutateGlobal(["chats", projectId]);
        await mutateGlobal(["sources", projectId]);
        await mutateGlobal(["chat-sources", effectiveChatId]);
      } catch (e) {
        const msg = e instanceof ApiError ? e.message : "Could not send message.";
        await mutateTurns(
          (cur) => ({
            items: (cur?.items ?? apiTurns).map((t) =>
              t.role === "ASSISTANT" && (t.status === "QUEUED" || t.status === "RUNNING")
                ? { ...t, status: "FAILED", contentMarkdown: msg }
                : t,
            ),
          }),
          { revalidate: false },
        );
      } finally {
        sendingRef.current = false;
        setIsSending(false);
        pendingAssistantTurnIdRef.current = null;
      }
    },
    [mutateGlobal, mutateTurns, projectId, resolvedChatId, apiTurns],
  );

  return {
    chat,
    turns,
    isLoading: chatsLoading || turnsLoading,
    isSending,
    resolvedChatId,
    onSend,
    stopGeneration,
    regenerateAssistant,
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
  const { mutate: mutateGlobal } = useSWRConfig();
  const { data: canvas } = useSWR<Canvas>(["canvas", projectId], () =>
    getProjectCanvas(projectId),
  );
  const {
    chat,
    turns,
    isLoading,
    isSending,
    resolvedChatId,
    onSend,
    stopGeneration,
    regenerateAssistant,
  } = useSpaceChat(projectId, chatId);
  const [isCreatingChat, setIsCreatingChat] = useState(false);
  const creatingChatRef = useRef(false);

  const onNewChat = useCallback(async () => {
    if (creatingChatRef.current) return;
    creatingChatRef.current = true;
    setIsCreatingChat(true);
    try {
      const newChat = await createChat(projectId, { title: "New chat" });
      mutateGlobal(
        ["chats", projectId],
        (cur: { items?: Chat[] } | undefined) => ({
          items: [
            newChat,
            ...((cur?.items ?? []).filter((c) => c.id !== newChat.id)),
          ],
        }),
        { revalidate: false },
      );
      onChatReady(newChat.id);
    } finally {
      creatingChatRef.current = false;
      setIsCreatingChat(false);
    }
  }, [mutateGlobal, onChatReady, projectId]);

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

        .space-ai-markdown {
          font-size: 12.5px;
          line-height: 1.7;
          color: ${T.black};
          word-break: break-word;
        }
        .space-ai-markdown > *:first-child { margin-top: 0; }
        .space-ai-markdown > *:last-child { margin-bottom: 0; }
        .space-ai-markdown p {
          margin: 0 0 0.85em;
        }
        .space-ai-markdown h1,
        .space-ai-markdown h2,
        .space-ai-markdown h3,
        .space-ai-markdown h4,
        .space-ai-markdown h5,
        .space-ai-markdown h6 {
          font-weight: 700;
          color: ${T.black};
          line-height: 1.35;
          margin: 1.2em 0 0.5em;
        }
        .space-ai-markdown h1 { font-size: 18px; }
        .space-ai-markdown h2 { font-size: 16px; }
        .space-ai-markdown h3 { font-size: 14px; }
        .space-ai-markdown h4,
        .space-ai-markdown h5,
        .space-ai-markdown h6 { font-size: 13px; }
        .space-ai-markdown ul,
        .space-ai-markdown ol {
          margin: 0 0 0.85em;
          padding-left: 1.4em;
        }
        .space-ai-markdown li {
          margin: 0.2em 0;
        }
        .space-ai-markdown li > p {
          margin: 0 0 0.35em;
        }
        .space-ai-markdown li > ul,
        .space-ai-markdown li > ol {
          margin-top: 0.3em;
          margin-bottom: 0.3em;
        }
        .space-ai-markdown strong { font-weight: 700; color: ${T.black}; }
        .space-ai-markdown em { font-style: italic; }
        .space-ai-markdown a {
          color: ${T.black};
          text-decoration: underline;
          text-underline-offset: 2px;
        }
        .space-ai-markdown a:hover { color: ${T.gray600}; }
        .space-ai-markdown blockquote {
          margin: 0.6em 0 0.85em;
          padding: 0.2em 0 0.2em 12px;
          border-left: 3px solid ${T.gray200};
          color: ${T.gray600};
        }
        .space-ai-markdown code {
          font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
          font-size: 0.92em;
          background: ${T.gray100};
          border: 1px solid ${T.border};
          border-radius: 4px;
          padding: 1px 5px;
        }
        .space-ai-markdown pre {
          margin: 0.6em 0 0.85em;
          padding: 12px 14px;
          background: ${T.gray100};
          border: 1px solid ${T.border};
          border-radius: 8px;
          overflow-x: auto;
          line-height: 1.55;
        }
        .space-ai-markdown pre code {
          background: transparent;
          border: none;
          padding: 0;
          font-size: 12px;
        }
        .space-ai-markdown hr {
          border: 0;
          border-top: 1px solid ${T.border};
          margin: 1em 0;
        }
        .space-ai-markdown table {
          border-collapse: collapse;
          margin: 0.6em 0 0.85em;
          font-size: 12px;
          width: 100%;
        }
        .space-ai-markdown th,
        .space-ai-markdown td {
          border: 1px solid ${T.border};
          padding: 6px 10px;
          text-align: left;
          vertical-align: top;
        }
        .space-ai-markdown th {
          background: ${T.gray100};
          font-weight: 600;
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
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 4,
            flexShrink: 0,
          }}
        >
          <button
            type="button"
            aria-label="New chat"
            title="New chat"
            disabled={isCreatingChat || isLoading}
            onClick={() => void onNewChat()}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: 32,
              height: 32,
              padding: 0,
              color: T.gray400,
              background: "transparent",
              border: "none",
              borderRadius: 8,
              cursor:
                isCreatingChat || isLoading ? "not-allowed" : "pointer",
              opacity: isCreatingChat || isLoading ? 0.45 : 1,
            }}
          >
            <Icon.Plus size={18} />
          </button>
          <button
            type="button"
            style={{
              fontSize: 12,
              color: T.gray400,
              background: "transparent",
              border: "none",
              cursor: "pointer",
              padding: "6px 0",
              fontFamily: T.fontSans,
            }}
            onClick={() => {
              // no-op for now
            }}
          >
            Clear
          </button>
        </div>
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

        {turns.map((t, turnIdx) => {
          const role = String(t.role).toUpperCase();
          const isUser = role === "USER";
          const isAssistant = role === "ASSISTANT";
          if (isUser) {
            const userSrcIds = extractCreatedSourceIds(t);
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
                    marginLeft: 20,
                    maxWidth: "92%",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "flex-end",
                    minWidth: 0,
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
                      maxWidth: "100%",
                      whiteSpace: "pre-wrap",
                    }}
                  >
                    {t.contentMarkdown ?? ""}
                  </div>
                  <InlineSourceChipsRow
                    variant="user"
                    sourceIds={userSrcIds}
                  />
                </div>
              </div>
            );
          }

          if (isAssistant) {
            const loading = t.status === "QUEUED" || t.status === "RUNNING";
            const fromTurn = extractCreatedSourceIds(t);
            const srcIds =
              fromTurn.length > 0
                ? fromTurn
                : lastUserSourceIdsBeforeIndex(turns, turnIdx);
            const events = extractEvents(t);
            const rawMd = t.contentMarkdown ?? "";
            const parsed = parseAssistantReplyForDisplay(t, rawMd);
            const displayMd = parsed.body;
            const followUps = parsed.followUpQuestions;
            const mentionedEntities = parsed.mentionedEntities;
            const suggestedCanvasInsights = parsed.suggestedCanvasInsights;
            const modeForFollowUp = researchModeBeforeAssistantIndex(
              turns,
              turnIdx,
            );
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
                  <ResearchProgress events={events} loading={loading} />
                  {srcIds.length > 0 ? (
                    <InlineSourceChipsRow sourceIds={srcIds} />
                  ) : null}
                  {loading && events.length === 0 && !displayMd ? (
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
                      Analyzing…
                    </div>
                  ) : null}
                  {!loading && displayMd ? (
                    <>
                      <div className="space-ai-markdown">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          rehypePlugins={[rehypeSanitize]}
                        >
                          {displayMd}
                        </ReactMarkdown>
                      </div>
                      {t.status === "COMPLETED" &&
                      mentionedEntities.length > 0 ? (
                        <MentionedEntitiesBlock entities={mentionedEntities} />
                      ) : null}
                      {t.status === "COMPLETED" &&
                      suggestedCanvasInsights.length > 0 ? (
                        <CanvasInsightSuggestions
                          insights={suggestedCanvasInsights}
                          canvasId={canvas?.id}
                          disabled={isLoading || isSending}
                        />
                      ) : null}
                      {t.status === "COMPLETED" && canvas?.id ? (
                        <CandidateSuggestions
                          assistantTurnId={t.id}
                          canvasId={canvas.id}
                        />
                      ) : null}
                      {t.status === "COMPLETED" && followUps.length > 0 ? (
                        <FollowUpQuestionsBlock
                          questions={followUps}
                          onSelect={(q) => void onSend(q, modeForFollowUp)}
                          disabled={isLoading || isSending}
                        />
                      ) : null}
                    </>
                  ) : null}
                  {!loading &&
                  !displayMd &&
                  (t.status === "FAILED" ||
                    Boolean(t.errorMessage?.trim())) ? (
                    <div
                      style={{
                        color: T.gray500,
                        fontSize: 13,
                        fontFamily: T.fontSans,
                        lineHeight: 1.6,
                      }}
                    >
                      {t.errorMessage?.trim() ||
                        t.contentMarkdown?.trim() ||
                        "Something went wrong."}
                    </div>
                  ) : null}
                  {!loading &&
                  (t.status === "COMPLETED" || t.status === "FAILED") ? (
                    <div style={{ marginTop: 12 }}>
                      <button
                        type="button"
                        disabled={isLoading || isSending}
                        onClick={() => void regenerateAssistant(t.id)}
                        style={{
                          border: "none",
                          background: "transparent",
                          padding: 0,
                          cursor:
                            isLoading || isSending
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
        isGenerating={isSending}
        onStop={stopGeneration}
        placeholder="Ask, or paste a URL to research..."
        disabled={isLoading}
        containerBackground={T.white}
      />
    </div>
  );
}

