# AlphaBrief v0.3 Data Model

## Version

`v0.3 First Milestone — Projects → Agent Chat → Freeform Canvas → Sources / Memory → On-demand Briefs`

## Status

This document updates the previous Canvas-first brief-generation model.

AlphaBrief v0.3 is a **market learning and research workspace**. The latest direction is:

```text
Project
→ focused Agent chat and source analysis
→ AI suggests useful research blocks
→ user builds understanding in a freeform Canvas
→ Sources preserve evidence
→ Memory preserves project-level understanding
→ Briefs are generated on request from selected context
```

Important change:

```text
The Canvas is no longer the required source of truth for brief generation.
The Canvas is the user's evolving understanding space.
Briefs are generated on demand from chat, selected sources, project memory, and optionally selected Canvas elements or clusters.
```

This avoids turning Canvas into a rigid report-prep form. The Canvas should feel like a research desk: editable, spatial, visual, and useful for building understanding over time. Apparently users like thinking, not filling out tax forms disguised as software.

---

# 1. v0.3 Product Scope

## 1.1 In Scope

v0.3 should support:

- User accounts
- Project workspaces
- Auto-created Catchall project for low-friction asking
- Threads / chats inside projects
- One universal Ask box / Agent composer
- Smart input detection for URLs, YouTube links, PDFs, filings, browser-extension captures, and general questions
- Chat turns with attached sources
- URL, YouTube, PDF, and Chrome-extension-ready source ingestion
- Source extraction status tracking
- Metadata-only fallback for blocked/unavailable sources
- Cheap source scan and segmentation for long/complex external sources
- Quick / Standard / Deep research modes
- Optimize Research adaptive section-depth control
- Freeform Canvas as the center thinking workspace
- Canvas elements with absolute position, size, type, and provenance
- AI-generated blocks added from chat to Canvas
- User-created text notes and images on Canvas
- Simple mind-map elements: nodes, connectors, groups/frames, labels
- User editing, moving, resizing, archiving, deleting, duplicating Canvas elements
- Optional source references on Canvas elements
- Project Memory as explicit accumulated understanding
- On-demand brief generation from selected context, not necessarily Canvas
- Saved brief versions and “what changed” comparison when relevant
- Tags and lightweight company references
- Research activity tracking
- Basic usage/cost tracking
- Compliance-safe language: educational/informational, not personalized investment advice

## 1.2 Extension-Ready Scope

The Chrome extension should remain represented in v0.3 architecture and data model, but the extension client can ship after the web workspace is stable.

Recommended framing:

```text
v0.3 backend should be extension-compatible.
The Chrome extension client can be built after source ingestion + chat attachment works.
```

## 1.3 Out of Scope for v0.3

Move these to later versions:

- Full autonomous multi-agent research planner
- Fully AI-generated market graph across all projects
- Proactive monitoring
- Watchlist alerts
- Push/email notifications
- Portfolio-aware analysis
- Broker/trading integrations
- Paid subscriptions and billing
- Promo codes/referrals
- Public sharing
- PDF/DOCX exports
- Full claim/citation verification tables
- Cross-project Canvas element reuse
- Complex collaborative whiteboarding
- Real-time multiplayer Canvas
- Broad web crawling
- Paywall/login/CAPTCHA bypass
- Permanent storage of full copyrighted article text by default

---

# 2. Core Design Principles

