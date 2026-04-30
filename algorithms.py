"""
algorithms.py — Pathfinding algorithms for the traffic graph.

Provides:
    dijkstra(graph, start, end)
    astar(graph, start, end, coords)
    heuristic(a, b, coords)       — Haversine distance
    get_all_paths(graph, start, end, max_depth)
    compute_path_cost(path, graph)
"""

import heapq
import math


# ═══════════════════════════════════════════════
# HAVERSINE HEURISTIC
# ═══════════════════════════════════════════════
def heuristic(a, b, coords, avg_speed_kmh=80):
    """
    Haversine distance between two cities, converted to estimated hours.

    This is an admissible heuristic for A* (never overestimates)
    because the straight-line distance at max plausible speed
    is always ≤ actual travel time.

    Args:
        a, b: city names
        coords: {city: (lat, lon)}
        avg_speed_kmh: assumed max speed for converting km → hours

    Returns:
        float: estimated travel time in hours
    """
    if a not in coords or b not in coords:
        return 0

    lat1, lon1 = coords[a]
    lat2, lon2 = coords[b]

    R = 6371  # Earth's radius in km

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a_val = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a_val), math.sqrt(1 - a_val))

    distance_km = R * c
    return distance_km / avg_speed_kmh  # convert to hours


# ═══════════════════════════════════════════════
# DIJKSTRA'S ALGORITHM
# ═══════════════════════════════════════════════
def dijkstra(graph, start, end):
    """
    Standard Dijkstra shortest-path algorithm.

    Args:
        graph: {city: [(neighbor, cost), ...]}
        start, end: city names

    Returns:
        (total_cost, path_list)  — (inf, []) if unreachable
    """
    pq = [(0, start, [])]
    visited = set()

    while pq:
        cost, node, path = heapq.heappop(pq)

        if node in visited:
            continue
        visited.add(node)

        path = path + [node]

        if node == end:
            return cost, path

        for neighbor, weight in graph.get(node, []):
            if neighbor not in visited:
                heapq.heappush(pq, (cost + weight, neighbor, path))

    return float("inf"), []


# ═══════════════════════════════════════════════
# A* ALGORITHM
# ═══════════════════════════════════════════════
def astar(graph, start, end, coords):
    """
    A* shortest-path algorithm using Haversine heuristic.

    Explores fewer nodes than Dijkstra by prioritising nodes
    that are geographically closer to the destination.

    Args:
        graph: {city: [(neighbor, cost), ...]}
        start, end: city names
        coords: {city: (lat, lon)}

    Returns:
        (total_cost, path_list)  — (inf, []) if unreachable
    """
    # (f_score, g_score, node, path)
    pq = [(heuristic(start, end, coords), 0, start, [])]
    visited = set()

    while pq:
        f, g, node, path = heapq.heappop(pq)

        if node in visited:
            continue
        visited.add(node)

        path = path + [node]

        if node == end:
            return g, path

        for neighbor, weight in graph.get(node, []):
            if neighbor not in visited:
                new_g = g + weight
                new_f = new_g + heuristic(neighbor, end, coords)
                heapq.heappush(pq, (new_f, new_g, neighbor, path))

    return float("inf"), []


# ═══════════════════════════════════════════════
# ALL PATHS (DFS ENUMERATION)
# ═══════════════════════════════════════════════
def get_all_paths(graph, start, end, max_depth=8):
    """
    Enumerate all simple paths between start and end up to max_depth hops.

    Args:
        graph: {city: [(neighbor, cost), ...]}
        max_depth: maximum number of nodes in a path

    Returns:
        list of paths, where each path is a list of city names
    """
    paths = []

    def dfs(node, path):
        if len(path) > max_depth:
            return
        if node == end:
            paths.append(list(path))
            return
        for neighbor, _ in graph.get(node, []):
            if neighbor not in path:
                path.append(neighbor)
                dfs(neighbor, path)
                path.pop()

    dfs(start, [start])
    return paths


# ═══════════════════════════════════════════════
# PATH COST COMPUTATION
# ═══════════════════════════════════════════════
def compute_path_cost(path, graph):
    """
    Compute total travel cost along a given path.

    Args:
        path: list of city names
        graph: preprocessed {city: [(neighbor, cost), ...]}

    Returns:
        float: total cost (inf if any edge is missing)
    """
    total = 0.0

    for i in range(len(path) - 1):
        city = path[i]
        nxt = path[i + 1]

        found = False
        for neighbor, cost in graph.get(city, []):
            if neighbor == nxt:
                total += cost
                found = True
                break

        if not found:
            return float("inf")

    return round(total, 4)
