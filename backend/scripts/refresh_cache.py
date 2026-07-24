"""
refresh_cache.py — one-time (or periodic) local cache population.

Run this once after setup: python scripts/refresh_cache.py

Fetches the live dengue dataset and writes it to app/data/srilanka_weekly_dengue.csv
so the API has an offline fallback if the live GitHub fetch is ever unavailable.
The API works without running this too — it tries the live fetch first on every
request to /api/dengue-summary — but running this once means the fallback path is
tested and populated, matching the notebook's cache-fallback design.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.dengue_data import load_weekly_data, CACHE_PATH

if __name__ == "__main__":
    df, mode = load_weekly_data()
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_out = df.copy()
    df_out["start_date"] = df_out["start_date"].dt.strftime("%m/%d/%Y")
    df_out["end_date"] = df_out["end_date"].dt.strftime("%m/%d/%Y")
    df_out.to_csv(CACHE_PATH, index=False)
    print(f"Loaded in '{mode}' mode: {len(df):,} rows")
    print(f"Cache written to: {CACHE_PATH}")
