# Alphabrief v0.3 AI Pipeline

## Version

`v0.3 MVP`

## Purpose

This document defines how Alphabrief turns a user-submitted source into a structured investor brief.

## Pipeline Overview

```text
1. Validate input
2. Extract content
3. Clean content
4. Detect financial entities
5. Retrieve context based on user tier
6. Construct AI prompt
7. Generate structured brief
8. Validate AI output
9. Persist brief
10. Return result to user
```

## Step 1: Validate Input

Supported source types:

```text
ARTICLE_URL
YOUTUBE_URL
PASTED_TEXT
```

Validation should reject:

- Empty input
- Unsupported URL types
- Extremely short text
- Input above configured length
- Invalid URL
- Suspicious private/internal URLs where possible

Suggested limits:

| Rule | Free | Premium |
|---|---:|---:|
| Max pasted text length | 8,000 characters | 30,000 characters |
| Max briefs per day | 3 | 50 |

## Step 2: Extract Content

### Article URL

```text
URL → Article extractor → Title + body text
```

### YouTube URL

```text
URL → Transcript extractor → Transcript text + video metadata
```

### Pasted Text

```text
Text input → Cleaning service → Normalized raw text
```

The extracted content should be stored in the `sources` table.

## Step 3: Clean Content

The cleaning stage should:

- Remove repeated whitespace
- Remove irrelevant boilerplate where possible
- Normalize line breaks
- Preserve important finance-specific wording
- Avoid accidentally removing numbers, tickers, percentages, dates, and financial terms

## Step 4: Detect Financial Entities

The system should identify:

- Company names
- Tickers
- Sectors
- Industries
- Indexes
- Commodities
- Crypto assets
- Macro factors

Recommended v0.3 approach:

```text
Rule-based ticker/company detection
        +
AI extraction for ambiguous financial entities
        +
Normalization against market/company data provider
```

Example entity extraction output:

```json
[
  {
    "name": "Apple Inc.",
    "ticker": "AAPL",
    "entityType": "COMPANY",
    "sector": "Technology",
    "industry": "Consumer Electronics"
  }
]
```

## Step 5: Retrieve Context

### Free Tier Context

Free users should receive:

- Basic company/entity explanation
- Source-specific entity insight
- Basic risks

### Premium Tier Context

Premium users should additionally receive:

- Industry context
- Competitor context
- Macro context
- Political/regulatory context
- Market sentiment where available
- Second-order implications

## Step 6: Construct AI Prompt

The prompt should include:

- User tier
- Source type
- Cleaned source text
- Detected entities
- Retrieved context
- Required output schema
- Financial disclaimer requirement

The AI should be instructed to:

- Stay grounded in the source and retrieved context
- Avoid making unsupported claims
- Separate source-specific summary from external context
- Avoid giving personalized financial advice
- Return structured JSON

## Step 7: Generate Structured Brief

Recommended output sections:

```text
title
sourceSummary
keyTakeaways
detectedEntities
risks
opportunities
investorQuestions
disclaimer
```

For premium users, entity insights may include:

```text
industryContext
macroContext
politicalRegulatoryContext
competitorContext
```

## Step 8: Validate AI Output

Treat AI output as untrusted.

Validation should check:

- Required fields exist
- Output is valid JSON if JSON mode is used
- Arrays are arrays
- Strings are not empty
- Disclaimer exists
- Premium-only fields are not exposed incorrectly to free users
- No obviously unsafe financial advice wording appears

If validation fails, either:

1. Retry once with a repair prompt, or
2. Mark brief as failed with `AI_OUTPUT_INVALID`

## Step 9: Persist Brief

Store:

- Source
- Brief
- Detected entities
- Entity insights
- Status
- Tier used
- Generation timestamp
- Error message, if failed

## Step 10: Return Result

Recommended flow:

```text
POST /briefs
→ returns briefId and PROCESSING

GET /briefs/{briefId}
→ returns latest brief status
```

## AI Output Example

```json
{
  "title": "Apple demand concerns and services growth",
  "sourceSummary": "The source discusses Apple's recent demand concerns and the role of services revenue in supporting margins.",
  "keyTakeaways": [
    "iPhone demand remains a key concern.",
    "Services revenue may help offset hardware weakness.",
    "Investors should watch regional sales trends."
  ],
  "detectedEntities": [
    {
      "name": "Apple Inc.",
      "ticker": "AAPL",
      "entityType": "COMPANY",
      "sourceSpecificInsight": "The source focuses on Apple's hardware demand and services growth.",
      "companyContext": "Apple is a large technology company with revenue from hardware, services, and software ecosystems.",
      "premiumContext": {
        "industryContext": "Premium smartphone demand and AI device cycles may affect future growth.",
        "macroContext": "Consumer spending and interest-rate expectations may influence demand.",
        "politicalRegulatoryContext": "App store regulation and China exposure remain relevant risks.",
        "competitorContext": "Samsung and other smartphone competitors may pressure device sales."
      }
    }
  ],
  "risks": [
    "Hardware demand may weaken.",
    "Regulatory pressure could affect services margins."
  ],
  "opportunities": [
    "Services growth may support profitability.",
    "A future AI device cycle could improve upgrade demand."
  ],
  "investorQuestions": [
    "Is services growth enough to offset hardware weakness?",
    "How exposed is Apple to China demand risk?"
  ],
  "disclaimer": "This brief is for informational purposes only and is not financial advice."
}
```

## Important Principle

The AI pipeline should not only summarize.

It should transform messy financial content into a repeatable investor briefing format.
