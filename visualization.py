"""
visualization.py — Plotly-based visualizations for the traffic graph.

Provides:
    plotly_network_graph(path, graph, coords, traffic_details)
    plotly_map(path, coords)
    plotly_time_analysis(path, raw_graph, all_traffic, coords)
"""

import numpy as np
import plotly.graph_objects as go
from algorithms import compute_path_cost
from graph_builder import preprocess_graph


# ═══════════════════════════════════════════════
# COLOUR PALETTE
# ═══════════════════════════════════════════════
_BG        = "#080b14"
_EDGE_DIM  = "rgba(100, 130, 200, 0.12)"
_EDGE_PATH = "#7c9cff"
_NODE_DEFAULT = "#3b6cf6"
_NODE_PATH    = "#f59e0b"
_NODE_START   = "#22c55e"
_NODE_END     = "#ef4444"
_TEXT_COLOR   = "#cbd5e1"


# ═══════════════════════════════════════════════
# NETWORK GRAPH (GEO-POSITIONED)
# ═══════════════════════════════════════════════
def plotly_network_graph(path, raw_graph, coords, traffic_details=None):
    """
    Interactive Plotly scatter plot of the full road network with the
    shortest path highlighted.

    Nodes are positioned by their real longitude (x) and latitude (y).

    Args:
        path: list of city names on the shortest route
        raw_graph: {city: [(neighbor, road_id), ...]}  — raw from Neo4j
        coords: {city: (lat, lon)}
        traffic_details: {road_id: {avg_speed, congestion_level, travel_time}} or None
    """
    path_set = set(path)
    path_edges = set()
    for i in range(len(path) - 1):
        path_edges.add((path[i], path[i + 1]))
        path_edges.add((path[i + 1], path[i]))

    # ---- Background edges ----
    bg_edge_x, bg_edge_y = [], []
    # ---- Path edges ----
    path_edge_x, path_edge_y = [], []

    seen = set()
    for city in raw_graph:
        for neighbor, road_id in raw_graph[city]:
            edge_key = tuple(sorted([city, neighbor]))
            if edge_key in seen:
                continue
            seen.add(edge_key)

            if city not in coords or neighbor not in coords:
                continue

            x0, y0 = coords[city][1], coords[city][0]   # lon, lat
            x1, y1 = coords[neighbor][1], coords[neighbor][0]

            if (city, neighbor) in path_edges or (neighbor, city) in path_edges:
                path_edge_x += [x0, x1, None]
                path_edge_y += [y0, y1, None]
            else:
                bg_edge_x += [x0, x1, None]
                bg_edge_y += [y0, y1, None]

    traces = []

    # Background edges
    traces.append(go.Scatter(
        x=bg_edge_x, y=bg_edge_y,
        mode="lines",
        line=dict(width=1, color=_EDGE_DIM),
        hoverinfo="none",
        showlegend=False,
    ))

    # Path edges (glowing effect via wider semi-transparent line + solid line)
    if path_edge_x:
        # Outer glow layer
        traces.append(go.Scatter(
            x=path_edge_x, y=path_edge_y,
            mode="lines",
            line=dict(width=16, color="rgba(124, 156, 255, 0.08)"),
            hoverinfo="none",
            showlegend=False,
        ))
        # Mid glow layer
        traces.append(go.Scatter(
            x=path_edge_x, y=path_edge_y,
            mode="lines",
            line=dict(width=8, color="rgba(124, 156, 255, 0.18)"),
            hoverinfo="none",
            showlegend=False,
        ))
        # Core line
        traces.append(go.Scatter(
            x=path_edge_x, y=path_edge_y,
            mode="lines",
            line=dict(width=3.5, color=_EDGE_PATH),
            hoverinfo="none",
            name="Shortest Path",
        ))

    # ---- Nodes ----
    node_x, node_y, node_colors, node_sizes, node_text, hover_text = [], [], [], [], [], []

    all_cities = set(raw_graph.keys())
    for city in all_cities:
        if city not in coords:
            continue

        lat, lon = coords[city]
        node_x.append(lon)
        node_y.append(lat)
        node_text.append(city)

        if path and city == path[0]:
            node_colors.append(_NODE_START)
            node_sizes.append(22)
            hover_text.append(f"<b>{city}</b> (START)")
        elif path and city == path[-1]:
            node_colors.append(_NODE_END)
            node_sizes.append(22)
            hover_text.append(f"<b>{city}</b> (END)")
        elif city in path_set:
            node_colors.append(_NODE_PATH)
            node_sizes.append(18)
            hover_text.append(f"<b>{city}</b> (on route)")
        else:
            node_colors.append(_NODE_DEFAULT)
            node_sizes.append(14)
            hover_text.append(f"<b>{city}</b>")

    traces.append(go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        text=node_text,
        textposition="top center",
        textfont=dict(size=11, color=_TEXT_COLOR, family="Inter, sans-serif"),
        hovertext=hover_text,
        hoverinfo="text",
        marker=dict(
            size=node_sizes,
            color=node_colors,
            line=dict(width=2, color="rgba(255,255,255,0.5)"),
            opacity=0.95,
        ),
        showlegend=False,
    ))

    # Pulsing glow rings for start/end nodes
    if path and len(path) >= 2:
        for city_name, ring_color in [(path[0], _NODE_START), (path[-1], _NODE_END)]:
            if city_name in coords:
                lat, lon = coords[city_name]
                traces.append(go.Scatter(
                    x=[lon], y=[lat],
                    mode="markers",
                    marker=dict(size=36, color="rgba(0,0,0,0)",
                                line=dict(width=2, color=ring_color)),
                    hoverinfo="none", showlegend=False,
                ))

    fig = go.Figure(data=traces)
    fig.update_layout(
        height=700,
        showlegend=True,
        legend=dict(font=dict(color=_TEXT_COLOR), bgcolor="rgba(0,0,0,0.3)"),
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        font=dict(color=_TEXT_COLOR, family="Inter, sans-serif"),
        xaxis=dict(
            showgrid=False, zeroline=False, showticklabels=False,
            title="Longitude",
        ),
        yaxis=dict(
            showgrid=False, zeroline=False, showticklabels=False,
            title="Latitude",
            scaleanchor="x", scaleratio=1,
        ),
        margin=dict(l=20, r=20, t=40, b=20),
    )

    return fig


