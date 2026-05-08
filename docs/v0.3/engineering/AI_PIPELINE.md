# AlphaBrief v0.3 AI Pipeline

## Version

`v0.3 First Milestone — Projects → Canvas → Versioned Briefs`

## Status

AlphaBrief v0.3 is a market learning and research workspace.

The updated pipeline is no longer:

```text
Input → generate one research item / brief → save with tags
```

It is now:

```text
Project
→ focused chats and source analysis
→ candidate insight extraction
→ user-curated Canvas
→ versioned briefs generated from Canvas snapshots
```

The Canvas is the key quality layer. Brief generation should use the Canvas because it contains selected, edited, ordered, source-linked research blocks. Raw chat history is too noisy to be the primary formal-brief input. Humanity invented editing for a reason, then immediately tried to automate around it. We will not repeat that tiny tragedy.

---

# 1. Pipeline Modes

AlphaBrief v0.3 supports five AI workflows.

## 1.1 Chat Research Mode

Flexible market/finance exploration inside a project chat.

Examples:

```text
Why did Nvidia data center revenue growth decelerate?
What does this article imply for AI chip demand?
Explain Visa's cross-border volume trend.
```

Output:

```text
Structured assistant reply inside a project chat.
```

The reply may produce candidate Canvas blocks.

## 1.2 Source Analysis Mode

Analysis of attached sources inside chat.

Supported sources:

```text
ARTICLE_URL
YOUTUBE_URL
PDF_FILE
BROWSER_PAGE
```

Output:

```text
Chat reply grounded in source availability.
If full text is available → source-aware answer.
If only metadata is available → context answer with clear source-access note.
```

## 1.3 Canvas Candidate Extraction

After an assistant reply, AlphaBrief may extract candidate blocks:

```text
Claim
Quote
Note
Summary
Risk
Question
Metric
Bull case
Bear case
```

Candidates are suggestions, not truth. Users review, promote, edit, or dismiss them.

## 1.4 Brief Version Generation

Formal structured artifact generated from Canvas blocks.

Examples:

```text
Generate Nvidia thesis brief v1.
Update this brief from the latest Canvas.
Generate an earnings reaction brief from selected Canvas blocks.
```

Output:

```text
BriefVersion with content_markdown, structured sections, source/provenance summary, and optional what-changed summary.
```

## 1.5 Daily / Reflection Workflows

Optional later in v0.3:

```text
Daily research summary
Journal/reflection assistant
Learning goal progress summary
```

These should summarize structured activity and Canvas updates, not raw endless chat history.

---

# 2. Core Workflow

```text
1. User enters workspace.
2. User is placed in Catchall or selected Project.
3. User creates/opens a focused Chat.
4. User asks a question and optionally attaches Sources.
5. Backend creates user ChatTurn and queued assistant ChatTurn.
6. AI generates assistant response.
7. Response is validated and persisted.
8. Candidate Canvas extraction runs after response generation.
9. User promotes, edits, and reorders Canvas blocks.
10. User generates BriefVersion from selected/current Canvas blocks.
11. Later research updates Canvas.
12. User generates newer BriefVersion and sees what changed.
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
Direct user questions are stored as ChatTurns, not Source rows.
```

```text
PASTED_TEXT is not a primary v0.3 UX path.
Do not make users paste entire articles as the normal fallback.
```

---

# 4. Source Access Methods

Normalize source intake using `source_access_method`.

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

Analysis framing:

```text
SOURCE_ANALYSIS   # Source text/transcript is available
CONTEXT_ANALYSIS  # Full source unavailable; use metadata + public context
CHAT_ONLY         # No external source used
```

---

# 5. Chat Turn Generation Pipeline

```text
User submits message
→ owner check on chat/project
→ reject archived chat
→ validate attached source ownership/status
→ create completed user ChatTurn
→ create queued assistant ChatTurn
→ attach sources to user turn
→ schedule background assistant generation
→ return assistantTurnId for polling
```

## 5.1 Assistant Generation Background Flow

```text
1. Open fresh DB session inside background task.
2. Lock assistant turn; return if not QUEUED.
3. Set status = RUNNING.
4. Load chat, project, prior turns, attached sources, and optional Canvas context.
5. Build prompt.
6. Call AI provider.
7. Validate output.
8. Persist assistant turn.
9. Attach viewed sources to assistant turn.
10. Set assistant status = COMPLETED.
11. Trigger candidate extraction asynchronously or as a non-blocking follow-up.
```

## 5.2 Important Candidate Timing Rule

