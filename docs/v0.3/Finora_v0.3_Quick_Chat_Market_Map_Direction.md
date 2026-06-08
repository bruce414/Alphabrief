# Finora v0.3 New Direction: Quick Chat + Source Analysis + Market Map

## 1. Product Direction Summary

Finora v0.3 should focus on one clear user moment:

> “I’m reading financial news and I don’t fully understand what it means or what I should look at next.”

The first deliverable version should **not** ship the full dedicated research workspace or infinite canvas. That broader workspace requires too much UX complexity and should be treated as a later-stage feature.

Instead, v0.3 should ship:

> **Quick Chat with automatic source analysis and a right-side Market Map panel.**

The core product experience should be simple:

1. User asks a quick finance/market question.
2. Finora answers in normal chat.
3. User submits a financial source, such as a news URL, pasted article, earnings-related content, or market update.
4. Finora runs source analysis.
5. A right-side **Market Map** panel opens automatically.
6. The main chat shows the structured text analysis.
7. The Market Map visually shows entities, causes, impacts, risks, and what to watch next.
8. User can save the analysis for later.

This gives Finora a differentiated experience without forcing the user into a complex research workspace immediately.

---

## 2. Why This Direction

The previous direction had two major pieces:

1. **Quick Chat**
   - For quick market and finance questions.
   - Lightweight, easy to understand.
   - Good for general finance learning and simple source analysis.

2. **Dedicated Research Workspace**
   - User creates a broader research workspace.
   - Opens an infinite canvas.
   - Supports deeper research, manual organization, and long-term thinking.

The dedicated research workspace is still valuable long term, but it is too heavy for the first deliverable version.

The v0.3 deliverable should focus only on the strongest, clearest wedge:

> **Finora helps users understand financial news by explaining what happened, why it matters, and visually mapping how the news connects to the market.**

This direction is easier to build, easier to explain, and easier to validate with users.

---

## 3. Core User Problem

Users often read financial news but struggle to understand:

- What actually happened.
- Why the news matters.
- Which companies, sectors, or themes are affected.
- Whether the impact is short-term or long-term.
- What risks or uncertainties exist.
- What related news or events they should watch next.

Normal text summaries are helpful, but they are linear. Financial markets are connected systems. One event can affect multiple companies, sectors, macro themes, investor sentiment, and future events.

Therefore, Finora should combine:

- **Text explanation** for depth and reasoning.
- **Market Map** for relationships, structure, and follow-up paths.

---

## 4. Main Product Promise

The product promise for v0.3 should be:

> **Paste any financial news into Finora. It explains what happened, why it matters, and automatically builds a Market Map showing the companies, risks, themes, and follow-up events connected to the news.**

This is more specific and compelling than saying Finora is a general finance AI chat or a broad research workspace.

---

## 5. v0.3 Scope

### In Scope

v0.3 should include:

- Quick Chat interface.
- Finance-focused Q&A.
- Source submission through pasted URLs or pasted text.
- Structured source analysis.
- Automatic right-side Market Map panel.
- Entity extraction from the source and generated analysis.
- Relationship extraction between entities, risks, impacts, and follow-up items.
- Clickable map nodes with detail views.
- Save analysis feature.
- Saved analysis history.
- Tags for saved analysis.
- Basic related follow-up suggestions.

### Out of Scope

v0.3 should **not** include:

- Full infinite canvas workspace.
- Manually created research workspaces.
- Full drag-and-drop canvas editing.
- Custom user-created map nodes.
- Custom user-created edges.
- Project-wide graph memory.
- Multi-source merged graph.
- Advanced semantic zoom.
- Complex cluster layers.
- Portfolio-aware analysis.
- Stock recommendations.
- Buy/sell/hold advice.
- Full due diligence workflow.
- B2B analyst workspace.
- Financial advice features.

These can be revisited after the initial source-analysis experience is validated.

---

## 6. Product Architecture at a High Level

The first deliverable should have this structure:

```txt
Quick Chat
   |
   |-- Normal finance question
   |      -> Text answer only
   |
   |-- Source detected
          -> Structured source analysis
          -> Market Map generation
          -> Saveable analysis record
```

The Market Map should be treated as a **source-specific visual companion**, not as a full standalone workspace.

---

## 7. Quick Chat Behavior

Quick Chat remains the main product surface.

Users can ask:

- “What is EBITDA?”
- “Why do interest rates affect growth stocks?”
- “What happened to Nvidia today?”
- “How does inflation affect bank stocks?”
- “Explain this article.”
- “Analyze this news.”

### Text-Only Mode

For simple questions, Finora should respond only in chat.

Examples:

- Definitions.
- Simple finance concepts.
- Basic comparisons.
- Quick factual explanations.
- Short market questions.

