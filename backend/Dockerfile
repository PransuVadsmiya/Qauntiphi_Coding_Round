# ---- Backend: FastAPI + SQLite cache ----
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    # SQLite cache lives on a mounted volume so it survives container restarts
    DB_PATH=/data/portfolio_cache.db

WORKDIR /app

# Install dependencies first so this layer is cached between code changes
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app

# Run as a non-root user that owns the data directory
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /data && chown appuser:appuser /data
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=2)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
