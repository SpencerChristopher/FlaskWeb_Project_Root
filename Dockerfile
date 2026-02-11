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
RUN chown -R appuser:appuser /app
# Create logs directory and set permissions for appuser
RUN mkdir -p logs && chown -R appuser:appuser logs
USER appuser

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv ./.venv

# Copy the application source code
COPY ./src ./src
COPY ./scripts ./scripts
COPY ./static ./static
COPY ./templates ./templates
COPY ./tests ./tests

COPY ./main.py ./

# Make port 443 available
EXPOSE 443

# Define the command to run the application
# We use the full path to the gunicorn executable in the virtual environment
# Define the command to run the application. This uses a shell script to allow
# for conditional logic based on the RUN_MODE environment variable.
CMD if [ "$RUN_MODE" = "https" ]; then \
        echo "Starting Gunicorn in HTTPS mode..."; \
        exec /app/.venv/bin/gunicorn --bind 0.0.0.0:443 --workers 4 --log-level debug --access-logfile - --certfile /app/certs/server.crt --keyfile /app/certs/server.key main:wsgi_app; \
    else \
        echo "Starting Gunicorn in HTTP mode..."; \
        exec /app/.venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 4 --log-level debug --access-logfile - main:wsgi_app; \
    fi