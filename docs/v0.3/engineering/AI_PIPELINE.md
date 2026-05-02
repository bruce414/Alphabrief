# AlphaBrief v0.3 AI Pipeline

## Version

`v0.3 First Milestone`

## Status

This document treats **v0.3 as the first major AlphaBrief milestone**.

Earlier v0.1/v0.2 ideas are now internal implementation slices inside v0.3:

```text
v0.3 foundation slice
v0.3 source/question brief flow
v0.3 agentic/deep analysis flow
v0.3 validation before launch
```

## Purpose

This document defines how AlphaBrief turns either:

```text
1. A user-submitted financial source
2. A direct finance / market research question
3. A combination of both
```

into a structured finance research brief.

The central product artifact is the **Brief**.

Sources are optional inputs, not the parent object of every brief.

---

# 1. Pipeline Overview

AlphaBrief v0.3 should support three request types.

## 1.1 Source-Based Brief

Examples:

```text
Analyse this Visa earnings report.
Summarise this fintech article.
Turn this YouTube video into a finance brief.
```

Supported inputs:

```text
ARTICLE_URL
YOUTUBE_URL
PDF_FILE
PASTED_TEXT
```

## 1.2 Question-Based Brief

Examples:

```text
Analyse the fintech industry for me.
What are the main risks facing Tesla?
How do interest rates affect banks?
Is Visa threatened by fintech disruption?
```

A question-based brief may not have a user-provided source.

## 1.3 Mixed Brief

Examples:

```text
Use this Visa report and explain whether fintech disruption is a serious risk.
Analyse this earnings report and compare it with current industry trends.
```

A mixed brief includes both:

```text
source_id
user_query
```

---

# 2. Recommended v0.3 Pipeline

```text
1. Validate request
2. Classify input type
3. Check usage limit
4. Check entitlement if Pro/deep analysis is requested
5. Create source if input is source-based
6. Create brief
7. Create brief_generation_job
8. Extract/transcribe source content if applicable
9. Clean content
10. Detect financial entities
11. Detect events and claims
12. Resolve research scope
13. Select allowed research channels
14. Retrieve context if allowed
15. Store brief_sources and external_context_items where applicable
16. Construct AI prompt
17. Generate structured brief
18. Validate AI output
19. Persist generated_content, summary_markdown, entities, events, claims, citations where applicable
20. Update usage and cost tracking
21. Mark job completed or failed
22. Return result to user
```

---

# 3. Step 1: Validate Request

The request should support:

```text
QUESTION
ARTICLE_URL
YOUTUBE_URL
PDF_FILE
PASTED_TEXT
MIXED
```

Validation should reject:

- Empty input
- Unsupported input type
- Unsupported URL type
- Invalid URL
- Suspicious private/internal URL
- Extremely short pasted text
- Input above configured limit
- PDF above configured size limit
- Unsupported file MIME type
- Direct finance question that is too vague to process safely
- Requests that ask for personalised financial advice

Suggested limits:

| Rule | Free | Pro / Student Pro / Beta |
|---|---:|---:|
| Max pasted text length | 8,000 characters | 30,000 characters |
| Max PDF size | 5 MB | 20 MB |
| Max briefs per day | 3 | 50 |
| Deep briefs | 0 or limited preview | plan/credit controlled |

---

# 4. Step 2: Classify Input Type

The backend should classify the request into one of:

```text
QUESTION
ARTICLE_URL
YOUTUBE_URL
PDF_FILE
PASTED_TEXT
MIXED
```

## Source-based request

```json
{
  "inputType": "ARTICLE_URL",
  "input": "https://example.com/fintech-article",
  "userQuery": null
}
```

## Question-based request

```json
{
  "inputType": "QUESTION",
  "input": "Analyse the fintech industry for me",
  "userQuery": "Analyse the fintech industry for me"
}
```

## Mixed request

```json
{
  "inputType": "MIXED",
  "input": "file_id_or_url",
  "userQuery": "Focus on implications for Visa and Mastercard"
}
```

### Important rule

Direct finance questions should be stored on:

```text
briefs.user_query
```

not in the `sources` table.

The `sources` table should store user-provided material such as:

```text
ARTICLE_URL
YOUTUBE_URL
PDF_FILE
PASTED_TEXT
```

---

# 5. Step 3: Resolve Research Scope

AlphaBrief should allow the user to choose a research scope before external retrieval.

Default:

```text
RECOMMENDED_SOURCES
```

