# Alphabrief v0.3 Technical Architecture

## Version

`v0.3 MVP`

## Status

Draft for MVP implementation.

---

## 1. Overview

Alphabrief is an AI-powered summarisation and investment research assistant for retail investors and finance-minded users.

Users can submit a financial source, such as a YouTube video, finance article, earnings commentary, market update, or pasted text. Alphabrief extracts the important information, identifies relevant financial entities, retrieves relevant context, and produces a structured investor-friendly brief.

For the free tier, Alphabrief focuses mainly on:

- The submitted source itself
- Directly mentioned companies/tickers/entities
- Basic company/entity context
- Source-specific risks and takeaways

For the Pro tier, Alphabrief goes deeper by adding broader context around:

- Industry trends
- Competitor dynamics
- Macro factors
- Political/regulatory factors
- Market sentiment
- Earnings or valuation context where available

The v0.3 architecture should be simple enough to build quickly, but structured enough that the system can grow into a more advanced financial intelligence product later.

---

## 2. Product Goals

The v0.3 MVP should prove three things:

1. Users can submit financial content from multiple input types.
2. Alphabrief can generate a useful, structured investor brief.
3. The product can clearly separate free-tier and Pro-tier insight depth.

The MVP does not need to become a full portfolio platform, brokerage product, or institutional research terminal.

The main goal is:

```text
Turn messy finance content into a clear, structured investor brief.
```

---

## 3. Recommended Stack

### Frontend

```text
React
TypeScript
Vite
TailwindCSS
shadcn/ui or similar component library
```

### Backend

```text
Python
FastAPI
SQLAlchemy 2.x
Alembic
Pydantic
PostgreSQL
```

### Background Processing

For early v0.3, brief generation can start synchronously if needed.

However, the architecture should be designed so it can move to async/background processing.

Recommended later options:

```text
Celery + Redis
RQ + Redis
Arq + Redis
FastAPI BackgroundTasks for very simple local MVP usage
```

### External Services

Possible external services:

```text
AI model provider
Article extraction provider
YouTube transcript provider
Market/company data provider
News/search provider
```

---

## 4. High-Level Architecture

Recommended v0.3 shape:

```text
React/Vite Frontend
        ↓
FastAPI Backend
        ↓
Service Layer
        ↓
SQLAlchemy Repositories
        ↓
PostgreSQL
```

AI and data-provider calls should be isolated behind service/client classes:

```text
AI Provider Client
Article Extraction Client
Transcript Client
Market Data Client
News/Search Client
```

The backend should own:

- Authentication
- Authorization
- Brief orchestration
- Source extraction
- Entity detection
- Context retrieval
- AI generation
- Subscription entitlement checks
- Promo-code redemption
- Usage limits
- Persistence

The frontend should own:

- Source input UI
- Brief generation status UI
- Brief result display
- Brief history
- Login/signup screens
- Subscription/promo-code page
- Locked premium sections
- Error and loading states

---

## 5. Core User Flow

### 5.1 Free User Flow

```text
User submits source
        ↓
Backend validates source type and usage limit
        ↓
System extracts raw content
        ↓
System cleans content
        ↓
System identifies financial entities
        ↓
System retrieves basic company/entity context
        ↓
AI generates structured basic brief
        ↓
Backend stores brief and entity insights
        ↓
User views summary, key takeaways, entity insights, and risks
```

### 5.2 Pro User Flow

```text
User submits source
        ↓
Backend validates source type and Pro entitlement
        ↓
System extracts raw content
        ↓
System cleans content
        ↓
System identifies financial entities
        ↓
System retrieves company-level context
        ↓
System retrieves broader context:
    - Industry trends
    - Competitor movement
    - Macro factors
    - Regulatory/political factors
    - Market sentiment
        ↓
AI generates deeper investment brief
        ↓
Backend stores brief, entity insights, and external context items
        ↓
User views richer entity analysis and environment-level insights
```

### 5.3 Promo Code Flow

```text
User enters promo code
        ↓
Backend normalizes and hashes code
        ↓
Backend validates code status, expiry, and redemption limits
        ↓
Backend creates user entitlement
        ↓
Backend records promo code redemption
        ↓
User receives Pro access
```

Promo codes should not bypass backend authorization. They should create an entitlement, and Pro-only features should check active entitlements.

---

## 6. Frontend Architecture

### Recommended Stack

- React
- TypeScript
- Vite
- TailwindCSS
- shadcn/ui or similar component library

### Key Pages

