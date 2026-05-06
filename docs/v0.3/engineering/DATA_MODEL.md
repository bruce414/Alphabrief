# AlphaBrief v0.3 Data Model

## Version

`v0.3 First Milestone`

## Status

This document defines the narrowed v0.3 data model for AlphaBrief as a **market learning and research workspace**.

The earlier model treated **Brief** as the central artifact and included many advanced entities such as entitlement, promo-code, referral, export, citation, claim, and deep research infrastructure. That model remains useful as a long-term design sketch, but it is too broad for the first build.

For v0.3, AlphaBrief has two primary output modes:

```text
Ask Mode   → flexible finance/source analysis, similar to a ChatGPT-style answer but more market-aware
Brief Mode → formal structured research artifact, such as a company brief or earnings breakdown
```

The central saved object is:

```text
ResearchItem
```

A `ResearchItem` can represent an Ask response, a formal Brief, a source analysis, a daily research summary, or a journal entry.

This updated version also adds **Chrome Extension-ready source ingestion**. The extension is treated as a source access method, not as a separate product universe. Civilization briefly avoids duplicating every table. Incredible.

---

# 1. v0.3 Product Scope

## 1.1 In Scope

v0.3 should support:

- User accounts
- Ask Mode
- Brief Mode
- URL-based article source submission
- YouTube URL source submission
- PDF/file source upload
- Chrome Extension-ready source ingestion architecture
- Source extraction status tracking
- Metadata-only fallback for blocked/unavailable sources
- Saved research log
- Tags
- Lightweight company references
- Daily AI research summary
- User-written market journal
- Learning / research goals
- Basic AI generation job tracking
- Basic usage and cost tracking
- Quick / Standard / Deep research modes
- Cheap pre-scan for all external sources
- Source segmentation/chunk mapping for long or complex sources
- Optimize Research adaptive section-depth control
- Pre-analysis high-usage warning when estimated impact exceeds 50%
- Analysis depth by section in final outputs

## 1.2 Near-Roadmap / Extension-Ready Scope

The Chrome browser extension should be represented in v0.3 architecture and data model, but the actual extension UI can be built as a near-roadmap feature if needed.

Recommended framing:

```text
v0.3 backend should be extension-compatible.
The Chrome extension client can be built after the core source ingestion pipeline works.
```

## 1.3 Out of Scope for v0.3

The following should be moved to future versions:

- Full company library with live event tracking
- Watchlist alerts
- Auto-generated company event impact notes
- Push/email notifications
- Paid subscriptions and billing
- Promo codes
- Referral rewards
- Public sharing
- PDF/DOCX exports
- Portfolio-aware analysis
- Broker/trading integrations
- Full thesis tracking system
- Full claim/citation verification tables
- Full research channel registry
- Social sentiment ingestion
- Admin console
- Broad web crawling
- Paywall/login/CAPTCHA bypass
- Permanent storage of full copyrighted article text by default

These are good ideas. They are simply not v0.3. Shocking restraint, I know.

---

# 2. Core Design Principles

1. `ResearchItem` is the central saved artifact.
2. `Brief` is a formal subtype of `ResearchItem`, not the only output type.
3. `Source` represents user-submitted or user-authorized material such as URL, PDF, YouTube URL, or browser-extension page capture.
4. Direct user questions should not be stored as sources.
5. Do not expose a primary "paste entire article" workflow in v0.3. If source text is manually provided later, it should be an advanced fallback, not the main UX.
6. Use JSONB for flexible AI output sections in v0.3.
7. Normalize only the relationships that matter for retrieval and organization: sources, tags, companies.
8. Keep the daily summary and journal separate.
9. Track meaningful user activity so daily summaries can be generated from structured events, not from a giant cursed chat transcript.
10. Keep compliance-safe language: educational and informational, not personalized financial advice.
11. Store AI cost/usage data from the beginning, but keep billing out of v0.3.
12. Track how each source was accessed: server fetch, browser extension, API context, upload, or YouTube metadata/transcript path.
13. Store generated analysis and source metadata by default; avoid permanent raw full-text storage unless there is a clear retention policy.
14. Every external source should support cheap pre-scan, segmentation/chunk mapping, source complexity estimation, and research-depth control.
15. Research depth should be segment-aware: requested mode and actual mode may differ when Optimize Research is enabled or when allowance risk requires user-approved downgrade.
16. Warn users before generation when a single run is estimated to consume more than 50% of their current available research allowance.
17. Final outputs for segmented sources should show analysis depth by section.

