# Alphabrief v0.3 Environment Setup

## Version

`v0.3 MVP`

## Purpose

This document explains how to run Alphabrief locally.

This version assumes the following stack:

```text
Frontend: React + TypeScript + Vite
Backend: Python + FastAPI
Database: PostgreSQL
Migrations: Alembic
ORM: SQLAlchemy or SQLModel
```

---

## 1. Required Tools

Recommended local tools:

- Python 3.11 or later
- Node.js 20 or later
- npm or pnpm
- Docker
- Docker Compose
- PostgreSQL client
- Git

Optional but recommended:

- `uv` or Poetry for Python dependency management
- `psql` for database inspection
- Postman, Bruno, Insomnia, or Swagger UI for API testing

---

## 2. Project Structure

Recommended structure:

```text
alphabrief/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── repositories/
│   │   └── main.py
│   ├── alembic/
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── .env.example
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── .env.example
│   └── vite.config.ts
│
├── docs/
└── docker-compose.yml
```

---

## 3. Backend Setup

Navigate to backend:

```bash
cd backend
```

Create local environment file:

```bash
cp .env.example .env
```

Example backend `.env`:

```text
APP_ENV=local
APP_NAME=Alphabrief
DEBUG=true

DATABASE_URL=postgresql+psycopg://alphabrief:alphabrief@localhost:5432/alphabrief

JWT_SECRET=replace_me_with_a_long_random_value
ACCESS_TOKEN_EXPIRE_MINUTES=60

AI_PROVIDER_API_KEY=replace_me
MARKET_DATA_API_KEY=replace_me
NEWS_API_KEY=replace_me

FRONTEND_BASE_URL=http://localhost:5173
BACKEND_BASE_URL=http://localhost:8000

CORS_ALLOWED_ORIGINS=http://localhost:5173
```

---

## 4. Python Virtual Environment

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

### macOS / Linux

```bash
source .venv/bin/activate
```

### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

If using `uv`:

```bash
uv sync
```

If using Poetry:

```bash
poetry install
```

---

## 5. Backend Dependencies

Recommended backend dependencies:

```text
fastapi
uvicorn[standard]
pydantic
pydantic-settings
sqlalchemy
psycopg[binary]
alembic
python-jose[cryptography]
passlib[bcrypt]
python-multipart
httpx
```

Optional later:

```text
celery
redis
arq
rq
pytest
pytest-asyncio
ruff
mypy
```

---

## 6. Database Setup

Recommended local database:

```text
PostgreSQL 16
```

Example root-level `docker-compose.yml`:

```yaml
services:
  postgres:
    image: postgres:16
    container_name: alphabrief-postgres
    environment:
      POSTGRES_DB: alphabrief
      POSTGRES_USER: alphabrief
      POSTGRES_PASSWORD: alphabrief
    ports:
      - "5432:5432"
    volumes:
      - alphabrief_postgres_data:/var/lib/postgresql/data

volumes:
  alphabrief_postgres_data:
```

Start PostgreSQL:

```bash
docker compose up -d
```

Check database container:

```bash
docker ps
```

Optional database connection test:

```bash
psql postgresql://alphabrief:alphabrief@localhost:5432/alphabrief
```

---

## 7. Database Migrations

Alphabrief should use Alembic for database migrations.

Run migrations:

```bash
alembic upgrade head
```

Create a new migration:

```bash
alembic revision --autogenerate -m "create users table"
```

Recommended migration order:

```text
001_create_users
002_create_plans
003_create_user_entitlements
004_create_promo_codes
005_create_promo_code_redemptions
006_create_sources
007_create_briefs
008_create_brief_generation_jobs
009_create_financial_entities
010_create_brief_entity_insights
011_create_external_context_items
012_create_user_usage_daily
013_create_indexes
```

---

## 8. Run Backend

Run FastAPI locally:

```bash
uvicorn app.main:app --reload --port 8000
```

Backend should run at:

```text
http://localhost:8000
```

OpenAPI docs should be available at:

```text
http://localhost:8000/docs
```

Alternative ReDoc documentation:

```text
http://localhost:8000/redoc
```

