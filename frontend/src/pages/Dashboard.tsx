import { lazy, Suspense, useEffect, useState } from "react";
import { api } from "../api/client";
import type {
  Algorithm, DengueSummary, GraphOut, RouteComparison, RouteResult, TriageResponse,
} from "../types";
import Header from "../components/Header";
import RoutePanel from "../components/RoutePanel";
import TriagePanel from "../components/TriagePanel";
import DengueSummaryCard from "../components/DengueSummaryCard";
import DataVerificationCard from "../components/DataVerificationCard";

// Leaflet and Recharts are the largest runtime deps — split them out of the
// main bundle so the initial load doesn't pay for both up front.
const MapView = lazy(() => import("../components/MapView"));
const CompareChart = lazy(() => import("../components/CompareChart"));

type BackendStatus = "checking" | "waking" | "ready" | "down";

const HEALTH_TIMEOUT_MS = 10_000;
const RETRY_DELAY_MS = 4_000;
const MAX_WAKE_ATTEMPTS = 20; // ~ up to ~2.5 minutes, covers Render free-tier cold starts

export default function Dashboard() {
  const [graph, setGraph] = useState<GraphOut | null>(null);
  const [towns, setTowns] = useState<string[]>([]);
  const [hospitals, setHospitals] = useState<string[]>([]);
  const [symptoms, setSymptoms] = useState<string[]>([]);
  const [summary, setSummary] = useState<DengueSummary | null>(null);

  const [start, setStart] = useState("");
  const [goal, setGoal] = useState("");
  const [algorithm, setAlgorithm] = useState<Algorithm>("astar");
  const [route, setRoute] = useState<RouteResult | null>(null);
  const [comparison, setComparison] = useState<RouteComparison | null>(null);
  const [routeLoading, setRouteLoading] = useState(false);

  const [triageResult, setTriageResult] = useState<TriageResponse | null>(null);
  const [triageLoading, setTriageLoading] = useState(false);

  const [error, setError] = useState<string | null>(null);

  const [backendStatus, setBackendStatus] = useState<BackendStatus>("checking");
  const [wakeAttempt, setWakeAttempt] = useState(0);
  const [retryKey, setRetryKey] = useState(0);

  // Poll /api/health until the backend responds. On a free hosting tier
  // (e.g. Render) the backend spins down when idle, so the first request
  // after a while wakes it up but can take up to ~50s to answer.
  useEffect(() => {
    let cancelled = false;
    setBackendStatus("checking");
    setWakeAttempt(0);

    (async () => {
      for (let attempt = 1; attempt <= MAX_WAKE_ATTEMPTS; attempt++) {
        if (cancelled) return;
        setWakeAttempt(attempt);
        try {
          await api.health(HEALTH_TIMEOUT_MS);
          if (!cancelled) setBackendStatus("ready");
          return;
        } catch {
          if (cancelled) return;
          setBackendStatus("waking");
          await new Promise((r) => setTimeout(r, RETRY_DELAY_MS));
        }
      }
      if (!cancelled) setBackendStatus("down");
    })();

    return () => {
      cancelled = true;
    };
  }, [retryKey]);

  // Once the backend is confirmed awake, load graph, towns, hospitals,
  // symptoms, and real dengue data.
  useEffect(() => {
    if (backendStatus !== "ready") return;
    (async () => {
      try {
        const [g, t, h, s, d] = await Promise.all([
          api.graph(), api.towns(), api.hospitals(), api.symptoms(), api.dengueSummary(),
        ]);
        setGraph(g);
        setTowns(t.sort());
        setHospitals(h);
        setSymptoms(s);
        setSummary(d);

        // Default the start cluster to the REAL highest-priority town, not an
        // arbitrary hardcoded one — the whole point of wiring in live data.
        const defaultStart = d.top_priority_cluster || t[0];
        const defaultGoal = h[0];
        setStart(defaultStart);
        setGoal(defaultGoal);
      } catch (e) {
        setError("Backend woke up but the initial data load failed. Please retry.");
      }
    })();
  }, [backendStatus]);

  const retryBackend = () => {
    setError(null);
    setRetryKey((k) => k + 1);
  };

  const runRoute = async (s: string, g: string, algo: Algorithm) => {
    setStart(s); setGoal(g); setAlgorithm(algo);
    setRouteLoading(true);
    try {
      const [r, c] = await Promise.all([api.route(s, g, algo), api.compare(s, g)]);
      setRoute(r);
      setComparison(c);
    } catch (e) {
      const detail = e instanceof Error ? e.message : String(e);
      setError(`Route request failed: ${detail}`);
    } finally {
      setRouteLoading(false);
    }
  };

  const runTriage = async (selected: string[]) => {
    setTriageLoading(true);
    try {
      const r = await api.triage(selected, "safety_first");
      setTriageResult(r);
    } catch (e) {
      const detail = e instanceof Error ? e.message : String(e);
      setError(`Triage request failed: ${detail}`);
    } finally {
      setTriageLoading(false);
    }
  };

  if (backendStatus === "checking" || backendStatus === "waking") {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-slate-50 p-8 text-center">
        <Header />
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-teal-600 border-t-transparent" />
        <p className="max-w-md text-sm text-slate-600">
          {backendStatus === "checking"
            ? "Connecting to the backend…"
            : "Waking up the backend server — free-tier hosting spins it down when idle, " +
              "so this can take up to a minute."}
        </p>
        <p className="text-xs text-slate-400">Attempt {wakeAttempt} of {MAX_WAKE_ATTEMPTS}</p>
      </div>
    );
  }

  if (backendStatus === "down") {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-slate-50 p-8 text-center">
        <Header />
        <p className="max-w-md text-sm text-red-600">
          The backend isn't responding. It may be down, or still starting up.
        </p>
        <button
          onClick={retryBackend}
          className="rounded bg-teal-600 px-4 py-2 text-sm font-semibold text-white hover:brightness-110"
        >
          Retry
        </button>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-slate-50 p-8 text-center">
        <Header />
        <p className="max-w-md text-sm text-red-600">{error}</p>
        <button
          onClick={retryBackend}
          className="rounded bg-teal-600 px-4 py-2 text-sm font-semibold text-white hover:brightness-110"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-slate-50 lg:h-screen">
      <Header />
      <div className="grid flex-1 grid-cols-1 gap-4 p-4 lg:grid-cols-[1fr_380px] lg:overflow-hidden">
        <div className="flex flex-col gap-4 lg:overflow-hidden">
          <div className="h-72 overflow-hidden rounded-lg border border-slate-200 sm:h-96 lg:h-auto lg:min-h-[320px] lg:flex-1">
            <Suspense fallback={
              <div className="flex h-full items-center justify-center text-sm text-slate-400">
                Loading map…
              </div>
            }>
              <MapView graph={graph} route={route} start={start} goal={goal} />
            </Suspense>
          </div>
          <Suspense fallback={null}>
            <CompareChart comparison={comparison} />
          </Suspense>
        </div>

        <div className="flex flex-col gap-4 lg:overflow-y-auto lg:pr-1">
          <DengueSummaryCard summary={summary} />
          <DataVerificationCard />
          <RoutePanel
            towns={towns} hospitals={hospitals}
            start={start} goal={goal} algorithm={algorithm}
            route={route} loading={routeLoading}
            onChange={runRoute}
          />
          <TriagePanel
            symptoms={symptoms} loading={triageLoading}
            result={triageResult} onRun={runTriage}
          />
        </div>
      </div>
    </div>
  );
}
