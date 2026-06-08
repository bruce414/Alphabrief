import { listCandidatesForTurn, listChatTurns } from "@/lib/workspaceApi";
import type { CandidateElement } from "@/types/workspace";

export function pendingCandidatesKey(
  projectId: string,
  chatId: string | null | undefined,
) {
  return chatId
    ? (["pendingCandidates", projectId, chatId] as const)
    : null;
}

export async function fetchPendingCandidates(
  projectId: string,
  chatId: string,
): Promise<CandidateElement[]> {
  const { items: turns } = await listChatTurns(chatId);
  const assistantTurnIds = turns
    .filter(
      (t) =>
        String(t.role).toUpperCase() === "ASSISTANT" &&
        String(t.status).toUpperCase() === "COMPLETED",
    )
    .map((t) => t.id);

  if (assistantTurnIds.length === 0) return [];

  const batches = await Promise.all(
    assistantTurnIds.map((turnId) => listCandidatesForTurn(turnId)),
  );

  const seen = new Set<string>();
  const pending: CandidateElement[] = [];
  for (const batch of batches) {
    for (const c of batch) {
      if (c.projectId !== projectId) continue;
      if (String(c.status).toUpperCase() !== "PENDING") continue;
      if (seen.has(c.id)) continue;
      seen.add(c.id);
      pending.push(c);
    }
  }

  return pending;
}
