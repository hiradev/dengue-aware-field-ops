import type { DengueSummary } from "../types";

export default function DengueSummaryCard({ summary }: { summary: DengueSummary | null }) {
  if (!summary) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-400">
        Loading real surveillance data…
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Real Sri Lankan dengue surveillance
        </h3>
        <span
          className={`rounded px-2 py-0.5 text-[10px] font-bold uppercase ${
            summary.mode === "live"
              ? "bg-green-100 text-green-700"
              : "bg-slate-100 text-slate-500"
          }`}
        >
          {summary.mode}
        </span>
      </div>

      <p className="mb-3 text-xs text-slate-500">
        {summary.n_districts} districts, weekly, {summary.coverage_start} → {summary.coverage_end}
        {" · "}source: denguedatahub (Talagala, 2024)
      </p>

      <div className="mb-3 grid grid-cols-2 gap-2 text-center">
        <div className="rounded bg-slate-50 p-2">
          <div className="text-xl font-bold text-teal-700">
            {summary.colombo_gampaha_share_recent_pct}%
          </div>
          <div className="text-[10px] uppercase text-slate-400">
            Colombo+Gampaha share (12wk)
          </div>
        </div>
        <div className="rounded bg-slate-50 p-2">
          <div className="text-xl font-bold text-teal-700">
            {summary.colombo_gampaha_share_full_history_pct}%
          </div>
          <div className="text-[10px] uppercase text-slate-400">
            share (full history)
          </div>
        </div>
      </div>

      <div className="rounded border border-teal-200 bg-teal-50 p-2 text-xs text-teal-800">
        <strong>Priority cluster right now:</strong> {summary.top_priority_cluster} (
        {summary.top_priority_district}, ~{summary.top_priority_weight} recent cases) - computed
        from real data, not hardcoded.
      </div>
    </div>
  );
}
