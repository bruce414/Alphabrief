# Alphabrief v0.3 Data Model

## Version

`v0.3 MVP`

## Status

Refined after adding entitlement-based subscriptions, promo-code access, shareable/downloadable briefs, referral rewards, event-level AI analysis support, beta tester quotas, student pricing readiness, and internal token/cost tracking.

---

## 1. Database

Recommended database:

```text
PostgreSQL
```

PostgreSQL is suitable for Alphabrief because the product needs:

- Relational ownership rules, such as users owning sources and briefs
- Transactional subscription, promo-code redemption, referral, credit, and quota logic
- JSONB fields for structured AI output
- Indexing for brief history, entity lookup, event lookup, sharing, exports, and usage limits

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
7. Store share tokens/slugs instead of full share URLs so domains can change safely.
8. Model downloadable exports separately from briefs instead of storing PDF/DOCX files inside the brief row.
9. Model referrals and rewards as separate transactional records instead of storing a `referral_list` directly on `users`.
10. Capture financial events, claims, and citations separately enough to support deeper research, verification, and future "what changed" features.
11. Separate access from usage. `user_entitlements` decides what a user is allowed to access; `plan_limits`, `user_usage_daily`, and `credit_transactions` decide how much they can use.
12. Treat student pricing as a plan or verified discount path, not as an entitlement source type by default.
13. Track token and estimated cost internally from v0.3, even if users only see simple brief-count limits.
14. Design beta/testing access with explicit quotas so test users cannot accidentally burn AI budget.

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
- Plan limits
- Brief shares
- Brief exports
- Referrals
- Credit transactions
- Beta/tester credits
- Brief events
- Brief claims
- Brief citations

---

## 4. Entity Relationship Overview

```text
User
 ├── Source
 │    └── Brief
 │         ├── BriefEntityInsight
 │         │    └── FinancialEntity
 │         ├── BriefEvent
 │         │    └── FinancialEntity
 │         ├── BriefClaim
 │         │    └── BriefCitation
 │         ├── BriefShare
 │         └── BriefExport
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

Access model:

```text
Plan = what product tier exists
UserEntitlement = what access a user currently has
PromoCode = one possible way to create an entitlement
Payment = another possible way to create an entitlement later
PlanLimit = reusable default usage rules for each plan
CreditTransaction = extra grants, referral rewards, deductions, and reservations
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
| referral_code | VARCHAR(50) | Unique user-owned referral code |
| referred_by_user_id | UUID | Nullable FK to users; who referred this user |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### Notes

Do **not** rely on `users.subscription_tier` as the source of truth.

A cached field such as `current_plan_code` can be added later for performance, but the real access should come from `user_entitlements`.

### Recommended constraints

```sql
ALTER TABLE users
ADD CONSTRAINT uq_users_email UNIQUE (email);

ALTER TABLE users
ADD CONSTRAINT uq_users_referral_code UNIQUE (referral_code);
```

---

## 5.2 `plans`

Defines available product plans.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| code | VARCHAR(50) | Unique, e.g. FREE, PRO, STUDENT_PRO, BETA_TESTER, ADMIN |
| name | VARCHAR(100) | Human-readable name |
| description | TEXT | Optional |
| active | BOOLEAN | Required, default true |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### Example plan codes

```text
FREE
PRO
STUDENT_PRO
BETA_TESTER
ADMIN
```

### Notes

For v0.3, this could technically be an enum. However, a `plans` table gives more flexibility once pricing, trial plans, beta plans, student plans, creator plans, or admin-only plans are added.

Student pricing should normally be represented as a plan such as `STUDENT_PRO`, not as `user_entitlements.source_type = STUDENT`.

Why:

```text
plan_code = what access/package the user has
source_type = how that access was granted
```

Example:

```text
plan_code = STUDENT_PRO
source_type = PAID_SUBSCRIPTION
```

or, if access is granted after verification without immediate payment:

