# Finora Research Workspace UI Reference

## Product Context

Finora is an AI-powered finance research workspace. Each research space helps users explore a focused finance, market, company, or industry topic through chat, sources, and a living research graph.

The research workspace should not feel like a generic chat app. It should feel like a scoped, structured research environment where the user's research compounds over time.

The core product loop is:

1. User creates or opens a scoped research space.
2. User chats with Finora, pastes URLs, uploads sources, or manually adds notes.
3. Finora answers in the right-side AI chat panel.
4. Finora suggests new research nodes, edges, updates, risks, evidence, claims, or open questions.
5. Suggested nodes and edges appear directly on the canvas.
6. User accepts, edits, or dismisses suggestions in place.
7. The canvas becomes a living, source-backed market/research graph.
8. When the user reopens the research space, Finora can check time-sensitive nodes and surface updates.

The UI should be clean, graph-first, and minimal. The canvas should help users understand relationships, not overwhelm them with every detail at once.

---

## Global Layout

The research workspace uses a three-column structure:

```text
┌────────────────────┬──────────────────────────────────────┬────────────────────────────┐
│ Left Sidebar       │ Center Area                          │ Right AI Chat Panel         │
│                    │                                      │                            │
│ Navigation         │ Canvas or Overview content            │ AI assistant/chat           │
│ Manual tools       │ Research graph / settings             │ Recent response             │
│ User actions       │                                      │ Follow-up questions         │
│                    │                                      │ Input box                   │
└────────────────────┴──────────────────────────────────────┴────────────────────────────┘
```

### Left Sidebar

The left sidebar is for workspace navigation, manual tools, and user actions.

Recommended navigation items:

```text
Overview
Canvas
Sources
Memory
Briefs
```

Recommended toolsets:

```text
Sticky note
Mindmap node
Claim node
Evidence node
Risk node
Question node
Group / Frame
Connection
```

Footer actions:

```text
Brief
Pin
Share
User profile/settings
```

### Center Area

The center area changes depending on the selected left-sidebar tab.

- If `Overview` is selected, the center area shows the research space overview/configuration page.
- If `Canvas` is selected, the center area shows the graph-first canvas.
- If `Sources`, `Memory`, or `Briefs` are selected, the center area shows the corresponding workspace page.

### Right AI Chat Panel

The right panel should remain stable as the AI assistant/chat panel.

It should not be replaced by node suggestion dashboards, map suggestion dashboards, risk review dashboards, or configuration panels.

The right panel can include:

```text
AI assistant title
Current scoped chat context
Recent AI response
Source/research status
Follow-up questions
Chat input
Research mode selector
Attachment / URL / source controls
Small contextual notices
```

The right panel should always feel like:

```text
AI assistant + research chat + follow-up guidance
```

Not:

```text
Node suggestion dashboard
```

Node suggestions should appear directly on the canvas, not take over the AI chat panel.

---

# Canvas UI

## Canvas Purpose

The Canvas is the main research-thinking surface.

It should represent the research space as a living, source-backed graph/mind map. It grows from user chats, sources, manual notes, and AI suggestions.

The canvas is not a static dashboard. It is not a kanban board. It is not just a blank whiteboard.

It should feel like:

```text
A graph-first research map where complexity is revealed gradually through zoom, cluster focus, and node selection.
```

---

## Canvas Top Bar

The canvas top bar should remain minimal.

### Required Controls

```text
View selector
Zoom controls with percentage
Last checked status
Updates available status, only when updates exist
```

Recommended layout:

```text
View: Map ▼        − 100% +        Last checked · 2 days ago
                                      3 updates available
```

If no updates are available:

```text
View: Map ▼        − 100% +        Last checked · Today
```

Do not show:

```text
0 updates available
```

### Remove From Canvas Top Bar

The canvas top bar should not include:

```text
AI Intelligence toggle
Scope chips
Layer buttons such as Risks / Evidence / Implications / Updates
Too many action buttons
```

The canvas should remain clean and tidy.

---

## View Selector

The primary view selector should remain simple.

Recommended views:

```text
Map
Focus
Evidence
Timeline
Brief
```

### View Definitions

#### Map View

Default graph-first canvas view.

Shows the research space as a living map with:

```text
Central research topic
Major clusters
Research nodes
Relationship edges
Suggestion/update badges
Collapsed or expanded cluster details depending on zoom level
```

#### Focus View

Focused local graph view for a selected cluster or node.

Shows:

```text
Selected cluster or node
Directly connected nodes
Important first-degree relationships
Possibly second-degree relationships if useful
Relevant evidence
Open questions
Suggested updates
```

#### Evidence View

Graph-based claim/evidence view.

Shows:

```text
Claims
Evidence/source nodes
Support/contradiction relationships
Unsupported claims
Weak evidence areas
Source-backed confidence
```

#### Timeline View

Shows how the research graph changes over time.

Shows:

```text
Changed nodes
Stale nodes
New evidence
Suggested updates
Accepted/rejected update history
Compact update log
```

#### Brief View

Output-building view.

Shows structured brief sections:

```text
Executive Summary
Thesis
Market Drivers
Evidence
Risks
Open Questions
Conclusion
```

Users can drag selected graph nodes into brief sections.

Brief View can be more card/section-based than graph-based because the user is creating an output.

---

## Layer Buttons Are Removed

Do not use top-bar layer buttons like:

```text
All
Risks
Implications
Evidence
Questions
Updates
```

Instead, clusters inside the graph act as the layer/focus controls.

For example, the graph can include cluster nodes such as:

```text
Risks
Evidence
Open Questions
Implications
Updates
Key Companies
Financial Impact
Demand Drivers
Infrastructure Stack
```

When a user selects a cluster node, the canvas enters focus mode for that cluster.

Example:

```text
User clicks "Risks" cluster
→ Risk cluster becomes focused
→ Risk nodes are highlighted
→ Related affected nodes remain visible
→ Unrelated nodes fade
→ Risk-impact edges become prominent
```

This keeps the UI graph-first and avoids top-bar clutter.

---

## Semantic Zoom

### Principle

Users should freely zoom in and out, and the UI should visually display zoom as a percentage.

Example:

```text
40%
75%
100%
150%
```

However, Finora should use semantic zoom thresholds behind the scenes. Different detail levels appear based on zoom percentage.

The graph should not simply scale the same content larger or smaller. It should reveal more or less information depending on zoom level.

### Recommended Zoom Range

```text
Minimum zoom: 25%
Maximum zoom: 220% to 240%
```

### Semantic Zoom Levels

#### Level 1: Research Space Overview

Recommended range:

```text
25%–50%
```

Visible:

```text
Central research space node
Major cluster nodes
Cluster-level update/suggestion badges
Very important cluster-to-cluster edges only
```

Hidden:

```text
Individual detailed nodes
Evidence snippets
Full node descriptions
Most edge labels
Action buttons
Ghost node details
```

Example:

```text
AI Infra 2026

Demand Drivers       Key Companies
Infrastructure       Financial Impact
Risks                Evidence
Open Questions       Catalysts
```

Cluster badge example:

```text
Risks
3 updates available
```

#### Level 2: Cluster Summary

Recommended range:

```text
51%–90%
```

Visible:

```text
Top nodes inside each cluster
Important paths
Cluster health/status
Update/suggestion badges attached to relevant clusters
Minimal node metadata
```

Hidden:

```text
Long node summaries
Evidence snippets
Full action controls
Low-priority edges
```

Example:

```text
Demand Drivers
- Hyperscaler capex
- AI model training demand
- Enterprise AI adoption
```

#### Level 3: Node Detail

Recommended range:

```text
91%–140%
```

Visible:

```text
Readable node cards
Node type badges
Source counts
Confidence
Update status
Nearby relationship labels
Specific node-level update badges
```

Hidden:

```text
Long descriptions
Evidence snippets
Full suggestion controls unless selected
```

Example node:

```text
DRIVER
Hyperscaler capex
4 sources
Supports: GPU demand
```

#### Level 4: Evidence / Editing Detail

Recommended range:

```text
141%–220%
```

Visible:

```text
Full node cards
Short descriptions
Evidence snippets
Ghost suggested nodes
Ghost suggested edges
Accept / Edit / Dismiss actions
Connection controls
```

Example selected/suggested node:

```text
Suggested by AI
RISK
Cloud capex slowdown

May reduce GPU demand and delay data center expansion if hyperscalers pull back spending after 2026.

Accept | Edit | Dismiss
```

#### Level 5: Deep Inspect, Optional

Recommended range:

```text
220%+
```

Visible:

```text
Detailed source snippets
Full evidence details
Manual editing fields
Expanded update history
```

This level is optional and should not be required for normal use.

---

## Zoom Transition Behavior

Avoid flickering when users zoom near threshold boundaries.

Use a small buffer/hysteresis.

Example:

```text
Cluster Summary → Node Detail only when zoom reaches 95%
Node Detail → Cluster Summary only when zoom drops below 85%
```

The UI should not rapidly switch back and forth when the user is near a threshold.

---

## Resolution and Rendering Requirements

The canvas must remain crisp when users zoom in and out.

Do not render the canvas as one large raster image.

Recommended rendering approach:

```text
Nodes/cards: real React/HTML components
Text: real text, not image text
Edges: SVG paths or high-quality canvas/WebGL rendering
Zoom/pan: transform-based interaction with semantic component changes
```

Avoid:

```text
Rasterizing the entire canvas into a bitmap
Scaling screenshots or image-based nodes
Blurry text during zoom
```

The map should feel sharp at all zoom levels.

---

## Graph Structure

### Core Graph Objects

The graph should contain typed nodes and typed edges.

Recommended node types:

```text
Research Space
Cluster
Company
Event
Concept
Metric
Claim
Evidence
Risk
Catalyst
Question
Conclusion
Manual Note
Suggested Node
```

Recommended edge types:

```text
drives
supports
contradicts
affects
constrains
depends on
raises question
derived from
updates
is example of
is part of
```

### Central Research Node

Each research space should have a central node.

Example:

```text
AI Infra 2026
38 nodes · living map
```

Major clusters grow around this central node.

Example clusters:

```text
Demand Drivers
Key Companies
Infrastructure Stack
Financial Impact
Risks
Evidence
Open Questions
Catalysts
Updates
```

---

## Cluster Behavior

Every node should belong to a cluster unless it is temporarily in an `Unsorted` cluster.

Clusters are both visual containers and navigation/focus controls.

### Cluster Node

At low zoom, a cluster appears as one large node/card.

Example:

```text
Risks
7 nodes
3 updates available
1 high severity
```

### Cluster Focus

When the user clicks a cluster node:

```text
The canvas enters cluster focus mode.
```

Cluster focus behavior:

```text
Selected cluster becomes central
All nodes inside the cluster become visible
Relevant connected nodes outside the cluster remain visible
Unrelated clusters/nodes fade
Relevant edges become prominent
Breadcrumb/focus pill appears
```

Example focus pill:

```text
Focused: Risks ×
```

Clicking `×` clears focus and returns to the full map.

### Cluster-Level Update Badges

Updates and suggestions should never disappear just because detailed nodes are hidden at low zoom.

At low zoom, show badges on clusters.

Example:

```text
Risks
3 updates available
```

At higher zoom, reveal the specific affected nodes.

Update visibility hierarchy:

```text
Low zoom: cluster badge only
Medium zoom: cluster badge + affected top nodes marked
Node detail zoom: specific node badges like Needs update
High zoom/editing detail: full ghost update with Accept/Edit/Dismiss
```

---

## Node Behavior

### Node Default Display

Nodes should be lightweight by default.

At normal map level, show:

```text
Type badge
Short title
Optional small metadata
```

Example:

```text
DRIVER
Hyperscaler capex
4 sources
```

Do not show full descriptions on every node by default.

### Node Selection

When the user clicks a node, show more details.

Recommended behavior:

```text
Single click: show compact popover or inline expanded preview
Double click: enter Focus View for that node
```

### Selected Node Detail

Selected node detail can appear as:

```text
Inline expanded card
Floating popover near node
Small contextual mini-toolbar
```

Do not use a permanent right-side node details panel, because the right panel should remain the AI chat assistant.

Selected node detail may show:

```text
Full title
Node type
Short description
Connected nodes
Evidence/source count
Update status
Confidence
Actions
```

Example:

