# AlphaBrief v0.3 API Spec

## Version

`v0.3 First Milestone`

## Base Path

```text
/api/v1
```

## Status

This API spec treats **v0.3 as the first major AlphaBrief milestone**.

Earlier v0.1/v0.2 ideas are now internal implementation slices inside v0.3:

```text
v0.3 foundation slice
v0.3 source/question brief flow
v0.3 agentic/deep analysis flow
v0.3 validation before launch
```

---

# 1. API Principles

The API should be:

- Predictable
- Frontend-friendly
- Authenticated by default
- Consistent in error shape
- Designed for async brief generation
- Able to support both source-based and question-based briefs
- Able to support future deep/agentic research workflows

Important product rule:

```text
Brief is the central artifact.
Source is optional input.
```

This means a brief can be created from:

```text
ARTICLE_URL
YOUTUBE_URL
PDF_FILE
PASTED_TEXT
QUESTION
MIXED
```

---

# 2. Authentication Endpoints

## Register

```http
POST /api/v1/auth/register
```

Request:

```json
{
  "email": "user@example.com",
  "password": "password",
  "displayName": "Bruce"
}
```

Response:

```json
{
  "userId": "uuid",
  "email": "user@example.com",
  "displayName": "Bruce",
  "effectivePlanCode": "FREE"
}
```

## Login

```http
POST /api/v1/auth/login
```

Request:

```json
{
  "email": "user@example.com",
  "password": "password"
}
```

Response:

```json
{
  "userId": "uuid",
  "email": "user@example.com",
  "displayName": "Bruce",
  "effectivePlanCode": "FREE"
}
```

## Logout

```http
POST /api/v1/auth/logout
```

Response:

```json
{
  "success": true
}
```

---

# 3. User Endpoints

## Get Current User

```http
GET /api/v1/me
```

Response:

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "displayName": "Bruce",
  "effectivePlanCode": "FREE",
  "defaultResearchScope": "RECOMMENDED_SOURCES",
  "createdAt": "2026-04-29T00:00:00Z"
}
```

## Update Current User

```http
PATCH /api/v1/me
```

Request:

```json
{
  "displayName": "New Name",
  "defaultResearchScope": "RECOMMENDED_SOURCES"
}
```

Response:

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "displayName": "New Name",
  "effectivePlanCode": "FREE",
  "defaultResearchScope": "RECOMMENDED_SOURCES"
}
```

---

# 4. Brief Endpoints

## Create Brief

```http
POST /api/v1/briefs
```

This endpoint creates a brief from:

```text
1. A source
2. A direct finance question
3. A source plus an additional user question/instruction
```

### Request: Article URL

```json
{
  "inputType": "ARTICLE_URL",
  "input": "https://example.com/article",
  "userQuery": null,
  "requestedDepth": "AUTO",
  "researchScope": "RECOMMENDED_SOURCES"
}
```

### Request: YouTube URL

```json
{
  "inputType": "YOUTUBE_URL",
  "input": "https://www.youtube.com/watch?v=example",
  "userQuery": "Focus on the investment implications.",
  "requestedDepth": "AUTO",
  "researchScope": "RECOMMENDED_SOURCES"
}
```

### Request: Pasted Text

```json
{
  "inputType": "PASTED_TEXT",
  "input": "Long pasted finance article or report excerpt...",
  "userQuery": null,
  "requestedDepth": "BASIC",
  "researchScope": "USER_PROVIDED_ONLY"
}
```

### Request: Question

```json
{
  "inputType": "QUESTION",
  "input": "Analyse the fintech industry for me.",
  "userQuery": "Analyse the fintech industry for me.",
  "requestedDepth": "AUTO",
  "researchScope": "RECOMMENDED_SOURCES"
}
```

### Request: Mixed

```json
{
  "inputType": "MIXED",
  "input": "source_id_or_uploaded_file_id_or_url",
  "userQuery": "Use this report and explain the implications for Visa and Mastercard.",
  "requestedDepth": "DEEP",
  "researchScope": "EXPANDED_MARKET_CONTEXT"
}
```

If `researchScope` is omitted, the backend should default to:

```text
RECOMMENDED_SOURCES
```

