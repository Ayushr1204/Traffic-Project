# ──────────────────────────────────────────────
# NGD Traffic Route Analyzer — Streamlit App
# ──────────────────────────────────────────────
FROM python:3.11-slim

# System deps for cassandra-driver (Cython wheel build)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc build-essential && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

EXPOSE 8501

ENTRYPOINT ["./entrypoint.sh"]
