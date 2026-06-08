# Finora: Product Direction

**Tagline:** Build investment conviction that compounds.

**Version:** Direction v1.1
**Date:** May 2026
**Status:** Strategic redirection from prior positioning

**Changes in v1.1:**
- Thesis defined as a persistent stateful object (not a string); architecture clarified
- Brief Room section expanded: three modes detailed with use cases, cost profiles, and input scopes
- First brief auto-generates on thesis creation (single auto-generation event; no recurring auto briefs)
- Watch surface clarified as a display layer over continuous event ingestion (no LLM cost per view)
- New subsection: contextual interactions replace the idea of a generic AI chat
- No-generic-chat added as an explicit positioning principle
- MVP build priorities reordered to put thesis state architecture first
- Open questions updated with cost ceiling on Deep mode and Quick mode state-read tuning

---

## 1. The Problem

Long-term investors carry a quiet, persistent anxiety: holding positions for months or years without a reliable system for knowing whether they are still right.

They commit capital based on a reasoned thesis. Then reality unfolds — earnings reports, regulatory shifts, competitive moves, macro changes, narrative drift. Some of this matters to their thesis. Most of it does not. But there is no good system for telling the difference, so they either:

- Drown in headlines and news, becoming reactive and emotionally exhausted, or
- Tune out and risk missing the slow accumulation of evidence that quietly invalidates a position (the Kodak, Intel, Enron pattern), or
- Re-do research from scratch every quarter because nothing has been carrying their reasoning forward in the interim.

The current tools serve adjacent jobs but not this one:

- **Seeking Alpha** delivers other people's opinions, not the user's own evolving thesis.
- **Koyfin** delivers data without context for what the user already believes.
- **Finchat** answers questions the user thinks to ask, but doesn't surface questions the user *should* be asking.
- **Bloomberg / Refinitiv** are institutional firehoses, expensive and unfocused for individual investors.
- **Substack newsletters** are static content, not personalized to a portfolio.
- **General AI agents (ChatGPT, Claude, Perplexity)** are stateless — they have no memory of the user's positions, theses, or history.

None of these maintain the user's reasoning over time. None of them is organized around the unit that matters: **the thesis**.

---

## 2. The Product

**Finora is the system of record for an investor's reasoning.**

It is built on a single foundational idea: the thesis is the primary object. Everything else — companies, tickers, news, data, briefs, alerts — is organized in service of maintaining, stress-testing, and evolving the user's theses over time.

Finora does four things, each on a different temporal rhythm:

1. **Captures and stewards investment theses.** Every company or theme a user tracks has an explicit thesis attached to it — one or two sentences articulating why the user holds the view they do, plus optional focus areas defining what specifically to monitor.

2. **Maintains conviction state.** Finora continuously evaluates incoming information against each thesis and reports whether conviction is intact, under pressure, shifting, or broken — always with sourced reasoning.

3. **Produces structured briefs on demand.** Quick, Standard, or Deep mode, every brief is built around the user's thesis: what confirms it, what challenges it, what is unresolved, and what has changed since last time.

4. **Evaluates incoming information against active theses.** When a user encounters a headline, article, or claim, Finora assesses its veracity, novelty, source quality, and — most importantly — its implications for whatever thesis it touches.

**What Finora explicitly is not:**

- Not a real-time news feed.
- Not a buy/sell/hold recommender.
- Not a price-target generator or stock screener.
- Not a portfolio tracker or brokerage.
- Not optimized for daily engagement or active trading.
- Not chasing the swing-trader / alert-junkie market.

These exclusions are positioning, not omissions. Saying no to these defines the product.

---

## 3. The Core Object: The Thesis

The thesis is the first-class object in Finora. Without it, the rest of the product does not function. With it, every other feature becomes meaningful.

**A thesis is a persistent stateful object**, not a string attached to documents. This distinction is architecturally important: the thesis itself accumulates understanding over time, and briefs are *projections* of its current state, not independent re-analyses.

**A thesis consists of:**

