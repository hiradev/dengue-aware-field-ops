"""
main.py — FastAPI application for the Dengue-Aware Field Response demo app.

This is a SEPARATE, independently-implemented demonstration app. It does not
import from, or depend on, the coursework notebook — the notebook remains
fully self-contained and gradeable on its own. This app exists to give the
project a working, browsable interface beyond the notebook and the static
dengue_app.html page.

Run: uvicorn app.main:app --reload --port 8000
Docs: http://localhost:8000/docs
"""
import logging
import os
from functools import lru_cache
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import dengue_data, expert_system, graph_data, heuristics, search
from .models import (
    DengueSummary, EdgeOut, GraphOut, NodeOut, RouteComparison,
    RouteResult, TraceStep, TriageRequest, TriageResponse,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title="Dengue-Aware Field Response API",
    description="Search-based routing + rule-based triage for Sri Lankan dengue field response.",
    version="1.0.0",
)

DEFAULT_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
extra_origins = [o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=DEFAULT_ORIGINS + extra_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@lru_cache(maxsize=1)
def get_graph() -> search.Graph:
    return search.Graph(graph_data.get_nodes(), graph_data.get_edges())


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/graph", response_model=GraphOut)
def get_graph_data():
    nodes = graph_data.get_nodes()
    districts = graph_data.get_node_district()
    node_list = [
        NodeOut(name=n, lat=lat, lon=lon, type=t, district=districts.get(n))
        for n, (lat, lon, t) in nodes.items()
    ]
    edge_list = [EdgeOut(a=a, b=b, km=km) for a, b, km in graph_data.get_edges()]
    return GraphOut(nodes=node_list, edges=edge_list)


@app.get("/api/route", response_model=RouteResult)
def route(
    start: str = Query(..., description="Start node (case cluster town)"),
    goal: str = Query(..., description="Goal node (referral hospital)"),
    algorithm: str = Query("astar", pattern="^(bfs|ucs|astar)$"),
):
    g = get_graph()
    if start not in g.nodes or goal not in g.nodes:
        raise HTTPException(404, "Unknown start or goal node")

    if algorithm == "bfs":
        result = search.breadth_first_search(g, start, goal)
    elif algorithm == "ucs":
        result = search.uniform_cost_search(g, start, goal)
    else:
        h = heuristics.make_straight_line_heuristic(g)
        result = search.a_star_search(g, start, goal, h, label="A*")

    return RouteResult(**result.as_dict())


@app.get("/api/compare", response_model=RouteComparison)
def compare(
    start: str = Query(...),
    goal: str = Query(...),
):
    """Run all three algorithms on the same start/goal pair — Comparison A, live."""
    g = get_graph()
    if start not in g.nodes or goal not in g.nodes:
        raise HTTPException(404, "Unknown start or goal node")

    h = heuristics.make_straight_line_heuristic(g)
    results = [
        search.breadth_first_search(g, start, goal),
        search.uniform_cost_search(g, start, goal),
        search.a_star_search(g, start, goal, h, label="A*"),
    ]
    return RouteComparison(
        start=start, goal=goal,
        results=[RouteResult(**r.as_dict()) for r in results],
    )


@app.get("/api/nodes/towns", response_model=List[str])
def list_towns():
    return graph_data.towns()


@app.get("/api/nodes/hospitals", response_model=List[str])
def list_hospitals():
    return graph_data.hospitals()


@app.post("/api/triage", response_model=TriageResponse)
def triage(req: TriageRequest):
    if req.strategy not in expert_system.CONFLICT_STRATEGIES:
        raise HTTPException(400, f"Unknown strategy: {req.strategy}")
    facts = {s: 1.0 for s in req.symptoms}
    result = expert_system.forward_chain(facts, strategy=req.strategy)
    return TriageResponse(
        recommendation=result.recommendation,
        certainty=result.certainty,
        conflict_strategy=result.conflict_strategy,
        iterations=result.iterations,
        trace=[TraceStep(
            rule_id=f.rule_id, conditions_met=f.conditions_met,
            conclusion=f.conclusion, cf=f.cf, rationale=f.rationale,
            iteration=f.iteration,
        ) for f in result.trace],
    )


@app.get("/api/symptoms", response_model=List[str])
def list_symptoms():
    return expert_system.OBSERVABLE_FEATURES


@app.get("/api/dengue-summary", response_model=DengueSummary)
def dengue_summary(recent_weeks: int = 12):
    df, mode = dengue_data.load_weekly_data()
    share = dengue_data.district_share(df, dengue_data.OUR_GRAPH_DISTRICTS)
    totals = dengue_data.recent_district_totals(df, dengue_data.OUR_GRAPH_DISTRICTS, n_weeks=recent_weeks)

    node_district = graph_data.get_node_district()
    town_district = {t: node_district[t] for t in graph_data.towns()}
    weights = dengue_data.cluster_weights(town_district, totals)

    top_cluster = max(weights, key=weights.get) if weights else ""
    return DengueSummary(
        mode=mode,
        coverage_start=str(df["start_date"].min().date()),
        coverage_end=str(df["start_date"].max().date()),
        n_districts=int(df["district"].nunique()),
        colombo_gampaha_share_recent_pct=round(float(share.tail(recent_weeks).mean()), 1),
        colombo_gampaha_share_full_history_pct=round(float(share.mean()), 1),
        recent_district_totals={k: int(v) for k, v in totals.items()},
        top_priority_cluster=top_cluster,
        top_priority_district=town_district.get(top_cluster, ""),
        top_priority_weight=round(weights.get(top_cluster, 0.0), 1),
        all_cluster_weights={k: round(v, 1) for k, v in weights.items()},
    )