```text
plan_code = STUDENT_PRO
source_type = EDUCATION_VERIFICATION
```

---

## 5.3 `user_entitlements`

Represents a user's active, expired, revoked, or cancelled access.

This is the central table for deciding whether a user has Pro access.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| plan_code | VARCHAR(50) | FREE, PRO, STUDENT_PRO, BETA_TESTER, ADMIN |
| source_type | VARCHAR(50) | FREE_DEFAULT, PROMO_CODE, PAID_SUBSCRIPTION, ADMIN_GRANT, TRIAL, EDUCATION_VERIFICATION |
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
EDUCATION_VERIFICATION
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

### Important separation

Do not use `source_type` to store every commercial segment. For example, do not default to `source_type = STUDENT` just because a user has student pricing. Use `plan_code = STUDENT_PRO`, then use `source_type` to record whether access came from payment, trial, promo code, education verification, or admin grant.

For beta testers, use something like:

```text
plan_code = BETA_TESTER
source_type = TRIAL
```

Then enforce the 2-deep-brief testing limit through `plan_limits`, `credit_transactions`, or both. Entitlements grant access; quotas control cost.

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
| bull_case | JSONB | Array of strings or structured points |
| bear_case | JSONB | Array of strings or structured points |
| confidence_score | NUMERIC(5,2) | Optional 0-100 score |
| confidence_explanation | TEXT | Explains why confidence is high/medium/low |
| generated_content | JSONB | Full structured AI output for flexible rendering |
| summary_markdown | TEXT | Renderable/exportable markdown version |
| disclaimer | TEXT | Required |
| model_provider | VARCHAR(100) | Optional |
| model_name | VARCHAR(100) | Optional |
| prompt_version | VARCHAR(50) | Optional |
| research_pipeline_version | VARCHAR(50) | Optional, useful when deep-analysis workflow changes |
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

## 5.10 `brief_events`

Represents a financial, market, company, political, regulatory, macro, or industry event identified inside the source or retrieved context.