| Page | Purpose |
|---|---|
| Landing page | Explain Alphabrief and its value proposition |
| Sign in / Sign up | Basic authentication |
| Dashboard | Show recent briefs and main input box |
| New Brief page | Submit URL or pasted text |
| Brief Detail page | Display generated brief |
| Brief History page | List previous briefs |
| Subscription page | Show current plan and promo-code input |
| Pricing page | Explain Free vs Pro behavior |

### Frontend Responsibilities

- Collect source input
- Display validation errors
- Call backend APIs
- Poll brief status if generation is async
- Display generated brief sections
- Show locked Pro sections for free users
- Display user subscription status
- Submit promo codes
- Handle loading and error states

### Recommended Frontend Structure

```text
frontend/src/
├── api/
├── components/
├── features/
│   ├── auth/
│   ├── briefs/
│   ├── subscription/
│   └── layout/
├── pages/
├── routes/
├── types/
└── main.tsx
```

---

## 7. Backend Architecture

### Recommended Stack

- Python
- FastAPI
- SQLAlchemy 2.x
- Alembic
- Pydantic
- PostgreSQL
- Uvicorn

### Backend Responsibilities

- User and auth management
- Source submission
- Brief orchestration
- AI pipeline coordination
- Entity extraction persistence
- Entitlement-based subscription enforcement
- Promo-code redemption
- Usage limit enforcement
- Brief history storage
- API response formatting
- Error handling

### Recommended Backend Structure

```text
backend/app/
├── api/
│   ├── deps.py
│   └── v1/
│       ├── auth.py
│       ├── users.py
│       ├── briefs.py
│       ├── entities.py
│       ├── subscription.py
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
│   ├── plan.py
│   ├── user_entitlement.py
│   ├── promo_code.py
│   ├── promo_code_redemption.py
│   ├── source.py
│   ├── brief.py
│   ├── brief_generation_job.py
│   ├── financial_entity.py
│   ├── brief_entity_insight.py
│   ├── external_context_item.py
│   └── user_usage_daily.py
│
├── schemas/
│   ├── auth.py
│   ├── brief.py
│   ├── entity.py
│   ├── subscription.py
│   └── common.py
│
├── repositories/
│   ├── user_repository.py
│   ├── brief_repository.py
│   ├── entitlement_repository.py
│   ├── promo_code_repository.py
│   └── usage_repository.py
│
├── services/
│   ├── auth_service.py
│   ├── access_service.py
│   ├── promo_code_service.py
│   ├── usage_limit_service.py
│   ├── source_extraction_service.py
│   ├── entity_detection_service.py
│   ├── context_retrieval_service.py
│   ├── brief_generation_service.py
│   └── ai_output_validation_service.py
│
├── clients/
│   ├── ai_provider_client.py
│   ├── article_extraction_client.py
│   ├── transcript_client.py
│   ├── market_data_client.py
│   └── news_search_client.py
│
└── main.py
```

### Backend Layering Rule

Route handlers should stay thin.

Recommended flow:

```text
API route
→ Service
→ Repository
→ Database
```

External API calls should go through client classes.

AI prompting should live in services, not route handlers.

---

## 8. Database Architecture

Recommended database:

```text
PostgreSQL
```

Recommended migration tool:

```text
Alembic
```

Recommended ORM:

```text
SQLAlchemy 2.x
```

### Database Responsibilities

- Store users
- Store submitted sources
- Store generated briefs
- Store brief generation jobs
- Store detected financial entities
- Store brief/entity relationships
- Store external context used for generation
- Store plans and user entitlements
- Store promo codes and redemptions
- Store usage limits

### Core Tables

Required for v0.3:

```text
users
plans
user_entitlements
promo_codes
promo_code_redemptions
sources
briefs
brief_generation_jobs
financial_entities
brief_entity_insights
external_context_items
user_usage_daily
```

### Shared Columns

Most core tables should include:

```text
id
created_at
updated_at
```

In code, these should be represented using shared SQLAlchemy mixins.

Example concept:

```python
class UUIDPrimaryKeyMixin:
    id = mapped_column(UUID(as_uuid=True), primary_key=True)

class TimestampMixin:
    created_at = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at = mapped_column(DateTime(timezone=True), nullable=False)
```

Individual database tables should still list these columns clearly in `DATA_MODEL.md`.

---

## 9. Subscription and Entitlement Architecture

Alphabrief should not rely on a single `subscription_tier` field on the user as the source of truth.

Instead, access should be calculated from active entitlements.

### Access Model

```text
Plan = what product tier exists
UserEntitlement = what access the user currently has
PromoCode = one possible way to create entitlement
Payment = another possible way to create entitlement later
```

### Required Plans

```text
FREE
PRO
ADMIN
```

