# AlphaBrief v0.3 Technical Architecture

## Version

`v0.3 First Milestone — One Ask Box → Smart Source Detection → Freeform Canvas → On-demand Briefs`

## Status

This architecture reflects AlphaBrief's latest direction:

```text
Market learning + research workspace
Projects as top-level containers
Threads/chats as focused explorations inside projects
One universal Ask box with smart source detection
Sources attached to chats and projects
Canvas as a freeform editable visual thinking space
Memory as explicit project-level understanding
Briefs as on-demand generated outputs from selected context
Chrome Extension-ready source ingestion
Adaptive external-source research architecture
```

The earlier architecture treated Canvas as the source of truth for formal brief generation. The updated architecture makes Canvas the **middle visual understanding workspace**, while brief generation uses explicit selected context:

```text
current thread
selected sources
project memory
selected Canvas elements or cluster
full project context when requested
```

This is better for v0.3 because users can paste a link and ask for analysis without first turning their Canvas into a sacred database shrine. Progress, somehow.

---

# 1. Product Goal

AlphaBrief v0.3 should prove this loop:

```text
Ask naturally or paste a source
→ AlphaBrief detects source/intent
→ analyze inside a project thread
→ AI suggests useful Canvas candidates
→ user builds understanding in a freeform Canvas
→ project Memory captures durable understanding
→ user generates briefs on demand from chosen context
→ user keeps researching over time
```

The Chrome extension strengthens source capture:

```text
Read article/video page
→ click AlphaBrief extension
→ create Source
→ attach Source to project chat
→ promote useful insights/images/quotes to Canvas
```

AlphaBrief is not only a one-click report generator. The core product bet is that users need a workspace to build understanding over time, not just another AI answer that evaporates into chat sludge.

---

# 2. Recommended Stack

## Frontend Web App

```text
React
TypeScript
Vite or Next.js
TailwindCSS
shadcn/ui or similar component system
react-router v6 if Vite
```

## Freeform Canvas Layer

Recommended options:

```text
React Flow        # good for nodes/edges/mind-map-like structures
Konva / react-konva # good for freeform canvas and shapes
Tldraw SDK        # strong whiteboard behavior, heavier dependency
Custom absolute-positioned div canvas # simplest first implementation
```

v0.3 pragmatic recommendation:

```text
Start with a custom absolute-positioned CanvasElement layer.
Add React Flow or a graph library only if connectors/mind-map behavior becomes painful.
```

## Chrome Extension

```text
Chrome Extension Manifest V3
TypeScript
React optional for popup UI
Content script
Service worker
activeTab permission where possible
```

## Backend

```text
Python
FastAPI
SQLAlchemy 2.x async
Alembic
Pydantic
PostgreSQL
```

## Background Processing

For early v0.3:

```text
FastAPI BackgroundTasks
```

For later scale:

```text
RQ + Redis
Celery + Redis
Arq + Redis
```

Do not start with distributed-worker theater until the simple version actually hurts.

---

# 3. High-Level Architecture

```text
React/TypeScript Workspace App
        ↓
FastAPI API Layer
        ↓
Service Layer
        ↓
Repository Layer
        ↓
PostgreSQL

Chrome Extension
        ↓
Source ingestion API
        ↓
Same Source / Chat / Canvas pipeline
```

External services should sit behind client classes:

```text
AI Provider Client
Article Extraction Client
YouTube Transcript/Metadata Client
PDF Extraction Client
Company Data Client optional lightweight
Market/News API Client optional lightweight
Object Storage Client
```

---

# 4. Client Surfaces

| Client Surface | Purpose |
|---|---|
| Web App | Main research workspace: Projects, Agent chat, Canvas, Sources, Memory, Briefs |
| Chrome Extension | User-initiated page capture and source creation from current browser page |

## Web App Core Areas

