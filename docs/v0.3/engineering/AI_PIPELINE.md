# AlphaBrief v0.3 AI Pipeline

## Version

`v0.3 First Milestone`

## Status

This pipeline reflects AlphaBrief's positioning as:

```text
Market learning + research workspace
Ask Mode + Brief Mode
Daily research summary
Journal/reflection assistant
Learning goals
Chrome Extension-ready source analysis
Adaptive external-source research for URLs, YouTube, PDFs, earnings reports, articles, and browser pages
```

The earlier pipeline focused on turning every input into a structured brief. v0.3 should be more flexible: not every answer needs to be a formal brief.

This version also adds the Chrome extension as a source ingestion adapter. The extension is not a scraping loophole or a magical lawsuit umbrella. It is a user-initiated way to analyze the page the user is already viewing.

This version also adds the v0.3 adaptive research architecture. Every external source should go through a cheap scan, segmentation/chunking, source-complexity estimation, user intent selection, research-depth selection, allowance risk checks, and optional Optimize Research. This applies to YouTube videos, finance news/articles, earnings reports, PDFs, company pages, browser-extension captured pages, and pasted URLs.

---

# 1. Pipeline Modes

AlphaBrief v0.3 supports four AI workflows.

## 1.1 Ask Mode Analysis

Flexible finance/source analysis.

Examples:

```text
Explain this Visa earnings report.
What does this market news mean?
Why did a stock fall after good earnings?
```

Output:

```text
ChatGPT-like structured response, but finance-aware and research-oriented.
```

## 1.2 Brief Mode Generation

Formal structured artifact.

Examples:

```text
Generate a company brief for Visa.
Create an earnings breakdown for this report.
Create a market event explainer for this Fed decision.
```

Output:

```text
Formal saved brief with stable sections.
```

## 1.3 Daily Research Summary

AI-generated recap of what the user researched today.

Output:

```text
Topics researched
Companies mentioned
Sources analyzed
Key insights
Open questions
Suggested follow-ups
```

## 1.4 Reflection Assistant

AI-assisted, user-owned journal writing.

Output:

```text
Small writing suggestions, prompts, and learning points.
```

The AI should not fully replace the user reflection by default. Humanity has enough ghostwritten introspection already.

---

# 2. Shared Intake Pipeline

All AI workflows share the following early steps:

```text
1. Validate request
2. Identify workflow mode
3. Create or reference Source if source input exists
4. Determine source access method and extraction status
5. Extract/normalize source text if applicable
6. If full source unavailable, build metadata + API context fallback
7. Run cheap source scan for all external sources
8. Segment/chunk source content where applicable
9. Estimate source complexity, entity density, topic density, and allowance impact
10. Ask user for analysis intent, coverage, and research mode when needed
11. If estimated impact is above the warning threshold, show a pre-analysis warning
12. Create ResearchItem when output should be saved
13. Create GenerationJob and AnalysisRun
14. Build prompt context by segment or source chunk
15. Generate output section-by-section when applicable
16. Validate output
17. Persist output, analysis depth by section, and activity
18. Track usage/cost
19. Return result or status
```

---

# 3. Input Types

Supported v0.3 input types:

```text
QUESTION
ARTICLE_URL
YOUTUBE_URL
PDF_FILE
BROWSER_PAGE
MIXED
```

Important rules:

```text
Direct user questions are stored on ResearchItem.original_user_input.
They are not stored as Source rows.
```

```text
PASTED_TEXT is not a primary v0.3 UX path.
Do not make users paste entire articles as the normal fallback.
```

---

# 4. Source Access Methods

AlphaBrief should normalize source intake using `source_access_method`.

```text
SERVER_FETCH         # Backend attempts safe public URL extraction
BROWSER_EXTENSION    # User clicked extension on page they were viewing
API_CONTEXT          # Related market/news/filing context from allowed APIs
UPLOAD               # User uploaded a PDF/file
YOUTUBE_METADATA     # YouTube title/channel/description metadata
YOUTUBE_TRANSCRIPT   # Transcript/caption data from an allowed path
```

Source access status:

```text
PENDING
FULL_TEXT_EXTRACTED
METADATA_ONLY
BLOCKED
FAILED
```

Analysis modes:

```text
SOURCE_BRIEF   # Source text/transcript is available
CONTEXT_BRIEF  # Full source unavailable; use metadata + public context
```

Research modes:

```text
QUICK      # Fast understanding, low depth, minimal context
STANDARD   # Balanced default analysis with key implications and risks
DEEP       # Richer segment-level analysis for complex or high-value sources
```

Completion strategies:

```text
STRICT_REQUESTED_MODE  # Keep the requested research mode unless the user intervenes
OPTIMIZE_RESEARCH      # Adapt depth by section to finish the source efficiently
```

Coverage options for long or complex sources:

```text
FULL_SOURCE
SELECTED_TOPICS
SELECTED_ENTITIES
CUSTOM_QUESTION
```

The selected research mode describes desired depth. The selected coverage describes how much of the source should be analyzed. These are different controls and should not be collapsed into one confused little dropdown.

---

# 5. Article URL Pipeline

```text
User submits article URL
→ validate URL
→ block localhost/private IP fetch targets
→ create Source(source_type = ARTICLE_URL, source_access_method = SERVER_FETCH)
→ try safe public extraction
→ extract metadata: title, publisher, author, date, canonical URL
→ if readable text is available:
     mark source_access_status = FULL_TEXT_EXTRACTED
     select analysis_mode = SOURCE_BRIEF
→ if readable text is unavailable/blocked:
     mark source_access_status = METADATA_ONLY or BLOCKED
     select analysis_mode = CONTEXT_BRIEF
     retrieve related market/news/filing context if researchScope = RECOMMENDED_CONTEXT
→ create ResearchItem + GenerationJob
→ generate output
→ save source metadata + generated analysis
```

## URL Extraction Guardrails

Do not:

```text
- bypass paywalls
- bypass login walls
- bypass CAPTCHAs
- ignore clear technical access controls
- store full copyrighted article text permanently by default
- claim the article said something if only metadata was available
```

---

# 6. Chrome Extension Source Pipeline

The Chrome extension allows AlphaBrief to analyze the current page from the user's browser after explicit user action.

```text
User opens article page
→ user clicks AlphaBrief Chrome extension
→ extension reads page DOM after user action
→ extension extracts readable article text if available
→ extension extracts metadata: title, publisher, URL, publish date, OpenGraph/JSON-LD
→ extension shows preview/status to user
→ user clicks Generate AlphaBrief
→ extension sends payload to POST /api/v1/sources/browser-extension
→ backend creates Source(source_type = BROWSER_PAGE, source_access_method = BROWSER_EXTENSION)
→ backend decides source_access_status
→ backend creates ResearchItem + GenerationJob
→ pipeline generates Source Brief or Context Brief
→ output is saved in Research Log with tags/company links
```

## Extension Full-Text Case

```text
BROWSER_EXTENSION payload includes extractedText
→ mark source_access_status = FULL_TEXT_EXTRACTED
→ select analysis_mode = SOURCE_BRIEF
→ summarize exact source
→ extract claims and key numbers
→ enrich with market APIs/filings if researchScope = RECOMMENDED_CONTEXT
→ validate that source-specific claims are grounded in extracted text
```

## Extension Metadata-Only Case

```text
BROWSER_EXTENSION payload has title/URL/metadata only
→ mark source_access_status = METADATA_ONLY
→ select analysis_mode = CONTEXT_BRIEF
→ detect company/ticker/topic from metadata
→ retrieve related news, market data, filings, or company context
→ generate context brief
→ clearly state that full page text was unavailable
```

## Extension Compliance Rule

The extension should be positioned as:

```text
User-initiated page analysis of content the user chooses to process.
```

It should not be positioned as:

```text
A paywall bypasser, login-content scraper, or background crawler.
```

Annoyingly important difference. Tiny sentence, giant risk profile.

---

# 7. YouTube URL Pipeline

```text
User submits YouTube URL
→ validate URL
→ create Source(source_type = YOUTUBE_URL)
→ extract metadata: title, channel, description, publish date if available
→ attempt transcript/caption access only through allowed paths
→ if transcript is available:
     source_access_method = YOUTUBE_TRANSCRIPT
     source_access_status = FULL_TEXT_EXTRACTED
     analysis_mode = SOURCE_BRIEF
→ if transcript is unavailable:
     source_access_method = YOUTUBE_METADATA
     source_access_status = METADATA_ONLY
     analysis_mode = CONTEXT_BRIEF
     retrieve related company/topic/market context if possible
→ create ResearchItem + GenerationJob
→ generate output
```

Do not make v0.3 depend on always having YouTube transcripts. That path is fragile, because naturally video platforms were not designed around your startup roadmap.

---

