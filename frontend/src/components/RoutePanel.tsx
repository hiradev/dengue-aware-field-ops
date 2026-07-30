import { useEffect, useState } from "react";
import type { Algorithm, RouteResult } from "../types";

interface Props {
  towns: string[];
  hospitals: string[];
  start: string;
  goal: string;
  algorithm: Algorithm;
  route: RouteResult | null;
  loading: boolean;
  onChange: (start: string, goal: string, algorithm: Algorithm) => void;
}

const ALGO_LABELS: Record<Algorithm, string> = { bfs: "BFS", ucs: "UCS", astar: "A*" };

export default function RoutePanel({
  towns, hospitals, start, goal, algorithm, route, loading, onChange,
}: Props) {
  const [localStart, setLocalStart] = useState(start);
  const [localGoal, setLocalGoal] = useState(goal);
  const [localAlgo, setLocalAlgo] = useState<Algorithm>(algorithm);

  useEffect(() => {
    setLocalStart(start);
    setLocalGoal(goal);
    setLocalAlgo(algorithm);
  }, [start, goal, algorithm]);

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
        1 · Route the field team
      </h3>

      <label className="mb-1 block text-xs text-slate-500">Case cluster (start)</label>
      <select
        className="mb-3 w-full rounded border border-slate-300 px-2 py-1.5 text-sm"
        value={localStart}
        onChange={(e) => setLocalStart(e.target.value)}
      >
        {towns.map((t) => (
          <option key={t} value={t}>{t}</option>
        ))}
      </select>

      <label className="mb-1 block text-xs text-slate-500">Referral hospital (goal)</label>
      <select
        className="mb-3 w-full rounded border border-slate-300 px-2 py-1.5 text-sm"
        value={localGoal}
        onChange={(e) => setLocalGoal(e.target.value)}
      >
        {hospitals.map((h) => (
          <option key={h} value={h}>{h}</option>
        ))}
      </select>

      <label className="mb-1 block text-xs text-slate-500">Search algorithm</label>
      <div className="mb-3 flex gap-1.5">
        {(Object.keys(ALGO_LABELS) as Algorithm[]).map((a) => (
          <button
            key={a}
            onClick={() => setLocalAlgo(a)}
            className={`flex-1 rounded border px-2 py-1.5 text-xs font-medium transition ${
              localAlgo === a
                ? "border-teal-700 bg-teal-700 text-white"
                : "border-slate-300 bg-white text-slate-600 hover:bg-slate-50"
            }`}
          >
            {ALGO_LABELS[a]}
          </button>
        ))}
      </div>

      <button
        onClick={() => onChange(localStart, localGoal, localAlgo)}
        disabled={loading}
        className="w-full rounded bg-teal-600 px-3 py-2 text-sm font-semibold text-white hover:brightness-110 disabled:opacity-50"
      >
        {loading ? "Running…" : "▶ Run search"}
      </button>

      {route && (
        <div className="mt-4 grid grid-cols-3 gap-2 text-center">
          <div className="rounded bg-slate-50 p-2">
            <div className="text-lg font-bold text-teal-700">
              {route.cost_km?.toFixed(1) ?? "-"}
            </div>
            <div className="text-[10px] uppercase text-slate-400">km</div>
          </div>
          <div className="rounded bg-slate-50 p-2">
            <div className="text-lg font-bold text-teal-700">{route.nodes_expanded}</div>
            <div className="text-[10px] uppercase text-slate-400">expanded</div>
          </div>
          <div className="rounded bg-slate-50 p-2">
            <div className="text-lg font-bold text-teal-700">
              {route.runtime_ms.toFixed(2)}
            </div>
            <div className="text-[10px] uppercase text-slate-400">ms</div>
          </div>
        </div>
      )}
    </div>
  );
}