```text
RISK
Cloud capex slowdown

May reduce GPU demand and delay data center expansion if hyperscalers pull back spending after 2026.

Affects:
- GPU demand
- Nvidia revenue growth
- Valuation support

Evidence:
- 3 sources
- 1 source needs re-check

Actions:
Ask AI · View evidence · Add to brief · Edit
```

### Node Actions

Default canvas should not show many action buttons.

Actions should appear only when relevant:

```text
Hover: minimal "..." menu
Select: small mini-toolbar
Suggested ghost node at high zoom: Accept / Edit / Dismiss
```

Possible node actions:

```text
Edit
Connect
Ask AI
View evidence
Add to brief
Archive
```

---

## Focus Mode

Focus Mode helps users inspect one cluster or node without being overwhelmed by the full graph.

### Trigger

Focus Mode can be triggered by:

```text
Clicking a cluster node
Double-clicking a regular node
Selecting "Focus" from a node mini-toolbar
```

### Focus Mode Behavior

When active:

```text
Selected cluster/node becomes central
Directly connected nodes are shown
Important second-degree nodes may be shown if useful
Unrelated nodes fade or hide
Relevant edges become clear
Node details become easier to inspect
```

Example: selected node `Regulatory Tightening`

Visible neighborhood:

```text
Evidence sources
→ Regulatory Tightening
→ Compliance costs
→ Margin pressure
→ Shift to subscription revenue

Regulatory Tightening
→ Open question: Will new rules reduce transaction volume?
```

### Clear Focus

Always provide a subtle way to leave focus mode.

Example:

```text
Focused: Regulatory Tightening ×
```

or:

```text
Back to full map
```

---

## Edge Display Rules

Edges can make the graph messy quickly, so they must be filtered aggressively.

### Default Edge Rule

The default map should not show every edge.

Show only:

```text
Important cluster-to-cluster edges
Edges connected to selected/hovered node
Edges in the current focus neighborhood
High-confidence/high-importance edges
Edges relevant to the current view
```

Hide or fade:

```text
Low-confidence edges
Weak related_to edges
Evidence edges unless Evidence View is active
Most background edges
```

### Edge Visibility by Zoom

#### Low zoom

Show only high-level cluster-to-cluster edges.

Example:

```text
Demand Drivers → Financial Impact
Risks → Financial Impact
Infrastructure Stack → Demand Drivers
```

#### Medium zoom

Show important node-level edges.

Example:

```text
Hyperscaler capex → GPU demand
GPU demand → Nvidia revenue growth
```

#### High zoom

Show nearby direct edges and relationship labels.

#### Selected node / focus mode

Show first-degree edges clearly and optionally second-degree edges.

### Edge Labels

Use concise labels:

```text
drives
supports
affects
constrains
pressures
raises risk
contradicts
updates
```

Avoid long edge labels.

---

## Suggestions and Updates

AI suggestions should be reviewed on the canvas, not primarily in the right AI chat panel.

### Suggestion Types

Finora may suggest:

```text
New node
New edge
Updated node
Updated relationship
Missing evidence
New open question
Stale claim
Conflicting evidence
```

### Low-Zoom Suggestion Display

At low zoom, suggestions should appear as cluster-level badges.

Example:

```text
Risks
2 suggestions
3 updates available
```

### Medium-Zoom Suggestion Display

At medium zoom, show affected top nodes and small suggestion indicators.

Example:

```text
Cloud capex slowdown
Needs update
```

### High-Zoom Suggestion Display

At high zoom, show ghost nodes or ghost edges.

Ghost node style:

```text
Dashed border
Slight transparency
Small "Suggested by AI" label
Accept / Edit / Dismiss actions
```

Ghost edge style:

```text
Dashed relationship line
Small label
Accept connection action
```

Example:

```text
Suggested by AI
CLAIM
DUV unwind → N3/N2 acceleration

Accept | Edit | Dismiss
```

### Update Badges

Possible badges:

```text
3 updates available
Needs update
Updated today
Source missing
Conflicting evidence
Weak evidence
New source
```

Important rule:

```text
Total update/suggestion counts must remain visible at cluster level even when the affected detailed nodes are hidden by zoom level.
```

---

## Right AI Chat Panel Behavior

The right AI chat panel should remain stable and usable across all canvas states.

It should not be replaced by:

```text
Map suggestions panel
Node suggestions panel
Risk review panel
Chain suggestions panel
```

