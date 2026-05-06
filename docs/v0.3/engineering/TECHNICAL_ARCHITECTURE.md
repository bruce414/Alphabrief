# AlphaBrief v0.3 Technical Architecture

## Version

`v0.3 First Milestone`

## Status

This architecture reflects AlphaBrief's direction:

```text
Market learning + research workspace
Ask Mode + Brief Mode
Saved research log
Daily research summary
Market journal
Learning goals
Chrome Extension-ready source ingestion
Adaptive external-source research architecture
Optimize Research for section-level depth control
```

The updated architecture treats `ResearchItem` as the central saved object, with `Brief` as a formal output subtype.

This version adds Chrome extension support as a client surface and source ingestion path. The extension should reuse the same backend source pipeline instead of becoming a separate Frankenstein limb stapled to the product later.

This version also introduces adaptive research for every external source. AlphaBrief should run a cheap scan, segment/chunk the source, estimate complexity and allowance impact, ask for intent/coverage/depth when needed, and optionally use Optimize Research to adapt depth by section. This applies to YouTube videos, finance news/articles, earnings reports, PDFs, browser-extension pages, company pages, and pasted URLs.

---

# 1. Product Goal

AlphaBrief v0.3 should prove this product loop:

```text
Ask or submit source
→ cheap scan and segment external source when needed
→ choose intent, coverage, and research depth
→ receive market-aware analysis or formal brief
→ save research
→ organize by tags/company
→ generate daily research summary
→ reflect in journal
→ progress toward learning/research goals
```

The Chrome extension strengthens this loop:

```text
Read article/video page
→ click AlphaBrief extension
→ generate source or context brief
→ save to research log
```

This is a learning and research workspace, not just another summarizer wearing a finance blazer.

---

# 2. Recommended Stack

## Frontend Web App

```text
React
TypeScript
Vite
TailwindCSS
shadcn/ui or similar component system
```

## Chrome Extension

```text
Chrome Extension Manifest V3
TypeScript
React optional for popup UI
Content script
Service worker
activeTab permission where possible
```

## Backend

```text
Python
FastAPI
SQLAlchemy 2.x
Alembic
Pydantic
PostgreSQL
```

## Background Processing

For early v0.3:

```text
FastAPI BackgroundTasks
```

For later scale:

```text
RQ + Redis
Celery + Redis
Arq + Redis
```

Do not start with distributed-worker theater unless the simple version actually hurts.

---

# 3. High-Level Architecture

```text
React/Vite Web App
        ↓
FastAPI API Layer
        ↓
Service Layer
        ↓
Repository Layer
        ↓
PostgreSQL

Chrome Extension
        ↓
Source ingestion API
        ↓
Same Source / ResearchItem / GenerationJob pipeline
```

External services should be wrapped behind client classes:

```text
AI Provider Client
Article Extraction Client
YouTube Transcript/Metadata Client
PDF Extraction Client
Company Data Client optional lightweight
Market/News API Client optional lightweight
Object Storage Client
```

---

# 4. Client Surfaces

| Client Surface | Purpose |
|---|---|
| Web App | Main product workspace: Ask, Brief, Research Log, Journal, Goals |
| Chrome Extension | User-initiated page capture and quick AlphaBrief generation from current browser page |

## Web App Core Areas

| Area | Purpose |
|---|---|
| Ask | Flexible finance/source analysis |
| Brief | Formal structured output generation |
| Research Log | Saved Ask outputs, Briefs, summaries, journal entries |
| Journal | Reflection and learning notes |
| Goals | Research/learning goals |
| Library Lite | Lightweight company lookup/filtering foundation |

## Main Composer

The main composer should support:

```text
Question input
Article URL
YouTube URL
PDF upload
Output mode switch: Ask or Brief
```

Do not make "paste full article" a primary user-facing input. That UX feels like asking users to bring their own electricity.

Output mode:

```text
ASK
BRIEF
```

---

# 5. Chrome Extension Architecture

The Chrome extension should be a lightweight source capture layer.

```text
extension/
├── manifest.json
├── popup/
│   ├── popup.html
│   └── popup.tsx
├── content/
│   └── content-script.ts
├── background/
│   └── service-worker.ts
├── lib/
│   ├── extractArticle.ts
│   ├── apiClient.ts
│   └── auth.ts
└── assets/
```