### Entitlement Sources

```text
FREE_DEFAULT
PROMO_CODE
PAID_SUBSCRIPTION
ADMIN_GRANT
TRIAL
```

### Access Check

A user has Pro access if they have an active entitlement where:

```text
user_id = current user
plan_code in ('PRO', 'ADMIN')
status = ACTIVE
starts_at <= now
ends_at is null OR ends_at > now
```

### Promo Code Redemption

Promo-code redemption should be transactional:

```text
Start transaction
Lock promo code row
Validate redemption availability
Create entitlement
Create redemption record
Increment current_redemptions
Commit transaction
```

This prevents two users from redeeming the final available promo-code slot at the same time.

---

## 10. AI Provider Layer

The AI provider should be wrapped behind an internal client/service abstraction.

Example concept:

```python
class AiProviderClient:
    async def generate_brief(self, request: BriefGenerationRequest) -> BriefGenerationResult:
        ...
```

This matters because:

- AI providers can be changed later.
- Service logic can be tested without always calling the AI API.
- Prompt templates stay isolated.
- Cost and usage monitoring becomes cleaner.
- Output validation can be handled consistently.

### Prompting Rule

The system should avoid building prompts directly inside route handlers.

Preferred flow:

```text
BriefGenerationService
→ builds request
→ ContextRetrievalService adds supporting context
→ AiProviderClient calls model
→ AiOutputValidationService validates output
→ BriefRepository persists result
```

---

## 11. External Data Providers

For v0.3, Alphabrief may need data from:

- Article URL extraction provider
- YouTube transcript extraction provider
- Market data provider
- Company profile provider
- News/search provider
- AI model provider

These should be isolated behind client classes:

```text
ArticleExtractionClient
TranscriptClient
MarketDataClient
CompanyProfileClient
NewsSearchClient
AiProviderClient
```

This prevents the core app from becoming tangled with third-party APIs.

---

## 12. Core Domains

### User

Represents a registered user.

Main fields:

```text
id
email
password_hash
display_name
role
created_at
updated_at
```

User access should be determined through `user_entitlements`, not through `users.subscription_tier`.

---

### Plan

Represents a product access tier.

Plan examples:

```text
FREE
PRO
ADMIN
```

Main fields:

```text
id
code
name
description
active
created_at
updated_at
```

---

### User Entitlement

Represents the access a user currently has.

Main fields:

```text
id
user_id
plan_code
source_type
source_id
status
starts_at
ends_at
created_at
updated_at
```

Entitlements allow Alphabrief to support:

```text
Free users
Paid Pro users
Promo-code Pro users
Trial users
Admin-granted Pro users
Future student discounts
```

---

### Promo Code

Represents a code that can grant temporary or open-ended access.

Main fields:

```text
id
code_hash
display_code_suffix
plan_code
duration_days
max_redemptions
current_redemptions
max_redemptions_per_user
starts_at
expires_at
active
created_by
created_at
updated_at
```

---

### Source

Represents the original user input.

Supported v0.3 source types:

```text
ARTICLE_URL
YOUTUBE_URL
PASTED_TEXT
```

Main fields:

```text
id
user_id
source_type
original_input
normalized_url
title
raw_text
extraction_status
extraction_error
content_hash
created_at
updated_at
```

---

### Brief

Represents the final AI-generated output.

Main fields:

```text
id
user_id
source_id
title
brief_status
plan_code_used
requested_depth
source_summary
key_takeaways
risks
opportunities
investor_questions
disclaimer
model_provider
model_name
prompt_version
generation_error
generated_at
created_at
updated_at
```

---

### Brief Generation Job

Tracks the async or step-by-step generation process for a brief.

Main fields:

```text
id
brief_id
user_id
status
current_step
retry_count
max_retries
error_code
error_message
started_at
completed_at
created_at
updated_at
```

This is useful for status polling, retries, debugging, and future background workers.

---

### Financial Entity

Represents a company, ticker, sector, asset, index, or macro entity detected in the source.

Entity types:

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

Main fields:

```text
id
name
ticker
exchange
entity_type
country
sector
industry
external_provider
external_id
created_at
updated_at
```

---

### Brief Entity Insight

Represents analysis for one entity inside one brief.

Main fields:

```text
id
brief_id
entity_id
source_specific_insight
company_context
industry_context
macro_context
political_regulatory_context
competitor_context
risk_factors
opportunity_factors
premium_only
created_at
updated_at
```

---

### External Context Item

Stores external data used to enrich a brief.

Main fields:

```text
id
brief_id
entity_id
context_type
provider
title
url
published_at
snippet
raw_payload
used_in_prompt
created_at
updated_at
```

