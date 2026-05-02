# AlphaBrief v0.3 Technical Architecture

## Version

`v0.3 First Milestone`

## Status

Architecture draft for the first major AlphaBrief milestone.

Earlier v0.1/v0.2 ideas are now treated as internal implementation slices inside v0.3:

```text
v0.3 foundation slice
v0.3 source/question brief flow
v0.3 agentic/deep analysis flow
v0.3 validation before launch
```

---

# 1. Overview

AlphaBrief is an AI finance research assistant for students, beginner investors, and finance-minded users.

Users can submit:

- A finance article URL
- A YouTube video URL
- A PDF such as an earnings report or annual report
- Pasted text
- A direct finance or market question
- A source plus an additional research instruction

AlphaBrief extracts or interprets the input, identifies relevant financial entities, retrieves relevant context when allowed, and produces a structured finance research brief.

The product should not only summarise.

It should explain:

```text
What happened
Why it matters
Who it affects
What the implications are
What evidence supports it
What remains uncertain
What to research next
```

The central product artifact is:

```text
Brief
```

A source is optional input. A direct finance question can create a brief without a source.

---

# 2. Product Goals

The v0.3 first milestone should prove:

1. Users can create briefs from multiple input types.
2. Users can ask direct finance questions and receive structured finance research briefs.
3. AlphaBrief can produce differentiated output beyond generic summaries.
4. AlphaBrief can support source-based, question-based, and mixed workflows.
5. The backend can support async or job-based brief generation.
6. The product can separate free/basic and Pro/deep analysis.
7. The product can use research scopes without publicly ranking individual sources.
8. The product can track usage and cost enough to avoid AI budget chaos.

Main product goal:

```text
Turn messy finance content or finance questions into clear, structured, source-aware research briefs.
```

---

# 3. Recommended Stack

## Frontend

```text
React
TypeScript
Vite
TailwindCSS
shadcn/ui or similar component library
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

For early v0.3, generation can start synchronously if needed.

The architecture should still be async-ready.

Recommended options:

```text
FastAPI BackgroundTasks for simple local MVP
RQ + Redis
Celery + Redis
Arq + Redis
```

## External Services

Possible external services:

```text
AI model provider
Article extraction provider
YouTube transcript provider
PDF extraction library/service
Market/company data provider
News/search provider
Object storage for uploaded PDFs and exports
```

---

# 4. High-Level Architecture

```text
React/Vite Frontend
        ↓
FastAPI Backend
        ↓
Service Layer
        ↓
Repository Layer
        ↓
PostgreSQL
```

External services should be isolated behind client classes:

```text
AI Provider Client
Article Extraction Client
Transcript Client
PDF Extraction Client
Market Data Client
News/Search Client
Object Storage Client
Research Channel Registry
```

The backend owns:

- Authentication
- Authorization
- Brief orchestration
- Input classification
- Source extraction
- PDF handling
- Entity detection
- Event and claim extraction
- Research scope resolution
- Research channel selection
- Context retrieval
- AI generation
- AI output validation
- Subscription entitlement checks
- Usage limits
- Promo-code redemption
- Brief persistence
- Sharing/export generation

The frontend owns:

- Input UI
- File upload UI
- Research scope selection UI
- Brief generation status UI
- Brief detail display
- Brief history
- Login/signup screens
- Subscription/promo-code UI
- Share/export UI
- Loading/error states

---

# 5. Core User Flows

## 5.1 Research Scope Selection Flow

```text
User starts a new brief
        ↓
Frontend shows research scope options
        ↓
Default selected option is Recommended Sources
        ↓
User accepts default or selects broader scope
        ↓
Backend stores selected researchScope on the brief
        ↓
ContextRetrievalService searches only allowed source categories
```

Recommended UI options:

```text
Recommended Sources
Expanded Market Context
Sentiment & Discussion Signals
User-Provided Sources Only
```

The UI must not display ranked lists of publishers or channels.

---

## 5.2 Source-Based Brief Flow

```text
User submits article/video/PDF/text
        ↓
