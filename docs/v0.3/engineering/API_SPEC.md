# AlphaBrief v0.3 API Spec

## Version

`v0.3 First Milestone`

## Base Path

```text
/api/v1
```

## Status

This API spec reflects AlphaBrief's v0.3 direction:

```text
Market learning + research workspace
Ask Mode + Brief Mode
Saved research log
Daily research summary
Journal
Learning goals
Chrome Extension-ready source ingestion
```

The API uses `ResearchItem` as the central saved object, with `Brief` reserved for formal structured outputs.

The Chrome extension is represented as an additional source ingestion path. It should reuse the same source, research item, and generation job pipeline rather than creating a separate parallel system, because one haunted code path is enough.

---

# 1. API Principles

- Authenticated by default
- Frontend-friendly
- Async-ready for AI generation
- Consistent error shape
- Supports both flexible Ask Mode and formal Brief Mode
- Saves outputs into a research log
- Tracks daily activity for summaries
- Keeps trading/investment advice language compliance-safe
- Supports URL, YouTube, PDF, and browser-extension source ingestion
- Clearly distinguishes full source analysis from metadata/API context fallback
- Does not expose a primary paste-entire-article workflow
- Supports Quick, Standard, and Deep research modes
- Supports cheap source scanning before expensive generation
- Supports Optimize Research for adaptive section-level depth control
- Warns users before generation when estimated allowance impact exceeds 50%
- Tracks analysis depth by section for segmented external sources

---

# 2. Auth Endpoints

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

## Login

```http
POST /api/v1/auth/login
```

## Logout

```http
POST /api/v1/auth/logout
```

---

# 3. Current User Endpoints

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
  "defaultOutputMode": "ASK",
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
  "defaultOutputMode": "ASK",
  "defaultResearchScope": "RECOMMENDED_CONTEXT",
  "defaultResearchMode": "STANDARD",
  "optimizeResearchDefault": true
}
```

---

# 4. Source Endpoints

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

Supported v0.3 source types:

```text
ARTICLE_URL
YOUTUBE_URL
PDF_FILE
BROWSER_PAGE
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

### Important UX Rule

`PASTED_TEXT` is intentionally not a primary v0.3 source type. The main product should avoid asking users to paste full articles. If manual text support is added later, treat it as an advanced fallback, not the core workflow.

---

# 5. Browser Extension Source Endpoint

## Create Source From Browser Extension

```http
POST /api/v1/sources/browser-extension
```

Use when the user clicks the AlphaBrief Chrome extension on a page they are viewing.