---

# 3. Entity Relationship Overview

```text
User
 ├── ResearchItem
 │    ├── Brief optional
 │    ├── ResearchItemSource
 │    │    └── Source
 │    ├── ResearchItemTag
 │    │    └── Tag
 │    └── ResearchItemCompany
 │         └── Company
 │
 ├── Source
 ├── ResearchActivity
 ├── DailyResearchSummary
 ├── JournalEntry
 ├── LearningGoal
 ├── Tag
 ├── Company optional lightweight reference
 ├── GenerationJob
 ├── SourceScan
 ├── SourceSegment
 ├── AnalysisRun
 ├── AnalysisSegment
 ├── UserResearchAllowance
 └── UsageEvent
```

---

# 4. Tables

## 4.1 `users`

Represents a registered user.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| email | VARCHAR(255) | Unique, required |
| password_hash | VARCHAR(255) | Required unless OAuth-only later |
| display_name | VARCHAR(120) | Optional |
| role | VARCHAR(50) | USER, ADMIN |
| default_output_mode | VARCHAR(50) | ASK or BRIEF, default ASK |
| default_research_scope | VARCHAR(50) | USER_PROVIDED_ONLY or RECOMMENDED_CONTEXT |
| default_research_mode | VARCHAR(50) | QUICK, STANDARD, DEEP; default STANDARD |
| optimize_research_default | BOOLEAN | Default true for long/complex sources |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### Values

```text
role: USER, ADMIN
default_output_mode: ASK, BRIEF
default_research_scope: USER_PROVIDED_ONLY, RECOMMENDED_CONTEXT
default_research_mode: QUICK, STANDARD, DEEP
```

---

## 4.2 `research_items`

Central saved artifact for AlphaBrief.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| item_type | VARCHAR(50) | ASK_ANALYSIS, BRIEF, SOURCE_ANALYSIS, DAILY_SUMMARY, JOURNAL_ENTRY |
| title | TEXT | Display title |
| status | VARCHAR(50) | DRAFT, QUEUED, PROCESSING, COMPLETED, FAILED, ARCHIVED |
| original_user_input | TEXT | User question or instruction |
| output_markdown | TEXT | Renderable output |
| output_json | JSONB | Structured AI output |
| short_summary | TEXT | One-paragraph summary for list views |
| confidence_label | VARCHAR(50) | HIGH, MEDIUM, LOW, UNKNOWN |
| confidence_explanation | TEXT | Nullable |
| analysis_mode | VARCHAR(50) | SOURCE_BRIEF, CONTEXT_BRIEF, ASK_ANALYSIS, FORMAL_BRIEF |
| disclaimer | TEXT | Required for AI-generated research |
| model_provider | VARCHAR(100) | Nullable |
| model_name | VARCHAR(100) | Nullable |
| prompt_version | VARCHAR(50) | Nullable |
| requested_research_mode | VARCHAR(50) | QUICK, STANDARD, DEEP; nullable for non-AI journal rows |
| completion_strategy | VARCHAR(50) | STRICT_REQUESTED_MODE, OPTIMIZE_RESEARCH; nullable |
| coverage_mode | VARCHAR(50) | FULL_SOURCE, SELECTED_TOPICS, SELECTED_ENTITIES, CUSTOM_QUESTION; nullable |
| analysis_depth_summary | JSONB | Section-level depth summary for segmented outputs |
| generated_at | TIMESTAMP | Nullable |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### Values

```text
item_type:
ASK_ANALYSIS
BRIEF
SOURCE_ANALYSIS
DAILY_SUMMARY
JOURNAL_ENTRY

status:
DRAFT
QUEUED
PROCESSING
COMPLETED
FAILED
ARCHIVED

analysis_mode:
SOURCE_BRIEF       # Full source text/transcript was available
CONTEXT_BRIEF      # Full source unavailable; analysis uses metadata + public/market context
ASK_ANALYSIS       # Direct flexible user question
FORMAL_BRIEF       # Formal Brief Mode output
```

