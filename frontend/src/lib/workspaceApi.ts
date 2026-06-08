import { apiFetch } from "./api";
import type {
  Canvas,
  CanvasConnection,
  CanvasElement,
  CandidateElement,
  Chat,
  ChatTurn,
  Project,
  PatchProjectOverview,
  ProjectMemory,
  ProjectMemoryRefreshResponse,
  ProjectOverview,
  ResearchDirection,
  SendMessageResponse,
  Source,
  SuggestDirectionsResponse,
} from "../types/workspace";

function parseGraphContextNodeCount(
  raw: Record<string, unknown>,
): number | null {
  const top = raw.graphContextNodeCount;
  if (typeof top === "number" && Number.isFinite(top)) {
    return top;
  }
  const cj = raw.contentJson;
  if (cj && typeof cj === "object" && !Array.isArray(cj)) {
    const nested = (cj as Record<string, unknown>).graphContextNodeCount;
    if (typeof nested === "number" && Number.isFinite(nested)) {
      return nested;
    }
  }
  return null;
}

export function normalizeChatTurn(raw: Record<string, unknown>): ChatTurn {
  return {
    ...(raw as unknown as ChatTurn),
    graphContextNodeCount: parseGraphContextNodeCount(raw),
  };
}

export function listProjects(): Promise<{ items: Project[] }> {
  return apiFetch("/projects");
}

