FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps — minimal, the heavy lifting is in Stirling-PDF itself
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY scripts/ ./scripts/

RUN mkdir -p /output /cache /data && \
    chmod -R 0777 /output /cache /data

ENV OUTPUT_DIR=/output \
    CACHE_DIR=/cache \
    PYTHONPATH=/app/src \
    PORT=8087 \
    HOST=0.0.0.0

EXPOSE 8087

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python3 -c "import socket; s=socket.socket(); s.settimeout(5); s.connect(('localhost',8087)); s.close()" || exit 1

CMD ["python", "-m", "stirling_mcp.server"]