# 8. Ask Mode Pipeline

```text
User submits question/source
→ validate input
→ create or reference Source if source exists
→ determine SOURCE_BRIEF vs CONTEXT_BRIEF if source is involved
→ create ResearchItem(item_type = ASK_ANALYSIS)
→ create GenerationJob(job_type = ASK_ANALYSIS)
→ extract/normalize source text if needed
→ retrieve recommended context if enabled
→ detect companies/topics
→ generate structured analysis
→ validate answer
→ save output_markdown and output_json
→ create ResearchActivity(ASKED_QUESTION or ANALYZED_SOURCE or ANALYZED_BROWSER_PAGE)
→ create UsageEvent
→ return ResearchItem
```

## Ask Mode output shape

```json
{
  "title": "Visa earnings impact analysis",
  "quick_answer": "...",
  "analysis_mode": "SOURCE_BRIEF",
  "source_access_status": "FULL_TEXT_EXTRACTED",
  "what_happened": "...",
  "why_it_matters": "...",
  "market_implications": [],
  "companies_or_topics_mentioned": [],
  "risks_and_uncertainties": [],
  "finance_concepts": [],
  "follow_up_questions": [],
  "confidence_label": "MEDIUM",
  "confidence_explanation": "...",
  "disclaimer": "For educational and informational purposes only."
}
```

---

# 9. Brief Mode Pipeline

```text
User selects Brief Mode
→ user chooses or implies brief_type
→ validate subject/source/question
→ create or reference Source if source exists
→ determine SOURCE_BRIEF vs CONTEXT_BRIEF if source is involved
→ create ResearchItem(item_type = BRIEF)
→ create Brief linked to ResearchItem
→ create GenerationJob(job_type = BRIEF_GENERATION)
→ extract/normalize source text if needed
→ retrieve recommended context if enabled
→ detect companies/topics/events
→ select brief template
→ generate formal structured brief
→ validate required sections
→ persist Brief.sections + ResearchItem.output_json
→ create ResearchActivity(GENERATED_BRIEF)
→ create UsageEvent
→ return Brief
```

## v0.3 brief types

```text
COMPANY_RESEARCH
EARNINGS_BREAKDOWN
SOURCE_SUMMARY
MARKET_EVENT_EXPLAINER
```

## Company Research Brief sections

```text
companyOverview
businessModel
recentContext
growthDrivers
risks
competitorContext
bullCase
bearCase
whatToWatchNext
learningTakeaway
disclaimer
```

## Earnings Breakdown sections

```text
headlineResult
keyNumbers
whatChanged
managementCommentary
guidanceAndOutlook
positiveSignals
negativeSignals
whatToWatchNext
learningTakeaway
disclaimer
```

## Source Summary sections

```text
mainTakeaway
keyClaims
importantNumbers
sourcePerspective
missingContext
whyItMatters
sourceAccessNote
followUpQuestions
disclaimer
```

## Market Event Explainer sections

```text
eventSummary
whyItMatters
whoIsAffected
shortTermImpact
longTermImpact
risksAndUncertainties
whatToWatchNext
learningTakeaway
disclaimer
```

---

# 10. Context Brief Fallback Pipeline

Use this when full source text is unavailable.

```text
Source has metadata only or extraction blocked
→ extract title, URL, publisher, date, ticker/company/topic hints
→ retrieve allowed context sources if researchScope = RECOMMENDED_CONTEXT
     - financial news API
     - market data API
     - SEC/company filings where relevant
     - company profile/fundamentals where relevant
→ generate context brief
→ include sourceAccessNote
→ avoid claiming the original article/video said something specific
```

Recommended source access note:

```text
The full source text was unavailable, so this analysis uses source metadata plus related public market/news/filing context.
```

This makes failure useful instead of just shrugging in JSON.

---

# 11. Daily Research Summary Pipeline

```text
User clicks Generate Today's Summary
→ fetch today's ResearchActivity rows
→ fetch today's completed ResearchItems
→ fetch linked tags, companies, and sources
→ create or update DailyResearchSummary
→ optionally create ResearchItem(item_type = DAILY_SUMMARY)
→ generate summary
→ persist topics, companies, insights, open questions, follow-ups
→ create ResearchActivity(GENERATED_DAILY_SUMMARY)
→ return summary
```

## Daily summary output shape

```json
{
  "summary_date": "2026-05-04",
  "topics_covered": [],
  "companies_mentioned": [],
  "sources_analyzed": [],
  "key_insights": [],
  "open_questions": [],
  "suggested_followups": [],
  "summary_markdown": "..."
}
```