1. `Project` is the top-level organizing container.
2. `Chat` / `Thread` is an exploration session inside a project.
3. The visible product should use one main Ask box, not separate hard modes for news/video/PDF.
4. Input type detection happens internally after the user asks or pastes a source.
5. `Source` stores user-submitted or user-authorized source material and metadata.
6. `Canvas` is the freeform visual workspace in the middle of the UI.
7. `CanvasElement` is the atomic visual object on the Canvas.
8. Canvas elements must be editable, movable, resizable, and optionally source-linked.
9. Canvas is for understanding-building, not a mandatory brief-generation input form.
10. `ProjectMemory` stores explicit project-level understanding, summaries, entities, themes, and open questions.
11. `Brief` is a logical brief series inside a project.
12. `BriefVersion` is a point-in-time generated output from a selected `BriefContextSnapshot`.
13. Brief generation can use current chat, selected sources, project memory, selected Canvas elements, or full project context.
14. Direct user questions belong in chat turns, not sources.
15. Long/complex sources should be scanned, segmented, and analyzed with depth controls.
16. The Catchall project exists to remove friction, but the product should nudge users toward real projects when research starts accumulating.
17. Preserve provenance from Canvas elements back to chat turns and/or sources when applicable.
18. Use JSONB for flexible AI output and Canvas content in v0.3.
19. Keep compliance-safe language: educational and informational, not personalized financial advice.
20. Store AI usage/cost data from the beginning, but keep billing out of v0.3.
21. Store generated analysis and source metadata by default; avoid permanent raw full-text storage without a retention policy.
22. Final segmented-source outputs should show analysis depth by section.
23. Project memory should be explicit and controlled. Bad hidden memory is worse than no memory.

---

# 3. Entity Relationship Overview

```text
User
 ├── Project
 │    ├── Chat
 │    │    ├── ChatTurn
 │    │    └── ChatTurnSource
 │    │         └── Source
 │    ├── Canvas
 │    │    ├── CanvasElement
 │    │    └── CanvasConnection
 │    ├── CandidateElement
 │    ├── ProjectMemory
 │    ├── Brief
 │    │    └── BriefVersion
 │    │         └── BriefContextSnapshot
 │    ├── ProjectTag optional
 │    └── ProjectCompany optional
 │
 ├── Source
 ├── SourceScan
 ├── SourceSegment
 ├── Tag
 ├── Company
 ├── ResearchActivity
 ├── DailyResearchSummary optional later in v0.3
 ├── JournalEntry optional later in v0.3
 ├── LearningGoal optional later in v0.3
 └── UsageEvent
```

`ResearchItem` should remain deprecated for the new build or kept only as a backward-compatibility/search-log wrapper. The clearer v0.3 nouns are: `Project`, `Chat`, `Source`, `Canvas`, `CanvasElement`, `ProjectMemory`, `Brief`, and `BriefVersion`.

---

# 4. Tables

## 4.1 `users`

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| email | VARCHAR(255) | Unique, required |
| password_hash | VARCHAR(255) | Required unless OAuth-only later |
| display_name | VARCHAR(120) | Optional |
| role | VARCHAR(50) | USER, ADMIN |
| default_research_scope | VARCHAR(50) | USER_PROVIDED_ONLY, RECOMMENDED_CONTEXT |
| default_research_mode | VARCHAR(50) | QUICK, STANDARD, DEEP; default STANDARD |
| optimize_research_default | BOOLEAN | Default true for long/complex sources |
| created_at | TIMESTAMPTZ | Required |
| updated_at | TIMESTAMPTZ | Required |

---

## 4.2 `projects`

Top-level workspace container.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users, indexed |
| kind | VARCHAR(32) | CATCHALL, COVERAGE, THESIS, EVENT, THEME, DECISION |
| title | TEXT | Required |
| description | TEXT | Nullable |
| archived_at | TIMESTAMPTZ | Nullable |
| metadata | JSONB | Default `{}` |
| created_at | TIMESTAMPTZ | Required |
| updated_at | TIMESTAMPTZ | Required |

### Values

```text
CATCHALL  # auto-created default workspace for unsorted chats
COVERAGE  # tracking a company/sector
THESIS    # building an investment view
EVENT     # earnings season, Fed meeting, product launch, regulation
THEME     # cross-cutting topic such as AI capex, GLP-1s, tariffs
DECISION  # specific compare/decision research; not personalized advice
```

### Constraints

```sql
CREATE UNIQUE INDEX uq_projects_one_catchall_per_user
ON projects(user_id)
WHERE kind = 'CATCHALL';
```

---

## 4.3 `chats`

Focused exploration sessions inside a project.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| project_id | UUID | FK to projects ON DELETE CASCADE, indexed |
| user_id | UUID | FK to users, denormalized |
| title | TEXT | Default `New chat` |
| status | VARCHAR(32) | ACTIVE, ARCHIVED |
| last_turn_at | TIMESTAMPTZ | Nullable |
| metadata | JSONB | Default `{}` |
| created_at | TIMESTAMPTZ | Required |
| updated_at | TIMESTAMPTZ | Required |

