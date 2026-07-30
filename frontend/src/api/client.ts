import type {
  Algorithm, DengueSummary, DistrictIncidence, GraphOut, RainfallContext,
  RouteComparison, RouteResult, TriageResponse, WERSnapshot,
} from "../types";

const BASE = import.meta.env.VITE_API_BASE ?? "/api";

async function get<T>(path: string, timeoutMs?: number): Promise<T> {
  const controller = new AbortController();
  const timer = timeoutMs ? setTimeout(() => controller.abort(), timeoutMs) : undefined;
  try {
    const res = await fetch(`${BASE}${path}`, { signal: controller.signal });
    if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
    return res.json() as Promise<T>;
  } finally {
    if (timer) clearTimeout(timer);
  }
}

async function post<T>(path: string, body: unknown, timeoutMs?: number): Promise<T> {
  const controller = new AbortController();
  const timer = timeoutMs ? setTimeout(() => controller.abort(), timeoutMs) : undefined;
  try {
    const res = await fetch(`${BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    if (!res.ok) throw new Error(`POST ${path} failed: ${res.status}`);
    return res.json() as Promise<T>;
  } finally {
    if (timer) clearTimeout(timer);
  }
}

export const api = {
  health: (timeoutMs?: number) => get<{ status: string }>("/health", timeoutMs),
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
    post<TriageResponse>("/triage", { symptoms, strategy }, 15_000),

  dengueSummary: (recentWeeks = 12) =>
    get<DengueSummary>(`/dengue-summary?recent_weeks=${recentWeeks}`),

  districtIncidence: (recentWeeks = 12) =>
    get<DistrictIncidence[]>(`/district-incidence?recent_weeks=${recentWeeks}`),

  werLatest: () => get<WERSnapshot>("/wer-latest", 20_000),

  rainfallContext: () => get<RainfallContext>("/rainfall-context", 10_000),
};
