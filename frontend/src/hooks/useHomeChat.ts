import { useCallback, useEffect, useRef, useState } from "react";
import { useSWRConfig } from "swr";

import type { ApiResearchMode } from "@/components/workspace/chat-input-bar";
import type { ChatMessage } from "@/components/workspace/home-chat-view";
import { useProjects } from "@/hooks/useProjects";
import { MAX_USER_MESSAGE_CHARS } from "@/lib/chatLimits";
import { ApiError } from "@/lib/api";
import {
  createChat,
  getChat,
  getChatTurn,
  getSourceById,
  listChatTurns,
  regenerateAssistantTurn,
  sendChatMessage,
  stopChatTurnGeneration,
} from "@/lib/workspaceApi";
import { parseAssistantReplyForDisplay } from "@/lib/followUpQuestions";
import type { ChatTurn, ResearchEvent } from "@/types/workspace";

function extractEvents(turn: ChatTurn): ResearchEvent[] {
  const cj = (turn.contentJson ?? {}) as Record<string, unknown>;
  const raw = cj.events;
  if (!Array.isArray(raw)) return [];
  return raw.filter(
    (x): x is ResearchEvent =>
      x !== null && typeof x === "object" && "type" in (x as Record<string, unknown>),
  );
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function domainFromUrl(url: string | null): string {
  if (!url?.trim()) return "source";
  try {
    const u = new URL(url);
    return u.hostname.replace(/^www\./i, "");
  } catch {
    const strip = url.replace(/^https?:\/\//i, "");
    return strip.split("/")[0]?.slice(0, 48) || "source";
  }
}

export type UseHomeChatOptions = {
  /** Chat selected in the main sidebar (App shell). */
  selectedChatId: string | null;
  /** After creating a chat from the first send, sync sidebar selection. */
  onChatCreated?: (chatId: string) => void;
};

export function useHomeChat(options: UseHomeChatOptions) {
  const { selectedChatId, onChatCreated } = options;
  const { catchall, isLoading: projectsLoading } = useProjects();
  const { mutate: mutateGlobal } = useSWRConfig();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [catchallChatId, setCatchallChatId] = useState<string | null>(null);
  const [chatTitle, setChatTitle] = useState("New chat");
  const [historyLoading, setHistoryLoading] = useState(false);
  const sendingRef = useRef(false);
  const pollAbortRef = useRef(false);
  const pendingAssistantTurnIdRef = useRef<string | null>(null);
  const awaitingReplyRef = useRef(false);
  const lastResearchModeRef = useRef<ApiResearchMode>("STANDARD");

  const [awaitingReply, setAwaitingReply] = useState(false);

  useEffect(() => {
    awaitingReplyRef.current = awaitingReply;
  }, [awaitingReply]);

  const chatIdRef = useRef<string | null>(null);
  useEffect(() => {
    chatIdRef.current = catchallChatId;
  }, [catchallChatId]);

  const messagesRef = useRef(messages);
  messagesRef.current = messages;

  /** Tracks shell selection so clearing to null resets local state only when leaving a chat. */
  const prevShellChatRef = useRef<string | null | undefined>(undefined);

  useEffect(() => {
    if (selectedChatId !== null) {
      prevShellChatRef.current = selectedChatId;
      return;
    }
    const prev = prevShellChatRef.current;
    prevShellChatRef.current = null;
    if (prev !== undefined && prev !== null) {
      setMessages([]);
      setCatchallChatId(null);
      chatIdRef.current = null;
      setChatTitle("New chat");
    }
  }, [selectedChatId]);

  useEffect(() => {
    if (!selectedChatId || !catchall?.id) return;

    if (
      selectedChatId === chatIdRef.current &&
      messagesRef.current.length > 0
    ) {
      return;
    }

    let cancelled = false;
    setHistoryLoading(true);
    setChatTitle("Loading…");

    (async () => {
      try {
        const [detail, turnsRes] = await Promise.all([
          getChat(selectedChatId),
          listChatTurns(selectedChatId),
        ]);
        if (cancelled) return;

        const items = [...turnsRes.items].sort(
          (a, b) => a.turnIndex - b.turnIndex,
        );
        const mapped: ChatMessage[] = [];
        for (const t of items) {
          const role = String(t.role).toUpperCase();
          const pending =
            t.status === "QUEUED" || t.status === "RUNNING";
          if (role === "USER") {
            mapped.push({
              id: t.id,
              role: "user",
              text: t.contentMarkdown ?? "",
            });
          } else if (role === "ASSISTANT") {
            const raw = (t.contentMarkdown ?? "").trim() || "_No content_";
            const parsed = parseAssistantReplyForDisplay(
              t,
              pending ? "" : raw,
            );
            mapped.push({
              id: t.id,
              role: "ai",
              text: pending ? "" : parsed.body || "_No content_",
              loading: pending,
              events: extractEvents(t),
              mentionedEntities: pending ? undefined : parsed.mentionedEntities,
              suggestedCanvasInsights: pending
                ? undefined
                : parsed.suggestedCanvasInsights,
              followUpQuestions: pending ? undefined : parsed.followUpQuestions,
            });
          }
        }

        setCatchallChatId(selectedChatId);
        chatIdRef.current = selectedChatId;
        setChatTitle(detail.chat.title);
        setMessages(mapped);
      } catch {
        if (!cancelled) {
          setMessages([]);
          setChatTitle("Chat unavailable");
        }
      } finally {
        if (!cancelled) setHistoryLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [selectedChatId, catchall?.id]);

  const hasConversation =
    Boolean(selectedChatId) ||
    Boolean(catchallChatId) ||
    messages.length > 0;

  const isStarted = hasConversation;

  const inputDisabled =
    projectsLoading || !catchall?.id || historyLoading;

  const stopGeneration = useCallback(async () => {
    if (!awaitingReplyRef.current) return;
    const tid = pendingAssistantTurnIdRef.current;
    if (!tid) return;
    pollAbortRef.current = true;
    try {
      await stopChatTurnGeneration(tid);
    } catch {
      /* still try to refresh UI */
    }
    try {
      const t = await getChatTurn(tid);
      const err =
        t.errorMessage?.trim() ||
        t.errorCode ||
        "Generation stopped.";
      const ev = extractEvents(t);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === tid
            ? { ...m, loading: false, text: err, events: ev }
            : m,
        ),
      );
    } catch {
      /* ignore */
    } finally {
      sendingRef.current = false;
      setAwaitingReply(false);
      pendingAssistantTurnIdRef.current = null;
    }
  }, []);

  const regenerateAssistant = useCallback(
    async (turnId: string) => {
      if (!catchall?.id || sendingRef.current || awaitingReplyRef.current)
        return;
      const chatId = chatIdRef.current;
      if (!chatId) return;
      sendingRef.current = true;
      setAwaitingReply(true);
      pollAbortRef.current = false;
      pendingAssistantTurnIdRef.current = turnId;
      setMessages((prev) =>
        prev.map((m) =>
          m.id === turnId
            ? {
                ...m,
                loading: true,
                text: "",
                events: [],
                followUpQuestions: undefined,
                mentionedEntities: undefined,
                suggestedCanvasInsights: undefined,
                sources: undefined,
              }
            : m,
        ),
      );
      try {
        await regenerateAssistantTurn(turnId);
        const deadline = Date.now() + 120_000;
        let turn: ChatTurn = await getChatTurn(turnId);
        while (
          turn.status !== "COMPLETED" &&
          turn.status !== "FAILED" &&
          Date.now() < deadline
        ) {
          if (pollAbortRef.current) break;
          const events = extractEvents(turn);
          if (events.length > 0) {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === turnId ? { ...m, events } : m,
              ),
            );
          }
          await sleep(1200);
          if (pollAbortRef.current) break;
          turn = await getChatTurn(turnId);
        }
        if (pollAbortRef.current) return;
        const finalEvents = extractEvents(turn);
        if (turn.status === "COMPLETED") {
          const raw = turn.contentMarkdown?.trim() || "_No content_";
          const parsed = parseAssistantReplyForDisplay(turn, raw);
          setMessages((prev) =>
            prev.map((m) =>
              m.id === turnId
                ? {
                    ...m,
                    loading: false,
                    text: parsed.body || "_No content_",
                    events: finalEvents,
                    mentionedEntities: parsed.mentionedEntities,
                    suggestedCanvasInsights: parsed.suggestedCanvasInsights,
                    followUpQuestions: parsed.followUpQuestions,
                  }
                : m,
            ),
          );
        } else if (turn.status === "FAILED") {
          const err =
            turn.errorMessage?.trim() ||
            turn.errorCode ||
            "Something went wrong.";
          setMessages((prev) =>
            prev.map((m) =>
              m.id === turnId
                ? { ...m, loading: false, text: err, events: finalEvents }
                : m,
            ),
          );
        } else {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === turnId
                ? {
                    ...m,
                    loading: false,
                    text: "Timed out waiting for a reply. Try again.",
                    events: finalEvents,
                  }
                : m,
            ),
          );
        }
        await mutateGlobal(["chat-sources", chatId]);
      } catch (e) {
        const msg =
          e instanceof ApiError ? e.message : "Could not regenerate.";
        setMessages((prev) =>
          prev.map((m) =>
            m.id === turnId ? { ...m, loading: false, text: msg } : m,
          ),
        );
      } finally {
        sendingRef.current = false;
        setAwaitingReply(false);
        pendingAssistantTurnIdRef.current = null;
      }
    },
    [catchall?.id, mutateGlobal],
  );

  const onSend = useCallback(
    async (text: string, researchMode: ApiResearchMode) => {
      const trimmed = text.trim();
      if (!trimmed || !catchall?.id || sendingRef.current) return;
      if (trimmed.length > MAX_USER_MESSAGE_CHARS) {
        window.alert(
          `Message is too long. Maximum length is ${MAX_USER_MESSAGE_CHARS.toLocaleString()} characters.`,
        );
        return;
      }

      lastResearchModeRef.current = researchMode;
      sendingRef.current = true;
      setAwaitingReply(true);

      let assistantLocalId = "";

      try {
        let chatId = chatIdRef.current;
        if (!chatId) {
          const chat = await createChat(catchall.id, { title: "New chat" });
          chatId = chat.id;
          chatIdRef.current = chat.id;
          setCatchallChatId(chat.id);
          setChatTitle(chat.title);
          onChatCreated?.(chat.id);
        }

        const userId = crypto.randomUUID();
        assistantLocalId = crypto.randomUUID();

        setMessages((prev) => [
          ...prev,
          { id: userId, role: "user", text: trimmed },
          {
            id: assistantLocalId,
            role: "ai",
            text: "",
            loading: true,
            events: [],
          },
        ]);

        const sendRes = await sendChatMessage(chatId, {
          content: trimmed,
          researchMode,
        });

        const assistantTurnId = sendRes.assistantTurnId;
        const userTurnId = sendRes.userTurnId;
        const createdIds = sendRes.createdSourceIds ?? [];

        setMessages((prev) =>
          prev.map((m) => {
            if (m.id === assistantLocalId) {
              return { ...m, id: assistantTurnId };
            }
            if (m.id === userId) {
              return { ...m, id: userTurnId };
            }
            return m;
          }),
        );

        pollAbortRef.current = false;
        pendingAssistantTurnIdRef.current = assistantTurnId;

        const deadline = Date.now() + 120_000;
        let turn: ChatTurn = await getChatTurn(assistantTurnId);
        while (
          turn.status !== "COMPLETED" &&
          turn.status !== "FAILED" &&
          Date.now() < deadline
        ) {
          if (pollAbortRef.current) break;
          const events = extractEvents(turn);
          if (events.length > 0) {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantTurnId ? { ...m, events } : m,
              ),
            );
          }
          await sleep(1200);
          if (pollAbortRef.current) break;
          turn = await getChatTurn(assistantTurnId);
        }

        if (pollAbortRef.current) {
          sendingRef.current = false;
          setAwaitingReply(false);
          pendingAssistantTurnIdRef.current = null;
          return;
        }

        const finalEvents = extractEvents(turn);

        let domains: string[] = [];
        if (createdIds.length > 0) {
          const results = await Promise.all(
            createdIds.map((id) =>
              getSourceById(id).then((s) => domainFromUrl(s.normalizedUrl)),
            ),
          );
          domains = results;
        }

        if (turn.status === "COMPLETED") {
          const raw = turn.contentMarkdown?.trim() || "_No content_";
          const parsed = parseAssistantReplyForDisplay(turn, raw);
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantTurnId
                ? {
                    ...m,
                    loading: false,
                    text: parsed.body || "_No content_",
                    sources: domains.length > 0 ? domains : undefined,
                    events: finalEvents,
                    mentionedEntities: parsed.mentionedEntities,
                    suggestedCanvasInsights: parsed.suggestedCanvasInsights,
                    followUpQuestions: parsed.followUpQuestions,
                  }
                : m,
            ),
          );
        } else if (turn.status === "FAILED") {
          const err =
            turn.errorMessage?.trim() ||
            turn.errorCode ||
            "Something went wrong.";
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantTurnId
                ? { ...m, loading: false, text: err, events: finalEvents }
                : m,
            ),
          );
        } else {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantTurnId
                ? {
                    ...m,
                    loading: false,
                    text: "Timed out waiting for a reply. Try again.",
                    events: finalEvents,
                  }
                : m,
            ),
          );
        }

        try {
          const detail = await getChat(chatId);
          setChatTitle(detail.chat.title);
        } catch {
          /* keep existing title */
        }

        // Refresh the chats list (sidebar) and chat-sources tab so the AI-
        // generated chat title and newly researched URLs appear without a manual reload.
        if (catchall?.id) {
          await mutateGlobal(["chats", catchall.id]);
        }
        await mutateGlobal(["chat-sources", chatId]);
      } catch (e) {
        const msg =
          e instanceof ApiError ? e.message : "Could not send message.";
        if (assistantLocalId) {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantLocalId
                ? { ...m, loading: false, text: msg }
                : m,
            ),
          );
        }
      } finally {
        sendingRef.current = false;
        setAwaitingReply(false);
      }
    },
    [catchall, mutateGlobal, onChatCreated],
  );

  const onFollowUpQuestion = useCallback(
    (text: string) => {
      const trimmed = text.trim();
      if (!trimmed) return;
      void onSend(trimmed, lastResearchModeRef.current);
    },
    [onSend],
  );

  const resolvedChatId = selectedChatId ?? catchallChatId ?? null;

  return {
    messages,
    isStarted,
    onSend,
    onFollowUpQuestion,
    chatTitle,
    inputDisabled,
    awaitingReply,
    stopGeneration,
    regenerateAssistant,
    chatId: resolvedChatId,
    projectId: catchall?.id ?? null,
  };
}
