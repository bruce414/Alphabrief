import type { Chat } from "@/types/workspace";

/**
 * Milliseconds used for ordering: prefer last activity, else creation time
 * (so brand-new chats without lastTurnAt still sort to the top among recent items).
 */
export function chatRecencyMs(chat: Chat): number {
  const last = chat.lastTurnAt ? new Date(chat.lastTurnAt).getTime() : 0;
  const created = chat.createdAt ? new Date(chat.createdAt).getTime() : 0;
  return Math.max(last, created);
}

/** Newest first (sidebar / workspace default). */
export function sortChatsByRecent(items: Chat[]): Chat[] {
  return [...items].sort((a, b) => chatRecencyMs(b) - chatRecencyMs(a));
}
