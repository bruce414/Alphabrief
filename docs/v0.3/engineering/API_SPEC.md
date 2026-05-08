# AlphaBrief v0.3 API Spec

## Version

`v0.3 First Milestone — Projects → Canvas → Versioned Briefs`

## Base Path

```text
/api/v1
```

## Status

This API spec reflects AlphaBrief's updated direction:

```text
Projects → Chats / Sources → Canvas → Brief Versions
```

Chats are exploratory. The Canvas is the curated research artifact. Formal briefs are versioned snapshots generated from the Canvas.

---

# 1. API Principles

- Authenticated by default
- Frontend-workspace friendly
- Async-ready for AI generation
- Consistent error shape
- Supports low-friction asking through Catchall project
- Supports explicit project workspaces for ongoing research
- Treats Canvas as the source of truth for formal briefs
- Tracks source provenance from Canvas blocks back to chat turns and sources
- Distinguishes full source analysis from metadata/API context fallback
- Avoids primary paste-entire-article workflow
- Supports Quick, Standard, and Deep research modes for source analysis
- Supports cheap source scanning before expensive generation
- Supports Optimize Research for adaptive section-level depth control
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
CANVAS_BLOCK_NOT_FOUND
BRIEF_GENERATION_FAILED
HIGH_USAGE_WARNING_REQUIRED
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

Registration should ensure a Catchall project exists for the user. For legacy users, Catchall creation is also handled lazily by `GET /projects`.

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

Reject Catchall. Deleting a project cascades to chats, Canvas blocks, candidates, and brief versions.

---

# 6. Chat Endpoints

## Create Chat

```http
POST /api/v1/projects/{projectId}/chats
```

Request:

```json
{
  "title": "Why did Nvidia data center revenue growth decelerate?"
}
```

Response:

```json
{
  "id": "uuid",
  "projectId": "uuid",
  "title": "Why did Nvidia data center revenue growth decelerate?",
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
      "title": "New chat",
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

# 7. Source Endpoints

## Create Source From URL

```http
POST /api/v1/sources
```

Use for article URLs and YouTube URLs submitted from the web app.

Request:

```json
{
  "sourceType": "ARTICLE_URL",
  "input": "https://example.com/market-news"
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

Use for PDF files.

Request:

```text
multipart/form-data
file=<pdf>
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
GET /api/v1/sources?limit=20&status=FULL_TEXT_EXTRACTED,METADATA_ONLY
```

Used by the chat SourcePicker.

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
      "normalizedUrl": "https://example.com/news"
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

# 8. Source Scan Endpoints

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

# 9. Chat Turn Endpoints

## Send Chat Message

```http
POST /api/v1/chats/{chatId}/turns
```

Request:

```json
{
  "content": "What does this article imply for Nvidia and AI chip demand?",
  "sourceIds": ["uuid"]
}
```

Flow:

```text
1. Owner check on chat.
2. Reject archived chats.
3. Validate sources belong to user and are FULL_TEXT_EXTRACTED or METADATA_ONLY.
4. Create completed user turn.
5. Create queued assistant turn.
6. Attach sources to user turn.
7. Schedule assistant generation in background.
8. Return turn IDs for polling.
```

Response:

```json
{
  "userTurnId": "uuid",
  "assistantTurnId": "uuid",
  "assistantStatus": "QUEUED"
}
```

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

# 10. Candidate Canvas Block Endpoints

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
      "blockType": "CLAIM",
      "title": "AI capex remains the core driver",
      "contentMarkdown": "Nvidia's near-term demand depends heavily on hyperscaler AI infrastructure spending.",
      "status": "PENDING"
    }
  ]
}
```

## Promote Candidate

```http
POST /api/v1/candidates/{candidateId}/promote
```

Request:

```json
{
  "positionAfter": "uuid-or-null"
}
```

Response:

```json
{
  "id": "uuid",
  "projectId": "uuid",
  "blockType": "CLAIM",
  "title": "AI capex remains the core driver",
  "contentMarkdown": "Nvidia's near-term demand depends heavily on hyperscaler AI infrastructure spending.",
  "provenanceKind": "CHAT_TURN",
  "provenanceChatTurnId": "uuid",
  "positionIndex": "4.0000000000"
}
```

Promotion is idempotent. If already promoted, return the existing block.

## Dismiss Candidate

```http
POST /api/v1/candidates/{candidateId}/dismiss
```

No-op if already dismissed.

---

# 11. Canvas Block Endpoints

## Create Manual Canvas Block

```http
POST /api/v1/projects/{projectId}/canvas-blocks
```

Request:

```json
{
  "blockType": "NOTE",
  "title": "My thesis note",
  "contentMarkdown": "The market may already price in near-perfect Blackwell execution.",
  "contentJson": {},
  "positionAfter": null,
  "provenanceKind": "MANUAL"
}
```

Only `MANUAL` provenance is allowed through this endpoint.

## Promote Chat Turn to Canvas

```http
POST /api/v1/projects/{projectId}/canvas-blocks/from-turn
```

Request:

```json
{
  "chatTurnId": "uuid",
  "blockType": "SUMMARY",
  "title": "Nvidia demand summary",
  "contentMarkdown": "Edited summary text selected by the user.",
  "positionAfter": null
}
```

If `contentMarkdown` is omitted, default to the turn markdown. The frontend should allow edit-before-promote.

## Create Canvas Block From Source

```http
POST /api/v1/projects/{projectId}/canvas-blocks/from-source
```

Request:

```json
{
  "sourceId": "uuid",
  "blockType": "QUOTE",
  "title": "Management quote on demand",
  "contentMarkdown": "Short source quote or user-written source note.",
  "positionAfter": null
}
```

For quote blocks, keep quotes short and source-linked. Do not encourage storing full copyrighted article text as Canvas content.

## List Canvas Blocks

```http
GET /api/v1/projects/{projectId}/canvas-blocks?includeArchived=0
```

Response:

```json
{
  "items": [
    {
      "id": "uuid",
      "projectId": "uuid",
      "blockType": "CLAIM",
      "title": "Blackwell ramp is the key catalyst",
      "contentMarkdown": "The core near-term thesis depends on whether Blackwell revenue contribution ramps cleanly.",
      "positionIndex": "1.0000000000",
      "provenanceKind": "CHAT_TURN",
      "provenanceChatTurnId": "uuid",
      "provenanceSourceId": null,
      "archivedAt": null
    }
  ]
}
```

## Update Canvas Block

```http
PATCH /api/v1/canvas-blocks/{blockId}
```

Request:

```json
{
  "title": "Updated title",
  "contentMarkdown": "Updated user-edited block content.",
  "contentJson": {},
  "blockType": "CLAIM",
  "archived": false,
  "positionAfter": "uuid-or-null"
}
```

## Delete Canvas Block

```http
DELETE /api/v1/canvas-blocks/{blockId}
```

Hard delete. Future versions may prefer soft delete by default.

---

# 12. Brief Endpoints

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

## Generate Brief Version From Canvas

```http
POST /api/v1/briefs/{briefId}/versions
```

Request:

```json
{
  "selectedCanvasBlockIds": ["uuid", "uuid"],
  "briefStyle": "INVESTOR_STYLE_LEARNING",
  "includeWhatChanged": true,
  "compareToVersionId": "uuid-or-null",
  "userInstructions": "Keep it beginner-friendly but still structured."
}
```

If `selectedCanvasBlockIds` is omitted, default to all active project Canvas blocks.

Response:

```json
{
  "briefVersionId": "uuid",
  "briefId": "uuid",
  "versionNumber": 2,
  "canvasSnapshotId": "uuid",
  "status": "QUEUED"
}
```

Important rule:

```text
Brief versions must be generated from Canvas snapshots, not from raw chat transcripts.
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

## List Brief Versions

```http
GET /api/v1/briefs/{briefId}/versions
```

Response:

```json
{
  "items": [
    {
      "id": "uuid",
      "versionNumber": 2,
      "status": "COMPLETED",
      "generatedFromBlockCount": 18,
      "summaryOfChanges": "Added valuation risk and Blackwell ramp dependency.",
      "createdAt": "2026-06-20T00:00:00Z"
    }
  ]
}
```

## Get Brief Version

```http
GET /api/v1/brief-versions/{briefVersionId}
```

Response:

