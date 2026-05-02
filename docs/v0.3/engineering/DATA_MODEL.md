# AlphaBrief v0.3 Data Model

## Version

`v0.3 First Milestone`

## Status

This data model treats **v0.3 as the first major AlphaBrief milestone**. Earlier ideas that would have been considered v0.1 or v0.2 are now treated as internal implementation slices inside v0.3.

The model supports AlphaBrief as an **AI finance research assistant** where users can:

* Paste an article URL
* Paste a YouTube URL
* Upload a PDF or report
* Paste raw text
* Ask a direct finance or market-related question

All input types create the same central product artifact:

> A structured AlphaBrief research brief.

The brief is the core object. Sources are optional inputs, not the parent of every brief.

---

# 1. Product Direction

AlphaBrief v0.3 should support both:

## 1.1 Source-Based Briefs

Examples:

```text
Analyse this Visa earnings report.
Summarise this fintech article.
Turn this YouTube video into a finance brief.
```

Source-based briefs start from a user-provided source such as an article, video, PDF, or pasted text.

## 1.2 Question-Based Research Briefs

Examples:

```text
Analyse the fintech industry for me.
What are the main risks facing Tesla?
How do interest rates affect banks?
Is Visa threatened by fintech disruption?
```

Question-based briefs may start without any user-provided source. AlphaBrief should be able to generate a basic response first, and later use agent-discovered sources for deeper analysis.

## 1.3 Deep / Agentic Research Briefs

Deep briefs should not rely on one giant prompt. They should follow a structured pipeline:

```text
Input
→ classify input type
→ extract source content if applicable
→ detect entities
→ detect events and claims
→ retrieve external context if allowed
→ analyse implications
→ generate structured brief
→ verify claims where possible
→ persist structured output
```

---

# 2. Database

Recommended database:

```text
PostgreSQL
```

PostgreSQL is suitable because AlphaBrief needs:

* Relational ownership rules
* User-owned briefs and sources
* Optional source-based and question-based brief creation
* JSONB for flexible AI-generated output
* Indexing for brief history, source lookup, entity lookup, and usage limits
* Transactional subscription, promo-code, referral, and quota logic
* Traceable research sources, claims, citations, and external context

---

# 3. Core Design Principles

1. **Brief is the central artifact.** A source is only one possible input.
2. A brief may be created from a source, a direct question, or both.
3. `briefs.source_id` must be nullable.
4. Store the user's original question on the brief when the input is question-based.
5. Use `input_type` on `briefs` to classify how the brief was requested.
6. Use `sources` only for user-provided source material such as article URLs, YouTube URLs, PDFs, or pasted text.
7. Use `brief_sources` for any source used in the final brief, including user-provided and agent-discovered sources.
8. Use `JSONB` for flexible AI-generated sections such as implication maps, finance concepts, assignment angles, and research paths.
9. Avoid creating a separate table for every AI output section too early.
10. Store claim, event, citation, and entity data separately enough to support future verification and “what changed” features.
11. Keep internal source trust/channel metadata private.
12. Public UI should show safe source categories, not ranked lists of publishers.
13. Separate access from usage.
14. Use `user_entitlements` to determine what a user can access.
15. Use `plan_limits`, `user_usage_daily`, and `credit_transactions` to determine how much a user can use.
16. Track token and estimated cost internally from v0.3.
17. Store share tokens/slugs instead of full share URLs.
18. Model downloadable exports separately from briefs.
19. Model referrals and rewards as transactional records.
20. Design beta/testing access with explicit quotas.
21. Design deep brief generation as a pipeline, not a single prompt.
22. Store disclaimer text or disclaimer version on each generated brief.

---

# 4. Core Entities

The v0.3 first milestone should support:

* Users
* Sources
* Briefs
* Brief generation jobs
* Research channels
* Brief source usage records
* Financial entities
* Entity insights
* Brief events
* Brief claims
* Brief citations
* External context items
* Plans
* User entitlements
* Promo codes
* Promo code redemptions
* Usage limits
* Plan limits
* User daily usage
* Credit transactions
* Brief shares
* Brief exports
* Referrals

Optional future extensions:

* Paid subscriptions
* Admin grants
* Education verifications
* Watchlists
* Brief comparisons
* Entity relationships
* Legal document acceptance records

---

# 5. Entity Relationship Overview

## 5.1 Updated Core Relationship

```text
User
 ├── Source
 ├── Brief
 │    ├── Source optional
 │    ├── BriefGenerationJob
 │    ├── BriefSource
 │    │    └── ResearchChannel optional
 │    ├── BriefEntityInsight
 │    │    └── FinancialEntity
 │    ├── BriefEvent
 │    │    └── FinancialEntity optional
 │    ├── BriefClaim
 │    │    ├── BriefEvent optional
 │    │    └── FinancialEntity optional
 │    ├── BriefCitation
 │    │    ├── BriefClaim optional
 │    │    ├── BriefEvent optional
 │    │    └── FinancialEntity optional
 │    ├── ExternalContextItem
 │    │    └── FinancialEntity optional
 │    ├── BriefShare
 │    └── BriefExport
 │
 ├── UserEntitlement
 │    └── Plan
 │
 ├── PromoCodeRedemption
 │    ├── PromoCode
 │    └── UserEntitlement
 │
 ├── Referral
 ├── CreditTransaction
 ├── UserUsageDaily
 └── PlanLimit
```

## 5.2 Key Design Change

Old conceptual model:

```text
User
 └── Source
      └── Brief
```

Updated conceptual model:

```text
User
 └── Brief
      └── Source optional
```

Reason:

```text
A brief may be generated from a direct finance question without a user-provided source.
```

---

# 6. Access and Usage Model

```text
Plan = what product tier exists
UserEntitlement = what access a user currently has
PromoCode = one possible way to create an entitlement
Payment = another possible way to create an entitlement later
PlanLimit = default usage rules for each plan
CreditTransaction = grants, rewards, reservations, deductions, and refunds
UserUsageDaily = daily aggregate usage and cost tracking
```

Example:

```text
A user may have PRO access through a promo code.
That access is stored in user_entitlements.
Their brief limits are checked through plan_limits, user_usage_daily, and credit_transactions.
```

---

# 7. Tables

---

## 7.1 `users`

Represents a registered user.

| Field                  | Type         | Notes                               |
| ---------------------- | ------------ | ----------------------------------- |
| id                     | UUID         | Primary key                         |
| email                  | VARCHAR(255) | Unique, required                    |
| password_hash          | VARCHAR(255) | Nullable if OAuth-only auth is used |
| display_name           | VARCHAR(120) | Optional                            |
| role                   | VARCHAR(50)  | USER, ADMIN                         |
| referral_code          | VARCHAR(50)  | Unique user-owned referral code     |
| referred_by_user_id    | UUID         | Nullable FK to users                |
| default_research_scope | VARCHAR(50)  | Defaults to RECOMMENDED_SOURCES     |
| created_at             | TIMESTAMP    | Required                            |
| updated_at             | TIMESTAMP    | Required                            |

### Notes

Do not rely on `users.subscription_tier` as the source of truth.

A cached field such as `current_plan_code` can be added later for performance, but real access should come from `user_entitlements`.

### Recommended constraints

```sql
ALTER TABLE users
ADD CONSTRAINT uq_users_email UNIQUE (email);

ALTER TABLE users
ADD CONSTRAINT uq_users_referral_code UNIQUE (referral_code);
```

---

## 7.2 `plans`

Defines available product plans.

| Field       | Type         | Notes                                      |
| ----------- | ------------ | ------------------------------------------ |
| id          | UUID         | Primary key                                |
| code        | VARCHAR(50)  | FREE, PRO, STUDENT_PRO, BETA_TESTER, ADMIN |
| name        | VARCHAR(100) | Human-readable name                        |
| description | TEXT         | Optional                                   |
| active      | BOOLEAN      | Required, default true                     |
| created_at  | TIMESTAMP    | Required                                   |
| updated_at  | TIMESTAMP    | Required                                   |

### Example plan codes

```text
FREE
PRO
STUDENT_PRO
BETA_TESTER
ADMIN
```

### Notes

Student pricing should be represented as a plan such as `STUDENT_PRO`, not as `user_entitlements.source_type = STUDENT`.

Correct:

```text
plan_code = STUDENT_PRO
source_type = EDUCATION_VERIFICATION
```

or:

```text
plan_code = STUDENT_PRO
source_type = PAID_SUBSCRIPTION
```

---

## 7.3 `user_entitlements`

Represents a user's active, expired, revoked, or cancelled access.