# ═══════════════════════════════════════════════
# MAP VISUALIZATION (OPENSTREETMAP)
# ═══════════════════════════════════════════════
def plotly_map(path, coords, all_cities=None):
    """
    Scattermapbox plot showing the route on a real map of India.

    Args:
        path: list of city names
        coords: {city: (lat, lon)}
        all_cities: optional set of all city names to show as markers
    """
    fig = go.Figure()

    # All city markers (if provided)
    if all_cities:
        all_lats, all_lons, all_names = [], [], []
        for city in all_cities:
            if city in coords:
                lat, lon = coords[city]
                all_lats.append(lat)
                all_lons.append(lon)
                all_names.append(city)

        fig.add_trace(go.Scattermapbox(
            lat=all_lats, lon=all_lons,
            mode="markers+text",
            text=all_names,
            textposition="top center",
            marker=dict(size=8, color=_NODE_DEFAULT, opacity=0.6),
            name="All Cities",
            textfont=dict(size=10, color="#94a3b8"),
        ))

    # Route path
    path_lats, path_lons, path_names = [], [], []
    for city in path:
        if city in coords:
            lat, lon = coords[city]
            path_lats.append(lat)
            path_lons.append(lon)
            path_names.append(city)

    if path_lats:
        # Route line
        fig.add_trace(go.Scattermapbox(
            lat=path_lats, lon=path_lons,
            mode="lines",
            line=dict(width=4, color=_EDGE_PATH),
            name="Route",
        ))

        # Route city markers
        marker_colors = []
        for i, city in enumerate(path_names):
            if i == 0:
                marker_colors.append(_NODE_START)
            elif i == len(path_names) - 1:
                marker_colors.append(_NODE_END)
            else:
                marker_colors.append(_NODE_PATH)

        fig.add_trace(go.Scattermapbox(
            lat=path_lats, lon=path_lons,
            mode="markers+text",
            text=path_names,
            textposition="top right",
            marker=dict(size=14, color=marker_colors),
            name="Route Cities",
            textfont=dict(size=12, color="white"),
        ))

        center_lat = sum(path_lats) / len(path_lats)
        center_lon = sum(path_lons) / len(path_lons)
    else:
        center_lat, center_lon = 22.0, 79.0  # center of India

    fig.update_layout(
        mapbox=dict(
            style="carto-darkmatter",
            center=dict(lat=center_lat, lon=center_lon),
            zoom=4.2,
        ),
        height=600,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor=_BG,
        font=dict(color=_TEXT_COLOR),
        legend=dict(
            font=dict(color=_TEXT_COLOR),
            bgcolor="rgba(0,0,0,0.5)",
            x=0.01, y=0.99,
        ),
    )

    return fig


