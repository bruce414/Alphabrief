# Alphabrief v0.3 Data Model

## Version

`v0.3 MVP`

## Status

Refined after adding entitlement-based subscriptions and promo-code access.

---

## 1. Database

Recommended database:

```text
PostgreSQL
```

PostgreSQL is suitable for Alphabrief because the product needs:

- Relational ownership rules, such as users owning sources and briefs
- Transactional subscription and promo-code redemption logic
- JSONB fields for structured AI output
- Indexing for brief history, entity lookup, and usage limits

---

## 2. Core Design Principles

For v0.3, the data model should stay simple but not paint the product into a corner.

Important principles:

1. Use relational tables for ownership, subscriptions, promo codes, usage limits, and entities.
2. Use `JSONB` for flexible AI-generated arrays and structured sections.
3. Do not store premium access only as a single field on `users`.
4. Model access through `user_entitlements`.
5. Treat promo codes as one way to create Pro access, not as the subscription system itself.
6. Keep AI output structured enough that the frontend does not need to parse one giant text blob.

---

## 3. Core Entities

The v0.3 data model should support:

- Users
- Sources
- Briefs
- Financial entities
- Entity insights
- Plans
- User entitlements
- Promo codes
- Promo code redemptions
- Usage limits

---

## 4. Entity Relationship Overview

```text
User
 ├── Source
 │    └── Brief
 │         └── BriefEntityInsight
 │              └── FinancialEntity
 │
 ├── UserEntitlement
 │    └── Plan
 │
 ├── PromoCodeRedemption
 │    ├── PromoCode
 │    └── UserEntitlement
 │
 └── UserUsageDaily
```

Access model:

```text
Plan = what product tier exists
UserEntitlement = what access a user currently has
PromoCode = one possible way to create an entitlement
Payment = another possible way to create an entitlement later
```

---

# 5. Tables

---

## 5.1 `users`

Represents a registered user.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| email | VARCHAR(255) | Unique, required |
| password_hash | VARCHAR(255) | Nullable if using OAuth-only auth |
| display_name | VARCHAR(120) | Optional |
| role | VARCHAR(50) | USER, ADMIN |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### Notes

Do **not** rely on `users.subscription_tier` as the source of truth.

A cached field such as `current_plan_code` can be added later for performance, but the real access should come from `user_entitlements`.

### Recommended constraints

```sql
ALTER TABLE users
ADD CONSTRAINT uq_users_email UNIQUE (email);
```

---

## 5.2 `plans`

Defines available product plans.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| code | VARCHAR(50) | Unique, e.g. FREE, PRO, ADMIN |
| name | VARCHAR(100) | Human-readable name |
| description | TEXT | Optional |
| active | BOOLEAN | Required, default true |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### Example plan codes

```text
FREE
PRO
ADMIN
```

### Notes

For v0.3, this could technically be an enum. However, a `plans` table gives more flexibility once pricing, trial plans, beta plans, or student plans are added.

---

## 5.3 `user_entitlements`

Represents a user's active, expired, revoked, or cancelled access.

This is the central table for deciding whether a user has Pro access.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| plan_code | VARCHAR(50) | FREE, PRO, ADMIN |
| source_type | VARCHAR(50) | FREE_DEFAULT, PROMO_CODE, PAID_SUBSCRIPTION, ADMIN_GRANT, TRIAL |
| source_id | UUID | Nullable reference to redemption/payment/admin grant |
| status | VARCHAR(50) | ACTIVE, EXPIRED, REVOKED, CANCELLED |
| starts_at | TIMESTAMP | Required |
| ends_at | TIMESTAMP | Nullable for no fixed end date |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### Source type values

```text
FREE_DEFAULT
PROMO_CODE
PAID_SUBSCRIPTION
ADMIN_GRANT
TRIAL
```

### Status values

```text
ACTIVE
EXPIRED
REVOKED
CANCELLED
```

### Access rule

A user has access to a plan if they have an entitlement where:

```text
user_id = current user
plan_code = required plan
status = ACTIVE
starts_at <= now
ends_at IS NULL OR ends_at > now
```

### Example

```text
user_id = 123
plan_code = PRO
source_type = PROMO_CODE
source_id = promo_code_redemption.id
status = ACTIVE
starts_at = 2026-04-29T00:00:00Z
ends_at = 2026-05-29T00:00:00Z
```

This means the user has Pro access until May 29, 2026 because they redeemed a promo code.

---

## 5.4 `promo_codes`

