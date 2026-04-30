# Backend (FastAPI)

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

Then hit `GET http://localhost:8000/api/health`.