| Field       | Type        | Notes                                                                                   |
| ----------- | ----------- | --------------------------------------------------------------------------------------- |
| id          | UUID        | Primary key                                                                             |
| user_id     | UUID        | FK to users                                                                             |
| plan_code   | VARCHAR(50) | FREE, PRO, STUDENT_PRO, BETA_TESTER, ADMIN                                              |
| source_type | VARCHAR(50) | FREE_DEFAULT, PROMO_CODE, PAID_SUBSCRIPTION, ADMIN_GRANT, TRIAL, EDUCATION_VERIFICATION |
| source_id   | UUID        | Nullable reference to redemption/payment/admin grant                                    |
| status      | VARCHAR(50) | ACTIVE, EXPIRED, REVOKED, CANCELLED                                                     |
| starts_at   | TIMESTAMP   | Required                                                                                |
| ends_at     | TIMESTAMP   | Nullable                                                                                |
| created_at  | TIMESTAMP   | Required                                                                                |
| updated_at  | TIMESTAMP   | Required                                                                                |

### Access rule

A user has access to a plan if:

```text
user_id = current user
plan_code = required plan
status = ACTIVE
starts_at <= now
ends_at IS NULL OR ends_at > now
```

---

## 7.4 `promo_codes`

Stores promo codes that can grant temporary or permanent access.

| Field                    | Type         | Notes                                  |
| ------------------------ | ------------ | -------------------------------------- |
| id                       | UUID         | Primary key                            |
| code_hash                | VARCHAR(255) | Hash of normalized promo code          |
| display_code_suffix      | VARCHAR(12)  | Last few chars for admin/debug display |
| plan_code                | VARCHAR(50)  | Plan granted by this code              |
| duration_days            | INTEGER      | Nullable                               |
| max_redemptions          | INTEGER      | Nullable                               |
| current_redemptions      | INTEGER      | Required, default 0                    |
| max_redemptions_per_user | INTEGER      | Required, usually 1                    |
| starts_at                | TIMESTAMP    | Nullable                               |
| expires_at               | TIMESTAMP    | Nullable                               |
| active                   | BOOLEAN      | Required, default true                 |
| created_by               | UUID         | Nullable FK to users/admin             |
| created_at               | TIMESTAMP    | Required                               |
| updated_at               | TIMESTAMP    | Required                               |

### Notes

Recommended flow:

```text
User enters code
→ normalize code
→ hash normalized code
→ compare with code_hash
```

For the earliest implementation, plain text storage is possible but not ideal.

---

## 7.5 `promo_code_redemptions`

Tracks which users redeemed which promo codes.

| Field          | Type        | Notes                   |
| -------------- | ----------- | ----------------------- |
| id             | UUID        | Primary key             |
| promo_code_id  | UUID        | FK to promo_codes       |
| user_id        | UUID        | FK to users             |
| entitlement_id | UUID        | FK to user_entitlements |
| redeemed_at    | TIMESTAMP   | Required                |
| status         | VARCHAR(50) | REDEEMED, REVOKED       |

### Recommended constraint

```sql
ALTER TABLE promo_code_redemptions
ADD CONSTRAINT uq_promo_redemptions_code_user
UNIQUE (promo_code_id, user_id);
```

---

## 7.6 `sources`

Represents user-provided input material.

A source is optional for a brief. Direct question-based briefs may not create a source.

| Field                 | Type         | Notes                                           |
| --------------------- | ------------ | ----------------------------------------------- |
| id                    | UUID         | Primary key                                     |
| user_id               | UUID         | FK to users                                     |
| source_type           | VARCHAR(50)  | ARTICLE_URL, YOUTUBE_URL, PDF_FILE, PASTED_TEXT |
| original_input        | TEXT         | Original URL, pasted text, or file reference    |
| normalized_url        | TEXT         | Nullable                                        |
| file_key              | TEXT         | Nullable storage key for uploaded file          |
| file_name             | TEXT         | Nullable original filename                      |
| mime_type             | VARCHAR(120) | Nullable                                        |
| file_size_bytes       | BIGINT       | Nullable                                        |
| title                 | TEXT         | Nullable                                        |
| raw_text              | TEXT         | Extracted or cleaned text                       |
| extraction_status     | VARCHAR(50)  | PENDING, EXTRACTED, FAILED                      |
| extraction_error      | TEXT         | Nullable                                        |
| content_hash          | VARCHAR(255) | Optional deduplication hash                     |
| submitted_source_role | VARCHAR(50)  | Usually USER_PROVIDED_SOURCE                    |
| created_at            | TIMESTAMP    | Required                                        |
| updated_at            | TIMESTAMP    | Required                                        |

### Source type values

```text
ARTICLE_URL
YOUTUBE_URL
PDF_FILE
PASTED_TEXT
```

### Extraction status values

```text
PENDING
EXTRACTED
FAILED
```

### Notes

Do not store direct finance questions in `sources`.

Use:

```text
briefs.user_query
```

for question-based requests.

---

## 7.7 `briefs`

Represents the generated AlphaBrief research brief.

This is the central product artifact.

| Field                     | Type         | Notes                                                                                      |
| ------------------------- | ------------ | ------------------------------------------------------------------------------------------ |
| id                        | UUID         | Primary key                                                                                |
| user_id                   | UUID         | FK to users                                                                                |
| source_id                 | UUID         | Nullable FK to sources                                                                     |
| input_type                | VARCHAR(50)  | QUESTION, ARTICLE_URL, YOUTUBE_URL, PDF_FILE, PASTED_TEXT, MIXED                           |
| user_query                | TEXT         | Nullable. Stores direct finance question or user instruction                               |
| title                     | TEXT         | Brief title                                                                                |
| brief_status              | VARCHAR(50)  | QUEUED, PROCESSING, COMPLETED, FAILED                                                      |
| plan_code_used            | VARCHAR(50)  | FREE, PRO, STUDENT_PRO, BETA_TESTER, ADMIN                                                 |
| requested_depth           | VARCHAR(50)  | AUTO, BASIC, DEEP                                                                          |
| research_scope            | VARCHAR(50)  | RECOMMENDED_SOURCES, EXPANDED_MARKET_CONTEXT, SENTIMENT_AND_DISCUSSION, USER_PROVIDED_ONLY |
| source_mix                | JSONB        | Safe user-facing source categories used                                                    |
| source_summary            | TEXT         | Main source summary if applicable                                                          |
| key_takeaways             | JSONB        | Array of strings or structured points                                                      |
| risks                     | JSONB        | Array of risks                                                                             |
| opportunities             | JSONB        | Array of opportunities                                                                     |
| investor_questions        | JSONB        | Questions investors/students should ask next                                               |
| bull_case                 | JSONB        | Bullish interpretation                                                                     |
| bear_case                 | JSONB        | Bearish interpretation                                                                     |
| confidence_score          | NUMERIC(5,2) | Optional 0-100 score                                                                       |
| confidence_explanation    | TEXT         | Why confidence is high/medium/low                                                          |
| generated_content         | JSONB        | Full structured AI output                                                                  |
| summary_markdown          | TEXT         | Renderable/exportable markdown version                                                     |
| disclaimer                | TEXT         | Required                                                                                   |
| disclaimer_version        | VARCHAR(50)  | Optional but recommended                                                                   |
| model_provider            | VARCHAR(100) | Optional                                                                                   |
| model_name                | VARCHAR(100) | Optional                                                                                   |
| prompt_version            | VARCHAR(50)  | Optional                                                                                   |
| research_pipeline_version | VARCHAR(50)  | Optional                                                                                   |
| generation_error          | TEXT         | Nullable                                                                                   |
| generated_at              | TIMESTAMP    | Nullable                                                                                   |
| created_at                | TIMESTAMP    | Required                                                                                   |
| updated_at                | TIMESTAMP    | Required                                                                                   |

### Input type values

```text
QUESTION
ARTICLE_URL
YOUTUBE_URL
PDF_FILE
PASTED_TEXT
MIXED
```

### Brief status values

```text
QUEUED
PROCESSING
COMPLETED
FAILED
```

### Requested depth values

```text
AUTO
BASIC
DEEP
```

### Research scope values

```text
RECOMMENDED_SOURCES
EXPANDED_MARKET_CONTEXT
SENTIMENT_AND_DISCUSSION
USER_PROVIDED_ONLY
```

### Notes

`source_id` must be nullable because question-based briefs may not have a user-provided source.

Examples:

```text
Question brief:
input_type = QUESTION
user_query = "Analyse the fintech industry for me"
source_id = null
```

```text
Source brief:
input_type = PDF_FILE
source_id = sources.id
user_query = "Focus on risks and implications"
```

```text
Mixed brief:
input_type = MIXED
source_id = sources.id
user_query = "Use this report and compare it with the fintech industry context"
```

