"""
dengue_data.py — real Sri Lankan dengue surveillance data.

Source: `denguedatahub` R package (Talagala, 2024), R-Consortium-funded,
maintained by Dr Thiyanga S. Talagala, University of Sri Jayewardenepura.
Weekly, district-level, 2006-present, scraped from the Epidemiology Unit's
Weekly Epidemiological Reports.

Cache-fallback: live fetch from GitHub, falling back to a committed CSV.
Same design as the coursework notebook, independently implemented here.
"""
import tempfile
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
import requests

LIVE_URL = "https://raw.githubusercontent.com/thiyangt/denguedatahub/main/data/srilanka_weekly_data.rda"
CACHE_PATH = Path(__file__).parent / "data" / "srilanka_weekly_dengue.csv"
OUR_GRAPH_DISTRICTS = ["Colombo", "Gampaha"]


def load_weekly_data(cache_path: Path = CACHE_PATH) -> Tuple[pd.DataFrame, str]:
    try:
        import pyreadr
        resp = requests.get(LIVE_URL, timeout=8)
        resp.raise_for_status()
        with tempfile.NamedTemporaryFile(suffix=".rda", delete=False) as tmp:
            tmp.write(resp.content)
            tmp_path = tmp.name
        result = pyreadr.read_r(tmp_path)
        df = result["srilanka_weekly_data"].copy()
        df.columns = ["year", "week", "start_date", "end_date", "district", "cases"]
        df["year"] = df["year"].astype(int)
        df["week"] = df["week"].astype(int)
        df["cases"] = df["cases"].astype(int)
        mode = "live"
    except Exception:
        df = pd.read_csv(cache_path)
        mode = "cache"

    df["start_date"] = pd.to_datetime(df["start_date"], format="%m/%d/%Y")
    df["end_date"] = pd.to_datetime(df["end_date"], format="%m/%d/%Y")
    return df.sort_values("start_date").reset_index(drop=True), mode


def district_share(df: pd.DataFrame, districts) -> pd.Series:
    sub = df[df["district"].isin(districts)].groupby("start_date")["cases"].sum()
    total = df.groupby("start_date")["cases"].sum()
    return (sub / total * 100).dropna()


def recent_district_totals(df: pd.DataFrame, districts, n_weeks: int = 12) -> Dict[str, int]:
    cutoff = df["start_date"].max() - pd.Timedelta(weeks=n_weeks)
    recent = df[df["start_date"] > cutoff]
    return recent[recent["district"].isin(districts)].groupby("district")["cases"].sum().to_dict()


def cluster_weights(node_district: Dict[str, str], district_totals: Dict[str, int]) -> Dict[str, float]:
    """Even-split a district total across its towns. Documented simplification:
    public data resolves only to district level, not MOH-area / town level."""
    by_district: Dict[str, list] = {}
    for town, dist in node_district.items():
        by_district.setdefault(dist, []).append(town)
    weights = {}
    for dist, town_list in by_district.items():
        share = district_totals.get(dist, 0) / len(town_list) if town_list else 0.0
        for t in town_list:
            weights[t] = share
    return weights
