# AlphaBrief v0.3 API Spec

## Version

`v0.3 First Milestone — One Ask Box → Smart Source Detection → Freeform Canvas → On-demand Briefs`

## Base Path

```text
/api/v1
```

## Status

This API spec updates the previous Canvas-as-brief-source model.

AlphaBrief v0.3 now follows this product model:

```text
Projects → Threads / Agent Chat → Sources → Freeform Canvas → Memory → On-demand Brief Versions
```

Key change:

```text
The Canvas is an editable visual thinking space.
Briefs are generated on request from selected context: current thread, selected sources, project memory, selected Canvas elements/clusters, or full project context.
Canvas is optional context for briefs, not a mandatory source of truth.
```

The visible UX should use one main Ask box. Users can paste a news link or YouTube link and write “analyze this for me.” The backend detects the input type and routes the request internally. Revolutionary stuff: making software do the classification instead of making the user file paperwork.

---

# 1. API Principles

- Authenticated by default
- Frontend-workspace friendly
- Async-ready for AI generation
- Consistent error shape
- Supports low-friction asking through Catchall project
- Supports explicit project workspaces for ongoing research
- Uses one user-facing Ask endpoint / composer behavior
- Performs smart input detection for source links and user intent
- Distinguishes full source analysis from metadata/API context fallback
- Avoids primary paste-entire-article workflow
- Supports Quick, Standard, and Deep research modes for source analysis
- Supports cheap source scanning before expensive generation
- Supports Optimize Research for adaptive section-level depth control
- Treats Canvas as a freeform editable thinking workspace
- Supports Canvas text, AI blocks, images, mind-map nodes, connectors, and groups
- Tracks source provenance from Canvas elements back to chat turns and sources
- Supports explicit project memory
- Supports brief generation from selected context, not only Canvas
- Tracks usage/cost from the beginning
- Keeps finance output educational/informational, not personalized investment advice

---

# 2. Error Shape

```json
{
  "error": {
    "code": "INVALID_SOURCE_REF",
    "message": "One or more sources are unavailable.",
    "details": {}
  }
}
```

Common error codes:

```text
UNAUTHORIZED
FORBIDDEN
NOT_FOUND
VALIDATION_ERROR
INVALID_PROJECT_KIND
IMMUTABLE_CATCHALL
CHAT_ARCHIVED
INVALID_SOURCE_REF
SOURCE_NOT_READY
CANDIDATE_DISMISSED
CANVAS_NOT_FOUND
CANVAS_ELEMENT_NOT_FOUND
CANVAS_CONNECTION_NOT_FOUND
BRIEF_GENERATION_FAILED
HIGH_USAGE_WARNING_REQUIRED
CONTEXT_SELECTION_EMPTY
```

---

# 3. Auth Endpoints

## Register

```http
POST /api/v1/auth/register
```

Request:

```json
{
  "email": "user@example.com",
  "password": "password",
  "displayName": "Alex"
}
```

Response:

```json
{
  "userId": "uuid",
  "email": "user@example.com",
  "displayName": "Alex"
}
```

Registration should ensure a Catchall project and default Canvas exist for the user. For legacy users, Catchall and Canvas creation can also be handled lazily by `GET /projects` and `GET /projects/{projectId}/canvas`.

## Login

```http
POST /api/v1/auth/login
```

## Logout

```http
POST /api/v1/auth/logout
```

---

# 4. Current User Endpoints

## Get Current User

```http
GET /api/v1/me
```

