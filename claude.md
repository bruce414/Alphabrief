# CLAUDE.md

## Project
AlphaBrief: AI-powered finance research app. Turns URLs, PDFs, YouTube videos, raw text, or finance questions into structured, source-grounded research briefs.
Current stage: **v0.3 first milestone** (v0.1/v0.2 are internal slices inside v0.3, not separate milestones).

---

## Tech Stack
**Backend:** Python, FastAPI, PostgreSQL, SQLAlchemy, Alembic, Pydantic, Docker Compose, pytest
**Frontend:** React, TypeScript, Vite, Tailwind CSS, shadcn/ui
**UI style:** minimal, clean, professional, modern SaaS — not playful or cluttered

Do not use: Java, Spring Boot, Celery/Redis (unless asked).

---

## Development Areas (v0.3)
1. **Foundation** — setup, DB, core models, API structure, tests
2. **Source/Brief Flow** — user input, source ingestion, URL/PDF/text/YouTube, brief generation
3. **Agentic/Deep Analysis** — research planning, entity extraction, multi-source synthesis, confidence/risk notes
4. **Pre-Launch Validation** — tests, bug fixes, security, cost controls, deployment

---

## Core Product Flow
Build simple first:
1. User creates brief request + provides source(s) or finance question
2. Backend stores brief and sources
3. System extracts/normalizes source text
4. System generates structured brief
5. User views brief with source references

Do not build the full agentic workflow early.

---

## Architecture

```text
backend/
├── app/
│   ├── api/v1/       ← thin routers only
│   ├── core/
│   ├── db/
│   ├── models/       ← persistence only
│   ├── schemas/      ← Pydantic request/response
│   ├── services/     ← business logic
│   ├── repositories/
│   └── jobs/
├── alembic/
├── tests/
└── docker-compose.yml
```

**DB:** PostgreSQL + Alembic migrations.
**Core models:** User, Brief, BriefSource, BriefJob (statuses: PENDING, PROCESSING, COMPLETED, FAILED).
Don't add tables before the flow needs them.

---

## AI Generation Implementation

For v0.3, keep AI brief generation simple and backend-driven.

**Rules:**
- AI generation logic lives in `backend/app/services/brief_generation_service.py`
- Prompt construction lives in `backend/app/services/prompt_builder.py` as a standalone module
- API routes call service methods — never call the LLM directly from a route
- Generation runs synchronously for early v0.3
- Store generated output on the `Brief` model or a related result table per the existing schema
- Use environment variables for all LLM API keys and model names — never hardcode them
- If no LLM provider is configured, use a mock generator with clear `# TODO: replace with real LLM call` comments

**Simple flow (build this first):**
```txt
POST /api/v1/briefs/{brief_id}/generate
→ route validates request
→ route calls BriefGenerationService.generate_brief(brief_id)
→ service loads Brief + BriefSource records
→ service calls PromptBuilder.build_brief_prompt(sources, brief_context)
→ service calls LLM client (or mock generator)
→ service saves result and updates status to COMPLETED or FAILED
→ route returns updated brief
```

**Future async flow — do not implement unless explicitly asked:**
```txt
POST /api/v1/briefs/{brief_id}/generate
→ create BriefJob → background worker → frontend polls → user views brief
```

---

## AI Pipeline
**Simple (build first):**
user input → normalize source → extract text → generate brief → save → show

**Future (deep):**
user query → classify intent → identify entities → search trusted sources → compare claims → synthesize → cite → show confidence/risk notes

Do not implement multi-agent systems unless explicitly requested. For early v0.3, simple background processing is acceptable (no Celery/Redis yet).

---

## Source & Compliance Rules
- Prefer high-trust financial/news/company sources
- Distinguish facts, analysis, assumptions, uncertainty, and risks
- Do not present outputs as guaranteed truth
- No direct financial advice ("buy this stock", "guaranteed return") — use educational/research framing

---

## Cost Control
- Store generated outputs; avoid unnecessary regeneration
- Cap source length and limit deep research usage
- Keep prompts compact
- No unlimited deep research access by default

---


## Coding Rules
1. Make small, focused changes
2. Don't rewrite unrelated files or silently change architecture
3. Don't introduce new infrastructure unless asked
4. Add/update tests for meaningful logic
5. Run tests when possible
6. Explain changed files after implementation
7. State assumptions clearly
8. Don't mix unrelated features in one task

---

## Common Commands

```text
pytest
alembic upgrade head
uvicorn app.main:app --reload
docker compose up -d && docker compose ps
```

Inspect the repo before running — don't invent commands.

---

## Never Do Unless Asked
- Switch to Java/Spring Boot
- Add Celery/Redis early
- Build full auth before core brief flow works
- Build billing before product flow works
- Redesign UI away from clean professional style
- Create multi-agent framework early
- Rewrite whole repo for a small task
- Hardcode secrets or API keys

---

## v0.3 First Milestone — Active Scope (2026-05-10)

**Focus:** workspace shell, freeform Canvas (absolute-positioned, not Miro),
agent chat panel, project sidebar, project memory, smart input detection.

**Source of truth:** docs/v0.3/engineering/ (AI_PIPELINE.md, API_SPEC.md,
DATA_MODEL.md, TECHNICAL_ARCHITECTURE.md).

**DEFERRED — do not implement, do not refactor:**
- Brief generation and brief versions
- File / PDF upload
- Chrome extension client
- /briefs* endpoints (keep existing legacy code as-is)
- brief_versions, brief_sources, canvas_snapshots tables (legacy, dormant)

**Legacy files — do not touch:**
- backend/app/api/v1/endpoints/briefs.py
- backend/app/services/brief_service.py
- backend/app/models/brief.py
- backend/app/models/brief_version.py
- backend/app/models/brief_source.py
- backend/app/models/canvas_snapshot.py