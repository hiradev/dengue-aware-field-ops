"""
graph_data.py — independent re-implementation for the demo API.

This deliberately duplicates (rather than imports) the graph logic from the
coursework notebook. Per the project's own design principle, the demo app must
stand on its own — the notebook must remain self-contained and gradeable with
zero dependency on this app, and this app must not silently depend on the
notebook's environment either.

Real locations across Colombo and Gampaha districts, Sri Lanka: 36 towns
(case-cluster locations) + 8 real referral hospitals.

Road distances are DERIVED FROM GEOMETRY (haversine x detour factor >= 1.15),
never hand-estimated — this guarantees the straight-line heuristic used by A*
is admissible by construction. See heuristics.py for the proof this is exact.
"""
import math

NODES = {
    "Colombo Fort":      (6.9344, 79.8428, "town"),
    "Pettah":            (6.9370, 79.8500, "town"),
    "Maradana":          (6.9290, 79.8650, "town"),
    "Borella":           (6.9147, 79.8776, "town"),
    "Narahenpita":       (6.8990, 79.8770, "town"),
    "Kirulapone":        (6.8790, 79.8760, "town"),
    "Nugegoda":          (6.8649, 79.8997, "town"),
    "Maharagama":        (6.8482, 79.9265, "town"),
    "Kotte":             (6.8905, 79.9018, "town"),
    "Rajagiriya":        (6.9080, 79.8940, "town"),
    "Battaramulla":      (6.8990, 79.9180, "town"),
    "Dehiwala":          (6.8511, 79.8650, "town"),
    "Mount Lavinia":     (6.8389, 79.8653, "town"),
    "Ratmalana":         (6.8210, 79.8860, "town"),
    "Moratuwa":          (6.7730, 79.8816, "town"),
    "Piliyandala":       (6.8010, 79.9220, "town"),
    "Kesbewa":           (6.7950, 79.9390, "town"),
    "Homagama":          (6.8440, 80.0020, "town"),
    "Kaduwela":          (6.9330, 79.9840, "town"),
    "Kolonnawa":         (6.9330, 79.8890, "town"),
    "Kelaniya":          (6.9553, 79.9220, "town"),
    "Wellampitiya":      (6.9400, 79.9050, "town"),
    "Angoda":            (6.9370, 79.9210, "town"),
    "Mulleriyawa":       (6.9450, 79.9350, "town"),
    "Kadawatha":         (7.0000, 79.9500, "town"),
    "Ragama":            (7.0280, 79.9180, "town"),
    "Wattala":           (6.9890, 79.8920, "town"),
    "Ja-Ela":            (7.0740, 79.8920, "town"),
    "Negombo":           (7.2090, 79.8380, "town"),
    "Gampaha":           (7.0910, 79.9990, "town"),
    "Minuwangoda":       (7.1670, 79.9500, "town"),
    "Kiribathgoda":      (6.9790, 79.9280, "town"),
    "Biyagama":          (6.9560, 79.9700, "town"),
    "Delgoda":           (6.9930, 80.0000, "town"),
    "Veyangoda":         (7.1540, 80.0600, "town"),
    "Divulapitiya":      (7.2210, 80.0170, "town"),
    "NHSL Colombo":              (6.9210, 79.8640, "hospital"),
    "Colombo South TH":          (6.8570, 79.8770, "hospital"),
    "Sri Jayewardenepura GH":    (6.8830, 79.9050, "hospital"),
    "NIID Angoda":               (6.9390, 79.9250, "hospital"),
    "Colombo North TH Ragama":   (7.0290, 79.9210, "hospital"),
    "DGH Gampaha":               (7.0930, 79.9970, "hospital"),
    "DGH Negombo":               (7.2110, 79.8420, "hospital"),
    "BH Homagama":               (6.8430, 80.0040, "hospital"),
}

