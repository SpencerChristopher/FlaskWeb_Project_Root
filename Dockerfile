# --- Builder Stage ---
# This stage installs dependencies using Poetry
FROM python:3.11-slim-bookworm AS builder

# Set the working directory
WORKDIR /app

# Install poetry and secure system tools
RUN pip install --upgrade pip setuptools wheel && pip install poetry && \
    poetry self add poetry-plugin-export

# Copy only the dependency definition files to leverage Docker cache
COPY poetry.lock pyproject.toml ./

# Install dependencies into a virtual environment
# --no-root is important to avoid installing the project itself, just the deps
# --no-dev is used to skip development dependencies in the final image
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
RUN poetry install --no-root

# --- Validation Stage ---
# This stage runs security audits and lints before final image creation
FROM builder AS validate
WORKDIR /app
COPY . .
# Install validation tools (silently)
RUN apt-get update -qq && apt-get install -y -qq wget curl ca-certificates > /dev/null && \
    wget -qO- https://raw.githubusercontent.com/rhysd/actionlint/main/scripts/download-actionlint.bash | bash -s -- latest /usr/local/bin/ && \
    ./.venv/bin/pip install --quiet pip-audit
# Execute lints and audits (reporting only errors)
RUN /usr/local/bin/actionlint .github/workflows/*.yml && \
    poetry export --format=constraints.txt --output=constraints.txt --without-hashes && \
    ./.venv/bin/pip-audit -r constraints.txt && \
    rm constraints.txt

# --- Final Stage ---
# This stage creates the final, lean production image
FROM python:3.11-slim-bookworm

# Set the working directory
WORKDIR /app

# Create a non-root user to run the application
RUN useradd --create-home appuser
# Create necessary directories and set permissions for appuser
RUN mkdir -p logs static/uploads && chown -R appuser:appuser /app

# Upgrade system tools to secure versions
USER root
RUN pip install --upgrade pip setuptools wheel
USER appuser

ARG LOG_LEVEL=INFO
ENV LOG_LEVEL=$LOG_LEVEL
ENV GUNICORN_TIMEOUT=30
ENV FORWARDED_ALLOW_IPS=*

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv ./.venv

# Copy the application source code
COPY ./src ./src
COPY ./scripts ./scripts
COPY ./static ./static
COPY ./templates ./templates
COPY ./pytest.ini ./
COPY ./tests ./tests

COPY ./main.py ./

# Make port 8000 available
EXPOSE 8000

# Define the command to run the application
# We use the full path to the gunicorn executable in the virtual environment
CMD exec /app/.venv/bin/gunicorn --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS} --timeout ${GUNICORN_TIMEOUT} --log-level ${LOG_LEVEL} --limit-request-line 4094 --limit-request-fields 100 --max-requests 1000 --forwarded-allow-ips="${FORWARDED_ALLOW_IPS}" --preload --access-logfile - 'main:create_app()'