This table is important for deeper AlphaBrief analysis because a single source can mention multiple entities and multiple events.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| brief_id | UUID | FK to briefs |
| entity_id | UUID | Nullable FK to financial_entities |
| event_type | VARCHAR(80) | EARNINGS, TARIFF, REGULATION, PRODUCT_LAUNCH, MACRO, etc. |
| title | TEXT | Short event title |
| event_date | DATE | Nullable if unknown |
| description | TEXT | Event summary |
| source_origin | VARCHAR(50) | SOURCE_MENTIONED, EXTERNAL_CONTEXT, MODEL_INFERRED |
| impact_direction | VARCHAR(50) | POSITIVE, NEGATIVE, MIXED, UNCLEAR |
| impact_magnitude | VARCHAR(50) | LOW, MEDIUM, HIGH, UNKNOWN |
| confidence_score | NUMERIC(5,2) | Optional 0-100 score |
| reasoning_summary | TEXT | Why this event matters |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

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
M&A
INDUSTRY_TREND
UNKNOWN
```

### Notes

Example:

```text
A video mentions a tariff increase.
AlphaBrief detects a TARIFF event and maps it to Apple, Tesla, Nvidia, retailers, and supply-chain-sensitive industries.
```

This makes the product more than a summarizer. It supports event-to-entity impact analysis.

---

## 5.11 `brief_claims`

Represents key claims extracted from the source or generated during analysis.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| brief_id | UUID | FK to briefs |
| event_id | UUID | Nullable FK to brief_events |
| entity_id | UUID | Nullable FK to financial_entities |
| claim_text | TEXT | The claim being made |
| claim_type | VARCHAR(80) | FACTUAL, INTERPRETIVE, FORECAST, RISK, OPPORTUNITY |
| support_status | VARCHAR(50) | SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED, SPECULATIVE |
| confidence_score | NUMERIC(5,2) | Optional 0-100 score |
| verification_notes | TEXT | Why the claim received this support status |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### Notes

This table helps AlphaBrief distinguish between:

```text
What the source said
What external evidence supports
What the model inferred
What remains speculative
```

That distinction is critical for user trust. Nobody needs a confident finance hallucination wearing a suit.

---

## 5.12 `brief_citations`

Stores supporting evidence used in the brief, especially for Pro/deep analysis.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| brief_id | UUID | FK to briefs |
| claim_id | UUID | Nullable FK to brief_claims |
| event_id | UUID | Nullable FK to brief_events |
| entity_id | UUID | Nullable FK to financial_entities |
| source_title | TEXT | Article/page/report title |
| source_url | TEXT | Nullable for sources without public URL |
| publisher | VARCHAR(255) | Nullable |
| published_at | TIMESTAMP | Nullable |
| accessed_at | TIMESTAMP | Required |
| snippet | TEXT | Short supporting excerpt or paraphrased evidence note |
| source_quality | VARCHAR(50) | HIGH, MEDIUM, LOW, UNKNOWN |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### Notes

Citations should support claim verification, public shared pages, and future compliance/audit features.

---

## 5.13 `brief_shares`

Represents a shareable public or unlisted version of a brief.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| brief_id | UUID | FK to briefs |
| user_id | UUID | Owner FK to users |
| share_token | VARCHAR(120) | Unique random token used in URL |
| slug | VARCHAR(180) | Optional SEO-friendly slug |
| visibility | VARCHAR(50) | PRIVATE, UNLISTED, PUBLIC |
| enabled | BOOLEAN | Required, default true |
| allow_download | BOOLEAN | Required, default false |
| view_count | INTEGER | Required, default 0 |
| created_at | TIMESTAMP | Required |
| shared_at | TIMESTAMP | Nullable |
| expires_at | TIMESTAMP | Nullable |
| revoked_at | TIMESTAMP | Nullable |
| updated_at | TIMESTAMP | Required |

### Notes

Do **not** store the full public URL as the source of truth.

Store:

```text
share_token = brf_9xK2pLmQ
```

Generate:

```text
https://alphabrief.ai/share/brf_9xK2pLmQ
```

This keeps the model safe if the domain, route, or frontend app changes later.

### Visibility values

```text
PRIVATE
UNLISTED
PUBLIC
```

For v0.3, `UNLISTED` is enough for shareable links. `PUBLIC` can wait until SEO/community discovery exists.

---

## 5.14 `brief_exports`

Represents downloadable versions of a brief.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| brief_id | UUID | FK to briefs |
| user_id | UUID | FK to users |
| export_type | VARCHAR(50) | MARKDOWN, PDF, DOCX |
| status | VARCHAR(50) | PENDING, COMPLETED, FAILED, EXPIRED |
| storage_provider | VARCHAR(50) | LOCAL, S3, R2, NONE |
| storage_key | TEXT | Nullable object key if stored |
| file_url | TEXT | Nullable temporary/signed URL, not always persisted |
| file_size_bytes | BIGINT | Nullable |
| error_message | TEXT | Nullable |
| created_at | TIMESTAMP | Required |
| completed_at | TIMESTAMP | Nullable |
| expires_at | TIMESTAMP | Nullable |
| updated_at | TIMESTAMP | Required |

### Export type values

```text
MARKDOWN
PDF
DOCX
```

### Notes

For MVP, Markdown can be generated on demand without storing a file.

For production, PDF/DOCX exports should be generated asynchronously and stored in object storage such as S3 or Cloudflare R2.

Do not store PDF/DOCX binary content inside the `briefs` table. Databases have suffered enough.

---

## 5.15 `referrals`

Tracks referral relationships between users.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| referrer_user_id | UUID | FK to users; inviter |
| referred_user_id | UUID | Nullable FK to users; filled after signup |
| referral_code | VARCHAR(50) | Code used at signup |
| status | VARCHAR(50) | INVITED, SIGNED_UP, ACTIVATED, REWARDED, CANCELLED, FRAUD_REVIEW |
| reward_granted | BOOLEAN | Required, default false |
| reward_credit_transaction_id | UUID | Nullable FK to credit_transactions |
| created_at | TIMESTAMP | Required |
| signed_up_at | TIMESTAMP | Nullable |
| activated_at | TIMESTAMP | Nullable |
| rewarded_at | TIMESTAMP | Nullable |
| updated_at | TIMESTAMP | Required |

### Notes

Do **not** store a `referral_list` directly on `users`.

A referral needs its own lifecycle:

```text
INVITED → SIGNED_UP → ACTIVATED → REWARDED
```

This makes anti-abuse checks and reward auditing much cleaner.

---

## 5.16 `credit_transactions`

Tracks brief credits, referral bonuses, signup bonuses, purchases, trial grants, reservations, refunds, and usage deductions.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| amount | INTEGER | Positive for grants/refunds, negative for deductions/reservations |
| credit_type | VARCHAR(50) | BASIC_BRIEF, DEEP_BRIEF, EXPORT_MARKDOWN, EXPORT_PDF, EXPORT_DOCX, GENERAL |
| transaction_type | VARCHAR(80) | REFERRAL_BONUS, SIGNUP_BONUS, PURCHASE, TRIAL_GRANT, USAGE_RESERVATION, USAGE_DEDUCTION, USAGE_REFUND, ADMIN_ADJUSTMENT, EXPIRY |
| transaction_status | VARCHAR(50) | RESERVED, CONFIRMED, REFUNDED, CANCELLED, EXPIRED |
| source_type | VARCHAR(80) | REFERRAL, PROMO_CODE, SUBSCRIPTION, USER_ENTITLEMENT, BRIEF_GENERATION, EXPORT_GENERATION, ADMIN, SYSTEM |
| source_id | UUID | Nullable reference to referral/promo/payment/brief/export/etc. |
| idempotency_key | VARCHAR(120) | Optional but recommended for preventing duplicate deductions |
| description | TEXT | Optional human-readable note |
| expires_at | TIMESTAMP | Nullable |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### Notes

`+5 DEEP_BRIEF credits` means the user can generate 5 additional deep briefs.

Example grant:

```text
credit_type = DEEP_BRIEF
amount = +5
transaction_type = REFERRAL_BONUS
transaction_status = CONFIRMED
```

Example usage:

```text
credit_type = DEEP_BRIEF
amount = -1
transaction_type = USAGE_DEDUCTION
transaction_status = CONFIRMED
source_type = BRIEF_GENERATION
source_id = brief.id
```

For expensive deep briefs, prefer a reservation pattern:

```text
1. Before generation starts, create -1 DEEP_BRIEF with transaction_type = USAGE_RESERVATION and status = RESERVED.
2. If generation succeeds, mark it CONFIRMED.
3. If generation fails before useful output is produced, mark it REFUNDED or CANCELLED and create a refund entry if needed.
```

This prevents a user from firing multiple deep-brief requests at the same time and slipping past the limit. Because naturally the most expensive endpoint is also the one users will double-click. Software comedy writes itself.

For v0.3, `credit_transactions` is especially useful for:

- beta tester deep-brief allowances
- referral rewards
- temporary promo credits
- one-off admin grants
- export credits

A beta tester with only 2 deep briefs can be represented as:

```text
user_entitlements:
plan_code = BETA_TESTER
source_type = TRIAL