### Notes

Use `research_items` for the research log and saved history. Do not create separate list pages for every output type unless the frontend needs a specialized view.

---

## 4.3 `briefs`

Formal structured research artifact generated when the user chooses Brief Mode.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| research_item_id | UUID | Unique FK to research_items |
| brief_type | VARCHAR(50) | COMPANY_RESEARCH, EARNINGS_BREAKDOWN, SOURCE_SUMMARY, MARKET_EVENT_EXPLAINER |
| subject | TEXT | Company/topic/event/source being analyzed |
| ticker | VARCHAR(20) | Nullable |
| structure_version | VARCHAR(50) | Example: company_brief_v1 |
| sections | JSONB | Structured formal sections |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### v0.3 brief types

```text
COMPANY_RESEARCH
EARNINGS_BREAKDOWN
SOURCE_SUMMARY
MARKET_EVENT_EXPLAINER
```

### Notes

Only create a `briefs` row when the output is a formal structured brief. Ask Mode responses should usually stay as `research_items` without a `briefs` row.

---

## 4.4 `sources`

Represents source material provided or authorized by the user.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| source_type | VARCHAR(50) | ARTICLE_URL, YOUTUBE_URL, PDF_FILE, BROWSER_PAGE |
| source_access_method | VARCHAR(50) | SERVER_FETCH, BROWSER_EXTENSION, API_CONTEXT, UPLOAD, YOUTUBE_METADATA, YOUTUBE_TRANSCRIPT |
| source_access_status | VARCHAR(50) | PENDING, FULL_TEXT_EXTRACTED, METADATA_ONLY, BLOCKED, FAILED |
| original_input | TEXT | URL, file reference, or browser page URL |
| normalized_url | TEXT | Nullable canonical URL |
| file_key | TEXT | Nullable storage key |
| file_name | TEXT | Nullable |
| mime_type | VARCHAR(120) | Nullable |
| file_size_bytes | BIGINT | Nullable |
| title | TEXT | Nullable |
| publisher | TEXT | Nullable |
| author | TEXT | Nullable |
| published_at | TIMESTAMP | Nullable |
| extracted_text | TEXT | Nullable; preferably temporary or limited retention |
| extracted_text_word_count | INTEGER | Nullable |
| extraction_confidence | VARCHAR(50) | HIGH, MEDIUM, LOW, UNKNOWN |
| extraction_error | TEXT | Nullable |
| raw_text_retention | VARCHAR(50) | EPHEMERAL, TEMPORARY_24H, NOT_STORED |
| content_hash | VARCHAR(255) | Optional deduplication |
| metadata | JSONB | OpenGraph, JSON-LD, YouTube metadata, DOM extraction metadata, etc. |
| source_complexity | VARCHAR(50) | LOW, MEDIUM, HIGH, VERY_HIGH; nullable until scanned |
| segment_count | INTEGER | Nullable |
| scan_status | VARCHAR(50) | NOT_SCANNED, SCANNED, SCAN_FAILED |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### Values

```text
source_type:
ARTICLE_URL
YOUTUBE_URL
PDF_FILE
BROWSER_PAGE

source_access_method:
SERVER_FETCH         # Backend attempts safe public URL extraction
BROWSER_EXTENSION    # User clicked extension on a page they were viewing
API_CONTEXT          # Market/news/filing API fallback context
UPLOAD               # User uploaded a file, usually PDF
YOUTUBE_METADATA     # Title, description, channel, public metadata only
YOUTUBE_TRANSCRIPT   # Transcript/captions available through an allowed path

source_access_status:
PENDING
FULL_TEXT_EXTRACTED
METADATA_ONLY
BLOCKED
FAILED

raw_text_retention:
EPHEMERAL       # Used in memory only during generation
TEMPORARY_24H   # Kept briefly for debugging/retry, then deleted
NOT_STORED      # Only metadata and generated output stored
```

### Notes

