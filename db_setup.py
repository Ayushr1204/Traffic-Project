"""
db_setup.py — Create schemas and seed data in Neo4j + Cassandra.

Usage:
    python db_setup.py          # full setup (clear + seed)
    python db_setup.py --seed   # same as above

This script is idempotent — safe to run multiple times.
"""

import random
import math
from config import get_neo4j_driver, get_cassandra_session, CASSANDRA_KEYSPACE


# ═══════════════════════════════════════════════
# CITY DATA — 20 major Indian cities
# ═══════════════════════════════════════════════
CITIES = [
    {"name": "Delhi",           "lat": 28.6100, "lon": 77.2300},
    {"name": "Mumbai",          "lat": 19.0761, "lon": 72.8775},
    {"name": "Kolkata",         "lat": 22.5675, "lon": 88.3700},
    {"name": "Chennai",         "lat": 13.0825, "lon": 80.2750},
    {"name": "Bengaluru",       "lat": 12.9789, "lon": 77.5917},
    {"name": "Hyderabad",       "lat": 17.3617, "lon": 78.4747},
    {"name": "Ahmedabad",       "lat": 23.0225, "lon": 72.5714},
    {"name": "Pune",            "lat": 18.5203, "lon": 73.8567},
    {"name": "Jaipur",          "lat": 26.9000, "lon": 75.8000},
    {"name": "Lucknow",         "lat": 26.8500, "lon": 80.9500},
    {"name": "Kanpur",          "lat": 26.4500, "lon": 80.3500},
    {"name": "Nagpur",          "lat": 21.1458, "lon": 79.0882},
    {"name": "Indore",          "lat": 22.7196, "lon": 75.8577},
    {"name": "Bhopal",          "lat": 23.2599, "lon": 77.4126},
    {"name": "Patna",           "lat": 25.6100, "lon": 85.1400},
    {"name": "Ranchi",          "lat": 23.3400, "lon": 85.3100},
    {"name": "Bhubaneswar",     "lat": 20.2961, "lon": 85.8245},
    {"name": "Visakhapatnam",   "lat": 17.6868, "lon": 83.2185},
    {"name": "Kochi",           "lat":  9.9312, "lon": 76.2673},
    {"name": "Coimbatore",      "lat": 11.0168, "lon": 76.9558},
]


# ═══════════════════════════════════════════════
# ROAD DATA — ~40 bidirectional roads
# (source, target, road_id, road_length_km, base_avg_speed, base_congestion)
# ═══════════════════════════════════════════════
ROADS = [
    # --- Northern corridor ---
    ("Delhi",         "Jaipur",         "R001",  280,  85, 0.35),
    ("Delhi",         "Lucknow",        "R002",  555,  80, 0.40),
    ("Delhi",         "Kanpur",         "R003",  480,  75, 0.38),
    ("Delhi",         "Ahmedabad",      "R036",  940,  80, 0.30),

    # --- Western corridor ---
    ("Jaipur",        "Ahmedabad",      "R004",  660,  78, 0.30),
    ("Jaipur",        "Indore",         "R005",  600,  70, 0.25),
    ("Jaipur",        "Bhopal",         "R040",  600,  72, 0.28),
    ("Ahmedabad",     "Mumbai",         "R006",  530,  82, 0.45),
    ("Ahmedabad",     "Indore",         "R007",  400,  75, 0.25),

    # --- Mumbai hub ---
    ("Mumbai",        "Pune",           "R008",  150,  90, 0.55),
    ("Mumbai",        "Nagpur",         "R009",  840,  78, 0.32),
    ("Mumbai",        "Hyderabad",      "R037",  710,  76, 0.35),

    # --- Southern-western corridor ---
    ("Pune",          "Bengaluru",      "R010",  840,  80, 0.30),
    ("Pune",          "Hyderabad",      "R011",  560,  78, 0.33),

    # --- Central India ---
    ("Indore",        "Bhopal",         "R012",  195,  85, 0.22),
    ("Indore",        "Nagpur",         "R038",  500,  72, 0.28),
    ("Bhopal",        "Nagpur",         "R013",  350,  80, 0.27),
    ("Bhopal",        "Kanpur",         "R014",  530,  70, 0.30),

    # --- Central-East corridor ---
    ("Nagpur",        "Hyderabad",      "R015",  500,  82, 0.35),
    ("Nagpur",        "Ranchi",         "R016",  700,  68, 0.28),
    ("Nagpur",        "Bhubaneswar",    "R017",  890,  70, 0.25),

    # --- Northern-East corridor ---
    ("Lucknow",       "Kanpur",         "R018",   80,  75, 0.45),
    ("Lucknow",       "Patna",          "R019",  540,  72, 0.38),
    ("Kanpur",        "Patna",          "R020",  590,  68, 0.35),

    # --- Eastern corridor ---
    ("Patna",         "Kolkata",        "R021",  580,  74, 0.40),
    ("Patna",         "Ranchi",         "R022",  330,  65, 0.30),
    ("Kolkata",       "Bhubaneswar",    "R023",  440,  78, 0.35),
    ("Kolkata",       "Ranchi",         "R024",  400,  70, 0.32),
    ("Kolkata",       "Visakhapatnam",  "R039",  900,  72, 0.28),

    # --- Odisha / East coast ---
    ("Ranchi",        "Bhubaneswar",    "R025",  480,  68, 0.26),
    ("Bhubaneswar",   "Visakhapatnam",  "R026",  440,  76, 0.30),

    # --- South-East corridor ---
    ("Visakhapatnam", "Hyderabad",      "R027",  620,  78, 0.33),
    ("Visakhapatnam", "Chennai",        "R028",  770,  80, 0.30),

    # --- Southern corridor ---
    ("Hyderabad",     "Bengaluru",      "R029",  570,  84, 0.38),
    ("Hyderabad",     "Chennai",        "R030",  630,  82, 0.35),
    ("Chennai",       "Bengaluru",      "R031",  350,  88, 0.40),
    ("Chennai",       "Coimbatore",     "R032",  510,  80, 0.32),

    # --- Deep south ---
    ("Bengaluru",     "Coimbatore",     "R033",  365,  82, 0.30),
    ("Bengaluru",     "Kochi",          "R034",  560,  76, 0.28),
    ("Coimbatore",    "Kochi",          "R035",  200,  80, 0.25),
]