- **Statement** — one or two sentences in the user's own words. Versioned; every edit creates a new version with a timestamp. Example: "I'm long NVDA because AI infrastructure spend has years to run and CUDA's moat is underappreciated. The risk is custom silicon adoption."
- **Focus areas** — optional explicit items the user wants monitored. Versioned. Example for the above: hyperscaler capex guidance, CUDA adoption indicators, custom silicon announcements, data center revenue growth, gross margin trajectory.
- **Accumulated evidence** — append-only log of facts surfaced over the life of the thesis, each tagged with source, timestamp, and which thesis component or focus area it touches. Briefs read from and write back to this log.
- **Open questions** — things flagged in past briefs as unresolved or worth monitoring; tracked until resolved.
- **Conviction state** — Finora's current read: intact / under pressure / shifting / broken, with reasoning. Versioned; conviction state changes are part of the thesis history.
- **Position context** (optional) — long / short / watching, time horizon, conviction level. Used only for tone and prioritization, never for advice generation.
- **Brief history** — every brief generated against this thesis, linked to the thesis state-version it was generated from.
- **Full timeline** — every edit, every conviction shift, every brief generated, every Challenger event evaluated against it.

**Why this architecture matters:**

Each brief reads from the thesis state and writes back to it. A Deep brief in March establishes facts that the Standard brief in April builds on rather than re-derives. A Quick check in May reads from the accumulated state rather than starting from scratch. Reasoning genuinely compounds. This is what makes the Archive valuable over time, what makes Finora structurally different from stateless AI tools, and what creates real switching cost: users cannot replicate their thesis history elsewhere.

**How focus areas work:**

Focus areas are what prevent briefs from being generic. When a user writes a thesis, Finora proposes default focus areas based on what is typically relevant for that kind of thesis (capex monitoring, competitive intensity, margin trajectory, regulatory exposure, etc.). The user accepts, edits, removes, or adds.

Focus areas become explicit sections in every brief. They train Finora's relevance filtering. They define what alerts can fire and what cannot. In Deep mode, Finora can suggest new focus areas it believes are becoming relevant based on incoming information.

This three-layer structure — thesis statement, focus areas, brief mode — is what guarantees that no brief is a generic overview. Every brief has a point of view because the user has supplied one.

---

## 4. The Four Surfaces

Finora is organized as four surfaces, each serving a different mode of the long-term investor's life.

### Surface 1: The Brief Room

**Purpose:** Deliberate research and thesis stress-testing.
**When used:** Initiating a new position, quarterly reviews, earnings season, after a material event.
**Cadence:** As needed; typically weekly to quarterly per thesis.

The Brief Room generates structured research artifacts on demand. Every brief is organized around the user's active thesis and follows a consistent structure:

- **The thesis** (current version, displayed at the top)
- **What confirms it** — recent evidence, data, filings, developments supporting the thesis
- **What challenges it** — counter-evidence, bear arguments, disconfirming signals
- **What is unresolved** — open questions, things to monitor, pending catalysts
- **What has changed** — diff from the previous brief, so the user is never re-reading the same content
- **Focus area sections** — explicit reporting on each user-defined focus area
- **Sources** — every claim is auditable back to primary source

**Briefs build on previous briefs.**

Each brief reads from the persistent thesis state established by previous briefs and Challenger evaluations, and writes back to it. Generation begins by consulting:

- The current thesis statement and focus areas
- All accumulated evidence in the thesis state
- Open questions raised by prior briefs
- The conviction state and its history
- The most recent brief, to establish the "since last time" diff

This is what makes the "What has changed" section meaningful — it is a true diff against established understanding, not a re-summarization. It is also what allows Deep briefs to build on Standard briefs without redoing baseline work, and what makes Quick briefs feel grounded in real prior reasoning rather than starting fresh each time.

**First brief auto-generates on thesis creation.**

When a user adds a company and writes a thesis, Finora immediately generates a Standard brief automatically. This is the only auto-generated brief. It serves three purposes: it demonstrates Finora's value in the first session, it establishes the baseline thesis state that everything subsequent builds on, and it gives the user something concrete to react to and refine the thesis against.

After this initiation brief, all subsequent briefs are user-initiated. Finora does not auto-generate briefs on a schedule. Daily and weekly information needs are served by the Watch (Surface 2), which does not require LLM generation. This separation is deliberate — see Section 5 on the cadence model.

#### The three modes