## Extension Responsibilities

```text
1. Run only after explicit user action
2. Read the current active tab when permitted
3. Extract article/video page metadata
4. Extract readable page text when available
5. Show a preview/status to the user
6. Send source payload to AlphaBrief backend
7. Open the generated ResearchItem in the web app
```

## Extension Non-Responsibilities

```text
1. No broad background crawling
2. No paywall bypass
3. No CAPTCHA bypass
4. No login-wall bypass positioning
5. No permanent local archive of article text
6. No hidden browsing-history collection
```

## Preferred Permissions

Start conservative:

```json
{
  "permissions": ["activeTab", "scripting", "storage"],
  "host_permissions": ["https://api.alphabrief.com/*"]
}
```

Avoid requesting `<all_urls>` unless the product truly needs it later. Browser permissions are where user trust goes to die if you get greedy.

---

# 6. Backend Package Structure

```text
backend/app/
├── api/
│   ├── deps.py
│   └── v1/
│       ├── auth.py
│       ├── users.py
│       ├── ask.py
│       ├── briefs.py
│       ├── sources.py
│       ├── research_items.py
│       ├── tags.py
│       ├── companies.py
│       ├── daily_summaries.py
│       ├── journal_entries.py
│       ├── learning_goals.py
│       ├── jobs.py
│       └── health.py
│
├── core/
│   ├── config.py
│   ├── security.py
│   ├── errors.py
│   └── logging.py
│
├── db/
│   ├── session.py
│   └── base.py
│
├── models/
│   ├── user.py
│   ├── research_item.py
│   ├── brief.py
│   ├── source.py
│   ├── research_item_source.py
│   ├── tag.py
│   ├── research_item_tag.py
│   ├── company.py
│   ├── research_item_company.py
│   ├── research_activity.py
│   ├── daily_research_summary.py
│   ├── journal_entry.py
│   ├── learning_goal.py
│   ├── generation_job.py
│   └── usage_event.py
│
├── schemas/
│   ├── auth.py
│   ├── ask.py
│   ├── brief.py
│   ├── source.py
│   ├── extension_source.py
│   ├── research_item.py
│   ├── tag.py
│   ├── company.py
│   ├── daily_summary.py
│   ├── journal_entry.py
│   ├── learning_goal.py
│   ├── job.py
│   └── common.py
│
├── repositories/
│   ├── user_repository.py
│   ├── research_item_repository.py
│   ├── brief_repository.py
│   ├── source_repository.py
│   ├── tag_repository.py
│   ├── company_repository.py
│   ├── activity_repository.py
│   ├── daily_summary_repository.py
│   ├── journal_repository.py
│   ├── goal_repository.py
│   ├── job_repository.py
│   └── usage_repository.py
│
├── services/
│   ├── auth_service.py
│   ├── ask_service.py
│   ├── brief_service.py
│   ├── source_service.py
│   ├── source_extraction_service.py
│   ├── browser_extension_source_service.py
│   ├── context_retrieval_service.py
│   ├── input_classification_service.py
│   ├── entity_detection_service.py
    ├── source_scan_service.py
    ├── source_segmentation_service.py
    ├── source_complexity_service.py
    ├── research_allowance_service.py
    ├── adaptive_research_service.py
│   ├── research_item_service.py
│   ├── activity_service.py
│   ├── daily_summary_service.py
│   ├── reflection_assistant_service.py
│   ├── journal_service.py
│   ├── learning_goal_service.py
│   ├── ai_output_validation_service.py
│   └── usage_tracking_service.py
│
├── clients/
│   ├── ai_provider_client.py
│   ├── article_extraction_client.py
│   ├── transcript_client.py
│   ├── pdf_extraction_client.py
│   ├── company_data_client.py
│   ├── market_news_client.py
│   └── object_storage_client.py
│
└── main.py
```

---

# 7. Core Services

## `AskService`

Owns flexible Ask Mode analysis.

Responsibilities:

- Validate question/source context
- Create ResearchItem
- Create GenerationJob
- Build prompt
- Persist output
- Create ResearchActivity
- Track usage

