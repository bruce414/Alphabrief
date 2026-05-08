# AlphaBrief v0.3 Technical Architecture

## Version

`v0.3 First Milestone — Projects → Canvas → Versioned Briefs`

## Status

This architecture reflects AlphaBrief's updated direction:

```text
Market learning + research workspace
Projects as top-level containers
Chats as focused explorations inside projects
Sources attached to chats
Canvas as the curated research artifact
Briefs as versioned snapshots generated from Canvas
Chrome Extension-ready source ingestion
Adaptive external-source research architecture
```

The earlier architecture treated `ResearchItem` as the central saved object. The new architecture makes `Project`, `Chat`, `CanvasBlock`, and `BriefVersion` the core product objects.

---

# 1. Product Goal

AlphaBrief v0.3 should prove this loop:

```text
Ask or submit source
→ explore inside a project chat
→ AI suggests useful Canvas candidates
→ user promotes/edits/reorders Canvas blocks
→ generate a structured brief version from the Canvas
→ continue researching
→ generate updated brief versions and see what changed
```

The Chrome extension strengthens source capture:

```text
Read article/video page
→ click AlphaBrief extension
→ create Source
→ attach Source to project chat
→ promote useful insights to Canvas
```

AlphaBrief is not trying to be only a one-click report generator. That road is crowded enough to need traffic lights.

---

# 2. Recommended Stack

## Frontend Web App

```text
React
TypeScript
Vite
TailwindCSS
shadcn/ui or similar component system
react-router v6
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

Do not start with distributed-worker theater until the simple version hurts.

---

# 3. High-Level Architecture

```text
React/Vite Workspace App
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
| Web App | Main research workspace: Projects, Chats, Sources, Canvas, Brief Versions |
| Chrome Extension | User-initiated page capture and source creation from current browser page |

## Web App Core Areas

| Area | Purpose |
|---|---|
| Project Sidebar | Top-level navigation; Catchall pinned; user projects below |
| Chat Pane | Focused exploration inside active project |
| Source Picker | Create/select sources and attach to chat messages |
| Canvas Pane | Curated research blocks with provenance and editing |
| Brief View | Versioned brief snapshots generated from Canvas |
| Activity / Timeline later | Show research progress and what changed |

---

# 5. Workspace UI Architecture

## 5.1 Layout

Recommended MVP layout:

```text
Left sidebar: Projects
Center pane: Chats / active conversation
Right pane: Canvas
```

The right Canvas pane should be collapsible.

## 5.2 Project Sidebar

Responsibilities:

```text
- Show Catchall pinned at top
- List user projects ordered by updated_at desc
- Create project inline
- Navigate to /workspace/projects/:id
```

## 5.3 Chat Pane

Responsibilities:

```text
- List chats in active project
- Create/select chat
- Show turns
- Send message
- Attach sources
- Poll assistant replies
- Render candidate review UI after assistant completion
```

## 5.4 Canvas Pane

Responsibilities:

```text
- Show active Canvas blocks ordered by position_index
- Manual block creation
- Edit/archive/delete blocks
- Promote assistant turn to Canvas
- Promote/dismiss candidate blocks
- Show provenance footer
```

## 5.5 Brief View

Responsibilities:

```text
- Create brief series
- Generate new version from Canvas
- Show version history
- Show what changed between versions
- Warn when Canvas changed since latest version
```

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
│       ├── canvas_blocks.py
│       ├── candidate_blocks.py
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
│   ├── canvas_block.py
│   ├── candidate_block.py
│   ├── brief.py
│   ├── brief_version.py
│   ├── canvas_snapshot.py
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
│   ├── canvas_block.py
│   ├── candidate_block.py
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
│   ├── canvas_block_repository.py
│   ├── candidate_block_repository.py
│   ├── brief_repository.py
│   ├── brief_version_repository.py
│   ├── canvas_snapshot_repository.py
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
│   ├── canvas_block_service.py
│   ├── candidate_extraction_service.py
│   ├── brief_version_service.py
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

## `ProjectService`

Responsibilities:

```text
- Create/update/archive/delete projects
- Ensure Catchall project exists
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
- Build prompt
- Call AI provider
- Validate response
- Persist response and usage
- Trigger candidate extraction as best effort
- Mark orphaned turns failed on startup sweep
```

