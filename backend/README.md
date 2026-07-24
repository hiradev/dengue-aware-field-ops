# Backend — FastAPI

Independently-implemented API layer. Does **not** import the coursework
notebook — the algorithms (BFS/UCS/A*, forward-chaining expert system) are
re-implemented here from scratch, matching the notebook's verified behaviour,
so the notebook stays fully self-contained and gradeable on its own.

## Setup

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## (Optional) populate the offline data cache

```powershell
python scripts\refresh_cache.py
```

Not required to run the API — `/api/dengue-summary` tries a live fetch first
on every call — but running this once means there's a tested local fallback
if you're ever offline.

## Run

```powershell
uvicorn app.main:app --reload --port 8000
```

Interactive API docs: http://localhost:8000/docs

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | liveness check |
| GET | `/api/graph` | full node/edge graph |
| GET | `/api/nodes/towns`, `/api/nodes/hospitals` | node name lists |
| GET | `/api/route?start=&goal=&algorithm=bfs\|ucs\|astar` | run one search algorithm |
| GET | `/api/compare?start=&goal=` | run all three algorithms on the same pair (Comparison A) |
| GET | `/api/symptoms` | the 16-feature triage vocabulary |
| POST | `/api/triage` | `{symptoms: string[], strategy: string}` → recommendation + explanation trace |
| GET | `/api/dengue-summary?recent_weeks=12` | real live surveillance data + priority cluster |
