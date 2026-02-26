# --- Builder Stage ---
# This stage installs dependencies using Poetry
FROM python:3.11-slim-buster AS builder

# Set the working directory
WORKDIR /app

# Install poetry
RUN pip install poetry

# Copy only the dependency definition files to leverage Docker cache
COPY poetry.lock pyproject.toml ./

# Install dependencies into a virtual environment
# --no-root is important to avoid installing the project itself, just the deps
# --no-dev is used to skip development dependencies in the final image
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
RUN poetry install --no-root

# --- Final Stage ---
# This stage creates the final, lean production image
FROM python:3.11-slim-buster

# Set the working directory
WORKDIR /app

# Create a non-root user to run the application
RUN useradd --create-home appuser
# Create necessary directories and set permissions for appuser
RUN mkdir -p logs static/uploads && chown -R appuser:appuser /app
USER appuser

ARG LOG_LEVEL=INFO
ENV LOG_LEVEL=$LOG_LEVEL
ENV GUNICORN_TIMEOUT=30

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
CMD exec /app/.venv/bin/gunicorn --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS} --timeout ${GUNICORN_TIMEOUT} --log-level ${LOG_LEVEL} --access-logfile - 'main:create_app()'
