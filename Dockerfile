# ── FL-IDS Platform — Root Dockerfile for Railway/Render ──────────────────
# Build context = repo root (includes both server/ and dashboard/)
FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY server/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy server source
COPY server/ ./

# Copy dashboard into server working directory so routes can find it
COPY dashboard/ ./dashboard/

# Data directory for SQLite + weights
RUN mkdir -p /data/weights

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
