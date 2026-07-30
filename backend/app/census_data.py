"""
census_data.py — Sri Lanka Census of Population and Housing 2024.

Source: Department of Census and Statistics (DCS), Sri Lanka.
- Preliminary Report: received by the President at the Presidential
  Secretariat, Colombo, 7 April 2025. District-level figures.
- Final report (district + Divisional Secretariat Division level):
  released 30 October 2025.
- Hub page: https://www.statistics.gov.lk/Population/StaticalInformation/CPH2024/

FIGURES USED HERE, AND WHY:
We use the PRELIMINARY district figures for BOTH Colombo and Gampaha, because
that is the vintage for which we have a confirmed figure for both districts
from the same report. The final report's press release confirmed Gampaha's
final figure (2,436,142) but our source material did not carry a matching
final figure for Colombo specifically — rather than mix a final figure for
one district with a preliminary figure for the other (which would silently
compare two different vintages), we use the preliminary figures for both,
consistently, and say so. This is exactly the kind of vintage-mixing mistake
that's easy to make silently; call it out instead.

WHAT THIS DATA CAN AND CANNOT DO:
Census data here is DISTRICT-level population. It lets us compute a
population-NORMALISED incidence rate (cases per 100,000 people) at district
level, which is a genuinely better metric than raw case counts. It does NOT
give us town/MOH-area population, so it CANNOT resolve the town-level
even-split limitation already documented in dengue_data.cluster_weights() --
that limitation stands. Do not claim otherwise in the report.
"""

CENSUS_2024_DISTRICT_POPULATION = {
    # District: (population, vintage, source_note)
    "Colombo": {
        "population": 2_374_461,
        "density_per_km2": 3_549,
        "vintage": "preliminary",
        "source": "DCS Census of Population and Housing 2024, Preliminary Report "
                   "(received by the President, 7 April 2025)",
    },
    "Gampaha": {
        "population": 2_433_685,
        "density_per_km2": None,  # not confirmed in our source material
        "vintage": "preliminary",
        "source": "DCS Census of Population and Housing 2024, Preliminary Report "
                   "(received by the President, 7 April 2025). NOTE: the DCS final "
                   "release (30 Oct 2025) confirmed Gampaha's FINAL figure as "
                   "2,436,142 -- deliberately not used here, to avoid mixing a "
                   "final figure for one district with a preliminary figure for "
                   "the other in the same comparison.",
    },
}

NATIONAL_CONTEXT = {
    "preliminary_total": 21_763_170,  # DCS Preliminary Report, 7 April 2025
    "final_total": 21_781_800,        # DCS final release, 30 October 2025
    "final_national_density_per_km2": 350,
}


def get_district_population(district: str) -> int:
    """Population for a district, or raise KeyError if not covered here."""
    return CENSUS_2024_DISTRICT_POPULATION[district]["population"]


def incidence_per_100k(cases: int, district: str) -> float:
    """
    Cases per 100,000 population -- lets you compare disease BURDEN across
    districts of different sizes fairly, rather than comparing raw counts
    (where the larger district always looks "worse" even if it is actually
    less affected per person).
    """
    pop = get_district_population(district)
    return round(cases / pop * 100_000, 1)


def compare_incidence(district_case_totals: dict) -> dict:
    """
    Given {district: case_count}, return {district: {cases, population,
    incidence_per_100k}} for every district we have census coverage for.

    Districts not in CENSUS_2024_DISTRICT_POPULATION are silently skipped --
    we only cover Colombo and Gampaha, which is all this project needs, and
    silently guessing a population for an uncovered district would be worse
    than omitting it.
    """
    out = {}
    for district, cases in district_case_totals.items():
        if district not in CENSUS_2024_DISTRICT_POPULATION:
            continue
        pop = get_district_population(district)
        out[district] = {
            "cases": cases,
            "population": pop,
            "incidence_per_100k": incidence_per_100k(cases, district),
        }
    return out
