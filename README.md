# dengue-field-ops - demo application

A working, browsable demonstration of the Dengue-Aware Field Response System,
built as a stretch goal alongside the CW1 coursework notebook. Stack:
**FastAPI + Pydantic v2** backend, **React 19 + TypeScript + Vite + Tailwind v4
+ Leaflet + Recharts + React Router v7** frontend.

## ⚠️ Relationship to the coursework notebook

This app **independently re-implements** the search algorithms and the
rule-based expert system - it does not import the notebook, and the notebook
does not depend on this app. That separation is deliberate: the graded
notebook must remain self-contained and runnable with zero external
dependencies beyond what's in its own setup cell, regardless of what happens
here.

If you change an algorithm's behaviour in one place (e.g. fixing a bug), the
same fix needs to be made in the other. They are currently in sync as of the
notebook's `v1.0-frozen` tag.

## Quick start

**Terminal 1 - backend:**
```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - frontend:**
```powershell
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**.

See `backend/README.md` and `frontend/README.md` for full detail on each half.

## Real data

The `/api/dengue-summary` endpoint pulls live weekly, district-level dengue
case data from the `denguedatahub` package (Talagala, 2024), with a cache
fallback. The dashboard's default case cluster is chosen from this real data,
not hardcoded.

**Note:** the coursework notebook (`Cw1_STUDENTID_Notebook.ipynb`) does
*not* use this data source - it's fully self-contained with a hand-estimated
road network and synthetic patient vignettes, by design, so it stays
gradeable with zero external dependencies. This app is a separate,
independent exploration of what real-data integration could look like; the
two are not the same artefact and should not be described as sharing a data
source.

## Priority reminder

CW1 submission is the priority. This app is explicitly a stretch goal - if
building it starts eating into report-writing or viva-prep time, stop and
come back to it after submission. The notebook alone already satisfies the
brief.