_RAW_EDGES = [
    ("Colombo Fort", "Pettah"), ("Pettah", "Maradana"), ("Maradana", "Borella"),
    ("Maradana", "NHSL Colombo"), ("Pettah", "NHSL Colombo"), ("Borella", "NHSL Colombo"),
    ("Borella", "Narahenpita"), ("Borella", "Rajagiriya"), ("Narahenpita", "Kirulapone"),
    ("Kirulapone", "Nugegoda"), ("Nugegoda", "Maharagama"), ("Nugegoda", "Kotte"),
    ("Nugegoda", "Dehiwala"), ("Nugegoda", "Sri Jayewardenepura GH"),
    ("Kotte", "Sri Jayewardenepura GH"), ("Kotte", "Rajagiriya"), ("Kotte", "Battaramulla"),
    ("Rajagiriya", "Battaramulla"), ("Battaramulla", "Kaduwela"),
    ("Kirulapone", "Colombo South TH"), ("Dehiwala", "Colombo South TH"),
    ("Dehiwala", "Mount Lavinia"), ("Mount Lavinia", "Ratmalana"), ("Ratmalana", "Moratuwa"),
    ("Moratuwa", "Piliyandala"), ("Piliyandala", "Kesbewa"), ("Piliyandala", "Maharagama"),
    ("Kesbewa", "Homagama"), ("Maharagama", "Homagama"), ("Homagama", "BH Homagama"),
    ("Homagama", "Kaduwela"), ("Maharagama", "Sri Jayewardenepura GH"),
    ("Maradana", "Kolonnawa"), ("Kolonnawa", "Wellampitiya"), ("Wellampitiya", "Angoda"),
    ("Angoda", "NIID Angoda"), ("Angoda", "Mulleriyawa"), ("Mulleriyawa", "Kaduwela"),
    ("Kolonnawa", "Kelaniya"), ("Angoda", "Kelaniya"), ("Kelaniya", "Kiribathgoda"),
    ("Kelaniya", "Biyagama"), ("Biyagama", "Delgoda"), ("Delgoda", "Kaduwela"),
    ("Kaduwela", "Biyagama"), ("Pettah", "Wattala"), ("Wattala", "Kiribathgoda"),
    ("Kiribathgoda", "Kadawatha"), ("Kadawatha", "Ragama"),
    ("Ragama", "Colombo North TH Ragama"), ("Ragama", "Ja-Ela"), ("Wattala", "Ja-Ela"),
    ("Ja-Ela", "Negombo"), ("Negombo", "DGH Negombo"), ("Ja-Ela", "Minuwangoda"),
    ("Negombo", "Minuwangoda"), ("Kadawatha", "Gampaha"), ("Ragama", "Gampaha"),
    ("Gampaha", "DGH Gampaha"), ("Gampaha", "Minuwangoda"), ("Gampaha", "Veyangoda"),
    ("Gampaha", "Delgoda"), ("Veyangoda", "Divulapitiya"), ("Minuwangoda", "Divulapitiya"),
    ("Kadawatha", "Delgoda"),
]

MIN_DETOUR = 1.15
URBAN_DETOUR = 1.30
SUBURBAN_DETOUR = 1.22


def _haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _detour_factor(straight_km: float) -> float:
    return URBAN_DETOUR if straight_km < 5.0 else SUBURBAN_DETOUR


def get_edges():
    """Edge list with distances DERIVED from geometry — admissible by construction."""
    edges = []
    for a, b in _RAW_EDGES:
        lat1, lon1, _ = NODES[a]
        lat2, lon2, _ = NODES[b]
        straight = _haversine(lat1, lon1, lat2, lon2)
        road = max(straight * _detour_factor(straight), straight * MIN_DETOUR)
        edges.append((a, b, round(road, 3)))
    return edges


def get_nodes():
    return dict(NODES)


def hospitals():
    return [n for n, (_, _, t) in NODES.items() if t == "hospital"]


def towns():
    return [n for n, (_, _, t) in NODES.items() if t == "town"]


NODE_DISTRICT = {
    "Colombo Fort": "Colombo", "Pettah": "Colombo", "Maradana": "Colombo",
    "Borella": "Colombo", "Narahenpita": "Colombo", "Kirulapone": "Colombo",
    "Nugegoda": "Colombo", "Maharagama": "Colombo", "Kotte": "Colombo",
    "Rajagiriya": "Colombo", "Battaramulla": "Colombo", "Dehiwala": "Colombo",
    "Mount Lavinia": "Colombo", "Ratmalana": "Colombo", "Moratuwa": "Colombo",
    "Piliyandala": "Colombo", "Kesbewa": "Colombo", "Homagama": "Colombo",
    "Kaduwela": "Colombo", "Kolonnawa": "Colombo", "Kelaniya": "Colombo",
    "Wellampitiya": "Colombo", "Angoda": "Colombo", "Mulleriyawa": "Colombo",
    "NHSL Colombo": "Colombo", "Colombo South TH": "Colombo",
    "Sri Jayewardenepura GH": "Colombo", "NIID Angoda": "Colombo", "BH Homagama": "Colombo",
    "Kadawatha": "Gampaha", "Ragama": "Gampaha", "Wattala": "Gampaha",
    "Ja-Ela": "Gampaha", "Negombo": "Gampaha", "Gampaha": "Gampaha",
    "Minuwangoda": "Gampaha", "Kiribathgoda": "Gampaha", "Biyagama": "Gampaha",
    "Delgoda": "Gampaha", "Veyangoda": "Gampaha", "Divulapitiya": "Gampaha",
    "Colombo North TH Ragama": "Gampaha", "DGH Gampaha": "Gampaha", "DGH Negombo": "Gampaha",
}


def get_node_district():
    return dict(NODE_DISTRICT)
