"""
config.py — Centralised database connection management.

Environment variables (all optional, sensible defaults provided):
    NEO4J_URI       bolt://localhost:7687
    NEO4J_USER      neo4j
    NEO4J_PASSWORD  12345678
    CASSANDRA_HOST  127.0.0.1
    CASSANDRA_KEYSPACE  traffic
"""

import os
from neo4j import GraphDatabase
from cassandra.cluster import Cluster


# ──────────────────────────────────────────────
# Neo4j
# ──────────────────────────────────────────────
_NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
_NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
_NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "12345678")

_neo4j_driver = None


def get_neo4j_driver():
    """Return a singleton Neo4j driver instance."""
    global _neo4j_driver
    if _neo4j_driver is None:
        _neo4j_driver = GraphDatabase.driver(
            _NEO4J_URI,
            auth=(_NEO4J_USER, _NEO4J_PASSWORD),
        )
    return _neo4j_driver


def close_neo4j():
    """Gracefully close the Neo4j driver."""
    global _neo4j_driver
    if _neo4j_driver is not None:
        _neo4j_driver.close()
        _neo4j_driver = None


# ──────────────────────────────────────────────
# Cassandra
# ──────────────────────────────────────────────
_CASSANDRA_HOST = os.getenv("CASSANDRA_HOST", "127.0.0.1")
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "traffic")

_cassandra_cluster = None
_cassandra_session = None


def get_cassandra_session():
    """Return a singleton Cassandra session connected to the traffic keyspace."""
    global _cassandra_cluster, _cassandra_session
    if _cassandra_session is None:
        _cassandra_cluster = Cluster([_CASSANDRA_HOST])
        _cassandra_session = _cassandra_cluster.connect()
        # Ensure the keyspace exists before setting it
        try:
            _cassandra_session.set_keyspace(CASSANDRA_KEYSPACE)
        except Exception:
            pass  # Keyspace may not exist yet (db_setup will create it)
    return _cassandra_session


def close_cassandra():
    """Gracefully shut down the Cassandra cluster connection."""
    global _cassandra_cluster, _cassandra_session
    if _cassandra_cluster is not None:
        _cassandra_cluster.shutdown()
        _cassandra_cluster = None
        _cassandra_session = None
