import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell,
} from "recharts";
import type { RouteComparison } from "../types";

const COLORS: Record<string, string> = { BFS: "#94a3b8", UCS: "#028090", "A*": "#00a896" };

export default function CompareChart({ comparison }: { comparison: RouteComparison | null }) {
  if (!comparison) {
    return (
      <div className="flex h-40 items-center justify-center text-sm text-slate-400">
        Run a search to compare all three algorithms.
      </div>
    );
  }

  const data = comparison.results.map((r) => ({
    algorithm: r.algorithm,
    nodes_expanded: r.nodes_expanded,
    cost_km: r.cost_km ?? 0,
  }));

  const optimalCost = Math.min(...data.map((d) => d.cost_km).filter((c) => c > 0));

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
        Comparison A - nodes expanded ({comparison.start} → {comparison.goal})
      </h3>
      <div style={{ width: "100%", height: 180 }}>
        <ResponsiveContainer>
          <BarChart data={data} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e9e8" />
            <XAxis dataKey="algorithm" fontSize={11} />
            <YAxis fontSize={11} />
            <Tooltip
              formatter={(v: number, name: string) =>
                name === "nodes_expanded" ? [`${v} nodes`, "expanded"] : [v, name]
              }
            />
            <Bar dataKey="nodes_expanded" radius={[4, 4, 0, 0]}>
              {data.map((d, i) => (
                <Cell key={i} fill={COLORS[d.algorithm] ?? "#028090"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-2 text-[11px] text-slate-500">
        Path cost: {data.map((d) => `${d.algorithm} ${d.cost_km.toFixed(1)}km`).join(" · ")}
        {" - "}
        {data.every((d) => Math.abs(d.cost_km - optimalCost) < 0.01)
          ? "all three found the optimal route"
          : "BFS returned a longer route (non-uniform edge costs)"}
        .
      </p>
    </div>
  );
}
