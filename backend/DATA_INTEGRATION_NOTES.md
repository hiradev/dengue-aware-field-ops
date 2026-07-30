# Data source integration - status and decisions

Follow-up to the original data-source research. This documents what actually
got wired into the backend, and - just as important - what was deliberately
**not** integrated, and why. Silence on a caveat is worse than stating it.

## ✅ Integrated

### 1. Census 2024 (`app/census_data.py`)
Real, cited DCS Preliminary Report figures (Colombo 2,374,461; Gampaha
2,433,685; both same vintage, deliberately not mixed with the later final
figure for Gampaha alone - see the module docstring for why that would be a
silent error). Powers `/api/district-incidence`: dengue cases **per 100,000
population**, not just raw counts - a genuinely fairer district comparison.

**What this does NOT do:** it does not resolve the town-level even-split
limitation in `dengue_data.cluster_weights()`. Census data here is
district-level; there is no public town/MOH-area population breakdown to
split by. That limitation is unchanged and still honestly documented in
`dengue_data.py`.

### 2. WER live cross-check (`app/wer_scraper.py`, `/api/wer-latest`)
Resolves the specific caveat about unpredictable, hash-prefixed WER filenames:
this module scrapes the listing page for the current report's real URL rather
than guessing a pattern (which would silently break weekly). Falls back to a
**real** snapshot (Vol. 53 No. 01, week ending 26 Dec 2025 - Colombo 388
cases/12,062 cumulative; Gampaha 259/7,739) captured directly during
development - not a fabricated placeholder.

## ⚠️ Attempted, partially resolved

### 3. Rainfall context (`app/rainfall_data.py`, `/api/rainfall-context`)
**Honest status: live fetch was not verified to succeed during development.**
HDX's web application returned bot detection against automated fetches from
this development environment, both on the dataset landing page and
intermittently on the direct resource link. A normal `requests` call from an
ordinary machine may well succeed - it's a different traffic profile - but
this was **not confirmed**, and no fabricated cache was created to hide that.

The code tries live fetch, then a manually-placed local file
(`data/lka_rainfall_adm2.csv`, if you download it yourself from
`https://data.humdata.org/dataset/lka-rainfall-subnational` in an ordinary
browser), then honestly reports `available: false` if neither works. **Never
invents plausible-looking rainfall numbers.** This is explicitly framed as
report-introduction context only - it was never going to be a model input.

## ❌ Deliberately not integrated

### 4. HDX Health Facilities (coordinate verification)
The exact download resource ID for the **points** GeoJSON (as opposed to the
polygons layer, whose ID is confirmed) could not be reliably resolved via
public search snippets or the CKAN API in this environment. Rather than guess
a resource ID or fabricate a "verified" result, this remains an open item:
**if you want the hand-placed hospital/town coordinates in `graph_data.py`
independently checked, visit
`https://data.humdata.org/dataset/hotosm_lka_health_facilities` in your own
browser, download the points layer, and cross-check manually** - an ordinary
browser session doesn't hit the same bot wall automated tools do. The
coordinates currently in use remain clearly documented as approximate,
general-knowledge placements, not survey-grade.

### 5. Kaggle dengue datasets
Not integrated, on purpose. Both confirmed to exist and be public, but:
- Kaggle gates programmatic downloads behind an API token (`kaggle.json`),
  which isn't something to embed in a shared codebase without it being the
  user's own credential.
- More importantly: `denguedatahub` (already integrated, live, weekly,
  2006–present) **strictly dominates** what these Kaggle sets offer - the
  "2010–2020" set is monthly, not weekly, and neither goes further back or
  updates. Adding Kaggle here would mean extra complexity and an auth
  dependency for data that's already covered, better, by the pipeline. If a
  specific reason arises to want the Kaggle sets specifically (e.g. their
  weather-joined variant for a feature not otherwise available), revisit
  this decision explicitly rather than adding it by default.

## New endpoints summary

| Endpoint | Purpose | Status |
|---|---|---|
| `GET /api/district-incidence` | Cases per 100k, Census-normalised | ✅ working, real data |
| `GET /api/wer-latest` | Live single-week cross-check from the primary source | ✅ working, real live fetch + real fallback |
| `GET /api/rainfall-context` | Monsoon context for the report | ⚠️ honest best-effort, may report unavailable |

## What wasn't touched in this pass

This integration round focused on the **backend** (`dengue-field-ops`). The
coursework notebook (`Cw1_STUDENTID_Notebook.ipynb`) was not modified - it
remains exactly as previously frozen/verified. If you want the same
Census/WER additions mirrored into the notebook for the written report, say
so explicitly; it wasn't done automatically here to avoid touching a
graded artefact without being asked.
