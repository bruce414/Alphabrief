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

export interface ProjectOverviewStatus {
  totalNodes: number;
  totalSources: number;
  openQuestionsCount: number;
  unsupportedClaimsCount: number;
  updatesAvailableCount: number;
  lastCheckedAt: string | null;
}

export interface ProjectOverview {
  id: string;
  title: string;
  description: string | null;
  researchGoal: string | null;
  researchType: string | null;
  includedTopics: string[];
  excludedTopics: string[];
  targetEntities: string[];
  timeHorizon: string | null;
  createdAt: string;
  updatedAt: string;
  status: ProjectOverviewStatus;
}

export type PatchProjectOverview = Partial<
  Pick<
    ProjectOverview,
    | "researchGoal"
    | "researchType"
    | "includedTopics"
    | "excludedTopics"
    | "targetEntities"
    | "timeHorizon"
  >
>;

export interface Chat {
  id: string;
  projectId: string;
  title: string;
  status: string;
  lastTurnAt: string | null;
  createdAt: string;
}

export type ResearchEventType = "search" | "read" | "thinking" | "text";

export interface ResearchEvent {
  type: ResearchEventType;
  status?: "running" | "done";
  query?: string | null;
  url?: string | null;
  title?: string | null;
  publisher?: string | null;
  text?: string | null;
  snippet?: string | null;
}

export interface WebSearchResult {
  url: string;
  title: string | null;
  publisher: string | null;
  pageAge?: string | null;
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
  contentJson: Record<string, unknown> | null;
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

export type ProjectMemoryRefreshStatus =
  | "QUEUED"
  | "RUNNING"
  | "COMPLETED"
  | "FAILED"
  | "NO_ACTIVITY";

export interface ProjectMemoryRefreshResponse {
  memoryRefreshJobId: string;
  status: ProjectMemoryRefreshStatus;
}

export interface Source {
  id: string;
  projectId?: string | null;
  title: string | null;
  publisher: string | null;
  sourceType: string;
  sourceAccessMethod?: string;
  sourceAccessStatus: string;
  normalizedUrl: string | null;
  origin?: "user" | "ai_web_search" | string | null;
  createdAt?: string;
}

export interface ApiError {
  code: string;
  message: string;
  details?: unknown;
}

export type StickyNoteKind = "CLAIM" | "RISK" | "EVIDENCE" | "QUESTION";

export interface OnboardingStarterElement {
  elementType: "STICKY_NOTE";
  provenanceKind: "AI_ONBOARDING";
  kind: StickyNoteKind;
  title: string;
  body: string;
}

export interface ResearchDirection {
  key: string;
  title: string;
  summary: string;
  researchGoal: string;
  includedTopics: string[];
  excludedTopics: string[];
  targetEntities: string[];
  timeHorizon: string | null;
  starterElements: OnboardingStarterElement[];
}

export interface SuggestDirectionsResponse {
  suggestionId: string;
  directions: ResearchDirection[];
}