credit_transactions:
credit_type = DEEP_BRIEF
amount = +2
transaction_type = TRIAL_GRANT
source_type = USER_ENTITLEMENT
source_id = user_entitlements.id
```

---

## 5.17 `user_usage_daily`

Tracks daily usage for product limits, cost control, and internal monitoring.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| usage_date | DATE | Required |
| plan_code_at_usage | VARCHAR(50) | FREE, PRO, STUDENT_PRO, BETA_TESTER, ADMIN |
| basic_brief_count | INTEGER | Number of basic briefs generated |
| deep_brief_count | INTEGER | Number of deep briefs generated |
| export_count | INTEGER | Number of exports generated |
| ai_input_token_estimate | INTEGER | Optional but recommended |
| ai_output_token_estimate | INTEGER | Optional but recommended |
| ai_total_token_estimate | INTEGER | Optional but recommended |
| ai_search_call_count | INTEGER | Optional; useful for web/retrieval cost tracking |
| estimated_ai_cost_usd | NUMERIC(12,6) | Optional internal estimate |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### Recommended unique constraint

```sql
ALTER TABLE user_usage_daily
ADD CONSTRAINT uq_user_usage_daily_user_date
UNIQUE (user_id, usage_date);
```

### Notes

Users should see simple limits such as:

```text
You have 2 deep briefs remaining.
```

Do not expose token counts as the main user-facing limit in v0.3. Most users do not want to think in tokens unless they have committed some sort of API billing crime.

However, AlphaBrief should internally track token and estimated cost from day one. This helps answer:

- Which brief type is expensive?
- Which users are costly?
- Is Pro pricing profitable?
- Should deep briefs be capped daily, monthly, or lifetime for testers?
- Which model/provider is driving cost?

Suggested user-facing limits:

| Feature | Free | Beta Tester | Pro |
|---|---:|---:|---:|
| Basic briefs per day | 3 | 5 | 50 |
| Deep briefs | 0 or limited preview | 2 lifetime | 20 per month or controlled by credits |
| Pasted text length | 8,000 characters | 15,000 characters | 30,000 characters |
| Saved brief history | 20 briefs | 20 briefs | High or unlimited |
| Premium external context | No | Limited | Yes |

---

## 5.18 `plan_limits`

Defines reusable usage rules for each plan.

This table is optional for the earliest MVP, but it is the cleanest way to control testing access, free-tier limits, Pro limits, and student pricing without hardcoding everything.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| plan_code | VARCHAR(50) | FREE, PRO, STUDENT_PRO, BETA_TESTER, ADMIN |
| feature_code | VARCHAR(80) | BASIC_BRIEF, DEEP_BRIEF, EXPORT_PDF, EXPORT_DOCX, PREMIUM_CONTEXT, WATCHLIST |
| limit_amount | INTEGER | Nullable for unlimited |
| reset_period | VARCHAR(50) | DAILY, WEEKLY, MONTHLY, LIFETIME, NONE |
| active | BOOLEAN | Required, default true |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### Example plan limits

```text
Example plan limits:

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