Supported `inputType` values:

```text
QUESTION
ARTICLE_URL
YOUTUBE_URL
PDF_FILE
PASTED_TEXT
MIXED
```

Supported `requestedDepth` values:

```text
AUTO
BASIC
DEEP
```

Supported `researchScope` values:

```text
RECOMMENDED_SOURCES
EXPANDED_MARKET_CONTEXT
SENTIMENT_AND_DISCUSSION
USER_PROVIDED_ONLY
```

Response:

```json
{
  "briefId": "uuid",
  "jobId": "uuid",
  "status": "QUEUED",
  "inputType": "QUESTION",
  "researchScope": "RECOMMENDED_SOURCES",
  "requestedDepth": "AUTO"
}
```

---

## Upload Source File

```http
POST /api/v1/sources/upload
```

Use this for PDF upload.

Request:

```text
multipart/form-data
file=<pdf>
```

Response:

```json
{
  "sourceId": "uuid",
  "sourceType": "PDF_FILE",
  "fileName": "visa-annual-report.pdf",
  "mimeType": "application/pdf",
  "fileSizeBytes": 1048576,
  "extractionStatus": "PENDING"
}
```

Then create a brief with:

```json
{
  "inputType": "PDF_FILE",
  "sourceId": "uuid",
  "userQuery": "Focus on revenue growth, risks, and payment volume.",
  "requestedDepth": "AUTO",
  "researchScope": "RECOMMENDED_SOURCES"
}
```

Alternative simple path:

```text
POST /api/v1/briefs
```

can accept multipart form data later, but keeping file upload separate is cleaner for v0.3.

---

## List Briefs

```http
GET /api/v1/briefs
```

Query params:

```text
page
size
status
inputType
researchScope
requestedDepth
```

Response:

```json
{
  "items": [
    {
      "id": "uuid",
      "title": "Fintech industry analysis",
      "inputType": "QUESTION",
      "status": "COMPLETED",
      "planCodeUsed": "FREE",
      "requestedDepth": "AUTO",
      "researchScope": "RECOMMENDED_SOURCES",
      "createdAt": "2026-04-29T00:00:00Z",
      "generatedAt": "2026-04-29T00:01:00Z"
    }
  ],
  "page": 0,
  "size": 20,
  "totalItems": 1
}
```

---

## Get Brief By ID

```http
GET /api/v1/briefs/{briefId}
```

Response:

```json
{
  "id": "uuid",
  "title": "Fintech industry analysis",
  "inputType": "QUESTION",
  "userQuery": "Analyse the fintech industry for me.",
  "status": "COMPLETED",
  "planCodeUsed": "FREE",
  "requestedDepth": "AUTO",
  "researchScope": "RECOMMENDED_SOURCES",
  "researchScopeLabel": "Recommended Sources",
  "sourceMix": [
    "Established financial media where available",
    "Company and regulatory sources where available"
  ],
  "source": null,
  "generatedContent": {
    "quickSummary": "The fintech industry includes payments, lending, digital banking, wealthtech, insurtech, regtech, and crypto-related infrastructure.",
    "keyFacts": [
      "Fintech is not one single market.",
      "Regulation is a major factor.",
      "Many fintech firms both compete with and rely on traditional finance infrastructure."
    ],
    "keyTakeaways": [
      "Payments and embedded finance remain important growth areas.",
      "Profitability and regulation are key risks.",
      "Incumbents and fintechs often partner as much as they compete."
    ],
    "soWhat": "This matters because fintech changes how consumers and businesses access money, credit, payments, and financial tools.",
    "implicationMap": {
      "companyImpact": [],
      "industryImpact": [],
      "investorImpact": [],
      "regulatoryImpact": [],
      "whatToWatchNext": []
    },
    "bullBearNeutral": {
      "bull": [],
      "bear": [],
      "neutral": []
    },
    "financeConcepts": [],
    "risksAndUncertainties": [],
    "researchPathRecommendations": [],
    "studentTakeaway": "",
    "investorTakeaway": ""
  },
  "summaryMarkdown": "# Fintech industry analysis\n\n...",
  "confidenceScore": 78,
  "confidenceExplanation": "Confidence is medium-high because the brief uses stable industry structure, but specific company-level conclusions require current source retrieval.",
  "disclaimer": "This brief is for informational and educational purposes only and is not financial advice.",
  "createdAt": "2026-04-29T00:00:00Z",
  "generatedAt": "2026-04-29T00:01:00Z"
}
```

