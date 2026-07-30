import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { DistrictIncidence, RainfallContext, WERSnapshot } from "../types";

/**
 * DataVerificationCard - surfaces the three supplementary data sources added
 * after the initial build: Census-normalised incidence, a live WER
 * cross-check, and rainfall context. Each loads independently and fails
 * independently - one source being unavailable never blocks the others.
 */
export default function DataVerificationCard() {
  const [incidence, setIncidence] = useState<DistrictIncidence[] | null>(null);
  const [wer, setWer] = useState<WERSnapshot | null>(null);
  const [rainfall, setRainfall] = useState<RainfallContext | null>(null);
  const [werError, setWerError] = useState(false);

  useEffect(() => {
    api.districtIncidence().then(setIncidence).catch(() => setIncidence([]));
    api.werLatest().then(setWer).catch(() => setWerError(true));
    api.rainfallContext().then(setRainfall).catch(() => setRainfall({ available: false, mode: null, data: {}, note: "" }));
  }, []);

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
        Cross-checks &amp; supplementary data
      </h3>

      {/* --- Population-normalised incidence (Census 2024) --- */}
      <div className="mb-3">
        <div className="mb-1.5 flex items-center justify-between">
          <span className="text-[11px] font-semibold text-slate-600">
            Incidence per 100,000 (Census 2024)
          </span>
        </div>
        {incidence === null ? (
          <p className="text-xs text-slate-400">Loading…</p>
        ) : incidence.length === 0 ? (
          <p className="text-xs text-slate-400">Unavailable this run.</p>
        ) : (
          <div className="grid grid-cols-2 gap-2">
            {incidence.map((d) => (
              <div key={d.district} className="rounded bg-slate-50 p-2 text-center">
                <div className="text-lg font-bold text-teal-700">{d.incidence_per_100k}</div>
                <div className="text-[10px] uppercase text-slate-400">
                  {d.district} · pop {(d.population / 1e6).toFixed(2)}M
                </div>
              </div>
            ))}
          </div>
        )}
        <p className="mt-1 text-[10px] text-slate-400">
          Cases per capita, not raw counts - a fairer comparison across districts of different sizes.
        </p>
      </div>

      {/* --- Live WER cross-check --- */}
      <div className="mb-3 border-t border-slate-100 pt-3">
        <div className="mb-1.5 flex items-center justify-between">
          <span className="text-[11px] font-semibold text-slate-600">
            WER live cross-check (primary source)
          </span>
          {wer && (
            <span
              className={`rounded px-1.5 py-0.5 text-[9px] font-bold uppercase ${
                wer.mode === "live" ? "bg-green-100 text-green-700" : "bg-slate-100 text-slate-500"
              }`}
            >
              {wer.mode}
            </span>
          )}
        </div>
        {werError ? (
          <p className="text-xs text-slate-400">Unavailable this run.</p>
        ) : wer === null ? (
          <p className="text-xs text-slate-400">Loading… (can take a few seconds - live PDF fetch)</p>
        ) : (
          <>
            <p className="text-[11px] text-slate-500">
              {wer.report_label ?? "Latest available report"}
            </p>
            <div className="mt-1 grid grid-cols-2 gap-2">
              {Object.entries(wer.districts).map(([d, v]) => (
                <div key={d} className="rounded bg-slate-50 p-2 text-center">
                  <div className="text-sm font-bold text-teal-700">{v.dengue_week}</div>
                  <div className="text-[10px] uppercase text-slate-400">
                    {d} this week ({v.dengue_cumulative_2025} YTD)
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
        <p className="mt-1 text-[10px] text-slate-400">
          Independent cross-check against the Epidemiology Unit's own weekly report - separate
          from the denguedatahub aggregated series used elsewhere on this page.
        </p>
      </div>

      {/* --- Rainfall context (never a model input) --- */}
      <div className="border-t border-slate-100 pt-3">
        <span className="text-[11px] font-semibold text-slate-600">Rainfall context</span>
        {rainfall === null ? (
          <p className="text-xs text-slate-400">Loading…</p>
        ) : !rainfall.available ? (
          <p className="mt-1 text-xs text-slate-400">
            Not available this run (source blocks automated fetches; see backend notes).
          </p>
        ) : (
          <div className="mt-1 grid grid-cols-2 gap-2">
            {Object.entries(rainfall.data).map(([d, v]) => (
              <div key={d} className="rounded bg-slate-50 p-2 text-center">
                <div className="text-sm font-bold text-teal-700">{v.rainfall_mm_10day}mm</div>
                <div className="text-[10px] uppercase text-slate-400">{d} · {v.latest_date}</div>
              </div>
            ))}
          </div>
        )}
        <p className="mt-1 text-[10px] text-slate-400">
          Background context only - never used as input to any algorithm here.
        </p>
      </div>
    </div>
  );
}
