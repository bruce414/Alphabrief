# Finora Research Graph Rules and Workflow Reference

## Purpose

This document defines the rules and workflow for how Finora should create, display, connect, update, and manage nodes and edges inside the research canvas.

It is intended as a UI/product/implementation reference for Claude Code.

The goal is to keep Finora's canvas useful, readable, source-backed, and clean as the research graph grows.

Finora should not simply dump every extracted idea onto a canvas. The graph must follow clear rules so it remains a thinking interface rather than a messy database visualization. Because apparently “AI made a hairball” is not a product strategy.

---

# 1. Product Concept

Finora is an AI-powered finance research workspace.

Each research space contains:

```text
Right-side AI chat
Sources
Research graph / canvas
Project memory
Briefs
Updates
```

The canvas is the living research graph. It grows from:

```text
User chats
AI responses
Pasted URLs
Uploaded sources
Manual notes
Market update checks
Accepted AI suggestions
```

The graph should help users understand:

```text
What exists
What caused what
What supports or contradicts what
What is risky
What is uncertain
What changed over time
What needs more evidence
What should be turned into a brief
```

---

# 2. Full Workflow

## 2.1 High-Level Product Loop

The core workflow is:

```text
User asks question / adds source
        ↓
AI generates response in the right chat panel
        ↓
AI extracts reusable research insights from the conversation/source
        ↓
AI converts insights into suggested nodes and edges
        ↓
AI places suggested nodes/edges onto the canvas near relevant clusters
        ↓
User accepts, edits, or dismisses suggestions in place
        ↓
Accepted nodes/edges become part of the research graph
        ↓
Graph becomes source-backed project memory
        ↓
User can use graph to continue research, review evidence, track updates, or generate briefs
```

The AI chat response should remain useful on its own. Graph extraction should enhance the workspace, not block the user from getting an answer.

---

## 2.2 Detailed Workflow

### Step 1: User Input

User may interact with Finora through:

```text
Typing a research question in the right AI chat panel
Pasting a finance/news/article URL
Uploading a PDF/report/filing/transcript
Adding a manual canvas note
Opening an existing research space
Running a market update check
```

Example:

```text
"How do export restrictions affect Nvidia's AI chip revenue?"
```

---

### Step 2: Scope Check

Before using the input to update the research graph, Finora checks whether the input belongs to the current research space scope.

Possible outcomes:

```text
In scope
Partially related
Out of scope
Unclear
```

If out of scope, Finora should not silently pollute the research graph.

Recommended UX:

```text
This looks outside the current research scope.

Choose how to handle it:
1. Ask as one-off chat
2. Add it to this research space
3. Create a new research space
```

If partially related:

```text
This may relate to the Valuation cluster through interest-rate sensitivity.
Add it to this research space?
```

---

### Step 3: AI Response Generation

Finora generates a normal AI response in the right-side chat panel.

The right panel should stay stable as the AI assistant/chat panel. It should not be replaced by a node suggestion dashboard.

The response should answer the user’s question directly.

Example response summary:

```text
Export restrictions can affect Nvidia by limiting sales of advanced AI chips to China, increasing geopolitical revenue risk, and potentially pushing Nvidia toward compliant chip variants. The impact depends on China exposure, availability of modified chips, demand from other regions, and regulatory changes.
```

---

### Step 4: Insight Extraction

After or during response generation, Finora extracts reusable insights from the response and supporting sources.

Extracted insight categories:

```text
Entities
Companies
Events
Concepts
Metrics
Claims
Evidence
Risks
Catalysts
Open questions
Conclusions
Relationships
Possible updates
```

Example extracted insights:

```text
Company: Nvidia
Concept: Export restrictions
Metric: China revenue exposure
Risk: Further export controls
Claim: Export restrictions may pressure Nvidia's China revenue
Question: Can Nvidia offset China weakness through other regions?
Evidence: Source mentioning export restriction policy
Conclusion: Geopolitical risk remains material for Nvidia's AI chip business
```

---

### Step 5: Node Candidate Generation

Finora converts extracted insights into candidate nodes.

Candidate nodes should not immediately become permanent graph nodes.

They should first exist as suggestions unless the user has enabled trusted auto-accept behavior for low-risk updates.

Example candidate nodes:

```text
Risk: Further export restrictions
Metric: China revenue exposure
Claim: Export restrictions may pressure Nvidia's China revenue
Question: Can Nvidia offset China weakness elsewhere?
Evidence: Export restriction policy source
```

---

### Step 6: Duplicate and Merge Check

Before suggesting a new node, Finora checks the existing graph.

Questions:

```text
Does an existing node already represent this idea?
Is this a synonym or alias?
Is this a more specific child of an existing node?
Should this update an existing node instead of creating a new one?
Should this become evidence for an existing claim instead of a new claim?
```

Example:

```text
Existing node:
Cloud capex slowdown

New extraction:
Hyperscaler spending slowdown

Likely action:
Update existing node or add alias, not create duplicate.
```

---

