export interface Project {
  id: string;
  kind: string;
  title: string;
  description: string | null;
  chatCount: number;
  canvasElementCount: number;
  sourceCount: number;
  briefCount: number;
  archivedAt: string | null;
  updatedAt: string;
}

export interface Chat {
  id: string;
  projectId: string;
  title: string;
  status: string;
  lastTurnAt: string | null;
  createdAt: string;
}

export interface ChatTurn {
  id: string;
  chatId: string;
  turnIndex: number;
  role: string;
  status: string;
  intentType: string | null;
  detectedInputType: string | null;
  contentMarkdown: string | null;
  contentJson: Record<string, unknown> | null;
  errorCode: string | null;
  errorMessage: string | null;
  modelProvider: string | null;
  modelName: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface SendMessageResponse {
  userTurnId: string;
  assistantTurnId: string;
  assistantStatus: string;
  detectedInputType: string | null;
  detectedIntentType: string | null;
  createdSourceIds: string[];
  requiresPreAnalysisWarning: boolean;
}

export interface Canvas {
  id: string;
  projectId: string;
  title: string;
  viewportJson: Record<string, unknown>;
  updatedAt: string;
}

export interface CanvasElement {
  id: string;
  canvasId: string;
  projectId: string;
  elementType: string;
  title: string | null;
  contentMarkdown: string | null;
  contentJson: Record<string, unknown> | null;
  x: number;
  y: number;
  width: number;
  height: number;
  zIndex: number;
  styleJson: Record<string, unknown>;
  provenanceKind: string;
  provenanceChatTurnId: string | null;
  provenanceSourceId: string | null;
  archivedAt: string | null;
}

export interface CanvasConnection {
  id: string;
  canvasId: string;
  fromElementId: string;
  toElementId: string;
  label: string | null;
  connectionType: string;
  styleJson: Record<string, unknown>;
}

export interface CandidateElement {
  id: string;
  chatTurnId: string;
  projectId: string;
  suggestedElementType: string;
  title: string | null;
  contentMarkdown: string | null;
  status: string;
}

export interface ProjectMemory {
  id: string;
  projectId: string;
  summaryMarkdown: string | null;
  entities: string[];
  themes: string[];
  openQuestions: string[];
  conclusions: string[];
  updatedAt: string;
}

export interface Source {
  id: string;
  projectId?: string;
  title: string | null;
  publisher: string | null;
  sourceType: string;
  sourceAccessStatus: string;
  normalizedUrl: string | null;
}

export interface ApiError {
  code: string;
  message: string;
  details?: unknown;
}