Instead, it may show small contextual notices.

Example:

```text
Two new nodes are waiting on the map. Accept or dismiss them in place.
```

The right panel should include:

```text
AI assistant title
Current research space context
Recent response
Source count/status
Follow-up questions
Chat input
Research mode selector
```

Example title:

```text
Finora assistant
AI Infra 2026 · scoped chat
```

Example follow-up questions:

```text
Which driver has the weakest evidence today?
How would a 20% capex pullback ripple through this map?
What second-order effects would export controls have?
```

---

# Overview Tab

## Purpose

The `Overview` tab is the configuration and summary page for the research space.

It should replace the center canvas area when selected.

The Overview tab exists because the canvas should stay clean. Research scope, settings, boundaries, and configuration should not clutter the canvas top bar.

The Overview page answers:

```text
What is this research space about?
What is included or excluded?
What should Finora track?
How should Finora behave inside this space?
What is the update/checking configuration?
```

---

## Overview Page Layout

The Overview page should use a clean settings/summary layout.

Recommended sections:

```text
Research Space Summary
Research Scope
Research Rules / Boundaries
Update Settings
Graph / Canvas Settings
Research Status
```

The page should look polished and non-technical, even though it represents configuration.

---

## Research Space Summary Section

Show:

```text
Research space title
Short description
Research goal
Research type
Created date
Last active date
Last checked date
Update status
```

Example:

```text
Title:
AI Infra 2026

Description:
Researching AI infrastructure market growth, hyperscaler capex, chip supply, data center demand, power constraints, and investment implications through 2026.

Research goal:
Understand key market drivers, risks, evidence, and implications for AI infrastructure companies.

Research type:
Market research / investment learning

Status:
Last checked 2 days ago · 3 updates available
```

---

## Research Scope Section

Scope should live in the Overview tab, not permanently on the canvas top bar.

Editable fields:

```text
Included topics
Excluded topics
Target companies/entities
Time horizon
Research depth
Preferred output type
```

Example:

```text
Included topics:
- AI infrastructure market
- Cloud capex
- Chips
- Data centers
- Power/energy constraints
- GPU supply chain

Excluded topics:
- Consumer AI apps
- Crypto mining
- Unrelated macro unless directly connected

Target entities:
- Nvidia
- AMD
- TSMC
- ASML
- Microsoft
- Google
- Meta
- Amazon

Time horizon:
2025–2026

Research depth:
Standard research

Preferred output:
Living market map + structured brief
```

---

## Research Rules / Boundaries Section

This section defines how Finora handles off-topic questions and scope drift.

Example behavior:

```text
If the user asks something outside this research scope, Finora should ask whether to:
1. Treat it as a one-off chat
2. Add it to this research space
3. Create a new research space
```

Recommended setting rows:

```text
Require confirmation before adding off-scope topics
Allow one-off questions inside the right chat panel
Suggest new research space for unrelated topics
Warn when a new question may pollute the current research map
```

---

## Update Settings Section

This section controls real-time market update behavior.

Settings:

```text
Auto-check time-sensitive nodes when reopening this space
Check stale claims, metrics, risks, and conclusions
Check for new sources related to high-priority nodes
Show update suggestions before changing the canvas
Require user approval before applying updates
Highlight stale nodes on the map
```

Example:

```text
Auto-check time-sensitive nodes: On
Require approval before applying updates: On
Highlight stale nodes: On
```

Important principle:

```text
Finora should not silently rewrite the research graph. Updates should be suggested and reviewable.
```

---

## Graph / Canvas Settings Section

This section controls how the canvas behaves.

Settings:

```text
Auto-suggest new nodes from AI chat
Show suggested nodes directly on canvas
Show suggested edges directly on canvas
Auto-cluster related nodes
Use semantic zoom
Show cluster-level update badges
Show evidence links
Show relationship labels at detailed zoom
Hide low-confidence edges by default
```

Recommended defaults:

```text
Auto-suggest new nodes from AI chat: On
Show suggested nodes directly on canvas: On
Auto-cluster related nodes: On
Use semantic zoom: On
Show cluster-level update badges: On
Hide low-confidence edges by default: On
```

---

## Research Status Section

This section gives the user a quick health check of the research space.