The Market Map should **not** open for every question.

### Source Analysis Mode

The Market Map should open when the user submits or references a source, or when the query is relationship-heavy.

Examples:

- User pastes a financial news URL.
- User pastes article text.
- User submits a YouTube finance video link.
- User asks how a news event affects a company or sector.
- User asks about multi-entity market impact.
- User asks “what should I watch next?”

---

## 8. Market Map Concept

The Market Map is the key differentiating feature in v0.3.

It should answer:

> “How does this news connect to the market?”

The Market Map should show:

- The main event.
- Key companies.
- Sectors and themes.
- Market impacts.
- Risks and uncertainties.
- Follow-up items to watch next.
- Cause-and-effect relationships.

It should not be a decorative diagram. Every node and edge must help the user understand the financial meaning of the source.

---

## 9. Why Market Map Is Better Than Text Alone

Text is good for explaining:

> “What happened and why does it matter?”

The Market Map is better for showing:

> “How is this connected, what else is affected, and what should I look at next?”

Finance is a relationship-heavy domain. Market news often affects multiple entities at once.

Example:

```txt
U.S. Export Restrictions
   -> affects Nvidia China Revenue
   -> creates risk for Earnings Guidance
   -> may affect TSMC supply chain expectations
   -> may benefit AMD or other competitors
   -> connects to U.S.-China geopolitical risk
```

A text explanation can describe this, but the user has to mentally connect everything. A Market Map makes the structure visible.

---

## 10. Market Map UI Behavior

### Default State

Before source analysis, the UI should show:

```txt
┌──────────────┬─────────────────────────────────────┐
│ Left Sidebar │ Quick Chat                          │
│              │                                     │
│ History      │ Ask about markets, companies, news  │
│ Saved        │                                     │
│ Tags         │                                     │
└──────────────┴─────────────────────────────────────┘
```

### Source Analysis Starts

When a source is detected and submitted:

1. Chat begins analysis.
2. Right-side Market Map panel slides in with animation.
3. Main chat content is pushed left.
4. Market Map panel starts in loading/building state.

```txt
┌──────────────┬────────────────────────┬──────────────────────┐
│ Left Sidebar │ AI Analysis             │ Market Map            │
│              │                         │                      │
│ History      │ Analyzing source...     │ Building map...       │
│ Saved        │                         │ Extracting entities...│
│ Tags         │                         │ Finding relationships │
└──────────────┴────────────────────────┴──────────────────────┘
```

### Completed State

When analysis completes:

```txt
┌──────────────┬────────────────────────┬──────────────────────┐
│ Left Sidebar │ Source Analysis         │ Market Map            │
│              │                         │                      │
│ History      │ Summary                 │ Main event node       │
│ Saved        │ Why it matters          │ Company nodes         │
│ Tags         │ Market impact           │ Risk nodes            │
│              │ Risks                   │ Watch-next nodes      │
│              │ Watch next              │                      │
└──────────────┴────────────────────────┴──────────────────────┘
```

---

## 11. Panel Layout Rules

The Market Map should behave like a side panel, not a full workspace.

### Default Layout

- Left sidebar: fixed width, around 240px.
- Main chat: full width when Market Map is closed.
- Market Map: hidden by default.

### When Source Analysis Starts

- Market Map slides in from the right.
- Sidebar remains visible.
- Chat takes around 65% of remaining space.
- Market Map takes around 35% of remaining space.

### When Sidebar Is Collapsed

If the user collapses the left sidebar:

- Chat can take around 45–50%.
- Market Map can expand to around 50–55%.

### Controls

The Market Map panel should include:

- Collapse map button.
- Expand map button.
- Optional full-width view later.
- Zoom in/out.
- Reset view.
- Node detail drawer.

---

## 12. Animation Guidelines

The Market Map should open smoothly when source analysis starts.

Recommended behavior:

1. User submits source.
2. Chat shows source analysis loading state.
3. Market Map panel slides in from the right.
4. Panel initially shows skeleton map/loading state.
5. Entity chips appear as they are extracted.
6. Relationship preview appears.
7. Final graph renders when ready.

The animation should make the Market Map feel like part of the analysis process, not a random extra feature.

---

## 13. Market Map Loading States

The right panel should not be empty while AI is working.

Use progressive loading states:

### Stage 1: Source Detected

```txt
Source detected
Preparing financial analysis...
```

### Stage 2: Extracting Entities

```txt
Extracting entities...
[Nvidia] [China] [AI chips] [U.S. export controls]
```

### Stage 3: Mapping Relationships

```txt
Mapping relationships...
Export controls -> China revenue exposure
AI chip demand -> data center growth
Policy risk -> investor sentiment
```

### Stage 4: Final Map Ready

The final interactive Market Map appears.

---