# ═══════════════════════════════════════════════
# TIME-OF-DAY TRAFFIC PROFILES
# ═══════════════════════════════════════════════
# Multipliers for (speed_factor, congestion_factor) at each hour.
# speed_factor < 1 means slower; congestion_factor > 1 means more congested.
HOUR_PROFILES = {
    0:  {"speed_mult": 1.15, "cong_mult": 0.25},   # Late night — empty roads
    3:  {"speed_mult": 1.20, "cong_mult": 0.15},   # Deep night — minimal traffic
    6:  {"speed_mult": 0.85, "cong_mult": 1.40},   # Early morning rush begins
    9:  {"speed_mult": 0.70, "cong_mult": 1.80},   # Peak morning rush
    12: {"speed_mult": 0.90, "cong_mult": 1.10},   # Midday — moderate
    15: {"speed_mult": 0.80, "cong_mult": 1.50},   # Afternoon buildup
    18: {"speed_mult": 0.65, "cong_mult": 1.90},   # Peak evening rush
    21: {"speed_mult": 1.00, "cong_mult": 0.60},   # Late evening — winding down
}


def compute_travel_time(road_length, base_speed, base_congestion, hour):
    """
    Compute travel time (hours) for a road at a given hour.

    Formula:
        effective_speed = base_speed × speed_mult × (1 - effective_congestion × 0.6)
        travel_time     = road_length / effective_speed

    A small random jitter (±5 %) is added for realism.
    """
    profile = HOUR_PROFILES[hour]
    jitter = random.uniform(0.95, 1.05)

    effective_speed = base_speed * profile["speed_mult"] * jitter
    effective_congestion = min(base_congestion * profile["cong_mult"], 0.95)  # cap at 0.95

    # Congestion reduces effective speed
    effective_speed *= (1 - effective_congestion * 0.6)
    effective_speed = max(effective_speed, 10)  # floor at 10 km/h

    travel_time = road_length / effective_speed
    return round(travel_time, 4), round(effective_speed, 2), round(effective_congestion, 4)


