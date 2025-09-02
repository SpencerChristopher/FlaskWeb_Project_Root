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

# Create .pytest_cache directory and set permissions for appuser
RUN mkdir -p .pytest_cache && chown -R appuser:appuser .pytest_cache

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv ./.venv

# Copy the application source code
COPY ./src ./src
COPY ./tests ./tests
COPY ./scripts ./scripts
COPY ./static ./static
COPY ./templates ./templates

COPY ./main.py ./

# Make port 5000 available
EXPOSE 5000

# Define the command to run the application
# We use the full path to the gunicorn executable in the virtual environment
CMD ["/app/.venv/bin/gunicorn", "--bind", "0.0.0.0:5000", "main:wsgi_app"]

# Create .pytest_cache directory and set permissions for appuser
RUN mkdir -p .pytest_cache && chown -R appuser:appuser .pytest_cache