User-facing labels should describe the research breadth, not rank individual publishers.

| Research scope | User-facing meaning | Internal behavior |
|---|---|---|
| RECOMMENDED_SOURCES | Uses official, regulatory, company, government, and established financial media sources | Searches channels internally marked as suitable for primary or strong supporting evidence |
| EXPANDED_MARKET_CONTEXT | Adds selected commentary, newsletters, videos, and specialist finance platforms | Allows broader context, but labels opinion-based material clearly |
| SENTIMENT_AND_DISCUSSION | Adds limited public discussion sources for sentiment and market narrative only | Social/community sources may inform sentiment but must not verify factual claims |
| USER_PROVIDED_ONLY | Uses only submitted source plus minimal metadata | Useful for narrow source-focused briefs |

## Compliance and UI principle

Do not show user-facing rankings like:

```text
Bloomberg = Tier 1
Newsletter X = Tier 3
Reddit = Low Trust
```

Use safe labels:

```text
Recommended Sources
Expanded Market Context
Sentiment & Discussion Signals
User-Provided Sources Only
```

Internally, AlphaBrief can still store:

```text
internal_trust_tier
usage_role
source_quality
source_category_label
```

---

# 6. Step 4: Create Source If Applicable

## Article URL

```text
URL → Article extractor → title + body text
```

## YouTube URL

```text
URL → Transcript extractor → transcript text + video metadata
```

## PDF File

```text
PDF upload → storage → PDF text extraction → title/metadata + raw text
```

## Pasted Text

```text
Text input → cleaning service → normalized raw text
```

## Question

```text
No source row required.
Store question in briefs.user_query.
```

---

# 7. Step 5: Create Brief

Every request creates a `briefs` row.

For source-based brief:

```text
input_type = ARTICLE_URL / YOUTUBE_URL / PDF_FILE / PASTED_TEXT
source_id = sources.id
user_query = optional user instruction
```

For question-based brief:

```text
input_type = QUESTION
source_id = null
user_query = user question
```

For mixed brief:

```text
input_type = MIXED
source_id = sources.id
user_query = user instruction/question
```

Initial status:

```text
brief_status = QUEUED
```

---

# 8. Step 6: Create Brief Generation Job

The backend should create a `brief_generation_jobs` row.

Recommended initial state:

```text
status = QUEUED
current_step = VALIDATING_INPUT
```

Possible current steps:

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

Recommended async-friendly flow:

```text
POST /api/v1/briefs
→ create source if needed
→ create brief with QUEUED status
→ create brief_generation_job
→ return briefId
→ worker processes job
→ frontend polls GET /api/v1/briefs/{briefId}
```

---

# 9. Step 7: Extract and Clean Content

For source-based and mixed briefs, extract raw text.

The cleaning stage should:

- Remove repeated whitespace
- Remove irrelevant boilerplate where possible
- Normalize line breaks
- Preserve tickers, numbers, percentages, dates, financial terms, and named entities
- Avoid accidentally removing accounting/finance details
- Preserve transcript structure when useful

For question-based briefs, there may be no extracted source text. The pipeline should continue using:

```text
briefs.user_query
```

---

# 10. Step 8: Detect Financial Entities

The system should identify:

- Companies
- Tickers
- Sectors
- Industries
- Indexes
- Commodities
- Crypto assets
- Currencies
- Macro factors
- Regions
- Regulatory/political factors where relevant

Recommended v0.3 approach:

```text
Rule-based ticker/company detection
+
AI extraction for ambiguous entities
+
Normalization against market/company data provider where available
```

Example output:

```json
[
  {
    "name": "Visa Inc.",
    "ticker": "V",
    "entityType": "COMPANY",
    "sector": "Financial Services",
    "industry": "Payments"
  }
]
```

---

# 11. Step 9: Detect Events and Claims

For deeper analysis, AlphaBrief should detect:

## Events

Examples:

```text
EARNINGS
GUIDANCE
REGULATION
TARIFF
PRODUCT_LAUNCH
MACRO
SUPPLY_CHAIN
COMPETITOR_NEWS
INDUSTRY_TREND
MARKET_MOVEMENT
```

## Claims

Examples:

```text
FACTUAL
INTERPRETIVE
FORECAST
RISK
OPPORTUNITY
```

This supports AlphaBrief's unique positioning:

```text
not just “what did the source say?”
but “what does this imply, who is affected, and what evidence supports it?”
```