# ═══════════════════════════════════════════════
# NEO4J SETUP
# ═══════════════════════════════════════════════
def setup_neo4j():
    """Clear existing data and seed cities + roads into Neo4j."""
    driver = get_neo4j_driver()

    with driver.session() as session:
        # 1. Clear existing data
        print("[Neo4j] Clearing existing data...")
        session.run("MATCH (n) DETACH DELETE n")

        # 2. Create constraint
        print("[Neo4j] Creating uniqueness constraint on City.name...")
        session.run(
            "CREATE CONSTRAINT city_name_unique IF NOT EXISTS "
            "FOR (c:City) REQUIRE c.name IS UNIQUE"
        )

        # 3. Create city nodes
        print(f"[Neo4j] Creating {len(CITIES)} city nodes...")
        session.run(
            """
            UNWIND $cities AS city
            CREATE (c:City {name: city.name, lat: city.lat, lon: city.lon})
            """,
            cities=CITIES,
        )

        # 4. Create bidirectional road relationships
        roads_data = [
            {
                "source": r[0],
                "target": r[1],
                "road_id": r[2],
                "road_length": r[3],
                "avg_speed": r[4],
                "congestion_level": r[5],
            }
            for r in ROADS
        ]

        print(f"[Neo4j] Creating {len(ROADS)} bidirectional roads ({len(ROADS)*2} directed edges)...")
        session.run(
            """
            UNWIND $roads AS road
            MATCH (a:City {name: road.source}), (b:City {name: road.target})
            CREATE (a)-[:ROAD {
                road_id: road.road_id,
                road_length: road.road_length,
                avg_speed: road.avg_speed,
                congestion_level: road.congestion_level
            }]->(b)
            CREATE (b)-[:ROAD {
                road_id: road.road_id,
                road_length: road.road_length,
                avg_speed: road.avg_speed,
                congestion_level: road.congestion_level
            }]->(a)
            """,
            roads=roads_data,
        )

    print("[Neo4j] ✓ Setup complete.")


# ═══════════════════════════════════════════════
# CASSANDRA SETUP
# ═══════════════════════════════════════════════
def setup_cassandra():
    """Create keyspace, table, and seed time-series traffic data into Cassandra."""
    session = get_cassandra_session()

    # 1. Create keyspace
    print(f"[Cassandra] Creating keyspace '{CASSANDRA_KEYSPACE}'...")
    session.execute(f"""
        CREATE KEYSPACE IF NOT EXISTS {CASSANDRA_KEYSPACE}
        WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': '1'}}
    """)
    session.set_keyspace(CASSANDRA_KEYSPACE)

    # 2. Create table
    print("[Cassandra] Creating traffic_data table...")
    session.execute("""
        CREATE TABLE IF NOT EXISTS traffic_data (
            road_id TEXT,
            hour INT,
            avg_speed FLOAT,
            congestion_level FLOAT,
            travel_time FLOAT,
            PRIMARY KEY (road_id, hour)
        )
    """)

    # 3. Truncate existing data for idempotency
    session.execute("TRUNCATE traffic_data")

    # 4. Seed data — 40 roads × 8 hours = 320 rows
    hours = [0, 3, 6, 9, 12, 15, 18, 21]
    insert_stmt = session.prepare("""
        INSERT INTO traffic_data (road_id, hour, avg_speed, congestion_level, travel_time)
        VALUES (?, ?, ?, ?, ?)
    """)

    row_count = 0
    for road in ROADS:
        src, dst, road_id, road_length, base_speed, base_congestion = road

        for hour in hours:
            travel_time, eff_speed, eff_congestion = compute_travel_time(
                road_length, base_speed, base_congestion, hour
            )
            session.execute(insert_stmt, (road_id, hour, eff_speed, eff_congestion, travel_time))
            row_count += 1

    print(f"[Cassandra] ✓ Inserted {row_count} rows into traffic_data.")
    print("[Cassandra] ✓ Setup complete.")


# ═══════════════════════════════════════════════
# VERIFICATION
# ═══════════════════════════════════════════════
def verify():
    """Quick verification of seeded data."""
    driver = get_neo4j_driver()

    with driver.session() as session:
        city_count = session.run("MATCH (c:City) RETURN count(c) AS cnt").single()["cnt"]
        road_count = session.run("MATCH ()-[r:ROAD]->() RETURN count(r) AS cnt").single()["cnt"]
        print(f"\n[Verify] Neo4j: {city_count} cities, {road_count} directed road edges")

    cass = get_cassandra_session()
    cass.set_keyspace(CASSANDRA_KEYSPACE)
    rows = cass.execute("SELECT COUNT(*) FROM traffic_data")
    print(f"[Verify] Cassandra: {rows.one()[0]} traffic_data rows")


# ═══════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════
if __name__ == "__main__":
    random.seed(42)  # reproducible jitter

    print("=" * 55)
    print("  NGD DevOps AAT — Database Setup & Seeding")
    print("=" * 55)

    setup_neo4j()
    print()
    setup_cassandra()
    print()
    verify()

    print("\n✅ All done! Databases are ready.")
