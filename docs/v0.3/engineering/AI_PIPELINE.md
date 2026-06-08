# AlphaBrief v0.3 AI Pipeline

## Version

`v0.3 First Milestone — One Ask Box → Smart Source Detection → Freeform Canvas → On-demand Briefs`

## Status

AlphaBrief v0.3 is a market learning and research workspace.

The pipeline is no longer:

```text
Input → generate one research item / brief → save with tags
```

It is also no longer:

```text
Project → chat → curated Canvas → brief must be generated from Canvas
```

The latest direction is:

```text
Project
→ one Ask box / Agent chat
→ smart input and source detection
→ source-aware analysis when relevant
→ AI suggests Canvas candidates
→ user builds understanding in a freeform Canvas
→ project Memory accumulates explicit understanding
→ briefs are generated on request from selected context
```

The Canvas is the user's living thinking space. Brief generation can use Canvas context, especially selected elements or clusters, but it should not require the Canvas. This avoids punishing users who simply paste a link and ask for a brief, which would be a silly hill for software to die on.

---

# 1. Pipeline Modes

AlphaBrief v0.3 supports these AI workflows internally.

## 1.1 Unified Ask / Agent Mode

The visible user experience should be one main Ask box.

Examples:

```text
Why did Nvidia data center revenue growth decelerate?
https://www.reuters.com/... Analyze this for market implications.
https://youtube.com/... Summarize the bull and bear case.
Generate a brief from this thread and the two linked sources.
Add the key risks from this answer to Canvas.
```

Output:

```text
Structured assistant reply inside a project chat.
```

The reply may produce candidate Canvas elements.

## 1.2 Smart Input Detection

After the user sends a message, AlphaBrief should detect:

```text
- user intent
- source type, if any
- source URLs or uploaded files
- whether the request needs source ingestion
- whether the request is a Canvas action
- whether the request is a brief-generation request
```

Detected input types:

```text
QUESTION
ARTICLE_URL
YOUTUBE_URL
PDF_FILE
BROWSER_PAGE
FILING_URL
IMAGE_FILE
MIXED
```

Detected internal intent types:

```text
GENERAL_ASK
SOURCE_ANALYSIS
ARTICLE_ANALYSIS
YOUTUBE_ANALYSIS
PDF_ANALYSIS
FILING_ANALYSIS
BRIEF_GENERATION
CANVAS_ACTION
COMPARISON
```

These are internal routes, not separate required user modes. Humans should not need to label their own request before the system understands it. That is what the machine is for.

## 1.3 Source Analysis Mode

Analysis of attached or detected sources inside chat.

Supported sources:

```text
ARTICLE_URL
YOUTUBE_URL
PDF_FILE
BROWSER_PAGE
FILING_URL
IMAGE_FILE
```

Output:

```text
Chat reply grounded in source availability.
If full text/transcript is available → source-aware answer.
If only metadata is available → context answer with clear source-access note.
```

## 1.4 Canvas Candidate Extraction

After an assistant reply, AlphaBrief may extract candidate Canvas elements:

```text
Claim
Evidence
Quote
Data point
Note
Summary
Risk
Question
Catalyst
Bull case
Bear case
Mind-map node suggestion
```

Candidates are suggestions, not truth. Users review, promote, edit, or dismiss them.

## 1.5 Canvas AI Helper Mode

AI can help with selected Canvas areas:

```text
Summarize this area
Find contradictions in this area
Turn this cluster into open questions
Create a simple mind map from this answer
Generate a brief from this selected cluster
```

Outputs should be draft elements or assistant replies, not irreversible Canvas mutations.

## 1.6 Brief Version Generation

Formal structured artifact generated from selected context.

Examples:

```text
Generate a Nvidia thesis brief from this thread.
Generate a source summary from these two articles.
Generate a bear-case memo from this Canvas cluster.
Generate a market research brief from full project context.
```

Output:

```text
BriefVersion with content_markdown, structured sections, source/provenance summary, generated-from summary, and optional what-changed summary.
```

## 1.7 Daily / Reflection Workflows

Optional later in v0.3:

```text
Daily research summary
Journal/reflection assistant
Learning goal progress summary
```

These should summarize structured activity, Canvas updates, and Memory changes, not raw endless chat history.

---

# 2. Core Workflow

```text
1. User enters workspace.
2. User is placed in Catchall or selected Project.
3. User creates/opens a focused Chat/Thread.
4. User asks naturally in one Ask box.
5. Backend detects intent and source type.
6. If URLs/files are present, backend creates/attaches Source rows.
7. Backend creates user ChatTurn and queued assistant ChatTurn.
8. AI generates assistant response.
9. Response is validated and persisted.
10. Candidate Canvas extraction runs after response generation.
11. User may add AI blocks, notes, images, or mind-map elements to Canvas.
12. Project Memory may be updated explicitly or by user-approved AI refresh.
13. User generates BriefVersion on request from selected context.
14. Later research can update chat, sources, Canvas, or Memory.
15. User generates newer BriefVersion and sees what changed.
```

---

# 3. Input Handling Rules

Supported v0.3 input types:

```text
QUESTION
ARTICLE_URL
YOUTUBE_URL
PDF_FILE
BROWSER_PAGE
FILING_URL
IMAGE_FILE
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

```text
If a message contains a URL, AlphaBrief should auto-detect whether it is article, YouTube, filing, PDF, or unknown URL.
```

```text
If source access fails, do not pretend the source body was read.
Use metadata + allowed context and disclose the limitation.
```

---

# 4. Source Access Methods

Normalize source intake using `source_access_method`.

```text
SERVER_FETCH         # Backend attempts safe public URL extraction
BROWSER_EXTENSION    # User clicked extension on page they were viewing
API_CONTEXT          # Related market/news/filing context from allowed APIs
UPLOAD               # User uploaded a PDF/file/image
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

# 5. Unified Ask Generation Pipeline

```text
User submits message
→ owner check on chat/project
→ reject archived chat
→ detect intent and source inputs
→ create/reuse Source records when URLs/files are detected
→ validate attached source ownership/status
→ create completed user ChatTurn
→ create queued assistant ChatTurn
→ attach sources to user turn
→ decide pipeline route
→ schedule background assistant generation
→ return assistantTurnId for polling
```

## 5.1 Pipeline Router

Routing logic:

```text
No source + normal question
→ GENERAL_ASK

Article/news URL detected
→ create Source(ARTICLE_URL)
→ ARTICLE_ANALYSIS

YouTube URL detected
→ create Source(YOUTUBE_URL)
→ YOUTUBE_ANALYSIS

PDF/file uploaded or attached
→ create Source(PDF_FILE)
→ PDF_ANALYSIS

SEC/filing URL detected
→ create Source(FILING_URL)
→ FILING_ANALYSIS

User asks to generate a brief
→ BRIEF_GENERATION

User asks to add/move/summarize Canvas material
→ CANVAS_ACTION
```

## 5.2 Assistant Generation Background Flow

```text
1. Open fresh DB session inside background task.
2. Lock assistant turn; return if not QUEUED.
3. Set status = RUNNING.
4. Load chat, project, prior turns, attached sources, optional Memory, and optional Canvas context.
5. Build prompt according to route.
6. Call AI provider.
7. Validate output.
8. Persist assistant turn.
9. Attach viewed sources to assistant turn.
10. Track usage.
11. Set assistant status = COMPLETED.
12. Trigger candidate extraction asynchronously or as a non-blocking follow-up.
```

## 5.3 Candidate Timing Rule

Candidate extraction should not delay visible assistant replies.

Recommended behavior:

```text
Mark assistant turn COMPLETED as soon as the reply is validated and saved.
Then run candidate extraction as a separate best-effort step.
```

