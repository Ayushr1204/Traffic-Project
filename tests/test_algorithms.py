"""
test_algorithms.py — Unit tests for algorithms.py

Covers:
    - Dijkstra's algorithm
    - A* algorithm with Haversine heuristic
    - Haversine heuristic function
    - All-paths DFS enumeration
    - Path cost computation
"""

import sys
import os
import math
import pytest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from algorithms import dijkstra, astar, heuristic, get_all_paths, compute_path_cost


# ═══════════════════════════════════════════════
# FIXTURES — Small synthetic graphs
# ═══════════════════════════════════════════════

def simple_graph():
    """
    A → B (cost 1)
    A → C (cost 4)
    B → C (cost 2)
    B → D (cost 6)
    C → D (cost 3)

    Shortest A→D: A→B→C→D = 6
    """
    return {
        "A": [("B", 1), ("C", 4)],
        "B": [("C", 2), ("D", 6)],
        "C": [("D", 3)],
        "D": [],
    }


def bidirectional_graph():
    """
    Small bidirectional graph mimicking city roads:

        Delhi ←→ Jaipur  (cost 3.5)
        Delhi ←→ Lucknow (cost 7.0)
        Jaipur ←→ Ahmedabad (cost 8.0)
        Lucknow ←→ Patna (cost 6.5)
        Ahmedabad ←→ Mumbai (cost 6.5)
        Patna ←→ Kolkata (cost 7.0)

    Shortest Delhi→Mumbai: Delhi→Jaipur→Ahmedabad→Mumbai = 18.0
    """
    return {
        "Delhi":     [("Jaipur", 3.5), ("Lucknow", 7.0)],
        "Jaipur":    [("Delhi", 3.5), ("Ahmedabad", 8.0)],
        "Lucknow":   [("Delhi", 7.0), ("Patna", 6.5)],
        "Ahmedabad": [("Jaipur", 8.0), ("Mumbai", 6.5)],
        "Patna":     [("Lucknow", 6.5), ("Kolkata", 7.0)],
        "Mumbai":    [("Ahmedabad", 6.5)],
        "Kolkata":   [("Patna", 7.0)],
    }


def coords_fixture():
    """Approximate lat/lon for the bidirectional graph cities."""
    return {
        "Delhi":     (28.61, 77.23),
        "Jaipur":    (26.90, 75.80),
        "Lucknow":   (26.85, 80.95),
        "Ahmedabad": (23.02, 72.57),
        "Patna":     (25.61, 85.14),
        "Mumbai":    (19.08, 72.88),
        "Kolkata":   (22.57, 88.37),
    }


# ═══════════════════════════════════════════════
# DIJKSTRA TESTS
# ═══════════════════════════════════════════════

class TestDijkstra:
    def test_shortest_path_simple(self):
        g = simple_graph()
        cost, path = dijkstra(g, "A", "D")
        assert path == ["A", "B", "C", "D"]
        assert cost == 6

    def test_direct_neighbor(self):
        g = simple_graph()
        cost, path = dijkstra(g, "A", "B")
        assert path == ["A", "B"]
        assert cost == 1

    def test_start_equals_end(self):
        g = simple_graph()
        cost, path = dijkstra(g, "A", "A")
        assert cost == 0
        assert path == ["A"]

    def test_unreachable(self):
        g = simple_graph()
        cost, path = dijkstra(g, "D", "A")  # D has no outgoing edges
        assert cost == float("inf")
        assert path == []

    def test_bidirectional(self):
        g = bidirectional_graph()
        cost, path = dijkstra(g, "Delhi", "Mumbai")
        assert path == ["Delhi", "Jaipur", "Ahmedabad", "Mumbai"]
        assert cost == 18.0

    def test_unknown_node(self):
        g = simple_graph()
        cost, path = dijkstra(g, "A", "Z")
        assert cost == float("inf")
        assert path == []


# ═══════════════════════════════════════════════
# A* TESTS
# ═══════════════════════════════════════════════

