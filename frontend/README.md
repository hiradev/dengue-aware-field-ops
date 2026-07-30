# Frontend - React + TypeScript + Vite

React 19, TypeScript, Vite, Tailwind CSS v4, Leaflet (via react-leaflet),
Recharts, React Router v7.

## Setup

Requires Node.js 20+ (Node 24 LTS recommended, per the original stack).

```powershell
cd frontend
npm install
```

## Run

Make sure the backend is running first (`http://localhost:8000`), then:

```powershell
npm run dev
```

Open http://localhost:5173

Vite proxies all `/api/*` requests to the backend (see `vite.config.ts`), so
no CORS configuration is needed beyond what's already in `backend/app/main.py`.

## What's on the dashboard

- **Map** - the real Colombo/Gampaha graph, animates the selected search
  algorithm's path and (implicitly, via node styling) which nodes were
  expanded.
- **Comparison chart** - Comparison A (nodes expanded, BFS vs UCS vs A\*) for
  whatever start/goal pair is currently selected, computed live by the API.
- **Dengue summary card** - real surveillance data pulled from the backend;
  shows whether it loaded in `live` or `cache` mode, and the current
  highest-priority case cluster.
- **Triage panel** - toggle symptoms, get a recommendation with the full
  rule-firing explanation trace.