Show:

```text
Total nodes
Total sources
Open questions
Unsupported claims
Stale risks
Available updates
Last checked date
```

Example:

```text
38 nodes
12 sources
7 open questions
3 unsupported claims
2 stale risks
3 updates available
Last checked 2 days ago
```

This section can include a button:

```text
Run update check
```

or:

```text
Review available updates
```

---

## Overview Tab Design Principles

The Overview tab should be:

```text
Clear
Editable
Non-cluttered
Configuration-focused
Research-space-specific
```

It should not feel like a developer settings page.

Use friendly labels and concise explanations.

Avoid overwhelming the user with too many toggles at once. Group settings into collapsible sections if needed.

---

# Clean UI Principles

## Keep Canvas Clean

Do not overload the canvas with buttons.

Default canvas should show:

```text
Graph nodes
Cluster nodes
Important edges
Badges
Minimal top controls
```

Actions should appear only on:

```text
Hover
Selection
Focus mode
High zoom detail
```

## Keep Right Panel Stable

The right panel should always remain the AI assistant/chat panel.

Do not use it as the main node/update management panel.

## Keep Suggestions Contextual

Suggestions should appear where they belong:

```text
Cluster badge at low zoom
Affected node badge at medium zoom
Ghost node/edge at high zoom
Full action controls only when selected or zoomed in
```

## Keep Scope Out of Canvas Top Bar

The research scope is managed in the Overview tab.

The canvas top bar should not show permanent scope chips.

## Make Updates Visible But Not Noisy

If updates exist, show:

```text
3 updates available
```

If none exist, hide the update badge entirely.

---

# Recommended Final Canvas Mental Model

```text
Semantic zoom controls how much detail is visible.
Cluster selection controls what area the user is focused on.
Node selection controls what specific idea the user is inspecting.
The right panel remains the AI chat assistant.
The Overview tab manages research space configuration.
```

---

# Implementation Notes for Claude Code

The UI should be designed around state-driven rendering.

Important state variables:

```ts
type CanvasView = "map" | "focus" | "evidence" | "timeline" | "brief";

type SemanticZoomLevel =
  | "research_space_overview"
  | "cluster_summary"
  | "node_detail"
  | "evidence_editing_detail"
  | "deep_inspect";

type FocusTarget =
  | { type: "cluster"; id: string }
  | { type: "node"; id: string }
  | null;

type UpdateStatus = {
  lastCheckedAt: string;
  updatesAvailableCount: number;
};

type GraphNode = {
  id: string;
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
    | "suggested_node";

  title: string;
  shortLabel: string;
  description?: string;
  clusterId?: string;
  sourceCount?: number;
  confidence?: "low" | "medium" | "high";
  updateStatus?: "none" | "needs_update" | "updated_today" | "source_missing" | "conflicting_evidence";
  suggestionStatus?: "none" | "suggested" | "accepted" | "dismissed";
};

type GraphEdge = {
  id: string;
  fromNodeId: string;
  toNodeId: string;
  type:
    | "drives"
    | "supports"
    | "contradicts"
    | "affects"
    | "constrains"
    | "depends_on"
    | "raises_question"
    | "derived_from"
    | "updates"
    | "is_example_of"
    | "is_part_of";

  confidence?: "low" | "medium" | "high";
  suggestionStatus?: "none" | "suggested" | "accepted" | "dismissed";
};
```

Semantic zoom should be computed from the visual zoom percentage.

Example:

```ts
function getSemanticZoomLevel(zoom: number): SemanticZoomLevel {
  if (zoom <= 50) return "research_space_overview";
  if (zoom <= 90) return "cluster_summary";
  if (zoom <= 140) return "node_detail";
  if (zoom <= 220) return "evidence_editing_detail";
  return "deep_inspect";
}
```

Use hysteresis/buffer in the real implementation to avoid flickering at thresholds.

---

# Final Direction

The final UI should feel like:

```text
A clean, scoped, graph-first finance research workspace.
The canvas is the living market map.
The Overview tab manages research space configuration.
The right panel is always the AI assistant/chat.
Complexity is revealed through semantic zoom, cluster focus, and node selection.
Updates and suggestions remain visible at cluster level even when detailed nodes are hidden.
```