### Step 7: Cluster Placement

Every node should belong to a cluster unless it is temporarily placed in `Unsorted`.

Finora decides which cluster the node belongs to.

Example:

```text
Further export restrictions → Risks
China revenue exposure → Financial Impact
Nvidia → Key Companies
Export restrictions → Regulation / Risks
Can Nvidia offset China weakness? → Open Questions
```

If the correct cluster does not exist, Finora may suggest creating a new cluster.

---

### Step 8: Edge Candidate Generation

Finora creates candidate relationships between new and existing nodes.

Example edges:

```text
Export restrictions → affects → China revenue exposure
China revenue exposure → affects → Nvidia revenue growth
Further export restrictions → raises_question → Can Nvidia offset China weakness?
Evidence source → supports → Export restrictions may pressure Nvidia's China revenue
Claim → supports → Conclusion about geopolitical risk
```

Edges should use controlled relationship types only.

---

### Step 9: Confidence, Importance, and Source Attribution

Every suggested node and edge should include:

```text
Confidence
Importance
Source references where available
Reason/explanation
Suggestion status
```

Example:

```text
Edge:
Export restrictions → affects → China revenue exposure

Confidence: High
Importance: 4
Source: user chat + policy source
Explanation: Restrictions limit Nvidia's ability to sell certain advanced AI chips into China.
Status: suggested
```

---

### Step 10: Canvas Suggestion Placement

Suggested nodes and edges appear directly on the canvas, not primarily in the right AI chat panel.

Display depends on zoom level.

Low zoom:

```text
Risks
3 updates available
2 suggestions
```

Medium zoom:

```text
Further export restrictions
Suggested
```

High zoom:

```text
Suggested by AI
RISK
Further export restrictions

May increase downside risk to Nvidia's China AI chip revenue.

Accept | Edit | Dismiss
```

Ghost node style:

```text
Dashed border
Slight transparency
Small "Suggested by AI" label
Accept/Edit/Dismiss controls only when selected or zoomed in
```

Ghost edge style:

```text
Dashed relationship line
Small edge label
Accept connection action
```

---

### Step 11: User Review

The user can:

```text
Accept node
Edit node
Dismiss node
Accept edge
Edit edge
Dismiss edge
Move node to another cluster
Convert suggested node type
Ask AI about a node
View evidence
Add node to brief
```

Accepted suggestions become permanent graph items.

Dismissed suggestions should not clutter the canvas.

Edited suggestions become accepted with status `edited`.

---

### Step 12: Graph Update

Once accepted, nodes and edges update the research graph.

The graph can then support:

```text
Future AI answers
Project memory
Evidence review
Timeline updates
Brief generation
Follow-up questions
Cluster focus
Node focus
```

---

### Step 13: Future Chat Uses the Graph

When the user asks a new question inside the same research space, Finora should use the existing graph as project context.

Example:

```text
User: "What should I investigate next?"
Finora can inspect:
- open question nodes
- weak evidence nodes
- stale risk nodes
- unsupported claims
- important clusters
```

The AI response can then say:

```text
The weakest part of your current map is the evidence behind the cloud capex slowdown risk. You have two claims connected to this risk but only one source. I suggest checking latest hyperscaler capex guidance from Microsoft, Amazon, Google, and Meta.
```

---

### Step 14: Market Update Workflow

When the user reopens a research space, Finora may run an update check for time-sensitive nodes.

Flow:

```text
User opens research space
        ↓
Finora checks update-sensitive nodes
        ↓
Finora searches for relevant new information
        ↓
Finora compares new information against existing nodes/claims/conclusions
        ↓
Finora creates suggested updates
        ↓
Cluster badges show total updates
        ↓
User reviews and accepts/rejects updates
```

Important:

```text
Finora should not silently rewrite the graph.
Updates should be suggested and reviewable.
```

Example update:

```text
Existing node:
Cloud capex slowdown risk

New information:
Latest hyperscaler guidance suggests capex remains strong.

Suggested change:
Risk severity: High → Medium
Confidence: Medium → High
Reason: New guidance weakens the prior slowdown assumption.

Actions:
Accept | Edit | Reject | Mark uncertain
```

---

# 3. Core Graph Principle

A connection should exist only if it helps the user understand one of these things:

```text
1. What caused what
2. What supports or contradicts what
3. What belongs under what
4. What example illustrates what concept
5. What uncertainty or open question emerges
6. What new information updates previous understanding
7. What evidence backs a claim or conclusion
8. What metric, risk, catalyst, or event affects another research object
```

If a relationship does not help the user understand any of those, Finora should not create the edge.

Bad connections are worse than missing connections.

`related_to` should be the last resort.

---

# 4. Graph-Level Structure

Each research space contains one main graph.

The graph is made of:

```text
Research Space
→ Clusters
→ Nodes
→ Edges
→ Evidence links
→ Suggestions
→ Updates
```

The graph should be graph-first, but tidy.

The user should experience the graph as:

