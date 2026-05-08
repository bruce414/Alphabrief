# AlphaBrief v0.3 Data Model

## Version

`v0.3 First Milestone — Projects → Canvas → Versioned Briefs`

## Status

This document replaces the earlier `ResearchItem`-first model with AlphaBrief's new workspace direction:

```text
Projects → Chats / Sources → Canvas → Versioned Briefs
```

AlphaBrief v0.3 is no longer only a saved research log with tags. It is a market research workspace where chats are exploratory tools inside projects, the Canvas is the curated research artifact, and Briefs are generated snapshots from the Canvas.

The core product loop is:

```text
Ask or submit source
→ explore through a focused chat
→ AI suggests useful claims/notes
→ user promotes, edits, adds, and orders Canvas blocks
→ generate a versioned research brief from selected Canvas content
→ continue researching and generate updated versions later
```

The Canvas is the source of truth for brief generation. Raw chat transcripts are not the primary input for formal briefs.

---

# 1. v0.3 Product Scope

## 1.1 In Scope

v0.3 should support:

- User accounts
- Project workspaces
- Auto-created Catchall project for low-friction asking
- Focused chats inside projects
- Chat turns with attached sources
- URL, YouTube, PDF, and Chrome-extension-ready source ingestion
- Source extraction status tracking
- Metadata-only fallback for blocked/unavailable sources
- Cheap source scan and segmentation for long/complex external sources
- Quick / Standard / Deep research modes
- Optimize Research adaptive section-depth control
- Canvas blocks as curated research units
- Manual Canvas block creation
- Promote chat turns to Canvas
- Promote source-derived notes/quotes to Canvas
- AI-suggested candidate Canvas blocks after assistant replies
- User editing, archiving, deleting, and reordering Canvas blocks
- Brief generation from Canvas, not raw chat history
- Brief version history and “what changed since last version” summary
- Tags and lightweight company references
- Research activity tracking
- Basic usage/cost tracking
- Compliance-safe language: educational/informational, not personalized investment advice

## 1.2 Near-Roadmap / Extension-Ready Scope

The Chrome extension should remain represented in v0.3 architecture and data model, but the extension client can ship after the web workspace is stable.

Recommended framing:

```text
v0.3 backend should be extension-compatible.
The Chrome extension client can be built after source ingestion + chat attachment works.
```

## 1.3 Out of Scope for v0.3

Move these to later versions:

- Full autonomous multi-agent research planner
- Project memory beyond explicit Canvas context
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
- Cross-project Canvas block reuse
- Full visual mind map / market graph
- Collaboration / team workspaces
- Broad web crawling
- Paywall/login/CAPTCHA bypass
- Permanent storage of full copyrighted article text by default

---

# 2. Core Design Principles

1. `Project` is the top-level organizing container.
2. `Chat` is an exploration session inside a project, not the primary organizing unit.
3. `Source` stores user-submitted or user-authorized source material and metadata.
4. `CanvasBlock` is the atomic curated research unit.
5. `CanvasBlock` must be editable by the user. If the Canvas is only an extraction bucket, it does not justify existing.
6. `Brief` is a logical brief series inside a project.
7. `BriefVersion` is a point-in-time snapshot generated from a Canvas snapshot.
8. Formal briefs should be generated from selected/current Canvas blocks, not raw chat turns.
9. Direct user questions belong in chat turns, not sources.
10. Long/complex sources should be scanned, segmented, and analyzed with depth controls.
11. The Catchall project exists to remove friction, but the product should nudge users toward real projects when research starts accumulating.
12. The product should preserve provenance from Canvas blocks back to chat turns and/or sources.
13. Use JSONB for flexible AI output sections in v0.3.
14. Keep compliance-safe language: educational and informational, not personalized financial advice.
15. Store AI usage/cost data from the beginning, but keep billing out of v0.3.
16. Store generated analysis and source metadata by default; avoid permanent raw full-text storage without a retention policy.
17. Final segmented-source outputs should show analysis depth by section.
18. Project memory should be explicit and controlled. Bad hidden memory is worse than no memory.

---

# 3. Entity Relationship Overview

```text
User
 ├── Project
 │    ├── Chat
 │    │    ├── ChatTurn
 │    │    └── ChatTurnSource
 │    │         └── Source
 │    ├── CanvasBlock
 │    │    ├── provenance_chat_turn optional
 │    │    └── provenance_source optional
 │    ├── CandidateBlock
 │    ├── Brief
 │    │    └── BriefVersion
 │    │         └── CanvasSnapshot
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

`ResearchItem` can be deprecated for the new build or kept only as a backward-compatibility/search-log wrapper. For a clean v0.3 workspace build, prefer explicit domain objects: `Project`, `Chat`, `CanvasBlock`, `Brief`, and `BriefVersion`.

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
DECISION  # specific buy/sell/hold or compare decision research
```

### Constraints

```sql
CREATE UNIQUE INDEX uq_projects_one_catchall_per_user
ON projects(user_id)
WHERE kind = 'CATCHALL';
```