## 14. Source Analysis Text Structure

The text analysis should be structured and consistent.

Recommended sections:

```md
## Summary
What happened?

## Why It Matters
Why is this financially or strategically important?

## Market Impact
Which companies, sectors, assets, or themes may be affected?

## Reasoning
Why could this news create those impacts?

## Risks and Uncertainties
What is not confirmed? What could change the interpretation?

## What to Watch Next
Which events, companies, data points, or news should the user follow next?
```

This structure should align with the Market Map.

---

## 15. Market Map Node Types

For v0.3, keep node types simple and limited.

Recommended node types:

| Node Type | Purpose | Example |
|---|---|---|
| Main Event | The core news event | “New U.S. AI chip export restrictions” |
| Company | Public/private company involved | Nvidia, AMD, TSMC |
| Sector / Theme | Broader market category | Semiconductors, AI infrastructure |
| Market Impact | Financial or market consequence | Revenue risk, margin pressure |
| Risk / Uncertainty | Unknowns or possible negative outcomes | China retaliation, demand uncertainty |
| Watch Next | Follow-up item | Earnings guidance, policy updates |

Avoid too many node types in v0.3. The goal is clarity, not visual complexity.

---

## 16. Market Map Edge Types

Edges should be labeled. Unlabeled edges are not useful enough.

Recommended edge labels:

- affects
- caused by
- increases risk for
- may benefit
- may pressure
- may offset
- depends on
- watch next
- linked to
- creates uncertainty around

Example:

```txt
U.S. Export Restrictions -> affects -> Nvidia
Nvidia -> exposed to -> China Revenue
China Revenue Risk -> affects -> Earnings Guidance
Cloud Demand -> may offset -> China Weakness
AMD -> may benefit from -> Nvidia Restriction Pressure
```

---

## 17. Node Detail Interaction

Clicking a node should open a detail view inside the Market Map panel.

Example node detail:

```md
### China Revenue Exposure

This matters because Nvidia may lose access to some Chinese customers if export restrictions limit high-end AI chip sales.

**Why it matters**
Potential revenue pressure in one geographic market.

**Evidence from source**
The article mentions tighter U.S. restrictions on AI chip exports to China.

**Watch next**
- Nvidia earnings guidance
- Management comments on China demand
- Further U.S. policy updates
```

Node detail should make the graph useful beyond surface-level visualization.

---

## 18. Linking Text Analysis and Market Map

The text analysis and Market Map should be connected.

Recommended behavior:

- Each node stores a linked analysis section ID.
- Clicking a node scrolls or highlights the relevant text section.
- Hovering over a text section can highlight related nodes.
- Clicking a “Watch Next” item can trigger a follow-up query or source search later.

For v0.3, simple section linking is enough.

---

## 19. Recommended Data Shape

The backend or AI pipeline should produce both:

1. A structured text analysis.
2. A structured Market Map JSON object.

Example:

```json
{
  "analysis": {
    "summary": "string",
    "why_it_matters": "string",
    "market_impact": "string",
    "reasoning": "string",
    "risks_and_uncertainties": "string",
    "watch_next": ["string"]
  },
  "market_map": {
    "nodes": [
      {
        "id": "event_1",
        "type": "main_event",
        "label": "U.S. AI chip export restrictions",
        "description": "New restrictions may limit sales of advanced AI chips to China.",
        "linked_section": "summary",
        "confidence": "medium"
      },
      {
        "id": "company_nvda",
        "type": "company",
        "label": "Nvidia",
        "description": "Most directly affected due to AI chip exposure.",
        "linked_section": "market_impact",
        "confidence": "high"
      },
      {
        "id": "impact_china_revenue",
        "type": "market_impact",
        "label": "China revenue exposure",
        "description": "Potential revenue risk if sales are restricted.",
        "linked_section": "risks_and_uncertainties",
        "confidence": "medium"
      }
    ],
    "edges": [
      {
        "id": "edge_1",
        "source": "event_1",
        "target": "company_nvda",
        "label": "affects",
        "description": "The export restrictions directly affect Nvidia because of its AI chip sales exposure.",
        "confidence": "high"
      },
      {
        "id": "edge_2",
        "source": "company_nvda",
        "target": "impact_china_revenue",
        "label": "creates risk for",
        "description": "Nvidia may face revenue pressure if China sales are restricted.",
        "confidence": "medium"
      }
    ]
  }
}
```

---

## 20. Suggested Frontend Components

Recommended components:

```txt
QuickChatPage
ChatMessageList
ChatInputBox
SourceAnalysisMessage
MarketMapPanel
MarketMapGraph
MarketMapNode
MarketMapEdge
MarketMapNodeDetailDrawer
ResizableSplitLayout
SaveAnalysisButton
AnalysisTagSelector
Sidebar
SavedAnalysisList
```

