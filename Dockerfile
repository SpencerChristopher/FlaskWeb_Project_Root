# --- Builder Stage ---
# This stage installs dependencies using Poetry
ARG PYTHON_IMAGE=python:3.12-slim-bookworm@sha256:06584c6c0b328c74577881be68b6b15e47820e1d087796d85915d311b7dfb2a4
ARG NODE_IMAGE=node:20-slim@sha256:a82f40540f5959e0003fb7b3c0f80490def2927be8bdbee7e3e0ac65cce3be92
FROM ${PYTHON_IMAGE} AS builder

WORKDIR /app

# Install poetry and secure system tools
# hadolint ignore=DL3013
RUN pip install --no-cache-dir --upgrade --default-timeout=100 pip setuptools wheel && \
    pip install --no-cache-dir --default-timeout=100 "poetry>=2.0.0" && \
    poetry self add poetry-plugin-export

# Copy dependency definition files to leverage Docker cache
COPY poetry.lock pyproject.toml ./

# Install dependencies into a virtual environment
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
RUN poetry install --no-root

# --- Static Assets Obfuscation Stage ---
# This stage minifies and obfuscates Vanilla JS using Terser
FROM ${NODE_IMAGE} AS static-builder
WORKDIR /app
COPY ./static ./static
# Install Terser globally and minify in a single layer
# Use npm configuration to handle flaky network
RUN npm config set fetch-retries 5 && \
    npm config set fetch-retry-mintimeout 20000 && \
    npm config set fetch-retry-maxtimeout 120000 && \
    npm install -g terser@5.27.0 && \
    find ./static -name "*.js" -exec sh -c 'terser "$1" --compress --mangle -o "$1"' _ {} \;

# --- Final Stage ---
# This stage creates the lean, high-integrity production/staging image
FROM ${PYTHON_IMAGE} AS final

WORKDIR /app

# Create a non-root user and set up the environment
RUN useradd --create-home appuser && \
    mkdir -p logs static/uploads && \
    chown -R appuser:appuser /app

# Install system deps needed for Playwright/Chromium headless and secure tools
# hadolint ignore=DL3008,DL3013
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      libglib2.0-0 libnss3 libatk-bridge2.0-0 libatk1.0-0 libcups2 \
      libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
      libgbm1 libpango-1.0-0 libcairo2 libasound2 fonts-liberation \
      libxshmfence1 libxcb1 libx11-6 libxext6 libxtst6 libxss1 libgtk-3-0 \
      wget ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir --upgrade --default-timeout=100 pip setuptools wheel
USER appuser

# Environment configuration
ARG LOG_LEVEL=INFO
ENV LOG_LEVEL=$LOG_LEVEL \
    FLASK_ENV=development \
    GUNICORN_TIMEOUT=30 \
    GUNICORN_WORKERS=3 \
    GUNICORN_THREADS=2 \
    FORWARDED_ALLOW_IPS=* \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    JWT_COOKIE_SECURE=false \
    JWT_COOKIE_CSRF_PROTECT=true \
    JWT_COOKIE_SAMESITE=Lax \
    PROXY_FIX_X_FOR=1 \
    PROXY_FIX_X_PROTO=1 \
    PROXY_FIX_X_HOST=1 \
    PROXY_FIX_X_PREFIX=1 \
    CORS_ORIGINS=http://localhost:5001,http://127.0.0.1:5001 \
    MONGO_SERVER_SELECTION_TIMEOUT_MS=10000 \
    MONGO_CONNECT_TIMEOUT_MS=10000 \
    MONGO_SOCKET_TIMEOUT_MS=10000 \
    TALISMAN_FORCE_HTTPS=false \
    CSP_REPORT_URI=""

# Copy the virtual environment and application source
# We use --chown to ensure the non-root user has immediate ownership
COPY --from=builder --chown=appuser:appuser /app/.venv ./.venv
COPY --chown=appuser:appuser ./src ./src
COPY --chown=appuser:appuser ./scripts ./scripts
COPY --from=static-builder --chown=appuser:appuser /app/static ./static
COPY --chown=appuser:appuser ./templates ./templates
COPY --chown=appuser:appuser ./main.py ./
COPY --chown=appuser:appuser ./pytest.ini ./

EXPOSE 8000

# Define the command to run the application
# We use 'sh -c' within JSON to allow ENV variable expansion safely
CMD ["sh", "-c", "exec /app/.venv/bin/gunicorn --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS} --threads ${GUNICORN_THREADS} --timeout ${GUNICORN_TIMEOUT} --log-level ${LOG_LEVEL} --limit-request-line 4094 --limit-request-fields 100 --max-requests 1000 --forwarded-allow-ips=\"${FORWARDED_ALLOW_IPS}\" --preload --access-logfile - 'main:create_app()'"]
