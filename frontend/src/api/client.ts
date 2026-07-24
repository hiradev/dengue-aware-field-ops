import type {
  Algorithm, DengueSummary, GraphOut, RouteComparison, RouteResult, TriageResponse,
} from "../types";

const BASE = import.meta.env.VITE_API_BASE ?? "/api";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`POST ${path} failed: ${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
  health: () => get<{ status: string }>("/health"),
  graph: () => get<GraphOut>("/graph"),
  towns: () => get<string[]>("/nodes/towns"),
  hospitals: () => get<string[]>("/nodes/hospitals"),
  symptoms: () => get<string[]>("/symptoms"),

  route: (start: string, goal: string, algorithm: Algorithm) =>
    get<RouteResult>(
      `/route?start=${encodeURIComponent(start)}&goal=${encodeURIComponent(goal)}&algorithm=${algorithm}`
    ),

  compare: (start: string, goal: string) =>
    get<RouteComparison>(
      `/compare?start=${encodeURIComponent(start)}&goal=${encodeURIComponent(goal)}`
    ),

  triage: (symptoms: string[], strategy = "safety_first") =>
    post<TriageResponse>("/triage", { symptoms, strategy }),

  dengueSummary: (recentWeeks = 12) =>
    get<DengueSummary>(`/dengue-summary?recent_weeks=${recentWeeks}`),
};