Stores promo codes that can grant temporary or permanent access.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| code_hash | VARCHAR(255) | Hash of normalized promo code |
| display_code_suffix | VARCHAR(12) | Last few chars for admin/debug display |
| plan_code | VARCHAR(50) | Plan granted by this code, usually PRO |
| duration_days | INTEGER | Nullable. If null, grant can be open-ended |
| max_redemptions | INTEGER | Nullable for unlimited |
| current_redemptions | INTEGER | Required, default 0 |
| max_redemptions_per_user | INTEGER | Required, usually 1 |
| starts_at | TIMESTAMP | Nullable |
| expires_at | TIMESTAMP | Nullable |
| active | BOOLEAN | Required, default true |
| created_by | UUID | Nullable FK to users/admin |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### Notes

Promo codes should ideally not be stored in plain text.

Recommended flow:

```text
User enters code
→ Normalize code
→ Hash normalized code
→ Compare with code_hash
```

For MVP, storing plain text is possible if the risk is low, but hashing is cleaner.

### Promo code examples

```text
ALPHA-BETA-2026
FOUNDER-PRO-30
UOA-FINTECH-ACCESS
```

Store only the hash, not the raw code.

---

## 5.5 `promo_code_redemptions`

Tracks which users redeemed which promo codes.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| promo_code_id | UUID | FK to promo_codes |
| user_id | UUID | FK to users |
| entitlement_id | UUID | FK to user_entitlements |
| redeemed_at | TIMESTAMP | Required |
| status | VARCHAR(50) | REDEEMED, REVOKED |

### Status values

```text
REDEEMED
REVOKED
```

### Recommended constraint

For most promo codes, prevent the same user redeeming the same code multiple times:

```sql
ALTER TABLE promo_code_redemptions
ADD CONSTRAINT uq_promo_redemptions_code_user
UNIQUE (promo_code_id, user_id);
```

If you later support reusable codes for the same user, remove or adjust this constraint and enforce limits through business logic.

---

## 5.6 `sources`

Represents the original user input and extracted content.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| source_type | VARCHAR(50) | ARTICLE_URL, YOUTUBE_URL, PASTED_TEXT |
| original_input | TEXT | Original URL or pasted text |
| normalized_url | TEXT | Nullable |
| title | TEXT | Nullable |
| raw_text | TEXT | Extracted or cleaned text |
| extraction_status | VARCHAR(50) | PENDING, EXTRACTED, FAILED |
| extraction_error | TEXT | Nullable |
| content_hash | VARCHAR(255) | Optional, useful for deduplication |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### Source type values

```text
ARTICLE_URL
YOUTUBE_URL
PASTED_TEXT
```

### Extraction status values

```text
PENDING
EXTRACTED
FAILED
```

---

## 5.7 `briefs`

Represents the generated AI brief.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| source_id | UUID | FK to sources |
| title | TEXT | Brief title |
| brief_status | VARCHAR(50) | QUEUED, PROCESSING, COMPLETED, FAILED |
| plan_code_used | VARCHAR(50) | FREE or PRO |
| requested_depth | VARCHAR(50) | AUTO, BASIC, DEEP |
| source_summary | TEXT | Main source summary |
| key_takeaways | JSONB | Array of strings |
| risks | JSONB | Array of strings |
| opportunities | JSONB | Array of strings |
| investor_questions | JSONB | Array of strings |
| disclaimer | TEXT | Required |
| model_provider | VARCHAR(100) | Optional |
| model_name | VARCHAR(100) | Optional |
| prompt_version | VARCHAR(50) | Optional |
| generation_error | TEXT | Nullable |
| generated_at | TIMESTAMP | Nullable |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

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

### Notes

`plan_code_used` captures what access level was used at generation time.

Example:

```text
User currently has PRO because of a promo code.
Brief is generated with PRO context.
Later the promo expires.
The brief still says plan_code_used = PRO.
```

This is useful for auditing and future product logic.

---

## 5.8 `financial_entities`

