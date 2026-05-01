# Backend (FastAPI)

## PostgreSQL (local)

From the `backend` directory, start Postgres with Docker Compose:

```bash
docker compose up -d
```

This runs PostgreSQL 17 with credentials matching `.env.example`. Copy `.env.example` to `.env` and adjust if needed.

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Run (dev)

```bash
uvicorn app.main:app --reload --port 8000
```

Open Swagger docs at `http://localhost:8000/docs`.

Health check: `GET http://localhost:8000/api/v1/health`.

## Database migrations (Alembic)

Run from the `backend` directory with Postgres up (`docker compose up -d`) and `.env` configured:

```bash
alembic revision --autogenerate -m "message"
alembic upgrade head
```
