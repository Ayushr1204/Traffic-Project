"""
app.py — Streamlit dashboard for interactive traffic route analysis.

Run with:
    streamlit run app.py
"""

import streamlit as st
import time
import base64
import os

from graph_builder import (
    build_graph,
    load_weights,
    load_coordinates,
    load_traffic_details,
    load_all_traffic,
    preprocess_graph,
    get_road_id_between,
)
from algorithms import dijkstra, astar, get_all_paths, compute_path_cost
from visualization import (
    plotly_network_graph,
    plotly_map,
    plotly_time_analysis,
    plotly_congestion_heatmap,
)


# ═══════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════
# Load logo
_LOGO_PATH = os.path.join(os.path.dirname(__file__), "logo.png")
if os.path.exists(_LOGO_PATH):
    _LOGO_B64 = base64.b64encode(open(_LOGO_PATH, "rb").read()).decode()
else:
    _LOGO_B64 = None

st.set_page_config(
    page_title="Next-Gen Traffic Route Analyzer",
    page_icon=_LOGO_PATH if os.path.exists(_LOGO_PATH) else "🛣️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════
# CUSTOM CSS — Premium Dark Theme
# ═══════════════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* ── Global ──────────────────────────────── */
    .stApp {
        font-family: 'Inter', sans-serif;
        background: #080b14;
        background-image:
            radial-gradient(ellipse at 20% 50%, rgba(59,130,246,0.04) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 20%, rgba(139,92,246,0.04) 0%, transparent 50%),
            radial-gradient(ellipse at 50% 80%, rgba(245,158,11,0.03) 0%, transparent 50%);
    }

    /* ── Animated Header ─────────────────────── */
    .main-header {
        background: linear-gradient(135deg, #0f1b2d 0%, #1a1040 40%, #0d2137 70%, #0a0f1a 100%);
        border-radius: 20px;
        padding: 2.2rem 2.8rem;
        margin-bottom: 1.8rem;
        border: 1px solid rgba(99, 140, 255, 0.12);
        box-shadow:
            0 4px 24px rgba(0,0,0,0.4),
            inset 0 1px 0 rgba(255,255,255,0.04);
        position: relative;
        overflow: hidden;
    }
    .main-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: conic-gradient(
            from 0deg,
            transparent 0deg,
            rgba(99, 140, 255, 0.03) 60deg,
            transparent 120deg
        );
        animation: headerShimmer 8s linear infinite;
    }
    @keyframes headerShimmer {
        to { transform: rotate(360deg); }
    }
    .main-header h1 {
        position: relative;
        color: #f1f5f9;
        font-size: 2.1rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
        background: linear-gradient(135deg, #e2e8f0, #94a3b8, #e2e8f0);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: textGradient 4s ease infinite;
    }
    @keyframes textGradient {
        0%, 100% { background-position: 0% center; }
        50% { background-position: 200% center; }
    }
    .main-header p {
        position: relative;
        color: #64748b;
        font-size: 0.95rem;
        margin: 0.6rem 0 0 0;
        font-weight: 400;
        letter-spacing: 0.3px;
    }
    .main-header .badge {
        display: inline-block;
        background: rgba(99, 140, 255, 0.1);
        border: 1px solid rgba(99, 140, 255, 0.2);
        color: #7c9cff;
        font-size: 0.7rem;
        font-weight: 600;
        padding: 0.25rem 0.7rem;
        border-radius: 20px;
        margin-left: 0.5rem;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        vertical-align: middle;
        animation: badgePulse 2s ease-in-out infinite;
    }
    .main-header .badge::before {
        content: '';
        display: inline-block;
        width: 6px; height: 6px;
        background: #22c55e;
        border-radius: 50%;
        margin-right: 6px;
        vertical-align: middle;
        box-shadow: 0 0 6px #22c55e;
        animation: liveDot 1.5s ease-in-out infinite;
    }
    @keyframes badgePulse {
        0%,100% { box-shadow: 0 0 0 0 rgba(99,140,255,0); }
        50% { box-shadow: 0 0 12px 2px rgba(99,140,255,0.15); }
    }
    @keyframes liveDot {
        0%,100% { opacity:1; } 50% { opacity:0.3; }
    }

    /* ── Metric Cards ────────────────────────── */
    .metric-card {
        background: linear-gradient(160deg, rgba(30,41,59,0.7), rgba(15,23,42,0.9));
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px;
        padding: 1.4rem 1.2rem;
        text-align: center;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    .metric-card:hover {
        transform: translateY(-4px) scale(1.02);
        border-color: rgba(255,255,255,0.15);
        box-shadow: 0 8px 32px rgba(0,0,0,0.4), 0 0 20px rgba(99,140,255,0.08);
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        border-radius: 16px 16px 0 0;
    }
    .metric-card.mc-time::before { background: linear-gradient(90deg, #3b82f6, #60a5fa); }
    .metric-card.mc-stops::before { background: linear-gradient(90deg, #8b5cf6, #a78bfa); }
    .metric-card.mc-algo::before { background: linear-gradient(90deg, #10b981, #34d399); }
    .metric-card.mc-hour::before { background: linear-gradient(90deg, #f59e0b, #fbbf24); }

    .metric-card .icon {
        font-size: 1.6rem;
        margin-bottom: 0.3rem;
    }
    .metric-card .label {
        color: #64748b;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }
    .metric-card .value {
        color: #f1f5f9;
        font-size: 1.9rem;
        font-weight: 800;
        line-height: 1.1;
    }
    .metric-card .unit {
        color: #475569;
        font-size: 0.78rem;
        margin-top: 0.3rem;
        font-weight: 500;
    }

    /* ── Route Path Display ──────────────────── */
    .route-display {
        background: linear-gradient(160deg, rgba(30,41,59,0.6), rgba(15,23,42,0.85));
        backdrop-filter: blur(12px);
        border: 1px solid rgba(99, 140, 255, 0.1);
        border-radius: 16px;
        padding: 1.4rem 1.8rem;
        margin: 1.2rem 0;
        position: relative;
        overflow: hidden;
    }
    .route-display::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6, #f59e0b, #ef4444);
        background-size: 300% 100%;
        animation: routeGradient 3s ease infinite;
    }
    @keyframes routeGradient {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    .route-display .route-label {
        color: #64748b;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 600;
        margin-bottom: 0.6rem;
    }
    .route-display .route-path {
        color: #e2e8f0;
        font-size: 1.05rem;
        font-weight: 500;
        line-height: 2.2;
    }
    .route-display .city-node {
        display: inline-block;
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.2);
        padding: 0.2rem 0.7rem;
        border-radius: 8px;
        font-weight: 600;
        color: #93c5fd;
        font-size: 0.9rem;
        transition: all 0.25s cubic-bezier(0.4,0,0.2,1);
        animation: nodeAppear 0.4s ease backwards;
    }
    .route-display .city-node:hover {
        background: rgba(59, 130, 246, 0.25);
        transform: translateY(-2px) scale(1.08);
        box-shadow: 0 4px 12px rgba(59,130,246,0.2);
    }
    .route-display .city-node.start {
        background: rgba(34, 197, 94, 0.15);
        border-color: rgba(34, 197, 94, 0.3);
        color: #86efac;
        box-shadow: 0 0 12px rgba(34,197,94,0.15);
    }
    .route-display .city-node.end {
        background: rgba(239, 68, 68, 0.15);
        border-color: rgba(239, 68, 68, 0.3);
        color: #fca5a5;
        box-shadow: 0 0 12px rgba(239,68,68,0.15);
    }
    .route-display .arrow {
        color: #475569;
        margin: 0 0.2rem;
        font-size: 1rem;
        animation: arrowSlide 0.3s ease backwards;
    }
    @keyframes nodeAppear {
        from { opacity:0; transform: translateY(8px) scale(0.9); }
        to { opacity:1; transform: translateY(0) scale(1); }
    }
    @keyframes arrowSlide {
        from { opacity:0; transform: translateX(-6px); }
        to { opacity:1; transform: translateX(0); }
    }

    /* ── Section Headers ─────────────────────── */
    .section-header {
        color: #e2e8f0;
        font-size: 1.15rem;
        font-weight: 700;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.6rem;
        border-bottom: 1px solid rgba(255,255,255,0.06);
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* ── Sidebar ─────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0f1e 0%, #111827 50%, #0a0f1e 100%);
        border-right: 1px solid rgba(255,255,255,0.04);
    }
    section[data-testid="stSidebar"] .stMarkdown h2 {
        background: linear-gradient(135deg, #e2e8f0, #94a3b8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        font-size: 1.3rem;
    }

    /* ── Tabs Styling ────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: rgba(15,23,42,0.5);
        border-radius: 12px;
        padding: 4px;
        border: 1px solid rgba(255,255,255,0.04);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #94a3b8;
        font-weight: 500;
        font-size: 0.85rem;
        padding: 0.5rem 1rem;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(59, 130, 246, 0.15) !important;
        color: #93c5fd !important;
        border: 1px solid rgba(59, 130, 246, 0.2);
    }

    /* ── Data Table ──────────────────────────── */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.06);
    }

    /* ── Primary Button Glow ─────────────────── */
    .stButton > button[kind="primary"],
    .stButton > button {
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        box-shadow: 0 0 20px rgba(59,130,246,0.3) !important;
        transform: translateY(-1px);
    }

    /* ── Alt Route Row ───────────────────────── */
    .alt-route-row {
        background: linear-gradient(160deg, rgba(30,41,59,0.4), rgba(15,23,42,0.6));
        border: 1px solid rgba(255,255,255,0.04);
        border-radius: 12px;
        padding: 0.8rem 1.2rem;
        margin-bottom: 0.5rem;
        transition: all 0.25s ease;
        display: flex;
        align-items: center;
    }
    .alt-route-row:hover {
        border-color: rgba(99,140,255,0.15);
        background: linear-gradient(160deg, rgba(30,41,59,0.6), rgba(15,23,42,0.8));
        transform: translateX(4px);
    }
    .alt-route-row .rank-badge {
        background: rgba(99,140,255,0.12);
        border: 1px solid rgba(99,140,255,0.2);
        color: #93c5fd;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 0.2rem 0.5rem;
        border-radius: 6px;
        margin-right: 1rem;
        min-width: 28px;
        text-align: center;
    }
    .alt-route-row .route-text {
        flex: 2;
        color: #cbd5e1;
        font-size: 0.85rem;
    }
    .alt-route-row .eta-text {
        color: #22c55e;
        font-weight: 600;
        font-size: 0.9rem;
        min-width: 80px;
        text-align: right;
    }
    .alt-route-row .diff-text {
        color: #94a3b8;
        font-size: 0.78rem;
        min-width: 80px;
        text-align: right;
    }
    .alt-route-row .diff-text.slower { color: #f87171; }
    .alt-route-row .diff-text.faster { color: #34d399; }

    /* ── Footer Stats Bar ────────────────────── */
    .footer-stats {
        background: linear-gradient(160deg, rgba(30,41,59,0.4), rgba(15,23,42,0.6));
        border: 1px solid rgba(255,255,255,0.04);
        border-radius: 12px;
        padding: 0.8rem 1.5rem;
        margin-top: 2rem;
        display: flex;
        justify-content: space-around;
        align-items: center;
    }
    .footer-stat {
        text-align: center;
    }
    .footer-stat .fs-val {
        color: #7c9cff;
        font-size: 1.1rem;
        font-weight: 700;
    }
    .footer-stat .fs-lbl {
        color: #475569;
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* ── Landing Card ────────────────────────── */
    .landing-card {
        background: linear-gradient(160deg, rgba(30,41,59,0.5), rgba(15,23,42,0.7));
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 16px;
        padding: 2.5rem;
        text-align: center;
        margin: 2rem 0;
    }
    .landing-card .landing-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    .landing-card h3 {
        color: #e2e8f0;
        font-size: 1.3rem;
        font-weight: 700;
        margin: 0 0 0.5rem 0;
    }
    .landing-card p {
        color: #64748b;
        font-size: 0.9rem;
        margin: 0;
    }

    /* ── Stats Row (landing page) ────────────── */
    .stats-row {
        display: flex;
        justify-content: center;
        gap: 2rem;
        margin-top: 1.5rem;
    }
    .stat-item {
        text-align: center;
    }
    .stat-item .stat-value {
        color: #7c9cff;
        font-size: 1.5rem;
        font-weight: 800;
    }
    .stat-item .stat-label {
        color: #475569;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }

    /* ── Scrollbar ───────────────────────────── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: rgba(99,140,255,0.2);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover { background: rgba(99,140,255,0.35); }

    /* ── Hide default Streamlit chrome ────────── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════
# CACHED DATA LOADING
# ═══════════════════════════════════════════════
@st.cache_data(ttl=300)
def cached_build_graph():
    return build_graph()

@st.cache_data(ttl=300)
def cached_load_coordinates():
    return load_coordinates()

@st.cache_data(ttl=300)
def cached_load_all_traffic():
    return load_all_traffic()


# ═══════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════
if _LOGO_B64:
    _logo_html = f'<img src="data:image/png;base64,{_LOGO_B64}" style="height:48px; vertical-align:middle; margin-right:12px; filter: drop-shadow(0 0 8px rgba(34,197,94,0.3));" />'
else:
    _logo_html = '🛣️ '

st.markdown(f"""
<div class="main-header">
    <h1>{_logo_html}Next-Gen Traffic Route Analyzer</h1>
    <p>Real-time traffic analysis across 20 major Indian cities
       <span class="badge">Neo4j + Cassandra</span>
    </p>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════
# LOAD DATA
# ═══════════════════════════════════════════════
try:
    raw_graph = cached_build_graph()
    coords = cached_load_coordinates()
    all_traffic = cached_load_all_traffic()
    cities = sorted(raw_graph.keys())

    if not cities:
        st.error("⚠️ No cities found in Neo4j. Run `python db_setup.py` first!")
        st.stop()
except Exception as e:
    st.error(f"⚠️ Database connection failed: {e}")
    st.info("Make sure Neo4j and Cassandra are running, then run `python db_setup.py` to seed data.")
    st.stop()


# ═══════════════════════════════════════════════
# SIDEBAR CONTROLS
# ═══════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🎛️ Route Configuration")
    st.markdown("---")

    source = st.selectbox("🟢 Source City", cities, index=cities.index("Delhi") if "Delhi" in cities else 0)

    destination = st.selectbox(
        "🔴 Destination City",
        [c for c in cities if c != source],
        index=([c for c in cities if c != source].index("Chennai")
               if "Chennai" in [c for c in cities if c != source] else 0),
    )

    st.markdown("---")

    hour = st.select_slider(
        "🕐 Time of Day",
        options=[0, 3, 6, 9, 12, 15, 18, 21],
        value=9,
        format_func=lambda h: f"{h:02d}:00",
    )

    time_labels = {
        0: "🌙 Late Night", 3: "🌙 Deep Night", 6: "🌅 Early Morning",
        9: "☀️ Morning Rush", 12: "🌤️ Midday", 15: "⛅ Afternoon",
        18: "🌆 Evening Rush", 21: "🌃 Late Evening",
    }
    st.caption(time_labels.get(hour, ""))

    st.markdown("---")

    algorithm = st.radio(
        "⚡ Algorithm",
        ["A* (Recommended)", "Dijkstra"],
        index=0,
        help="A* uses geographic heuristic for faster convergence",
    )

    st.markdown("---")

    show_all_paths = st.checkbox("📋 Show alternative paths", value=True)
    max_depth = st.slider("Max path depth", 4, 10, 7, help="Maximum hops for alternative path search")

    st.markdown("---")

    find_route = st.button("🚀 Find Best Route", use_container_width=True, type="primary")


# ═══════════════════════════════════════════════
# ROUTE COMPUTATION
# ═══════════════════════════════════════════════
if find_route:
    with st.spinner("Computing optimal route..."):
        start_time = time.time()

        # Load weights for selected hour
        weights = all_traffic.get(hour, {})
        processed_graph = preprocess_graph(raw_graph, weights)

        # Run pathfinding
        if "A*" in algorithm:
            cost, path = astar(processed_graph, source, destination, coords)
            algo_name = "A*"
        else:
            cost, path = dijkstra(processed_graph, source, destination)
            algo_name = "Dijkstra"

        elapsed = time.time() - start_time

    if not path:
        st.error(f"❌ No route found from **{source}** to **{destination}** at {hour:02d}:00")
        st.stop()

    # ---- Store results in session ----
    st.session_state["result"] = {
        "path": path,
        "cost": cost,
        "algo": algo_name,
        "elapsed": elapsed,
        "hour": hour,
        "source": source,
        "destination": destination,
        "raw_graph": raw_graph,
        "processed_graph": processed_graph,
        "weights": weights,
    }


# ═══════════════════════════════════════════════
# DISPLAY RESULTS
# ═══════════════════════════════════════════════
if "result" in st.session_state:
    r = st.session_state["result"]
    path = r["path"]
    cost = r["cost"]

    # ---- Metrics row ----
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        hours_val = int(cost)
        mins_val = int((cost - hours_val) * 60)
        st.markdown(f"""
        <div class="metric-card mc-time">
            <div class="icon">⏱️</div>
            <div class="label">Travel Time</div>
            <div class="value">{cost:.2f}</div>
            <div class="unit">{hours_val}h {mins_val}m</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card mc-stops">
            <div class="icon">📍</div>
            <div class="label">Cities on Route</div>
            <div class="value">{len(path)}</div>
            <div class="unit">{len(path) - 1} segments</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card mc-algo">
            <div class="icon">⚡</div>
            <div class="label">Algorithm</div>
            <div class="value">{r['algo']}</div>
            <div class="unit">{r['elapsed']*1000:.1f} ms</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card mc-hour">
            <div class="icon">🕐</div>
            <div class="label">Departure</div>
            <div class="value">{r['hour']:02d}:00</div>
            <div class="unit">{time_labels.get(r['hour'], '')}</div>
        </div>
        """, unsafe_allow_html=True)

    # ---- Route path display ----
    city_nodes = []
    for i, c in enumerate(path):
        if i == 0:
            city_nodes.append(f'<span class="city-node start">{c}</span>')
        elif i == len(path) - 1:
            city_nodes.append(f'<span class="city-node end">{c}</span>')
        else:
            city_nodes.append(f'<span class="city-node">{c}</span>')

    route_html = ' <span class="arrow">→</span> '.join(city_nodes)

    st.markdown(f"""
    <div class="route-display">
        <div class="route-label">Optimal Route</div>
        <div class="route-path">{route_html}</div>
    </div>
    """, unsafe_allow_html=True)

    # ---- Visualisation tabs ----
    tab1, tab2, tab3, tab4 = st.tabs([
        "🌐 Network Graph",
        "🗺️ Map View",
        "📊 Time Analysis",
        "🔥 Congestion Heatmap",
    ])

    with tab1:
        st.markdown('<div class="section-header">Road Network — Shortest Path Highlighted</div>',
                    unsafe_allow_html=True)
        fig_net = plotly_network_graph(path, r["raw_graph"], coords)
        st.plotly_chart(fig_net, use_container_width=True)

    with tab2:
        st.markdown('<div class="section-header">Route on Map</div>',
                    unsafe_allow_html=True)
        fig_map = plotly_map(path, coords, all_cities=set(cities))
        st.plotly_chart(fig_map, use_container_width=True)

    with tab3:
        st.markdown('<div class="section-header">Travel Time Across All Hours (same route)</div>',
                    unsafe_allow_html=True)
        fig_time = plotly_time_analysis(path, r["raw_graph"], all_traffic, coords)
        st.plotly_chart(fig_time, use_container_width=True)

    with tab4:
        st.markdown('<div class="section-header">Congestion per Segment × Time of Day</div>',
                    unsafe_allow_html=True)
        # Load full traffic details for all hours
        all_details = {}
        for h in [0, 3, 6, 9, 12, 15, 18, 21]:
            all_details[h] = load_traffic_details(h)

        fig_hm = plotly_congestion_heatmap(path, r["raw_graph"], all_details)
        st.plotly_chart(fig_hm, use_container_width=True)

    # ---- Segment details table ----
    st.markdown('<div class="section-header">📋 Segment Breakdown</div>',
                unsafe_allow_html=True)

    traffic_det = load_traffic_details(r["hour"])
    segments_data = []
    for i in range(len(path) - 1):
        rid = get_road_id_between(r["raw_graph"], path[i], path[i + 1])
        if rid and rid in traffic_det:
            d = traffic_det[rid]
            segments_data.append({
                "Segment": f"{path[i]} → {path[i+1]}",
                "Road ID": rid,
                "Avg Speed (km/h)": f"{d['avg_speed']:.1f}",
                "Congestion": f"{d['congestion_level']:.0%}",
                "Travel Time (hrs)": f"{d['travel_time']:.2f}",
            })

    if segments_data:
        st.dataframe(segments_data, use_container_width=True, hide_index=True)

    # ---- Alternative paths ----
    if show_all_paths:
        st.markdown('<div class="section-header">🔀 Alternative Routes</div>',
                    unsafe_allow_html=True)

        with st.spinner("Searching alternative paths..."):
            all_paths = get_all_paths(r["processed_graph"], r["source"], r["destination"], max_depth=max_depth)

        if all_paths:
            # Sort by cost
            path_costs = []
            for p in all_paths:
                c = compute_path_cost(p, r["processed_graph"])
                path_costs.append((p, c))

            path_costs.sort(key=lambda x: x[1])

            # Display top 10 as styled cards
            for idx, (p, c) in enumerate(path_costs[:10]):
                is_best = (p == path)
                route_str = " → ".join(p)
                diff = c - cost
                if diff > 0:
                    diff_html = f'<span class="diff-text slower">+{diff:.2f} hrs</span>'
                elif diff < 0:
                    diff_html = f'<span class="diff-text faster">{diff:.2f} hrs</span>'
                else:
                    diff_html = f'<span class="diff-text">same</span>'

                rank_label = f"⭐ {idx+1}" if is_best else str(idx+1)

                st.markdown(f"""
                <div class="alt-route-row" style="{'border-color: rgba(245,158,11,0.25);' if is_best else ''}">
                    <span class="rank-badge">{rank_label}</span>
                    <span class="route-text">{route_str} &nbsp;({len(p)-1} hops)</span>
                    <span class="eta-text">{c:.2f} hrs</span>
                    {diff_html}
                </div>
                """, unsafe_allow_html=True)

            st.caption(f"Showing top {min(10, len(path_costs))} of {len(all_paths)} paths found")
        else:
            st.info("No alternative paths found within the depth limit.")

    # ---- Footer stats bar ----
    st.markdown("""
    <div class="footer-stats">
        <div class="footer-stat"><div class="fs-val">20</div><div class="fs-lbl">Cities</div></div>
        <div class="footer-stat"><div class="fs-val">40</div><div class="fs-lbl">Roads</div></div>
        <div class="footer-stat"><div class="fs-val">8</div><div class="fs-lbl">Time Slots</div></div>
        <div class="footer-stat"><div class="fs-val">320</div><div class="fs-lbl">Records</div></div>
        <div class="footer-stat"><div class="fs-val">Neo4j</div><div class="fs-lbl">Graph DB</div></div>
        <div class="footer-stat"><div class="fs-val">Cassandra</div><div class="fs-lbl">Time-Series</div></div>
    </div>
    """, unsafe_allow_html=True)

else:
    # ── Landing state — show the full network with a nice intro ──
    st.markdown("""
    <div class="landing-card">
        <div class="landing-icon">🗺️</div>
        <h3>Explore India's Road Network</h3>
        <p>Configure your route in the sidebar and click <b>Find Best Route</b> to discover the optimal path.</p>
        <div class="stats-row">
            <div class="stat-item">
                <div class="stat-value">20</div>
                <div class="stat-label">Cities</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">40</div>
                <div class="stat-label">Roads</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">8</div>
                <div class="stat-label">Time Slots</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">320</div>
                <div class="stat-label">Traffic Records</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">🌐 Full Road Network</div>',
                unsafe_allow_html=True)

    fig_net = plotly_network_graph([], raw_graph, coords)
    st.plotly_chart(fig_net, use_container_width=True)
