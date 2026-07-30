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

from . import census_data, dengue_data, expert_system, graph_data, heuristics, rainfall_data, search, wer_scraper
from .models import (
    DengueSummary, DistrictIncidence, EdgeOut, GraphOut, NodeOut, RainfallContext,
    RouteComparison, RouteResult, TraceStep, TriageRequest, TriageResponse, WERSnapshot,
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


@app.get("/api/district-incidence", response_model=List[DistrictIncidence])
def district_incidence(recent_weeks: int = 12):
    """
    Population-normalised dengue burden (cases per 100,000 people), using real
    Census 2024 district population figures. This is a genuinely better
    comparison than raw case counts -- a bigger district looks worse on raw
    counts even if its per-person risk is actually lower.

    Resolves the earlier documented limitation: cluster_weights() still uses
    an even split within a district (public data doesn't resolve below
    district level), but THIS endpoint gives a properly normalised,
    district-level comparison that raw counts alone cannot.
    """
    df, _ = dengue_data.load_weekly_data()
    totals = dengue_data.recent_district_totals(df, dengue_data.OUR_GRAPH_DISTRICTS, n_weeks=recent_weeks)
    incidence = census_data.compare_incidence(totals)

    return [
        DistrictIncidence(
            district=d,
            cases=v["cases"],
            population=v["population"],
            incidence_per_100k=v["incidence_per_100k"],
            census_vintage=census_data.CENSUS_2024_DISTRICT_POPULATION[d]["vintage"],
            census_source=census_data.CENSUS_2024_DISTRICT_POPULATION[d]["source"],
        )
        for d, v in incidence.items()
    ]


@app.get("/api/wer-latest", response_model=WERSnapshot)
def wer_latest():
    """
    Latest single-week dengue snapshot fetched LIVE directly from the
    Epidemiology Unit's own Weekly Epidemiological Report -- independent of
    the denguedatahub aggregated series used elsewhere, as a genuine
    cross-check from the primary source itself.

    Scrapes the WER listing page to find the current report (filenames carry
    an unpredictable hash and cannot be constructed from a pattern), then
    parses Table 1 for Colombo/Gampaha dengue figures. Falls back to a real,
    dated snapshot captured during development if the live fetch or parse
    fails for any reason.
    """
    snap = wer_scraper.fetch_latest_dengue_snapshot()
    return WERSnapshot(
        mode=snap["mode"],
        report_label=snap.get("report_label"),
        source_url=snap.get("source_url"),
        districts=snap["districts"],
    )


@app.get("/api/rainfall-context", response_model=RainfallContext)
def rainfall_context():
    """
    Contextual rainfall data (HDX/WFP, CHIRPS-derived) for the report's
    introduction -- monsoon seasonality background ONLY. Never used as a
    feature by any algorithm. Returns available=False, honestly, if neither
    a live fetch nor a manually-placed cache file succeeds -- no fabricated
    numbers are ever substituted.
    """
    result = rainfall_data.load_rainfall()
    if result is None:
        return RainfallContext(available=False)
    return RainfallContext(available=True, mode=result["mode"], data=result["data"])
