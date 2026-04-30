"""
wait_for_dbs.py — Wait for Neo4j and Cassandra to become available.

Used by entrypoint.sh to block until both databases accept connections,
preventing startup errors when docker-compose brings everything up together.
"""

import os
import sys
import time
import socket


def wait_for_port(host, port, name, timeout=90):
    """Block until a TCP port is accepting connections."""
    start = time.time()
    attempt = 0

    while True:
        attempt += 1
        try:
            with socket.create_connection((host, port), timeout=5):
                elapsed = time.time() - start
                print(f"[wait] ✓ {name} ({host}:{port}) ready after {elapsed:.1f}s")
                return
        except OSError:
            elapsed = time.time() - start
            if elapsed >= timeout:
                print(f"[wait] ✗ {name} ({host}:{port}) not reachable after {timeout}s — giving up")
                sys.exit(1)
            wait_time = min(2 ** min(attempt, 4), 10)  # 2, 4, 8, 10, 10 ...
            print(f"[wait]   {name} not ready (attempt {attempt}, {elapsed:.0f}s elapsed) — retrying in {wait_time}s")
            time.sleep(wait_time)


if __name__ == "__main__":
    neo4j_host = os.getenv("NEO4J_HOST", "neo4j")
    neo4j_port = int(os.getenv("NEO4J_BOLT_PORT", "7687"))

    cassandra_host = os.getenv("CASSANDRA_HOST", "cassandra")
    cassandra_port = int(os.getenv("CASSANDRA_PORT", "9042"))

    print("=" * 50)
    print("  Waiting for databases...")
    print("=" * 50)

    wait_for_port(neo4j_host, neo4j_port, "Neo4j")
    wait_for_port(cassandra_host, cassandra_port, "Cassandra")

    print("\n✅ All databases are reachable.\n")
