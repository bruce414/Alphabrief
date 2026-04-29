# Alphabrief v0.3 API Spec

## Version

`v0.3 MVP`

## Base Path

```text
/api/v1
```

## API Principles

The API should be:

- Predictable
- Frontend-friendly
- Authenticated by default
- Consistent in error shape
- Designed to support async brief generation later

## Authentication Endpoints

### Register

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
  "subscriptionTier": "PRO"
}
```

### Login

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
  "subscriptionTier": "PRO"
}
```

### Logout

```http
POST /api/v1/auth/logout
```

Response:

```json
{
  "success": true
}
```

## User Endpoints

### Get Current User

```http
GET /api/v1/me
```

Response:

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "displayName": "Bruce",
  "subscriptionTier": "PRO",
  "createdAt": "2026-04-29T00:00:00Z"
}
```

### Update Current User

```http
PATCH /api/v1/me
```

Request:

```json
{
  "displayName": "New Name"
}
```

Response:

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "displayName": "New Name",
  "subscriptionTier": "FREE"
}
```

## Brief Endpoints

### Create Brief

```http
POST /api/v1/briefs
```

Request:

```json
{
  "sourceType": "ARTICLE_URL",
  "input": "https://example.com/article",
  "requestedDepth": "AUTO"
}
```

Supported `sourceType` values:

```text
ARTICLE_URL
YOUTUBE_URL
PASTED_TEXT
```

Supported `requestedDepth` values:

```text
AUTO
BASIC
DEEP
```

Response:

```json
{
  "briefId": "uuid",
  "status": "PROCESSING"
}
```

### List Briefs

```http
GET /api/v1/briefs
```

Query params:

```text
page
size
status
sourceType
```

Response:

```json
{
  "items": [
    {
      "id": "uuid",
      "title": "Apple earnings summary",
      "sourceType": "ARTICLE_URL",
      "status": "COMPLETED",
      "tierUsed": "FREE",
      "createdAt": "2026-04-29T00:00:00Z"
    }
  ],
  "page": 0,
  "size": 20,
  "totalItems": 1
}
```

### Get Brief By ID

```http
GET /api/v1/briefs/{briefId}
```

Response:

```json
{
  "id": "uuid",
  "title": "Apple earnings summary",
  "status": "COMPLETED",
  "tierUsed": "FREE",
  "source": {
    "id": "uuid",
    "sourceType": "ARTICLE_URL",
    "title": "Original article title",
    "normalizedUrl": "https://example.com/article"
  },
  "sourceSummary": "Summary text.",
  "keyTakeaways": [
    "Takeaway 1",
    "Takeaway 2"
  ],
  "entities": [
    {
      "id": "uuid",
      "name": "Apple Inc.",
      "ticker": "AAPL",
      "entityType": "COMPANY",
      "sourceSpecificInsight": "Insight from the source.",
      "companyContext": "Basic company context.",
      "premiumLocked": true
    }
  ],
  "risks": [
    "Risk 1"
  ],
  "opportunities": [
    "Opportunity 1"
  ],
  "investorQuestions": [
    "Question 1"
  ],
  "disclaimer": "This brief is for informational purposes only and is not financial advice.",
  "createdAt": "2026-04-29T00:00:00Z",
  "generatedAt": "2026-04-29T00:01:00Z"
}
```

### Delete Brief

```http
DELETE /api/v1/briefs/{briefId}
```

Response:

```json
{
  "success": true
}
```

## Entity Endpoints

### Get Entity

```http
GET /api/v1/entities/{entityId}
```

Response:

```json
{
  "id": "uuid",
  "name": "Apple Inc.",
  "ticker": "AAPL",
  "exchange": "NASDAQ",
  "entityType": "COMPANY",
  "country": "United States",
  "sector": "Technology",
  "industry": "Consumer Electronics"
}
```

## Subscription Endpoints

### Get My Subscription

```http
GET /api/v1/subscription/me
```

Response:

```json
{
  "subscriptionTier": "FREE",
  "dailyBriefLimit": 3,
  "briefsUsedToday": 1,
  "premiumContextEnabled": false
}
```

## Common Error Response

```json
{
  "errorCode": "SOURCE_EXTRACTION_FAILED",
  "message": "We could not extract readable content from this source.",
  "details": null,
  "timestamp": "2026-04-29T00:00:00Z"
}
```

## Error Codes

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
```

## Status Values

### Brief Status

```text
QUEUED
PROCESSING
COMPLETED
FAILED
```

### Extraction Status

```text
PENDING
EXTRACTED
FAILED
```

## Notes

For v0.3, brief generation can start synchronously if needed, but the API should be designed around async behavior.

Recommended flow:

```text
POST /briefs
→ returns briefId and PROCESSING

GET /briefs/{briefId}
→ frontend polls until COMPLETED or FAILED
```