Direct questions belong in `research_items.original_user_input`, not in `sources`.

`BROWSER_PAGE` is for Chrome extension ingestion. It represents a page the user explicitly chose to analyze from their browser. It should not imply broad crawling, background browsing, or bypassing access controls.

`PASTED_TEXT` is intentionally not a primary v0.3 source type. The user-facing product should avoid asking users to paste entire articles. If manual source text is added later, use a separate advanced flow and retention policy.

---

## 4.5 `research_item_sources`

Many-to-many join between saved research outputs and sources.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| research_item_id | UUID | FK to research_items |
| source_id | UUID | FK to sources |
| role | VARCHAR(50) | PRIMARY_INPUT, SUPPORTING_CONTEXT, API_ENRICHMENT |
| created_at | TIMESTAMP | Required |

---

## 4.6 `tags`

User-owned tags for organization.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| name | VARCHAR(80) | Required |
| color | VARCHAR(30) | Nullable frontend hint |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### Constraint

```sql
UNIQUE (user_id, name)
```

---

## 4.7 `research_item_tags`

Many-to-many join between research items and tags.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| research_item_id | UUID | FK to research_items |
| tag_id | UUID | FK to tags |
| created_at | TIMESTAMP | Required |

---

## 4.8 `companies`

Lightweight company reference table for v0.3.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| ticker | VARCHAR(20) | Nullable but preferred for public companies |
| name | VARCHAR(255) | Required |
| exchange | VARCHAR(50) | Nullable |
| sector | VARCHAR(120) | Nullable |
| industry | VARCHAR(150) | Nullable |
| country | VARCHAR(100) | Nullable |
| description | TEXT | Nullable |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### Notes

This is not the full Company Library yet. For v0.3, it exists only to support filtering, tagging, and future expansion.

---

## 4.9 `research_item_companies`

Many-to-many join between research outputs and companies.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| research_item_id | UUID | FK to research_items |
| company_id | UUID | FK to companies |
| relevance | VARCHAR(50) | PRIMARY, MENTIONED, AFFECTED |
| created_at | TIMESTAMP | Required |

---

## 4.10 `research_activities`

Tracks meaningful user/product activity for daily summaries.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| activity_type | VARCHAR(50) | ASKED_QUESTION, ANALYZED_SOURCE, GENERATED_BRIEF, SAVED_RESEARCH, CREATED_JOURNAL_ENTRY, CREATED_GOAL, GENERATED_DAILY_SUMMARY, ANALYZED_BROWSER_PAGE |
| title | TEXT | Short human-readable title |
| description | TEXT | Nullable |
| related_research_item_id | UUID | Nullable FK |
| related_source_id | UUID | Nullable FK |
| activity_metadata | JSONB | Optional structured context |
| created_at | TIMESTAMP | Required |

### Notes

Daily summaries should be generated from `research_activities`, `research_items`, tags, sources, and linked companies.

---

## 4.11 `daily_research_summaries`

AI-generated summary of what a user researched on a given day.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| research_item_id | UUID | Nullable FK to research_items if saved as item |
| summary_date | DATE | Required |
| title | TEXT | Required |
| topics_covered | JSONB | Array |
| companies_mentioned | JSONB | Array |
| sources_analyzed | JSONB | Array |
| key_insights | JSONB | Array |
| open_questions | JSONB | Array |
| suggested_followups | JSONB | Array |
| summary_markdown | TEXT | Renderable summary |
| generated_at | TIMESTAMP | Required |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### Constraint

```sql
UNIQUE (user_id, summary_date)
```

---

## 4.12 `journal_entries`

User-written market learning / reflection journal entries.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| research_item_id | UUID | Nullable FK if saved in research log |
| linked_daily_summary_id | UUID | Nullable FK to daily_research_summaries |
| entry_date | DATE | Required |
| entry_type | VARCHAR(50) | LEARNING_REFLECTION, MARKET_REFLECTION |
| title | TEXT | Required |
| body | TEXT | User-written body |
| ai_assisted | BOOLEAN | Default false |
| reflection_prompts | JSONB | Optional prompts shown to user |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### v0.3 entry types

```text
LEARNING_REFLECTION
MARKET_REFLECTION
```