For source-based briefs, `source` should be populated:

```json
{
  "id": "uuid",
  "sourceType": "ARTICLE_URL",
  "title": "Original article title",
  "normalizedUrl": "https://example.com/article"
}
```

---

## Get Brief Generation Job

```http
GET /api/v1/briefs/{briefId}/job
```

Response:

```json
{
  "jobId": "uuid",
  "briefId": "uuid",
  "status": "RUNNING",
  "currentStep": "RETRIEVING_CONTEXT",
  "retryCount": 0,
  "maxRetries": 3,
  "startedAt": "2026-04-29T00:00:05Z",
  "completedAt": null,
  "errorCode": null,
  "errorMessage": null
}
```

---

## Delete Brief

```http
DELETE /api/v1/briefs/{briefId}
```

Response:

```json
{
  "success": true
}
```

---

# 5. Brief Source / Evidence Endpoints

## List Sources Used In Brief

```http
GET /api/v1/briefs/{briefId}/sources
```

Response:

```json
{
  "items": [
    {
      "id": "uuid",
      "sourceOrigin": "USER_PROVIDED",
      "sourceTitle": "Visa Annual Report",
      "sourceUrl": null,
      "publisher": "Visa",
      "sourceType": "FILING",
      "usageRole": "MAIN_EVIDENCE",
      "sourceCategoryLabel": "User-Provided Source",
      "publishedAt": null,
      "accessedAt": "2026-04-29T00:00:00Z",
      "snippet": "Revenue and payment volume details were used for the brief."
    }
  ]
}
```

Do not expose internal trust tiers directly.

---

# 6. Entity Endpoints

## Get Entity

```http
GET /api/v1/entities/{entityId}
```

Response:

```json
{
  "id": "uuid",
  "name": "Visa Inc.",
  "ticker": "V",
  "exchange": "NYSE",
  "entityType": "COMPANY",
  "country": "United States",
  "sector": "Financial Services",
  "industry": "Payments"
}
```

---

# 7. Research Scope Endpoints

## List Research Scopes

```http
GET /api/v1/research-scopes
```

Response:

```json
{
  "defaultResearchScope": "RECOMMENDED_SOURCES",
  "items": [
    {
      "code": "RECOMMENDED_SOURCES",
      "label": "Recommended Sources",
      "description": "Prioritises official, regulatory, company, government, and established financial media sources.",
      "recommended": true
    },
    {
      "code": "EXPANDED_MARKET_CONTEXT",
      "label": "Expanded Market Context",
      "description": "Adds selected market commentary, newsletters, videos, and specialist finance platforms.",
      "recommended": false
    },
    {
      "code": "SENTIMENT_AND_DISCUSSION",
      "label": "Sentiment & Discussion Signals",
      "description": "Adds limited public discussion sources for sentiment and market narrative only.",
      "recommended": false
    },
    {
      "code": "USER_PROVIDED_ONLY",
      "label": "User-Provided Sources Only",
      "description": "Uses the submitted source plus minimal entity metadata only.",
      "recommended": false
    }
  ]
}
```

This endpoint must not expose individual publisher/channel trust tiers.

---

# 8. Subscription / Entitlement Endpoints

## Get My Subscription

```http
GET /api/v1/subscription/me
```

Response:

```json
{
  "effectivePlanCode": "FREE",
  "accessSource": "FREE_DEFAULT",
  "startsAt": "2026-04-29T00:00:00Z",
  "endsAt": null,
  "dailyBriefLimit": 3,
  "briefsUsedToday": 1,
  "deepBriefsRemaining": 0,
  "premiumContextEnabled": false,
  "defaultResearchScope": "RECOMMENDED_SOURCES"
}
```

## Redeem Promo Code

```http
POST /api/v1/subscription/redeem-promo-code
```

Request:

```json
{
  "code": "ALPHA-BETA-2026"
}
```

Response:

```json
{
  "success": true,
  "effectivePlanCode": "PRO",
  "accessSource": "PROMO_CODE",
  "startsAt": "2026-04-29T00:00:00Z",
  "endsAt": "2026-05-29T00:00:00Z",
  "message": "Promo code redeemed successfully. Pro access is now active."
}
```

---

# 9. Share Endpoints

## Create Share Link

```http
POST /api/v1/briefs/{briefId}/share
```

Request:

```json
{
  "visibility": "UNLISTED",
  "allowDownload": false
}
```

Response:

```json
{
  "shareUrl": "https://alphabrief.ai/share/brf_9xK2pLmQ",
  "shareToken": "brf_9xK2pLmQ",
  "visibility": "UNLISTED",
  "allowDownload": false
}
```

## Disable Share Link

```http
DELETE /api/v1/briefs/{briefId}/share
```

Response:

```json
{
  "success": true
}
```

## Get Shared Brief

```http
GET /api/v1/shared-briefs/{shareToken}
```

Response should return a public-safe view model.

It must not expose:

- private user metadata
- raw upload metadata
- internal model traces
- internal trust tiers
- private premium context unless intentionally included

---

# 10. Export Endpoints

## Download Markdown

```http
GET /api/v1/briefs/{briefId}/download?type=MARKDOWN
```

## Create Export

```http
POST /api/v1/briefs/{briefId}/exports
```

Request:

```json
{
  "type": "PDF"
}
```

Response:

```json
{
  "exportId": "uuid",
  "briefId": "uuid",
  "type": "PDF",
  "status": "PENDING"
}
```

## Get Export Status

```http
GET /api/v1/briefs/{briefId}/exports/{exportId}
```

Response:

```json
{
  "exportId": "uuid",
  "type": "PDF",
  "status": "COMPLETED",
  "downloadUrl": "https://signed-url.example.com/file.pdf",
  "expiresAt": "2026-04-29T01:00:00Z"
}
```

---

# 11. Referral Endpoints

## Get My Referral Code

```http
GET /api/v1/me/referral-code
```

Response:

```json
{
  "referralCode": "BRUCE-ALPHA-123"
}
```

## Apply Referral Code

```http
POST /api/v1/referrals/apply
```

Request:

```json
{
  "referralCode": "BRUCE-ALPHA-123"
}
```

Response:

```json
{
  "success": true,
  "status": "SIGNED_UP"
}
```

## List My Referrals

```http
GET /api/v1/me/referrals
```

Response:

```json
{
  "items": [
    {
      "id": "uuid",
      "status": "ACTIVATED",
      "rewardGranted": false,
      "createdAt": "2026-04-29T00:00:00Z"
    }
  ]
}
```

---

# 12. Common Error Response

```json
{
  "errorCode": "SOURCE_EXTRACTION_FAILED",
  "message": "We could not extract readable content from this source.",
  "details": null,
  "timestamp": "2026-04-29T00:00:00Z"
}
```

---

# 13. Error Codes

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

---

# 14. Status Values

## Brief Status

```text
QUEUED
PROCESSING
COMPLETED
FAILED
```

## Job Status

```text
QUEUED
RUNNING
COMPLETED
FAILED
RETRYING
CANCELLED
```

## Extraction Status

```text
PENDING
EXTRACTED
FAILED
```

## Research Scope

```text
RECOMMENDED_SOURCES
EXPANDED_MARKET_CONTEXT
SENTIMENT_AND_DISCUSSION
USER_PROVIDED_ONLY
```

## Input Type

```text
QUESTION
ARTICLE_URL
YOUTUBE_URL
PDF_FILE
PASTED_TEXT
MIXED
```

---

# 15. Notes

For v0.3, brief generation should be designed around async behavior.

Recommended flow:

```text
POST /api/v1/briefs
→ returns briefId, jobId, and QUEUED/PROCESSING status

GET /api/v1/briefs/{briefId}
→ frontend polls until COMPLETED or FAILED

GET /api/v1/briefs/{briefId}/job
→ optional detailed job progress
```

The API should support source-based, question-based, and mixed brief creation from the beginning, even if deeper external retrieval is implemented in later internal slices of v0.3.
