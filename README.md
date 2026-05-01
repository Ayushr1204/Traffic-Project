# 🛣️ NGD DevOps AAT — Traffic Route Analyzer

Real-time traffic analysis and optimal route computation across **20 major Indian cities**, powered by **Neo4j** (graph database) and **Apache Cassandra** (time-series store).

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│              Streamlit Dashboard                │
│   (Interactive UI + Plotly Visualisations)       │
├───────────────┬─────────────────────────────────┤
│  Algorithms   │       Visualization             │
│  (A*, Dijkstra│  (Network Graph, Map,           │
│   All-Paths)  │   Time Analysis, Heatmap)       │
├───────────────┴─────────────────────────────────┤
│            Graph Builder Layer                   │
│  (Query Neo4j + Cassandra, Build Weighted Graph) │
├────────────────────┬────────────────────────────┤
│      Neo4j         │      Cassandra             │
│  (20 City Nodes,   │  (320 Traffic Records,     │
│   80 Road Edges)   │   8 Timestamps/Road)       │
└────────────────────┴────────────────────────────┘
```

## 📋 Prerequisites

- **Python 3.9+**
- **Neo4j** (Community or Enterprise) running on `bolt://localhost:7687`
- **Apache Cassandra** running on `127.0.0.1:9042`
- **Docker & Docker Compose** (optional — for containerised deployment)

## 🐳 Quick Start (Docker — Recommended)

The fastest way to run everything with zero local setup:

```bash
docker-compose up --build
```

This spins up **Neo4j**, **Cassandra**, and the **Streamlit app** together. The app automatically waits for the databases, seeds data, and launches at:

> **http://localhost:8501**

To tear down and remove volumes:

```bash
docker-compose down -v
```

## 🚀 Quick Start (Local)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Databases (Optional)

Default connection settings work out of the box. Override with environment variables if needed:

```bash
# Neo4j
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=12345678

# Cassandra
export CASSANDRA_HOST=127.0.0.1
export CASSANDRA_KEYSPACE=traffic
```

### 3. Seed the Databases

```bash
python db_setup.py
```

This creates:
- **20 city nodes** in Neo4j with lat/lon coordinates
- **80 directed road edges** (40 bidirectional roads) with road_id, length, speed, congestion
- **320 traffic records** in Cassandra (40 roads × 8 timestamps)

### 4. Launch the Dashboard

```bash
streamlit run app.py
```

## 🗂️ Project Structure

| File | Description |
|------|-------------|
| `app.py` | Streamlit interactive dashboard |
| `config.py` | Database connection management (Neo4j + Cassandra) |
| `db_setup.py` | Schema creation and data seeding script |
| `graph_builder.py` | Build weighted graph from database queries |
| `algorithms.py` | Dijkstra, A*, all-paths enumeration |
| `visualization.py` | Plotly network graph, map, charts |
| `Dockerfile` | Container image for the Streamlit app |
| `docker-compose.yml` | Full stack — Neo4j + Cassandra + App |
| `entrypoint.sh` | Container startup script (wait → seed → run) |
| `wait_for_dbs.py` | Health-check script for database readiness |
| `tests/` | Unit tests for algorithms and graph builder |

## 🌆 Cities in the Network

Delhi • Mumbai • Kolkata • Chennai • Bengaluru • Hyderabad • Ahmedabad • Pune • Jaipur • Lucknow • Kanpur • Nagpur • Indore • Bhopal • Patna • Ranchi • Bhubaneswar • Visakhapatnam • Kochi • Coimbatore

## ⚡ Features

- **Dual pathfinding algorithms** — Dijkstra and A* with Haversine heuristic
- **Time-aware routing** — 8 traffic snapshots (every 3 hours) with realistic rush-hour patterns
- **4 visualization tabs** — Network graph, OpenStreetMap, time-of-day analysis, congestion heatmap
- **Alternative routes** — DFS-based path enumeration ranked by cost
- **Segment breakdown** — Per-road speed, congestion, and travel time details
- **Dark-themed UI** — Premium Streamlit dashboard with custom CSS

## 📊 Traffic Patterns

| Hour | Profile | Congestion |
|------|---------|------------|
| 00:00 | 🌙 Late Night | Very Low |
| 03:00 | 🌙 Deep Night | Minimal |
| 06:00 | 🌅 Early Morning | Rising |
| 09:00 | ☀️ Morning Rush | **Peak** |
| 12:00 | 🌤️ Midday | Moderate |
| 15:00 | ⛅ Afternoon | High |
| 18:00 | 🌆 Evening Rush | **Peak** |
| 21:00 | 🌃 Late Evening | Low |

## 🧪 Testing

Run the unit test suite (no database required):

```bash
python -m pytest tests/ -v
```

Tests cover:
- **Dijkstra** — shortest path, unreachable nodes, edge cases
- **A*** — heuristic admissibility, result parity with Dijkstra
- **All-paths DFS** — enumeration, depth limits
- **Graph preprocessing** — weight merging, parallel edges, missing data
- **Road lookup** — directional queries, missing cities

## 🔁 Jenkins CI/CD Demo (GitHub -> Jenkins -> Deploy)

This repository includes a ready `Jenkinsfile` for your AAT DevOps demo.

### What the pipeline does

1. **Checkout** latest code from GitHub
2. **Build** Docker image(s)
3. **Test** with `pytest`
4. **Deploy** full stack (`neo4j`, `cassandra`, `app`) via Docker Compose
5. **Verify** app health endpoint at `http://localhost:8501/_stcore/health`

### Trigger mode for demo

- The pipeline uses **SCM polling every 2 minutes**:
  - `pollSCM('H/2 * * * *')`
- This satisfies "automatically or periodically fetched changes from GitHub".
- You can also add a GitHub webhook (`/github-webhook/`) for immediate trigger.

### Jenkins job setup (recommended)

1. Create a **Pipeline** job in Jenkins.
2. Under **Pipeline Definition**, choose **Pipeline script from SCM**.
3. SCM: **Git**; provide your GitHub repo URL and credentials if private.
4. Branch: `*/main` (or your active branch).
5. Script Path: `Jenkinsfile`.
6. Save and run once manually to validate environment.

### Jenkins node prerequisites

- Docker Desktop (running)
- Git
- Jenkins running with permission to execute Docker CLI
- Required Jenkins plugins:
  - Pipeline
  - Git
  - GitHub Integration (optional but useful for webhook trigger)

### Demo flow to show examiner

1. Make a small code change in GitHub (for example, UI text in `app.py`).
2. Commit and push.
3. Wait for Jenkins poll (or trigger manually/webhook).
4. Show Jenkins stages: Checkout -> Build -> Test -> Deploy -> Verify.
5. Open deployed app at `http://localhost:8501`.
