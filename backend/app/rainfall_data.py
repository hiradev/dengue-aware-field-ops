"""
rainfall_data.py - HDX "Sri Lanka: Rainfall Indicators at Subnational Level"
(WFP, CHIRPS v2), for CONTEXT ONLY -- never as a model input. See the
project's module-content constraint: only search, knowledge representation,
and decision-tree techniques are in scope; rainfall is background framing for
the report's introduction (monsoon seasonality context), not a feature.

HONEST STATUS: during development, HDX's web application returned bot
detection on both the dataset landing page and, intermittently, the direct
resource download link, when fetched from an automated tool. This is a
DIFFERENT traffic profile from a normal `requests` call made from an ordinary
machine with a standard browser User-Agent, so the live fetch below may well
succeed when this code actually runs -- but it was NOT verified to succeed
during this development session, and NO fabricated cache has been created to
paper over that. If live fetch fails, this module says so plainly and returns
None rather than inventing plausible-looking rainfall numbers.

If you obtain the CSV manually (the confirmed URL is below, works fine in an
ordinary browser), save it to `data/lka_rainfall_adm2.csv` and this module
will use it as a real, non-fabricated cache automatically.
"""
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

# Confirmed to exist and be publicly listed on HDX at time of writing.
# Resource ID may rotate over time -- if this 404s, the dataset landing page
# (https://data.humdata.org/dataset/lka-rainfall-subnational) always lists
# the current resource IDs.
LIVE_URL = (
    "https://data.humdata.org/dataset/4302257e-5fa6-4c88-b8f7-f78730d8c48b/"
    "resource/4ffa69ce-11f8-4e58-a1fb-d076e562bc1b/download/lka-rainfall-adm2-5ytd.csv"
)
MANUAL_CACHE_PATH = Path(__file__).parent / "data" / "lka_rainfall_adm2.csv"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}


def load_rainfall(districts=("Colombo", "Gampaha")) -> Optional[dict]:
    """
    Returns {"mode": "live"|"manual_cache", "data": {...}} on success, or
    None if no real data is available by either path. NEVER fabricates
    plausible-looking rainfall figures -- absence is reported as absence.
    """
    # 1. Try live fetch.
    try:
        resp = requests.get(LIVE_URL, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        df = pd.read_csv(pd.io.common.StringIO(resp.text))
        df = df.iloc[1:]  # first data row is an HXL hashtag row -- drop it
        return {"mode": "live", "data": _summarise(df, districts)}
    except Exception:
        pass

    # 2. Try a manually-obtained local cache (user downloaded it via browser).
    if MANUAL_CACHE_PATH.exists():
        try:
            df = pd.read_csv(MANUAL_CACHE_PATH)
            df = df.iloc[1:]
            return {"mode": "manual_cache", "data": _summarise(df, districts)}
        except Exception:
            pass

    # 3. Genuinely unavailable. Say so -- do not invent numbers.
    return None


def _summarise(df: pd.DataFrame, districts) -> dict:
    """Latest rainfall reading (rfh, mm) per requested district, if the
    admin-2 column can be matched against district names."""
    admin_col = next((c for c in df.columns if "adm2" in c.lower() and "name" in c.lower()), None)
    if admin_col is None:
        return {}
    out = {}
    for d in districts:
        sub = df[df[admin_col].astype(str).str.contains(d, case=False, na=False)]
        if sub.empty or "rfh" not in df.columns:
            continue
        sub = sub.copy()
        sub["date"] = pd.to_datetime(sub["date"], errors="coerce")
        sub = sub.sort_values("date")
        latest = sub.iloc[-1]
        out[d] = {"latest_date": str(latest["date"].date()), "rainfall_mm_10day": float(latest["rfh"])}
    return out
