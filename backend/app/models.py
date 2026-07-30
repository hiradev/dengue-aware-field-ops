"""Pydantic v2 request/response schemas."""
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class NodeOut(BaseModel):
    name: str
    lat: float
    lon: float
    type: str  # "town" | "hospital"
    district: Optional[str] = None


class EdgeOut(BaseModel):
    a: str
    b: str
    km: float


class GraphOut(BaseModel):
    nodes: List[NodeOut]
    edges: List[EdgeOut]


class RouteResult(BaseModel):
    algorithm: str
    start: str
    goal: str
    path: Optional[List[str]]
    cost_km: Optional[float]
    nodes_expanded: int
    max_frontier: int
    runtime_ms: float
    expansion_order: List[str]


class RouteComparison(BaseModel):
    start: str
    goal: str
    results: List[RouteResult]


class TriageRequest(BaseModel):
    symptoms: List[str] = Field(default_factory=list)
    strategy: str = "safety_first"


class TraceStep(BaseModel):
    rule_id: str
    conditions_met: List[str]
    conclusion: str
    cf: float
    rationale: str
    iteration: int


class TriageResponse(BaseModel):
    recommendation: str
    certainty: float
    conflict_strategy: str
    iterations: int
    trace: List[TraceStep]


class DengueSummary(BaseModel):
    mode: str  # "live" | "cache"
    coverage_start: str
    coverage_end: str
    n_districts: int
    colombo_gampaha_share_recent_pct: float
    colombo_gampaha_share_full_history_pct: float
    recent_district_totals: Dict[str, int]
    top_priority_cluster: str
    top_priority_district: str
    top_priority_weight: float
    all_cluster_weights: Dict[str, float]


class DistrictIncidence(BaseModel):
    """Population-normalised dengue burden -- from Census 2024 + real case data."""
    district: str
    cases: int
    population: int
    incidence_per_100k: float
    census_vintage: str
    census_source: str


class WERSnapshot(BaseModel):
    """Latest single-week cross-check from the Epidemiology Unit's own WER,
    independent of the denguedatahub aggregated series."""
    mode: str  # "live" | "cache"
    report_label: Optional[str] = None
    source_url: Optional[str] = None
    districts: Dict[str, Dict[str, int]]


class RainfallContext(BaseModel):
    """Background context only -- NOT used as a model input anywhere."""
    available: bool
    mode: Optional[str] = None  # "live" | "manual_cache" | None
    data: Dict[str, Dict] = Field(default_factory=dict)
    note: str = (
        "Rainfall is contextual background for the report introduction only. "
        "It is never used as a feature by any algorithm in this project."
    )
