export interface NodeOut {
  name: string;
  lat: number;
  lon: number;
  type: "town" | "hospital";
  district?: string | null;
}

export interface EdgeOut {
  a: string;
  b: string;
  km: number;
}

export interface GraphOut {
  nodes: NodeOut[];
  edges: EdgeOut[];
}

export interface RouteResult {
  algorithm: string;
  start: string;
  goal: string;
  path: string[] | null;
  cost_km: number | null;
  nodes_expanded: number;
  max_frontier: number;
  runtime_ms: number;
  expansion_order: string[];
}

export interface RouteComparison {
  start: string;
  goal: string;
  results: RouteResult[];
}

export interface TraceStep {
  rule_id: string;
  conditions_met: string[];
  conclusion: string;
  cf: number;
  rationale: string;
  iteration: number;
}

export interface TriageResponse {
  recommendation: "REFER_URGENT" | "REFER" | "MONITOR" | "HOME_CARE";
  certainty: number;
  conflict_strategy: string;
  iterations: number;
  trace: TraceStep[];
}

export interface DengueSummary {
  mode: "live" | "cache";
  coverage_start: string;
  coverage_end: string;
  n_districts: number;
  colombo_gampaha_share_recent_pct: number;
  colombo_gampaha_share_full_history_pct: number;
  recent_district_totals: Record<string, number>;
  top_priority_cluster: string;
  top_priority_district: string;
  top_priority_weight: number;
  all_cluster_weights: Record<string, number>;
}

export type Algorithm = "bfs" | "ucs" | "astar";

export interface DistrictIncidence {
  district: string;
  cases: number;
  population: number;
  incidence_per_100k: number;
  census_vintage: string;
  census_source: string;
}

export interface WERSnapshot {
  mode: "live" | "cache";
  report_label: string | null;
  source_url: string | null;
  districts: Record<string, { dengue_week: number; dengue_cumulative_2025: number }>;
}

export interface RainfallContext {
  available: boolean;
  mode: "live" | "manual_cache" | null;
  data: Record<string, { latest_date: string; rainfall_mm_10day: number }>;
  note: string;
}