class TestAStar:
    def test_same_result_as_dijkstra(self):
        g = bidirectional_graph()
        c = coords_fixture()
        cost_a, path_a = astar(g, "Delhi", "Mumbai", c)
        cost_d, path_d = dijkstra(g, "Delhi", "Mumbai")
        assert cost_a == cost_d
        assert path_a == path_d

    def test_start_equals_end(self):
        g = bidirectional_graph()
        c = coords_fixture()
        cost, path = astar(g, "Delhi", "Delhi", c)
        assert cost == 0
        assert path == ["Delhi"]

    def test_unreachable(self):
        g = {"X": []}
        c = {"X": (0, 0), "Y": (1, 1)}
        cost, path = astar(g, "X", "Y", c)
        assert cost == float("inf")
        assert path == []

    def test_long_path(self):
        """Delhi → Kolkata should go through Lucknow → Patna."""
        g = bidirectional_graph()
        c = coords_fixture()
        cost, path = astar(g, "Delhi", "Kolkata", c)
        assert "Lucknow" in path
        assert "Patna" in path
        assert cost == pytest.approx(20.5)


# ═══════════════════════════════════════════════
# HEURISTIC TESTS
# ═══════════════════════════════════════════════

class TestHeuristic:
    def test_same_city_is_zero(self):
        c = coords_fixture()
        assert heuristic("Delhi", "Delhi", c) == 0.0

    def test_positive_distance(self):
        c = coords_fixture()
        h = heuristic("Delhi", "Mumbai", c)
        assert h > 0

    def test_admissible(self):
        """
        Heuristic should never overestimate actual travel time.
        At avg_speed_kmh=80, straight-line distance ÷ 80 < actual road time.
        """
        c = coords_fixture()
        g = bidirectional_graph()
        cost, _ = dijkstra(g, "Delhi", "Mumbai")
        h = heuristic("Delhi", "Mumbai", c, avg_speed_kmh=80)
        assert h <= cost, f"Heuristic {h} exceeds actual cost {cost} — not admissible"

    def test_missing_coords_returns_zero(self):
        c = coords_fixture()
        assert heuristic("Delhi", "FakeCity", c) == 0

    def test_symmetry(self):
        c = coords_fixture()
        h1 = heuristic("Delhi", "Mumbai", c)
        h2 = heuristic("Mumbai", "Delhi", c)
        assert h1 == pytest.approx(h2)


# ═══════════════════════════════════════════════
# ALL PATHS TESTS
# ═══════════════════════════════════════════════

class TestGetAllPaths:
    def test_finds_all_simple(self):
        g = simple_graph()
        paths = get_all_paths(g, "A", "D", max_depth=10)
        assert len(paths) >= 2  # A→B→C→D and A→C→D and A→B→D
        assert ["A", "B", "C", "D"] in paths
        assert ["A", "C", "D"] in paths

    def test_depth_limit(self):
        g = simple_graph()
        paths = get_all_paths(g, "A", "D", max_depth=3)
        # max_depth=3 means at most 3 nodes, so only A→C→D (3 nodes)
        for p in paths:
            assert len(p) <= 3

    def test_no_path(self):
        g = simple_graph()
        paths = get_all_paths(g, "D", "A", max_depth=10)
        assert paths == []

    def test_same_node(self):
        g = simple_graph()
        paths = get_all_paths(g, "A", "A", max_depth=5)
        assert [["A"]] == paths


# ═══════════════════════════════════════════════
# COMPUTE PATH COST TESTS
# ═══════════════════════════════════════════════

class TestComputePathCost:
    def test_valid_path(self):
        g = simple_graph()
        cost = compute_path_cost(["A", "B", "C", "D"], g)
        assert cost == 6

    def test_single_node(self):
        g = simple_graph()
        cost = compute_path_cost(["A"], g)
        assert cost == 0.0

    def test_broken_edge(self):
        g = simple_graph()
        cost = compute_path_cost(["A", "D"], g)  # no direct A→D edge
        assert cost == float("inf")

    def test_empty_path(self):
        g = simple_graph()
        cost = compute_path_cost([], g)
        assert cost == 0.0

    def test_matches_dijkstra(self):
        g = bidirectional_graph()
        cost_d, path_d = dijkstra(g, "Delhi", "Mumbai")
        cost_c = compute_path_cost(path_d, g)
        assert cost_c == pytest.approx(cost_d)