```text
Central research topic
Major clusters around it
Important nodes inside clusters
Important relationships between nodes
More details revealed through zoom, focus, and selection
```

The graph should not feel like:

```text
A random network diagram
A kanban board
A static dashboard
A giant table of cards
A spiderweb of every possible relationship
```

---

# 5. Node Types

Finora should use a controlled node type vocabulary.

Recommended node types:

```text
research_space
cluster
company
event
concept
metric
claim
evidence
risk
catalyst
question
conclusion
manual_note
source
brief_section
suggested_node
```

---

# 6. Node Type Definitions and Rules

## research_space

Represents the overall research topic.

Example:

```text
AI Infra 2026
```

Rules:

```text
One main research_space node per research space.
Usually centered in the graph at low zoom.
Connects to main cluster nodes.
```

---

## cluster

Represents a major thematic group.

Examples:

```text
Demand Drivers
Risks
Evidence
Open Questions
Financial Impact
Key Companies
```

Rules:

```text
Clusters organize the graph.
Clusters can be selected to enter cluster focus mode.
Clusters should show aggregate badges such as updates, suggestions, source gaps, or open questions.
Every normal node should belong to a cluster unless temporarily Unsorted.
```

---

## company

Represents a company or organization.

Examples:

```text
Nvidia
AMD
TSMC
ASML
Microsoft
Amazon
Google
Meta
```

Rules:

```text
Companies should connect to relevant metrics, events, risks, catalysts, claims, and evidence.
Companies should not duplicate if ticker/name variants refer to the same entity.
Company nodes can appear in multiple contexts but should have one canonical node per research space.
```

---

## event

Represents something that happened or may happen.

Examples:

```text
Nvidia Q2 earnings
US export restriction update
Hyperscaler capex announcement
New chip launch
Fed rate decision
```

Rules:

```text
Events should usually have a date or time context.
Events often connect to affected metrics, risks, catalysts, companies, or claims.
Events are usually time-sensitive and may need update checks.
```

---

## concept

Represents an abstract finance, business, or market concept.

Examples:

```text
Margin compression
Valuation multiple
Quality of earnings
Operating leverage
GPU supply constraint
Customer concentration
```

Rules:

```text
Concepts should connect to examples, claims, metrics, and learning explanations.
Concept nodes are usually less time-sensitive than event, metric, risk, or claim nodes.
```

---

## metric

Represents a financial, operational, market, or measurable data point.

Examples:

```text
Revenue growth
Gross margin
Free cash flow
Cloud capex
GPU shipment volume
Data center utilization
Forward P/E
```

Rules:

```text
Metrics should connect to drivers, companies, events, claims, risks, and conclusions.
Metrics are often time-sensitive.
Metric nodes should include period/date context when possible.
```

---

## claim

Represents a debatable statement that needs evidence.

Examples:

```text
AI infrastructure demand is being driven by hyperscaler capex.
Cloud capex slowdown may pressure GPU demand.
Power constraints may limit data center expansion.
Nvidia's valuation is supported by continued AI infrastructure demand.
```

Rules:

```text
Claims must be connected to evidence when possible.
Claims can be supported, contradicted, partially supported, or marked as needing verification.
Claims should not be treated as facts.
Unsupported claims should be visibly marked.
```

---

## evidence

Represents support from a source, user note, filing, transcript, article, or AI-derived research result.

Examples:

```text
Earnings transcript excerpt
SEC filing data point
Reuters article summary
User-uploaded PDF quote
Manual note
Source-backed AI summary
```

Rules:

```text
Evidence should connect to claims, metrics, risks, conclusions, or events.
Evidence should include source reference metadata.
Evidence nodes should usually be hidden in low zoom and surfaced in Evidence View or node detail.
```

---

## risk

Represents a potential negative uncertainty or downside factor.

Examples:

```text
Cloud capex slowdown
GPU supply bottleneck
Power constraints
Regulatory tightening
Margin compression
Export restrictions
Overcapacity risk
```

Rules:

```text
Risks should connect to affected companies, metrics, claims, catalysts, and conclusions.
Risks should include severity and confidence where possible.
Risks are usually time-sensitive and should be update-checkable.
```

---

## catalyst

Represents a potential positive or negative trigger.

Examples:

```text
New product launch
Regulatory approval
Earnings beat
Rate cut
Major partnership
Capex acceleration
```

Rules:

```text
Catalysts should connect to affected companies, metrics, risks, claims, and conclusions.
Catalysts are time-sensitive.
```

---

## question

Represents an unresolved research gap or open question.

Examples:

```text
Is AI infrastructure demand sustainable beyond 2026?
Are valuations already pricing in GPU demand?
Will power constraints delay data center expansion?
Can Nvidia offset China weakness elsewhere?
```

Rules:

```text
Questions should connect to the node that raised the uncertainty.
Questions can connect to evidence gaps, risks, claims, or next research steps.
Questions help guide future research.
```

---

## conclusion

Represents a synthesized takeaway.

Examples:

```text
AI infrastructure growth remains strong but increasingly dependent on capex durability.
Power constraints are a material bottleneck for data center expansion.
Valuation support depends on sustained GPU demand and margin resilience.
```

Rules:

```text
Conclusions should connect to supporting claims and evidence.
Conclusions can be updated or contradicted by new information.
Conclusions should never appear unsupported.
```

---

## manual_note

Represents user-created notes or freeform thoughts.

Examples:

```text
Need to compare Nvidia and AMD margin sensitivity.
Remember to check latest cloud capex guidance.
This could become a brief section.
```

Rules:

```text
Manual notes can be unstructured.
Finora may suggest converting manual notes into typed nodes.
Manual notes should not automatically become claims unless the user accepts conversion.
```

---

## source

Represents a source object.

Examples:

```text
Reuters article
Company annual report
Earnings transcript
SEC filing
YouTube transcript
Uploaded PDF
```

Rules:

```text
Source nodes can appear in Evidence View.
Source nodes should connect to evidence nodes or directly to claims if the evidence is simple.
```

---

## brief_section

Represents a section in a brief output.

Examples:

```text
Executive Summary
Thesis
Market Drivers
Evidence
Risks
Open Questions
Conclusion
```

Rules:

```text
Brief section nodes are mostly used in Brief View.
They can receive dragged/selected graph nodes as brief inputs.
```

---

## suggested_node

Represents an AI-proposed node that has not yet been accepted.

Rules:

```text
Suggested nodes should appear as ghost nodes.
Suggested nodes should not become permanent until accepted.
Suggested nodes should have Accept / Edit / Dismiss actions when visible at high zoom or selected.
```

---

# 7. Node Schema

Recommended conceptual schema:

```ts
type GraphNode = {
  id: string;
  researchSpaceId: string;

  type:
    | "research_space"
    | "cluster"
    | "company"
    | "event"
    | "concept"
    | "metric"
    | "claim"
    | "evidence"
    | "risk"
    | "catalyst"
    | "question"
    | "conclusion"
    | "manual_note"
    | "source"
    | "brief_section"
    | "suggested_node";

  title: string;
  shortLabel: string;
  description?: string;

  clusterId?: string;

  sourceRefs?: SourceRef[];
  evidenceCount?: number;
  sourceCount?: number;

  confidence?: "low" | "medium" | "high";
  severity?: "low" | "medium" | "high";
  priority?: 1 | 2 | 3 | 4 | 5;

  updateSensitivity?: "low" | "medium" | "high";
  lastCheckedAt?: string;
  updateStatus?:
    | "none"
    | "needs_update"
    | "updated_today"
    | "source_missing"
    | "conflicting_evidence"
    | "stale";

  suggestionStatus?:
    | "none"
    | "suggested"
    | "accepted"
    | "dismissed"
    | "edited";

  createdBy: "user" | "ai";
  createdFrom:
    | "chat"
    | "source"
    | "manual"
    | "market_update"
    | "system";

  createdAt: string;
  updatedAt: string;
};
```

---

# 8. Node Creation Rules

Finora should create a node only when the extracted information is meaningfully reusable.

## Create a Node When

Create a node if the item is:

```text
A major entity
A recurring concept
A specific event
A measurable metric
A debatable claim
A source-backed evidence point
A risk
A catalyst
An open question
A synthesized conclusion
A user-created manual note
```

## Do Not Create a Node When

Do not create a node for:

```text
Trivial sentences
Generic filler
Repeated explanations that duplicate existing nodes
One-off phrasing differences
Unsupported speculation with no research value
A connection that only exists because two words are similar
```

## Duplicate Prevention

Before creating a node, Finora should check:

```text
1. Does an existing node already represent this idea?
2. Is this just a synonym or rewording?
3. Is this a more specific version of an existing node?
4. Should this update an existing node instead of creating a new one?
5. Should this become evidence for an existing claim instead of a new claim?
```

---

# 9. Node Display Rules

Nodes should reveal information gradually.

## Default Node Display

At normal map level, show:

```text
Type badge
Short title
Optional metadata
```

Example:

```text
RISK
Cloud capex slowdown
Needs update
```

Do not show full descriptions on every node by default.

## Selected Node Display

When selected, show:

```text
Full title
Type
Short description
Connected nodes
Evidence/source count
Confidence
Update status
Actions
```

Actions:

```text
Edit
Connect
Ask AI
View evidence
Add to brief
Archive
```

Node details should appear as:

```text
Inline expanded card
Floating popover
Mini-toolbar
```

Do not use a permanent right-side node detail panel, because the right panel should remain the AI chat panel.

---

# 10. Edge Types

Finora should use a controlled edge vocabulary.

Recommended edge types:

```text
is_part_of
affects
causes
contributes_to
supports
contradicts
depends_on
competes_with
is_example_of
raises_question
leads_to_research
derived_from
updates
related_to
```

`related_to` should be a last resort.

---

# 11. Edge Type Definitions

## is_part_of

Meaning:

```text
A belongs under B.
```

