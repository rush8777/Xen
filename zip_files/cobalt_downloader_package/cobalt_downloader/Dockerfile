# ─────────────────────────────────────────────────────────────────────────────
# Dockerfile — Cobalt video downloader backend
# Optimised for Google Cloud Run (no yt-dlp, no ffmpeg required)
# ─────────────────────────────────────────────────────────────────────────────

# Use slim Python image — no ffmpeg or yt-dlp needed anymore
FROM python:3.11-slim

# Cloud Run best practices
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

WORKDIR /app

# ── System deps ──────────────────────────────────────────────────────────────
# curl + ca-certificates ensure aiohttp can reach Cobalt HTTPS instances
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ── Python deps ──────────────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── App source ───────────────────────────────────────────────────────────────
COPY . .

# ── Non-root user (Cloud Run security best practice) ─────────────────────────
RUN useradd -m -u 1000 appuser \
    && mkdir -p /app/downloads /tmp/downloads \
    && chown -R appuser:appuser /app /tmp/downloads
USER appuser

# ── Startup ──────────────────────────────────────────────────────────────────
# Cloud Run injects PORT env var; uvicorn binds to it.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 1"]