### Indexes

```sql
CREATE INDEX idx_chats_project_order
ON chats(project_id, last_turn_at DESC NULLS LAST, created_at DESC);
```

---

## 4.4 `chat_turns`

Individual user/assistant turns.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| chat_id | UUID | FK to chats ON DELETE CASCADE, indexed |
| user_id | UUID | FK to users, denormalized |
| turn_index | INT | 0-based ordering within chat |
| role | VARCHAR(16) | USER, ASSISTANT |
| status | VARCHAR(16) | QUEUED, RUNNING, COMPLETED, FAILED |
| intent_type | VARCHAR(50) | GENERAL_ASK, SOURCE_ANALYSIS, BRIEF_GENERATION, CANVAS_ACTION, COMPARISON |
| detected_input_type | VARCHAR(50) | QUESTION, ARTICLE_URL, YOUTUBE_URL, PDF_FILE, BROWSER_PAGE, MIXED |
| content_markdown | TEXT | User text or assistant response |
| content_json | JSONB | Structured assistant output |
| error_code | VARCHAR(64) | Nullable |
| error_message | TEXT | Nullable |
| input_tokens | INT | Nullable |
| output_tokens | INT | Nullable |
| cache_read_tokens | INT | Nullable |
| cache_write_tokens | INT | Nullable |
| model_provider | VARCHAR(64) | mock, anthropic, openai, etc. |
| model_name | VARCHAR(128) | Nullable |
| created_at | TIMESTAMPTZ | Required |
| updated_at | TIMESTAMPTZ | Required |

### Constraints

```sql
UNIQUE (chat_id, turn_index)
```

---

## 4.5 `chat_turn_sources`

Many-to-many join between chat turns and sources.

| Field | Type | Notes |
|---|---|---|
| chat_turn_id | UUID | FK to chat_turns ON DELETE CASCADE |
| source_id | UUID | FK to sources ON DELETE CASCADE |

Primary key:

```sql
PRIMARY KEY (chat_turn_id, source_id)
```

---

## 4.6 `sources`

Represents source material provided or authorized by the user.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| project_id | UUID | Nullable FK to projects; can be attached later |
| source_type | VARCHAR(50) | ARTICLE_URL, YOUTUBE_URL, PDF_FILE, BROWSER_PAGE, FILING_URL, IMAGE_FILE |
| source_access_method | VARCHAR(50) | SERVER_FETCH, BROWSER_EXTENSION, API_CONTEXT, UPLOAD, YOUTUBE_METADATA, YOUTUBE_TRANSCRIPT |
| source_access_status | VARCHAR(50) | PENDING, FULL_TEXT_EXTRACTED, METADATA_ONLY, BLOCKED, FAILED |
| original_input | TEXT | URL, file ref, or browser page URL |
| normalized_url | TEXT | Nullable canonical URL |
| file_key | TEXT | Nullable storage key |
| file_name | TEXT | Nullable |
| mime_type | VARCHAR(120) | Nullable |
| file_size_bytes | BIGINT | Nullable |
| title | TEXT | Nullable |
| publisher | TEXT | Nullable |
| author | TEXT | Nullable |
| published_at | TIMESTAMPTZ | Nullable |
| extracted_text | TEXT | Nullable; preferably temporary or limited retention |
| extracted_text_word_count | INTEGER | Nullable |
| extraction_confidence | VARCHAR(50) | HIGH, MEDIUM, LOW, UNKNOWN |
| extraction_error | TEXT | Nullable |
| raw_text_retention | VARCHAR(50) | EPHEMERAL, TEMPORARY_24H, NOT_STORED |
| content_hash | VARCHAR(255) | Optional deduplication |
| metadata | JSONB | OpenGraph, JSON-LD, YouTube metadata, extraction metadata |
| source_complexity | VARCHAR(50) | LOW, MEDIUM, HIGH, VERY_HIGH; nullable until scanned |
| segment_count | INTEGER | Nullable |
| scan_status | VARCHAR(50) | NOT_SCANNED, SCANNED, SCAN_FAILED |
| created_at | TIMESTAMPTZ | Required |
| updated_at | TIMESTAMPTZ | Required |

