"""
heuristics.py — straight-line (haversine) heuristic, admissible by construction
because edges are always haversine x detour_factor (detour_factor > 1).
"""
import math
from typing import Callable

EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlam / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def make_straight_line_heuristic(graph) -> Callable[[str, str], float]:
    def h(node: str, goal: str) -> float:
        lat1, lon1 = graph.coords(node)
        lat2, lon2 = graph.coords(goal)
        return haversine_km(lat1, lon1, lat2, lon2)
    return h