## `BriefService`

Owns formal Brief Mode generation.

Responsibilities:

- Resolve brief type
- Create ResearchItem + Brief
- Select template
- Generate structured sections
- Persist output

## `SourceService`

Owns source creation and normalization.

Responsibilities:

- Create URL, YouTube, PDF, and browser-extension sources
- Normalize URLs and metadata
- Track access method and status
- Coordinate extraction services
- Decide whether a source supports SOURCE_BRIEF or CONTEXT_BRIEF

## `BrowserExtensionSourceService`

Owns source payloads submitted by the Chrome extension.

Responsibilities:

- Validate extension payload
- Create `Source(source_type = BROWSER_PAGE)`
- Set `source_access_method = BROWSER_EXTENSION`
- Set `source_access_status = FULL_TEXT_EXTRACTED` or `METADATA_ONLY`
- Apply raw text retention policy
- Pass source to normal research item generation pipeline

## `ContextRetrievalService`

Responsibilities:

- Retrieve market/news/filing context when source text is unavailable or when recommended context is enabled
- Avoid presenting context as if it came from the original source
- Return structured context for prompt building



## `SourceScanService`

Runs cheap pre-analysis scans for every external source.

Responsibilities:

- Detect source length, source type, topic density, entity density, and transcript/text availability
- Decide whether segmentation is required
- Estimate source complexity and allowance impact
- Determine whether the 50% warning threshold is crossed
- Recommend research mode and completion strategy

## `SourceSegmentationService`

Splits external sources into analyzable segments.

Responsibilities:

- YouTube transcripts → timestamped segments
- Articles/news → section or paragraph-group chunks
- Earnings reports/PDFs → page and section chunks
- Browser pages → extracted readable sections
- Store `source_segments` for later analysis and reruns

## `ResearchAllowanceService`

Owns user-facing allowance percentage and internal cost/risk scoring.

Responsibilities:

- Estimate allowance impact before generation
- Track actual allowance impact after generation
- Apply cooldown/recovery rules
- Decide whether Quick/Standard/Deep are currently available
- Hide exact internal cost score from normal users

## `AdaptiveResearchService`

Coordinates segment-level analysis and Optimize Research.

Responsibilities:

- Create `analysis_runs`
- Select segment depth based on requested mode, user intent, relevance, and allowance risk
- Pause for user decision when strict mode cannot finish safely
- Downgrade lower-priority sections first when Optimize Research is enabled
- Store `analysis_segments` with requested vs actual research mode
- Produce `Analysis depth by section` summary
- Support rerunning downgraded sections later


## `DailySummaryService`

Responsibilities:

- Collect today's ResearchActivity rows
- Collect relevant ResearchItems, tags, companies, and sources
- Generate daily summary
- Persist DailyResearchSummary

## `ReflectionAssistantService`

Responsibilities:

- Use daily summary + current draft
- Return small assistive suggestions
- Avoid pretending to be the user's inner voice, because even software should have standards

## `LearningGoalService`

Responsibilities:

- Create/update goals
- Link future activities to goals if needed
- Support simple progress tracking

---

# 8. Data Flow: Ask Mode

```text
Frontend Ask Composer
   ↓ POST /api/v1/ask
FastAPI ask route
   ↓
AskService
   ↓
SourceService optional
   ↓
ContextRetrievalService optional
   ↓
AiProviderClient
   ↓
AiOutputValidationService
   ↓
ResearchItemRepository
   ↓
ActivityService + UsageTrackingService
   ↓
Frontend polls job or receives result
```

---

# 9. Data Flow: Brief Mode

```text
Frontend Brief Composer
   ↓ POST /api/v1/briefs
FastAPI briefs route
   ↓
BriefService
   ↓
SourceService optional
   ↓
ContextRetrievalService optional
   ↓
Brief template selection
   ↓
AiProviderClient
   ↓
AiOutputValidationService
   ↓
ResearchItemRepository + BriefRepository
   ↓
ActivityService + UsageTrackingService
```

---

# 10. Data Flow: Chrome Extension Page Analysis