### Retention defaults

```text
ARTICLE_URL          → NOT_STORED after generation unless user explicitly saves text
BROWSER_PAGE         → TEMPORARY_24H by default, then purge extracted_text
PDF_FILE             → TEMPORARY_24H for extracted text; original file follows upload policy
YOUTUBE_TRANSCRIPT   → EPHEMERAL unless transcript retention is explicitly enabled later
```

---

## 4.7 `source_scans`

Cheap pre-analysis scan result for external sources.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| source_id | UUID | FK to sources ON DELETE CASCADE |
| user_id | UUID | FK to users |
| status | VARCHAR(50) | COMPLETED, FAILED |
| detected_document_subtype | VARCHAR(80) | COMPANY_PAGE, EARNINGS_REPORT, FINANCE_NEWS_ARTICLE, etc. |
| detected_entities | JSONB | Companies, tickers, themes, macro factors |
| estimated_source_complexity | VARCHAR(50) | LOW, MEDIUM, HIGH, VERY_HIGH |
| estimated_allowance_impact_percent | INTEGER | Nullable |
| estimate_confidence | VARCHAR(50) | HIGH, MEDIUM, LOW |
| requires_pre_analysis_warning | BOOLEAN | Default false |
| recommended_research_mode | VARCHAR(50) | QUICK, STANDARD, DEEP |
| recommended_completion_strategy | VARCHAR(50) | STRICT_REQUESTED_MODE, OPTIMIZE_RESEARCH |
| summary_json | JSONB | Scan-level summary |
| created_at | TIMESTAMPTZ | Required |

---

## 4.8 `source_segments`

Chunk map for long or complex sources.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| source_id | UUID | FK to sources ON DELETE CASCADE |
| source_scan_id | UUID | FK to source_scans nullable |
| segment_index | INT | Required |
| title | TEXT | Nullable |
| text_excerpt | TEXT | Optional excerpt; avoid long raw storage |
| start_offset | INT | Nullable |
| end_offset | INT | Nullable |
| start_timestamp_seconds | INT | Nullable for video |
| end_timestamp_seconds | INT | Nullable for video |
| detected_entities | JSONB | Nullable |
| topic_tags | JSONB | Nullable |
| estimated_complexity | VARCHAR(50) | LOW, MEDIUM, HIGH, VERY_HIGH |
| relevance_score | NUMERIC | Nullable |
| requested_research_mode | VARCHAR(50) | Nullable |
| actual_research_mode | VARCHAR(50) | Nullable |
| created_at | TIMESTAMPTZ | Required |

---

## 4.9 `canvases`

One freeform workspace per project for v0.3.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| project_id | UUID | FK to projects ON DELETE CASCADE, unique |
| user_id | UUID | FK to users, denormalized |
| title | TEXT | Default `Working canvas` |
| viewport_json | JSONB | Optional last viewport/zoom state |
| metadata | JSONB | Default `{}` |
| created_at | TIMESTAMPTZ | Required |
| updated_at | TIMESTAMPTZ | Required |

---

## 4.10 `canvas_elements`

Freeform visual elements inside a Canvas. This replaces strict ordered `CanvasBlock` as the main v0.3 Canvas model.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| canvas_id | UUID | FK to canvases ON DELETE CASCADE |
| project_id | UUID | FK to projects ON DELETE CASCADE, indexed |
| user_id | UUID | FK to users, denormalized |
| element_type | VARCHAR(40) | TEXT, AI_BLOCK, CLAIM, EVIDENCE, QUOTE, DATA, IMAGE, QUESTION, RISK, CATALYST, MINDMAP_NODE, GROUP, STICKY_NOTE |
| title | TEXT | Optional |
| content_markdown | TEXT | Nullable for text-like elements |
| content_json | JSONB | Default `{}`; structured fields per type |
| x | NUMERIC | Required |
| y | NUMERIC | Required |
| width | NUMERIC | Nullable |
| height | NUMERIC | Nullable |
| z_index | INT | Default 0 |
| style_json | JSONB | Optional color/tag/shape/font info |
| provenance_kind | VARCHAR(32) | CHAT_TURN, SOURCE, MANUAL, CANDIDATE, GENERATED |
| provenance_chat_turn_id | UUID | FK to chat_turns ON DELETE SET NULL, nullable |
| provenance_source_id | UUID | FK to sources ON DELETE SET NULL, nullable |
| confidence_label | VARCHAR(50) | HIGH, MEDIUM, LOW, UNKNOWN; optional |
| edited_by_user | BOOLEAN | Default false |
| archived_at | TIMESTAMPTZ | Nullable |
| created_at | TIMESTAMPTZ | Required |
| updated_at | TIMESTAMPTZ | Required |

