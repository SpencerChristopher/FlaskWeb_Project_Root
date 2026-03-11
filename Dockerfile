# --- Builder Stage ---
# This stage installs dependencies using Poetry
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim-bookworm AS builder

WORKDIR /app

# Install poetry and secure system tools
# Hadolint: Pin versions in pip (DL3013)
RUN pip install --no-cache-dir --upgrade pip==24.0 setuptools==69.0.3 wheel==0.42.0 && \
    pip install --no-cache-dir poetry==1.7.1 && \
    poetry self add poetry-plugin-export

# Copy dependency definition files to leverage Docker cache
COPY poetry.lock pyproject.toml ./

# Install dependencies into a virtual environment
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
RUN poetry install --no-root

# --- Static Assets Obfuscation Stage ---
# This stage minifies and obfuscates Vanilla JS using Terser
FROM node:20-slim AS static-builder
WORKDIR /app
COPY ./static ./static
# Install Terser globally and minify in a single layer
# Hadolint: Pin versions in npm (DL3016), Consolidate RUNs (DL3059)
RUN npm install -g terser@5.27.0 && \
    find ./static -name "*.js" -exec sh -c 'terser "$1" --compress --mangle -o "$1"' _ {} \;

# --- Final Stage ---
# This stage creates the lean, high-integrity production/staging image
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim-bookworm AS final

WORKDIR /app

# Create a non-root user and set up the environment
RUN useradd --create-home appuser && \
    mkdir -p logs static/uploads && \
    chown -R appuser:appuser /app

# Secure system tools (as root) then switch to non-root
# Hadolint: Pin versions in pip (DL3013)
RUN pip install --no-cache-dir --upgrade pip==24.0 setuptools==69.0.3 wheel==0.42.0
USER appuser

# Environment configuration
ARG LOG_LEVEL=INFO
ENV LOG_LEVEL=$LOG_LEVEL \
    GUNICORN_TIMEOUT=30 \
    GUNICORN_WORKERS=3 \
    GUNICORN_THREADS=2 \
    FORWARDED_ALLOW_IPS=* \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

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
# Hadolint: Use arguments JSON notation (DL3025)
# We use 'sh -c' within JSON to allow ENV variable expansion safely
CMD ["sh", "-c", "exec /app/.venv/bin/gunicorn --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS} --threads ${GUNICORN_THREADS} --timeout ${GUNICORN_TIMEOUT} --log-level ${LOG_LEVEL} --limit-request-line 4094 --limit-request-fields 100 --max-requests 1000 --forwarded-allow-ips=\"${FORWARDED_ALLOW_IPS}\" --preload --access-logfile - 'main:create_app()'"]