The three modes are not "better and worse versions of the same thing." They are different jobs the user can do with a thesis, distinguished by use case as much as by depth. In the UI they should be labeled by use case (suggested labels in parentheses):

**Quick — "Check in" (target: 2-minute read, sub-30-second generation)**

- *Use case:* Daily or pre-market confidence check. "Did anything break since I last looked?"
- *Input scope:* Last ~7 days of events touching the thesis or focus areas. Filings, press releases, major news only.
- *Source count:* ~5–15 items.
- *Prompt structure:* Tight. Echo the thesis, summarize current conviction state, list the few recent events that matter, give one-line status per focus area, flag anything to watch.
- *Reasoning:* Minimal. This is a status read, not analysis.
- *Output length:* ~300–500 words.
- *Cost profile:* Cheap. Users can run freely.

**Standard — "Full review" (target: 10-minute read, 1–3 minute generation)**

- *Use case:* The weekly Sunday-morning sit-down. The default mode and the one users will run most often.
- *Input scope:* Last ~30 days of events, plus most recent earnings if relevant, plus competitive and industry context that touches the thesis. Includes second-order information that *might* matter even if not directly about the company.
- *Source count:* ~20–40 items.
- *Prompt structure:* Full brief structure — thesis / confirms / challenges / unresolved / changes / focus area sections / sources. Each section reasoned, not just summarized.
- *Reasoning:* Light multi-step. Connects evidence across multiple sources. Example: "Microsoft cut Azure capex guidance, which combined with Meta's similar move last week suggests hyperscaler spend may be plateauing — this challenges your NVDA thesis."
- *Output length:* ~1500–2500 words.
- *Cost profile:* Moderate. Used routinely on a paid tier.

**Deep — "Stress test" (target: 30+ minute read, 5–15 minute generation)**

- *Use case:* Quarterly review, position initiation, post-earnings deep dive, after a major event has shifted conviction. Used sparingly — meant to feel substantial.
- *Input scope:* Last quarter of events, full most-recent earnings (transcript and filing), 2–3 peer companies for comparison, industry-wide trends, relevant regulatory developments, macro touchpoints. Includes *proactive research* — Finora actively looks for things the user might be missing.
- *Source count:* ~50–150+ items.
- *Prompt structure:* Multi-step. First pass identifies what to investigate; second pass investigates; third pass synthesizes. Likely uses chained calls or sub-agents.
- *Reasoning:* Heavy. Cross-source synthesis, peer comparison, scenario analysis ("if hyperscaler capex flattens, what does that mean across the stack").
- *Proactive elements:* "Gross margin trajectory is becoming relevant to your thesis — you don't currently track it. Add as a focus area?" "Three competitors made similar moves this quarter — suggesting a sector trend you may want to incorporate."
- *Output length:* ~5000–10000 words, with collapsible sections.
- *Cost profile:* Expensive. Long generation time. Users kick it off and come back; Finora notifies them when complete. Should be treated as "this is real work," not a casual click.

#### Mode selection UX

Mode selection paralysis is a real UX risk and is handled by three mechanisms, not by auto-generation:

1. **Use-case labeling.** Modes are presented as "Check in / Full review / Stress test," not "Quick / Standard / Deep." Users select based on what they want to do, not on a depth slider.
2. **Smart defaults based on context.** Generating from a thesis card flagged "under pressure" suggests Standard or Deep. Generating from a Challenger result with major thesis implications suggests Deep. Generating from the Watch on a routine weekday suggests Quick. Generating after a long absence suggests Standard. The product knows the context and uses it.
3. **Event-triggered suggestions.** When a material event hits a thesis (earnings, guidance change, major regulatory action), the Watch surfaces a recommended action: *"Major event detected on NVDA — Standard brief recommended."* One click, right mode, no decision required.

A single onboarding moment after the first auto-generated brief explains the three modes by use case. This is a one-time orientation, not recurring tooltips.

### Surface 2: The Watch

**Purpose:** Ambient monitoring of all active theses.
**When used:** Morning coffee, Sunday morning review, end-of-day wrap-up.
**Cadence:** Daily or weekly, user's choice.

The Watch is **not a feed**. A chronological list of headlines is precisely the noise problem Finora exists to solve. The Watch is organized by thesis.