Represents a detected company, ticker, sector, asset, index, or macro factor.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| name | VARCHAR(255) | Required |
| ticker | VARCHAR(50) | Nullable |
| exchange | VARCHAR(50) | Nullable |
| entity_type | VARCHAR(50) | Required |
| country | VARCHAR(100) | Nullable |
| sector | VARCHAR(100) | Nullable |
| industry | VARCHAR(150) | Nullable |
| external_provider | VARCHAR(100) | Nullable |
| external_id | VARCHAR(150) | Nullable |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

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
UNKNOWN
```

### Notes

The same company may have multiple tickers or listings in the future. For v0.3, a simple entity model is enough.

If this becomes a serious financial data platform later, entity normalization may need its own module.

---

## 5.9 `brief_entity_insights`

Represents analysis for one financial entity within one brief.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| brief_id | UUID | FK to briefs |
| entity_id | UUID | FK to financial_entities |
| source_specific_insight | TEXT | What the source says |
| company_context | TEXT | Basic context |
| industry_context | TEXT | Premium context |
| macro_context | TEXT | Premium context |
| political_regulatory_context | TEXT | Premium context |
| competitor_context | TEXT | Premium context |
| risk_factors | JSONB | Array of strings |
| opportunity_factors | JSONB | Array of strings |
| premium_only | BOOLEAN | Whether this insight is premium-only |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### Free vs Pro behavior

Free users should usually receive:

- `source_specific_insight`
- `company_context`
- `risk_factors`

Pro users may additionally receive:

- `industry_context`
- `macro_context`
- `political_regulatory_context`
- `competitor_context`
- deeper risk/opportunity factors

---

## 5.10 `user_usage_daily`

Tracks daily usage for cost control.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| usage_date | DATE | Required |
| plan_code_at_usage | VARCHAR(50) | FREE or PRO |
| brief_count | INTEGER | Number of briefs generated |
| ai_input_token_estimate | INTEGER | Optional |
| ai_output_token_estimate | INTEGER | Optional |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### Recommended unique constraint

```sql
ALTER TABLE user_usage_daily
ADD CONSTRAINT uq_user_usage_daily_user_date
UNIQUE (user_id, usage_date);
```

### Notes

Usage limits should be checked against the user's current effective plan.

Suggested limits:

| Feature | Free | Pro |
|---|---:|---:|
| Briefs per day | 3 | 50 |
| Pasted text length | 8,000 characters | 30,000 characters |
| Saved brief history | 20 briefs | High or unlimited |
| Premium external context | No | Yes |

---

# 6. Optional Future Tables

These are not required for v0.3 but are likely useful later.

---

## 6.1 `paid_subscriptions`

Use this later when adding Stripe or another payment provider.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| provider | VARCHAR(50) | STRIPE, etc. |
| provider_customer_id | VARCHAR(255) | External customer ID |
| provider_subscription_id | VARCHAR(255) | External subscription ID |
| plan_code | VARCHAR(50) | PRO |
| status | VARCHAR(50) | ACTIVE, PAST_DUE, CANCELLED, EXPIRED |
| current_period_start | TIMESTAMP | Nullable |
| current_period_end | TIMESTAMP | Nullable |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

When payment is added, successful payment should create or update a `user_entitlements` row.

---

## 6.2 `admin_grants`

Use this later if admins need to manually grant access with reasons.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| granted_by | UUID | FK to users/admin |
| plan_code | VARCHAR(50) | PRO or ADMIN |
| reason | TEXT | Optional |
| starts_at | TIMESTAMP | Required |
| ends_at | TIMESTAMP | Nullable |
| created_at | TIMESTAMP | Required |

Admin grants should also create a `user_entitlements` row.

---

## `brief_generation_jobs`

Tracks the async or step-by-step generation process for a brief.

This table is especially useful if brief generation is handled by a background worker or if the frontend polls for status.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| brief_id | UUID | FK to briefs |
| user_id | UUID | FK to users |
| status | VARCHAR(50) | QUEUED, RUNNING, COMPLETED, FAILED, RETRYING, CANCELLED |
| current_step | VARCHAR(80) | Current pipeline step |
| retry_count | INTEGER | Required, default 0 |
| max_retries | INTEGER | Required, default 3 |
| error_code | VARCHAR(100) | Nullable |
| error_message | TEXT | Nullable |
| started_at | TIMESTAMP | Nullable |
| completed_at | TIMESTAMP | Nullable |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### Status values

```text
QUEUED
RUNNING
COMPLETED
FAILED
RETRYING
CANCELLED
```

### Current step values

```text
VALIDATING_INPUT
EXTRACTING_SOURCE
CLEANING_CONTENT
DETECTING_ENTITIES
RETRIEVING_CONTEXT
GENERATING_BRIEF
VALIDATING_OUTPUT
PERSISTING_RESULT
COMPLETED
FAILED
```

### Notes

`brief_generation_jobs` should be created when a user submits a new brief request.

Recommended flow:

```text
POST /api/v1/briefs
→ create source
→ create brief with status QUEUED
→ create brief_generation_job with status QUEUED
→ return briefId to frontend
→ background worker processes job
→ frontend polls GET /api/v1/briefs/{briefId}
```

If generation is synchronous in early v0.3, this table can still be useful for debugging and future migration to async processing.

---

## `external_context_items`

Stores external data used to enrich a brief, especially for Pro users.

This table helps with traceability, debugging, and future citation/explainability features.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| brief_id | UUID | FK to briefs |
| entity_id | UUID | Nullable FK to financial_entities |
| context_type | VARCHAR(80) | NEWS, COMPANY_PROFILE, MARKET_DATA, INDUSTRY_CONTEXT, MACRO_CONTEXT, REGULATORY_CONTEXT, COMPETITOR_CONTEXT |
| provider | VARCHAR(100) | External data provider or internal source |
| title | TEXT | Nullable |
| url | TEXT | Nullable |
| published_at | TIMESTAMP | Nullable |
| snippet | TEXT | Nullable |
| raw_payload | JSONB | Optional raw/structured provider response |
| used_in_prompt | BOOLEAN | Required, default true |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

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
UNKNOWN
```