| Area | Purpose |
|---|---|
| Project Sidebar | Top-level navigation; Catchall pinned; user projects and threads below |
| Center Canvas | Freeform editable thinking workspace |
| Agent Panel | Ask box, source analysis, AI replies, add-to-Canvas actions |
| Sources Tab | Evidence library for project/thread |
| Memory Tab | Explicit accumulated project understanding |
| Brief View | Generated brief versions and history |

---

# 5. Workspace UI Architecture

## 5.1 Layout

Recommended MVP layout based on the latest design:

```text
Left sidebar: Projects + threads
Center pane: Freeform Canvas
Right pane: Agent chat
Top tabs: Canvas | Sources | Memory
Top action: Generate brief
```

This is different from the previous left-chat/right-canvas layout.

The Canvas should feel central. The Agent should feel like the assistant beside the user's thinking board.

## 5.2 Project Sidebar

Responsibilities:

```text
- Show brand/date/user area if desired
- Show Catchall or active projects
- Show threads inside selected project
- Create new thread
- Search projects/threads
- Navigate to /workspace/projects/:projectId/threads/:chatId
```

## 5.3 Center Canvas

Responsibilities:

```text
- Render freeform Canvas elements
- Support text elements
- Support AI-imported blocks
- Support image/screenshot elements
- Support simple mind-map nodes
- Support connector lines
- Support group/frame elements
- Drag/move/resize elements
- Edit text directly or through a side/popover editor
- Preserve source/chat provenance
- Allow selected area actions
```

Minimum v0.3 Canvas operations:

```text
create text
create image
create node
move
resize
edit
delete/archive
duplicate
connect elements
group selected
add AI answer to Canvas
add source quote/note to Canvas
```

## 5.4 Agent Panel

Responsibilities:

```text
- One Ask box
- Allow paste URL / YouTube / source / question naturally
- Detect source type after send
- Show assistant answer cards
- Show source chips/citations
- Show candidate Canvas suggestions
- Provide Add to Canvas actions
- Trigger brief generation when requested
```

Recommended placeholder:

```text
Ask, paste a URL, or upload a source to research...
```

## 5.5 Sources Tab

Responsibilities:

```text
- List sources for project/thread
- Show extraction status
- Show metadata-only/full-text status
- Show linked Canvas elements and chat turns
- Allow source re-analysis
- Allow Add quote/note to Canvas
```

## 5.6 Memory Tab

Responsibilities:

```text
- Show project summary
- Show entities/tickers/themes
- Show open questions
- Show current conclusions
- Allow user edits
- Later: AI refresh from recent project activity
```

## 5.7 Brief View

Responsibilities:

```text
- Create brief series
- Generate new version from selected context
- Show context used for generation
- Show version history
- Show what changed between versions
```

Brief generation should not assume Canvas is the only source. Let users choose context because apparently agency is useful.

---

# 6. Chrome Extension Architecture

The Chrome extension is a lightweight source capture layer.

```text
extension/
├── manifest.json
├── popup/
│   ├── popup.html
│   └── popup.tsx
├── content/
│   └── content-script.ts
├── background/
│   └── service-worker.ts
├── lib/
│   ├── extractArticle.ts
│   ├── apiClient.ts
│   └── auth.ts
└── assets/
```

## Extension Responsibilities

```text
1. Run only after explicit user action
2. Read current active tab when permitted
3. Extract page/video metadata
4. Extract readable text when available
5. Show preview/status to user
6. Send source payload to backend
7. Open source or workspace in web app
```

## Extension Non-Responsibilities

```text
1. No broad background crawling
2. No paywall bypass
3. No CAPTCHA bypass
4. No login-wall bypass positioning
5. No hidden browsing-history collection
6. No permanent local archive of article text
```

## Extension Auth for v0.3

Recommended initial auth:

```text
1. User logs into web app.
2. User generates extension token from settings.
3. Extension stores token in chrome.storage.
4. Extension sends Authorization: Bearer <extension_token>.
5. Backend maps token to user and applies ownership rules.
```

Preferred permissions:

