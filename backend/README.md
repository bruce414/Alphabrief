# Alphabrief backend

FastAPI service with PostgreSQL, SQLAlchemy 2.x (async), asyncpg, and Alembic.

**Not implemented yet:** AI brief generation, authentication, payments, usage limits, and subscriptions.

---

## Local development checklist

Run everything from the `backend` directory unless noted.

### 1. Create virtual environment

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -e .
```

(`pip install -r requirements.txt` installs libraries only; editable install registers the `app` package.)

### 3. Copy environment file

```bash
cp .env.example .env
```

Edit `.env` if your Postgres URL differs.

### 4. Start PostgreSQL (Docker Compose)

```bash
docker compose up -d
```

### 5. Run Alembic migrations

```bash
alembic upgrade head
```

### 6. Start the FastAPI app

```bash
uvicorn app.main:app --reload --port 8000
```

### 7. Open Swagger docs

In a browser: [http://localhost:8000/docs](http://localhost:8000/docs)

### 8. Test creating a brief

```bash
curl -s -X POST http://localhost:8000/api/v1/briefs \
  -H "Content-Type: application/json" \
  -d '{"source_url": "https://example.com/article"}'
```

### Tests

Requires Postgres reachable at `DATABASE_URL` (use `postgresql+asyncpg://…` as in `.env.example`). Pytest sets `ENVIRONMENT=test` and rebuilds the ORM schema once per session (point at a disposable database if you share a cluster).

```bash
pytest
```

---

## HTTP API (current)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness-style health (also exposed without `/api/v1` prefix) |
| `GET` | `/api/v1/health` | Health (`{"status":"ok"}`) |
| `GET` | `/api/v1/health/db` | Database connectivity (`SELECT 1`) |
| `POST` | `/api/v1/briefs` | Create brief + initial URL source (`BriefCreate` → `BriefResponse`, `201`) |
| `GET` | `/api/v1/briefs` | List briefs (`limit` default `20`, max `100`; `offset` default `0`; newest first) |
| `GET` | `/api/v1/briefs/{brief_id}` | Fetch one brief with `sources` |

---

## Database migrations

Generate and apply revisions (Postgres must be running):

```bash
alembic revision --autogenerate -m "message"
alembic upgrade head
```