If extraction fails:

```text
- log the error
- create no candidates
- keep assistant turn COMPLETED
```

---

# 6. Chat Prompt Context

Prompt context should include:

```text
- System role: market research assistant, educational not advice
- Current project metadata
- Current user message
- Attached or detected source snippets/metadata
- Recent chat history, truncated from oldest first
- Project Memory if relevant and budget-safe
- Selected Canvas elements only when explicitly useful
```

Do not blindly inject the whole Canvas into every chat. A giant whiteboard is not “context,” it is an expensive soup.

## 6.1 Context Priority for Normal Chat Replies

```text
1. Current user message
2. Attached/detected sources
3. Recent relevant turns
4. Project Memory summary/entities/open questions
5. Selected/high-signal Canvas elements only if relevant
6. Project metadata
```

## 6.2 Context Priority for Brief Generation

```text
1. User's selected brief context
2. Current thread, if selected
3. Selected sources, if selected
4. Project Memory, if selected
5. Selected Canvas elements or cluster, if selected
6. Prior brief version, only for what-changed comparison
```

Do not use:

```text
- entire raw project history by default
- every Canvas element by default
- all project sources by default
- hidden unreviewed AI memory
```

---

# 7. Source Pipeline

## 7.1 Article URL Pipeline

```text
User pastes article URL in Ask box or Source picker
→ detect URL type
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

The extension is user-initiated page analysis, not a paywall bypasser, login-content scraper, or background crawler.

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

## 7.4 PDF / File Pipeline

```text
User uploads PDF/file/image
→ validate file type/size
→ create Source(source_type = PDF_FILE or IMAGE_FILE, source_access_method = UPLOAD)
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
FILING_URL
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

For long/complex sources, ask for intent only when needed. Do not make every user configure a spaceship launch just to summarize one article.