```json
{
  "permissions": ["activeTab", "scripting", "storage"],
  "host_permissions": ["https://api.alphabrief.com/*"]
}
```

Avoid `<all_urls>` unless truly needed later.

---

# 7. Backend Package Structure

```text
backend/app/
├── api/
│   ├── deps.py
│   └── v1/
│       ├── auth.py
│       ├── users.py
│       ├── projects.py
│       ├── chats.py
│       ├── chat_turns.py
│       ├── sources.py
│       ├── source_scans.py
│       ├── source_segments.py
│       ├── canvases.py
│       ├── canvas_elements.py
│       ├── canvas_connections.py
│       ├── candidate_elements.py
│       ├── project_memory.py
│       ├── briefs.py
│       ├── brief_versions.py
│       ├── tags.py
│       ├── companies.py
│       ├── activity.py
│       ├── allowance.py
│       └── health.py
│
├── core/
│   ├── config.py
│   ├── security.py
│   ├── enums.py
│   ├── errors.py
│   └── logging.py
│
├── db/
│   ├── session.py
│   └── base.py
│
├── models/
│   ├── user.py
│   ├── project.py
│   ├── chat.py
│   ├── chat_turn.py
│   ├── chat_turn_source.py
│   ├── source.py
│   ├── source_scan.py
│   ├── source_segment.py
│   ├── canvas.py
│   ├── canvas_element.py
│   ├── canvas_connection.py
│   ├── candidate_element.py
│   ├── project_memory.py
│   ├── brief.py
│   ├── brief_version.py
│   ├── brief_context_snapshot.py
│   ├── tag.py
│   ├── company.py
│   ├── research_activity.py
│   └── usage_event.py
│
├── schemas/
│   ├── auth.py
│   ├── user.py
│   ├── project.py
│   ├── chat.py
│   ├── chat_turn.py
│   ├── source.py
│   ├── extension_source.py
│   ├── source_scan.py
│   ├── source_segment.py
│   ├── canvas.py
│   ├── canvas_element.py
│   ├── canvas_connection.py
│   ├── candidate_element.py
│   ├── project_memory.py
│   ├── brief.py
│   ├── brief_version.py
│   ├── tag.py
│   ├── company.py
│   ├── activity.py
│   ├── allowance.py
│   └── common.py
│
├── repositories/
│   ├── user_repository.py
│   ├── project_repository.py
│   ├── chat_repository.py
│   ├── chat_turn_repository.py
│   ├── chat_turn_source_repository.py
│   ├── source_repository.py
│   ├── source_scan_repository.py
│   ├── source_segment_repository.py
│   ├── canvas_repository.py
│   ├── canvas_element_repository.py
│   ├── canvas_connection_repository.py
│   ├── candidate_element_repository.py
│   ├── project_memory_repository.py
│   ├── brief_repository.py
│   ├── brief_version_repository.py
│   ├── brief_context_snapshot_repository.py
│   ├── tag_repository.py
│   ├── company_repository.py
│   ├── activity_repository.py
│   └── usage_repository.py
│
├── services/
│   ├── auth_service.py
│   ├── project_service.py
│   ├── chat_service.py
│   ├── chat_turn_service.py
│   ├── input_detection_service.py
│   ├── chat_turn_orchestrator.py
│   ├── chat_prompt_builder.py
│   ├── chat_validation_service.py
│   ├── source_service.py
│   ├── source_extraction_service.py
│   ├── browser_extension_source_service.py
│   ├── context_retrieval_service.py
│   ├── source_scan_service.py
│   ├── source_segmentation_service.py
│   ├── research_allowance_service.py
│   ├── canvas_service.py
│   ├── canvas_element_service.py
│   ├── canvas_connection_service.py
│   ├── candidate_extraction_service.py
│   ├── project_memory_service.py
│   ├── brief_version_service.py
│   ├── brief_context_service.py
│   ├── brief_prompt_builder.py
│   ├── brief_validation_service.py
│   ├── activity_service.py
│   └── usage_tracking_service.py
│
├── clients/
│   ├── ai_provider_client.py
│   ├── anthropic_client.py
│   ├── article_extraction_client.py
│   ├── transcript_client.py
│   ├── pdf_extraction_client.py
│   ├── company_data_client.py
│   ├── market_news_client.py
│   └── object_storage_client.py
│
└── main.py
```