## `ChatPromptBuilder`

Responsibilities:

```text
- Build prompt from project, chat history, current message, and sources
- Cap prompt size
- Truncate oldest history first
- Trim source snippets
- Add educational/not-advice rules
- Avoid fabricated source claims
```

## `CanvasBlockService`

Responsibilities:

```text
- Create manual blocks
- Promote from chat turns
- Promote from sources
- Edit/archive/delete blocks
- Maintain fractional ordering
- Rebalance positions when needed
- Preserve provenance
```

## `CandidateExtractionService`

Responsibilities:

```text
- Ask AI provider for candidate Canvas blocks
- Validate candidate block types/content
- Persist PENDING candidates
- Fail safely without breaking assistant turn
```

## `BriefVersionService`

Responsibilities:

```text
- Create brief series
- Create CanvasSnapshot from selected blocks
- Generate BriefVersion from CanvasSnapshot
- Compare with previous version
- Persist sections and summary_of_changes
- Update current_version_id
```

## `SourceService`

Responsibilities:

```text
- Create URL, YouTube, PDF, and browser-extension sources
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

## `SourceSegmentationService`

Responsibilities:

```text
- Segment transcripts, articles, PDFs, browser pages
- Store source_segments
- Preserve section metadata and relevance
```

## `ResearchAllowanceService`

Responsibilities:

```text
- Estimate allowance impact before generation
- Track actual impact after generation
- Use config-based threshold initially
- Add persistent allowance/cooldown later
```

## `UsageTrackingService`

Responsibilities:

```text
- Persist token/cost events for chat turns, candidates, scans, and brief versions
- Track cache read/write tokens when provider supports it
```

---

# 9. Data Flow: Project + Chat

```text
Frontend Workspace
   ↓ POST /projects or GET /projects
FastAPI projects route
   ↓
ProjectService
   ↓
ProjectRepository
   ↓
PostgreSQL
```

```text
Frontend ChatPane
   ↓ POST /projects/{projectId}/chats
FastAPI chats route
   ↓
ChatService
   ↓
ChatRepository
```

---

# 10. Data Flow: Send Chat Message

```text
Frontend MessageComposer
   ↓ POST /chats/{chatId}/turns
FastAPI chat_turns route
   ↓
ChatTurnService
   ↓ validate chat + source ownership
   ↓ create user turn + queued assistant turn
   ↓ attach sources
   ↓ schedule background task
Return assistantTurnId
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

# 11. Data Flow: Source Attachment

```text
Frontend SourcePicker
   ↓ POST /sources or GET /sources
SourceService
   ↓ extraction / metadata fallback
SourceRepository
   ↓ source appears attachable when FULL_TEXT_EXTRACTED or METADATA_ONLY
```

Then:

```text
MessageComposer attaches sourceIds
   ↓ POST /chats/{chatId}/turns
chat_turn_sources join records source linkage
```

---

# 12. Data Flow: Candidate Blocks

```text
Assistant turn completed
   ↓
CandidateExtractionService
   ↓ AiProviderClient.extract_candidates
   ↓ validate candidates
   ↓ persist candidate_blocks(PENDING)
Frontend polls/loads candidates
   ↓ user promotes or dismisses
CanvasBlockService creates CanvasBlock on promote
```

Candidate extraction must be non-critical:

```text
AI reply success + candidate extraction failure = reply still succeeds.
```

---

# 13. Data Flow: Canvas

```text
Frontend CanvasPane
   ↓ GET /projects/{projectId}/canvas-blocks
CanvasBlockService
   ↓ CanvasBlockRepository
```

Manual block:

```text
Frontend Add Block
   ↓ POST /projects/{projectId}/canvas-blocks
CanvasBlockService
   ↓ position calculation + ownership
   ↓ persist CanvasBlock(provenance=MANUAL)
```

Promote from turn:

```text
Frontend +Canvas on assistant turn
   ↓ user edits content/type/title
   ↓ POST /projects/{projectId}/canvas-blocks/from-turn
CanvasBlockService
   ↓ persist CanvasBlock(provenance=CHAT_TURN)
```

---

# 14. Data Flow: Brief Version Generation