### Notes

`plan_limits` defines default rules. `credit_transactions` can grant extra credits on top.

Example:

```text
A BETA_TESTER plan allows 2 lifetime deep briefs.
A referral bonus grants +5 extra DEEP_BRIEF credits.
Effective available deep briefs = plan limit remaining + confirmed extra credits.
```

For v0.3, you can choose either:

```text
Simple path: use credit_transactions only for beta tester deep brief limits.
Cleaner path: use plan_limits for default plan rules and credit_transactions for bonuses/overrides.
```

Recommended: implement `plan_limits` if it does not slow you down too much. It prevents limit rules from becoming scattered across service code like confetti after a bad sprint planning meeting.

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

## 6.3 `education_verifications`

Use this later if AlphaBrief adds student pricing and wants to verify student eligibility.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| institution_name | VARCHAR(255) | Nullable |
| institution_email | VARCHAR(255) | Nullable student email |
| verification_provider | VARCHAR(100) | INTERNAL, MANUAL, SHEER_ID, etc. |
| status | VARCHAR(50) | PENDING, VERIFIED, REJECTED, EXPIRED |
| verified_at | TIMESTAMP | Nullable |
| expires_at | TIMESTAMP | Nullable |
| created_at | TIMESTAMP | Required |
| updated_at | TIMESTAMP | Required |

### Notes

Only add this table when student pricing is close to launch.

A successful verification can create or update an entitlement:

```text
plan_code = STUDENT_PRO
source_type = EDUCATION_VERIFICATION
```