### Catchall behavior

The Catchall keeps asking friction near zero. However, AlphaBrief should make real projects visibly more valuable.

Recommended rule:

```text
Catchall supports chats and temporary capture.
Real project Canvas + BriefVersion workflows should be strongly encouraged for ongoing research.
```

A strict version may block formal brief generation from Catchall. A softer version may allow it but show a prompt:

```text
This looks like ongoing research. Create a project so future chats, Canvas blocks, and brief versions stay together.
```

---

## 4.3 `chats`

Focused exploration sessions inside a project.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| project_id | UUID | FK to projects ON DELETE CASCADE, indexed |
| user_id | UUID | FK to users, denormalized for fast owner checks |
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

User turns reference attached sources. Assistant turns should reference the same viewed sources, plus any later retrieved context sources if implemented.

---

## 4.6 `sources`

Represents source material provided or authorized by the user.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| source_type | VARCHAR(50) | ARTICLE_URL, YOUTUBE_URL, PDF_FILE, BROWSER_PAGE |
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

A scheduled purge job must remove expired `sources.extracted_text` for `TEMPORARY_24H` rows. Otherwise the retention enum is decoration wearing a lab coat.

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

## 4.9 `canvas_blocks`

Curated, ordered research blocks inside a project. This is the working research artifact.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| project_id | UUID | FK to projects ON DELETE CASCADE, indexed |
| user_id | UUID | FK to users, denormalized |
| block_type | VARCHAR(32) | CLAIM, QUOTE, NOTE, SUMMARY, RISK, QUESTION, METRIC, BULL_CASE, BEAR_CASE |
| content_markdown | TEXT | Required, user-editable |
| content_json | JSONB | Default `{}`; structured fields per block type |
| position_index | NUMERIC(20,10) | Fractional ordering |
| provenance_kind | VARCHAR(32) | CHAT_TURN, SOURCE, MANUAL, CANDIDATE |
| provenance_chat_turn_id | UUID | FK to chat_turns ON DELETE SET NULL, nullable |
| provenance_source_id | UUID | FK to sources ON DELETE SET NULL, nullable |
| title | TEXT | Optional short label |
| confidence_label | VARCHAR(50) | HIGH, MEDIUM, LOW, UNKNOWN; optional |
| archived_at | TIMESTAMPTZ | Nullable |
| created_at | TIMESTAMPTZ | Required |
| updated_at | TIMESTAMPTZ | Required |

### Values

```text
CLAIM      # assertion or interpretation
QUOTE      # source quote; keep short and policy-safe
NOTE       # user free-form note
SUMMARY    # condensed summary block
RISK       # risk/uncertainty
QUESTION   # open research question
METRIC     # financial/market metric note
BULL_CASE  # positive thesis point
BEAR_CASE  # negative thesis point
```

### Position model

Use fractional indices:

```text
Append: max(position_index) + 1.0
Insert between A and B: (A.position_index + B.position_index) / 2
```

If adjacent positions become too close, rebalance all active blocks to integer spacing. Keep rebalancing internal to the service.

---

## 4.10 `candidate_blocks`

AI-suggested Canvas blocks generated from assistant turns. Users promote or dismiss them.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| chat_turn_id | UUID | FK to chat_turns ON DELETE CASCADE |
| project_id | UUID | FK to projects ON DELETE CASCADE |
| user_id | UUID | FK to users, denormalized |
| block_type | VARCHAR(32) | CanvasBlockType |
| title | TEXT | Nullable |
| content_markdown | TEXT | Required |
| status | VARCHAR(16) | PENDING, PROMOTED, DISMISSED |
| promoted_block_id | UUID | FK to canvas_blocks ON DELETE SET NULL |
| extraction_model_name | VARCHAR(128) | Nullable |
| created_at | TIMESTAMPTZ | Required |
| updated_at | TIMESTAMPTZ | Required |

Candidate extraction should never block the main assistant answer.

---

## 4.11 `briefs`

Logical brief series inside a project.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| project_id | UUID | FK to projects ON DELETE CASCADE |
| user_id | UUID | FK to users |
| title | TEXT | Required |
| brief_type | VARCHAR(50) | COMPANY_RESEARCH, EARNINGS_BREAKDOWN, SOURCE_SUMMARY, MARKET_EVENT_EXPLAINER, THESIS_MEMO |
| subject | TEXT | Company/topic/event |
| ticker | VARCHAR(20) | Nullable |
| current_version_id | UUID | Nullable FK to brief_versions |
| status | VARCHAR(32) | ACTIVE, ARCHIVED |
| metadata | JSONB | Default `{}` |
| created_at | TIMESTAMPTZ | Required |
| updated_at | TIMESTAMPTZ | Required |

---

## 4.12 `canvas_snapshots`

Point-in-time record of Canvas blocks used for a brief version.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| project_id | UUID | FK to projects |
| user_id | UUID | FK to users |
| selected_block_ids | UUID[] | Blocks included in generation |
| selected_source_ids | UUID[] | Optional source list inferred from blocks |
| canvas_hash | VARCHAR(255) | For staleness detection |
| snapshot_json | JSONB | Ordered block contents at generation time |
| created_at | TIMESTAMPTZ | Required |