```text
Frontend BriefView
   ↓ POST /projects/{projectId}/briefs if series does not exist
   ↓ POST /briefs/{briefId}/versions
BriefVersionService
   ↓ load selected CanvasBlocks
   ↓ create CanvasSnapshot
   ↓ BriefPromptBuilder
   ↓ AiProviderClient
   ↓ BriefValidationService
   ↓ persist BriefVersion
   ↓ update Brief.current_version_id
   ↓ UsageTrackingService + ActivityService
```

Important:

```text
Do not feed raw full chat transcripts into formal brief generation.
Use CanvasSnapshot as the formal input.
```

---

# 15. Prompt Caching / AI Provider Strategy

The AI provider client should expose:

```python
class AiProviderClient(Protocol):
    async def generate_chat_reply(self, prompt: ChatPrompt) -> ChatReply: ...
    async def extract_candidates(self, *, user_message: str, assistant_reply: str, attached_sources: list[Source]) -> list[CandidateExtraction]: ...
    async def generate_brief_version(self, prompt: BriefPrompt) -> BriefReply: ...
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
- project context summary later
- recent turns
- current user message
- attached sources
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
- allowed CanvasBlockType
- non-empty title/content
- no unsupported source-specific claims
- no personalized advice
```

## Brief Validation

Validate:

```text
- required sections exist
- disclaimer exists
- output generated from CanvasSnapshot
- no fabricated source claims
- no personalized investment recommendation
- source/provenance note present
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
ChatPaneStub
CanvasPaneStub
/workspace routes
```

## PR #13: Chat Pane

Build:

```text
Chat list
Turn list
Message composer
Source picker
Assistant polling
```

## PR #14: Canvas Pane

Build:

```text
Canvas block list
Candidate review banner
Manual promote-from-turn
Promote/dismiss candidates
Edit/archive/delete blocks
```

## Later: Brief View

Build:

```text
Brief series creation
Generate new version
Version history
Compare versions
Canvas changed warning
```

---

# 18. Backend Implementation Slices

## PR #7: Projects

```text
projects table
ProjectKind enum
auto Catchall
project endpoints
```

## PR #8: Chats

```text
chats table
ChatStatus enum
chat endpoints
```

## PR #9: Chat Turns

```text
chat_turns
chat_turn_sources
send endpoint
mock provider
background orchestrator
polling endpoints
orphan sweep
```

## PR #10: Canvas Blocks

```text
canvas_blocks
manual create
promote from turn/source
edit/reorder/archive/delete
```

## PR #11: Candidate Blocks

```text
candidate_blocks
AI extraction
promote/dismiss
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
canvas_snapshots
brief_versions
generate from Canvas
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

---

# 20. Key Architecture Concerns

## 20.1 Catchall vs Project Canvas

If Catchall has the same Canvas and Brief features as real projects, users may never feel the project difference.

Recommendation:

```text
Catchall = low-friction inbox.
Real projects = full Canvas + BriefVersion workflow.
```

A softer MVP can allow Catchall Canvas capture but should strongly prompt users to create a real project once multiple related chats/candidates appear.

## 20.2 Candidate Extraction Should Not Block Replies

The assistant reply is the primary user-visible result. Candidate extraction is enhancement.

Recommendation:

```text
Complete and show assistant turn first.
Then extract candidates best-effort.
```

## 20.3 Brief Generation Deferred But Data Model Ready

The provided PR sequence defers project-brief generation. That is reasonable, but the docs should keep `Brief`, `BriefVersion`, and `CanvasSnapshot` defined now so Cursor/Claude do not build a dead-end Canvas.

## 20.4 Avoid Recreating `ResearchItem` Ambiguity

Do not rebuild a universal `ResearchItem` abstraction unless search/log views require it. The new architecture has clearer nouns.

## 20.5 Do Not Overbuild Notion

Canvas needs editing and ordering, not a full Notion clone.

MVP Canvas:

```text
block type
content
title
provenance
ordering
edit/archive/delete
```

That is enough. No comments, backlinks, embeds, collaboration, or block-level AI agents yet. Save the product from becoming a cathedral of movable rectangles.

---

# 21. MVP Success Definition

v0.3 succeeds if a user can say:

```text
I asked several market questions, saved the useful parts into a Canvas, refined my thesis, and generated a better updated brief than I would get from a one-off AI report.
```

That is the wedge.
