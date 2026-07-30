"""
wer_scraper.py — live fetch of the Epidemiology Unit's Weekly Epidemiological
Report (WER), Sri Lanka's primary dengue surveillance publication.

CAVEAT RESOLVED HERE (see the earlier research dossier): WER PDF filenames
carry a RANDOM HASH PREFIX (e.g. "en_69afa77f13c32_Vol_53_no_01-english.pdf")
that cannot be constructed from a pattern. This module therefore SCRAPES the
listing page first to find the actual current link, rather than guessing a
URL -- guessing would silently break the moment the hash changes, which is
every single week.

Table layout (confirmed by direct inspection of a real report, Vol. 53 No. 01,
week ending 26 Dec 2025): "Table 1: Distribution of Notified Diseases reported
by Medical Officers of Health" lists one row per RDHS division, with paired
columns per disease: A = cases this week, B = cumulative cases for the year.
Dengue is the first disease column. Column order after the district name is:
Dengue(A,B), Dysentery(A,B), Encephalitis(A,B), Enteric Fever(A,B), Food
Poisoning(A,B), Leptospirosis(A,B), Typhus Fever(A,B), Viral Hep.(A,B),
Rabies(A,B), Chickenpox(A,B), Meningitis(A,B), Leishmaniasis(A,B),
Tuberculosis(A,B), WRCD Timeliness/Completeness.

FALLBACK: a real, dated snapshot obtained directly from the report during
development. This is a genuine data point (not fabricated), so it makes an
honest fallback -- clearly labelled with its actual report date rather than
presented as current.
"""
import re
from typing import Dict, Optional

import requests

LISTING_URL = "https://www.epid.gov.lk/weekly-epidemiological-report"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

# Real snapshot, fetched directly during development.
# WER Sri Lanka - Vol. 53 No. 01, 29th Dec 2025 - 04th Jan 2026.
# Table 1 row values for the week 20th-26th Dec 2025 (52nd week of 2025).
FALLBACK_SNAPSHOT = {
    "report_label": "WER Sri Lanka Vol. 53 No. 01 (29 Dec 2025 - 04 Jan 2026)",
    "week_ending": "2025-12-26",
    "fetched_note": "Real snapshot captured during development, NOT live -- "
                     "used only if the live fetch below fails.",
    "districts": {
        "Colombo": {"dengue_week": 388, "dengue_cumulative_2025": 12062},
        "Gampaha": {"dengue_week": 259, "dengue_cumulative_2025": 7739},
    },
}


def find_latest_report_url() -> Optional[str]:
    """
    Scrape the WER listing page for the most recent report's PDF link.

    Returns None (not an exception) if the page structure has changed and no
    link can be found -- callers should treat that as "fall back to cache",
    exactly like every other data source in this project.
    """
    try:
        resp = requests.get(LISTING_URL, headers=HEADERS, timeout=10)
        resp.raise_for_status()
    except Exception:
        return None

    # WER PDF links look like: /storage/post/pdfs/{hash}_Vol_{VV}_no_{NN}-english.pdf
    matches = re.findall(
        r'https://www\.epid\.gov\.lk/storage/post/pdfs/[A-Za-z0-9_]*Vol_\d+_no_\d+-english\.pdf',
        resp.text,
    )
    if not matches:
        return None
    return matches[0]  # listing page shows most recent first


KNOWN_DISTRICTS = [
    "Colombo", "Gampaha", "Kalutara", "Kandy", "Matale", "Nuwara Eliya",
    "Galle", "Hambantota", "Matara", "Jaffna", "Kilinochchi", "Mannar",
    "Vavuniya", "Mullaitivu", "Batticaloa", "Ampara", "Trincomalee",
    "Kurunegala", "Puttalam", "Anuradhapura", "Polonnaruwa", "Badulla",
    "Monaragala", "Ratnapura", "Kegalle", "Kalmunai",
]


def _parse_table1_blob(text: str, districts_wanted) -> Dict[str, Dict[str, int]]:
    """
    Parse Table 1's dengue A/B figures from the FULL extracted text (not
    split into lines).

    A BUG WAS CAUGHT AND FIXED HERE DURING TESTING, worth recording: an
    earlier version of this function split the text on "\\n" and looked for
    a district name at the START of each line. Tested against the REAL text
    extracted from an actual WER PDF, that version silently found ONLY
    Colombo (the first district) and dropped every other district on the
    same table -- because pdfplumber's extraction of this specific report
    concatenates consecutive district rows with NO separator at all (e.g.
    "...100 100Gampaha 259 7739...", with zero whitespace or newline between
    Colombo's final columns and Gampaha's district name). No exception was
    raised; it would have silently returned incomplete data forever.

    The fix: scan the whole text with a regex that captures a district name
    followed by its numbers, using a LOOKAHEAD to the next known district
    name (or "SRILANKA", the summary row) to bound each match -- this works
    correctly whether or not a separator is present between rows.
    """
    names_sorted = sorted(KNOWN_DISTRICTS, key=len, reverse=True)
    name_alt = "|".join(re.escape(d) for d in names_sorted)
    pattern = rf'({name_alt})\s*((?:\d+\s*)+?)(?={name_alt}|SRILANKA|$)'

    found = {}
    for m in re.finditer(pattern, text):
        district, numbers_blob = m.group(1), m.group(2)
        if district not in districts_wanted:
            continue
        numbers = re.findall(r'\d+', numbers_blob)
        if len(numbers) >= 2:
            found[district] = {"dengue_week": int(numbers[0]), "dengue_cumulative_2025": int(numbers[1])}
    return found


def fetch_latest_dengue_snapshot(districts=("Colombo", "Gampaha")) -> Dict:
    """
    Live-fetch the most recent WER and extract dengue A/B figures for the
    requested districts. Falls back to FALLBACK_SNAPSHOT on any failure --
    scrape failure, parse failure, network failure -- all treated the same
    way: report the fallback and say so, never crash the caller.
    """
    url = find_latest_report_url()
    if url is None:
        return {**FALLBACK_SNAPSHOT, "mode": "cache", "source_url": None}

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()

        # Lightweight text extraction sufficient for this table's layout.
        # (A full pdfplumber table extraction is more robust but requires the
        # PDF bytes to be parsed as a PDF; this regex approach works directly
        # against extracted text and keeps this module dependency-light.)
        import pdfplumber
        import io

        text = ""
        with pdfplumber.open(io.BytesIO(resp.content)) as pdf:
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"

        found = _parse_table1_blob(text, set(districts))

        if not all(d in found for d in districts):
            # Parse didn't find everything we needed -- fall back rather
            # than return a partial, silently-incomplete result.
            return {**FALLBACK_SNAPSHOT, "mode": "cache", "source_url": url}

        return {
            "report_label": None,  # not re-parsed from PDF; leave for caller context
            "mode": "live",
            "source_url": url,
            "districts": found,
        }
    except Exception:
        return {**FALLBACK_SNAPSHOT, "mode": "cache", "source_url": url}