---

## 4.13 `brief_versions`

Generated point-in-time document from a Canvas snapshot.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| brief_id | UUID | FK to briefs ON DELETE CASCADE |
| project_id | UUID | FK to projects |
| user_id | UUID | FK to users |
| version_number | INT | Starts at 1 |
| canvas_snapshot_id | UUID | FK to canvas_snapshots |
| status | VARCHAR(32) | QUEUED, PROCESSING, COMPLETED, FAILED, ARCHIVED |
| content_markdown | TEXT | Generated brief text |
| sections | JSONB | Structured brief sections |
| summary_of_changes | TEXT | Diff vs previous version when available |
| generated_from_block_count | INT | Convenience field |
| model_provider | VARCHAR(100) | Nullable |
| model_name | VARCHAR(100) | Nullable |
| prompt_version | VARCHAR(50) | Nullable |
| disclaimer | TEXT | Required |
| created_at | TIMESTAMPTZ | Required |
| updated_at | TIMESTAMPTZ | Required |

### Brief meaning

A brief is not final truth. It is a generated snapshot from the state of the Canvas.

```text
Canvas = living research base
BriefVersion = point-in-time output
```

---

## 4.14 `tags` and project/block tagging

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
canvas_block_tags(canvas_block_id, tag_id) optional later
brief_tags(brief_id, tag_id) optional later
```

For v0.3, project-level tags may be enough.

---

## 4.15 `companies` and project/company references

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
canvas_block_companies(canvas_block_id, company_id) optional later
```

---

## 4.16 `research_activities`

Structured activity events for daily summaries and future engagement loops.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| project_id | UUID | FK to projects nullable |
| activity_type | VARCHAR(50) | See values below |
| entity_id | UUID | Nullable |
| entity_type | VARCHAR(50) | PROJECT, CHAT, CHAT_TURN, SOURCE, CANVAS_BLOCK, BRIEF_VERSION |
| metadata | JSONB | Default `{}` |
| created_at | TIMESTAMPTZ | Required |

Values:

```text
CREATED_PROJECT
ASKED_QUESTION
ATTACHED_SOURCE
ANALYZED_SOURCE
GENERATED_CHAT_REPLY
PROMOTED_TO_CANVAS
CREATED_CANVAS_BLOCK
UPDATED_CANVAS_BLOCK
GENERATED_BRIEF_VERSION
CREATED_JOURNAL_ENTRY
GENERATED_DAILY_SUMMARY
```

---

## 4.17 `usage_events`

Basic AI usage/cost tracking.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| project_id | UUID | Nullable FK |
| entity_type | VARCHAR(50) | CHAT_TURN, CANDIDATE_EXTRACTION, BRIEF_VERSION, SOURCE_SCAN |
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

The previous docs used `ResearchItem` as the central saved artifact. In the new direction, it creates ambiguity because Projects, Canvas blocks, and Brief versions have clearer roles.

Recommended path:

```text
New build: avoid adding new ResearchItem dependencies.
If existing ResearchItem tables already exist, keep them as legacy/search-log wrappers.
Do not make formal brief generation depend on ResearchItem.
```

A future search page can index across chats, sources, Canvas blocks, and brief versions without needing one table to pretend to be all of them.

## 5.2 What about the old Ask Mode and Brief Mode?

Keep them conceptually, but route them through the workspace:

```text
Ask Mode → Chat turn inside a project
Brief Mode → Generate BriefVersion from Canvas
Source Mode → Create Source, attach to chat, analyze, promote outputs to Canvas
```

---

# 6. Implementation Slices

## Slice A: Projects

- `projects`
- auto-created Catchall
- project CRUD/read endpoints

## Slice B: Chats

- `chats`
- chat CRUD/read endpoints

## Slice C: Chat Turns + Source Attachment

- `chat_turns`
- `chat_turn_sources`
- mock AI provider
- send endpoint and polling

## Slice D: Canvas

- `canvas_blocks`
- manual creation
- promote from chat turn/source
- edit/reorder/archive/delete

## Slice E: Candidate Blocks

- `candidate_blocks`
- AI extraction after assistant replies
- promote/dismiss

## Slice F: Brief Versions

- `briefs`
- `canvas_snapshots`
- `brief_versions`
- generate from selected Canvas blocks
- compare with previous version

## Slice G: Real LLM + Validation

- real AI provider
- output validation
- repair prompt
- source grounding rules
- usage tracking

## Slice H: Daily Summary / Journal / Learning Goals

- structured activities
- daily summaries
- journal/reflection assistant
- learning goals

---

# 7. Critical Scope Decision

Do not build the full future research platform now.

The v0.3 proof is:

```text
Can a user explore a market topic, capture useful insights to a Canvas, refine them, and generate an updated brief from that Canvas later?
```

That is the non-wrapper product loop. Everything else is dessert. Expensive dessert, naturally.