### Notes

`external_context_items` should store the supporting information retrieved before AI generation.

Examples:

```text
A recent news article about Apple
A company profile for Nvidia
A market data snapshot for Tesla
A regulatory update affecting big tech
A macro note about interest rates
```

For free-tier briefs, this table may contain only basic company/entity context.

For Pro-tier briefs, it can store richer context such as:

```text
Industry trends
Competitor movement
Macro factors
Political/regulatory factors
Market sentiment
Earnings context
```

`raw_payload` should be used carefully. Avoid storing unnecessarily large provider responses or sensitive content.

---

# 7. Enums

## 7.1 `role`

```text
USER
ADMIN
```

## 7.2 `plan_code`

```text
FREE
PRO
ADMIN
```

## 7.3 `entitlement_source_type`

```text
FREE_DEFAULT
PROMO_CODE
PAID_SUBSCRIPTION
ADMIN_GRANT
TRIAL
```

## 7.4 `entitlement_status`

```text
ACTIVE
EXPIRED
REVOKED
CANCELLED
```

## 7.5 `promo_redemption_status`

```text
REDEEMED
REVOKED
```

## 7.6 `source_type`

```text
ARTICLE_URL
YOUTUBE_URL
PASTED_TEXT
```

## 7.7 `extraction_status`

```text
PENDING
EXTRACTED
FAILED
```

## 7.8 `brief_status`

```text
QUEUED
PROCESSING
COMPLETED
FAILED
```

## 7.9 `requested_depth`

```text
AUTO
BASIC
DEEP
```

## 7.10 `entity_type`

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
UNKNOWN
```

---

# 8. Recommended Indexes

```sql
CREATE INDEX idx_sources_user_id ON sources(user_id);
CREATE INDEX idx_sources_source_type ON sources(source_type);
CREATE INDEX idx_sources_content_hash ON sources(content_hash);

CREATE INDEX idx_briefs_user_id ON briefs(user_id);
CREATE INDEX idx_briefs_source_id ON briefs(source_id);
CREATE INDEX idx_briefs_status ON briefs(brief_status);
CREATE INDEX idx_briefs_created_at ON briefs(created_at);

CREATE INDEX idx_financial_entities_ticker ON financial_entities(ticker);
CREATE INDEX idx_financial_entities_name ON financial_entities(name);
CREATE INDEX idx_financial_entities_type ON financial_entities(entity_type);

CREATE INDEX idx_brief_entity_insights_brief_id ON brief_entity_insights(brief_id);
CREATE INDEX idx_brief_entity_insights_entity_id ON brief_entity_insights(entity_id);

CREATE INDEX idx_user_entitlements_user_id ON user_entitlements(user_id);
CREATE INDEX idx_user_entitlements_user_plan_status ON user_entitlements(user_id, plan_code, status);
CREATE INDEX idx_user_entitlements_active_window ON user_entitlements(starts_at, ends_at);

CREATE UNIQUE INDEX uq_promo_codes_code_hash ON promo_codes(code_hash);
CREATE INDEX idx_promo_codes_active ON promo_codes(active);
CREATE INDEX idx_promo_codes_expires_at ON promo_codes(expires_at);

CREATE INDEX idx_promo_redemptions_user_id ON promo_code_redemptions(user_id);
CREATE INDEX idx_promo_redemptions_promo_code_id ON promo_code_redemptions(promo_code_id);

CREATE INDEX idx_user_usage_daily_user_date ON user_usage_daily(user_id, usage_date);