---

# 8. Core Services

## `InputDetectionService`

Responsibilities:

```text
- Detect URLs in user message
- Classify source type: article, YouTube, PDF, filing, unknown
- Detect intent: general ask, source analysis, brief generation, Canvas action, comparison
- Return routing decision to ChatTurnService
```

## `ProjectService`

Responsibilities:

```text
- Create/update/archive/delete projects
- Ensure Catchall project exists
- Ensure default Canvas exists for project
- Ensure ProjectMemory row exists for project
- Reject user-created Catchall
- Enforce Catchall immutability
- Later: project accumulation detection
```

## `ChatService`

Responsibilities:

```text
- Create/list/update/delete chats
- Enforce project ownership
- Archive/unarchive chats
- Update last_turn_at
```

## `ChatTurnService`

Responsibilities:

```text
- Validate chat state and source refs
- Use InputDetectionService
- Create/reuse sources for detected URLs
- Create user + assistant turn pair
- Attach sources
- Schedule background generation
- Return assistant turn for polling
```

## `ChatTurnOrchestrator`

Responsibilities:

```text
- Run assistant generation in background
- Open fresh DB session
- Lock queued assistant turn
- Build prompt based on route
- Call AI provider
- Validate response
- Persist response and usage
- Trigger candidate extraction as best effort
- Mark orphaned turns failed on startup sweep
```

## `ChatPromptBuilder`

Responsibilities:

```text
- Build prompt from route, project, chat history, current message, sources, Memory, and selected Canvas context
- Cap prompt size
- Truncate oldest history first
- Trim source snippets
- Add educational/not-advice rules
- Avoid fabricated source claims
```

## `CanvasService`

Responsibilities:

```text
- Create/get default project Canvas
- Persist viewport state if needed
- Enforce project ownership
```

## `CanvasElementService`

Responsibilities:

```text
- Create manual text/image/node/group elements
- Promote from chat turns
- Promote from sources
- Promote candidate elements
- Edit/move/resize/archive/delete elements
- Preserve provenance
```

## `CanvasConnectionService`

Responsibilities:

```text
- Create/update/delete connections between Canvas elements
- Validate both elements belong to same Canvas
- Support simple relationship types
```

## `CandidateExtractionService`

Responsibilities:

```text
- Ask AI provider for candidate Canvas elements
- Validate candidate element types/content
- Persist PENDING candidates
- Fail safely without breaking assistant turn
```

## `ProjectMemoryService`

Responsibilities:

```text
- Get/update visible project memory
- Summarize entities/themes/open questions
- Refresh memory from recent project activity when requested
- Avoid hidden uncontrolled memory behavior
```

## `BriefContextService`

Responsibilities:

```text
- Build explicit context snapshots for brief generation
- Support current thread, selected sources, project memory, selected Canvas elements, Canvas clusters, and full project context
- Store exact snapshot_json used for generation
```

## `BriefVersionService`

Responsibilities:

```text
- Create brief series
- Create BriefContextSnapshot from selected context
- Generate BriefVersion from snapshot
- Compare with previous version when requested
- Persist sections and summary_of_changes
- Update current_version_id
```

## `SourceService`

Responsibilities:

```text
- Create URL, YouTube, PDF, image, filing, and browser-extension sources
- Normalize URLs and metadata
- Track access method and status
- Coordinate extraction services
- Decide whether source supports source analysis or context analysis
```

## `SourceScanService`

Responsibilities:

```text
- Run cheap pre-analysis scans
- Detect length, entities, topics, complexity
- Estimate allowance impact
- Recommend research mode/completion strategy
- Trigger segmentation when needed
```

## `UsageTrackingService`

