# --- Builder Stage ---
# This stage installs dependencies using Poetry
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim-bookworm AS builder

WORKDIR /app

# Install poetry and secure system tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir poetry && \
    poetry self add poetry-plugin-export

# Copy dependency definition files to leverage Docker cache
COPY poetry.lock pyproject.toml ./

# Install dependencies into a virtual environment
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
RUN poetry install --no-root

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
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
USER appuser

# Environment configuration
ARG LOG_LEVEL=INFO
ENV LOG_LEVEL=$LOG_LEVEL \
    GUNICORN_TIMEOUT=30 \
    FORWARDED_ALLOW_IPS=* \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copy the virtual environment and application source
# We use --chown to ensure the non-root user has immediate ownership
COPY --from=builder --chown=appuser:appuser /app/.venv ./.venv
COPY --chown=appuser:appuser ./src ./src
COPY --chown=appuser:appuser ./scripts ./scripts
COPY --chown=appuser:appuser ./static ./static
COPY --chown=appuser:appuser ./templates ./templates
COPY --chown=appuser:appuser ./main.py ./
COPY --chown=appuser:appuser ./pytest.ini ./

EXPOSE 8000

# Define the command to run the application
# Preload is used for fail-fast behavior on bootstrap errors
CMD exec /app/.venv/bin/gunicorn --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS} --timeout ${GUNICORN_TIMEOUT} --log-level ${LOG_LEVEL} --limit-request-line 4094 --limit-request-fields 100 --max-requests 1000 --forwarded-allow-ips="${FORWARDED_ALLOW_IPS}" --preload --access-logfile - 'main:create_app()'
