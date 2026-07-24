import { useEffect, useState } from "react";
import { api } from "../api/client";
import type {
  Algorithm, DengueSummary, GraphOut, RouteComparison, RouteResult, TriageResponse,
} from "../types";
import Header from "../components/Header";
import MapView from "../components/MapView";
import RoutePanel from "../components/RoutePanel";
import TriagePanel from "../components/TriagePanel";
import DengueSummaryCard from "../components/DengueSummaryCard";
import CompareChart from "../components/CompareChart";

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

  // Initial load: graph, towns, hospitals, symptoms, and real dengue data.
  useEffect(() => {
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
        setError(
          "Could not reach the backend API. Is it running? " +
          "Start it with: uvicorn app.main:app --reload --port 8000"
        );
      }
    })();
  }, []);

  const runRoute = async (s: string, g: string, algo: Algorithm) => {
    setStart(s); setGoal(g); setAlgorithm(algo);
    setRouteLoading(true);
    try {
      const [r, c] = await Promise.all([api.route(s, g, algo), api.compare(s, g)]);
      setRoute(r);
      setComparison(c);
    } catch {
      setError("Route request failed.");
    } finally {
      setRouteLoading(false);
    }
  };

  const runTriage = async (selected: string[]) => {
    setTriageLoading(true);
    try {
      const r = await api.triage(selected, "safety_first");
      setTriageResult(r);
    } catch {
      setError("Triage request failed.");
    } finally {
      setTriageLoading(false);
    }
  };

  if (error) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-3 bg-slate-50 p-8 text-center">
        <Header />
        <p className="max-w-md text-sm text-red-600">{error}</p>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col bg-slate-50">
      <Header />
      <div className="grid flex-1 grid-cols-1 gap-4 overflow-hidden p-4 lg:grid-cols-[1fr_380px]">
        <div className="flex flex-col gap-4 overflow-hidden">
          <div className="min-h-[320px] flex-1 overflow-hidden rounded-lg border border-slate-200">
            <MapView graph={graph} route={route} start={start} goal={goal} />
          </div>
          <CompareChart comparison={comparison} />
        </div>

        <div className="flex flex-col gap-4 overflow-y-auto pr-1">
          <DengueSummaryCard summary={summary} />
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