### Future entry types

```text
TRADE_REFLECTION
THESIS_UPDATE
```

---

## 4.13 `learning_goals`

User-defined research or learning goals.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| title | TEXT | Required |
| description | TEXT | Nullable |
| goal_type | VARCHAR(50) | LEARN_TOPIC, RESEARCH_COMPANY, FOLLOW_MARKET, BUILD_THESIS |
| status | VARCHAR(50) | ACTIVE, COMPLETED, PAUSED, ARCHIVED |
| target_date | DATE | Nullable |
| progress_notes | TEXT | Nullable |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

---

## 4.14 `generation_jobs`

Tracks AI generation for Ask Mode, Brief Mode, daily summaries, and reflection assistance.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| research_item_id | UUID | Nullable FK |
| job_type | VARCHAR(50) | ASK_ANALYSIS, BRIEF_GENERATION, DAILY_SUMMARY, REFLECTION_ASSIST, SOURCE_EXTRACTION |
| status | VARCHAR(50) | QUEUED, RUNNING, COMPLETED, FAILED, CANCELLED |
| current_step | VARCHAR(80) | Nullable |
| retry_count | INTEGER | Default 0 |
| error_code | VARCHAR(100) | Nullable |
| error_message | TEXT | Nullable |
| started_at | TIMESTAMP | Nullable |
| completed_at | TIMESTAMP | Nullable |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

---



## 4.15 `source_scans`

Stores cheap pre-analysis scan results for external sources.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| source_id | UUID | FK to sources |
| requested_output_mode | VARCHAR(50) | ASK, BRIEF |
| analysis_intent | VARCHAR(50) | QUICK_SUMMARY, MARKET_IMPACT, COMPANY_ANALYSIS, LEARNING_MODE, STRUCTURED_BRIEF |
| requested_research_mode | VARCHAR(50) | QUICK, STANDARD, DEEP |
| coverage_mode | VARCHAR(50) | FULL_SOURCE, SELECTED_TOPICS, SELECTED_ENTITIES, CUSTOM_QUESTION |
| focus_question | TEXT | Nullable |
| source_complexity | VARCHAR(50) | LOW, MEDIUM, HIGH, VERY_HIGH |
| estimate_confidence | VARCHAR(50) | HIGH, MEDIUM, LOW, UNKNOWN |
| estimated_allowance_impact_percent | NUMERIC(5,2) | Estimated impact on current available allowance |
| requires_warning | BOOLEAN | True when estimate exceeds warning threshold |
| warning_level | VARCHAR(50) | NONE, INLINE, HIGH, VERY_HIGH |
| recommended_research_mode | VARCHAR(50) | QUICK, STANDARD, DEEP |
| recommended_completion_strategy | VARCHAR(50) | STRICT_REQUESTED_MODE, OPTIMIZE_RESEARCH |
| detected_topics | JSONB | Array |
| detected_entities | JSONB | Array of companies, tickers, commodities, events, macro terms |
| created_at | TIMESTAMP | Required |

### Warning Rule

```text
If estimated_allowance_impact_percent > 50, show a pre-analysis warning before generation begins.
```

Do not warn users for small jobs. The goal is cost transparency, not turning the product into a nervous hall monitor.

---

## 4.16 `source_segments`

Represents source sections/chunks discovered during cheap scan.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| source_id | UUID | FK to sources |
| source_scan_id | UUID | Nullable FK to source_scans |
| segment_index | INTEGER | Required |
| start_offset_seconds | INTEGER | Nullable; for video/audio transcript |
| end_offset_seconds | INTEGER | Nullable; for video/audio transcript |
| start_char_offset | INTEGER | Nullable; for text/PDF/article chunks |
| end_char_offset | INTEGER | Nullable; for text/PDF/article chunks |
| page_start | INTEGER | Nullable; for PDFs |
| page_end | INTEGER | Nullable; for PDFs |
| title | TEXT | Nullable |
| topic_summary | TEXT | Nullable |
| detected_entities | JSONB | Array |
| detected_topics | JSONB | Array |
| estimated_complexity | VARCHAR(50) | LOW, MEDIUM, HIGH, VERY_HIGH |
| relevance_to_intent | VARCHAR(50) | HIGH, MEDIUM, LOW, UNKNOWN |
| recommended_research_mode | VARCHAR(50) | QUICK, STANDARD, DEEP |
| metadata | JSONB | Extra segment information |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