Backend validates input type and usage limit
        ↓
Backend creates source
        ↓
Backend creates brief with source_id
        ↓
Backend creates brief_generation_job
        ↓
System extracts/transcribes raw content
        ↓
System cleans content
        ↓
System identifies entities, events, and claims
        ↓
System applies selected research scope
        ↓
System retrieves context where allowed
        ↓
AI generates structured brief
        ↓
Backend validates and persists output
        ↓
User views brief
```

---

## 5.3 Question-Based Brief Flow

```text
User asks finance question
        ↓
Backend validates question and usage limit
        ↓
Backend creates brief with source_id = null
        ↓
Backend stores question in user_query
        ↓
Backend creates brief_generation_job
        ↓
System classifies intent
        ↓
System detects entities/topics
        ↓
System applies selected research scope
        ↓
System retrieves context where allowed
        ↓
AI generates structured research brief
        ↓
Backend validates and persists output
        ↓
User views brief
```

Example:

```text
“Analyse the fintech industry for me”
```

---

## 5.4 Mixed Brief Flow

```text
User uploads/pastes source and adds research instruction
        ↓
Backend creates source
        ↓
Backend creates brief with source_id and user_query
        ↓
Pipeline processes both source and question together
        ↓
AI generates structured brief
```

Example:

```text
“Use this Visa annual report and explain whether fintech disruption is a serious risk.”
```

---

## 5.5 Free User Flow

Free/basic brief should include:

- Quick summary
- Key facts
- Key takeaways
- So What?
- Basic implication map
- Mentioned financial entities
- Basic finance concepts
- Basic risks
- Research path recommendations
- Disclaimer

---

## 5.6 Pro / Deep Brief Flow

Pro/deep brief should include everything in free/basic, plus:

- Industry context
- Competitor context
- Macro context
- Political/regulatory context
- Market sentiment where available
- Event-to-entity impact reasoning
- Claim/evidence support status
- Contradictions or tensions across sources
- What would change this view
- Richer source evidence panel

---

## 5.7 Promo Code Flow

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
User receives upgraded access
```

Promo codes should create entitlements. They should not bypass authorization.

---

# 6. Frontend Architecture

## Key Pages

| Page | Purpose |
|---|---|
| Landing page | Explain AlphaBrief and value proposition |
| Sign in / Sign up | Authentication |
| Dashboard | Recent briefs and main input |
| New Brief page | Submit URL, PDF, pasted text, or finance question |
| Brief Detail page | Display generated brief |
| Brief History page | List previous briefs |
| Subscription page | Current plan, limits, promo-code input |
| Pricing page | Explain Free vs Pro / Student behavior |
| Shared Brief page | Public-safe brief view |
| Export page/modal | Download Markdown/PDF/DOCX where enabled |

## New Brief Page Requirements

The main input should support:

```text
Paste a link, upload a PDF, paste text, or ask a finance question.
```

Frontend should send:

```text
inputType
input or sourceId
userQuery
requestedDepth
researchScope
```

The UI should avoid forcing users into confusing modes.

Main action:

```text
Create Brief
```

## Frontend Responsibilities

- Collect source/question input
- Detect likely input type client-side where helpful
- Allow PDF upload
- Show safe research-scope choices
- Display validation errors
- Call backend APIs
- Poll brief status
- Show job progress where available
- Render generated brief sections
- Show locked Pro sections where appropriate
- Display subscription/usage status
- Submit promo codes
- Handle sharing/export flows
- Handle loading/error states

## Recommended Frontend Structure

```text
frontend/src/
├── api/
├── components/
├── features/
│   ├── auth/
│   ├── briefs/
│   ├── sources/
│   ├── subscription/
│   ├── sharing/
│   └── layout/
├── pages/
├── routes/
├── types/
└── main.tsx
```

---

# 7. Backend Architecture

## Recommended Backend Structure