export function createProject(body: {
  title: string;
  kind: string;
  description?: string;
}): Promise<Project> {
  return apiFetch("/projects", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getProjectCanvas(projectId: string): Promise<Canvas> {
  return apiFetch(`/projects/${encodeURIComponent(projectId)}/canvas`);
}

export function listChats(projectId: string): Promise<{ items: Chat[] }> {
  return apiFetch(`/projects/${encodeURIComponent(projectId)}/chats`);
}

export function createChat(
  projectId: string,
  body: { title: string },
): Promise<Chat> {
  return apiFetch(`/projects/${encodeURIComponent(projectId)}/chats`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getChat(chatId: string): Promise<{
  chat: Chat;
  project: { id: string; kind: string; title: string };
}> {
  return apiFetch(`/chats/${encodeURIComponent(chatId)}`);
}

export function listChatTurns(chatId: string): Promise<{ items: ChatTurn[] }> {
  return apiFetch<{ items: Record<string, unknown>[] }>(
    `/chats/${encodeURIComponent(chatId)}/turns`,
  ).then((res) => ({
    items: res.items.map(normalizeChatTurn),
  }));
}

export function getChatTurn(turnId: string): Promise<ChatTurn> {
  return apiFetch<Record<string, unknown>>(
    `/chat-turns/${encodeURIComponent(turnId)}`,
  ).then(normalizeChatTurn);
}

export function sendChatMessage(
  chatId: string,
  body: {
    content: string;
    sourceIds?: string[];
    researchMode?: string;
    optimizeResearch?: boolean;
    clientContext?: Record<string, unknown>;
  },
): Promise<SendMessageResponse> {
  return apiFetch<Record<string, unknown>>(
    `/chats/${encodeURIComponent(chatId)}/turns`,
    {
      method: "POST",
      body: JSON.stringify(body),
    },
  ).then((res) => ({
    ...(res as unknown as SendMessageResponse),
    graphContextNodeCount: parseGraphContextNodeCount(res),
  }));
}

export type AssistantTurnActionResponse = {
  assistantTurnId: string;
  assistantStatus: string;
};

export function stopChatTurnGeneration(
  turnId: string,
): Promise<AssistantTurnActionResponse> {
  return apiFetch(`/chat-turns/${encodeURIComponent(turnId)}/stop`, {
    method: "POST",
  });
}

export function regenerateAssistantTurn(
  turnId: string,
): Promise<AssistantTurnActionResponse> {
  return apiFetch(`/chat-turns/${encodeURIComponent(turnId)}/regenerate`, {
    method: "POST",
  });
}

function normalizeCandidateContentJson(
  contentJson: CandidateElement["contentJson"],
): CandidateElement["contentJson"] {
  if (!contentJson || typeof contentJson !== "object" || Array.isArray(contentJson)) {
    return contentJson;
  }
  const record = contentJson as Record<string, unknown>;
  const raw = record.proposed_edge ?? record.proposedEdge;
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
    return contentJson;
  }
  const edge = raw as Record<string, unknown>;
  const edgeType = String(edge.edge_type ?? edge.edgeType ?? "")
    .trim()
    .toLowerCase();
  const targetId = edge.target_element_id ?? edge.targetElementId;
  if (
    (edgeType !== "supports" &&
      edgeType !== "contradicts" &&
      edgeType !== "affects") ||
    typeof targetId !== "string" ||
    !targetId.trim()
  ) {
    return contentJson;
  }
  const targetTitleRaw = edge.target_title ?? edge.targetTitle;
  const targetTitle =
    typeof targetTitleRaw === "string" && targetTitleRaw.trim()
      ? targetTitleRaw.trim()
      : undefined;
  return {
    ...record,
    proposed_edge: {
      edge_type: edgeType,
      target_element_id: targetId.trim(),
      ...(targetTitle ? { target_title: targetTitle } : {}),
    },
  };
}

export function normalizeCandidateElement(
  raw: CandidateElement,
): CandidateElement {
  return {
    ...raw,
    contentJson: normalizeCandidateContentJson(raw.contentJson),
  };
}

export function listCandidates(
  chatTurnId: string,
): Promise<{ items: CandidateElement[] }> {
  const q = new URLSearchParams({ includeAll: "0" });
  return apiFetch<{ items: CandidateElement[] }>(
    `/chat-turns/${encodeURIComponent(chatTurnId)}/candidates?${q}`,
  ).then((r) => ({
    items: r.items.map(normalizeCandidateElement),
  }));
}

export function listCandidatesForTurn(
  chatTurnId: string,
): Promise<CandidateElement[]> {
  return listCandidates(chatTurnId).then((r) => r.items);
}

function promoteCandidateRaw(
  candidateId: string,
  body: Record<string, unknown>,
): Promise<CanvasElement> {
  return apiFetch(`/candidates/${encodeURIComponent(candidateId)}/promote`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function promoteCandidate(
  candidateId: string,
  body: {
    canvasId: string;
    elementType: string;
    title: string | null;
    contentMarkdown: string;
    x: number;
    y: number;
    width: number | null;
    height: number | null;
  },
): Promise<CanvasElement> {
  return promoteCandidateRaw(
    candidateId,
    body as unknown as Record<string, unknown>,
  );
}

export function dismissCandidate(candidateId: string): Promise<void> {
  return apiFetch(`/candidates/${encodeURIComponent(candidateId)}/dismiss`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export function listCanvasElements(
  canvasId: string,
): Promise<{ items: CanvasElement[] }> {
  const q = new URLSearchParams({ includeArchived: "0" });
  return apiFetch(
    `/canvases/${encodeURIComponent(canvasId)}/elements?${q}`,
  );
}

export function createManualElement(
  canvasId: string,
  body: Record<string, unknown>,
): Promise<CanvasElement> {
  return apiFetch(`/canvases/${encodeURIComponent(canvasId)}/elements`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function createElementFromTurn(
  canvasId: string,
  body: Record<string, unknown>,
): Promise<CanvasElement> {
  return apiFetch(
    `/canvases/${encodeURIComponent(canvasId)}/elements/from-turn`,
    {
      method: "POST",
      body: JSON.stringify(body),
    },
  );
}

export function createElementFromSource(
  canvasId: string,
  body: Record<string, unknown>,
): Promise<CanvasElement> {
  return apiFetch(
    `/canvases/${encodeURIComponent(canvasId)}/elements/from-source`,
    {
      method: "POST",
      body: JSON.stringify(body),
    },
  );
}

export function patchCanvasElement(
  elementId: string,
  body: Record<string, unknown>,
): Promise<CanvasElement> {
  return apiFetch(`/canvas-elements/${encodeURIComponent(elementId)}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export function deleteCanvasElement(elementId: string): Promise<void> {
  return apiFetch(`/canvas-elements/${encodeURIComponent(elementId)}`, {
    method: "DELETE",
  });
}

export function listCanvasConnections(
  canvasId: string,
): Promise<CanvasConnection[]> {
  return apiFetch<{ items: CanvasConnection[] }>(
    `/canvases/${encodeURIComponent(canvasId)}/connections`,
  ).then((r) => r.items);
}

export function createCanvasConnection(
  canvasId: string,
  body: {
    fromElementId: string;
    toElementId: string;
    label?: string | null;
    connectionType?: string;
  },
): Promise<CanvasConnection> {
  return apiFetch(`/canvases/${encodeURIComponent(canvasId)}/connections`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function patchCanvasConnection(
  connectionId: string,
  patch: {
    label?: string | null;
    connectionType?: string;
    styleJson?: Record<string, unknown>;
  },
): Promise<CanvasConnection> {
  return apiFetch(`/canvas-connections/${encodeURIComponent(connectionId)}`, {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
}

export function deleteCanvasConnection(connectionId: string): Promise<void> {
  return apiFetch(`/canvas-connections/${encodeURIComponent(connectionId)}`, {
    method: "DELETE",
  });
}

export function getProjectOverview(projectId: string): Promise<ProjectOverview> {
  return apiFetch(`/projects/${encodeURIComponent(projectId)}/overview`);
}

export function suggestResearchDirections(
  projectId: string,
  description: string,
): Promise<SuggestDirectionsResponse> {
  return apiFetch(
    `/projects/${encodeURIComponent(projectId)}/onboarding/suggest-directions`,
    {
      method: "POST",
      body: JSON.stringify({ description }),
    },
  );
}

export function applyResearchDirection(
  projectId: string,
  direction: ResearchDirection,
): Promise<ProjectOverview> {
  return apiFetch(
    `/projects/${encodeURIComponent(projectId)}/onboarding/apply`,
    {
      method: "POST",
      body: JSON.stringify({ direction }),
    },
  );
}

export function patchProjectOverview(
  projectId: string,
  patch: PatchProjectOverview,
): Promise<ProjectOverview> {
  return apiFetch(`/projects/${encodeURIComponent(projectId)}/overview`, {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
}

export function getProjectMemory(projectId: string): Promise<ProjectMemory> {
  return apiFetch(`/projects/${encodeURIComponent(projectId)}/memory`);
}

export function patchProjectMemory(
  projectId: string,
  body: Record<string, unknown>,
): Promise<ProjectMemory> {
  return apiFetch(`/projects/${encodeURIComponent(projectId)}/memory`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export function refreshProjectMemory(
  projectId: string,
): Promise<ProjectMemoryRefreshResponse> {
  return apiFetch(
    `/projects/${encodeURIComponent(projectId)}/memory/refresh`,
    {
      method: "POST",
      body: JSON.stringify({
        source: "RECENT_ACTIVITY",
        maxActivityItems: 30,
      }),
    },
  );
}

export function listProjectSources(
  projectId: string,
): Promise<{ items: Source[] }> {
  return apiFetch(`/projects/${encodeURIComponent(projectId)}/sources`);
}

export function listChatSources(
  chatId: string,
): Promise<{ items: Source[] }> {
  return apiFetch(`/chats/${encodeURIComponent(chatId)}/sources`);
}

export function getSourceById(sourceId: string): Promise<Source> {
  return apiFetch(`/sources/${encodeURIComponent(sourceId)}`);
}