If the user pays for the student tier directly, the entitlement can instead be:

```text
plan_code = STUDENT_PRO
source_type = PAID_SUBSCRIPTION
```

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
STUDENT_PRO
BETA_TESTER
ADMIN
```

## 7.3 `entitlement_source_type`

```text
FREE_DEFAULT
PROMO_CODE
PAID_SUBSCRIPTION
ADMIN_GRANT
TRIAL
EDUCATION_VERIFICATION
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


## 7.11 `brief_visibility`

```text
PRIVATE
UNLISTED
PUBLIC
```

## 7.12 `event_type`

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
M&A
INDUSTRY_TREND
UNKNOWN
```

## 7.13 `impact_direction`

```text
POSITIVE
NEGATIVE
MIXED
UNCLEAR
```

## 7.14 `impact_magnitude`

```text
LOW
MEDIUM
HIGH
UNKNOWN
```

## 7.15 `claim_type`

```text
FACTUAL
INTERPRETIVE
FORECAST
RISK
OPPORTUNITY
```

## 7.16 `claim_support_status`

```text
SUPPORTED
PARTIALLY_SUPPORTED
UNSUPPORTED
SPECULATIVE
```

## 7.17 `export_type`

```text
MARKDOWN
PDF
DOCX
```

## 7.18 `export_status`

```text
PENDING
COMPLETED
FAILED
EXPIRED
```

## 7.19 `referral_status`

```text
INVITED
SIGNED_UP
ACTIVATED
REWARDED
CANCELLED
FRAUD_REVIEW
```

## 7.20 `credit_transaction_type`

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

## 7.21 `credit_transaction_status`

```text
RESERVED
CONFIRMED
REFUNDED
CANCELLED
EXPIRED
```

## 7.22 `credit_type`

```text
BASIC_BRIEF
DEEP_BRIEF
EXPORT_MARKDOWN
EXPORT_PDF
EXPORT_DOCX
GENERAL
```

## 7.23 `plan_limit_feature_code`

```text
BASIC_BRIEF
DEEP_BRIEF
EXPORT_MARKDOWN
EXPORT_PDF
EXPORT_DOCX
PREMIUM_CONTEXT
WATCHLIST
```

## 7.24 `limit_reset_period`

```text
DAILY
WEEKLY
MONTHLY
LIFETIME
NONE
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

CREATE INDEX idx_plan_limits_plan_code ON plan_limits(plan_code);
CREATE INDEX idx_plan_limits_feature_code ON plan_limits(feature_code);
CREATE UNIQUE INDEX uq_plan_limits_plan_feature_period ON plan_limits(plan_code, feature_code, reset_period) WHERE active = true;
```

---


# 9. Shareable Brief Flow

Recommended endpoint:

```http
POST /api/v1/briefs/{briefId}/share
```

Backend flow:

```text
1. Verify the current user owns the brief
2. Verify the brief status is COMPLETED
3. Create a unique share_token if no active share exists
4. Set visibility to UNLISTED by default
5. Return generated share URL to frontend
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

Do not expose private user data, source upload metadata, internal model traces, or paid-only private context unless it is intentionally included in the public brief view.

---

# 10. Download / Export Flow

For MVP, Markdown can be generated on demand:

```http
GET /api/v1/briefs/{briefId}/download?type=MARKDOWN
```

For heavier exports such as PDF or DOCX, recommended flow:

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
1. Verify user owns brief or has access through a shared brief setting
2. Create brief_export with PENDING status
3. Generate export from summary_markdown/generated_content
4. Store file in object storage if needed
5. Mark export COMPLETED
6. Return download URL or export status
```

---

# 11. Referral Reward Flow

Recommended referral endpoints:

```http
GET /api/v1/me/referral-code
POST /api/v1/referrals/apply
GET /api/v1/me/referrals
```

Suggested flow:

```text
1. Existing user shares referral_code
2. New user signs up with referral_code
3. Create referral with status SIGNED_UP
4. When referred user generates first brief, mark referral ACTIVATED
5. Create credit_transactions for the referrer and referred user
6. Mark referral REWARDED
```

Reward rules should be server-side only. Never trust the frontend to decide whether a reward was earned, because apparently browsers are where honesty goes to retire.

---

# 12. Beta Tester / Trial Usage Control Flow

Testing access should be controlled from the backend. Do not rely on goodwill, vibes, or the sacred honor of beta users. That is how API bills become horror stories.

Recommended setup:

```text
plans:
BETA_TESTER