---

## 21. Suggested Frontend State

Example TypeScript state:

```ts
type AnalysisMode = "chat_only" | "source_analysis_with_map";

type MarketMapPanelStatus =
  | "idle"
  | "source_detected"
  | "extracting_entities"
  | "mapping_relationships"
  | "ready"
  | "error";

type MarketMapPanelState = {
  isOpen: boolean;
  widthRatio: number;
  isExpanded: boolean;
  selectedNodeId?: string;
  status: MarketMapPanelStatus;
};

type MarketMapNodeType =
  | "main_event"
  | "company"
  | "sector_theme"
  | "market_impact"
  | "risk_uncertainty"
  | "watch_next";

type MarketMapNode = {
  id: string;
  type: MarketMapNodeType;
  label: string;
  description: string;
  linkedSection?: string;
  confidence?: "low" | "medium" | "high";
};

type MarketMapEdge = {
  id: string;
  source: string;
  target: string;
  label: string;
  description?: string;
  confidence?: "low" | "medium" | "high";
};

type MarketMap = {
  nodes: MarketMapNode[];
  edges: MarketMapEdge[];
};
```

---

## 22. UX Rules

### Rule 1: Do Not Open Market Map for Every Query

Only open Market Map when the query/source benefits from relationship visualization.

### Rule 2: Map Must Explain Relationships

Do not show isolated entity bubbles. Every map should show meaningful edges.

### Rule 3: Every Node Must Earn Its Place

Every node should answer at least one of:

- What caused this?
- What does it affect?
- Who is exposed?
- What is uncertain?
- What should the user watch next?

### Rule 4: Keep the Map Small

For v0.3, target:

- 8–15 nodes.
- 8–20 edges.
- Maximum clarity over completeness.

### Rule 5: Text and Map Must Align

The map should be generated from the same reasoning as the text analysis, not as a disconnected visual.

### Rule 6: Avoid Financial Advice

The product should explain implications and possible effects, but should not provide direct buy/sell/hold recommendations in v0.3.

---

## 23. Save Analysis Behavior

Users should be able to save a completed source analysis.

Saved analysis should include:

- Source title.
- Source URL if available.
- Date analyzed.
- Structured text analysis.
- Market Map JSON.
- Tags.
- Related entities.
- Watch-next items.

This allows Finora to build toward a research history without needing the full research workspace yet.

---

## 24. Tags and History

Saved analysis should support lightweight organization.

Recommended tag examples:

- Company ticker: `NVDA`, `AAPL`, `TSLA`
- Sector: `Semiconductors`, `Banks`, `Energy`
- Theme: `AI`, `Inflation`, `Rates`, `China`
- Event type: `Earnings`, `Regulation`, `M&A`, `Macro`

The first version does not need advanced project management. Tags and saved history are enough.

---

## 25. Relationship to Future Research Workspace

The dedicated research workspace and infinite canvas should remain future scope.

Future workspace may include:

- Project-based research.
- Infinite editable canvas.
- Manual node creation.
- Manual note-taking.
- Multi-source graph merging.
- Long-term project memory.
- Clustered market maps.
- Semantic zoom.
- Brief generation from selected context.
- Broader research workflows.

But v0.3 should not depend on this.

The v0.3 Market Map can later become the foundation for the broader workspace.

---

## 26. Implementation Priority

### Priority 1: Quick Chat

- Stable chat layout.
- Finance-focused prompts.
- Normal Q&A flow.

### Priority 2: Source Detection and Analysis

- Detect source URLs or pasted source text.
- Produce structured source analysis.
- Handle unavailable source body honestly.

### Priority 3: Market Map Panel

- Right-side panel.
- Slide-in animation.
- Loading states.
- Final graph rendering.

### Priority 4: Node Detail and Text Linking

- Click node for detail.
- Link node to analysis section.

### Priority 5: Save Analysis

- Save text analysis and map.
- Add tags.
- Show saved analysis history.

---

## 27. MVP Acceptance Criteria

The first deliverable should be considered successful if:

1. User can ask normal finance questions in Quick Chat.
2. User can paste a financial news source.
3. Finora returns structured analysis.
4. Right-side Market Map opens during source analysis.
5. Market Map shows meaningful entities and relationships.
6. User can click nodes to understand details.
7. User can save the analysis.
8. Saved analysis can be reopened with the original text and map.
9. The product clearly feels different from a plain AI chat summary.

---

## 28. Final Product Positioning for v0.3

Use this as the guiding sentence:

> **Finora helps finance learners and retail investors understand financial news by explaining what happened, why it matters, and visually mapping what it connects to and what to watch next.**

This should guide all v0.3 design and implementation decisions.

If a feature does not support this sentence, it should be removed or postponed.