---

## 7.8 Recommended `generated_content` Structure

`generated_content` should contain the complete structured output used by the frontend.

Recommended shape:

```json
{
  "quick_summary": "",
  "key_facts": [],
  "key_takeaways": [],
  "so_what": "",
  "implication_map": {
    "company_impact": [],
    "industry_impact": [],
    "investor_impact": [],
    "consumer_impact": [],
    "regulatory_impact": [],
    "macro_impact": [],
    "what_to_watch_next": []
  },
  "bull_bear_neutral": {
    "bull": [],
    "bear": [],
    "neutral": []
  },
  "risks_and_uncertainties": [],
  "finance_concepts": [
    {
      "term": "",
      "simple_explanation": "",
      "why_it_matters": "",
      "how_to_use_it": ""
    }
  ],
  "source_evidence_panel": [],
  "claims": [],
  "contradictions_or_tensions": [],
  "assignment_angles": [],
  "research_path_recommendations": [],
  "what_would_change_this_view": [],
  "student_takeaway": "",
  "investor_takeaway": "",
  "disclaimer": ""
}
```

### Notes

The structured JSON should be stable enough for frontend rendering but flexible enough to evolve.

Do not create separate tables for every section unless the feature needs querying, filtering, comparison, or long-term tracking.

---

## 7.9 `brief_generation_jobs`

Tracks async or step-by-step generation for a brief.

| Field         | Type         | Notes                                                   |
| ------------- | ------------ | ------------------------------------------------------- |
| id            | UUID         | Primary key                                             |
| brief_id      | UUID         | FK to briefs                                            |
| user_id       | UUID         | FK to users                                             |
| status        | VARCHAR(50)  | QUEUED, RUNNING, COMPLETED, FAILED, RETRYING, CANCELLED |
| current_step  | VARCHAR(80)  | Current pipeline step                                   |
| retry_count   | INTEGER      | Required, default 0                                     |
| max_retries   | INTEGER      | Required, default 3                                     |
| error_code    | VARCHAR(100) | Nullable                                                |
| error_message | TEXT         | Nullable                                                |
| started_at    | TIMESTAMP    | Nullable                                                |
| completed_at  | TIMESTAMP    | Nullable                                                |
| created_at    | TIMESTAMP    | Required                                                |
| updated_at    | TIMESTAMP    | Required                                                |

### Current step values

```text
VALIDATING_INPUT
CREATING_SOURCE
EXTRACTING_SOURCE
CLEANING_CONTENT
CLASSIFYING_REQUEST
DETECTING_ENTITIES
DETECTING_EVENTS
EXTRACTING_CLAIMS
RETRIEVING_CONTEXT
GENERATING_BRIEF
VALIDATING_OUTPUT
PERSISTING_RESULT
COMPLETED
FAILED
```

### Recommended flow

```text
POST /api/v1/briefs
→ validate input
→ create source if input is source-based
→ create brief with status QUEUED
→ create brief_generation_job with status QUEUED
→ return briefId
→ worker processes job
→ frontend polls GET /api/v1/briefs/{briefId}
```

---

## 7.10 `research_channels`

Represents an internal registry of sources/channels AlphaBrief may search during context retrieval.

| Field                  | Type         | Notes                                                |
| ---------------------- | ------------ | ---------------------------------------------------- |
| id                     | UUID         | Primary key                                          |
| name                   | VARCHAR(255) | Internal channel name                                |
| slug                   | VARCHAR(180) | Unique machine-friendly identifier                   |
| channel_type           | VARCHAR(80)  | REGULATORY_FILING, COMPANY_IR, FINANCIAL_MEDIA, etc. |
| base_url               | TEXT         | Nullable                                             |
| internal_trust_tier    | VARCHAR(50)  | INTERNAL_ONLY                                        |
| research_scope         | VARCHAR(50)  | Highest user-facing scope this channel belongs to    |
| default_usage_role     | VARCHAR(80)  | PRIMARY_EVIDENCE, SUPPORTING_EVIDENCE, etc.          |
| is_default_enabled     | BOOLEAN      | Whether usable in default retrieval                  |
| requires_subscription  | BOOLEAN      | Whether provider normally requires paid access       |
| requires_api           | BOOLEAN      | Whether integration requires API/client              |
| public_display_enabled | BOOLEAN      | Default false                                        |
| active                 | BOOLEAN      | Required, default true                               |
| created_at             | TIMESTAMP    | Required                                             |
| updated_at             | TIMESTAMP    | Required                                             |

### User-facing research scope labels

```text
Recommended Sources
Expanded Market Context
Sentiment & Discussion Signals
User-Provided Sources Only
```

### Internal trust tier values

```text
VERY_HIGH
HIGH
MEDIUM
LOW
BLOCKED
UNKNOWN
```

### Notes

Never expose internal trust tiers directly in public UI.

---

## 7.11 `brief_sources`

Represents the relationship between a generated brief and all sources used during research.

This includes user-provided sources and agent-discovered sources.

| Field                 | Type         | Notes                                                                                                             |
| --------------------- | ------------ | ----------------------------------------------------------------------------------------------------------------- |
| id                    | UUID         | Primary key                                                                                                       |
| brief_id              | UUID         | FK to briefs                                                                                                      |
| source_id             | UUID         | Nullable FK to sources for user-provided source                                                                   |
| research_channel_id   | UUID         | Nullable FK to research_channels                                                                                  |
| source_origin         | VARCHAR(50)  | USER_PROVIDED, AGENT_DISCOVERED, SYSTEM_CONTEXT                                                                   |
| source_title          | TEXT         | Article/report/video/page title                                                                                   |
| source_url            | TEXT         | Nullable                                                                                                          |
| publisher             | VARCHAR(255) | Nullable                                                                                                          |
| source_type           | VARCHAR(80)  | FILING, ARTICLE, TRANSCRIPT, VIDEO, DATASET, SOCIAL_POST, USER_PROVIDED, OTHER                                    |
| usage_role            | VARCHAR(80)  | MAIN_EVIDENCE, SUPPORTING_EVIDENCE, CONTRADICTING_EVIDENCE, BACKGROUND_CONTEXT, OPINION_CONTEXT, SENTIMENT_SIGNAL |
| source_category_label | VARCHAR(120) | Safe user-facing category                                                                                         |
| published_at          | TIMESTAMP    | Nullable                                                                                                          |
| accessed_at           | TIMESTAMP    | Required                                                                                                          |
| reliability_score     | NUMERIC(5,2) | Internal optional 0-100 score                                                                                     |
| relevance_score       | NUMERIC(5,2) | Internal optional 0-100 score                                                                                     |
| recency_score         | NUMERIC(5,2) | Internal optional 0-100 score                                                                                     |
| snippet               | TEXT         | Short excerpt or paraphrased evidence note                                                                        |
| created_at            | TIMESTAMP    | Required                                                                                                          |
| updated_at            | TIMESTAMP    | Required                                                                                                          |

### Source origin values

```text
USER_PROVIDED
AGENT_DISCOVERED
SYSTEM_CONTEXT
```

### Notes

Social/community sources should normally use `SENTIMENT_SIGNAL`, not `MAIN_EVIDENCE` for factual claims.

---

## 7.12 `financial_entities`

Represents a detected company, ticker, sector, asset, index, or macro factor.

| Field             | Type         | Notes                         |
| ----------------- | ------------ | ----------------------------- |
| id                | UUID         | Primary key                   |
| name              | VARCHAR(255) | Required                      |
| ticker            | VARCHAR(50)  | Nullable                      |
| exchange          | VARCHAR(50)  | Nullable                      |
| entity_type       | VARCHAR(50)  | COMPANY, TICKER, SECTOR, etc. |
| country           | VARCHAR(100) | Nullable                      |
| sector            | VARCHAR(100) | Nullable                      |
| industry          | VARCHAR(150) | Nullable                      |
| external_provider | VARCHAR(100) | Nullable                      |
| external_id       | VARCHAR(150) | Nullable                      |
| created_at        | TIMESTAMP    | Required                      |
| updated_at        | TIMESTAMP    | Required                      |

### Entity type values

```text
COMPANY
TICKER
SECTOR
INDEX
CRYPTO
COMMODITY
MACRO_FACTOR
CURRENCY
ETF
INDUSTRY
REGION
UNKNOWN
```

---

## 7.13 `brief_entity_insights`

Represents analysis for one financial entity within one brief.