**The Watch does not generate AI analysis on its own.** It is a display surface over Finora's continuous event ingestion. This separation is architecturally important:

- **Continuous ingestion of structured events** (always on, no LLM cost) — Finora is constantly pulling filings, press releases, news API events, RSS, financial data. This is plumbing.
- **Continuous deterministic relevance matching** (always on, no LLM cost) — events get tagged against active theses based on tickers, focus areas, and topic matching.
- **Brief generation** (on demand only, LLM cost) — happens in the Brief Room when the user asks.

The Watch displays what continuous ingestion has accumulated. It does not invoke the LLM every time it's opened. This keeps cost flat per user, lets the Watch update in near real-time as events come in, and reinforces that the user's daily check-in does not require generation.

Each active thesis displays as a card showing:

- The thesis statement (a reminder)
- Current conviction state (intact / pressure / shifting / broken) with reasoning
- A three-to-four-sentence narrative of what has happened since last review, framed against the thesis
- The two-to-five material items (filing, earnings, guidance, competitor move) that drove the conviction read
- A button to generate a fresh brief if the user wants to go deeper, with the suggested mode based on context (see Surface 1)

When nothing material has happened to a thesis, the card says so explicitly. "Your AMD thesis is intact. No material developments this week." This is a feature, not a bug. The product that confidently reports "nothing changed" builds trust faster than one that manufactures content to fill space.

When something material *has* happened, the Watch surfaces a recommended action: *"Earnings results affect your NVDA thesis — Standard brief recommended."* This solves mode selection paralysis at the moment it matters by suggesting the right mode contextually.

The Watch is the surface that creates the daily/weekly ritual. It is short, dense, and respectful of attention.

### Surface 3: The Challenger

**Purpose:** Evaluate a specific piece of incoming information against active theses.
**When used:** A headline catches the user's attention; an article is forwarded; a friend mentions something.
**Cadence:** Transactional, as needed.

The Challenger accepts a URL (later: pasted text, browser extension, email forward) and produces a structured evaluation card:

- **Source assessment** — tier, type, reliability indicators
- **Veracity check** — claim cross-referenced against filings, prices, other coverage; what is corroborated, what is not
- **Novelty** — is this new information, or already reflected in market and prior reporting
- **Materiality to active theses** — which theses this touches, how each is affected, what would constitute confirming or disconfirming follow-through
- **Conviction implications** — whether any thesis state should be reconsidered based on this

The Challenger output is the differentiating artifact. No other tool produces "here is what this means for what you already believe." That is the wedge.

The Challenger also serves as a learning signal: what the user evaluates trains Finora's understanding of which sources and topics matter to them on which theses.

### Surface 4: The Archive

**Purpose:** Long-term record of the user's reasoning evolution.
**When used:** Year-end reviews, retrospectives, learning from past decisions.
**Cadence:** Slow-burn; valuable in months, deeply valuable in years.

The Archive is the surface that compounds. For each thesis, the Archive shows:

- The full timeline of the thesis — when written, every edit, every conviction state change
- All briefs generated, browsable in order
- All Challenger evaluations that touched the thesis
- Annotations from the user (optional notes added at any point)

Over a year, this becomes a record of how the user thinks. Over three years, it becomes the most valuable record of their investing life. The switching cost is enormous: no user will leave Finora and willingly abandon their reasoning history.