---

## 4.17 `analysis_runs`

Represents a generation run over a source or question, especially when segmented analysis is involved.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| research_item_id | UUID | FK to research_items |
| source_id | UUID | Nullable FK to sources |
| source_scan_id | UUID | Nullable FK to source_scans |
| requested_output_mode | VARCHAR(50) | ASK, BRIEF |
| analysis_intent | VARCHAR(50) | QUICK_SUMMARY, MARKET_IMPACT, COMPANY_ANALYSIS, LEARNING_MODE, STRUCTURED_BRIEF |
| requested_research_mode | VARCHAR(50) | QUICK, STANDARD, DEEP |
| completion_strategy | VARCHAR(50) | STRICT_REQUESTED_MODE, OPTIMIZE_RESEARCH |
| coverage_mode | VARCHAR(50) | FULL_SOURCE, SELECTED_TOPICS, SELECTED_ENTITIES, CUSTOM_QUESTION |
| focus_question | TEXT | Nullable |
| status | VARCHAR(50) | QUEUED, RUNNING, PAUSED, COMPLETED, FAILED, CANCELLED |
| estimated_allowance_impact_percent | NUMERIC(5,2) | Nullable |
| actual_allowance_impact_percent | NUMERIC(5,2) | Nullable |
| warning_acknowledged | BOOLEAN | Required, default false |
| allowance_before_percent | NUMERIC(5,2) | Nullable |
| allowance_after_percent | NUMERIC(5,2) | Nullable |
| started_at | TIMESTAMP | Nullable |
| completed_at | TIMESTAMP | Nullable |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### Completion Strategy Values

```text
STRICT_REQUESTED_MODE
OPTIMIZE_RESEARCH
```

---

## 4.18 `analysis_segments`

Stores the actual analysis produced for each source segment and records whether the requested research depth was changed.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| analysis_run_id | UUID | FK to analysis_runs |
| source_segment_id | UUID | Nullable FK to source_segments |
| segment_index | INTEGER | Required |
| title | TEXT | Nullable |
| start_offset_seconds | INTEGER | Nullable |
| end_offset_seconds | INTEGER | Nullable |
| requested_research_mode | VARCHAR(50) | QUICK, STANDARD, DEEP |
| actual_research_mode | VARCHAR(50) | QUICK, STANDARD, DEEP |
| status | VARCHAR(50) | QUEUED, RUNNING, COMPLETED, FAILED, SKIPPED |
| downgrade_reason | VARCHAR(80) | Nullable |
| analysis_markdown | TEXT | Nullable |
| analysis_json | JSONB | Nullable |
| key_entities | JSONB | Array |
| key_topics | JSONB | Array |
| can_rerun | BOOLEAN | True if lower-depth section can be rerun later |
| rerun_of_segment_id | UUID | Nullable self-reference |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### Downgrade Reasons

```text
ALLOWANCE_LIMIT
LOWER_RELEVANCE_TO_USER_INTENT
SOURCE_COMPLEXITY_HIGH
USER_SELECTED_OPTIMIZATION
ESTIMATE_UNCERTAINTY
```

---

## 4.19 `user_research_allowances`

Tracks the user-facing allowance percentage and cooldown/recovery state.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | Unique FK to users |
| allowance_percent_remaining | NUMERIC(5,2) | 0–100 user-facing value |
| cooldown_until | TIMESTAMP | Nullable |
| last_recovered_at | TIMESTAMP | Nullable |
| next_recovery_at | TIMESTAMP | Nullable |
| quick_available | BOOLEAN | Required |
| standard_available | BOOLEAN | Required |
| deep_available | BOOLEAN | Required |
| metadata | JSONB | Internal cost score, plan rules, recovery policy; do not expose directly |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### Notes

The UI should show percentages or plain labels. Internal cost scoring can consider tokens, entity count, source complexity, retrieval calls, source length, and uncertainty. Do not rely on fixed public units as the real source of truth.