Candidate extraction should not delay visible assistant replies.

Recommended behavior:

```text
Mark assistant turn COMPLETED as soon as the reply is validated and saved.
Then run candidate extraction as a separate best-effort step.
```

If the implementation keeps extraction in the same background task, the UI should still treat candidates as optional and never show the assistant answer as failed just because candidate extraction failed.

---

# 6. Chat Prompt Context

Prompt context should include:

```text
- System role: market research assistant, educational not advice
- Current project metadata
- Short project context summary if available later
- Recent chat history, truncated from oldest first
- Current user message
- Attached source snippets and metadata
- Canvas context only when explicitly useful and budget-safe
```

Do not blindly inject the whole Canvas into every chat. That will become expensive, noisy, and emotionally needy.

## 6.1 Context Priority

For normal chat replies:

```text
1. Current user message
2. Attached sources
3. Recent relevant turns
4. Selected/high-signal Canvas blocks
5. Project metadata
```

For brief generation:

```text
1. Selected Canvas blocks
2. Canvas snapshot ordering
3. Provenance/source metadata
4. User brief instructions
5. Prior brief version, only for what-changed comparison
```

---

# 7. Source Pipeline

## 7.1 Article URL Pipeline

```text
User submits article URL
→ validate URL
→ block localhost/private IP fetch targets
→ create Source(source_type = ARTICLE_URL, source_access_method = SERVER_FETCH)
→ try safe public extraction
→ extract metadata: title, publisher, author, date, canonical URL
→ if readable text is available:
     mark source_access_status = FULL_TEXT_EXTRACTED
→ if readable text unavailable/blocked:
     mark source_access_status = METADATA_ONLY or BLOCKED
     retrieve related market/news/filing context if RECOMMENDED_CONTEXT
→ source becomes attachable once status is FULL_TEXT_EXTRACTED or METADATA_ONLY
```

Guardrails:

```text
Do not bypass paywalls, login walls, CAPTCHAs, or technical controls.
Do not store full copyrighted article text permanently by default.
Do not claim the article said something specific if only metadata was available.
```

## 7.2 Chrome Extension Pipeline

```text
User opens page
→ user clicks AlphaBrief extension
→ extension extracts readable text/metadata after explicit user action
→ user confirms submission
→ POST /sources/browser-extension
→ backend creates Source(source_type = BROWSER_PAGE)
→ mark FULL_TEXT_EXTRACTED or METADATA_ONLY
→ source appears in workspace and can be attached to chats
```

The extension is user-initiated page analysis, not a paywall bypasser, login-content scraper, or background crawler. An important sentence, because apparently entire legal risk profiles can fit inside one verb.

## 7.3 YouTube URL Pipeline

```text
User submits YouTube URL
→ validate URL
→ create Source(source_type = YOUTUBE_URL)
→ extract metadata
→ attempt transcript/caption access through allowed paths
→ if transcript available:
     source_access_method = YOUTUBE_TRANSCRIPT
     source_access_status = FULL_TEXT_EXTRACTED
→ else:
     source_access_method = YOUTUBE_METADATA
     source_access_status = METADATA_ONLY
     retrieve related context if enabled
```

Do not make v0.3 depend on always having YouTube transcripts.

## 7.4 PDF Pipeline

```text
User uploads PDF
→ validate file type/size
→ create Source(source_type = PDF_FILE, source_access_method = UPLOAD)
→ extract text where possible
→ scan and segment if long/complex
→ mark FULL_TEXT_EXTRACTED or FAILED
→ make source attachable when ready
```

---

# 8. Adaptive External Source Research Pipeline

This applies to every external source type, not only YouTube videos.

Applicable source types:

```text
ARTICLE_URL
YOUTUBE_URL
PDF_FILE
BROWSER_PAGE
```

Core rule:

```text
Never treat a large external source as one giant prompt blob.
Always scan, segment, estimate, and analyze with source-aware depth control.
```

## 8.1 Cheap Pre-Scan

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

The scan should not generate the final answer.

## 8.2 Segmentation / Chunk Mapping

Examples:

```text
YouTube video      → timestamped transcript segments
Article/news page  → article sections or paragraph groups
Earnings report    → report sections
PDF                → page and section chunks
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

## 8.3 Research Intent, Coverage, and Depth

For long/complex sources, ask for:

```text
Analysis intent:
- Quick Summary
- Market Impact
- Company Analysis
- Learning Mode
- Structured Brief Support

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