The extension should send page metadata and, when available, extracted readable content from the currently active page. This endpoint should not be used for background crawling.

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
    "ogTitle": "Nvidia shares rise after earnings beat",
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
  "rawTextRetention": "EPHEMERAL",
  "title": "Nvidia shares rise after earnings beat"
}
```

## Browser Extension Metadata-Only Source

If the extension cannot reliably extract readable article text, it should still submit metadata.

Request:

```json
{
  "url": "https://finance.yahoo.com/news/example-article",
  "title": "Nvidia shares rise after earnings beat",
  "publisher": "Yahoo Finance",
  "extractedText": null,
  "extractionConfidence": "LOW",
  "metadata": {
    "reason": "NO_READABLE_ARTICLE_DETECTED",
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
  "sourceAccessStatus": "METADATA_ONLY",
  "recommendedAnalysisMode": "CONTEXT_BRIEF"
}
```

---

# 6. Ask Mode Endpoints

## Create Ask Analysis

```http
POST /api/v1/ask
```

Use this for flexible finance/source analysis that does not need to become a formal brief.

Request:

```json
{
  "question": "Explain why Visa's earnings matter for payment networks.",
  "sourceIds": ["uuid"],
  "analysisIntent": "MARKET_IMPACT",
  "researchScope": "RECOMMENDED_CONTEXT",
  "researchMode": "STANDARD",
  "coverageMode": "FULL_SOURCE",
  "optimizeResearch": true,
  "saveToResearchLog": true
}
```

Response:

```json
{
  "researchItemId": "uuid",
  "jobId": "uuid",
  "status": "QUEUED",
  "itemType": "ASK_ANALYSIS"
}
```

---

# 7. Brief Mode Endpoints

## Create Brief

```http
POST /api/v1/briefs
```

Use this when the user explicitly wants a formal structured artifact.

Request:

```json
{
  "briefType": "COMPANY_RESEARCH",
  "subject": "Visa",
  "ticker": "V",
  "userQuery": "Generate a company brief for Visa.",
  "sourceIds": [],
  "researchScope": "RECOMMENDED_CONTEXT"
}
```

Supported v0.3 brief types:

```text
COMPANY_RESEARCH
EARNINGS_BREAKDOWN
SOURCE_SUMMARY
MARKET_EVENT_EXPLAINER
```

Response:

```json
{
  "researchItemId": "uuid",
  "briefId": "uuid",
  "jobId": "uuid",
  "status": "QUEUED",
  "briefType": "COMPANY_RESEARCH"
}
```

## Get Brief

```http
GET /api/v1/briefs/{briefId}
```

Response:

```json
{
  "id": "uuid",
  "researchItemId": "uuid",
  "briefType": "COMPANY_RESEARCH",
  "subject": "Visa",
  "ticker": "V",
  "sections": {
    "companyOverview": "...",
    "businessModel": "...",
    "growthDrivers": [],
    "risks": [],
    "bullCase": [],
    "bearCase": [],
    "whatToWatchNext": []
  },
  "createdAt": "2026-05-04T00:00:00Z"
}
```

---

# 8. Research Item Endpoints

## Create Research Item From Source

```http
POST /api/v1/research-items/from-source
```

Use this endpoint when a source already exists and the user wants AlphaBrief to generate either a source brief or context brief.

Request:

```json
{
  "sourceId": "uuid",
  "requestedOutputMode": "ASK",
  "analysisIntent": "MARKET_IMPACT",
  "researchScope": "RECOMMENDED_CONTEXT",
  "researchMode": "DEEP",
  "coverageMode": "FULL_SOURCE",
  "focusQuestion": "What does this source imply for Nvidia and AI chip demand?",
  "selectedSegmentIds": [],
  "selectedEntityIds": [],
  "optimizeResearch": true,
  "saveToResearchLog": true
}
```

Response:

```json
{
  "researchItemId": "uuid",
  "analysisRunId": "uuid",
  "jobId": "uuid",
  "status": "QUEUED",
  "analysisMode": "SOURCE_BRIEF",
  "researchMode": "DEEP",
  "completionStrategy": "OPTIMIZE_RESEARCH",
  "estimatedAllowanceImpactPercent": 62,
  "requiresPreAnalysisWarning": true
}
```

If the source is metadata-only, the backend should select `CONTEXT_BRIEF` unless the user specifically requests otherwise.

## List Research Items

```http
GET /api/v1/research-items
```

Query params:

```text
page
size
itemType
status
companyId
tag
fromDate
toDate
analysisMode
sourceAccessMethod
```

Response:

```json
{
  "items": [
    {
      "id": "uuid",
      "itemType": "ASK_ANALYSIS",
      "title": "Visa earnings impact analysis",
      "shortSummary": "Explains why cross-border volume matters for Visa.",
      "status": "COMPLETED",
      "analysisMode": "SOURCE_BRIEF",
      "tags": ["visa", "earnings"],
      "companies": [{ "ticker": "V", "name": "Visa Inc." }],
      "createdAt": "2026-05-04T00:00:00Z"
    }
  ],
  "page": 0,
  "size": 20,
  "totalItems": 1
}
```

## Get Research Item

```http
GET /api/v1/research-items/{researchItemId}
```

## Delete Research Item

```http
DELETE /api/v1/research-items/{researchItemId}
```

---

# 9. Job Endpoints

## Get Generation Job

```http
GET /api/v1/jobs/{jobId}
```

Response:

```json
{
  "jobId": "uuid",
  "researchItemId": "uuid",
  "jobType": "ASK_ANALYSIS",
  "status": "RUNNING",
  "currentStep": "GENERATING_OUTPUT",
  "errorCode": null,
  "errorMessage": null
}
```

---

# 10. Tag Endpoints

## List Tags

```http
GET /api/v1/tags
```

## Create Tag

```http
POST /api/v1/tags
```

Request:

```json
{
  "name": "payments",
  "color": "blue"
}
```

## Add Tags to Research Item

```http
POST /api/v1/research-items/{researchItemId}/tags
```

Request:

```json
{
  "tagNames": ["visa", "payments", "earnings"]
}
```

---

# 11. Company Endpoints

## Search Companies

```http
GET /api/v1/companies/search?q=visa
```

Response:

```json
{
  "items": [
    {
      "id": "uuid",
      "ticker": "V",
      "name": "Visa Inc.",
      "exchange": "NYSE",
      "sector": "Financial Services"
    }
  ]
}
```

## Get Company

```http
GET /api/v1/companies/{companyId}
```

For v0.3, this is a lightweight reference endpoint only. Full company library pages belong to a future version.

---

# 12. Daily Research Summary Endpoints

## Generate Today's Research Summary

```http
POST /api/v1/daily-summaries/today/generate
```

Response:

```json
{
  "summaryId": "uuid",
  "researchItemId": "uuid",
  "jobId": "uuid",
  "status": "QUEUED"
}
```

## Get Summary By Date

```http
GET /api/v1/daily-summaries/{date}
```

Example:

```http
GET /api/v1/daily-summaries/2026-05-04
```

Response:

```json
{
  "id": "uuid",
  "summaryDate": "2026-05-04",
  "topicsCovered": ["Visa earnings", "payment networks"],
  "companiesMentioned": ["Visa", "Mastercard"],
  "keyInsights": [],
  "openQuestions": [],
  "suggestedFollowups": [],
  "summaryMarkdown": "..."
}
```

---

# 13. Journal Endpoints

## Create Journal Entry

```http
POST /api/v1/journal-entries
```

Request:

```json
{
  "entryDate": "2026-05-04",
  "entryType": "LEARNING_REFLECTION",
  "title": "What I learned about Visa today",
  "body": "Today I learned that cross-border volume is important because...",
  "linkedDailySummaryId": "uuid",
  "aiAssisted": false
}
```

## Reflection Assistant

```http
POST /api/v1/journal-entries/reflection-assist
```

Request:

```json
{
  "summaryDate": "2026-05-04",
  "currentDraft": "Today I researched Visa earnings...",
  "step": "SUGGEST_LEARNING_POINTS"
}
```

Supported steps:

```text
STARTER_SUMMARY
SUGGEST_LEARNING_POINTS
SUGGEST_OPEN_QUESTIONS
DRAFT_NEXT_PARAGRAPH
```

Response:

```json
{
  "suggestion": "One important lesson from today's research is that strong earnings can still disappoint if expectations were higher.",
  "nextPrompt": "What changed your view today?"
}
```

## List Journal Entries

```http
GET /api/v1/journal-entries
```

---

# 14. Learning Goal Endpoints

## Create Learning Goal

```http
POST /api/v1/learning-goals
```

Request:

```json
{
  "title": "Understand how earnings reports affect stock prices",
  "description": "Focus on revenue, EPS, guidance, and market expectations.",
  "goalType": "LEARN_TOPIC",
  "targetDate": "2026-06-01"
}
```

## List Learning Goals

```http
GET /api/v1/learning-goals
```

## Update Learning Goal

```http
PATCH /api/v1/learning-goals/{goalId}
```

---

# 15. Research Scopes

## List Research Scopes

```http
GET /api/v1/research-scopes
```

v0.3 scopes:

```text
USER_PROVIDED_ONLY
RECOMMENDED_CONTEXT
```

Advanced scopes such as social sentiment or expanded market context can wait until the retrieval layer is more mature.

---

# 16. Common Error Shape

```json
{
  "errorCode": "SOURCE_EXTRACTION_FAILED",
  "message": "We could not extract readable content from this source.",
  "details": null,
  "timestamp": "2026-05-04T00:00:00Z"
}
```

## Error Codes

```text
INVALID_INPUT
INVALID_SOURCE_TYPE
INVALID_URL
UNSUPPORTED_FILE_TYPE
FILE_TOO_LARGE
SOURCE_EXTRACTION_FAILED
SOURCE_METADATA_ONLY
SOURCE_BLOCKED
BROWSER_EXTENSION_PAYLOAD_INVALID
QUESTION_TOO_VAGUE
GENERATION_FAILED
AI_OUTPUT_INVALID
SOURCE_SCAN_FAILED
ANALYSIS_ALLOWANCE_TOO_LOW
HIGH_USAGE_WARNING_REQUIRED
ANALYSIS_SEGMENT_NOT_FOUND
ANALYSIS_RUN_NOT_FOUND
JOB_NOT_FOUND
RESEARCH_ITEM_NOT_FOUND
BRIEF_NOT_FOUND
DAILY_SUMMARY_NOT_FOUND
UNAUTHORIZED
FORBIDDEN
NOT_FOUND
INTERNAL_ERROR
```


---

# 17. Adaptive Research / Source Scan Endpoints

These endpoints support the v0.3 external-source architecture for all external source types: article URLs, browser pages, YouTube videos, earnings reports, PDFs, and company pages.

## Run Source Scan

```http
POST /api/v1/sources/{sourceId}/scan
```

Runs a cheap pre-analysis scan before expensive generation.

Request:

```json
{
  "requestedOutputMode": "ASK",
  "analysisIntent": "MARKET_IMPACT",
  "researchMode": "DEEP",
  "coverageMode": "FULL_SOURCE",
  "focusQuestion": "What does this source imply for Nvidia and AI chips?"
}
```

Response:

```json
{
  "sourceId": "uuid",
  "scanId": "uuid",
  "sourceComplexity": "HIGH",
  "estimateConfidence": "MEDIUM",
  "estimatedAllowanceImpactPercent": 64,
  "requiresWarning": true,
  "warningLevel": "HIGH",
  "recommendedResearchMode": "STANDARD",
  "recommendedCompletionStrategy": "OPTIMIZE_RESEARCH",
  "detectedTopics": ["AI chips", "earnings", "margin pressure"],
  "detectedEntities": [
    { "name": "Nvidia", "ticker": "NVDA", "type": "COMPANY" },
    { "name": "AMD", "ticker": "AMD", "type": "COMPANY" }
  ],
  "segments": [
    {
      "segmentId": "uuid",
      "segmentIndex": 0,
      "startOffsetSeconds": 0,
      "endOffsetSeconds": 720,
      "title": "Opening market context",
      "topicSummary": "Fed policy, bond yields, and tech market setup",
      "estimatedComplexity": "MEDIUM",
      "recommendedDepth": "STANDARD"
    }
  ]
}
```

## Create Analysis Run From Source

```http
POST /api/v1/research-items/from-source
```

This existing endpoint now accepts adaptive research options.

Important request fields:

```json
{
  "sourceId": "uuid",
  "requestedOutputMode": "ASK",
  "analysisIntent": "MARKET_IMPACT",
  "researchScope": "RECOMMENDED_CONTEXT",
  "researchMode": "DEEP",
  "coverageMode": "FULL_SOURCE",
  "focusQuestion": "What does this source imply for Nvidia and AI chips?",
  "selectedSegmentIds": [],
  "selectedEntityIds": [],
  "completionStrategy": "OPTIMIZE_RESEARCH",
  "acknowledgedHighUsageWarning": true,
  "saveToResearchLog": true
}
```

Rules:

```text
- If estimatedAllowanceImpactPercent > 50, require warning acknowledgement before starting.
- If estimatedAllowanceImpactPercent > 80, recommend Optimize Research or lower research mode.
- If the source is long/complex and Deep mode is selected, run source scan before generation.
- If completionStrategy = OPTIMIZE_RESEARCH, section depth may be adapted, but actual depth must be stored and shown in the final result.
```

## Get Analysis Run

```http
GET /api/v1/analysis-runs/{analysisRunId}
```

Response:

```json
{
  "id": "uuid",
  "researchItemId": "uuid",
  "sourceId": "uuid",
  "requestedResearchMode": "DEEP",
  "completionStrategy": "OPTIMIZE_RESEARCH",
  "coverageMode": "FULL_SOURCE",
  "status": "RUNNING",
  "estimatedAllowanceImpactPercent": 64,
  "actualAllowanceImpactPercent": 38,
  "warningAcknowledged": true,
  "currentSegmentIndex": 3,
  "segmentsTotal": 8
}
```

## List Analysis Segments

```http
GET /api/v1/analysis-runs/{analysisRunId}/segments
```

Response:

```json
{
  "items": [
    {
      "id": "uuid",
      "segmentIndex": 0,
      "title": "AI chip demand and Nvidia guidance",
      "startOffsetSeconds": 720,
      "endOffsetSeconds": 1680,
      "requestedResearchMode": "DEEP",
      "actualResearchMode": "DEEP",
      "status": "COMPLETED",
      "downgradeReason": null,
      "canRerun": false
    },
    {
      "id": "uuid",
      "segmentIndex": 1,
      "title": "Oil and geopolitical risk",
      "requestedResearchMode": "DEEP",
      "actualResearchMode": "STANDARD",
      "status": "COMPLETED",
      "downgradeReason": "LOWER_RELEVANCE_TO_USER_INTENT",
      "canRerun": true
    }
  ]
}
```

## Rerun Analysis Segment

```http
POST /api/v1/analysis-segments/{segmentId}/rerun
```

Use this later when a user wants a downgraded section rerun at a higher research mode after allowance recovers.

Request:

```json
{
  "researchMode": "DEEP"
}
```

Response:

```json
{
  "analysisRunId": "uuid",
  "segmentId": "uuid",
  "jobId": "uuid",
  "status": "QUEUED"
}
```

---

# 18. Research Allowance Endpoints

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

User-facing UI should prefer percentage/labels over exact internal cost numbers.

---

# 19. Adaptive Research Values

```text
researchMode:
QUICK
STANDARD
DEEP

completionStrategy:
STRICT_REQUESTED_MODE
OPTIMIZE_RESEARCH

coverageMode:
FULL_SOURCE
SELECTED_TOPICS
SELECTED_ENTITIES
CUSTOM_QUESTION

sourceComplexity:
LOW
MEDIUM
HIGH
VERY_HIGH

warningLevel:
NONE
INLINE
HIGH
VERY_HIGH

analysisIntent:
QUICK_SUMMARY
MARKET_IMPACT
COMPANY_ANALYSIS
LEARNING_MODE
STRUCTURED_BRIEF
```

---

# 20. Future API Endpoints Not in v0.3

Move these to future versions:

```text
/watchlists
/watchlist-items
/company-events
/event-impact-notes
/notifications
/theses
/thesis-updates
/subscription
/promo-codes
/referrals
/shares
/exports
/extension/connect
/extension/devices
/research-baskets
/multi-source-projects
```

`/extension/connect` and `/extension/devices` are only needed if the Chrome extension requires a separate device/session token model. For early builds, authenticated web sessions or a simple extension token flow may be enough.