| Field                        | Type      | Notes                                |
| ---------------------------- | --------- | ------------------------------------ |
| id                           | UUID      | Primary key                          |
| brief_id                     | UUID      | FK to briefs                         |
| entity_id                    | UUID      | FK to financial_entities             |
| source_specific_insight      | TEXT      | What the submitted source says       |
| company_context              | TEXT      | Basic context                        |
| industry_context             | TEXT      | Industry context                     |
| macro_context                | TEXT      | Macro context                        |
| political_regulatory_context | TEXT      | Political/regulatory context         |
| competitor_context           | TEXT      | Competitor context                   |
| risk_factors                 | JSONB     | Array of strings                     |
| opportunity_factors          | JSONB     | Array of strings                     |
| premium_only                 | BOOLEAN   | Whether this insight is premium-only |
| created_at                   | TIMESTAMP | Required                             |
| updated_at                   | TIMESTAMP | Required                             |

### Notes

This table is useful when AlphaBrief detects multiple companies or market entities inside one brief.

---

## 7.14 `brief_events`

Represents a financial, market, company, political, regulatory, macro, or industry event identified inside a brief.

| Field             | Type         | Notes                                              |
| ----------------- | ------------ | -------------------------------------------------- |
| id                | UUID         | Primary key                                        |
| brief_id          | UUID         | FK to briefs                                       |
| entity_id         | UUID         | Nullable FK to financial_entities                  |
| event_type        | VARCHAR(80)  | EARNINGS, TARIFF, REGULATION, PRODUCT_LAUNCH, etc. |
| title             | TEXT         | Short event title                                  |
| event_date        | DATE         | Nullable                                           |
| description       | TEXT         | Event summary                                      |
| source_origin     | VARCHAR(50)  | SOURCE_MENTIONED, EXTERNAL_CONTEXT, MODEL_INFERRED |
| impact_direction  | VARCHAR(50)  | POSITIVE, NEGATIVE, MIXED, UNCLEAR                 |
| impact_magnitude  | VARCHAR(50)  | LOW, MEDIUM, HIGH, UNKNOWN                         |
| confidence_score  | NUMERIC(5,2) | Optional 0-100 score                               |
| reasoning_summary | TEXT         | Why this event matters                             |
| created_at        | TIMESTAMP    | Required                                           |
| updated_at        | TIMESTAMP    | Required                                           |

### Event type values

```text
EARNINGS
GUIDANCE
TARIFF
REGULATION
PRODUCT_LAUNCH
LITIGATION
MACRO
SUPPLY_CHAIN
COMPETITOR_NEWS
MANAGEMENT_CHANGE
M_AND_A
INDUSTRY_TREND
MARKET_MOVEMENT
UNKNOWN
```

---

## 7.15 `brief_claims`

Represents key claims extracted from the source or generated during analysis.

| Field              | Type         | Notes                                                    |
| ------------------ | ------------ | -------------------------------------------------------- |
| id                 | UUID         | Primary key                                              |
| brief_id           | UUID         | FK to briefs                                             |
| event_id           | UUID         | Nullable FK to brief_events                              |
| entity_id          | UUID         | Nullable FK to financial_entities                        |
| claim_text         | TEXT         | The claim being made                                     |
| claim_type         | VARCHAR(80)  | FACTUAL, INTERPRETIVE, FORECAST, RISK, OPPORTUNITY       |
| support_status     | VARCHAR(50)  | SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED, SPECULATIVE |
| confidence_score   | NUMERIC(5,2) | Optional 0-100 score                                     |
| verification_notes | TEXT         | Why this support status was assigned                     |
| created_at         | TIMESTAMP    | Required                                                 |
| updated_at         | TIMESTAMP    | Required                                                 |

### Notes

This helps AlphaBrief distinguish between:

```text
What the source said
What external evidence supports
What the model inferred
What remains speculative
```

---

## 7.16 `brief_citations`

Stores supporting evidence used in the brief.

| Field           | Type         | Notes                                                 |
| --------------- | ------------ | ----------------------------------------------------- |
| id              | UUID         | Primary key                                           |
| brief_id        | UUID         | FK to briefs                                          |
| claim_id        | UUID         | Nullable FK to brief_claims                           |
| event_id        | UUID         | Nullable FK to brief_events                           |
| entity_id       | UUID         | Nullable FK to financial_entities                     |
| brief_source_id | UUID         | Nullable FK to brief_sources                          |
| source_title    | TEXT         | Article/page/report title                             |
| source_url      | TEXT         | Nullable                                              |
| publisher       | VARCHAR(255) | Nullable                                              |
| published_at    | TIMESTAMP    | Nullable                                              |
| accessed_at     | TIMESTAMP    | Required                                              |
| snippet         | TEXT         | Short supporting excerpt or paraphrased evidence note |
| source_quality  | VARCHAR(50)  | INTERNAL_ONLY                                         |
| created_at      | TIMESTAMP    | Required                                              |
| updated_at      | TIMESTAMP    | Required                                              |

### Source quality values

```text
HIGH
MEDIUM
LOW
UNKNOWN
```

### Notes

Do not expose `source_quality` directly if it may create publisher/channel ranking problems.

---

## 7.17 `external_context_items`

Stores external data used to enrich a brief, especially for deep briefs.

| Field          | Type         | Notes                                                      |
| -------------- | ------------ | ---------------------------------------------------------- |
| id             | UUID         | Primary key                                                |
| brief_id       | UUID         | FK to briefs                                               |
| entity_id      | UUID         | Nullable FK to financial_entities                          |
| context_type   | VARCHAR(80)  | NEWS, COMPANY_PROFILE, MARKET_DATA, INDUSTRY_CONTEXT, etc. |
| provider       | VARCHAR(100) | External provider or internal source                       |
| title          | TEXT         | Nullable                                                   |
| url            | TEXT         | Nullable                                                   |
| published_at   | TIMESTAMP    | Nullable                                                   |
| snippet        | TEXT         | Nullable                                                   |
| raw_payload    | JSONB        | Optional structured provider response                      |
| used_in_prompt | BOOLEAN      | Required, default true                                     |
| created_at     | TIMESTAMP    | Required                                                   |
| updated_at     | TIMESTAMP    | Required                                                   |

### Context type values

```text
NEWS
COMPANY_PROFILE
MARKET_DATA
INDUSTRY_CONTEXT
MACRO_CONTEXT
REGULATORY_CONTEXT
COMPETITOR_CONTEXT
ANALYST_COMMENTARY
EARNINGS_CONTEXT
SOCIAL_SENTIMENT
UNKNOWN
```

---

## 7.18 `brief_shares`

Represents a shareable public or unlisted version of a brief.

| Field          | Type         | Notes                           |
| -------------- | ------------ | ------------------------------- |
| id             | UUID         | Primary key                     |
| brief_id       | UUID         | FK to briefs                    |
| user_id        | UUID         | Owner FK to users               |
| share_token    | VARCHAR(120) | Unique random token used in URL |
| slug           | VARCHAR(180) | Optional SEO-friendly slug      |
| visibility     | VARCHAR(50)  | PRIVATE, UNLISTED, PUBLIC       |
| enabled        | BOOLEAN      | Required, default true          |
| allow_download | BOOLEAN      | Required, default false         |
| view_count     | INTEGER      | Required, default 0             |
| created_at     | TIMESTAMP    | Required                        |
| shared_at      | TIMESTAMP    | Nullable                        |
| expires_at     | TIMESTAMP    | Nullable                        |
| revoked_at     | TIMESTAMP    | Nullable                        |
| updated_at     | TIMESTAMP    | Required                        |

### Notes

Store:

```text
share_token = brf_9xK2pLmQ
```

Generate URLs dynamically:

```text
https://alphabrief.ai/share/brf_9xK2pLmQ
```

Do not store full URLs as the source of truth.

---

## 7.19 `brief_exports`

Represents downloadable versions of a brief.

| Field            | Type        | Notes                               |
| ---------------- | ----------- | ----------------------------------- |
| id               | UUID        | Primary key                         |
| brief_id         | UUID        | FK to briefs                        |
| user_id          | UUID        | FK to users                         |
| export_type      | VARCHAR(50) | MARKDOWN, PDF, DOCX                 |
| status           | VARCHAR(50) | PENDING, COMPLETED, FAILED, EXPIRED |
| storage_provider | VARCHAR(50) | LOCAL, S3, R2, NONE                 |
| storage_key      | TEXT        | Nullable object key                 |
| file_url         | TEXT        | Nullable temporary/signed URL       |
| file_size_bytes  | BIGINT      | Nullable                            |
| error_message    | TEXT        | Nullable                            |
| created_at       | TIMESTAMP   | Required                            |
| completed_at     | TIMESTAMP   | Nullable                            |
| expires_at       | TIMESTAMP   | Nullable                            |
| updated_at       | TIMESTAMP   | Required                            |

### Notes

For the first implementation, Markdown can be generated on demand from `summary_markdown`.