Responsibilities:

```text
- Persist token/cost events for chat turns, candidates, scans, memory refreshes, and brief versions
- Track cache read/write tokens when provider supports it
```

---

# 9. Data Flow: Unified Ask

```text
Frontend AgentComposer
   ↓ POST /chats/{chatId}/turns
FastAPI chat_turns route
   ↓
ChatTurnService
   ↓
InputDetectionService
   ↓ create/reuse sources if needed
   ↓ validate chat + source ownership
   ↓ create user turn + queued assistant turn
   ↓ attach sources
   ↓ schedule background task
Return assistantTurnId + detectedInputType + detectedIntentType
```

Background:

```text
Background task
   ↓ fresh DB session
ChatTurnOrchestrator
   ↓ ChatPromptBuilder
AiProviderClient
   ↓ ChatValidationService
ChatTurnRepository
   ↓ UsageTrackingService
   ↓ CandidateExtractionService best effort
```

---

# 10. Data Flow: Source Attachment

```text
User pastes URL in Ask box
   ↓
InputDetectionService detects source
   ↓
SourceService creates Source
   ↓ extraction / metadata fallback
   ↓ source attaches to ChatTurn
```

Manual SourcePicker flow remains available:

```text
Frontend SourcePicker
   ↓ POST /sources or GET /sources
SourceService
   ↓ extraction / metadata fallback
SourceRepository
   ↓ source appears attachable when FULL_TEXT_EXTRACTED or METADATA_ONLY
```

---

# 11. Data Flow: Candidate Elements

```text
Assistant turn completed
   ↓
CandidateExtractionService
   ↓ AiProviderClient.extract_candidates
   ↓ validate candidates
   ↓ persist candidate_elements(PENDING)
Frontend loads candidates
   ↓ user promotes or dismisses
CanvasElementService creates CanvasElement on promote
```

Candidate extraction must be non-critical:

```text
AI reply success + candidate extraction failure = reply still succeeds.
```

---

# 12. Data Flow: Freeform Canvas

```text
Frontend Canvas
   ↓ GET /projects/{projectId}/canvas
CanvasService
   ↓ returns default Canvas
```

Elements:

```text
Frontend Canvas
   ↓ GET /canvases/{canvasId}/elements
CanvasElementService
   ↓ CanvasElementRepository
```

Manual element:

```text
User adds text/image/node
   ↓ POST /canvases/{canvasId}/elements
CanvasElementService
   ↓ persist element with x/y/width/height
```

Move/resize:

```text
User drags/resizes element
   ↓ PATCH /canvas-elements/{elementId}
CanvasElementService
   ↓ persist x/y/width/height/zIndex
```

Connection:

```text
User draws connector
   ↓ POST /canvases/{canvasId}/connections
CanvasConnectionService
   ↓ validate same Canvas
   ↓ persist connection
```

---

# 13. Data Flow: Project Memory

```text
Frontend Memory tab
   ↓ GET /projects/{projectId}/memory
ProjectMemoryService
   ↓ ProjectMemoryRepository
```

Manual update:

```text
User edits memory
   ↓ PATCH /projects/{projectId}/memory
ProjectMemoryService
   ↓ persist visible memory
```

AI refresh:

```text
User clicks Refresh Memory
   ↓ POST /projects/{projectId}/memory/refresh
ProjectMemoryService
   ↓ load recent activity / high-signal turns / sources / selected Canvas elements
   ↓ AiProviderClient
   ↓ validate and persist memory update
```

---

# 14. Data Flow: Brief Version Generation

```text
Frontend GenerateBriefDialog
   ↓ user selects context:
      current thread / selected sources / selected Canvas / project memory / full project
   ↓ POST /briefs/{briefId}/versions
BriefVersionService
   ↓ BriefContextService creates BriefContextSnapshot
   ↓ BriefPromptBuilder
   ↓ AiProviderClient
   ↓ BriefValidationService
   ↓ persist BriefVersion
   ↓ update Brief.current_version_id
   ↓ UsageTrackingService + ActivityService
```