```text
User clicks AlphaBrief extension
   ↓
Extension gets active tab after user action
   ↓
Content script extracts readable DOM text + metadata
   ↓
Popup shows source preview/status
   ↓ POST /api/v1/sources/browser-extension
BrowserExtensionSourceService
   ↓
SourceRepository creates BROWSER_PAGE source
   ↓ POST /api/v1/research-items/from-source
ResearchItemService / AskService / BriefService
   ↓
SOURCE_BRIEF if full text exists
CONTEXT_BRIEF if metadata only
   ↓
AiProviderClient generates output
   ↓
Research Log stores result
   ↓
Extension opens AlphaBrief result page
```

---

# 11. Data Flow: Daily Summary

```text
User clicks Generate Today's Summary
   ↓ POST /api/v1/daily-summaries/today/generate
DailySummaryService
   ↓
ActivityRepository fetches today's activities
   ↓
ResearchItemRepository fetches completed outputs
   ↓
AiProviderClient generates summary
   ↓
DailySummaryRepository persists result
   ↓
ResearchItem optional saved item
```


---

# 12. Data Flow: Adaptive External Source Analysis

This flow applies to all external sources: YouTube videos, finance news/articles, earnings reports, PDFs, company pages, browser-extension captures, and pasted URLs.

```text
User submits or captures external source
   ↓
SourceService creates Source
   ↓
SourceExtractionService normalizes available content or metadata
   ↓
SourceScanService runs cheap scan
   ↓
SourceSegmentationService creates source segments/chunks when needed
   ↓
SourceComplexityService estimates complexity, entity density, topic density, and allowance impact
   ↓
ResearchAllowanceService checks warning threshold
   ↓
If estimated impact > 50%:
   show pre-analysis warning
   offer Continue, Switch to Standard, Switch to Quick, or Optimize Research
   ↓
AdaptiveResearchService creates AnalysisRun
   ↓
Analyze section-by-section
   ↓
If Optimize Research is enabled:
   assign Deep/Standard/Quick by segment relevance and remaining allowance
   ↓
If strict mode cannot safely finish:
   pause and ask user to downgrade remaining sections or continue later
   ↓
Store AnalysisSegments with requested vs actual research mode
   ↓
Assemble final ResearchItem
   ↓
Show Analysis depth by section
```

## Pre-Analysis Warning Rule

```text
If estimated analysis impact > 50% of current available research allowance:
    warn before generation begins
else:
    do not interrupt the user
```

Recommended behavior:

```text
< 30%    no warning
30–50%   inline usage note only
50–80%   warning card before generation
80%+     strong warning; recommend Optimize Research or lower mode
```

## Optimize Research Rule

When enabled:

```text
Use the requested research mode as the target depth.
Use lower depth for lower-priority or lower-relevance sections when needed.
Preserve full-source completion where possible.
Always show requested vs actual depth in final output.
```


---

# 13. v0.3 API Overview

```text
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/logout

GET    /api/v1/me
PATCH  /api/v1/me

POST   /api/v1/sources
POST   /api/v1/sources/upload
POST   /api/v1/sources/browser-extension

POST   /api/v1/ask
POST   /api/v1/briefs
GET    /api/v1/briefs/{briefId}

POST   /api/v1/research-items/from-source
GET    /api/v1/research-items
GET    /api/v1/research-items/{researchItemId}
DELETE /api/v1/research-items/{researchItemId}

GET    /api/v1/jobs/{jobId}

GET    /api/v1/tags
POST   /api/v1/tags
POST   /api/v1/research-items/{researchItemId}/tags

GET    /api/v1/companies/search
GET    /api/v1/companies/{companyId}

POST   /api/v1/daily-summaries/today/generate
GET    /api/v1/daily-summaries/{date}

POST   /api/v1/journal-entries
GET    /api/v1/journal-entries
POST   /api/v1/journal-entries/reflection-assist

POST   /api/v1/learning-goals
GET    /api/v1/learning-goals
PATCH  /api/v1/learning-goals/{goalId}

GET    /api/v1/health
```

---

# 14. Database Architecture

Use PostgreSQL and Alembic.

v0.3 core tables:

```text
users
research_items
briefs
sources
research_item_sources
tags
research_item_tags
companies
research_item_companies
research_activities
daily_research_summaries
journal_entries
learning_goals
generation_jobs
source_scans
source_segments
analysis_runs
analysis_segments
user_research_allowances
usage_events
```

