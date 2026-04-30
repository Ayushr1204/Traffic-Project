"""
test_graph_builder.py — Unit tests for graph_builder.py

Covers:
    - preprocess_graph: merging weights, handling parallel edges
    - get_road_id_between: road lookup between adjacent cities
"""

import sys
import os
import pytest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from graph_builder import preprocess_graph, get_road_id_between


# ═══════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════

def raw_graph_simple():
    """
    A→B via R001, A→C via R002, B→C via R003
    """
    return {
        "A": [("B", "R001"), ("C", "R002")],
        "B": [("C", "R003")],
        "C": [],
    }


def raw_graph_parallel_edges():
    """
    A→B via R001 AND R004 (parallel roads).
    """
    return {
        "A": [("B", "R001"), ("B", "R004"), ("C", "R002")],
        "B": [],
        "C": [],
    }


def weights_simple():
    return {
        "R001": 3.5,
        "R002": 7.0,
        "R003": 2.0,
    }


def weights_parallel():
    return {
        "R001": 5.0,
        "R004": 3.0,   # faster parallel road
        "R002": 7.0,
    }


# ═══════════════════════════════════════════════
# PREPROCESS_GRAPH TESTS
# ═══════════════════════════════════════════════

class TestPreprocessGraph:
    def test_basic_merge(self):
        """Weights are correctly applied to graph edges."""
        g = preprocess_graph(raw_graph_simple(), weights_simple())
        # A should have edges to B and C
        neighbors = {n: c for n, c in g["A"]}
        assert neighbors["B"] == 3.5
        assert neighbors["C"] == 7.0

    def test_b_to_c(self):
        g = preprocess_graph(raw_graph_simple(), weights_simple())
        neighbors = {n: c for n, c in g["B"]}
        assert neighbors["C"] == 2.0

    def test_empty_node(self):
        """Node with no outgoing edges should have empty list."""
        g = preprocess_graph(raw_graph_simple(), weights_simple())
        assert g["C"] == []

    def test_parallel_edges_picks_lowest(self):
        """When two roads connect the same pair, pick the cheaper one."""
        g = preprocess_graph(raw_graph_parallel_edges(), weights_parallel())
        neighbors = {n: c for n, c in g["A"]}
        # R004 (cost 3.0) should win over R001 (cost 5.0)
        assert neighbors["B"] == 3.0

    def test_missing_weight_drops_edge(self):
        """If a road_id has no weight data, that edge is dropped."""
        partial_weights = {"R001": 3.5}  # R002, R003 missing
        g = preprocess_graph(raw_graph_simple(), partial_weights)
        neighbors = {n: c for n, c in g["A"]}
        assert "B" in neighbors
        assert "C" not in neighbors  # R002 missing from weights

    def test_empty_graph(self):
        g = preprocess_graph({}, {})
        assert g == {}

    def test_empty_weights(self):
        """All edges should be dropped if no weights available."""
        g = preprocess_graph(raw_graph_simple(), {})
        for city in g:
            assert g[city] == []


# ═══════════════════════════════════════════════
# GET_ROAD_ID_BETWEEN TESTS
# ═══════════════════════════════════════════════

class TestGetRoadIdBetween:
    def test_existing_road(self):
        g = raw_graph_simple()
        assert get_road_id_between(g, "A", "B") == "R001"

    def test_another_road(self):
        g = raw_graph_simple()
        assert get_road_id_between(g, "A", "C") == "R002"

    def test_no_road(self):
        g = raw_graph_simple()
        assert get_road_id_between(g, "A", "D") is None

    def test_reverse_direction_not_found(self):
        """Raw graph is directed — reverse lookup should return None."""
        g = raw_graph_simple()
        # B→A doesn't exist in this graph
        assert get_road_id_between(g, "B", "A") is None

    def test_missing_city(self):
        g = raw_graph_simple()
        assert get_road_id_between(g, "Z", "A") is None

    def test_parallel_returns_first(self):
        """For parallel edges, returns the first matching road_id."""
        g = raw_graph_parallel_edges()
        result = get_road_id_between(g, "A", "B")
        assert result in ("R001", "R004")  # either is acceptable