The Archive is also the foundation for future intelligence features (pattern detection across the user's own history, e.g. "you tend to revise theses too quickly after one bad quarter") but those are not v1.

### How users interact with artifacts (no generic chat)

A natural temptation is to add a generic AI chat to Finora so users can ask questions about briefs, theses, and history. **Finora deliberately does not have a generic chat interface.** A chat box would dilute the product's identity, invite direct comparison with ChatGPT and similar tools, expand liability surface by inviting generic finance questions, and pull users toward always-open assistant behavior that conflicts with the cadence model.

The legitimate user needs that a chat would address — explaining sections of briefs, asking about sources, comparing briefs, asking why something matters for a thesis — are handled through structured contextual interactions instead:

**Inline interactions within briefs.**
Every brief, section, and claim is interactive. Selecting a sentence or section reveals constrained actions: *Explain in more detail / Show me the sources / Why does this matter for my thesis? / Compare to the previous brief.* Each action produces a constrained output. The AI is doing the work, but the interface guides users toward useful interactions and away from "ask anything."

**Ask about this brief.**
When viewing a specific brief, users can open a focused ask-about-this session. The scope is explicit and bounded: this conversation is about this brief, with full access to its content, sources, and the underlying thesis state. The session ends when the user leaves. There is no persistent chat history with Finora as a general assistant; each session is bounded to an artifact.

**Structured cross-artifact actions.**
Queries that span multiple artifacts ("compare my reasoning on NVDA and AMD," "summarize how my thinking on the AI infrastructure trade has evolved") are invoked through structured actions in the Archive, not typed into a chat. The output is a new structured artifact — a comparison, a retrospective — that is itself saved to the Archive. Artifacts compound; chats disappear.

**Principle:** when a user has a complex question, Finora produces an artifact, not a chat response. Artifacts are the unit of value. This protects the structured-output promise that is the core of the product's differentiation.

These contextual interactions are not part of v1.0 MVP (see Section 10). They are v1.1+. The MVP ships the structured surfaces; contextual interactions are layered on once the structured product has proven itself.

---

## 5. The Event System (Underlying Infrastructure)

Underneath the four surfaces sits an event detection and routing system. Finora ingests material events from licensed and properly accessed sources:

- **SEC filings** (EDGAR, free, real-time)
- **Exchange announcements** (ASX, LSE, HKEX, NZX, etc.)
- **Press releases** (PR Newswire, Business Wire, GlobeNewswire)
- **Financial news APIs** (Benzinga, Tiingo News, Marketaux, NewsAPI.ai)
- **Wire services** (Reuters, AP, where licensed)
- **Financial data providers** (Polygon, Tiingo, FMP, Alpha Vantage for prices/fundamentals)
- **RSS feeds** from publishers who offer them (explicit invitation to machine consumption)
- **Earnings transcripts** (licensed aggregators)
- **Regulatory / macro sources** (Fed, ECB, RBA, RBNZ, BoE statements; all public)
- **User-supplied content** (pasted URLs, forwarded articles — user has legal access; Finora analyzes on their behalf)

Events are classified by type and routed:

- Quietly into the Watch if relevant to an active thesis (most events)
- Surfaced as alerts only if materially affecting a thesis's conviction state (rare; the discipline of restraint is what builds trust)
- Used as corroboration data for Challenger evaluations
- Indexed for Brief Room generation

**Sourcing principle:** Finora does not scrape paywalled content, does not bypass robots.txt, does not operate in the legal grey zone. Every source is licensed, public, or user-supplied. This is both a legal/compliance posture and a marketing position — "every claim is auditable to a legitimate source" becomes a differentiator against grey-zone competitors as content licensing tightens industry-wide.

---

## 6. The Cadence Model

Finora is designed around three temporal rhythms, not real-time engagement:

- **Daily (optional):** Morning Watch glance, end-of-day Watch wrap. Five to ten minutes total. **No LLM generation** — the Watch displays continuously-ingested events without invoking generation per visit.
- **Weekly (core ritual):** Sunday morning Watch review across all theses, occasional Standard brief on whichever thesis needs it. Twenty to forty minutes.
- **Quarterly (deep work):** Earnings-driven Deep briefs, thesis revisions, Archive review. Two to four hours.
- **Event-driven (rare):** Challenger evaluations when something specific catches the user's attention. Three to ten minutes each.

**Critical separation:** event ingestion runs continuously and cheaply in the background; AI brief generation happens only on user request (with one exception, the auto-generated initiation brief when a new thesis is created). This is what allows Finora to feel always-up-to-date without burning generation cost on disengaged users, and what keeps daily check-ins frictionless.

Alerts exist but are off by default. Users opt in to alert categories as they build trust with the product. The threshold for an alert firing is materiality to thesis conviction, not generic newsworthiness.

---

## 7. Positioning Principles

These principles guide every product decision:

1. **The thesis is the product.** Everything is organized around it. Features that do not serve the thesis are features that do not belong.

2. **Finora challenges; the user decides.** The product never recommends a trade, never assigns a price target, never tells the user what to do. It surfaces what is true, what is changing, and what it means — and lets the user act.

3. **Restraint over engagement.** Finora is not optimized for daily-active-user metrics. The product succeeds when users feel sharper, not when they open the app more.

4. **Every claim is sourced.** No black-box AI summaries. Every assertion in every brief is auditable back to primary source. This is both trust-building and legally defensive.

5. **Compounding context wins.** The longer a user uses Finora, the more valuable it becomes. Theses accumulate. Archives deepen. Switching costs rise organically.

6. **Stay clear of the advice line.** Finora is an information and reasoning tool, not a financial advisor. Configuration (watchlists, theses, focus areas) is fine. Suitability assessments (income, risk tolerance, recommendations) are out of scope. Standard "not financial advice" disclaimers visible throughout.

7. **No generic chat.** Finora does not have a free-form AI assistant interface. Interactions are structured, contextual, and bounded to artifacts. This protects the product's identity, avoids direct comparison with general AI tools, and ensures every interaction produces consistently structured output.

8. **Licensed sources only.** No grey-zone scraping. This is a strategic moat as the industry tightens, not a constraint.

---

## 8. Who This Is For (and Who It Isn't)

**Target user:** The long-term individual investor or fundamental-leaning small-portfolio manager who:

- Holds 5–30 positions or watched names
- Operates on a months-to-years time horizon
- Cares about reasoning, not just outcomes
- Has tried Seeking Alpha, Koyfin, Finchat, or substack newsletters and found them insufficient
- Manages enough capital that a $20–50/month tool that improves decisions is obviously worth it
- Reads. Thinks. Writes things down.

**Explicitly not for:**

- Day traders and swing traders (time horizon too short, alerts model is wrong)
- Passive index investors (no thesis to maintain)
- Institutional traders (need Bloomberg-grade infrastructure)
- People looking for stock tips or hot picks

The product's voice, marketing, and design should be unmistakably aimed at the first group.

---

## 9. Business Model (Directional)

- **Free tier:** Up to three active theses; Quick briefs only; Watch with weekly cadence; limited Challenger evaluations per month.
- **Paid tier (~$25–40/month):** Unlimited theses; all brief modes; full Watch; unlimited Challenger; alerts; Archive history.
- **Annual discount** to encourage long-term commitment (which is also philosophically aligned with the product).

Future: institutional tier for RIAs and small family offices; team features; portfolio integration; broker connections. All v3+.

---

## 10. MVP for Pitch

This section is the recommendation on what to actually build first, given the goal of presenting a compelling demo to a panel of judges within a constrained build window.

### MVP Principle

The MVP must demonstrate the *core philosophical wedge* — that Finora is organized around the thesis and produces fundamentally different outputs than competitors — within a short live demo. Every feature included should reinforce this wedge. Every feature excluded should be defensible as "later."

A judge should walk away able to articulate: "Finora is the tool that maintains an investor's reasoning over time, instead of just showing them news or data."

### MVP Scope: What to Build

**1. Thesis-driven onboarding with auto-generated first brief.**
The user signs up, enters one or two companies they want to track, and is prompted to write a one-sentence thesis for each. Finora proposes default focus areas; user accepts or edits. **Immediately after thesis creation, Finora auto-generates a Standard brief** — this is the user's first Finora experience and the activation moment. It demonstrates value in the first session, establishes the baseline thesis state that everything subsequent builds on, and gives the user something concrete to react to. This entire flow (signup → thesis → first brief delivered) should take three to five minutes and feel different from any other fintech onboarding the judges have seen. **This is the moment that signals the product philosophy.**

**2. Brief generation in two modes (Quick and Standard) with persistent thesis state.**
Skip Deep mode for MVP — it requires the most infrastructure (filings parsing, transcript ingestion, peer data, multi-step generation) and the wedge is already demonstrated in Quick + Standard. Both modes structured around thesis: confirms / challenges / unresolved / changes / focus area sections. Every claim sourced and clickable. **Critically: implement the persistent thesis state architecture from day one**, even though Deep is deferred. Each brief reads from and writes to the thesis state. Subsequent briefs explicitly diff against previous ones. This is the architectural foundation; do not shortcut it for MVP.

This is the most visually impressive demo moment. Generate a Standard brief live in front of the judges and let them read the structure. The "what challenges your thesis" section is the showstopper — no other tool produces this.

**3. The Watch (single page, weekly cadence).**
Thesis cards with conviction state and short narratives. Build it for the demo with two or three theses pre-seeded so judges see the dense, organized view. Skip daily cadence for now; weekly is enough. Skip thesis-state visualizations (intact/pressure/shifting/broken indicators can be simple colored labels, not elaborate UI).

**4. The Challenger (URL paste → evaluation).**
This is the most demo-impressive feature because it produces an immediately legible "wow" output. A judge can paste any finance headline live and see Finora return source assessment, veracity, novelty, and thesis implications. **Make this work well. It is the single best showcase of the wedge.**

**5. Minimal Archive (read-only).**
Just a list of past briefs and Challenger evaluations per thesis, with timestamps. No fancy timeline visualization. The point is to show that history accumulates — judges will understand the implication.

### MVP Scope: What to Defer

- Deep brief mode (depth not needed for demo; Quick + Standard prove the wedge)
- Real alerts and push notifications (alert tuning is a v2 challenge; demo can show the Watch instead)
- Browser extension and email forwarding into Challenger (URL paste is sufficient)
- Portfolio integration and broker connections (not core; complicates compliance posture)
- Social or collaborative features (against the product's philosophy anyway)
- Mobile app (web responsive is enough for pitch; mobile is post-MVP)
- Thesis state history visualization in Archive (text list is enough)
- Multi-currency / international depth (pick US equities for demo; expand later)
- Auto-generated daily/weekly briefs (Watch handles ambient updates without LLM cost; do not put the product on an engagement treadmill)
- Inline contextual interactions within briefs (explain / source-check / compare) — v1.1, not v1.0
- Ask-about-this-brief sessions and structured cross-artifact actions — v1.1, not v1.0

### What is explicitly out of scope, not just deferred

- **Generic AI chat interface.** Finora does not have a free-form assistant. The legitimate user needs that chat would address are met by structured contextual interactions (v1.1+). Never carry the chat pattern over from prior Finora versions; it is a positioning dilution risk and a comparison-to-ChatGPT risk that Finora cannot afford.
- **Generic finance Q&A.** Finora does not answer "what is a P/E ratio" or "explain ETFs." This is not the product; users have ChatGPT and Investopedia for that.
- **Buy/sell/hold recommendations or price targets.** Out of scope permanently for legal and product reasons.

### Demo Narrative (for the Pitch)

Structure the live demo around a single coherent story. Suggested flow:

1. **Open with the problem** (60 seconds): Show a screenshot of a typical investor's information environment — news feed, Twitter, newsletters, Discord. Land the line: "Long-term investors don't have a memory problem. They have a reasoning problem."

2. **Show the onboarding** (60 seconds): Sign up live, add NVDA, write the thesis. Highlight the focus area prompt. Judges should see immediately that this is not a generic finance app.

3. **Generate a Standard brief live** (90 seconds): Watch it stream in. Stop on the "what challenges your thesis" section. Read one line aloud. Land: "No other tool tells you what challenges what you already believe."

4. **Switch to the Watch** (30 seconds): Show the pre-seeded version with 3 theses, one of which is "under pressure." Click into it briefly.

5. **Demo the Challenger** (90 seconds): Ask the judges for a recent finance headline URL. Paste it live. Show the structured evaluation. Highlight the thesis implications section. This is the moment the wedge becomes undeniable.

6. **Close on the moat** (45 seconds): Show the Archive view — "This is two months of one user's reasoning. After a year, this is the most valuable record in their investing life. After three years, they will not leave."

Total demo: ~6 minutes, leaving time for the rest of the pitch (problem, market, business model, ask).

### MVP Build Priorities (Suggested Order)

Given that AlphaBrief already has a brief generation pipeline and AI generation layer, the build should sequence to maximize reuse:

1. **Thesis state object as the foundational data model.** Not a string, not a row in a watchlist table — a stateful object with statement (versioned), focus areas (versioned), accumulated evidence (append-only), open questions, conviction state (versioned), brief history, and full timeline. Build this first; everything depends on it. Even features deferred to v1.1 (Deep mode, contextual interactions, cross-artifact comparisons) depend on this being right from day one. Do not shortcut this for MVP speed.
2. **Onboarding flow with auto-generated first brief.** Signup → company → thesis → focus areas (with proposed defaults) → auto-generated Standard brief delivered in under 60 seconds. This is the activation moment.
3. **Quick + Standard brief generation refactored around thesis state.** Adapt existing `brief_generation_service.py` and `prompt_builder.py` to (a) accept thesis state as input including accumulated evidence and prior briefs, (b) produce the structured format with confirms/challenges/unresolved/changes sections, and (c) write back to thesis state on completion. The "what has changed" diff requires real prior-brief context to work — invest in this.
4. **Source ingestion pipeline.** Wire up at minimum: SEC EDGAR, one news API (Benzinga or Tiingo News), one financial data API (Polygon or Tiingo), and RSS for a small set of company IR pages. Continuous ingestion runs as a background job; deterministic relevance tagging matches events to active theses. This is the foundation that lets the Watch update without LLM cost.
5. **The Challenger.** URL evaluation flow; reuses much of the brief generation infrastructure with a different prompt builder. Reads from thesis state to produce thesis-aware evaluations.
6. **The Watch.** Aggregation and presentation layer over ingested events and thesis state. No LLM generation on view. Surfaces contextual brief-mode recommendations when material events warrant.
7. **Minimal Archive.** Read-only list view over stored briefs, Challenger evaluations, and thesis state versions per thesis.

### Success Criteria for the Pitch

The MVP is successful for the pitch if a judge can, unprompted, say one of the following:

- "This is doing something I haven't seen anywhere else."
- "I would use this myself."
- "How is this different from Seeking Alpha / Koyfin / ChatGPT?" — *and the demo has already answered the question implicitly, so the founder can answer it crisply in one sentence.*

If judges leave saying "interesting AI finance tool," the MVP has failed to land the wedge. If they leave saying "Finora maintains investor reasoning over time" — even in their own words — it has succeeded.

---

## 11. Open Questions to Resolve Before Build

These are decisions still to make. Flagging here so they are not forgotten:

1. **Onboarding friction vs. activation:** how aggressively to require thesis writing in onboarding. Skippable is friendlier but creates non-customers; required is purer but may hurt signup conversion. Leaning toward required, since users who skip are unlikely to be Finora's target customer anyway.
2. **Cost ceiling on Deep mode:** Deep briefs are expensive ($1–3 per generation, 5–15 min wall-clock). Rate limit on paid tier? Credit system? Unlimited with fair-use policy? Decide before launching Deep mode in v1.1.
3. **Pricing exact point:** $25, $30, $40. Worth testing.
4. **Free tier limits:** generous enough to demonstrate value, tight enough to drive conversion. Suggested: 3 active theses, Quick mode only, Watch limited to weekly cadence, 5 Challenger evaluations per month.
5. **Source priority for MVP:** which news/data APIs to integrate first. Benzinga vs Tiingo News tradeoffs need testing.
6. **Voice and tone of generated briefs:** dry-analyst, conversational-but-rigorous, somewhere between. Should feel like a thoughtful colleague, not a research report and not a chatbot.
7. **Conviction state UI:** four states (intact / pressure / shifting / broken) is the right granularity, but how to display this without it feeling like a buy/sell signal is a design challenge worth careful work.
8. **International coverage scope:** US equities is the obvious starting market, but if pitching to NZ/AU judges, including ASX/NZX coverage in the demo may resonate. Decide based on audience.
9. **Architecture-A vs Architecture-B trade-off for MVP:** MVP will use Architecture B (persistent thesis state) from day one as decided above, but the depth to which Quick mode actually reads from accumulated state vs. operates more simply is a tuning decision worth revisiting once briefs are running. Quick should feel fast; if reading full state slows it down meaningfully, consider a lighter read.

---

## 12. Closing

Finora's positioning is now coherent. It is for long-term investors. It is organized around the thesis. It maintains reasoning over time. It does not chase the engagement-junkie market or compete in the crowded swing-trading alert space. It builds compounding value with every interaction.

The product to build first is a focused MVP that demonstrates the thesis-organized wedge in a six-minute demo: thesis onboarding, brief generation, the Watch, the Challenger, and minimal Archive. Everything else can wait.

The landing page headline can be honestly defended:

**Build investment conviction that compounds.**