PDF/DOCX exports should eventually be asynchronous.

---

## 7.20 `referrals`

Tracks referral relationships between users.

| Field                        | Type        | Notes                                                            |
| ---------------------------- | ----------- | ---------------------------------------------------------------- |
| id                           | UUID        | Primary key                                                      |
| referrer_user_id             | UUID        | FK to users                                                      |
| referred_user_id             | UUID        | Nullable FK to users                                             |
| referral_code                | VARCHAR(50) | Code used at signup                                              |
| status                       | VARCHAR(50) | INVITED, SIGNED_UP, ACTIVATED, REWARDED, CANCELLED, FRAUD_REVIEW |
| reward_granted               | BOOLEAN     | Required, default false                                          |
| reward_credit_transaction_id | UUID        | Nullable FK to credit_transactions                               |
| created_at                   | TIMESTAMP   | Required                                                         |
| signed_up_at                 | TIMESTAMP   | Nullable                                                         |
| activated_at                 | TIMESTAMP   | Nullable                                                         |
| rewarded_at                  | TIMESTAMP   | Nullable                                                         |
| updated_at                   | TIMESTAMP   | Required                                                         |

---

## 7.21 `credit_transactions`

Tracks brief credits, referral bonuses, signup bonuses, purchases, trial grants, reservations, refunds, and usage deductions.

| Field              | Type         | Notes                                                                                                                           |
| ------------------ | ------------ | ------------------------------------------------------------------------------------------------------------------------------- |
| id                 | UUID         | Primary key                                                                                                                     |
| user_id            | UUID         | FK to users                                                                                                                     |
| amount             | INTEGER      | Positive for grants/refunds, negative for deductions/reservations                                                               |
| credit_type        | VARCHAR(50)  | BASIC_BRIEF, DEEP_BRIEF, EXPORT_MARKDOWN, EXPORT_PDF, EXPORT_DOCX, GENERAL                                                      |
| transaction_type   | VARCHAR(80)  | REFERRAL_BONUS, SIGNUP_BONUS, PURCHASE, TRIAL_GRANT, USAGE_RESERVATION, USAGE_DEDUCTION, USAGE_REFUND, ADMIN_ADJUSTMENT, EXPIRY |
| transaction_status | VARCHAR(50)  | RESERVED, CONFIRMED, REFUNDED, CANCELLED, EXPIRED                                                                               |
| source_type        | VARCHAR(80)  | REFERRAL, PROMO_CODE, SUBSCRIPTION, USER_ENTITLEMENT, BRIEF_GENERATION, EXPORT_GENERATION, ADMIN, SYSTEM                        |
| source_id          | UUID         | Nullable reference to source object                                                                                             |
| idempotency_key    | VARCHAR(120) | Optional but recommended                                                                                                        |
| description        | TEXT         | Optional                                                                                                                        |
| expires_at         | TIMESTAMP    | Nullable                                                                                                                        |
| created_at         | TIMESTAMP    | Required                                                                                                                        |
| updated_at         | TIMESTAMP    | Required                                                                                                                        |

### Reservation pattern for expensive briefs

```text
1. Create -1 DEEP_BRIEF reservation before generation.
2. If generation succeeds, mark reservation CONFIRMED.
3. If generation fails before useful output, cancel or refund reservation.
```

---

## 7.22 `user_usage_daily`

Tracks daily usage for product limits, cost control, and monitoring.

| Field                    | Type          | Notes                                      |
| ------------------------ | ------------- | ------------------------------------------ |
| id                       | UUID          | Primary key                                |
| user_id                  | UUID          | FK to users                                |
| usage_date               | DATE          | Required                                   |
| plan_code_at_usage       | VARCHAR(50)   | FREE, PRO, STUDENT_PRO, BETA_TESTER, ADMIN |
| basic_brief_count        | INTEGER       | Number of basic briefs generated           |
| deep_brief_count         | INTEGER       | Number of deep briefs generated            |
| total_brief_count        | INTEGER       | Total briefs generated                     |
| export_count             | INTEGER       | Number of exports generated                |
| ai_input_token_estimate  | INTEGER       | Optional internal estimate                 |
| ai_output_token_estimate | INTEGER       | Optional internal estimate                 |
| ai_total_token_estimate  | INTEGER       | Optional internal estimate                 |
| ai_search_call_count     | INTEGER       | Optional retrieval/search count            |
| estimated_ai_cost_usd    | NUMERIC(12,6) | Optional internal estimate                 |
| created_at               | TIMESTAMP     | Required                                   |
| updated_at               | TIMESTAMP     | Required                                   |

### Recommended unique constraint

```sql
ALTER TABLE user_usage_daily
ADD CONSTRAINT uq_user_usage_daily_user_date
UNIQUE (user_id, usage_date);
```

---

## 7.23 `plan_limits`

Defines reusable usage rules for each plan.

| Field        | Type        | Notes                                                                                     |
| ------------ | ----------- | ----------------------------------------------------------------------------------------- |
| id           | UUID        | Primary key                                                                               |
| plan_code    | VARCHAR(50) | FREE, PRO, STUDENT_PRO, BETA_TESTER, ADMIN                                                |
| feature_code | VARCHAR(80) | TOTAL_BRIEF, BASIC_BRIEF, DEEP_BRIEF, EXPORT_PDF, EXPORT_DOCX, PREMIUM_CONTEXT, WATCHLIST |
| limit_amount | INTEGER     | Nullable for unlimited                                                                    |
| reset_period | VARCHAR(50) | DAILY, WEEKLY, MONTHLY, LIFETIME, NONE                                                    |
| active       | BOOLEAN     | Required, default true                                                                    |
| created_at   | TIMESTAMP   | Required                                                                                  |
| updated_at   | TIMESTAMP   | Required                                                                                  |

### Example plan limits

```text
FREE + TOTAL_BRIEF + 3 + DAILY
FREE + DEEP_BRIEF + 0 + MONTHLY

BETA_TESTER + TOTAL_BRIEF + 10 + LIFETIME
BETA_TESTER + DEEP_BRIEF + 2 + LIFETIME

PRO + TOTAL_BRIEF + 50 + DAILY
PRO + DEEP_BRIEF + 10 + MONTHLY

STUDENT_PRO + TOTAL_BRIEF + 30 + DAILY
STUDENT_PRO + DEEP_BRIEF + 5 + MONTHLY

ADMIN + TOTAL_BRIEF + null + NONE
ADMIN + DEEP_BRIEF + null + NONE
```

---

# 8. Optional Future Tables

These are useful later but do not have to block the v0.3 first implementation.

---

## 8.1 `paid_subscriptions`

Use when Stripe or another payment provider is added.

| Field                    | Type         | Notes                                |
| ------------------------ | ------------ | ------------------------------------ |
| id                       | UUID         | Primary key                          |
| user_id                  | UUID         | FK to users                          |
| provider                 | VARCHAR(50)  | STRIPE, etc.                         |
| provider_customer_id     | VARCHAR(255) | External customer ID                 |
| provider_subscription_id | VARCHAR(255) | External subscription ID             |
| plan_code                | VARCHAR(50)  | PRO, STUDENT_PRO                     |
| status                   | VARCHAR(50)  | ACTIVE, PAST_DUE, CANCELLED, EXPIRED |
| current_period_start     | TIMESTAMP    | Nullable                             |
| current_period_end       | TIMESTAMP    | Nullable                             |
| created_at               | TIMESTAMP    | Required                             |
| updated_at               | TIMESTAMP    | Required                             |

Successful payment should create or update a `user_entitlements` row.

---

## 8.2 `admin_grants`

Use if admins need to manually grant access.

| Field      | Type        | Notes                   |
| ---------- | ----------- | ----------------------- |
| id         | UUID        | Primary key             |
| user_id    | UUID        | FK to users             |
| granted_by | UUID        | FK to admin user        |
| plan_code  | VARCHAR(50) | PRO, STUDENT_PRO, ADMIN |
| reason     | TEXT        | Optional                |
| starts_at  | TIMESTAMP   | Required                |
| ends_at    | TIMESTAMP   | Nullable                |
| created_at | TIMESTAMP   | Required                |

Admin grants should create a `user_entitlements` row.

---

## 8.3 `education_verifications`

Use if AlphaBrief adds student pricing and needs verification.

| Field                 | Type         | Notes                                |
| --------------------- | ------------ | ------------------------------------ |
| id                    | UUID         | Primary key                          |
| user_id               | UUID         | FK to users                          |
| institution_name      | VARCHAR(255) | Nullable                             |
| institution_email     | VARCHAR(255) | Nullable                             |
| verification_provider | VARCHAR(100) | INTERNAL, MANUAL, SHEER_ID, etc.     |
| status                | VARCHAR(50)  | PENDING, VERIFIED, REJECTED, EXPIRED |
| verified_at           | TIMESTAMP    | Nullable                             |
| expires_at            | TIMESTAMP    | Nullable                             |
| created_at            | TIMESTAMP    | Required                             |
| updated_at            | TIMESTAMP    | Required                             |