Response:

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "displayName": "Alex",
  "defaultResearchScope": "RECOMMENDED_CONTEXT",
  "defaultResearchMode": "STANDARD",
  "optimizeResearchDefault": true,
  "researchAllowancePercentRemaining": 76,
  "createdAt": "2026-05-04T00:00:00Z"
}
```

## Update Current User

```http
PATCH /api/v1/me
```

Request:

```json
{
  "displayName": "Alex",
  "defaultResearchScope": "RECOMMENDED_CONTEXT",
  "defaultResearchMode": "STANDARD",
  "optimizeResearchDefault": true
}
```

---

# 5. Project Endpoints

## Create Project

```http
POST /api/v1/projects
```

Request:

```json
{
  "title": "Nvidia AI Infrastructure Thesis",
  "kind": "THESIS",
  "description": "Research workspace for tracking Nvidia, hyperscaler capex, and AI infrastructure demand."
}
```

`kind` defaults to `COVERAGE` if omitted. `CATCHALL` is rejected; only the system creates Catchall projects.

Response:

```json
{
  "id": "uuid",
  "kind": "THESIS",
  "title": "Nvidia AI Infrastructure Thesis",
  "description": "Research workspace for tracking Nvidia, hyperscaler capex, and AI infrastructure demand.",
  "archivedAt": null,
  "createdAt": "2026-05-08T00:00:00Z",
  "updatedAt": "2026-05-08T00:00:00Z"
}
```

## List Projects

```http
GET /api/v1/projects
```

Behavior:

```text
Returns Catchall first, then active user projects by updated_at desc.
If a legacy user has no Catchall, create it lazily before returning.
Each project should expose counts for chats, sources, Canvas elements, and briefs when cheap.
```

Response:

```json
{
  "items": [
    {
      "id": "uuid",
      "kind": "CATCHALL",
      "title": "My Research",
      "description": "Default workspace for unsorted chats.",
      "chatCount": 4,
      "canvasElementCount": 7,
      "sourceCount": 5,
      "briefCount": 1,
      "archivedAt": null,
      "updatedAt": "2026-05-08T00:00:00Z"
    }
  ]
}
```

## Get Project

```http
GET /api/v1/projects/{projectId}
```

Owner check required.

## Update Project

```http
PATCH /api/v1/projects/{projectId}
```

Request:

```json
{
  "title": "Updated title",
  "description": "Updated description",
  "archived": false
}
```

Catchall cannot be renamed or archived.

## Delete Project

```http
DELETE /api/v1/projects/{projectId}
```

Reject Catchall. Deleting a project cascades to chats, Canvas, candidates, memory, and brief versions.

---

# 6. Chat / Thread Endpoints

## Create Chat

```http
POST /api/v1/projects/{projectId}/chats
```

Request:

```json
{
  "title": "Nvidia moat after Blackwell"
}
```

Response:

```json
{
  "id": "uuid",
  "projectId": "uuid",
  "title": "Nvidia moat after Blackwell",
  "status": "ACTIVE",
  "lastTurnAt": null,
  "createdAt": "2026-05-08T00:00:00Z"
}
```

## List Chats in Project

```http
GET /api/v1/projects/{projectId}/chats?cursor=<cursor>&limit=30&includeArchived=0
```

Response:

```json
{
  "items": [
    {
      "id": "uuid",
      "projectId": "uuid",
      "title": "Nvidia moat after Blackwell",
      "status": "ACTIVE",
      "lastTurnAt": "2026-05-08T00:00:00Z"
    }
  ],
  "nextCursor": null
}
```

## Get Chat

```http
GET /api/v1/chats/{chatId}
```

Returns chat plus parent project summary.

## Update Chat

```http
PATCH /api/v1/chats/{chatId}
```

Request:

```json
{
  "title": "Updated chat title",
  "status": "ARCHIVED"
}
```

## Delete Chat

```http
DELETE /api/v1/chats/{chatId}
```

Hard delete. Future versions may switch to soft delete.

---

# 7. Unified Ask / Chat Turn Endpoints

## Send Message Through One Ask Box

```http
POST /api/v1/chats/{chatId}/turns
```

Request:

```json
{
  "content": "https://www.youtube.com/watch?v=example Analyze this for Nvidia's Blackwell moat.",
  "sourceIds": [],
  "researchMode": "STANDARD",
  "optimizeResearch": true,
  "clientContext": {
    "activeTab": "CANVAS",
    "selectedCanvasElementIds": []
  }
}
```

Flow:

```text
1. Owner check on chat.
2. Reject archived chats.
3. Detect input type and user intent.
4. If message contains source URLs, create or reuse Source rows.
5. Validate explicit sourceIds belong to user and are usable.
6. Create completed user turn.
7. Create queued assistant turn.
8. Attach sources to user turn.
9. Schedule assistant generation in background.
10. Return turn IDs, detected input, and source creation status.
```

Response:

```json
{
  "userTurnId": "uuid",
  "assistantTurnId": "uuid",
  "assistantStatus": "QUEUED",
  "detectedInputType": "YOUTUBE_URL",
  "detectedIntentType": "SOURCE_ANALYSIS",
  "createdSourceIds": ["uuid"],
  "requiresPreAnalysisWarning": false
}
```

### Internal intent types

```text
GENERAL_ASK
SOURCE_ANALYSIS
ARTICLE_ANALYSIS
YOUTUBE_ANALYSIS
PDF_ANALYSIS
FILING_ANALYSIS
BRIEF_GENERATION
CANVAS_ACTION
COMPARISON
```

These are internal routing labels. Do not force the user to select these as separate hard modes.

## List Chat Turns

```http
GET /api/v1/chats/{chatId}/turns
```

Response:

```json
{
  "items": [
    {
      "id": "uuid",
      "role": "USER",
      "status": "COMPLETED",
      "detectedInputType": "ARTICLE_URL",
      "intentType": "SOURCE_ANALYSIS",
      "contentMarkdown": "What does this article imply for Nvidia?",
      "createdAt": "2026-05-08T00:00:00Z"
    },
    {
      "id": "uuid",
      "role": "ASSISTANT",
      "status": "COMPLETED",
      "contentMarkdown": "### Quick answer\n...",
      "contentJson": {
        "summary": "...",
        "key_points": []
      }
    }
  ]
}
```

## Get Chat Turn

```http
GET /api/v1/chat-turns/{turnId}
```

Used for polling assistant turns.

---

# 8. Source Endpoints

## Create Source From URL

```http
POST /api/v1/sources
```

Use for article URLs, YouTube URLs, filings, and other URL-based sources submitted from the web app. The unified Ask endpoint may call this internally.

Request:

```json
{
  "sourceType": "AUTO_DETECT",
  "input": "https://example.com/market-news",
  "projectId": "uuid"
}
```

Response:

```json
{
  "sourceId": "uuid",
  "sourceType": "ARTICLE_URL",
  "sourceAccessMethod": "SERVER_FETCH",
  "sourceAccessStatus": "PENDING",
  "normalizedUrl": "https://example.com/market-news"
}
```

## Upload Source File

```http
POST /api/v1/sources/upload
```

Use for PDF files and images/screenshots.

Request:

```text
multipart/form-data
file=<pdf-or-image>
projectId=<uuid>
```

Response:

```json
{
  "sourceId": "uuid",
  "sourceType": "PDF_FILE",
  "sourceAccessMethod": "UPLOAD",
  "sourceAccessStatus": "PENDING",
  "fileName": "visa-annual-report.pdf",
  "mimeType": "application/pdf",
  "fileSizeBytes": 1048576
}
```

## List Sources

```http
GET /api/v1/projects/{projectId}/sources?limit=20&status=FULL_TEXT_EXTRACTED,METADATA_ONLY
```

Used by the Sources tab and chat SourcePicker.

Response:

```json
{
  "items": [
    {
      "id": "uuid",
      "title": "Nvidia shares rise after earnings beat",
      "publisher": "Yahoo Finance",
      "sourceType": "ARTICLE_URL",
      "sourceAccessStatus": "FULL_TEXT_EXTRACTED",
      "normalizedUrl": "https://example.com/news",
      "linkedChatTurnCount": 2,
      "linkedCanvasElementCount": 3
    }
  ]
}
```

## Create Source From Browser Extension

```http
POST /api/v1/sources/browser-extension
```

Use when the user clicks the AlphaBrief extension on a page they are viewing.

Request:

```json
{
  "projectId": "uuid",
  "url": "https://finance.yahoo.com/news/example-article",
  "canonicalUrl": "https://finance.yahoo.com/news/example-article",
  "title": "Nvidia shares rise after earnings beat",
  "publisher": "Yahoo Finance",
  "author": "Example Author",
  "publishedAt": "2026-05-05T10:00:00Z",
  "extractedText": "Readable article text extracted from the current page...",
  "extractedTextWordCount": 1426,
  "extractionConfidence": "HIGH",
  "metadata": {
    "siteName": "Yahoo Finance",
    "domExtractionVersion": "readability_v1",
    "extensionVersion": "0.1.0"
  }
}
```

Response:

```json
{
  "sourceId": "uuid",
  "sourceType": "BROWSER_PAGE",
  "sourceAccessMethod": "BROWSER_EXTENSION",
  "sourceAccessStatus": "FULL_TEXT_EXTRACTED",
  "rawTextRetention": "TEMPORARY_24H",
  "title": "Nvidia shares rise after earnings beat"
}
```

---

# 9. Source Scan Endpoints

## Run Source Scan

```http
POST /api/v1/sources/{sourceId}/scan
```

Request:

```json
{
  "analysisIntent": "MARKET_IMPACT",
  "researchMode": "DEEP",
  "coverageMode": "FULL_SOURCE"
}
```

Response:

```json
{
  "sourceScanId": "uuid",
  "sourceId": "uuid",
  "status": "COMPLETED",
  "detectedDocumentSubtype": "FINANCE_NEWS_ARTICLE",
  "estimatedSourceComplexity": "MEDIUM",
  "estimatedAllowanceImpactPercent": 34,
  "estimateConfidence": "HIGH",
  "requiresPreAnalysisWarning": false,
  "recommendedResearchMode": "STANDARD",
  "recommendedCompletionStrategy": "OPTIMIZE_RESEARCH",
  "segmentCount": 6
}
```

## List Source Segments

```http
GET /api/v1/sources/{sourceId}/segments
```

Response:

```json
{
  "items": [
    {
      "id": "uuid",
      "segmentIndex": 0,
      "title": "Earnings highlights",
      "estimatedComplexity": "MEDIUM",
      "detectedEntities": ["NVDA", "MSFT"],
      "topicTags": ["AI capex", "data center demand"]
    }
  ]
}
```

---

# 10. Candidate Element Endpoints

## List Candidates for Chat Turn

```http
GET /api/v1/chat-turns/{chatTurnId}/candidates?includeAll=0
```

Response:

```json
{
  "items": [
    {
      "id": "uuid",
      "chatTurnId": "uuid",
      "projectId": "uuid",
      "suggestedElementType": "CLAIM",
      "title": "AI capex remains the core driver",
      "contentMarkdown": "Nvidia's near-term demand depends heavily on hyperscaler AI infrastructure spending.",
      "status": "PENDING"
    }
  ]
}
```

## Promote Candidate to Canvas

```http
POST /api/v1/candidates/{candidateId}/promote
```

Request:

```json
{
  "canvasId": "uuid",
  "elementType": "CLAIM",
  "title": "AI capex remains the core driver",
  "contentMarkdown": "Edited version selected by the user.",
  "x": 640,
  "y": 280,
  "width": 320,
  "height": 180
}
```

Response:

```json
{
  "id": "uuid",
  "canvasId": "uuid",
  "projectId": "uuid",
  "elementType": "CLAIM",
  "title": "AI capex remains the core driver",
  "contentMarkdown": "Edited version selected by the user.",
  "provenanceKind": "CANDIDATE",
  "x": 640,
  "y": 280,
  "width": 320,
  "height": 180
}
```

Promotion is idempotent. If already promoted, return the existing element.

## Dismiss Candidate

```http
POST /api/v1/candidates/{candidateId}/dismiss
```

No-op if already dismissed.

---

# 11. Canvas Endpoints

## Get Project Canvas

```http
GET /api/v1/projects/{projectId}/canvas
```

Creates a default Canvas lazily if missing.

Response:

```json
{
  "id": "uuid",
  "projectId": "uuid",
  "title": "Working canvas",
  "viewportJson": {
    "x": 0,
    "y": 0,
    "zoom": 1
  },
  "updatedAt": "2026-05-08T00:00:00Z"
}
```

## List Canvas Elements

```http
GET /api/v1/canvases/{canvasId}/elements?includeArchived=0
```

Response:

```json
{
  "items": [
    {
      "id": "uuid",
      "canvasId": "uuid",
      "projectId": "uuid",
      "elementType": "CLAIM",
      "title": "Blackwell ramp is the key catalyst",
      "contentMarkdown": "The core near-term thesis depends on whether Blackwell revenue contribution ramps cleanly.",
      "x": 420,
      "y": 260,
      "width": 320,
      "height": 180,
      "zIndex": 3,
      "styleJson": {},
      "provenanceKind": "CHAT_TURN",
      "provenanceChatTurnId": "uuid",
      "provenanceSourceId": null,
      "archivedAt": null
    }
  ]
}
```

## Create Manual Canvas Element

```http
POST /api/v1/canvases/{canvasId}/elements
```

Request:

```json
{
  "elementType": "TEXT",
  "title": "My thesis note",
  "contentMarkdown": "The market may already price in near-perfect Blackwell execution.",
  "contentJson": {},
  "x": 220,
  "y": 180,
  "width": 360,
  "height": 180,
  "styleJson": {},
  "provenanceKind": "MANUAL"
}
```

Only `MANUAL` provenance is allowed through this endpoint unless using a promotion endpoint.

## Promote Chat Turn to Canvas

```http
POST /api/v1/canvases/{canvasId}/elements/from-turn
```

Request:

```json
{
  "chatTurnId": "uuid",
  "elementType": "AI_BLOCK",
  "title": "Nvidia demand summary",
  "contentMarkdown": "Edited summary text selected by the user.",
  "x": 640,
  "y": 260,
  "width": 360,
  "height": 220
}
```

If `contentMarkdown` is omitted, default to the turn markdown. The frontend should allow edit-before-promote.

## Create Canvas Element From Source

```http
POST /api/v1/canvases/{canvasId}/elements/from-source
```

Request:

```json
{
  "sourceId": "uuid",
  "elementType": "QUOTE",
  "title": "Management quote on demand",
  "contentMarkdown": "Short source quote or user-written source note.",
  "x": 520,
  "y": 500,
  "width": 320,
  "height": 160
}
```

For quote elements, keep quotes short and source-linked. Do not encourage storing full copyrighted article text as Canvas content.

## Update Canvas Element

```http
PATCH /api/v1/canvas-elements/{elementId}
```

Request:

```json
{
  "title": "Updated title",
  "contentMarkdown": "Updated user-edited element content.",
  "contentJson": {},
  "elementType": "CLAIM",
  "x": 700,
  "y": 300,
  "width": 360,
  "height": 200,
  "zIndex": 4,
  "styleJson": {},
  "archived": false
}
```

All fields are optional; omitted fields preserve existing values.

## Delete Canvas Element

```http
DELETE /api/v1/canvas-elements/{elementId}
```

Hard delete for v0.3. Future versions may prefer soft delete by default.

---

# 12. Canvas Connection Endpoints

## List Canvas Connections

```http
GET /api/v1/canvases/{canvasId}/connections
```

Response:

```json
{
  "items": [
    {
      "id": "uuid",
      "canvasId": "uuid",
      "fromElementId": "uuid",
      "toElementId": "uuid",
      "label": "supports",
      "connectionType": "SUPPORTS",
      "styleJson": {}
    }
  ]
}
```

## Create Canvas Connection

```http
POST /api/v1/canvases/{canvasId}/connections
```

Request:

```json
{
  "fromElementId": "uuid",
  "toElementId": "uuid",
  "label": "supports",
  "connectionType": "SUPPORTS",
  "styleJson": {}
}
```

## Update Canvas Connection

```http
PATCH /api/v1/canvas-connections/{connectionId}
```

Request:

```json
{
  "label": "depends on",
  "connectionType": "DEPENDS_ON",
  "styleJson": {}
}
```

## Delete Canvas Connection

```http
DELETE /api/v1/canvas-connections/{connectionId}
```

---

# 13. Project Memory Endpoints

## Get Project Memory

```http
GET /api/v1/projects/{projectId}/memory
```

Response:

```json
{
  "id": "uuid",
  "projectId": "uuid",
  "summaryMarkdown": "Current understanding of Nvidia's AI infrastructure thesis...",
  "entities": ["NVDA", "TSMC", "ASML", "AWS Trainium", "Google TPU"],
  "themes": ["AI capex", "advanced packaging", "sovereign AI"],
  "openQuestions": ["How durable is Blackwell demand into FY27?"],
  "conclusions": [],
  "updatedAt": "2026-05-08T00:00:00Z"
}
```

## Update Project Memory

```http
PATCH /api/v1/projects/{projectId}/memory
```

Request:

```json
{
  "summaryMarkdown": "Updated user-edited memory summary.",
  "entities": ["NVDA", "TSMC"],
  "themes": ["AI infrastructure"],
  "openQuestions": ["What changes the bear case?"],
  "conclusions": []
}
```

## Refresh Project Memory With AI

```http
POST /api/v1/projects/{projectId}/memory/refresh
```

Request:

```json
{
  "source": "RECENT_ACTIVITY",
  "maxActivityItems": 30
}
```

Response:

```json
{
  "memoryRefreshJobId": "uuid",
  "status": "QUEUED"
}
```

---

# 14. Brief Endpoints

## Create Brief Series

```http
POST /api/v1/projects/{projectId}/briefs
```

Request:

```json
{
  "title": "Nvidia AI Infrastructure Thesis Brief",
  "briefType": "THESIS_MEMO",
  "subject": "Nvidia AI infrastructure demand",
  "ticker": "NVDA"
}
```

Response:

```json
{
  "id": "uuid",
  "projectId": "uuid",
  "title": "Nvidia AI Infrastructure Thesis Brief",
  "briefType": "THESIS_MEMO",
  "subject": "Nvidia AI infrastructure demand",
  "ticker": "NVDA",
  "currentVersionId": null,
  "status": "ACTIVE"
}
```

## Generate Brief Version From Selected Context

```http
POST /api/v1/briefs/{briefId}/versions
```

Request:

```json
{
  "contextScope": "CUSTOM",
  "selectedChatTurnIds": ["uuid"],
  "selectedSourceIds": ["uuid", "uuid"],
  "selectedCanvasElementIds": ["uuid"],
  "includeProjectMemory": true,
  "includeCurrentThread": true,
  "briefStyle": "INVESTOR_STYLE_LEARNING",
  "includeWhatChanged": true,
  "compareToVersionId": "uuid-or-null",
  "userInstructions": "Keep it beginner-friendly but still structured."
}
```

Context scope values:

```text
CURRENT_THREAD
SELECTED_SOURCES
SELECTED_CANVAS
CANVAS_CLUSTER
PROJECT_MEMORY
FULL_PROJECT
CUSTOM
```

Default v0.3 behavior when context is omitted:

```text
Use current thread + linked sources + optional project memory.
Do not automatically use the entire Canvas unless the user selected it or requested full project context.
```

Response:

```json
{
  "briefVersionId": "uuid",
  "briefId": "uuid",
  "versionNumber": 2,
  "briefContextSnapshotId": "uuid",
  "status": "QUEUED",
  "generatedFromSummary": "current thread + 2 sources + project memory + 1 selected Canvas element"
}
```

Important rule:

```text
Brief versions must be generated from explicit selected context snapshots.
Canvas may be included, but it is not required.
```

## Get Brief

```http
GET /api/v1/briefs/{briefId}
```

Response:

```json
{
  "id": "uuid",
  "projectId": "uuid",
  "title": "Nvidia AI Infrastructure Thesis Brief",
  "briefType": "THESIS_MEMO",
  "subject": "Nvidia AI infrastructure demand",
  "ticker": "NVDA",
  "currentVersionId": "uuid",
  "versionCount": 2,
  "createdAt": "2026-05-08T00:00:00Z"
}
```

## List Project Briefs

```http
GET /api/v1/projects/{projectId}/briefs
```

## Get Brief Version

```http
GET /api/v1/brief-versions/{versionId}
```

Response:

```json
{
  "id": "uuid",
  "briefId": "uuid",
  "versionNumber": 2,
  "status": "COMPLETED",
  "contentMarkdown": "# Nvidia AI Infrastructure Thesis Brief\n...",
  "sections": {},
  "summaryOfChanges": "Added stronger TPU disconfirmation section.",
  "generatedFromSummary": "current thread + 2 sources + selected Canvas cluster",
  "disclaimer": "For educational and informational purposes only."
}
```

---

# 15. Canvas-AI Helper Endpoints

These are useful but optional for v0.3.

## Summarize Selected Canvas Area

```http
POST /api/v1/canvases/{canvasId}/summarize-selection
```

Request:

```json
{
  "selectedElementIds": ["uuid", "uuid"],
  "instruction": "Summarize this cluster into three key takeaways."
}
```

## Find Contradictions in Selected Canvas Area

```http
POST /api/v1/canvases/{canvasId}/find-contradictions
```

Request:

```json
{
  "selectedElementIds": ["uuid", "uuid"],
  "instruction": "Find claims that may conflict or need evidence."
}
```

## Generate Mind Map From Selected Context

```http
POST /api/v1/canvases/{canvasId}/generate-mindmap
```

Request:

```json
{
  "source": "CHAT_TURN",
  "chatTurnId": "uuid",
  "originX": 500,
  "originY": 300
}
```

Response:

```json
{
  "createdElementIds": ["uuid"],
  "createdConnectionIds": ["uuid"]
}
```

These helpers should create draft elements that users can edit. Do not let AI redecorate the user's Canvas like an overexcited interior designer with venture funding.

---

# 16. Activity and Usage Endpoints

## List Project Activity

```http
GET /api/v1/projects/{projectId}/activity?limit=50
```

## Get Allowance

```http
GET /api/v1/allowance
```

Response:

```json
{
  "researchAllowancePercentRemaining": 76,
  "cooldownUntil": null,
  "dailyUsedPercent": 24
}
```

---

# 17. MVP Endpoint Priority

## Build first

```text
/projects
/projects/{projectId}/chats
/chats/{chatId}/turns
/sources
/sources/upload
/projects/{projectId}/canvas
/canvases/{canvasId}/elements
/canvases/{canvasId}/connections
/chat-turns/{chatTurnId}/candidates
/projects/{projectId}/memory
/briefs/{briefId}/versions
```

## Defer if needed

```text
/canvases/{canvasId}/summarize-selection
/canvases/{canvasId}/find-contradictions
/canvases/{canvasId}/generate-mindmap
/projects/{projectId}/memory/refresh
```