Research intent is a cost-control tool. If the user only cares about Nvidia and AI chips, do not Deep-analyze unrelated oil commentary just because it appeared in the same video. The database has suffered enough.

## 8.4 Pre-Analysis Warning Threshold

Show warning when:

```text
1. estimated_allowance_impact_percent > 50, or
2. researchMode = DEEP and estimate_confidence = LOW, or
3. source_complexity = VERY_HIGH.
```

Warning levels:

```text
< 30%    → no warning
30–50%   → inline estimate
50–80%   → pre-analysis warning
80%+     → strong warning; recommend Optimize Research or lower mode
```

Recommended prompt:

```text
AlphaBrief has completed a quick scan of this source.

This source appears long or complex, so full Deep analysis may use a large part of your current research allowance.

How would you like to continue?

[Continue with Deep]
[Switch to Standard]
[Switch to Quick]
[Optimize Research]
```

## 8.5 Optimize Research

`Optimize Research` lets AlphaBrief adjust analysis depth by section.

Behavior:

```text
Deep + Optimize Research ON:
- Deep for high-relevance/high-complexity sections
- Standard for medium-relevance sections
- Quick for low-relevance/background sections
- Full selected coverage is prioritized
```

## 8.6 Analysis Depth by Section

Final source-aware outputs should include:

```text
Analysis depth by section

00:00–12:30 · Fed policy and bond yields
Depth used: Deep
Reason: High relevance to selected market-impact intent

12:30–28:00 · Nvidia and AI chip demand
Depth used: Deep
Reason: High relevance to selected company/theme

28:00–41:00 · Oil and geopolitical risk
Depth used: Standard
Reason: Medium relevance to selected intent
```

---

# 9. Candidate Canvas Extraction Pipeline

After a validated assistant reply:

```text
assistant reply
→ candidate extraction prompt
→ return 0–N candidate blocks
→ validate block types and markdown
→ persist candidate_blocks as PENDING
→ frontend shows promote/dismiss UX
```

## 9.1 Candidate Extraction Rules

The model should extract only useful, durable research units:

```text
Good candidate:
“Nvidia's near-term upside depends on whether Blackwell ramps without major supply delays.”

Bad candidate:
“Nvidia is a company.”
```

Candidates should be:

```text
- specific
- editable
- source-aware when applicable
- useful for future brief generation
- not framed as personalized advice
```

## 9.2 Candidate Output Shape

```json
{
  "candidates": [
    {
      "block_type": "CLAIM",
      "title": "Blackwell ramp is the key catalyst",
      "content_markdown": "Nvidia's near-term thesis depends heavily on whether Blackwell ramps smoothly into hyperscaler deployments."
    }
  ]
}
```

## 9.3 Failure Rule

Candidate extraction failure should never fail the assistant reply.

```text
If extraction fails:
- log the error
- create no candidates
- keep assistant turn COMPLETED
```

---

# 10. Canvas Pipeline

The Canvas is a curated project artifact.

Canvas blocks can come from:

```text
- Manual user notes
- Promoted assistant turns
- Promoted AI candidates
- Source quotes or source notes
```

## 10.1 Manual Block Flow

```text
User clicks Add block
→ chooses block type
→ writes content
→ backend creates CanvasBlock(provenance_kind = MANUAL)
→ Canvas reorders/refreshes
```

## 10.2 Promote From Turn Flow

```text
User clicks + Canvas on assistant turn
→ frontend opens edit-before-promote form
→ user selects block type and edits content
→ backend creates CanvasBlock(provenance_kind = CHAT_TURN)
```

## 10.3 Promote Candidate Flow

```text
Assistant reply finishes
→ candidates appear
→ user promotes one or more
→ backend creates CanvasBlock(provenance_kind = CHAT_TURN or CANDIDATE)
→ candidate marked PROMOTED
```

## 10.4 Edit/Reorder Flow

```text
User edits content/title/type
→ PATCH CanvasBlock
→ updated block becomes new source material for future briefs
```

This is why Canvas must support customization. A non-editable Canvas is just a warehouse for extracted chat scraps, and warehouses are not research workflows.

---

# 11. Brief Version Generation Pipeline

Formal briefs are generated from Canvas snapshots.

```text
User chooses project brief or creates a new brief series
→ selects all or some active Canvas blocks
→ optional brief instructions/style
→ backend creates CanvasSnapshot
→ backend creates queued BriefVersion
→ AI generates structured brief from snapshot
→ output validation
→ persist BriefVersion
→ update Brief.current_version_id
→ create ResearchActivity
→ create UsageEvent
```