CREATE INDEX idx_brief_generation_jobs_brief_id ON brief_generation_jobs(brief_id);
CREATE INDEX idx_brief_generation_jobs_user_id ON brief_generation_jobs(user_id);
CREATE INDEX idx_brief_generation_jobs_status ON brief_generation_jobs(status);
CREATE INDEX idx_brief_generation_jobs_created_at ON brief_generation_jobs(created_at);

CREATE INDEX idx_external_context_items_brief_id ON external_context_items(brief_id);
CREATE INDEX idx_external_context_items_entity_id ON external_context_items(entity_id);
CREATE INDEX idx_external_context_items_context_type ON external_context_items(context_type);
CREATE INDEX idx_external_context_items_provider ON external_context_items(provider);
CREATE INDEX idx_external_context_items_published_at ON external_context_items(published_at);
```

---

# 9. Promo Code Redemption Flow

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
1. Normalize submitted code
2. Hash normalized code
3. Find promo code by code_hash
4. Validate active status
5. Validate starts_at and expires_at
6. Validate max_redemptions
7. Validate max_redemptions_per_user
8. Check whether user already has equal or better active access
9. Create user_entitlement
10. Create promo_code_redemption
11. Increment promo_codes.current_redemptions
12. Return updated subscription status
```

Response:

```json
{
  "success": true,
  "planCode": "PRO",
  "accessSource": "PROMO_CODE",
  "startsAt": "2026-04-29T00:00:00Z",
  "endsAt": "2026-05-29T00:00:00Z",
  "message": "Promo code redeemed successfully. Pro access is now active."
}
```

---

# 10. Promo Code Error Codes

```text
PROMO_CODE_INVALID
PROMO_CODE_INACTIVE
PROMO_CODE_NOT_STARTED
PROMO_CODE_EXPIRED
PROMO_CODE_FULLY_REDEEMED
PROMO_CODE_ALREADY_USED
USER_ALREADY_HAS_PRO
PROMO_CODE_REDEMPTION_FAILED
```

---

# 11. Concurrency Requirement

Promo code redemption should be transactional.

Reason:

```text
If a promo code only has 1 redemption left, two users should not both be able to redeem it at the same time.
```

Recommended behavior:

```text
Start transaction
Lock promo code row
Validate redemption availability
Create entitlement
Create redemption record
Increment current_redemptions
Commit transaction
```

In SQL terms, this can be done with row-level locking:

```sql
SELECT *
FROM promo_codes
WHERE code_hash = :code_hash
FOR UPDATE;
```

---

# 12. Access Checking

Premium feature access should check active entitlements, not payment records directly.

Pseudo logic:

```text
function hasProAccess(userId):
    return exists user_entitlements
    where user_id = userId
    and plan_code in ('PRO', 'ADMIN')
    and status = 'ACTIVE'
    and starts_at <= now
    and (ends_at is null or ends_at > now)
```

Free access can be treated as the default if no Pro/Admin entitlement exists.

---

# 13. Effective Subscription Status

The backend should expose a subscription status response such as:

```json
{
  "effectivePlanCode": "PRO",
  "accessSource": "PROMO_CODE",
  "startsAt": "2026-04-29T00:00:00Z",
  "endsAt": "2026-05-29T00:00:00Z",
  "dailyBriefLimit": 50,
  "briefsUsedToday": 2,
  "premiumContextEnabled": true
}
```

This can power the frontend subscription page and premium gating UI.

---

# 14. Migration Order

Suggested Flyway or Alembic migration order:

```text
001_create_users
002_create_plans
003_create_user_entitlements
004_create_promo_codes
005_create_promo_code_redemptions
006_create_sources
007_create_briefs
008_create_financial_entities
009_create_brief_entity_insights
010_create_user_usage_daily
011_create_indexes
```

If using Java + Spring Boot, Flyway is a strong fit.

If using Python + FastAPI, Alembic is the more common migration tool.

---

# 15. v0.3 Simplification Option

If implementation speed is more important than long-term flexibility, the absolute simplest version is:

```text
users
- subscription_tier
- subscription_source
- subscription_expires_at

promo_codes
promo_code_redemptions
```

However, the recommended v0.3 design is still `user_entitlements`, because it keeps promo access, paid subscriptions, admin grants, and trials under the same access model.

This avoids painful rewrites later.

---

# 16. Final Recommendation

Use this model:

```text
User
→ has many UserEntitlements
→ effective access is calculated from active entitlements
→ promo codes create entitlements
→ paid subscriptions later create entitlements too
```

This keeps Alphabrief flexible without overbuilding.

The subscription wall should not ask:

```text
Did this user pay?
```

It should ask:

```text
Does this user have active Pro access right now?
```