For early internal slices of v0.3, claims/events can first live in `generated_content`.

As the pipeline matures, persist them into:

```text
brief_events
brief_claims
brief_citations
```

---

# 12. Step 10: Select Allowed Research Channels

Before retrieving external context, map selected `researchScope` to allowed internal channels.

Recommended mapping:

```text
RECOMMENDED_SOURCES
→ official filings, company IR, regulatory sources, government/macro data, established financial media

EXPANDED_MARKET_CONTEXT
→ recommended sources plus selected commentary, newsletters, videos, and specialist platforms

SENTIMENT_AND_DISCUSSION
→ expanded sources plus limited social/community sources for sentiment only

USER_PROVIDED_ONLY
→ submitted source plus minimal entity/company metadata only
```

Important rule:

```text
Social/community sources must not be used as primary evidence for factual claims.
```

---

# 13. Step 11: Retrieve Context

Context retrieval should be controlled by:

```text
1. Effective user plan / entitlement
2. Requested depth
3. Selected research scope
4. Input type
```

## Free / Basic Context

Free users should usually receive:

- Basic company/entity explanation
- Source-specific entity insight
- Basic risks
- Key takeaways
- Basic “So What?” explanation

## Pro / Deep Context

Pro/deep users may receive:

- Industry context
- Competitor context
- Macro context
- Political/regulatory context
- Market sentiment where available
- Second-order implications
- Contradictions/tensions across sources
- Claim/evidence mapping
- What would change this view

---

# 14. Step 12: Store Research Evidence

Store retrieved or used sources in:

```text
brief_sources
```

Store external context in:

```text
external_context_items
```

For user-provided sources, use:

```text
source_origin = USER_PROVIDED
```

For agent-discovered sources, use:

```text
source_origin = AGENT_DISCOVERED
```

For system/context metadata, use:

```text
source_origin = SYSTEM_CONTEXT
```

---

# 15. Step 13: Construct AI Prompt

The prompt should include:

- Input type
- User query if present
- User tier / effective plan
- Requested depth
- Research scope
- Cleaned source text if present
- Detected entities
- Detected events and claims where available
- Retrieved context
- Source category/evidence-role metadata
- Required output schema
- Disclaimer requirement

The AI should be instructed to:

- Stay grounded in source and retrieved context
- Clearly separate source-specific summary from external context
- Distinguish facts, interpretation, and speculation
- Avoid unsupported claims
- Treat social/community material as sentiment only
- Avoid personalised financial advice
- Explain implications, not just summaries
- Return structured JSON

---

# 16. Step 14: Generate Structured Brief

Recommended output sections:

```text
title
researchScope
sourceMix
quickSummary
keyFacts
keyTakeaways
soWhat
implicationMap
bullBearNeutral
risksAndUncertainties
financeConcepts
sourceEvidencePanel
claims
contradictionsOrTensions
assignmentAngles
researchPathRecommendations
whatWouldChangeThisView
studentTakeaway
investorTakeaway
confidenceScore
confidenceExplanation
disclaimer
```

For source-based briefs, include:

```text
sourceSummary
```

For question-based briefs, include:

```text
researchQuestion
researchApproach
```

For premium/deep briefs, include richer:

```text
industryContext
macroContext
politicalRegulatoryContext
competitorContext
secondOrderImplications
```

---

# 17. Step 15: Validate AI Output

Treat AI output as untrusted.

Validation should check:

- Output is valid JSON if JSON mode is used
- Required fields exist
- Arrays are arrays
- Strings are not empty
- Disclaimer exists
- No unsupported personalised financial advice
- Premium-only fields are not exposed incorrectly to free users
- Source evidence does not misrepresent weak/sentiment sources
- Social/community sources are not used as factual proof
- Confidence explanation exists when confidence score exists

If validation fails:

```text
1. Retry once with a repair prompt
2. If still invalid, mark brief as failed with AI_OUTPUT_INVALID
```

---

# 18. Step 16: Persist Brief

Persist:

- Brief status
- Input type
- User query
- Source if applicable
- Research scope
- Source mix
- Generated content JSON
- Summary markdown
- Detected entities
- Entity insights
- Brief sources
- External context items
- Events, claims, citations where implemented
- Model provider/name
- Prompt version
- Pipeline version
- Disclaimer/disclaimer version
- Token and estimated cost data where available
- Generation timestamp
- Error message if failed

---

# 19. Step 17: Return Result

Recommended flow:

```text
POST /api/v1/briefs
→ returns briefId and PROCESSING/QUEUED

GET /api/v1/briefs/{briefId}
→ returns latest status and final brief when completed
```

---

# 20. Structured AI Output Example

```json
{
  "title": "Fintech industry analysis: payments, regulation, and competition",
  "inputType": "QUESTION",
  "researchQuestion": "Analyse the fintech industry for me",
  "researchScope": "RECOMMENDED_SOURCES",
  "sourceMix": [
    "Company and regulatory sources where available",
    "Established financial media where available",
    "Market data/context where available"
  ],
  "quickSummary": "The fintech industry continues to evolve across digital payments, banking, lending, wealth management, and infrastructure. The strongest themes are payment innovation, regulatory pressure, embedded finance, and competition between banks, fintech startups, and large technology platforms.",
  "keyFacts": [
    "Fintech is not one single market; it includes payments, lending, digital banking, wealthtech, insurtech, regtech, and crypto-related infrastructure.",
    "Regulation is a major factor because fintech businesses often touch payments, consumer finance, banking, data, and compliance.",
    "Many fintech companies compete with banks but also rely on banks, card networks, cloud providers, and regulated partners."
  ],
  "soWhat": "The fintech industry matters because it changes how consumers and businesses access money, payments, credit, banking services, and financial tools. The impact is not limited to startups; it also affects banks, card networks, payment processors, regulators, merchants, and consumers.",
  "implicationMap": {
    "companyImpact": [
      "Banks may face pressure on customer experience and digital product speed.",
      "Payment networks may partner with fintechs but also face alternative payment rails."
    ],
    "industryImpact": [
      "Competition may shift from standalone apps toward embedded financial services.",
      "Compliance and licensing may become a stronger barrier to entry."
    ],
    "investorImpact": [
      "Investors need to separate growth narratives from sustainable unit economics.",
      "Regulatory risk and funding conditions can materially change fintech valuations."
    ],
    "regulatoryImpact": [
      "Regulators may increase scrutiny around consumer protection, data privacy, payments, and lending."
    ],
    "whatToWatchNext": [
      "Interest-rate environment",
      "Payment regulation",
      "Bank-fintech partnerships",
      "Profitability of major fintech firms",
      "Adoption of account-to-account payments"
    ]
  },
  "bullBearNeutral": {
    "bull": [
      "Fintech can expand access, reduce friction, and create more efficient financial infrastructure."
    ],
    "bear": [
      "Many fintech models face pressure from regulation, funding costs, competition, and weak profitability."
    ],
    "neutral": [
      "Fintech may not replace traditional finance directly; it may become integrated into existing financial infrastructure."
    ]
  },
  "financeConcepts": [
    {
      "term": "Unit economics",
      "simpleExplanation": "Whether each customer or transaction is profitable after direct costs.",
      "whyItMatters": "A fintech company can grow quickly but still lose money if customer acquisition costs or credit losses are too high.",
      "howToUseIt": "When analysing fintech firms, compare user growth with margins, customer acquisition cost, default risk, and retention."
    }
  ],
  "risksAndUncertainties": [
    "Regulatory changes may limit fees or business models.",
    "Higher interest rates can pressure lending-focused fintechs.",
    "Customer acquisition costs may make growth less profitable than headline numbers suggest."
  ],
  "researchPathRecommendations": [
    "Compare fintech subsectors: payments, lending, digital banking, wealthtech, and regtech.",
    "Study Visa and Mastercard as payment infrastructure examples.",
    "Compare fintech startups with incumbent banks.",
    "Research how regulation affects payment fees and consumer lending."
  ],
  "studentTakeaway": "For an assignment, fintech is best analysed as a set of business models and infrastructure changes rather than as one broad industry.",
  "investorTakeaway": "For investors, the key question is whether a fintech business has durable economics, regulatory resilience, and a defensible role in the financial system.",
  "confidenceScore": 78,
  "confidenceExplanation": "Confidence is medium-high because the analysis uses stable industry structure and common finance concepts, but specific company-level conclusions would require current source retrieval.",
  "disclaimer": "This brief is for informational and educational purposes only and is not financial advice."
}
```

---

# 21. Important Principle

AlphaBrief should not only summarise.

It should transform messy financial information or finance questions into a repeatable research brief that explains:

```text
What happened
Why it matters
Who it affects
What the implications are
What evidence supports it
What remains uncertain
What to research next
```