Key adaptive/source-related fields are added to `sources`:

```text
source_access_method
source_access_status
raw_text_retention
extraction_confidence
metadata
source_complexity
segment_count
scan_status
```

Do not add extension-specific tables until there is a real device/session management requirement.

---

# 15. Security and Compliance

Minimum v0.3 requirements:

- Validate URLs before fetching
- Block localhost/private IP URL fetching where possible
- Limit PDF/file size
- Sanitize rendered markdown
- Enforce user ownership on all records
- Never expose AI/API keys to frontend or extension
- Avoid personalized financial advice
- Add disclaimer to generated outputs
- Do not claim source certainty unless source content supports it
- Do not expose internal source quality ranking in public UI
- Do not bypass paywalls, login walls, CAPTCHAs, or technical access controls
- Do not permanently store full copyrighted article text by default
- Clearly label CONTEXT_BRIEF outputs when full source text is unavailable

## Chrome Extension Security Principles

```text
1. Use activeTab permission where possible
2. Require explicit user action before analyzing a page
3. Show preview/status before sending content to backend
4. Send only necessary page content and metadata
5. Avoid hidden background collection
6. Store extension auth token securely using Chrome storage APIs
7. Support logout/disconnect from extension
8. Keep raw text retention limited on backend
```

---

# 16. Observability

Log these events:

- Ask analysis created/completed/failed
- Brief generation created/completed/failed
- Source extraction succeeded/failed
- Browser extension ingestion succeeded/failed
- Context brief fallback triggered
- Daily summary generated/failed
- Journal entry created
- Learning goal created/completed
- AI output validation failed
- Usage/cost event created
- Source scan created/completed/failed
- High-usage warning shown/acknowledged
- Optimize Research enabled
- Segment downgraded from requested depth
- Analysis segment rerun requested

Track these metrics:

- Ask analyses per day
- Briefs per day
- Source extraction success rate
- Browser extension full-text extraction rate
- Metadata-only fallback rate
- Daily summaries generated
- Journal entries created
- Most common tags/companies
- AI cost estimate
- Generation failure rate
- Average generation latency
- Average estimated allowance impact
- Percentage of runs above 50% warning threshold
- Optimize Research usage rate
- Segment downgrade rate
- Deep-to-Standard and Deep-to-Quick downgrade counts
- Rerun rate for downgraded sections

---

# 17. Future Architecture Not in v0.3

Move these to later versions:

- Watchlist service
- Company event ingestion service
- Notification service
- Thesis tracking service
- Billing/subscription service
- Referral service
- Export/share service
- Claim-level verification service
- Research channel registry service
- Social sentiment retrieval service
- Extension device/session management service
- Browser research basket service
- Multi-source research project service

---

# 18. Implementation Slices

## Slice A: Core Research Workspace

```text
Auth
ResearchItem
Ask Mode
Brief Mode
Source handling
GenerationJob
UsageEvent
```

## Slice B: Adaptive Source Scan + Research Modes

```text
SourceScanService
SourceSegmentationService
ResearchAllowanceService
AdaptiveResearchService
Quick / Standard / Deep research mode support
Optimize Research
50% high-usage warning threshold
Analysis depth by section
```

## Slice C: URL / YouTube / Context Fallback

```text
Article URL ingestion
YouTube URL ingestion
Safe extraction
Metadata-only fallback
ContextRetrievalService
SOURCE_BRIEF vs CONTEXT_BRIEF distinction
```

## Slice D: Organization

```text
Tags
Companies
Research log filters
```

## Slice E: Learning Loop

```text
ResearchActivity
DailyResearchSummary
JournalEntry
ReflectionAssistant
LearningGoal
```

## Slice F: Chrome Extension MVP

```text
Manifest V3 extension
Popup UI
Content script extraction
POST /sources/browser-extension
Open generated ResearchItem in web app
```

Build this after the backend source ingestion pipeline works. Otherwise the extension becomes a pretty button connected to existential emptiness.

## Slice G: Polish and Validation

```text
Error handling
Markdown rendering safety
AI output validation
Basic cost dashboard/logging
Extraction status UI
Context brief transparency
```