### Element values

```text
TEXT          # user freeform writing
AI_BLOCK      # imported assistant answer or selected excerpt
CLAIM         # assertion or interpretation
EVIDENCE      # supporting fact/source point
QUOTE         # short source quote; policy-safe
DATA          # financial/market metric note
IMAGE         # screenshot/chart/image
QUESTION      # open research question
RISK          # risk/uncertainty
CATALYST      # event/change driver
MINDMAP_NODE  # simple graph/mind-map node
GROUP         # visual frame/group
STICKY_NOTE   # lightweight note card
```

---

## 4.11 `canvas_connections`

Edges between Canvas elements for simple mind maps and relationship mapping.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| canvas_id | UUID | FK to canvases ON DELETE CASCADE |
| project_id | UUID | FK to projects ON DELETE CASCADE |
| user_id | UUID | FK to users, denormalized |
| from_element_id | UUID | FK to canvas_elements ON DELETE CASCADE |
| to_element_id | UUID | FK to canvas_elements ON DELETE CASCADE |
| label | TEXT | Optional |
| connection_type | VARCHAR(40) | SUPPORTS, CONTRADICTS, CAUSES, DEPENDS_ON, RELATED_TO, CUSTOM |
| style_json | JSONB | Optional line style/arrow style |
| created_at | TIMESTAMPTZ | Required |
| updated_at | TIMESTAMPTZ | Required |

---

## 4.12 `candidate_elements`

AI-suggested Canvas elements generated from assistant turns. Users promote or dismiss them.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| chat_turn_id | UUID | FK to chat_turns ON DELETE CASCADE |
| project_id | UUID | FK to projects ON DELETE CASCADE |
| user_id | UUID | FK to users, denormalized |
| suggested_element_type | VARCHAR(40) | CanvasElementType |
| title | TEXT | Nullable |
| content_markdown | TEXT | Required |
| content_json | JSONB | Default `{}` |
| status | VARCHAR(16) | PENDING, PROMOTED, DISMISSED |
| promoted_element_id | UUID | FK to canvas_elements ON DELETE SET NULL |
| extraction_model_name | VARCHAR(128) | Nullable |
| created_at | TIMESTAMPTZ | Required |
| updated_at | TIMESTAMPTZ | Required |

Candidate extraction should never block the main assistant answer.

---

## 4.13 `project_memories`

Explicit project-level accumulated understanding.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| project_id | UUID | FK to projects ON DELETE CASCADE, unique |
| user_id | UUID | FK to users |
| summary_markdown | TEXT | Nullable project summary |
| entities_json | JSONB | Companies/tickers/themes/macros |
| themes_json | JSONB | Recurring themes |
| open_questions_json | JSONB | Durable research questions |
| conclusions_json | JSONB | Current project-level conclusions |
| last_compiled_from_activity_id | UUID | Nullable |
| updated_by | VARCHAR(20) | USER, AI, SYSTEM |
| created_at | TIMESTAMPTZ | Required |
| updated_at | TIMESTAMPTZ | Required |

Memory should be visible and editable later. Do not build spooky invisible memory and then act surprised when users distrust it.

---

## 4.14 `briefs`

Logical brief series inside a project.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| project_id | UUID | FK to projects ON DELETE CASCADE |
| user_id | UUID | FK to users |
| title | TEXT | Required |
| brief_type | VARCHAR(50) | COMPANY_RESEARCH, EARNINGS_BREAKDOWN, SOURCE_SUMMARY, MARKET_EVENT_EXPLAINER, THESIS_MEMO, BULL_BEAR_MEMO |
| subject | TEXT | Company/topic/event |
| ticker | VARCHAR(20) | Nullable |
| current_version_id | UUID | Nullable FK to brief_versions |
| status | VARCHAR(32) | ACTIVE, ARCHIVED |
| metadata | JSONB | Default `{}` |
| created_at | TIMESTAMPTZ | Required |
| updated_at | TIMESTAMPTZ | Required |