Possible internal values:

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
→ return 0–N candidate elements
→ validate element types and markdown
→ persist candidate_elements as PENDING
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
- useful for future understanding
- optionally useful for future brief generation
- not framed as personalized advice
```

## 9.2 Candidate Output Shape

```json
{
  "candidates": [
    {
      "element_type": "CLAIM",
      "title": "Blackwell ramp is the key catalyst",
      "content_markdown": "Nvidia's near-term thesis depends heavily on whether Blackwell ramps smoothly into hyperscaler deployments.",
      "suggested_position": {
        "x": 640,
        "y": 280,
        "width": 320,
        "height": 180
      }
    }
  ]
}
```

---

# 10. Canvas Pipeline

The Canvas is a freeform visual thinking space, not a formal brief outline.

Canvas elements can come from:

```text
- Manual user notes
- User-uploaded images/screenshots
- Promoted assistant turns
- Promoted AI candidates
- Source quotes or source notes
- Generated mind-map nodes
```

## 10.1 Manual Element Flow

```text
User clicks Text / Image / Node
→ chooses element type
→ writes content or uploads image
→ frontend chooses x/y/size
→ backend creates CanvasElement(provenance_kind = MANUAL)
→ Canvas refreshes
```

## 10.2 Promote From Turn Flow

```text
User clicks Add to Canvas on assistant turn
→ frontend opens edit-before-promote form
→ user selects element type and edits content
→ frontend sends x/y/size
→ backend creates CanvasElement(provenance_kind = CHAT_TURN)
```

## 10.3 Promote Candidate Flow

```text
Assistant reply finishes
→ candidates appear
→ user promotes one or more
→ backend creates CanvasElement(provenance_kind = CANDIDATE)
→ candidate marked PROMOTED
```

## 10.4 Source Quote / Evidence Flow

```text
User selects short source excerpt or writes source note
→ user clicks Add to Canvas
→ backend creates CanvasElement(provenance_kind = SOURCE)
→ element keeps provenance_source_id
```

## 10.5 Move / Resize / Edit Flow

```text
User drags, resizes, edits, styles, or archives element
→ PATCH CanvasElement
→ updated element persists as part of Canvas state
```

## 10.6 Mind Map Flow

```text
User creates nodes and connector lines manually
OR user asks AI to create a draft mind map from selected answer/source
→ backend creates CanvasElements + CanvasConnections
→ user edits labels, positions, and relationships
```

Minimum v0.3 mind map elements:

```text
Node
Connection line
Group/frame
Label
Basic style/tag
```

---

# 11. Project Memory Pipeline

Project Memory preserves explicit accumulated understanding.

Sources of memory updates:

```text
- user edits Memory tab manually
- user asks AI to refresh Memory from recent project activity
- system suggests memory updates after repeated themes appear
```

Memory should include:

```text
- project summary
- key entities and tickers
- recurring themes
- current conclusions
- open questions
- important risks/catalysts
```

Memory should be visible. Invisible product memory turns into a haunted filing cabinet. Nobody needs that.

---

# 12. Brief Version Generation Pipeline

Briefs are generated from selected context snapshots.

```text
User clicks Generate Brief
→ frontend offers/contextually infers context choices
→ backend creates BriefContextSnapshot
→ backend creates queued BriefVersion
→ AI generates structured brief from snapshot
→ output validation
→ persist BriefVersion
→ update Brief.current_version_id
→ create ResearchActivity
→ create UsageEvent
```

## 12.1 Context Options

Supported context scopes:

```text
CURRENT_THREAD
SELECTED_SOURCES
SELECTED_CANVAS
CANVAS_CLUSTER
PROJECT_MEMORY
FULL_PROJECT
CUSTOM
```

Recommended v0.3 default:

```text
current thread + linked sources + optional project memory
```

Canvas should be included when:

```text
- user selected Canvas elements
- user selected a Canvas cluster
- user requests full project context
- user explicitly says “use my Canvas”
```

## 12.2 Brief Generation Prompt Context

Use:

```text
- selected chat turns, if any
- selected source summaries/snippets/metadata, if any
- selected Canvas elements, if any
- Project Memory, if requested
- user instructions
- previous brief version for comparison only when requested
```

Do not use:

```text
- entire raw chat history by default
- entire Canvas by default
- all project sources by default
- hidden unreviewed AI memory
```

## 12.3 Brief Output Shape

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
  "generated_from_note": "Generated from current thread, 2 linked sources, project memory, and 4 selected Canvas elements.",
  "confidence_label": "MEDIUM",
  "disclaimer": "For educational and informational purposes only."
}
```

## 12.4 Brief Types

```text
COMPANY_RESEARCH
EARNINGS_BREAKDOWN
SOURCE_SUMMARY
MARKET_EVENT_EXPLAINER
THESIS_MEMO
BULL_BEAR_MEMO
```

## 12.5 Versioning Rule

Every generated brief is a snapshot.

```text
Brief = series
BriefVersion = generated document at a point in time
BriefContextSnapshot = exact selected context used
```

## 12.6 What Changed Summary

When generating v2+, compare against previous version and summarize:

```text
- New claims added
- Removed/changed claims
- New risks
- Changed assumptions
- Thesis direction change
- Confidence change
- New open questions
```

---

# 13. Validation Rules

Treat AI output as untrusted.

Validate:

```text
- markdown is non-empty and sanitized
- JSON schema matches expected route
- source references map to actual attached/selected sources
- metadata-only sources are disclosed properly
- no fabricated source claims
- no personalized investment advice
- disclaimers exist for briefs
- generated-from note exists for briefs
```

Repair once. On second failure, mark entity failed and return a safe message.

---

# 14. MVP Success Definition

v0.3 succeeds if a user can say:

```text
I pasted links, asked questions naturally, saved useful ideas into a visual Canvas, built a better understanding of a market topic, and generated a useful brief when I needed one.
```

That is AlphaBrief's wedge against generic chatbots and one-click report tools.