Examples:

```text
Revenue growth → is_part_of → Financial Impact
Cloud capex → is_part_of → Demand Drivers
Nvidia → is_part_of → Key Companies
```

Use when:

```text
Organizing nodes under clusters
Showing topic hierarchy
Grouping metrics/concepts/events under a broader theme
```

---

## affects

Meaning:

```text
A impacts B, but direction or magnitude may vary.
```

Examples:

```text
Power constraints → affects → Data center expansion
Export restrictions → affects → Nvidia China revenue
Interest rates → affects → Valuation multiples
```

Use when:

```text
There is an impact relationship but causality or direction is not certain enough for causes.
```

---

## causes

Meaning:

```text
A directly causes B.
```

Examples:

```text
Price cuts → causes → lower gross margin
Higher power costs → causes → higher data center operating costs
```

Use carefully.

Rules:

```text
Only use causes when causal direction is clear.
If uncertain, use affects or contributes_to instead.
```

---

## contributes_to

Meaning:

```text
A partially contributes to B.
```

Examples:

```text
Higher input costs → contributes_to → margin pressure
Cloud capex growth → contributes_to → GPU demand
```

Use when:

```text
A is one of multiple drivers behind B.
```

---

## supports

Meaning:

```text
A supports B.
```

Examples:

```text
Earnings transcript evidence → supports → AI capex demand claim
Revenue growth metric → supports → demand strength claim
Claim → supports → conclusion
```

Use when:

```text
Evidence supports a claim.
A claim supports a conclusion.
A metric supports a thesis.
```

---

## contradicts

Meaning:

```text
A weakens or conflicts with B.
```

Examples:

```text
Falling cloud capex guidance → contradicts → sustained GPU demand claim
Weak margin data → contradicts → margin expansion thesis
```

Use when:

```text
Evidence or new information challenges a claim, conclusion, or assumption.
```

---

## depends_on

Meaning:

```text
A relies on B.
```

Examples:

```text
Nvidia GPU supply → depends_on → TSMC advanced nodes
Data center expansion → depends_on → power availability
AI infrastructure rollout → depends_on → capital expenditure
```

Use when:

```text
A cannot fully happen or continue without B.
```

---

## competes_with

Meaning:

```text
A competes with B.
```

Examples:

```text
Nvidia → competes_with → AMD
AWS Trainium → competes_with → Nvidia GPUs
```

Rules:

```text
Usually bidirectional.
Use for companies, products, technologies, or market segments.
```

---

## is_example_of

Meaning:

```text
A illustrates B.
```

Examples:

```text
Tesla price cuts → is_example_of → margin compression
Export controls → is_example_of → geopolitical risk
GPU shortage → is_example_of → supply constraint
```

Use when:

```text
A concrete event or case helps explain a concept.
```

---

## raises_question

Meaning:

```text
A creates or reveals an open question.
```

Examples:

```text
Cloud capex slowdown → raises_question → Is AI infra demand sustainable?
Margin compression → raises_question → Is pricing power weakening?
```

Use when:

```text
A node introduces uncertainty or an unresolved research gap.
```

---

## leads_to_research

Meaning:

```text
A suggests a next investigation.
```

Examples:

```text
Customer concentration risk → leads_to_research → Check customer revenue breakdown
Weak evidence claim → leads_to_research → Find primary source
```

Use when:

```text
A finding suggests a concrete next research step.
```

---

## derived_from

Meaning:

```text
A was created from B.
```

Examples:

```text
AI summary → derived_from → Reuters article
Claim → derived_from → user chat message
Evidence node → derived_from → SEC filing
```

Use when:

```text
Tracking provenance.
```

---

## updates

Meaning:

```text
New information changes old information.
```

Examples:

```text
New earnings data → updates → previous revenue growth assumption
New regulation → updates → previous risk assessment
New capex guidance → updates → GPU demand outlook
```

Use when:

```text
The time-update system identifies changed information.
```

---

## related_to

Meaning:

```text
A has a loose relationship to B.
```

Rules:

```text
Use only as a last resort.
Avoid overusing related_to.
If too many edges are related_to, the graph becomes meaningless.
```

---

# 12. Edge Schema

Recommended conceptual schema:

```ts
type GraphEdge = {
  id: string;
  researchSpaceId: string;

  fromNodeId: string;
  toNodeId: string;

  type:
    | "is_part_of"
    | "affects"
    | "causes"
    | "contributes_to"
    | "supports"
    | "contradicts"
    | "depends_on"
    | "competes_with"
    | "is_example_of"
    | "raises_question"
    | "leads_to_research"
    | "derived_from"
    | "updates"
    | "related_to";

  direction: "directed" | "bidirectional";

  label?: string;
  explanation?: string;

  confidence: "low" | "medium" | "high";
  importance: 1 | 2 | 3 | 4 | 5;

  sourceRefs?: SourceRef[];

  status:
    | "suggested"
    | "accepted"
    | "edited"
    | "dismissed"
    | "archived";

  createdBy: "user" | "ai";
  createdFrom:
    | "chat"
    | "source"
    | "manual"
    | "market_update"
    | "system";

  createdAt: string;
  updatedAt: string;
};
```