Successful verification can create or update:

```text
plan_code = STUDENT_PRO
source_type = EDUCATION_VERIFICATION
```

---

## 8.4 `watchlists`

Use later for tracked companies/topics.

| Field      | Type         | Notes          |
| ---------- | ------------ | -------------- |
| id         | UUID         | Primary key    |
| user_id    | UUID         | FK to users    |
| name       | VARCHAR(120) | Watchlist name |
| created_at | TIMESTAMP    | Required       |
| updated_at | TIMESTAMP    | Required       |

---

## 8.5 `watchlist_items`

Use later for saved entities or topics.

| Field        | Type      | Notes                             |
| ------------ | --------- | --------------------------------- |
| id           | UUID      | Primary key                       |
| watchlist_id | UUID      | FK to watchlists                  |
| entity_id    | UUID      | Nullable FK to financial_entities |
| topic_text   | TEXT      | Nullable custom topic             |
| created_at   | TIMESTAMP | Required                          |
| updated_at   | TIMESTAMP | Required                          |

---

## 8.6 `brief_comparisons`

Use later for “What Changed?” tracking.

| Field              | Type      | Notes              |
| ------------------ | --------- | ------------------ |
| id                 | UUID      | Primary key        |
| user_id            | UUID      | FK to users        |
| previous_brief_id  | UUID      | FK to briefs       |
| current_brief_id   | UUID      | FK to briefs       |
| comparison_summary | TEXT      | Summary of changes |
| changed_items      | JSONB     | Structured changes |
| created_at         | TIMESTAMP | Required           |

---

## 8.7 `entity_relationships`

Use later for entity graphs.

| Field             | Type         | Notes                                    |
| ----------------- | ------------ | ---------------------------------------- |
| id                | UUID         | Primary key                              |
| source_entity_id  | UUID         | FK to financial_entities                 |
| target_entity_id  | UUID         | FK to financial_entities                 |
| relationship_type | VARCHAR(80)  | COMPETITOR, SUPPLIER, REGULATED_BY, etc. |
| confidence_score  | NUMERIC(5,2) | Optional                                 |
| created_at        | TIMESTAMP    | Required                                 |
| updated_at        | TIMESTAMP    | Required                                 |

### Relationship type values

```text
COMPETITOR
SUPPLIER
CUSTOMER
SECTOR_MEMBER
REGULATED_BY
AFFECTED_BY
PARTNER
SUBSTITUTE
PARENT_COMPANY
SUBSIDIARY
UNKNOWN
```

---

# 9. Enums

## 9.1 `role`

```text
USER
ADMIN
```

## 9.2 `plan_code`

```text
FREE
PRO
STUDENT_PRO
BETA_TESTER
ADMIN
```

## 9.3 `entitlement_source_type`

```text
FREE_DEFAULT
PROMO_CODE
PAID_SUBSCRIPTION
ADMIN_GRANT
TRIAL
EDUCATION_VERIFICATION
```

## 9.4 `entitlement_status`

```text
ACTIVE
EXPIRED
REVOKED
CANCELLED
```

## 9.5 `source_type`

```text
ARTICLE_URL
YOUTUBE_URL
PDF_FILE
PASTED_TEXT
```

## 9.6 `brief_input_type`

```text
QUESTION
ARTICLE_URL
YOUTUBE_URL
PDF_FILE
PASTED_TEXT
MIXED
```

## 9.7 `extraction_status`

```text
PENDING
EXTRACTED
FAILED
```

## 9.8 `research_scope`

```text
RECOMMENDED_SOURCES
EXPANDED_MARKET_CONTEXT
SENTIMENT_AND_DISCUSSION
USER_PROVIDED_ONLY
```

## 9.9 `channel_type`

```text
REGULATORY_FILING
COMPANY_IR
FINANCIAL_MEDIA
NEWSLETTER
VIDEO_CHANNEL
SOCIAL_PLATFORM
MARKET_DATA
MACRO_DATA
SPECIALIST_RESEARCH
UNKNOWN
```

## 9.10 `internal_trust_tier`

```text
VERY_HIGH
HIGH
MEDIUM
LOW
BLOCKED
UNKNOWN
```

## 9.11 `brief_status`

```text
QUEUED
PROCESSING
COMPLETED
FAILED
```

## 9.12 `job_status`

```text
QUEUED
RUNNING
COMPLETED
FAILED
RETRYING
CANCELLED
```

## 9.13 `requested_depth`

```text
AUTO
BASIC
DEEP
```

## 9.14 `entity_type`

```text
COMPANY
TICKER
SECTOR
INDEX
CRYPTO
COMMODITY
MACRO_FACTOR
CURRENCY
ETF
INDUSTRY
REGION
UNKNOWN
```

## 9.15 `source_origin`

```text
USER_PROVIDED
AGENT_DISCOVERED
SYSTEM_CONTEXT
```

## 9.16 `brief_source_usage_role`

```text
MAIN_EVIDENCE
SUPPORTING_EVIDENCE
CONTRADICTING_EVIDENCE
BACKGROUND_CONTEXT
OPINION_CONTEXT
SENTIMENT_SIGNAL
```

## 9.17 `event_type`

```text
EARNINGS
GUIDANCE
TARIFF
REGULATION
PRODUCT_LAUNCH
LITIGATION
MACRO
SUPPLY_CHAIN
COMPETITOR_NEWS
MANAGEMENT_CHANGE
M_AND_A
INDUSTRY_TREND
MARKET_MOVEMENT
UNKNOWN
```

## 9.18 `impact_direction`

```text
POSITIVE
NEGATIVE
MIXED
UNCLEAR
```

## 9.19 `impact_magnitude`

```text
LOW
MEDIUM
HIGH
UNKNOWN
```

## 9.20 `claim_type`

```text
FACTUAL
INTERPRETIVE
FORECAST
RISK
OPPORTUNITY
```

## 9.21 `claim_support_status`

```text
SUPPORTED
PARTIALLY_SUPPORTED
UNSUPPORTED
SPECULATIVE
```

## 9.22 `brief_visibility`

```text
PRIVATE
UNLISTED
PUBLIC
```

## 9.23 `export_type`

```text
MARKDOWN
PDF
DOCX
```

## 9.24 `export_status`

```text
PENDING
COMPLETED
FAILED
EXPIRED
```

## 9.25 `referral_status`

```text
INVITED
SIGNED_UP
ACTIVATED
REWARDED
CANCELLED
FRAUD_REVIEW
```

## 9.26 `credit_transaction_type`

```text
REFERRAL_BONUS
SIGNUP_BONUS
PURCHASE
TRIAL_GRANT
USAGE_RESERVATION
USAGE_DEDUCTION
USAGE_REFUND
ADMIN_ADJUSTMENT
EXPIRY
```

## 9.27 `credit_transaction_status`

```text
RESERVED
CONFIRMED
REFUNDED
CANCELLED
EXPIRED
```

## 9.28 `credit_type`

```text
BASIC_BRIEF
DEEP_BRIEF
EXPORT_MARKDOWN
EXPORT_PDF
EXPORT_DOCX
GENERAL
```

## 9.29 `plan_limit_feature_code`

```text
TOTAL_BRIEF
BASIC_BRIEF
DEEP_BRIEF
EXPORT_MARKDOWN
EXPORT_PDF
EXPORT_DOCX
PREMIUM_CONTEXT
WATCHLIST
```

## 9.30 `limit_reset_period`

```text
DAILY
WEEKLY
MONTHLY
LIFETIME
NONE
```

---

# 10. Recommended Indexes