Important:

```text
Do not force every brief through Canvas.
Do not feed the entire raw project history by default.
Use explicit selected context snapshots.
```

---

# 15. Prompt Caching / AI Provider Strategy

The AI provider client should expose:

```python
class AiProviderClient(Protocol):
    async def generate_chat_reply(self, prompt: ChatPrompt) -> ChatReply: ...
    async def extract_candidates(self, *, user_message: str, assistant_reply: str, attached_sources: list[Source]) -> list[CandidateExtraction]: ...
    async def generate_brief_version(self, prompt: BriefPrompt) -> BriefReply: ...
    async def refresh_project_memory(self, prompt: MemoryPrompt) -> MemoryReply: ...
```

Provider selection:

```text
AI_PROVIDER=mock       → MockAiProviderClient
AI_PROVIDER=anthropic  → AnthropicClient if API key exists, else mock + warning
```

Keep the real model configurable. Do not hardcode a specific provider model name into business logic.

Prompt caching should be considered for repeated turns inside the same chat:

```text
Stable prefix:
- system role
- compliance rules
- output schema/tool schema
- style guide

Variable suffix:
- project context summary
- recent turns
- current user message
- attached sources
- selected Canvas context if relevant
```

---

# 16. Validation and Safety

## Chat Validation

Validate:

```text
- content_markdown non-empty
- markdown sanitized
- source markers reference actual attached sources
- no personalized investment advice phrases
- no fabricated source claims
- if source metadata-only, response says full source text was unavailable
```

## Candidate Validation

Validate:

```text
- allowed CanvasElementType
- non-empty title/content where applicable
- no unsupported source-specific claims
- no personalized advice
```

## Canvas Validation

Validate:

```text
- element belongs to user/project/canvas
- image/file references are owned by user
- connector endpoints belong to same Canvas
- element dimensions/coordinates are sane
- source quotes are short and source-linked
```

## Memory Validation

Validate:

```text
- memory is visible and user-editable
- no unsupported claims from inaccessible sources
- no personalized investment advice
- memory refresh cites or links back to project artifacts where possible
```

## Brief Validation

Validate:

```text
- required sections exist
- disclaimer exists
- output generated from BriefContextSnapshot
- generated-from note exists
- no fabricated source claims
- no personalized investment recommendation
- what-changed summary present for v2+ when requested
```

Repair once. On second failure, mark entity failed and return a safe message.

---

# 17. Frontend Implementation Slices

## PR #12: Workspace Shell

Build:

```text
WorkspaceShell
ProjectSidebar
CenterCanvasStub
AgentPanelStub
Canvas/Sources/Memory tabs
/workspace routes
```

## PR #13: Unified Agent Panel

Build:

```text
One Ask composer
Turn list / answer cards
URL paste support
Detected source chips
Assistant polling
Add-to-Canvas action placeholders
```

## PR #14: Freeform Canvas MVP

Build:

```text
Canvas viewport
CanvasElement rendering
Text element creation
Image element creation
Move/resize/edit/delete
Basic selection
```

## PR #15: Canvas Connections + Mind Map Basics

Build:

```text
Mind-map node element
Connector line creation
Connection labels
Group/frame element
```

## PR #16: Sources Tab

Build:

```text
Project source list
Extraction status
Source detail drawer
Linked chat/canvas counts
Add quote/note to Canvas
```

## PR #17: Memory Tab

Build:

```text
Project memory display
Entities/themes/open questions
Manual edit
AI refresh placeholder
```

## PR #18: Brief View

Build:

```text
Brief series creation
Generate from selected context
Version history
Context-used summary
Compare versions
```

---

# 18. Backend Implementation Slices

## PR #7: Projects

```text
projects table
ProjectKind enum
auto Catchall
auto default Canvas
auto ProjectMemory row
project endpoints
```

## PR #8: Chats

```text
chats table
ChatStatus enum
chat endpoints
```

