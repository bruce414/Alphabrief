# AlphaBrief Future Data Model Roadmap

## Purpose

This document stores entities that are intentionally out of scope for the v0.3 first milestone.

The goal is to avoid losing good product ideas while keeping v0.3 buildable. A bold concept, apparently.

---

# 1. Versioning Recommendation

Do **not** create a brand-new full `DATA_MODEL.md` for every tiny version.

Recommended documentation strategy:

```text
/docs
  /v0.3
    DATA_MODEL.md
    API_SPEC.md
    AI_PIPELINE.md
    TECHNICAL_ARCHITECTURE.md

  /future
    DATA_MODEL_ROADMAP.md
    PRODUCT_ROADMAP.md optional
```

Create a new full versioned doc set only when one of these changes materially:

- Major product scope
- Database relationship model
- API contract
- AI pipeline architecture
- Deployment or infrastructure architecture

Use a changelog or ADR for smaller changes.

Recommended version meaning:

| Version | Meaning |
|---|---|
| v0.3 | First usable AlphaBrief research workspace milestone |
| v0.4 | Organization and company library foundation |
| v0.5 | Watchlist, event tracking, thesis tracking foundation |
| v0.6+ | Monetization, sharing/export, deeper agentic research |
| v1.0 | Public MVP with stable core UX, reliability, and basic monetization |

Do not call the future data model `v1` yet. Most of these features should evolve through `v0.4`, `v0.5`, and `v0.6` before v1.

---

# 2. v0.4 Candidate: Company Library Lite

## Goal

Add a lightweight library of public companies so users can browse, save, and connect research to companies.

## Tables

### `company_profiles`

Extends the v0.3 `companies` table.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| company_id | UUID | FK to companies |
| overview_markdown | TEXT | Company overview |
| business_model_json | JSONB | Segments, revenue model, customers |
| key_risks_json | JSONB | Array |
| competitors_json | JSONB | Array or lightweight refs |
| last_refreshed_at | TIMESTAMP | Nullable |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### `saved_companies`

Early watchlist-like save without alerts.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| company_id | UUID | FK to companies |
| note | TEXT | Nullable |
| created_at | TIMESTAMP | Required |

---

# 3. v0.5 Candidate: Watchlist and Event Tracking

## Goal

Allow users to track companies and receive event-based analysis.

## Tables

### `watchlists`

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| name | VARCHAR(120) | Example: Main Watchlist |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### `watchlist_items`

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| watchlist_id | UUID | FK to watchlists |
| company_id | UUID | FK to companies |
| added_at | TIMESTAMP | Required |

### `company_events`

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| company_id | UUID | FK to companies |
| event_type | VARCHAR(80) | EARNINGS, REGULATION, PRODUCT, MACRO, COMPETITOR, MANAGEMENT, M_AND_A |
| title | TEXT | Required |
| description | TEXT | Nullable |
| event_date | TIMESTAMP | Nullable |
| source_url | TEXT | Nullable |
| source_title | TEXT | Nullable |
| raw_metadata | JSONB | Nullable |
| detected_at | TIMESTAMP | Required |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### `event_impact_notes`

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| company_event_id | UUID | FK to company_events |
| research_item_id | UUID | Nullable FK to research_items |
| impact_direction | VARCHAR(50) | POSITIVE, NEGATIVE, MIXED, UNCLEAR |
| impact_areas | JSONB | Revenue, margin, regulation, competition, valuation, etc. |
| explanation_markdown | TEXT | AI-generated analysis |
| confidence_label | VARCHAR(50) | HIGH, MEDIUM, LOW, UNKNOWN |
| generated_at | TIMESTAMP | Required |
| created_at | TIMESTAMP | Required |

### `notifications`

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| notification_type | VARCHAR(50) | WATCHLIST_EVENT, SUMMARY_READY, GOAL_REMINDER |
| title | TEXT | Required |
| body | TEXT | Nullable |
| related_company_id | UUID | Nullable |
| related_research_item_id | UUID | Nullable |
| read_at | TIMESTAMP | Nullable |
| created_at | TIMESTAMP | Required |

---

# 4. v0.5 / v0.6 Candidate: Thesis Tracking

## Goal

Let users save a market/company thesis and track whether new research supports or weakens it.

## Tables

### `theses`

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| company_id | UUID | Nullable FK to companies |
| title | TEXT | Required |
| thesis_body | TEXT | Required |
| status | VARCHAR(50) | ACTIVE, PAUSED, CLOSED, ARCHIVED |
| confidence_label | VARCHAR(50) | HIGH, MEDIUM, LOW, UNKNOWN |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### `thesis_updates`

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| thesis_id | UUID | FK to theses |
| research_item_id | UUID | Nullable FK to research_items |
| update_type | VARCHAR(50) | SUPPORTS, WEAKENS, MIXED, NO_CHANGE |
| evidence_summary | TEXT | Required |
| created_at | TIMESTAMP | Required |

---

# 5. v0.6+ Candidate: Monetization and Access Control

## Goal

Add proper Free/Pro/Beta/Student access control when the product has enough usage to justify it.

## Tables

- `plans`
- `user_entitlements`
- `plan_limits`
- `credit_transactions`
- `user_usage_daily`
- `promo_codes`
- `promo_code_redemptions`
- `payments`
- `subscriptions`

These existed in the earlier v0.3 draft, but they are too much for the immediate product-validation build.

---

# 6. v0.6+ Candidate: Sharing and Exports

## Tables

- `research_item_shares`
- `brief_exports`
- `export_jobs`

Add when users actually need public sharing or downloadable PDF/DOCX/Markdown outputs.

---

# 7. v0.6+ Candidate: Deep Evidence and Verification Layer

## Tables

- `research_channels`
- `external_context_items`
- `claims`
- `citations`
- `entity_insights`
- `entity_relationships`

Add when AlphaBrief begins doing deeper multi-source retrieval and needs claim-level traceability.

For v0.3, use `output_json` and a simple source list first. The AI does not become more accurate just because you created a table called `claims`. Humanity keeps learning this the hard way.

---

# 8. v1.0 Candidate: Public Product Baseline

v1.0 should not mean "every possible feature exists."

v1.0 should mean:

- Ask Mode works reliably
- Brief Mode works reliably
- Source extraction is acceptable
- Saved research log is useful
- Daily summary and journal create a real learning loop
- Company library/watchlist foundation is useful enough for retention
- Usage/cost controls are stable
- Compliance language is safe
- Basic monetization is ready or at least technically supportable

