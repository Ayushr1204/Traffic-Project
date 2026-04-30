"""
graph_builder.py — Build the weighted traffic graph from Neo4j + Cassandra.

Functions:
    build_graph()           → raw adjacency dict from Neo4j
    load_weights(hour)      → {road_id: travel_time} from Cassandra
    load_traffic_details(hour) → {road_id: {speed, congestion, travel_time}}
    load_coordinates()      → {city: (lat, lon)} from Neo4j
    preprocess_graph(graph, weights) → adjacency with numeric costs
"""

from config import get_neo4j_driver, get_cassandra_session, CASSANDRA_KEYSPACE


def build_graph():
    """
    Query Neo4j for all ROAD relationships.

    Returns:
        dict: {city: [(neighbor, road_id), ...]}
    """
    query = """
    MATCH (a:City)-[r:ROAD]->(b:City)
    RETURN a.name AS source, b.name AS target, r.road_id AS road_id,
           r.road_length AS road_length, r.avg_speed AS avg_speed,
           r.congestion_level AS congestion_level
    """
    graph = {}

    driver = get_neo4j_driver()
    with driver.session() as session:
        result = session.run(query)
        for record in result:
            src = record["source"]
            dst = record["target"]
            rid = record["road_id"]
            graph.setdefault(src, []).append((dst, rid))

    return graph


def load_weights(hour):
    """
    Query Cassandra for travel_time at a given hour.

    Args:
        hour: int — one of {0, 3, 6, 9, 12, 15, 18, 21}

    Returns:
        dict: {road_id: travel_time}
    """
    cass = get_cassandra_session()
    cass.set_keyspace(CASSANDRA_KEYSPACE)

    rows = cass.execute(
        "SELECT road_id, travel_time FROM traffic_data WHERE hour = %s ALLOW FILTERING",
        (hour,),
    )

    return {r.road_id: r.travel_time for r in rows}


def load_traffic_details(hour):
    """
    Load full traffic details for a given hour.

    Returns:
        dict: {road_id: {"avg_speed": ..., "congestion_level": ..., "travel_time": ...}}
    """
    cass = get_cassandra_session()
    cass.set_keyspace(CASSANDRA_KEYSPACE)

    rows = cass.execute(
        "SELECT road_id, avg_speed, congestion_level, travel_time "
        "FROM traffic_data WHERE hour = %s ALLOW FILTERING",
        (hour,),
    )

    return {
        r.road_id: {
            "avg_speed": r.avg_speed,
            "congestion_level": r.congestion_level,
            "travel_time": r.travel_time,
        }
        for r in rows
    }


def load_all_traffic():
    """
    Load traffic data for ALL hours.

    Returns:
        dict: {hour: {road_id: travel_time}}
    """
    cass = get_cassandra_session()
    cass.set_keyspace(CASSANDRA_KEYSPACE)

    rows = cass.execute("SELECT road_id, hour, travel_time FROM traffic_data")

    data = {}
    for r in rows:
        data.setdefault(r.hour, {})[r.road_id] = r.travel_time

    return data


def load_coordinates():
    """
    Query Neo4j for city coordinates.

    Returns:
        dict: {city_name: (lat, lon)}
    """
    driver = get_neo4j_driver()
    coords = {}

    with driver.session() as session:
        result = session.run("MATCH (c:City) RETURN c.name AS name, c.lat AS lat, c.lon AS lon")
        for r in result:
            coords[r["name"]] = (r["lat"], r["lon"])

    return coords


def preprocess_graph(graph, weights):
    """
    Merge raw graph structure with travel-time weights.

    For each city→neighbor pair, keeps only the edge with lowest cost
    (handles parallel edges between the same pair).

    Args:
        graph: {city: [(neighbor, road_id), ...]}
        weights: {road_id: travel_time}

    Returns:
        dict: {city: [(neighbor, cost), ...]}
    """
    new_graph = {}

    for city in graph:
        best = {}
        for neighbor, road_id in graph[city]:
            if road_id not in weights:
                continue
            cost = weights[road_id]
            if neighbor not in best or cost < best[neighbor]:
                best[neighbor] = cost

        new_graph[city] = [(n, c) for n, c in best.items()]

    return new_graph


def get_road_id_between(graph, city_a, city_b):
    """
    Look up the road_id connecting two adjacent cities.

    Returns:
        str or None
    """
    for neighbor, road_id in graph.get(city_a, []):
        if neighbor == city_b:
            return road_id
    return None