### Important rule

Daily summaries should summarize structured activity, not raw endless chat history. Otherwise, welcome back to the scroll swamp.

---

# 12. Reflection Assistant Pipeline

```text
User opens Journal
→ user links optional DailyResearchSummary
→ user writes or starts draft
→ user clicks reflection assist
→ backend sends limited context and selected assist step
→ AI returns one suggestion or prompt
→ user edits and saves JournalEntry
```

## Reflection assist steps

```text
STARTER_SUMMARY
SUGGEST_LEARNING_POINTS
SUGGEST_OPEN_QUESTIONS
DRAFT_NEXT_PARAGRAPH
```

## Guardrail

The reflection assistant should encourage the user to write and revise. It can help, but it should not pretend the AI had the user's personal experience.

---

# 13. Research Activity Creation

Create a `ResearchActivity` row for meaningful actions:

```text
ASKED_QUESTION
ANALYZED_SOURCE
ANALYZED_BROWSER_PAGE
GENERATED_BRIEF
SAVED_RESEARCH
CREATED_JOURNAL_ENTRY
CREATED_GOAL
GENERATED_DAILY_SUMMARY
```

These events power:

- Daily summaries
- Weekly summaries later
- Research streaks later
- Learning goal progress later

---

# 14. Validation Rules

Treat AI output as untrusted.

Validation should check:

- Required fields exist
- Markdown is renderable/safe
- JSON shape matches the workflow
- Disclaimer exists where needed
- No personalized financial advice
- No fabricated source claims
- No unsupported claim that a source said something it did not say
- If analysis mode is CONTEXT_BRIEF, output must clearly state that full source text was unavailable
- If source_access_status is METADATA_ONLY, output must not present the source as fully read
- Confidence label is present for AI analysis

If validation fails:

```text
1. Retry once with a repair prompt
2. If still invalid, mark GenerationJob as FAILED
3. Save a safe error message
```

---

# 15. v0.3 Research Scope

Keep research scope simple in v0.3:

```text
USER_PROVIDED_ONLY
RECOMMENDED_CONTEXT
```

Do not add broad social sentiment or source ranking in v0.3. That belongs to future deep research.


---

# 17. Adaptive External Source Research Pipeline

This pipeline applies to every external source type, not only YouTube videos.

Applicable sources:

```text
ARTICLE_URL
YOUTUBE_URL
PDF_FILE
BROWSER_PAGE
COMPANY_PAGE
EARNINGS_REPORT
FINANCE_NEWS_ARTICLE
```

Core rule:

```text
Never treat a large external source as one giant prompt blob.
Always scan, segment, estimate, and analyze with source-aware depth control.
```

## 17.1 Cheap Pre-Scan

Before full analysis, AlphaBrief should run a cheap scan.

The scan should detect:

```text
- source length
- source type
- transcript/text availability
- major topics
- companies/entities/tickers mentioned
- macro themes/events mentioned
- section/chunk boundaries
- estimated source complexity
- estimated allowance impact
- confidence in the estimate
```

The cheap scan should not generate the final answer. It exists to protect cost, improve focus, and prevent a half-completed output. Tiny thing called planning, apparently still underrated.

## 17.2 Segmentation / Chunk Mapping

Every external source should be mapped into segments or chunks.

Examples:

```text
YouTube video      → timestamped transcript segments
Article/news page  → article sections or paragraph groups
Earnings report    → report sections: highlights, income statement, guidance, risks, management commentary
PDF                → page/section chunks
Browser page       → extracted readable sections plus metadata
```

Each segment should store:

```text
segment_index
start/end position or timestamp
title/topic summary
entities detected
topic tags
estimated complexity
relevance to user intent
requested research mode
actual research mode used
```

## 17.3 Research Intent, Coverage, and Depth

For normal short sources, AlphaBrief can use defaults.

For long or complex sources, AlphaBrief should ask the user to choose:

```text
Analysis intent:
- Quick Summary
- Market Impact
- Company Analysis
- Learning Mode
- Structured Brief

Coverage:
- Full source
- Selected topics
- Selected entities
- Custom question

Research mode:
- Quick
- Standard
- Deep
```

Research intent is also a cost-control tool. If a user only cares about Nvidia and AI chips, AlphaBrief should not Deep-analyze unrelated oil, banking, and crypto sections just because they appeared in the same 90-minute finance video.