---

# 13. Edge Creation Rules

Finora should create an edge only when there is a meaningful research relationship.

## Create an Edge When

Create an edge if it shows:

```text
A causal or impact relationship
Evidence supporting or contradicting a claim
A node belonging under a cluster
A metric affected by a driver/risk/event
A question raised by a claim/risk/metric
A conclusion supported by claims/evidence
A new update changing previous understanding
A dependency relationship
A competition relationship
A concrete example of an abstract concept
```

## Do Not Create an Edge When

Do not create an edge if:

```text
The relationship is vague
The only connection is keyword similarity
The edge does not help user understanding
The edge creates visual clutter without adding meaning
The edge repeats an existing relationship
The relationship has very low confidence and is not worth surfacing
```

## Edge Confidence

Every edge should have confidence:

```text
High: directly stated in source or obvious financial relationship
Medium: reasonable inference
Low: speculative or weak relationship
```

Low-confidence edges should be hidden by default unless the user asks to show weak links.

## Edge Importance

Every edge should have importance:

```text
5: critical relationship central to research space
4: important relationship
3: useful relationship
2: secondary relationship
1: low-priority relationship
```

Default map should show mainly importance 4–5 edges.

Importance 1–2 edges should usually appear only in focus mode, high zoom, or detailed evidence views.

---

# 14. Direction Rules

Relationships should be directional when one node influences another.

Examples:

```text
Hyperscaler capex → drives → GPU demand
GPU demand → supports → Nvidia revenue growth
Revenue growth → supports → valuation support
```

Use bidirectional edges only for peer relationships.

Examples:

```text
Nvidia ↔ competes_with ↔ AMD
Nvidia ↔ related_to ↔ AI infrastructure market
```

Rule:

```text
If one thing influences another, use directed.
If both are peers or mutual alternatives, use bidirectional.
```

---

# 15. Evidence and Claim Rules

This is one of the most important parts of Finora.

## Rule: Claims Need Evidence

Every claim should ideally connect to at least one evidence node.

Example:

```text
Earnings transcript → supports → Cloud capex remains strong
```

Unsupported claims should be marked:

```text
Needs source
Weak evidence
Conflicting evidence
```

## Rule: Separate Facts, Claims, and Conclusions

Do not collapse facts, claims, and conclusions into one node.

Example structure:

```text
Evidence → supports → Claim → supports → Conclusion
Evidence → contradicts → Claim
New Evidence → updates → Conclusion
```

Example:

```text
Fact/Evidence:
Microsoft capex guidance increased.

Claim:
Hyperscaler capex remains strong.

Conclusion:
AI infrastructure demand remains supported by cloud investment.
```

This separation allows Finora to update conclusions when new evidence appears.

---

# 16. Time-Update Rules

Certain nodes and edges are time-sensitive.

## Update-Sensitive Node Types

High update sensitivity:

```text
event
metric
claim
risk
catalyst
conclusion
company
```

Lower update sensitivity:

```text
concept
manual_note
cluster
research_space
```

## Update Check Should Inspect

```text
Stale metrics
Recent event nodes
Risk severity
Catalyst status
Claims based on old evidence
Conclusions based on outdated assumptions
Unsupported claims
Conflicting evidence
```

## Update Suggestion Format

Suggested updates should include:

```text
Existing node/edge
New information
Suggested change
Reason
Source/evidence
Confidence
Actions
```

Example:

```text
Existing:
Cloud capex slowdown risk

New information:
Latest guidance from hyperscalers suggests capex remains strong.

Suggested change:
Severity: High → Medium
Confidence: Medium → High

Reason:
New guidance weakens the slowdown assumption.

Actions:
Accept | Edit | Reject | Mark uncertain
```

## Do Not Silently Rewrite

Finora should not silently rewrite accepted graph content.

Updates should be:

```text
Suggested
Reviewable
Source-backed
Acceptable/rejectable
Tracked in timeline
```

---

# 17. Suggestion Rules

AI suggestions are not permanent until accepted.

## Suggestion Types

```text
Suggested node
Suggested edge
Suggested update
Suggested evidence link
Suggested open question
Suggested cluster
Suggested brief section
```

## Suggestion Display by Zoom

Low zoom:

```text
Cluster badge only
Example: Risks · 3 updates available
```

Medium zoom:

```text
Affected nodes marked
Example: Cloud capex slowdown · Needs update
```

High zoom:

```text
Ghost nodes/edges with actions
Accept | Edit | Dismiss
```

## Suggestion Placement

Suggestions should appear near the relevant cluster or node.

Examples:

```text
Risk suggestion → near Risks cluster
Evidence suggestion → near Evidence cluster or claim node
Question suggestion → near Open Questions cluster and source node that raised it
Metric suggestion → near Financial Impact cluster
```

## Suggestion Count Visibility

