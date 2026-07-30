import { useState } from "react";
import type { TriageResponse } from "../types";

interface Props {
  symptoms: string[];
  loading: boolean;
  result: TriageResponse | null;
  onRun: (selected: string[]) => void;
}

const REC_STYLES: Record<string, string> = {
  REFER_URGENT: "bg-red-50 text-red-700 border-red-300",
  REFER: "bg-amber-50 text-amber-700 border-amber-300",
  MONITOR: "bg-teal-50 text-teal-700 border-teal-300",
  HOME_CARE: "bg-green-50 text-green-700 border-green-300",
};

const WARNING_SIGNS = new Set([
  "abdominal_pain", "persistent_vomiting", "mucosal_bleeding",
  "lethargy_restlessness", "fluid_accumulation", "liver_enlargement",
  "platelet_drop", "haematocrit_rise",
]);

export default function TriagePanel({ symptoms, loading, result, onRun }: Props) {
  const [selected, setSelected] = useState<Set<string>>(
    new Set(["fever", "fever_days_2_7", "headache", "retro_orbital_pain"])
  );

  const toggle = (s: string) => {
    const next = new Set(selected);
    next.has(s) ? next.delete(s) : next.add(s);
    setSelected(next);
  };

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
        2 · Triage the patient
      </h3>

      <label className="mb-1 block text-xs text-slate-500">
        Observed symptoms (click to toggle)
      </label>
      <div className="mb-3 flex flex-wrap gap-1.5">
        {symptoms.map((s) => (
          <button
            key={s}
            onClick={() => toggle(s)}
            className={`rounded-full border px-2.5 py-1 text-[11px] transition ${
              selected.has(s)
                ? WARNING_SIGNS.has(s)
                  ? "border-amber-500 bg-amber-500 text-white"
                  : "border-teal-600 bg-teal-600 text-white"
                : "border-slate-300 bg-white text-slate-500 hover:bg-slate-50"
            }`}
          >
            {s.replace(/_/g, " ")}
          </button>
        ))}
      </div>

      <button
        onClick={() => onRun([...selected])}
        disabled={loading}
        className="w-full rounded bg-teal-600 px-3 py-2 text-sm font-semibold text-white hover:brightness-110 disabled:opacity-50"
      >
        {loading ? "Running…" : "▶ Run triage"}
      </button>

      {result && (
        <>
          <div
            className={`mt-4 rounded border px-3 py-2 text-center text-sm font-bold ${
              REC_STYLES[result.recommendation] ?? ""
            }`}
          >
            {result.recommendation.replace("_", " ")} · certainty {result.certainty.toFixed(2)}
          </div>

          <div className="mt-3 max-h-64 overflow-auto rounded bg-slate-900 p-3 font-mono text-[11px] leading-relaxed text-slate-200">
            {result.trace.length === 0 ? (
              <p>No rules fired. Defaulting to HOME_CARE.</p>
            ) : (
              result.trace.map((t, i) => (
                <div key={i} className="mb-2">
                  <span className="text-teal-300">[{t.rule_id}]</span> CF={t.cf.toFixed(2)}
                  <br />
                  &nbsp;&nbsp;IF &nbsp;{t.conditions_met.join(" AND ")}
                  <br />
                  &nbsp;&nbsp;THEN {t.conclusion}
                  <br />
                  &nbsp;&nbsp;WHY &nbsp;{t.rationale}
                </div>
              ))
            )}
          </div>
        </>
      )}

      <p className="mt-3 rounded border border-dashed border-red-200 bg-red-50 p-2 text-[10.5px] text-red-600">
        ⚠ Coursework simplification of WHO/NDCU criteria. Not a validated clinical
        instrument - must not be used for patient care.
      </p>
    </div>
  );
}
