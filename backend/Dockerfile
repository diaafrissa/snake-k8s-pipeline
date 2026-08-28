# ---------- Stage 1: build dependencies ----------
FROM python:3.12-slim AS builder

WORKDIR /build

# Keep pip quiet & deterministic; no bytecode/caches leaking into the layer
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY requirements.txt .
RUN pip install --user --no-warn-script-location -r requirements.txt

# ---------- Stage 2: slim runtime image ----------
FROM python:3.12-slim

# Create a non-root user to run the app (never run as root in production)
RUN useradd --create-home --shell /usr/sbin/nologin appuser

WORKDIR /app

# Bring in the packages installed in the builder stage only (no build tools)
COPY --from=builder /root/.local /home/appuser/.local
COPY app/ ./app/

RUN chown -R appuser:appuser /app
USER appuser

ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

# Container-level healthcheck mirrors the K8s readiness probe we'll add later
HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0) if urllib.request.urlopen('http://localhost:8000/api/health', timeout=2).status == 200 else sys.exit(1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