## PR #9: Unified Ask + Chat Turns

```text
chat_turns
chat_turn_sources
InputDetectionService
send endpoint
mock provider
background orchestrator
polling endpoints
orphan sweep
```

## PR #10: Sources

```text
sources
source extraction status
article / YouTube / PDF routes
metadata-only fallback
browser-extension source route
```

## PR #11: Freeform Canvas

```text
canvases
canvas_elements
manual create
promote from turn/source
edit/move/resize/archive/delete
```

## PR #12: Canvas Connections

```text
canvas_connections
mind-map node support
relationship labels
same-canvas validation
```

## PR #13: Candidate Elements

```text
candidate_elements
AI extraction
promote/dismiss
```

## PR #14: Project Memory

```text
project_memories
get/update
AI refresh job optional
```

## PR #15: Real LLM

```text
Anthropic or configured provider client
structured outputs
tighter validation
cache token tracking
```

## Next Batch: Brief Versions

```text
briefs
brief_context_snapshots
brief_versions
generate from selected context
what-changed comparison
```

---

# 19. Pre-flight Cleanup Guidance

Before applying the new PR sequence, check for leftovers from abandoned earlier plans.

Recommended approach:

```text
1. Create a fresh branch.
2. Run tests before cleanup.
3. Search imports/usages before deleting files.
4. Remove abandoned files only if they are not referenced.
5. Remove matching abandoned migrations/tests carefully.
6. Run tests again.
7. Confirm alembic heads has exactly one head.
```

Do not blindly delete files from the previous plan if they were already completed and referenced by current source pipelines.

Load-bearing pieces to preserve:

```text
sources
source_scans
source_segments
source_fetch_policies
source_fetch_log
EDGAR client
enrichment service
source extraction / validation services
```

Things to rename or replace from the previous Canvas-first plan:

```text
CanvasBlock → CanvasElement
CanvasSnapshot → BriefContextSnapshot
canvas_blocks endpoints → canvas_elements endpoints
Brief from Canvas only → Brief from selected context
URL Mode / YouTube Mode as visible modes → one Ask box with internal routing
```

---

# 20. Key Architecture Concerns

## 20.1 One Ask Box vs Internal Modes

The user should see one Ask box. The backend can route internally.

Recommendation:

```text
Do not expose separate hard modes for Analyze Video / Analyze News / Ask.
Use source chips and detected context UI after input is parsed.
```

## 20.2 Freeform Canvas Can Become Messy

Canvas needs freedom plus lightweight helper actions.

Recommendation:

```text
Support group, connect, summarize selected area, and find contradictions.
Do not enforce a report outline.
```

## 20.3 Canvas Is Optional Brief Context

If the user built a useful Canvas, it should be usable for a brief. But if they want a quick source brief from a thread, they should not need Canvas first.

Recommendation:

```text
Generate briefs from explicit selected context snapshots.
```

## 20.4 Candidate Extraction Should Not Block Replies

The assistant reply is the primary user-visible result. Candidate extraction is enhancement.

Recommendation:

```text
Complete and show assistant turn first.
Then extract candidates best-effort.
```

## 20.5 Avoid Recreating `ResearchItem` Ambiguity

Do not rebuild a universal `ResearchItem` abstraction unless search/log views require it. The new architecture has clearer nouns.

## 20.6 Do Not Overbuild Miro

Canvas needs editable research thinking, not a full whiteboard startup inside your startup.

MVP Canvas:

```text
text
AI block
image
mind-map node
connector
group/frame
move/resize/edit/delete
provenance
```

That is enough for v0.3. No multiplayer, comments, complex vector tooling, backlinks, embedded spreadsheets, or block-level agents yet. Please let the MVP breathe.

---

# 21. MVP Success Definition

v0.3 succeeds if a user can say:

```text
I pasted sources and asked questions naturally, used the Canvas to visually build my understanding, tracked important sources and memory, and generated a useful brief when I needed one.
```

That is the wedge.