Total update/suggestion counts must remain visible at cluster level even when detailed suggested nodes are hidden by zoom.

Example:

```text
Risks
3 updates available
```

---

# 18. Semantic Zoom and Visibility Rules

Finora uses semantic zoom.

Users can freely zoom, and zoom percentage should be visible. The system changes detail level at thresholds.

## Recommended Zoom Levels

```text
25%–50%: Research Space Overview
51%–90%: Cluster Summary
91%–140%: Node Detail
141%–220%: Evidence / Editing Detail
220%+: Deep Inspect, optional
```

## Low Zoom: 25%–50%

Show:

```text
Research space node
Cluster nodes
Cluster badges
Very important cluster-to-cluster edges
```

Hide:

```text
Individual low-priority nodes
Evidence snippets
Full descriptions
Action buttons
Most edge labels
```

## Medium Zoom: 51%–90%

Show:

```text
Top nodes in clusters
Important paths
Cluster health
Affected nodes
```

Hide:

```text
Long summaries
Evidence snippets
Full controls
Low-priority edges
```

## Node Detail Zoom: 91%–140%

Show:

```text
Readable node cards
Type badges
Source counts
Confidence
Update status
Nearby relationship labels
Specific node-level update badges
```

## High Zoom: 141%–220%

Show:

```text
Full node cards
Short summaries
Evidence snippets
Ghost nodes
Ghost edges
Accept/Edit/Dismiss actions
Manual edit controls
```

## Hysteresis

Avoid flicker around thresholds.

Example:

```text
Cluster Summary → Node Detail only when zoom reaches 95%
Node Detail → Cluster Summary only when zoom drops below 85%
```

---

# 19. Cluster Focus Rules

Clusters act as focus/layer controls.

No top-bar layer buttons are required.

## Cluster Focus Trigger

User clicks a cluster node.

Example:

```text
Click Risks
```

## Cluster Focus Behavior

```text
Selected cluster becomes visually central
Nodes inside selected cluster are shown
Relevant external connected nodes remain visible
Unrelated nodes fade or hide
Relevant edges become prominent
Focus pill appears
```

Example focus pill:

```text
Focused: Risks ×
```

## Clear Focus

User can click `×`, press Escape, or click background to return to full map.

---

# 20. Node Focus Rules

## Node Click

Single click:

```text
Show compact popover or expanded preview
Highlight direct edges
Show mini-toolbar
```

## Node Double-Click

Double-click:

```text
Enter Focus View for that node
Center selected node
Show first-degree relationships
Optionally show second-degree relationships if useful
Fade unrelated graph
```

## Node Focus Should Show

```text
Selected node
Parent cluster
Direct drivers
Affected nodes
Supporting evidence
Contradicting evidence
Related open questions
Suggested updates
```

---

# 21. Edge Display Rules

Edges are the fastest way to destroy graph readability, so edge display must be strict.

## Default Map

Show only:

```text
Important cluster-to-cluster edges
High-importance node edges
Edges connected to selected/hovered node
Edges in current focus neighborhood
```

Hide:

```text
Low-confidence edges
Low-importance edges
Weak related_to edges
Evidence edges outside Evidence View
Most background edges
```

## Hover

When user hovers a node:

```text
Show direct edges
Fade unrelated edges
Highlight connected nodes
```

## Select

When user selects a node:

```text
Show first-degree edges clearly
Show edge labels
Optionally show second-degree edges faintly
```

## Focus Mode

Show:

```text
First-degree edges
Important second-degree edges
Evidence and question edges if relevant
```

---

# 22. Graph Hygiene Rules

To keep the graph usable:

```text
Every node should belong to a cluster.
Default map should never show all edges.
Evidence nodes should be hidden unless relevant.
Suggested nodes should start collapsed at low zoom.
Low-confidence edges should be hidden by default.
Unsorted nodes should be periodically reviewed.
Duplicate nodes should be merged or linked as aliases.
Clusters should show aggregate badges instead of expanding everything.
The UI should show 10–25 visible nodes by default, not hundreds.
```

The underlying database can store many nodes and edges. The UI should only reveal the amount needed for current thinking.

---

# 23. Brief Generation Rules

Briefs should be generated from selected graph context, not random raw chat history.

Possible brief inputs:

```text
Selected nodes
Selected clusters
Accepted claims
Evidence-backed conclusions
Risks
Open questions
Sources
Project memory
Current chat thread
```

Brief sections:

```text
Executive Summary
Thesis
Market Drivers
Evidence
Risks
Open Questions
Conclusion
```

Brief generation should warn if selected context has:

```text
Unsupported claims
Conflicting evidence
Stale metrics
Unresolved high-priority questions
```

---

# 24. Example End-to-End Workflow

## User Question

```text
How do export restrictions affect Nvidia's AI chip business?
```

## AI Chat Response

Finora answers in the right panel:

```text
Export restrictions can affect Nvidia by limiting the sale of advanced AI chips to China, increasing geopolitical revenue risk, and forcing Nvidia to rely on modified compliant chips. The impact depends on China exposure, substitute demand from other regions, and the regulatory path.
```

## Extracted Insights

```text
Company: Nvidia
Concept: Export restrictions
Metric: China revenue exposure
Risk: Further export controls
Claim: Export restrictions may pressure Nvidia's China AI chip revenue
Question: Can Nvidia offset China weakness elsewhere?
Conclusion: Geopolitical risk remains material for Nvidia's AI chip business
```

## Suggested Nodes

```text
RISK: Further export controls
METRIC: China revenue exposure
CLAIM: Export restrictions may pressure Nvidia's China AI chip revenue
QUESTION: Can Nvidia offset China weakness elsewhere?
CONCLUSION: Geopolitical risk remains material
```

## Suggested Edges

```text
Export restrictions → affects → China revenue exposure
China revenue exposure → affects → Nvidia revenue growth
Further export controls → raises_question → Can Nvidia offset China weakness elsewhere?
Evidence source → supports → Export restrictions may pressure Nvidia's China AI chip revenue
Claim → supports → Geopolitical risk remains material
```

## Canvas Placement

```text
Nvidia → Key Companies cluster
Export restrictions → Regulation/Risks cluster
China revenue exposure → Financial Impact cluster
Further export controls → Risks cluster
Open question → Open Questions cluster
```

## User Review

User sees ghost nodes and ghost edges on the canvas.

Actions:

```text
Accept
Edit
Dismiss
```

## Accepted Graph Update

Accepted nodes and edges become permanent.

The graph now supports future questions like:

```text
What should I investigate next?
Which risk has the weakest evidence?
Generate a brief from the export restriction risk path.
What changed since last week?
```

---

# 25. Implementation-Oriented Extraction Pipeline

Recommended internal pipeline:

```text
1. Receive user input
2. Run scope check
3. Generate AI response
4. Extract insight candidates
5. Classify candidates into node types
6. Compare against existing graph for duplicates
7. Assign candidate nodes to clusters
8. Generate candidate edges
9. Score confidence and importance
10. Attach source references
11. Create suggested graph updates
12. Render suggestions on canvas by zoom/focus state
13. User accepts/edits/dismisses
14. Persist accepted graph changes
15. Update project memory and timeline
```

---

# 26. Suggested Extraction Output Shape

AI extraction can output structured data like:

```json
{
  "candidate_nodes": [
    {
      "temporary_id": "node_1",
      "type": "risk",
      "title": "Further export controls",
      "shortLabel": "Export control risk",
      "description": "Further restrictions may limit Nvidia's ability to sell advanced AI chips into China.",
      "cluster": "Risks",
      "confidence": "medium",
      "importance": 4,
      "sourceRefs": ["source_1"],
      "suggestionReason": "User asked about export restrictions and the response identified regulatory downside."
    }
  ],
  "candidate_edges": [
    {
      "from": "Export restrictions",
      "to": "China revenue exposure",
      "type": "affects",
      "direction": "directed",
      "confidence": "high",
      "importance": 5,
      "explanation": "Restrictions affect Nvidia's ability to sell certain chips into China.",
      "sourceRefs": ["source_1"]
    }
  ],
  "duplicate_checks": [
    {
      "candidate": "Further export controls",
      "possibleExistingNode": "Export restriction risk",
      "recommendedAction": "merge_or_update"
    }
  ],
  "suggested_updates": [
    {
      "type": "create_node",
      "targetCluster": "Risks",
      "candidateNodeId": "node_1"
    }
  ]
}
```

---

# 27. Final Rules Summary

Finora graph rules in one place:

```text
1. The AI response appears in chat first.
2. The AI then extracts reusable insights from the response/source.
3. Insights become candidate nodes and edges.
4. Candidate nodes/edges are checked against existing graph content.
5. Candidate nodes are assigned to clusters.
6. Candidate edges use a controlled relationship vocabulary.
7. Suggestions appear on the canvas, not as a replacement for chat.
8. User accepts, edits, or dismisses suggestions.
9. Accepted suggestions become permanent graph memory.
10. Claims should connect to evidence.
11. Conclusions should connect to claims/evidence.
12. Questions should connect to the uncertainty that raised them.
13. New market information should create suggested updates, not silent rewrites.
14. Clusters act as focus/layer controls.
15. Semantic zoom controls detail visibility.
16. Edge visibility must be aggressively filtered.
17. The graph UI should reveal complexity gradually.
18. The right panel remains the AI assistant/chat.
19. The Overview tab manages research scope and configuration.
20. The canvas remains clean, graph-first, and source-backed.
```

---

# Final Direction

The final research graph should feel like:

```text
A clean, scoped, graph-first finance research workspace.
AI chat generates answers.
AI extraction turns answers and sources into suggested graph nodes and edges.
The user reviews suggestions directly on the canvas.
Accepted nodes and relationships become project memory.
The graph helps users understand market relationships, evidence, risks, open questions, and updates over time.
```