# ═══════════════════════════════════════════════
# TIME-OF-DAY ANALYSIS CHART
# ═══════════════════════════════════════════════
def plotly_time_analysis(path, raw_graph, all_traffic, coords):
    """
    Bar + line chart showing how the best route's travel time varies
    across all 8 timestamps.

    Args:
        path: list of city names (the best route at the selected hour)
        raw_graph: raw graph from Neo4j (before preprocessing)
        all_traffic: {hour: {road_id: travel_time}} for all hours
        coords: {city: (lat, lon)}

    Returns:
        plotly Figure
    """
    hours = sorted(all_traffic.keys())
    costs = []

    for h in hours:
        processed = preprocess_graph(raw_graph, all_traffic[h])
        cost = compute_path_cost(path, processed)
        costs.append(cost if cost != float("inf") else None)

    hour_labels = [f"{h:02d}:00" for h in hours]

    # Colour bars by intensity
    colors = []
    valid_costs = [c for c in costs if c is not None]
    if valid_costs:
        min_c, max_c = min(valid_costs), max(valid_costs)
        for c in costs:
            if c is None:
                colors.append("rgba(100,100,100,0.3)")
            else:
                # Interpolate green → yellow → red
                t = (c - min_c) / (max_c - min_c + 0.001)
                r = int(34 + t * 221)
                g = int(197 - t * 130)
                b = int(94 - t * 60)
                colors.append(f"rgb({r},{g},{b})")
    else:
        colors = ["rgba(100,100,100,0.3)"] * len(hours)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=hour_labels,
        y=costs,
        marker=dict(
            color=colors,
            line=dict(width=1, color="rgba(255,255,255,0.15)"),
            cornerradius=4,
        ),
        name="Travel Time (hrs)",
        text=[f"{c:.2f}h" if c else "N/A" for c in costs],
        textposition="outside",
        textfont=dict(color=_TEXT_COLOR, size=11),
    ))

    fig.add_trace(go.Scatter(
        x=hour_labels,
        y=costs,
        mode="lines+markers",
        line=dict(color="#f59e0b", width=2.5, shape="spline"),
        marker=dict(size=9, color="#f59e0b",
                    line=dict(width=2, color="rgba(245,158,11,0.3)")),
        name="Trend",
        fill="tozeroy",
        fillcolor="rgba(245,158,11,0.05)",
    ))

    fig.update_layout(
        height=400,
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        font=dict(color=_TEXT_COLOR, family="Inter, sans-serif"),
        xaxis=dict(title="Time of Day", showgrid=False),
        yaxis=dict(title="Travel Time (hours)", showgrid=True,
                   gridcolor="rgba(255,255,255,0.05)"),
        legend=dict(font=dict(color=_TEXT_COLOR), bgcolor="rgba(0,0,0,0.3)"),
        margin=dict(l=50, r=20, t=30, b=50),
        bargap=0.3,
    )

    return fig


# ═══════════════════════════════════════════════
# CONGESTION HEATMAP
# ═══════════════════════════════════════════════
def plotly_congestion_heatmap(path, raw_graph, all_traffic_details):
    """
    Heatmap showing congestion levels for each road segment on the path
    across all 8 timestamps.

    Args:
        path: list of city names
        raw_graph: {city: [(neighbor, road_id), ...]}
        all_traffic_details: {hour: {road_id: {avg_speed, congestion_level, travel_time}}}

    Returns:
        plotly Figure
    """
    if len(path) < 2:
        return go.Figure()

    # Get road segments on the path
    segments = []
    road_ids = []
    for i in range(len(path) - 1):
        seg = f"{path[i]} → {path[i+1]}"
        segments.append(seg)
        # Find road_id
        rid = None
        for neighbor, road_id in raw_graph.get(path[i], []):
            if neighbor == path[i + 1]:
                rid = road_id
                break
        road_ids.append(rid)

    hours = sorted(all_traffic_details.keys())
    hour_labels = [f"{h:02d}:00" for h in hours]

    # Build heatmap matrix
    z = []
    for rid in road_ids:
        row = []
        for h in hours:
            if rid and rid in all_traffic_details.get(h, {}):
                row.append(all_traffic_details[h][rid]["congestion_level"])
            else:
                row.append(0)
        z.append(row)

    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=hour_labels,
        y=segments,
        colorscale=[
            [0.0, "#22c55e"],
            [0.3, "#84cc16"],
            [0.5, "#eab308"],
            [0.7, "#f97316"],
            [1.0, "#ef4444"],
        ],
        colorbar=dict(title="Congestion", tickformat=".0%"),
        text=[[f"{v:.0%}" for v in row] for row in z],
        texttemplate="%{text}",
        textfont=dict(size=11),
    ))

    fig.update_layout(
        height=max(300, len(segments) * 50 + 100),
        plot_bgcolor=_BG,
        paper_bgcolor=_BG,
        font=dict(color=_TEXT_COLOR, family="Inter, sans-serif"),
        xaxis=dict(title="Time of Day", side="top"),
        yaxis=dict(autorange="reversed"),
        margin=dict(l=150, r=20, t=50, b=30),
    )

    return fig
