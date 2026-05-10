import { useCallback, useEffect, useRef, useState } from "react";

import type { ApiResearchMode } from "@/components/workspace/chat-input-bar";
import type { ChatMessage } from "@/components/workspace/home-chat-view";
import { useProjects } from "@/hooks/useProjects";
import { ApiError } from "@/lib/api";
import {
  createChat,
  getChat,
  getChatTurn,
  getSourceById,
  sendChatMessage,
} from "@/lib/workspaceApi";

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

export function useHomeChat() {
  const { catchall, isLoading: projectsLoading } = useProjects();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [catchallChatId, setCatchallChatId] = useState<string | null>(null);
  const [chatTitle, setChatTitle] = useState("New chat");
  const [awaitingReply, setAwaitingReply] = useState(false);
  const sendingRef = useRef(false);

  const chatIdRef = useRef<string | null>(null);
  useEffect(() => {
    chatIdRef.current = catchallChatId;
  }, [catchallChatId]);

  const isStarted = messages.length > 0;

  const inputDisabled =
    projectsLoading || !catchall?.id || awaitingReply;

  const onSend = useCallback(
    async (text: string, researchMode: ApiResearchMode) => {
      const trimmed = text.trim();
      if (!trimmed || !catchall?.id || sendingRef.current) return;

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
        }

        const userId = crypto.randomUUID();
        assistantLocalId = crypto.randomUUID();

        setMessages((prev) => [
          ...prev,
          { id: userId, role: "user", text: trimmed },
          {
            id: assistantLocalId,
            role: "ai",
            text: "Thinking…",
            loading: true,
          },
        ]);

        const sendRes = await sendChatMessage(chatId, {
          content: trimmed,
          researchMode,
        });

        const assistantTurnId = sendRes.assistantTurnId;
        const createdIds = sendRes.createdSourceIds ?? [];

        const deadline = Date.now() + 60_000;
        let turn = await getChatTurn(assistantTurnId);
        while (
          turn.status !== "COMPLETED" &&
          turn.status !== "FAILED" &&
          Date.now() < deadline
        ) {
          await sleep(1500);
          turn = await getChatTurn(assistantTurnId);
        }

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
          const body = turn.contentMarkdown?.trim() || "_No content_";
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantLocalId
                ? {
                    ...m,
                    loading: false,
                    text: body,
                    sources: domains.length > 0 ? domains : undefined,
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
              m.id === assistantLocalId
                ? { ...m, loading: false, text: err }
                : m,
            ),
          );
        } else {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantLocalId
                ? {
                    ...m,
                    loading: false,
                    text: "Timed out waiting for a reply. Try again.",
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
    [catchall],
  );

  return {
    messages,
    isStarted,
    onSend,
    chatTitle,
    inputDisabled,
  };
}