---

## 4.15 `brief_context_snapshots`

Point-in-time record of the context used for brief generation.

This replaces the earlier Canvas-only snapshot model.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| project_id | UUID | FK to projects |
| user_id | UUID | FK to users |
| context_scope | VARCHAR(50) | CURRENT_THREAD, SELECTED_SOURCES, SELECTED_CANVAS, CANVAS_CLUSTER, PROJECT_MEMORY, FULL_PROJECT, CUSTOM |
| selected_chat_turn_ids | UUID[] | Optional |
| selected_source_ids | UUID[] | Optional |
| selected_canvas_element_ids | UUID[] | Optional |
| selected_memory_keys | TEXT[] | Optional |
| snapshot_json | JSONB | Exact material passed to brief generation |
| context_hash | VARCHAR(255) | For staleness/dedup detection |
| created_at | TIMESTAMPTZ | Required |

---

## 4.16 `brief_versions`

Generated point-in-time document from a selected context snapshot.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| brief_id | UUID | FK to briefs ON DELETE CASCADE |
| project_id | UUID | FK to projects |
| user_id | UUID | FK to users |
| version_number | INT | Starts at 1 |
| brief_context_snapshot_id | UUID | FK to brief_context_snapshots |
| status | VARCHAR(32) | QUEUED, PROCESSING, COMPLETED, FAILED, ARCHIVED |
| content_markdown | TEXT | Generated brief text |
| sections | JSONB | Structured brief sections |
| summary_of_changes | TEXT | Diff vs previous version when available |
| generated_from_summary | TEXT | e.g. `current thread + 3 sources + 5 Canvas elements` |
| model_provider | VARCHAR(100) | Nullable |
| model_name | VARCHAR(100) | Nullable |
| prompt_version | VARCHAR(50) | Nullable |
| disclaimer | TEXT | Required |
| created_at | TIMESTAMPTZ | Required |
| updated_at | TIMESTAMPTZ | Required |

### Brief meaning

A brief is not final truth. It is a generated snapshot from selected project context.

```text
Canvas = living thinking space
Sources = evidence library
Memory = accumulated understanding
BriefVersion = point-in-time packaged output
```

---

## 4.17 `tags` and tagging

Keep tags as secondary organization.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| name | VARCHAR(80) | Required |
| color | VARCHAR(30) | Optional frontend hint |
| created_at | TIMESTAMPTZ | Required |
| updated_at | TIMESTAMPTZ | Required |

Constraint:

```sql
UNIQUE (user_id, name)
```

Recommended joins:

```text
project_tags(project_id, tag_id)
canvas_element_tags(canvas_element_id, tag_id) optional later
brief_tags(brief_id, tag_id) optional later
```

---

## 4.18 `companies` and project/company references

Lightweight company reference table.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| ticker | VARCHAR(20) | Nullable but preferred |
| name | VARCHAR(255) | Required |
| exchange | VARCHAR(50) | Nullable |
| sector | VARCHAR(120) | Nullable |
| industry | VARCHAR(150) | Nullable |
| country | VARCHAR(80) | Nullable |
| metadata | JSONB | Optional |
| created_at | TIMESTAMPTZ | Required |
| updated_at | TIMESTAMPTZ | Required |

Joins:

```text
project_companies(project_id, company_id)
source_companies(source_id, company_id) optional later
canvas_element_companies(canvas_element_id, company_id) optional later
```

---

## 4.19 `research_activities`

Structured activity events for daily summaries and future engagement loops.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| project_id | UUID | FK to projects nullable |
| activity_type | VARCHAR(50) | See values below |
| entity_id | UUID | Nullable |
| entity_type | VARCHAR(50) | PROJECT, CHAT, CHAT_TURN, SOURCE, CANVAS_ELEMENT, BRIEF_VERSION, PROJECT_MEMORY |
| metadata | JSONB | Default `{}` |
| created_at | TIMESTAMPTZ | Required |

