#!/bin/bash
# ──────────────────────────────────────────────
# NGD Traffic Route Analyzer — Container Entrypoint
# ──────────────────────────────────────────────
set -e

# If TESTING mode, just forward to the command (pytest)
if [ "${TESTING}" = "1" ]; then
    echo "🧪 Running in TESTING mode — executing: $@"
    exec "$@"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  NGD Traffic Route Analyzer — Starting Up"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Wait for Neo4j and Cassandra to be ready
python wait_for_dbs.py

# 2. Seed databases (idempotent — safe to re-run)
echo ""
echo "Seeding databases..."
python db_setup.py

# 3. Launch Streamlit
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🚀 Launching Streamlit on port 8501"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
exec streamlit run app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false