```json
{
  "id": "uuid",
  "briefId": "uuid",
  "versionNumber": 2,
  "status": "COMPLETED",
  "contentMarkdown": "# Nvidia AI Infrastructure Thesis Brief v2\n...",
  "sections": {
    "executiveSummary": "...",
    "coreThesis": "...",
    "evidenceBase": [],
    "risks": [],
    "openQuestions": [],
    "whatChanged": "...",
    "learningTakeaway": "...",
    "disclaimer": "For educational and informational purposes only."
  },
  "summaryOfChanges": "Added export restriction risk and valuation concern.",
  "generatedFromBlockCount": 18,
  "createdAt": "2026-06-20T00:00:00Z"
}
```

## Compare Brief Versions

```http
GET /api/v1/briefs/{briefId}/versions/compare?fromVersionId=uuid&toVersionId=uuid
```

Response:

```json
{
  "fromVersionId": "uuid",
  "toVersionId": "uuid",
  "summary": "The thesis moved from broadly bullish to conditional bullish.",
  "addedClaims": [],
  "removedClaims": [],
  "changedAssumptions": [],
  "newRisks": [],
  "confidenceChange": "MEDIUM_TO_LOW"
}
```

---

# 13. Research Activity Endpoints

## List Project Activity

```http
GET /api/v1/projects/{projectId}/activity
```

Response:

```json
{
  "items": [
    {
      "id": "uuid",
      "activityType": "PROMOTED_TO_CANVAS",
      "entityType": "CANVAS_BLOCK",
      "entityId": "uuid",
      "createdAt": "2026-05-08T00:00:00Z"
    }
  ]
}
```

---

# 14. Research Allowance Endpoints

## Get Current Allowance

```http
GET /api/v1/me/research-allowance
```

Response:

```json
{
  "allowancePercentRemaining": 76,
  "cooldownUntil": null,
  "nextRecoveryAt": "2026-05-05T16:00:00Z",
  "quickAvailable": true,
  "standardAvailable": true,
  "deepAvailable": true
}
```

User-facing UI should prefer percentages and labels over exact internal cost numbers.

---

# 15. Enum Values

```text
ProjectKind:
CATCHALL
COVERAGE
THESIS
EVENT
THEME
DECISION

ChatStatus:
ACTIVE
ARCHIVED

ChatTurnRole:
USER
ASSISTANT

ChatTurnStatus:
QUEUED
RUNNING
COMPLETED
FAILED

CanvasBlockType:
CLAIM
QUOTE
NOTE
SUMMARY
RISK
QUESTION
METRIC
BULL_CASE
BEAR_CASE

ProvenanceKind:
CHAT_TURN
SOURCE
MANUAL
CANDIDATE

CandidateStatus:
PENDING
PROMOTED
DISMISSED

BriefType:
COMPANY_RESEARCH
EARNINGS_BREAKDOWN
SOURCE_SUMMARY
MARKET_EVENT_EXPLAINER
THESIS_MEMO

BriefVersionStatus:
QUEUED
PROCESSING
COMPLETED
FAILED
ARCHIVED

ResearchMode:
QUICK
STANDARD
DEEP

CompletionStrategy:
STRICT_REQUESTED_MODE
OPTIMIZE_RESEARCH

CoverageMode:
FULL_SOURCE
SELECTED_TOPICS
SELECTED_ENTITIES
CUSTOM_QUESTION

AnalysisIntent:
QUICK_SUMMARY
MARKET_IMPACT
COMPANY_ANALYSIS
LEARNING_MODE
STRUCTURED_BRIEF
```

---

# 16. Future API Endpoints Not in v0.3

Move these to future versions:

```text
/project-memory
/project-summaries
/thread-summaries
/watchlists
/watchlist-items
/company-events
/event-impact-notes
/notifications
/theses/formal-tracking
/thesis-updates
/subscription
/promo-codes
/referrals
/shares
/exports
/extension/connect
/extension/devices
/research-baskets
/market-map
/multi-agent-research
/collaboration
```

---

# 17. MVP Demo Flow

The smallest compelling demo should be:

```text
Create/open project
→ create chat
→ attach source or ask question
→ assistant replies
→ candidate Canvas blocks appear
→ user promotes/edits blocks
→ Canvas fills up
→ user generates Brief v1 from Canvas
→ user adds more research later
→ user generates Brief v2 and sees what changed
```

This is the product wedge. Everything else is scaffolding with opinions.