## 4.20 `usage_events`

Basic usage and cost tracking for v0.3.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| research_item_id | UUID | Nullable FK |
| source_id | UUID | Nullable FK to sources |
| event_type | VARCHAR(50) | ASK, BRIEF, SUMMARY, REFLECTION_ASSIST, SOURCE_EXTRACTION, BROWSER_EXTENSION_INGESTION, API_CONTEXT_RETRIEVAL, SOURCE_SCAN, SEGMENT_ANALYSIS, ANALYSIS_RERUN |
| model_provider | VARCHAR(100) | Nullable |
| model_name | VARCHAR(100) | Nullable |
| input_tokens | INTEGER | Nullable |
| output_tokens | INTEGER | Nullable |
| estimated_allowance_impact_percent | NUMERIC(5,2) | Nullable |
| actual_allowance_impact_percent | NUMERIC(5,2) | Nullable |
| internal_cost_score | NUMERIC(12,4) | Nullable; not shown directly to users |
| estimated_cost_usd | NUMERIC(10,4) | Nullable |
| created_at | TIMESTAMP | Required |

### Notes

This gives cost visibility without implementing billing, subscriptions, credits, or plan limits yet.

---

# 5. Recommended v0.3 Implementation Slices

## Slice A: Core Workspace Foundation

Build:

```text
users
research_items
sources
research_item_sources
generation_jobs
source_scans
source_segments
analysis_runs
analysis_segments
user_research_allowances
usage_events
```

Supports:

```text
Ask Mode
Brief Mode foundation
source upload/submission
URL / YouTube input
browser-extension-compatible source ingestion
basic research log
```

## Slice B: Organization Layer

Build:

```text
tags
research_item_tags
companies
research_item_companies
```

Supports:

```text
saved research organization
company/topic filtering
future company library foundation
```

## Slice C: Learning Layer

Build:

```text
research_activities
daily_research_summaries
journal_entries
learning_goals
```

Supports:

```text
daily research summary
market journal
learning/reflection goals
engagement loop
```

## Slice D: Adaptive Research + Allowance Guardrails

Build:

```text
source_scans
source_segments
analysis_runs
analysis_segments
user_research_allowances
research_mode fields
completion_strategy fields
50% pre-analysis warning logic
Optimize Research support
analysis depth by section output
```

Supports:

```text
cheap scan for all external sources
source complexity estimation
segment-level research depth
long-source cost control
rerunnable downgraded sections
```

## Slice E: Browser Extension Integration

Backend-ready slice:

```text
source_access_method = BROWSER_EXTENSION
source_type = BROWSER_PAGE
POST /sources/browser-extension payload support
analysis_mode selection: SOURCE_BRIEF or CONTEXT_BRIEF
raw_text_retention handling
```

Frontend/extension client can be built after Slice A if desired.

---

# 6. Critical Scope Decision

Do not implement the old full v0.3 model all at once.

The previous model included many serious future-facing concepts: entitlements, promo codes, referrals, shares, exports, claim tables, citation tables, and deep research channels. Those are useful, but they are not necessary to prove the first product loop.

For v0.3, the product loop is:

```text
Ask or submit source
→ receive market-aware analysis or formal brief
→ save research
→ organize by tags/company
→ generate daily research summary
→ reflect in journal
→ progress toward learning goal
```

The Chrome extension should support the same loop by making source capture easier:

```text
Read article/video page
→ click AlphaBrief extension
→ generate source/context brief
→ save to research log
```

That is enough. The database is not supposed to be a museum of every thought you had at 2 a.m.

---

# 7. Future Migration Path

Later versions can add:

- `watchlists`
- `company_events`
- `event_impact_notes`
- `notifications`
- `theses`
- `thesis_updates`
- `plans`
- `user_entitlements`
- `plan_limits`
- `credit_transactions`
- `brief_shares`
- `brief_exports`
- `referrals`
- `research_channels`
- `claims`
- `citations`
- `extension_sessions`
- `extension_devices`
- `research_baskets`
- `multi_source_research_projects`

Do not add these until the workflow demands them.