```text
backend/app/
├── api/
│   ├── deps.py
│   └── v1/
│       ├── auth.py
│       ├── users.py
│       ├── sources.py
│       ├── briefs.py
│       ├── entities.py
│       ├── research_scopes.py
│       ├── subscription.py
│       ├── sharing.py
│       ├── exports.py
│       ├── referrals.py
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
│   ├── research_channel.py
│   ├── brief_source.py
│   ├── financial_entity.py
│   ├── brief_entity_insight.py
│   ├── brief_event.py
│   ├── brief_claim.py
│   ├── brief_citation.py
│   ├── external_context_item.py
│   ├── brief_share.py
│   ├── brief_export.py
│   ├── referral.py
│   ├── credit_transaction.py
│   ├── user_usage_daily.py
│   └── plan_limit.py
│
├── schemas/
│   ├── auth.py
│   ├── source.py
│   ├── brief.py
│   ├── entity.py
│   ├── subscription.py
│   ├── sharing.py
│   ├── export.py
│   └── common.py
│
├── repositories/
│   ├── user_repository.py
│   ├── source_repository.py
│   ├── brief_repository.py
│   ├── brief_job_repository.py
│   ├── entitlement_repository.py
│   ├── promo_code_repository.py
│   ├── usage_repository.py
│   └── referral_repository.py
│
├── services/
│   ├── auth_service.py
│   ├── access_service.py
│   ├── promo_code_service.py
│   ├── usage_limit_service.py
│   ├── input_classification_service.py
│   ├── research_scope_service.py
│   ├── research_channel_service.py
│   ├── source_extraction_service.py
│   ├── pdf_extraction_service.py
│   ├── entity_detection_service.py
│   ├── event_detection_service.py
│   ├── claim_extraction_service.py
│   ├── context_retrieval_service.py
│   ├── brief_orchestration_service.py
│   ├── brief_generation_service.py
│   ├── ai_output_validation_service.py
│   ├── sharing_service.py
│   ├── export_service.py
│   └── referral_service.py
│
├── clients/
│   ├── ai_provider_client.py
│   ├── article_extraction_client.py
│   ├── transcript_client.py
│   ├── market_data_client.py
│   ├── news_search_client.py
│   └── object_storage_client.py
│
└── main.py
```

## Backend Layering Rule

Route handlers should stay thin.

Recommended flow:

```text
API route
→ Service
→ Repository
→ Database
```

AI prompting should live in services, not route handlers.

External APIs should go through client classes.

---

# 8. Database Architecture

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

## Core Tables for v0.3 First Milestone

```text
users
plans
user_entitlements
promo_codes
promo_code_redemptions
sources
briefs
brief_generation_jobs
research_channels
brief_sources
financial_entities
brief_entity_insights
brief_events
brief_claims
brief_citations
external_context_items
brief_shares
brief_exports
referrals
credit_transactions
user_usage_daily
plan_limits
```

## Key Relationship Rule

```text
briefs.source_id is nullable.
```

Reason:

```text
Question-based briefs may not have a user-provided source.
```

The correct relationship is:

```text
User
 └── Brief
      └── Source optional
```

not:

```text
User
 └── Source
      └── Brief
```

---

# 9. Core Domains

## User

Represents a registered user.

Access is determined through:

```text
user_entitlements
```

not `users.subscription_tier`.

## Source

Represents user-provided material only.

Supported source types:

```text
ARTICLE_URL
YOUTUBE_URL
PDF_FILE
PASTED_TEXT
```

Direct finance questions should not be stored as sources.

## Brief

Represents the final AI-generated product artifact.

Important fields:

```text
id
user_id
source_id nullable
input_type
user_query
title
brief_status
plan_code_used
requested_depth
research_scope
generated_content
summary_markdown
disclaimer
```

## Brief Source

Represents all evidence/context used in the final brief.

This includes:

```text
USER_PROVIDED
AGENT_DISCOVERED
SYSTEM_CONTEXT
```

## Brief Generation Job

Tracks generation progress, retries, and failures.

## Research Channel

Internal registry for allowed source channels.

Do not expose internal trust tiers publicly.

## Financial Entity

Represents companies, tickers, sectors, macro factors, etc.

## Brief Event

