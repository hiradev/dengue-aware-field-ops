"""
search.py — BFS, Uniform-Cost Search, A*, implemented FROM SCRATCH.

No networkx, no library shortest-path calls. Mirrors the coursework notebook's
implementation exactly, so results are consistent between the graded artefact
and this demo. Independently maintained per the project's separation principle.
"""
import heapq
import math
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple


class Graph:
    def __init__(self, nodes: Dict[str, Tuple[float, float, str]], edges):
        self.nodes = nodes
        self.adj: Dict[str, List[Tuple[str, float]]] = {n: [] for n in nodes}
        for a, b, w in edges:
            self.adj[a].append((b, w))
            self.adj[b].append((a, w))

    def neighbours(self, node: str) -> List[Tuple[str, float]]:
        return sorted(self.adj[node])

    def coords(self, node: str) -> Tuple[float, float]:
        lat, lon, _ = self.nodes[node]
        return lat, lon

    def __len__(self):
        return len(self.nodes)


@dataclass
class SearchResult:
    algorithm: str
    start: str
    goal: str
    path: Optional[List[str]]
    cost: float
    nodes_expanded: int
    max_frontier: int
    runtime_ms: float
    expansion_order: List[str] = field(default_factory=list)

    @property
    def found(self) -> bool:
        return self.path is not None

    def as_dict(self) -> dict:
        return {
            "algorithm": self.algorithm, "start": self.start, "goal": self.goal,
            "path": self.path, "cost_km": round(self.cost, 3) if self.found else None,
            "nodes_expanded": self.nodes_expanded, "max_frontier": self.max_frontier,
            "runtime_ms": round(self.runtime_ms, 4),
            "expansion_order": self.expansion_order,
        }


def _reconstruct(parents, goal):
    path, node = [], goal
    while node is not None:
        path.append(node)
        node = parents[node]
    return list(reversed(path))


def _path_cost(graph: Graph, path: List[str]) -> float:
    total = 0.0
    for a, b in zip(path, path[1:]):
        total += next(w for (n, w) in graph.adj[a] if n == b)
    return total


def breadth_first_search(graph: Graph, start: str, goal: str) -> SearchResult:
    t0 = time.perf_counter()
    frontier = deque([start])
    parents = {start: None}
    expanded, order, max_frontier = 0, [], 1
    while frontier:
        max_frontier = max(max_frontier, len(frontier))
        node = frontier.popleft()
        expanded += 1
        order.append(node)
        if node == goal:
            path = _reconstruct(parents, goal)
            return SearchResult("BFS", start, goal, path, _path_cost(graph, path),
                                 expanded, max_frontier, (time.perf_counter() - t0) * 1000, order)
        for nb, _ in graph.neighbours(node):
            if nb not in parents:
                parents[nb] = node
                frontier.append(nb)
    return SearchResult("BFS", start, goal, None, math.inf, expanded, max_frontier,
                         (time.perf_counter() - t0) * 1000, order)


def uniform_cost_search(graph: Graph, start: str, goal: str) -> SearchResult:
    t0 = time.perf_counter()
    frontier = [(0.0, start)]
    g = {start: 0.0}
    parents = {start: None}
    explored = set()
    expanded, order, max_frontier = 0, [], 1
    while frontier:
        max_frontier = max(max_frontier, len(frontier))
        cost, node = heapq.heappop(frontier)
        if node in explored:
            continue
        explored.add(node)
        expanded += 1
        order.append(node)
        if node == goal:
            path = _reconstruct(parents, goal)
            return SearchResult("UCS", start, goal, path, cost, expanded, max_frontier,
                                 (time.perf_counter() - t0) * 1000, order)
        for nb, w in graph.neighbours(node):
            new_g = cost + w
            if nb not in g or new_g < g[nb]:
                g[nb] = new_g
                parents[nb] = node
                heapq.heappush(frontier, (new_g, nb))
    return SearchResult("UCS", start, goal, None, math.inf, expanded, max_frontier,
                         (time.perf_counter() - t0) * 1000, order)


def a_star_search(graph: Graph, start: str, goal: str,
                   heuristic: Callable[[str, str], float], label: str = "A*") -> SearchResult:
    t0 = time.perf_counter()
    h0 = heuristic(start, goal)
    frontier = [(h0, 0.0, start)]
    g = {start: 0.0}
    parents = {start: None}
    explored = set()
    expanded, order, max_frontier = 0, [], 1
    while frontier:
        max_frontier = max(max_frontier, len(frontier))
        f, cost, node = heapq.heappop(frontier)
        if node in explored:
            continue
        explored.add(node)
        expanded += 1
        order.append(node)
        if node == goal:
            path = _reconstruct(parents, goal)
            return SearchResult(label, start, goal, path, cost, expanded, max_frontier,
                                 (time.perf_counter() - t0) * 1000, order)
        for nb, w in graph.neighbours(node):
            new_g = cost + w
            if nb not in g or new_g < g[nb]:
                g[nb] = new_g
                parents[nb] = node
                heapq.heappush(frontier, (new_g + heuristic(nb, goal), new_g, nb))
    return SearchResult(label, start, goal, None, math.inf, expanded, max_frontier,
                         (time.perf_counter() - t0) * 1000, order)