Values:

```text
CREATED_PROJECT
ASKED_QUESTION
DETECTED_SOURCE_INPUT
ATTACHED_SOURCE
ANALYZED_SOURCE
GENERATED_CHAT_REPLY
PROMOTED_TO_CANVAS
CREATED_CANVAS_ELEMENT
UPDATED_CANVAS_ELEMENT
CONNECTED_CANVAS_ELEMENTS
UPDATED_PROJECT_MEMORY
GENERATED_BRIEF_VERSION
CREATED_JOURNAL_ENTRY
GENERATED_DAILY_SUMMARY
```

---

## 4.20 `usage_events`

Basic AI usage/cost tracking.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| project_id | UUID | Nullable FK |
| entity_type | VARCHAR(50) | CHAT_TURN, CANDIDATE_EXTRACTION, BRIEF_VERSION, SOURCE_SCAN, MEMORY_UPDATE |
| entity_id | UUID | Nullable |
| provider | VARCHAR(100) | Nullable |
| model_name | VARCHAR(100) | Nullable |
| input_tokens | INT | Nullable |
| output_tokens | INT | Nullable |
| cache_read_tokens | INT | Nullable |
| cache_write_tokens | INT | Nullable |
| estimated_cost_usd | NUMERIC | Nullable |
| created_at | TIMESTAMPTZ | Required |

---

# 5. Compatibility Notes

## 5.1 What happens to `ResearchItem`?

The previous docs used `ResearchItem` as the central saved artifact. In the new direction, it creates ambiguity because Projects, Sources, Canvas elements, Memory, and Brief versions have clearer roles.

Recommended path:

```text
New build: avoid adding new ResearchItem dependencies.
If existing ResearchItem tables already exist, keep them as legacy/search-log wrappers.
Do not make formal brief generation depend on ResearchItem.
```

## 5.2 What about the old Ask Mode, URL Mode, and YouTube Mode?

Keep them internally, not as hard user-facing modes.

```text
Visible UX: one Ask box.
Internal routing: GENERAL_ASK, ARTICLE_ANALYSIS, YOUTUBE_ANALYSIS, PDF_ANALYSIS, FILING_ANALYSIS, BRIEF_GENERATION, CANVAS_ACTION.
```

A user should be able to paste a link and type “analyze this for me.” AlphaBrief should detect the source type and route the request. Making the user pick five modes first is UX bureaucracy with a fancy border.

---

# 6. Implementation Slices

## Slice A: Projects + Catchall

- `projects`
- auto-created Catchall
- project CRUD/read endpoints

## Slice B: Chats + One Ask Composer

- `chats`
- `chat_turns`
- smart input detection
- source auto-detection from message text
- mock AI provider
- send endpoint and polling

## Slice C: Sources + Source Attachment

- `sources`
- `chat_turn_sources`
- article / YouTube / PDF / browser extension ingestion
- extraction statuses and metadata-only fallback

## Slice D: Freeform Canvas

- `canvases`
- `canvas_elements`
- `canvas_connections`
- manual text/image/node creation
- move/resize/edit/delete/archive
- source/chat provenance

## Slice E: Candidate Elements

- `candidate_elements`
- AI extraction after assistant replies
- promote/dismiss to Canvas

## Slice F: Project Memory

- `project_memories`
- visible project summary/entities/themes/open questions
- manual or AI-assisted refresh

## Slice G: Brief Versions

- `briefs`
- `brief_context_snapshots`
- `brief_versions`
- generate from current thread, selected sources, project memory, selected Canvas elements, or full project context
- compare with previous version

## Slice H: Real LLM + Validation

- real AI provider
- output validation
- repair prompt
- source grounding rules
- usage tracking

---

# 7. Critical Scope Decision

Do not build the full future research platform now.

The v0.3 proof is:

```text
Can a user ask naturally, analyze sources, save useful ideas to a freeform Canvas, build visual understanding over time, and generate useful briefs on demand from the context they choose?
```

That is the non-wrapper product loop. Everything else is dessert, and dessert has killed more MVPs than competitors have.