Represents a detected event such as earnings, regulation, tariff, macro shift, or competitor news.

## Brief Claim

Represents key claims, their type, support status, and verification notes.

## Brief Citation

Stores supporting evidence for claims/events/entities.

## External Context Item

Stores external context used in prompt construction.

---

# 10. Subscription and Entitlement Architecture

Do not rely on a single user subscription field.

Use:

```text
Plan
UserEntitlement
PlanLimit
CreditTransaction
UserUsageDaily
```

## Access Check

A user has Pro/deep access if they have an active entitlement where:

```text
user_id = current user
plan_code in ('PRO', 'STUDENT_PRO', 'ADMIN')
status = ACTIVE
starts_at <= now
ends_at is null OR ends_at > now
```

## Promo Code Redemption

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

---

# 11. AI Provider Layer

The AI provider should be wrapped behind an internal client/service abstraction.

Example:

```python
class AiProviderClient:
    async def generate_brief(self, request: BriefGenerationRequest) -> BriefGenerationResult:
        ...
```

This matters because:

- Providers can be changed later
- Service logic can be tested without always calling AI APIs
- Prompt templates stay isolated
- Output validation can be consistent
- Cost tracking becomes cleaner

Preferred flow:

```text
BriefOrchestrationService
→ ContextRetrievalService
→ BriefGenerationService
→ AiProviderClient
→ AiOutputValidationService
→ BriefRepository
```

---

# 12. v0.3 AI Pipeline

```text
1. Validate request
2. Classify input type
3. Check usage limit
4. Check entitlement if Pro/deep requested
5. Create source if source-based
6. Create brief
7. Create brief_generation_job
8. Extract/transcribe content if applicable
9. Clean content
10. Detect entities
11. Detect events
12. Extract claims
13. Resolve research scope
14. Select allowed research channels
15. Retrieve context where allowed
16. Store brief_sources and external_context_items
17. Construct AI prompt
18. Generate structured brief
19. Validate AI output
20. Persist generated_content, summary_markdown, entities, events, claims, citations
21. Update usage and estimated cost
22. Mark job completed or failed
23. Return result to user
```

---

# 13. Async-Friendly Generation Flow

```text
POST /api/v1/briefs
        ↓
Create source if needed
        ↓
Create brief with status QUEUED
        ↓
Create brief_generation_job with status QUEUED
        ↓
Return briefId and jobId
        ↓
Worker processes job
        ↓
Frontend polls GET /api/v1/briefs/{briefId}
```

For early v0.3, the worker can be simulated or replaced with synchronous processing. The API should still be async-shaped.

---

# 14. Research Scope Behavior

Default:

```text
RECOMMENDED_SOURCES
```

Supported values:

```text
RECOMMENDED_SOURCES
EXPANDED_MARKET_CONTEXT
SENTIMENT_AND_DISCUSSION
USER_PROVIDED_ONLY
```

Recommended UI labels:

| API value | UI label | Use |
|---|---|---|
| RECOMMENDED_SOURCES | Recommended Sources | Default. Accuracy-focused research using official and established categories |
| EXPANDED_MARKET_CONTEXT | Expanded Market Context | Adds selected market commentary, newsletters, videos, and specialist platforms |
| SENTIMENT_AND_DISCUSSION | Sentiment & Discussion Signals | Adds limited public discussion sources for market narrative only |
| USER_PROVIDED_ONLY | User-Provided Sources Only | Uses submitted source plus minimal metadata |

Important rule:

```text
The UI must not publicly rank individual publishers, newsletters, YouTube channels, subreddits, or creators by trust tier.
```

---

# 15. Brief Output Shape

Recommended output shape:

```json
{
  "title": "Brief title",
  "inputType": "QUESTION",
  "researchQuestion": "Analyse the fintech industry for me",
  "researchScope": "RECOMMENDED_SOURCES",
  "sourceMix": [],
  "quickSummary": "",
  "keyFacts": [],
  "keyTakeaways": [],
  "soWhat": "",
  "implicationMap": {
    "companyImpact": [],
    "industryImpact": [],
    "investorImpact": [],
    "consumerImpact": [],
    "regulatoryImpact": [],
    "macroImpact": [],
    "whatToWatchNext": []
  },
  "bullBearNeutral": {
    "bull": [],
    "bear": [],
    "neutral": []
  },
  "risksAndUncertainties": [],
  "financeConcepts": [],
  "sourceEvidencePanel": [],
  "claims": [],
  "contradictionsOrTensions": [],
  "assignmentAngles": [],
  "researchPathRecommendations": [],
  "whatWouldChangeThisView": [],
  "studentTakeaway": "",
  "investorTakeaway": "",
  "confidenceScore": 0,
  "confidenceExplanation": "",
  "disclaimer": "This brief is for informational and educational purposes only and is not financial advice."
}
```

---

# 16. API Overview

Detailed endpoint design should live in `docs/API_SPEC.md`.

Likely endpoints:

```text
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/logout

GET    /api/v1/me
PATCH  /api/v1/me

POST   /api/v1/sources/upload

GET    /api/v1/research-scopes

POST   /api/v1/briefs
GET    /api/v1/briefs
GET    /api/v1/briefs/{briefId}
GET    /api/v1/briefs/{briefId}/job
GET    /api/v1/briefs/{briefId}/sources
DELETE /api/v1/briefs/{briefId}

GET    /api/v1/entities/{entityId}

GET    /api/v1/subscription/me
POST   /api/v1/subscription/redeem-promo-code

POST   /api/v1/briefs/{briefId}/share
DELETE /api/v1/briefs/{briefId}/share
GET    /api/v1/shared-briefs/{shareToken}

GET    /api/v1/briefs/{briefId}/download
POST   /api/v1/briefs/{briefId}/exports
GET    /api/v1/briefs/{briefId}/exports/{exportId}

GET    /api/v1/me/referral-code
POST   /api/v1/referrals/apply
GET    /api/v1/me/referrals

GET    /api/v1/health
```

---

# 17. Data Flow

```text
Frontend
   ↓ POST /briefs
FastAPI Route
   ↓
BriefOrchestrationService
   ↓
UsageLimitService
   ↓
AccessService
   ↓
InputClassificationService
   ↓
SourceExtractionService / PDFExtractionService if needed
   ↓
EntityDetectionService
   ↓
EventDetectionService
   ↓
ClaimExtractionService
   ↓
ResearchScopeService
   ↓
ResearchChannelService
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

# 18. Error Handling

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
INVALID_INPUT_TYPE
INVALID_SOURCE_TYPE
INVALID_URL
UNSUPPORTED_FILE_TYPE
FILE_TOO_LARGE
SOURCE_EXTRACTION_FAILED
SOURCE_TOO_LONG
SOURCE_TOO_SHORT
QUESTION_TOO_VAGUE
BRIEF_GENERATION_FAILED
BRIEF_JOB_FAILED
AI_OUTPUT_INVALID
USAGE_LIMIT_REACHED
DEEP_BRIEF_LIMIT_REACHED
INVALID_RESEARCH_SCOPE
RESEARCH_SCOPE_NOT_ALLOWED
PREMIUM_REQUIRED
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

SHARE_NOT_FOUND
SHARE_DISABLED
EXPORT_FAILED
```

User-facing errors should be friendly.

Internal logs should not leak:

- API keys
- Auth tokens
- Passwords
- Full raw private user input in production logs

---

# 19. Authentication and Authorization

The system must support:

- User-owned briefs
- Private brief history
- Entitlement-based access checks
- Promo-code access
- Usage limit enforcement
- Shareable brief access
- Admin-only operations later

Authorization rules:

```text
Users can only access their own private briefs.
Users can only delete their own briefs.
Users can only view their own subscription status.
Pro/deep generation requires active PRO, STUDENT_PRO, or ADMIN entitlement.
Admin-only operations require ADMIN role.
Shared briefs must use public-safe view models.
```

---

# 20. Deployment Shape

Recommended v0.3 deployment:

```text
Frontend: Vercel, Netlify, or AWS Amplify
Backend: Render, Fly.io, Railway, or AWS ECS later
Database: Managed PostgreSQL
Object storage: S3, Cloudflare R2, or provider storage
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
OBJECT_STORAGE_BUCKET
OBJECT_STORAGE_ACCESS_KEY
OBJECT_STORAGE_SECRET_KEY
FRONTEND_BASE_URL
BACKEND_BASE_URL
CORS_ALLOWED_ORIGINS
```

Required frontend environment variables:

```text
VITE_API_BASE_URL
```

---

# 21. Observability

Log these events:

- User created brief
- Source upload succeeded/failed
- Source extraction succeeded/failed
- Question brief created
- Entity detection succeeded/failed
- Event/claim extraction succeeded/failed
- External context retrieval succeeded/failed
- AI generation succeeded/failed
- AI output validation failed
- Usage limit hit
- Promo code redeemed
- Promo code redemption failed
- Share link created
- Export created
- Free user attempted Pro-only feature

Track these metrics:

- Briefs generated per day
- Average generation time
- Failure rate
- Most common input type
- AI token usage estimate
- AI cost estimate
- Promo-code redemption count
- Free-to-Pro upgrade clicks
- Share/export usage

---

# 22. Security Considerations

Minimum v0.3 security requirements:

- Store API keys only in environment variables
- Never expose AI provider keys to frontend
- Validate URLs before fetching
- Prevent SSRF where possible
- Enforce user ownership on brief access
- Enforce Pro access in backend
- Use HTTPS in production
- Sanitize rendered AI output
- Add rate limiting for brief generation
- Validate uploaded PDFs
- Limit uploaded file size
- Avoid logging sensitive raw content in production

Blocked URL examples:

```text
localhost
127.0.0.1
0.0.0.0
10.0.0.0/8
172.16.0.0/12
192.168.0.0/16
```

---

# 23. Engineering Principles

1. Keep v0.3 as the first milestone, but implement it in slices.
2. Use a FastAPI monolith first.
3. Make Brief the central artifact.
4. Treat Source as optional input.
5. Support source-based, question-based, and mixed brief creation.
6. Separate AI prompting from route handlers.
7. Store structured outputs, not only raw AI text.
8. Design APIs so async generation is possible.
9. Enforce Free vs Pro logic in the backend.
10. Treat AI output as untrusted until validated.
11. Keep external providers replaceable.
12. Use SQLAlchemy for persistence, not business logic.
13. Use Alembic migrations for all schema changes.
14. Prioritize product clarity over architectural cleverness.

---

# 24. v0.3 Implementation Slices

## Slice A: Core Brief Foundation

```text
users
sources
briefs
brief_generation_jobs
basic generated_content
summary_markdown
```

## Slice B: Source and Research Traceability

```text
research_channels
brief_sources
external_context_items
```

## Slice C: Finance Intelligence Layer

```text
financial_entities
brief_entity_insights
brief_events
brief_claims
brief_citations
```

## Slice D: Usage and Access Control

```text
plans
user_entitlements
plan_limits
user_usage_daily
credit_transactions
promo_codes
promo_code_redemptions
```

## Slice E: Distribution and Growth

```text
brief_shares
brief_exports
referrals
```

---

# 25. Final Architecture Summary

AlphaBrief v0.3 should be built as a clean FastAPI-based full-stack web application with a structured AI pipeline.

The backend owns:

- Input classification
- Source extraction
- PDF handling
- Entity detection
- Event/claim detection
- Context retrieval
- AI brief generation
- Output validation
- Persistence
- Entitlement enforcement
- Usage limits
- Promo-code redemption
- Sharing/export flows

The frontend owns:

- Input and upload UI
- Research scope selection
- Brief status display
- Brief result display
- Brief history
- Subscription/promo-code UI
- Share/export UI
- Loading/error states

The core product experience is:

```text
Paste a source, upload a report, or ask a finance question.
AlphaBrief turns it into a clear, structured finance research brief.
```