```sql
CREATE INDEX idx_sources_user_id ON sources(user_id);
CREATE INDEX idx_sources_source_type ON sources(source_type);
CREATE INDEX idx_sources_content_hash ON sources(content_hash);

CREATE INDEX idx_briefs_user_id ON briefs(user_id);
CREATE INDEX idx_briefs_source_id ON briefs(source_id);
CREATE INDEX idx_briefs_input_type ON briefs(input_type);
CREATE INDEX idx_briefs_status ON briefs(brief_status);
CREATE INDEX idx_briefs_created_at ON briefs(created_at);
CREATE INDEX idx_briefs_research_scope ON briefs(research_scope);

CREATE INDEX idx_brief_generation_jobs_brief_id ON brief_generation_jobs(brief_id);
CREATE INDEX idx_brief_generation_jobs_user_id ON brief_generation_jobs(user_id);
CREATE INDEX idx_brief_generation_jobs_status ON brief_generation_jobs(status);
CREATE INDEX idx_brief_generation_jobs_created_at ON brief_generation_jobs(created_at);

CREATE INDEX idx_research_channels_scope ON research_channels(research_scope);
CREATE INDEX idx_research_channels_type ON research_channels(channel_type);
CREATE INDEX idx_research_channels_active ON research_channels(active);

CREATE INDEX idx_brief_sources_brief_id ON brief_sources(brief_id);
CREATE INDEX idx_brief_sources_source_id ON brief_sources(source_id);
CREATE INDEX idx_brief_sources_channel_id ON brief_sources(research_channel_id);
CREATE INDEX idx_brief_sources_origin ON brief_sources(source_origin);
CREATE INDEX idx_brief_sources_usage_role ON brief_sources(usage_role);

CREATE INDEX idx_financial_entities_ticker ON financial_entities(ticker);
CREATE INDEX idx_financial_entities_name ON financial_entities(name);
CREATE INDEX idx_financial_entities_type ON financial_entities(entity_type);

CREATE INDEX idx_brief_entity_insights_brief_id ON brief_entity_insights(brief_id);
CREATE INDEX idx_brief_entity_insights_entity_id ON brief_entity_insights(entity_id);

CREATE INDEX idx_brief_events_brief_id ON brief_events(brief_id);
CREATE INDEX idx_brief_events_entity_id ON brief_events(entity_id);
CREATE INDEX idx_brief_events_event_type ON brief_events(event_type);
CREATE INDEX idx_brief_events_event_date ON brief_events(event_date);

CREATE INDEX idx_brief_claims_brief_id ON brief_claims(brief_id);
CREATE INDEX idx_brief_claims_event_id ON brief_claims(event_id);
CREATE INDEX idx_brief_claims_entity_id ON brief_claims(entity_id);
CREATE INDEX idx_brief_claims_support_status ON brief_claims(support_status);

CREATE INDEX idx_brief_citations_brief_id ON brief_citations(brief_id);
CREATE INDEX idx_brief_citations_claim_id ON brief_citations(claim_id);
CREATE INDEX idx_brief_citations_event_id ON brief_citations(event_id);
CREATE INDEX idx_brief_citations_entity_id ON brief_citations(entity_id);
CREATE INDEX idx_brief_citations_brief_source_id ON brief_citations(brief_source_id);

CREATE INDEX idx_external_context_items_brief_id ON external_context_items(brief_id);
CREATE INDEX idx_external_context_items_entity_id ON external_context_items(entity_id);
CREATE INDEX idx_external_context_items_context_type ON external_context_items(context_type);
CREATE INDEX idx_external_context_items_provider ON external_context_items(provider);
CREATE INDEX idx_external_context_items_published_at ON external_context_items(published_at);

CREATE INDEX idx_user_entitlements_user_id ON user_entitlements(user_id);
CREATE INDEX idx_user_entitlements_user_plan_status ON user_entitlements(user_id, plan_code, status);
CREATE INDEX idx_user_entitlements_active_window ON user_entitlements(starts_at, ends_at);

CREATE UNIQUE INDEX uq_promo_codes_code_hash ON promo_codes(code_hash);
CREATE INDEX idx_promo_codes_active ON promo_codes(active);
CREATE INDEX idx_promo_codes_expires_at ON promo_codes(expires_at);

CREATE INDEX idx_promo_redemptions_user_id ON promo_code_redemptions(user_id);
CREATE INDEX idx_promo_redemptions_promo_code_id ON promo_code_redemptions(promo_code_id);

CREATE UNIQUE INDEX uq_brief_shares_share_token ON brief_shares(share_token);
CREATE INDEX idx_brief_shares_brief_id ON brief_shares(brief_id);
CREATE INDEX idx_brief_shares_user_id ON brief_shares(user_id);
CREATE INDEX idx_brief_shares_visibility ON brief_shares(visibility);
CREATE INDEX idx_brief_shares_enabled ON brief_shares(enabled);

CREATE INDEX idx_brief_exports_brief_id ON brief_exports(brief_id);
CREATE INDEX idx_brief_exports_user_id ON brief_exports(user_id);
CREATE INDEX idx_brief_exports_status ON brief_exports(status);
CREATE INDEX idx_brief_exports_export_type ON brief_exports(export_type);

CREATE INDEX idx_referrals_referrer_user_id ON referrals(referrer_user_id);
CREATE INDEX idx_referrals_referred_user_id ON referrals(referred_user_id);
CREATE INDEX idx_referrals_referral_code ON referrals(referral_code);
CREATE INDEX idx_referrals_status ON referrals(status);

CREATE INDEX idx_credit_transactions_user_id ON credit_transactions(user_id);
CREATE INDEX idx_credit_transactions_credit_type ON credit_transactions(credit_type);
CREATE INDEX idx_credit_transactions_status ON credit_transactions(transaction_status);
CREATE UNIQUE INDEX uq_credit_transactions_idempotency_key ON credit_transactions(idempotency_key) WHERE idempotency_key IS NOT NULL;
CREATE INDEX idx_credit_transactions_source ON credit_transactions(source_type, source_id);
CREATE INDEX idx_credit_transactions_created_at ON credit_transactions(created_at);

CREATE INDEX idx_user_usage_daily_user_date ON user_usage_daily(user_id, usage_date);
CREATE UNIQUE INDEX uq_user_usage_daily_user_date ON user_usage_daily(user_id, usage_date);

CREATE INDEX idx_plan_limits_plan_code ON plan_limits(plan_code);
CREATE INDEX idx_plan_limits_feature_code ON plan_limits(feature_code);
CREATE UNIQUE INDEX uq_plan_limits_plan_feature_period ON plan_limits(plan_code, feature_code, reset_period) WHERE active = true;
```

---

# 11. Recommended Alembic Migration Order

```text
001_create_users
002_create_plans
003_create_plan_limits
004_create_user_entitlements
005_create_promo_codes
006_create_promo_code_redemptions
007_create_sources
008_create_briefs
009_create_brief_generation_jobs
010_create_research_channels
011_create_brief_sources
012_create_financial_entities
013_create_brief_entity_insights
014_create_brief_events
015_create_brief_claims
016_create_brief_citations
017_create_external_context_items
018_create_brief_shares
019_create_brief_exports
020_create_referrals
021_create_credit_transactions
022_create_user_usage_daily
023_create_indexes
```

### Practical note

Even though this is the v0.3 first milestone model, implementation can still be sliced internally:

```text
Foundation slice:
users, sources, briefs, jobs

Research slice:
brief_sources, research_channels, external_context_items

Analysis slice:
financial_entities, entity_insights, events, claims, citations

Commercial/control slice:
plans, entitlements, limits, credits, promo codes

Distribution slice:
shares, exports, referrals
```

This keeps v0.3 as one milestone while avoiding one horrifying mega-PR.

---

# 12. Brief Creation Flow

## 12.1 Source-Based Brief

```text
User submits article/video/PDF/text
→ create source
→ create brief with source_id
→ create generation job
→ extract source text
→ classify source
→ detect entities/events/claims
→ generate structured brief
→ persist generated_content and summary_markdown
```

## 12.2 Question-Based Brief

```text
User asks finance question
→ create brief with source_id = null
→ store question in user_query
→ create generation job
→ classify intent
→ detect entities/topics
→ retrieve context if allowed
→ generate structured brief
→ persist generated_content and summary_markdown
```

## 12.3 Mixed Brief

```text
User uploads source and asks a custom question
→ create source
→ create brief with source_id and user_query
→ process source and query together
→ retrieve extra context if allowed
→ generate structured brief
```

---

# 13. Shareable Brief Flow

Recommended endpoint:

```http
POST /api/v1/briefs/{briefId}/share
```

Backend flow:

```text
1. Verify current user owns the brief.
2. Verify brief status is COMPLETED.
3. Create unique share_token if no active share exists.
4. Set visibility to UNLISTED by default.
5. Return generated share URL.
```

Response:

```json
{
  "shareUrl": "https://alphabrief.ai/share/brf_9xK2pLmQ",
  "visibility": "UNLISTED",
  "allowDownload": false
}
```

Disable sharing:

```http
DELETE /api/v1/briefs/{briefId}/share
```

Public read endpoint:

```http
GET /api/v1/shared-briefs/{shareToken}
```

Public shared pages must not expose:

* private user data
* raw upload metadata
* internal model traces
* internal trust tiers
* paid-only private context unless intentionally included

---

# 14. Download / Export Flow

For Markdown:

```http
GET /api/v1/briefs/{briefId}/download?type=MARKDOWN
```

For PDF/DOCX:

```http
POST /api/v1/briefs/{briefId}/exports
```

Request:

```json
{
  "type": "PDF"
}
```

Backend flow:

```text
1. Verify access.
2. Create brief_export with PENDING status.
3. Generate export from summary_markdown or generated_content.
4. Store file if needed.
5. Mark export COMPLETED.
6. Return download URL or export status.
```

---

# 15. Referral Reward Flow

Recommended endpoints:

```http
GET /api/v1/me/referral-code
POST /api/v1/referrals/apply
GET /api/v1/me/referrals
```

Suggested flow:

```text
1. Existing user shares referral_code.
2. New user signs up with referral_code.
3. Create referral with SIGNED_UP status.
4. When referred user generates first completed brief, mark referral ACTIVATED.
5. Create credit_transactions for rewards.
6. Mark referral REWARDED.
```

---

# 16. Beta Tester / Trial Usage Control Flow

Recommended setup:

```text
plans:
BETA_TESTER

user_entitlements:
plan_code = BETA_TESTER
source_type = TRIAL
status = ACTIVE

plan_limits:
BETA_TESTER + DEEP_BRIEF + 2 + LIFETIME
```

Alternative:

```text
credit_transactions:
credit_type = DEEP_BRIEF
amount = +2
transaction_type = TRIAL_GRANT
transaction_status = CONFIRMED
source_type = USER_ENTITLEMENT
source_id = user_entitlements.id
```

Deep brief generation should check:

```text
1. Does user have active entitlement?
2. Does user have remaining quota or credits?
3. Reserve or deduct 1 DEEP_BRIEF.
4. Generate brief.
5. Confirm deduction if successful.
6. Refund/cancel if failed before usable output.
```

---

# 17. Deep Brief Analysis Pipeline

A deep brief should use a pipeline, not one giant prompt.

Recommended pipeline:

```text
1. Validate input
2. Create source if needed
3. Create brief
4. Create generation job
5. Extract/transcribe source content if applicable
6. Clean content
7. Classify request intent
8. Detect financial entities
9. Detect events
10. Extract claims
11. Resolve research scope
12. Retrieve external context
13. Generate structured analysis
14. Verify claims against evidence where possible
15. Persist brief sources, events, claims, citations, entity insights, and generated content
16. Render summary_markdown
17. Mark brief completed
```

This supports AlphaBrief's core differentiation:

```text
It does not only summarise financial information.
It explains what happened, why it matters, what it affects, and what to research next.
```

---

# 18. Promo Code Redemption Flow

Recommended endpoint:

```http
POST /api/v1/subscription/redeem-promo-code
```

Request:

```json
{
  "code": "ALPHA-BETA-2026"
}
```

Backend flow:

```text
1. Normalize submitted code.
2. Hash normalized code.
3. Find promo code by code_hash.
4. Validate active status.
5. Validate starts_at and expires_at.
6. Validate max_redemptions.
7. Validate max_redemptions_per_user.
8. Check whether user already has equal or better access.
9. Create user_entitlement.
10. Create promo_code_redemption.
11. Increment promo_codes.current_redemptions.
12. Return updated subscription status.
```

Concurrency requirement:

```sql
SELECT *
FROM promo_codes
WHERE code_hash = :code_hash
FOR UPDATE;
```

---

# 19. Access Checking

Premium feature access should check active entitlements, not payment records directly.

Pseudo logic:

```text
function hasProAccess(userId):
    return exists user_entitlements
    where user_id = userId
    and plan_code in ('PRO', 'STUDENT_PRO', 'ADMIN')
    and status = 'ACTIVE'
    and starts_at <= now
    and (ends_at is null or ends_at > now)
```

Free access can be treated as the default if no Pro/Admin entitlement exists.

---

# 20. Effective Subscription Status Response

Example backend response:

```json
{
  "effectivePlanCode": "PRO",
  "accessSource": "PROMO_CODE",
  "startsAt": "2026-04-29T00:00:00Z",
  "endsAt": "2026-05-29T00:00:00Z",
  "dailyBriefLimit": 50,
  "briefsUsedToday": 2,
  "deepBriefsRemaining": 8,
  "premiumContextEnabled": true
}
```

This can power frontend subscription, usage, and gating UI.

---

# 21. v0.3 Implementation Slices

Even though v0.3 is the first milestone, implementation should still be sliced.

## Slice A: Core Brief Foundation

Build:

```text
users
sources
briefs
brief_generation_jobs
basic structured generated_content
summary_markdown
```

Supports:

```text
article URL → brief
YouTube URL → brief
PDF upload → brief
pasted text → brief
direct finance question → brief
```

## Slice B: Source and Research Traceability

Build:

```text
research_channels
brief_sources
external_context_items
```

Supports:

```text
agent-discovered sources
source evidence panel
research scope
source category labels
```

## Slice C: Finance Intelligence Layer

Build:

```text
financial_entities
brief_entity_insights
brief_events
brief_claims
brief_citations
```

Supports:

```text
implication map
claim extraction
claim support status
event-to-entity reasoning
citations
contradiction detection
```

## Slice D: Usage and Access Control

Build:

```text
plans
user_entitlements
plan_limits
user_usage_daily
credit_transactions
promo_codes
promo_code_redemptions
```

Supports:

```text
free/pro/student/beta tester access
usage limits
cost control
promo access
trial access
```

## Slice E: Distribution and Growth

Build:

```text
brief_shares
brief_exports
referrals
```

Supports:

```text
shareable briefs
downloadable briefs
referral rewards
```

---

# 22. Critical Editor Review

## 22.1 v0.3 as first milestone is ambitious

This model is intentionally broad. It supports the full early product vision, but implementing all tables before testing the product could slow development.

Recommendation:

```text
Keep v0.3 as the first milestone, but implement it through internal slices.
```

Do not make one enormous migration and one enormous PR unless the goal is to create a debugging swamp.

## 22.2 Brief must remain central

The most important architecture correction is:

```text
Brief is the central product artifact.
Source is optional input.
```

This supports:

```text
source-based brief
question-based brief
mixed brief
agent-discovered-source brief
```

## 22.3 JSONB should carry early feature experimentation

Unique AlphaBrief features such as:

```text
So What?
Implication Map
Bull/Bear/Neutral
Finance Concepts
Assignment Angles
Research Path
What Would Change This View?
```

should start inside `generated_content`.

Only normalize later if the data needs:

```text
search
filtering
comparison
analytics
cross-brief tracking
```

## 22.4 AI quality depends on pipeline quality

The data model supports high-quality analysis, but does not guarantee it.

Quality depends on:

* source extraction quality
* financial entity resolution
* retrieval quality
* prompt/schema design
* citation quality
* verification pass quality
* cost limits
* latency tolerance

A table named `brief_claims` does not magically create reliable research. The pipeline must earn that reliability.

## 22.5 Source trust must stay carefully framed

Do not expose internal trust tiers publicly.

Use safe public labels:

```text
Official Source
Established Financial Media
Market Commentary
Public Discussion
User-Provided Source
```

Avoid public labels like:

```text
Publisher X = low trust
Channel Y = Tier 3
```

## 22.6 Student pricing should not be rushed

`STUDENT_PRO` is useful for future positioning, but verification can wait.

Do not implement `education_verifications` until student pricing is close to launch.

## 22.7 Shareable briefs need privacy filtering

A public shared brief should use a safe public view model.

Do not dump raw `generated_content`, model traces, upload metadata, or private notes directly into the public page.

## 22.8 Anti-abuse is not fully modeled

Referral and credit systems invite abuse.

Future additions may include:

```text
email verification
account verification status
suspicious referral flags
rate limit records
IP/device heuristics
admin review workflow
```

For v0.3, keep reward rules conservative.

---

# 23. Final Recommendation

Use this model for AlphaBrief v0.3 first milestone:

```text
User
→ owns Briefs
→ may submit Sources
→ may have Entitlements
→ may consume Usage/Credits

Brief
→ is the central artifact
→ may or may not have a Source
→ stores structured generated_content
→ may use BriefSources, Events, Claims, Citations, EntityInsights, and ExternalContextItems
→ may be shared or exported

Source
→ stores user-provided material only
→ does not represent direct finance questions

BriefSource
→ stores all sources used in final analysis
→ includes user-provided and agent-discovered sources

Entitlements + Limits + Credits
→ control access and usage
→ prevent AI cost chaos
```

The most important architectural rule:

```text
Do not force every brief to belong to a source.
```

The most important product rule:

```text
AlphaBrief should not only summarise finance content.
It should explain implications, risks, evidence, and what to research next.
```
