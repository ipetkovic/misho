FROM python:3.12-slim

# /root is load-bearing: CONFIG.database_path is the relative path
# 'db/sportbooking.db', and compose bind-mounts the persistent disk at
# /root/db. Changing the workdir silently relocates the database.
WORKDIR /root

ENV UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir uv

# Dependency layer. Only the manifests are copied, so editing a source file
# reuses the cached third-party install instead of resolving from scratch.
COPY pyproject.toml uv.lock ./
COPY sportbooking/pyproject.toml sportbooking/README.md ./sportbooking/
COPY misho-server/pyproject.toml misho-server/README.md ./misho-server/
RUN uv sync --frozen --package misho-server --no-install-workspace

# Source layer.
COPY sportbooking/ ./sportbooking/
COPY misho-server/ ./misho-server/
RUN uv sync --frozen --package misho-server

# The image ships neither curl nor wget, so the probe uses stdlib urllib.
# urlopen raises on 503, which is exactly the non-zero exit Docker wants.
HEALTHCHECK --interval=15s --timeout=5s --start-period=120s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=4)"]

# Exec form, and the console script directly rather than `uv run`, so that
# Python is PID 1 and receives SIGTERM. Previously uv was PID 1 and the
# signal never reached the app, costing the full 10s grace period on every
# stop before a SIGKILL.
CMD ["/root/.venv/bin/misho-server"]