Health check endpoint recommendation:

```text
GET /api/v1/health
```

Expected response:

```json
{
  "status": "ok"
}
```

---

## 9. Frontend Setup

Navigate to frontend:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Or with pnpm:

```bash
pnpm install
```

Create frontend environment file:

```bash
cp .env.example .env.local
```

Example frontend `.env.local`:

```text
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

Run frontend:

```bash
npm run dev
```

Or with pnpm:

```bash
pnpm dev
```

Frontend should run at:

```text
http://localhost:5173
```

---

## 10. Environment Variables

### Backend

| Variable | Purpose |
|---|---|
| APP_ENV | local, staging, production |
| APP_NAME | Application name |
| DEBUG | Enables local debug mode |
| DATABASE_URL | PostgreSQL connection URL |
| JWT_SECRET | Secret used for token signing |
| ACCESS_TOKEN_EXPIRE_MINUTES | Access token lifetime |
| AI_PROVIDER_API_KEY | AI provider key |
| MARKET_DATA_API_KEY | Market/company data key |
| NEWS_API_KEY | News/search API key |
| FRONTEND_BASE_URL | Frontend origin |
| BACKEND_BASE_URL | Backend origin |
| CORS_ALLOWED_ORIGINS | Allowed frontend origins |

### Frontend

| Variable | Purpose |
|---|---|
| VITE_API_BASE_URL | Backend API base URL |

---

## 11. Local Development Flow

Recommended startup order:

```text
1. Start PostgreSQL with Docker Compose
2. Activate Python virtual environment
3. Run Alembic migrations
4. Run FastAPI backend
5. Run React/Vite frontend
6. Open frontend in browser
7. Test API through frontend or FastAPI docs
```

Commands:

```bash
docker compose up -d
cd backend
source .venv/bin/activate
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

In another terminal:

```bash
cd frontend
npm run dev
```

---

## 12. Common Issues

### Backend cannot connect to database

Check:

- Docker database is running
- Port `5432` is available
- `DATABASE_URL` matches Docker Compose credentials
- PostgreSQL container is healthy
- Alembic has been run

### Frontend cannot call backend

Check:

- `VITE_API_BASE_URL` is correct
- Backend is running on port `8000`
- CORS allows `http://localhost:5173`
- Browser console does not show CORS errors
- Auth token/session handling is configured correctly

### Alembic migration fails

Check:

- Database is running
- `DATABASE_URL` is loaded correctly
- Models are imported into Alembic environment
- The migration file does not conflict with current schema

### AI generation fails

Check:

- AI API key exists
- API key has enough credit/quota
- Request payload is not too long
- Provider is reachable
- AI output validation is not rejecting malformed responses

### Promo code redemption fails

Check:

- Promo code exists
- Promo code is active
- Promo code has not expired
- Promo code has remaining redemptions
- User has not already redeemed it
- Redemption logic runs inside a transaction

---

## 13. Seed Data

Optional v0.3 seed data:

- Test user
- Free plan
- Pro plan
- Sample promo code
- Sample article source
- Sample pasted text source
- Sample completed brief
- Sample financial entity

Recommended seed plans:

```text
FREE
PRO
ADMIN
```

Recommended test promo code:

```text
ALPHA-BETA-2026
```

---

## 14. Local Testing Checklist

Before pushing code:

- PostgreSQL starts successfully
- Backend starts successfully
- Frontend starts successfully
- Database migrations run successfully
- FastAPI docs load at `/docs`
- User can register/login
- User can create brief from pasted text
- User can view brief detail
- User can view brief history
- Invalid source errors are handled
- Usage limit behavior works
- Promo code redemption works
- Pro access is calculated from active entitlements
- Free users cannot access Pro-only context
- Frontend displays locked premium sections correctly

---

## 15. MVP Note

For v0.3, avoid mixing Java/Spring Boot and FastAPI unless there is a strong reason.

The recommended backend is a FastAPI monolith:

```text
FastAPI backend
PostgreSQL database
Alembic migrations
React/Vite frontend
```

If Alphabrief grows later, AI processing can be split into a separate worker or service.