## 17.4 Pre-Analysis Warning Threshold

After the cheap scan, AlphaBrief should estimate the allowance impact.

Warning rule:

```text
If one analysis run is estimated to consume more than 50% of the user's current available research allowance, warn the user before generation begins.
```

Do not warn for small or normal usage. A product that nags on every click becomes a tiny bureaucrat with a loading spinner.

Warning levels:

```text
< 30%    → no warning
30–50%   → small inline usage estimate only
50–80%   → pre-analysis warning
80%+     → strong warning; recommend Optimize Research or lower mode
```

Also warn when:

```text
- Deep mode is selected
- source is long or high complexity
- estimate confidence is low
- projected completion risk is high
```

Recommended pre-analysis prompt:

```text
AlphaBrief has completed a quick scan of this source.

This source appears long or complex, so the full content may not be fully analyzed in Deep mode with your current research allowance.

If you continue in Deep mode, AlphaBrief may ask you later to lower the depth for remaining sections so the full analysis can still be completed.

How would you like to continue?

[Continue with Deep]
[Switch to Standard]
[Switch to Quick]
```

## 17.5 Optimize Research

`Optimize Research` is a user-facing feature that allows AlphaBrief to adapt analysis depth by section.

User-facing description:

```text
Optimize Research lets AlphaBrief adjust analysis depth by section, so important parts get deeper analysis while lower-priority sections use lighter analysis.
```

Behavior:

```text
Deep + Optimize Research ON:
- Deep for high-relevance/high-complexity sections
- Standard for medium-relevance sections
- Quick for low-relevance or background sections
- Full source completion is prioritized
```

This should be recommended for long sources, dense earnings reports, and mixed-topic market videos.

## 17.6 Mid-Analysis Downgrade Prompt

During analysis, AlphaBrief should track actual usage against projected usage.

If remaining allowance may not support the remaining source at the requested depth, pause and ask:

```text
AlphaBrief may not be able to complete the remaining sections in Deep mode with your current research allowance.

To finish the full source, you can:

1. Switch remaining sections to Standard
2. Switch lower-priority sections to Quick
3. Optimize automatically
4. Stop here and save partial analysis
5. Continue later after your allowance recovers
```

Buttons:

```text
[Optimize and finish]
[Switch remaining to Standard]
[Save partial result]
[Continue later]
```

If the user enabled Optimize Research before generation, AlphaBrief can adapt automatically within the promised behavior, but it should still record what changed.

## 17.7 Analysis Depth by Section

Final outputs for segmented sources should include an `Analysis depth by section` block.

Example:

```text
Analysis depth by section

00:00–12:30 · Fed policy and bond yields
Depth used: Deep
Reason: High relevance to selected market-impact intent

12:30–28:00 · Nvidia and AI chip demand
Depth used: Deep
Reason: High relevance to selected companies and AI market theme

28:00–41:00 · Oil and geopolitical risk
Depth used: Standard
Reason: Medium relevance to selected intent

41:00–60:00 · China trade and tariffs
Depth used: Standard
Reason: Important macro context, but secondary to selected focus

60:00–75:00 · Banking sector commentary
Depth used: Quick
Reason: Lower relevance to selected focus
```

The output should make downgraded sections rerunnable later:

```text
Some sections were analyzed at lower depth to complete the full source within your current research allowance.
You can rerun selected sections in Deep mode after your allowance recovers.
```

## 17.8 Completion Priority

For long external sources, optimize around this priority order:

```text
1. Finish the full selected coverage
2. Preserve the user's main research intent
3. Use Deep mode where it matters most
4. Downgrade lower-priority sections first
5. Be transparent about actual depth used
6. Let the user rerun downgraded sections later
```

---

# 18. Updated v0.3 Pipeline Rule

The v0.3 pipeline should prove this loop:

```text
Source/question
→ cheap scan if external source
→ intent + coverage + research mode selection
→ allowance risk check
→ analysis generation
→ analysis depth by section if segmented
→ saved ResearchItem
→ follow-up, compare, tag, or rerun selected sections later
```

---

# 19. Future Pipeline Additions

Move these to later versions:

- Watchlist event ingestion
- Company timeline auto-refresh
- Notification generation
- Thesis support/weakening evaluation
- Claim-level citation verification
- Multi-agent research planner
- Social sentiment extraction
- Portfolio-aware implication layer
- Browser research basket
- Multi-source research project generation
- Extension-based highlight-to-analyze