user_entitlements:
plan_code = BETA_TESTER
source_type = TRIAL
status = ACTIVE
starts_at = now
ends_at = beta_end_date

plan_limits:
plan_code = BETA_TESTER
feature_code = DEEP_BRIEF
limit_amount = 2
reset_period = LIFETIME
```

Alternative simpler setup:

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
1. Does the user have an active entitlement that allows deep briefs?
2. Does the user have remaining quota or confirmed DEEP_BRIEF credits?
3. Reserve or deduct 1 DEEP_BRIEF credit.
4. Generate the brief.
5. Confirm the deduction if successful.
6. Refund or cancel the reservation if generation fails before producing usable output.
```

This keeps beta testing affordable and predictable.

---

# 13. Deep Brief Analysis Pipeline

A Pro/deep brief should not rely on one giant prompt.

Recommended pipeline:

```text
1. Ingest source
2. Extract or transcribe text
3. Detect financial entities
4. Detect events and claims
5. Map events to entities
6. Retrieve external context
7. Generate structured analysis
8. Verify claims against evidence
9. Persist brief, events, claims, citations, and entity insights
10. Render frontend sections and exportable markdown
```

This supports examples such as:

```text
A source mentions a tariff increase.
AlphaBrief detects the event, maps affected entities, retrieves context, explains impact channels, and separates supported evidence from speculative implications.
```

---

# 14. Promo Code Redemption Flow

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

# 15. Promo Code Error Codes

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

# 16. Concurrency Requirement

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

# 17. Access Checking

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

# 18. Effective Subscription Status

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

# 19. Migration Order

Suggested Alembic migration order:

```text
001_create_users
002_create_plans
003_create_plan_limits
004_create_user_entitlements
005_create_promo_codes
006_create_promo_code_redemptions
007_create_sources
008_create_briefs
009_create_financial_entities
010_create_brief_entity_insights
011_create_brief_events
012_create_brief_claims
013_create_brief_citations
014_create_brief_shares
015_create_brief_exports
016_create_referrals
017_create_credit_transactions
018_create_user_usage_daily
019_create_indexes
```

If using Python + FastAPI, Alembic is the common migration tool.

---

# 20. v0.3 Simplification Option

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

For sharing/export/referral/testing features, the simplest acceptable MVP is:

```text
brief_shares
brief_exports
referrals
credit_transactions
user_usage_daily
```

If beta tester cost control is the immediate priority, implement either:

```text
plan_limits
```

or:

```text
credit_transactions with +2 DEEP_BRIEF trial grants
```

Do not wait until users are already testing to add this. That would be like installing brakes after the car has met a tree.

Do not collapse referrals into `users.referral_list`, and do not store downloadable files directly inside `briefs`.

This avoids painful rewrites later.

---

# 21. Critical Editor Review: What This Model Might Still Miss

This section challenges the assumptions in the current design so v0.3 does not become overconfident architecture theater.

## 21.1 Possible overbuilding risk

The model now includes `brief_events`, `brief_claims`, `brief_citations`, `brief_entity_insights`, `external_context_items`, `brief_exports`, `brief_shares`, `referrals`, `credit_transactions`, and `plan_limits`.

That is powerful, but it may be too much to implement fully before the product proves retention.

Practical MVP priority:

```text
Must-have:
users
plans
user_entitlements
sources
briefs
user_usage_daily
credit_transactions or plan_limits for tester control
brief_shares

Good soon:
brief_exports
brief_citations
external_context_items

Can wait:
brief_events
brief_claims
brief_entity_insights at full normalization depth
education_verifications
paid_subscriptions
admin_grants
```

The product should not spend months perfecting research data normalization before users prove they want repeated briefs.

## 21.2 `plan_limits` and `credit_transactions` overlap

There is deliberate overlap:

```text
plan_limits = default allowance rules
credit_transactions = bonuses, deductions, reservations, and audit history
```

But this means the backend must define one clear usage calculation rule.

Recommended rule:

```text
available_usage = plan allowance remaining for the period + confirmed extra credits - confirmed/reserved deductions
```

Without this, limits can become inconsistent.

## 21.3 Token tracking is internal, not user-facing

The model recommends tracking tokens and cost immediately, but user-facing pricing should stay in briefs/credits.

Reason:

```text
Users understand “2 deep briefs remaining.”
Users do not want “142,000 tokens remaining.”
```

However, token/cost tracking must exist internally because deep briefs may involve multiple model calls, retrieval calls, and verification passes.

## 21.4 Student pricing should not be rushed

`STUDENT_PRO` is included for future readiness, but actual student pricing creates operational issues:

- verification method
- renewal/expiry
- abuse prevention
- pricing fairness
- support overhead

Unless student pricing is part of the near-term launch, keep `education_verifications` as future/optional.

## 21.5 Shareable briefs need privacy filtering

A shared brief should not automatically expose everything stored in `generated_content`, `external_context_items`, model traces, user-upload metadata, or private notes.

The app should render a public-safe view model, not dump raw brief JSON into the public page.

## 21.6 AI depth depends on retrieval quality, not only model intelligence

The data model supports deep analysis, but it does not guarantee deep analysis.

AlphaBrief’s actual quality will depend on:

- source extraction quality
- financial entity resolution
- retrieval sources
- citation quality
- prompt/schema design
- verification pass quality
- cost limits
- latency tolerance

A table named `brief_claims` does not magically create reliable research. Rude, but true.

## 21.7 Legal/compliance language is still missing from the data model

The product should eventually support:

- disclaimer versioning
- investment advice boundary
- source attribution policy
- public sharing terms
- user acceptance of terms

For v0.3, `briefs.disclaimer` is enough, but later a `legal_documents` or `user_acceptances` model may be needed.

## 21.8 Anti-abuse is not fully modeled

Referral and credit systems invite abuse.

Future additions may include:

- user account verification state
- email verification
- suspicious referral flags
- IP/device heuristics
- rate limiting records
- admin review workflow

For v0.3, keep reward rules conservative. For example, only reward after the referred user verifies email and generates a first non-failed brief.

---

# 22. Final Recommendation

Use this model:

```text
User
→ has many UserEntitlements
→ effective access is calculated from active entitlements
→ promo codes create entitlements
→ paid subscriptions later create entitlements too

Brief
→ has structured AI output
→ has events, claims, citations, entity insights
→ can be shared through BriefShare
→ can be exported through BriefExport

Referral
→ tracks referrer/referred lifecycle
→ rewards users through CreditTransaction

PlanLimit / CreditTransaction
→ controls beta tester limits, Pro allowances, student allowances, referral bonuses, and expensive deep-brief usage
```

This keeps Alphabrief flexible without overbuilding.

The testing system should not ask:

```text
Do we trust this beta user not to run too many deep briefs?
```

It should ask:

```text
Does this user have remaining DEEP_BRIEF quota or credits?
```

The subscription wall should not ask:

```text
Did this user pay?
```

It should ask:

```text
Does this user have active Pro access right now?
```

The sharing system should not ask:

```text
What full URL did we store?
```

It should ask:

```text
Is there an enabled share token for this completed brief?
```

The referral system should not ask:

```text
Who is inside this user's referral_list?
```

It should ask:

```text
Which referral records have been activated and rewarded?
```