## 11.1 Brief Generation Prompt Context

Use:

```text
- selected Canvas blocks, in user-defined order
- block types and titles
- provenance summaries
- source metadata, not necessarily raw source text
- user instructions
- previous brief version for comparison only when requested
```

Do not use:

```text
- entire raw chat history
- all project sources by default
- hidden unreviewed AI memory
```

## 11.2 Brief Output Shape

```json
{
  "title": "Nvidia AI Infrastructure Thesis Brief v2",
  "brief_type": "THESIS_MEMO",
  "executive_summary": "...",
  "core_thesis": "...",
  "evidence_base": [],
  "risks_and_uncertainties": [],
  "bull_case": [],
  "bear_case": [],
  "open_questions": [],
  "what_changed_since_previous": "...",
  "learning_takeaway": "...",
  "source_and_canvas_note": "Generated from 18 Canvas blocks and 7 linked sources.",
  "confidence_label": "MEDIUM",
  "disclaimer": "For educational and informational purposes only."
}
```

## 11.3 Brief Types

```text
COMPANY_RESEARCH
EARNINGS_BREAKDOWN
SOURCE_SUMMARY
MARKET_EVENT_EXPLAINER
THESIS_MEMO
```

## 11.4 Versioning Rule

Every generated brief is a snapshot.

```text
Brief = series
BriefVersion = generated document at a point in time
CanvasSnapshot = exact input used
```

When the Canvas changes materially after the latest brief version, the UI should show:

```text
Your Canvas has changed since this brief was generated.
Generate an updated version?
```

## 11.5 What Changed Summary

When generating v2+, compare against previous version and summarize:

```text
- New claims added
- Removed/archived claims
- New risks
- Changed assumptions
- Thesis direction change
- Confidence change
- New open questions
```

---

# 12. Validation Rules

Treat AI output as untrusted.

Validate:

```text
- Markdown is renderable/safe
- JSON shape matches workflow
- Required fields exist
- Disclaimer exists where needed
- No personalized financial advice
- No fabricated source claims
- If source is METADATA_ONLY, output clearly states that full source text was unavailable
- Candidate blocks use allowed block types
- Brief version references Canvas snapshot, not raw chat transcript
- Citations/source markers reference real attached or linked sources
```

If validation fails:

```text
1. Retry once with repair prompt
2. If still invalid, mark target entity FAILED
3. Save safe error message
```

---

# 13. Project Memory Policy

Project memory is deferred.

v0.3 should use explicit context only:

```text
- project metadata
- selected Canvas blocks
- recent chat history
- attached source metadata/text snippets
```

Do not add hidden long-term memory until:

```text
- Canvas workflow works
- brief versioning works
- users trust editable project state
```

Bad memory is not personalization. It is hallucination with a filing cabinet.

---

# 14. Research Activity Creation

Create `ResearchActivity` for meaningful actions:

```text
CREATED_PROJECT
ASKED_QUESTION
ATTACHED_SOURCE
GENERATED_CHAT_REPLY
PROMOTED_TO_CANVAS
CREATED_CANVAS_BLOCK
UPDATED_CANVAS_BLOCK
GENERATED_BRIEF_VERSION
CREATED_JOURNAL_ENTRY
GENERATED_DAILY_SUMMARY
```

These events power:

```text
Daily summaries
Research streaks later
Learning goal progress later
Project timeline later
```

---

# 15. Updated v0.3 Pipeline Rule

The v0.3 pipeline should prove this loop:

```text
Project
→ chat/source exploration
→ AI-assisted candidate extraction
→ user-curated Canvas
→ generated BriefVersion
→ later Canvas updates
→ updated BriefVersion + what changed
```

---

# 16. Future Pipeline Additions

Move these to later versions:

```text
ThreadSummary auto-promote
ProjectMemory
Proactive project suggestions
Daily project briefs
Monitoring and contradiction flagging
Watchlist event ingestion
Company timeline auto-refresh
Claim-level citation verification
Full multi-agent research planner
Portfolio-aware implication layer
Visual market map / mind map
```

---

# 17. MVP Demo Target

The first compelling AlphaBrief demo should show:

```text
1. Open Nvidia project.
2. Ask a question and attach a source.
3. Assistant replies.
4. Candidate claims appear.
5. User promotes and edits them.
6. Canvas visibly fills up.
7. User generates Brief v1.
8. User adds more research.
9. User generates Brief v2.
10. AlphaBrief explains what changed.
```

That is the product. Not another chat history with a nicer suit.