This is useful for traceability, debugging, and future citation/explainability features.

---

### User Usage Daily

Tracks daily usage for cost control.

Main fields:

```text
id
user_id
usage_date
plan_code_at_usage
brief_count
ai_input_token_estimate
ai_output_token_estimate
created_at
updated_at
```

---

## 13. v0.3 AI Pipeline

```text
1. Validate input
2. Check usage limit
3. Check entitlement if Pro-only depth is requested
4. Create source
5. Create brief
6. Create brief_generation_job
7. Extract content
8. Clean content
9. Detect financial entities
10. Retrieve context based on effective plan
11. Store external_context_items where applicable
12. Construct AI prompt
13. Generate structured brief
14. Validate AI output shape
15. Persist brief and entity insights
16. Update usage
17. Mark job as completed or failed
18. Return result to user
```

### Async-Friendly Generation Flow

```text
POST /api/v1/briefs
        ↓
Create source
        ↓
Create brief with status QUEUED
        ↓
Create brief_generation_job with status QUEUED
        ↓
Return briefId to frontend
        ↓
Worker processes job
        ↓
Frontend polls GET /api/v1/briefs/{briefId}
```

For very early v0.3, the worker can be simulated or replaced with synchronous processing. The API should still be shaped as if async processing is possible later.

---

## 14. Free vs Pro Behavior

### Free Tier

Free tier brief should include:

- Source summary
- Key takeaways
- Mentioned financial entities
- Basic company/entity explanation
- Source-specific risks
- Simple investor questions

### Pro Tier

Pro tier brief should include everything in free tier, plus:

- Industry trends
- Competitor dynamics
- Macro factors
- Political/regulatory factors
- Earnings and valuation context where available
- Broader risk/opportunity map
- Second-order implications

### Important Rule

Premium gating must be enforced by the backend.

Do not rely only on the frontend to hide premium sections.

Bad pattern:

```text
Backend returns premium context to everyone
Frontend hides it for free users
```

Good pattern:

```text
Backend checks active entitlement
Backend decides what context to retrieve
Backend decides what fields to return
Frontend displays locked cards where appropriate
```

---

## 15. API Overview

Detailed endpoint design should live in `docs/API_SPEC.md`.

Likely endpoints:

```text
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
GET    /api/v1/me
PATCH  /api/v1/me

POST   /api/v1/briefs
GET    /api/v1/briefs
GET    /api/v1/briefs/{briefId}
DELETE /api/v1/briefs/{briefId}

GET    /api/v1/entities/{entityId}

GET    /api/v1/subscription/me
POST   /api/v1/subscription/redeem-promo-code

GET    /api/v1/health
```

Preferred brief generation design:

```text
POST /briefs returns briefId + status
Frontend polls GET /briefs/{briefId}
```

---

## 16. Brief Output Shape

Recommended output shape:

```json
{
  "title": "Brief title",
  "sourceSummary": "Short summary of the original source.",
  "keyTakeaways": [
    "Takeaway 1",
    "Takeaway 2",
    "Takeaway 3"
  ],
  "detectedEntities": [
    {
      "name": "Apple Inc.",
      "ticker": "AAPL",
      "entityType": "COMPANY",
      "sourceSpecificInsight": "What the source says about Apple.",
      "companyContext": "Basic company-level context.",
      "premiumContext": {
        "industryContext": "Premium-only industry context.",
        "macroContext": "Premium-only macro context.",
        "politicalRegulatoryContext": "Premium-only regulatory context.",
        "competitorContext": "Premium-only competitor context."
      }
    }
  ],
  "risks": [
    "Risk 1",
    "Risk 2"
  ],
  "opportunities": [
    "Opportunity 1",
    "Opportunity 2"
  ],
  "investorQuestions": [
    "Question 1",
    "Question 2"
  ],
  "disclaimer": "This brief is for informational purposes only and is not financial advice."
}
```

For free users, `premiumContext` should either be omitted or represented as locked metadata, depending on frontend design.

---

## 17. Data Flow

```text
Frontend
   ↓ POST /briefs
FastAPI Route
   ↓
BriefGenerationService
   ↓
UsageLimitService
   ↓
AccessService
   ↓
SourceExtractionService
   ↓
EntityDetectionService
   ↓
ContextRetrievalService
   ↓
AiProviderClient
   ↓
AiOutputValidationService
   ↓
SQLAlchemy Repositories
   ↓
PostgreSQL
   ↓
Frontend Brief Detail Page
```

---

## 18. Error Handling

Example error response:

```json
{
  "errorCode": "SOURCE_EXTRACTION_FAILED",
  "message": "We could not extract readable content from this source.",
  "details": null,
  "timestamp": "2026-04-29T00:00:00Z"
}
```

Recommended error codes:

```text
INVALID_SOURCE_TYPE
SOURCE_EXTRACTION_FAILED
SOURCE_TOO_LONG
SOURCE_TOO_SHORT
BRIEF_GENERATION_FAILED
AI_OUTPUT_INVALID
USAGE_LIMIT_REACHED
UNAUTHORIZED
FORBIDDEN
NOT_FOUND
INTERNAL_ERROR

PROMO_CODE_INVALID
PROMO_CODE_INACTIVE
PROMO_CODE_NOT_STARTED
PROMO_CODE_EXPIRED
PROMO_CODE_FULLY_REDEEMED
PROMO_CODE_ALREADY_USED
USER_ALREADY_HAS_PRO
PROMO_CODE_REDEMPTION_FAILED
```

User-facing errors should be friendly.

Internal logs should contain enough debugging information, but should not leak:

- API keys
- Auth tokens
- Passwords
- Full raw private user input in production logs

---

## 19. Authentication and Authorization

The system must support:

- User-owned briefs
- Private brief history
- Entitlement-based subscription checks
- Promo-code access
- Usage limit enforcement

Authorization rules:

```text
Users can only access their own briefs.
Users can only delete their own briefs.
Users can only view their own subscription status.
Pro-only generation requires active PRO or ADMIN entitlement.
Admin-only operations require ADMIN role.
```

---

## 20. Deployment Shape

Recommended v0.3 deployment:

```text
Frontend: Vercel, Netlify, or AWS Amplify
Backend: Render, Fly.io, Railway, or AWS ECS later
Database: Managed PostgreSQL
```

Environment separation:

```text
local
staging
production
```

Required backend environment variables:

```text
APP_ENV
DATABASE_URL
JWT_SECRET
AI_PROVIDER_API_KEY
MARKET_DATA_API_KEY
NEWS_API_KEY
FRONTEND_BASE_URL
BACKEND_BASE_URL
CORS_ALLOWED_ORIGINS
```

Required frontend environment variables:

```text
VITE_API_BASE_URL
```

---

## 21. Observability

For v0.3, basic observability is enough.

Log these events:

- User created brief
- Source extraction succeeded/failed
- Entity detection succeeded/failed
- External context retrieval succeeded/failed
- AI generation succeeded/failed
- AI output validation failed
- Usage limit hit
- Promo code redeemed
- Promo code redemption failed
- Free user attempted Pro-only feature

Track these metrics:

- Number of briefs generated per day
- Average generation time
- Failure rate
- Most common source type
- AI token usage estimate
- Promo-code redemption count
- Free-to-Pro upgrade clicks

---

## 22. Security Considerations

Minimum v0.3 security requirements:

- Store API keys only in environment variables
- Never expose AI provider keys to frontend
- Validate URLs before fetching
- Prevent server-side request forgery where possible
- Enforce user ownership on brief access
- Enforce Pro access in backend
- Use HTTPS in production
- Sanitize rendered AI output
- Add rate limiting for brief generation
- Avoid logging sensitive raw content in production

For URL fetching, the backend should reject private/internal network addresses where possible.

Blocked examples:

```text
localhost
127.0.0.1
0.0.0.0
10.0.0.0/8
172.16.0.0/12
192.168.0.0/16
```

---

## 23. Engineering Principles

1. Keep the MVP narrow but useful.
2. Use a FastAPI monolith first.
3. Separate AI prompting from route handlers.
4. Store structured outputs, not only raw AI text.
5. Design APIs so async generation is possible.
6. Enforce Free vs Pro logic in the backend.
7. Treat AI output as untrusted until validated.
8. Keep external providers replaceable.
9. Use SQLAlchemy for persistence, not business logic.
10. Use Alembic migrations for all database schema changes.
11. Prioritize product clarity over architectural cleverness.

---

## 24. Final Architecture Summary

Alphabrief v0.3 should be built as a clean FastAPI-based full-stack web application with a structured AI pipeline.

The backend owns:

- Source extraction
- Entity detection
- Context retrieval
- AI brief generation
- Persistence
- Entitlement-based subscription enforcement
- Promo-code redemption
- Usage limits

The frontend owns:

- Input
- Display
- Brief history
- Loading/error states
- Subscription/promo-code UI
- Upgrade prompts

The MVP should focus on delivering one excellent core experience:

```text
Turn messy finance content into a clear, structured investor brief.
```
