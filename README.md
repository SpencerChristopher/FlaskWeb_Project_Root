# Flask Web Project

## Description

This project is a personal website and blog built with Flask and MongoDB, featuring a decoupled frontend and a JSON-based API. The backend leverages **Pydantic** for robust data validation, **Blinker** for a signal-based event-driven architecture, and **JWT** for secure authentication. The frontend is a vanilla JavaScript Single Page Application (SPA).

## Features

*   **API-First Design**: A comprehensive JSON API serves all public and administrative content.
*   **Pydantic Validation**: All API inputs, especially for CRUD operations, are strictly validated using Pydantic models, ensuring data integrity and security.
*   **Event-Driven Architecture**: Utilizes the **Blinker** signaling library to decouple application components. Events are dispatched for actions like user logins and post modifications, allowing for extensible and maintainable code.
*   **User Authentication**: Secure JWT-based login with role-based access control (RBAC) implemented via custom claims in the JSON Web Token.
*   **Admin Panel**: A secure area for administrators to perform full CRUD (Create, Read, Update, Delete) operations on blog posts.
*   **Security Hardening**: Includes rate limiting on sensitive endpoints with **Flask-Limiter** and HTML sanitization with **Bleach** to prevent XSS attacks.
*   **Single Page Application (SPA)**: The frontend dynamically renders content without full page reloads, providing a smooth user experience.
*   **Dockerized Environment**: Easy setup and deployment using Docker Compose, with **Nginx** terminating HTTPS and proxying to the Flask API.

## Technologies Used

*   **Backend**: Flask (Python)
*   **Database**: MongoDB with Flask-MongoEngine
*   **API Validation**: Pydantic
*   **Authentication**: Flask-JWT-Extended, Flask-Bcrypt
*   **Event Handling**: Blinker
*   **Security**: Flask-Limiter, Bleach
*   **Dependency Management**: Poetry
*   **Containerization**: Docker, Docker Compose, Nginx
*   **Testing**: Pytest, pytest-flask
*   **Frontend**: HTML, CSS, JavaScript (Vanilla SPA)

## Setup with Docker (Recommended for Local Development)

This is the recommended way to run the project for local development and QA. The environment is fully containerized, allowing for consistent setup. Nginx terminates HTTPS on `:443` and proxies to the Flask API.

**Understanding Docker Compose Files:**
*   **`docker-compose.yml`**: This is the base configuration file. For local development, it now directly contains the `build: .` context for the `web` service.
*   **`docker-compose.override.yml`**: (Generated from `docker-compose.override.yml.template`) This file **overrides** settings in `docker-compose.yml` for local development. It sets up volume mounts for live reloading, development-specific environment variables (e.g., `FLASK_ENV=development`), and exposes additional ports.


## Deployment & CI/CD

See `docs/DEPLOYMENT.md` for CI/CD flow, runner expectations, and production deployment notes.

## CI/CD Preflight (Local)

To avoid trial-and-error on GitHub Actions, run a local preflight before pushing:

Windows PowerShell:
```powershell
.\scripts\preflight_ci.ps1
```

macOS/Linux:
```bash
./scripts/preflight_ci.sh
```

Optional local workflow run:
```powershell
.\scripts\preflight_ci.ps1 -RunAct
```
```bash
./scripts/preflight_ci.sh -RunAct
```

### Prerequisites

*   Docker Desktop

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/your-repo-name.git # Replace with your actual repo URL
cd FlaskWeb_Project_Root
```

### 2. Set up Environment Variables

For local development, you will typically need a `.env` file to store sensitive secrets and to set local overrides for environment variables defined in `docker-compose.yml`.

*   **`docker-compose.yml`**: This file now centrally defines all non-secret default environment variables for the application (e.g., `LOG_LEVEL`, `FLASK_ENV`, `GUNICORN_TIMEOUT`). These values are used by default in both CI/CD and local environments.
*   **`.env`**: This file is for **local overrides and sensitive secrets only**. It is not committed to Git.
*   **`config.env`**: This file serves as a **reference** for all non-secret defaults. You can copy its contents into your local `.env` file as a starting point if you wish to override `docker-compose.yml` defaults, then add your secrets.

**Steps:**

1.  **Create your local `.env` file:**
    ```bash
    cp .env.template .env
    ```
2.  **Edit the `.env` file:** Open the newly created `.env` file and fill in your specific values. **Ensure that `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `MONGO_ROOT_USER`, `MONGO_ROOT_PASSWORD`, `MONGO_APP_USER`, and `MONGO_APP_PASSWORD` are always set**, as these are critical for application functionality and security.

**Required `.env` values (minimum):**
- `SECRET_KEY`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `MONGO_ROOT_USER`
- `MONGO_ROOT_PASSWORD`
- `MONGO_APP_USER`
- `MONGO_APP_PASSWORD`

### 3. Build and Run Containers

Before running, ensure you have created your local `docker-compose.override.yml` and generated SSL certificates for Nginx.

1.  **Create your local `docker-compose.override.yml`:**
    ```bash
    cp docker-compose.override.yml.template docker-compose.override.yml
    ```
2.  **Generate Self-Signed SSL Certificates:**
    Nginx expects certs at `./certs/server.crt` and `./certs/server.key`.
    ```bash
    mkdir -p certs
    openssl genrsa -out certs/server.key 2048
    openssl req -x509 -sha256 -nodes -days 365 -new -key certs/server.key -out certs/server.crt -subj "/C=US/ST=State/L=City/O=Organization/OU=Unit/CN=localhost"
    ```
3.  **Build and Run Services:**
    Build the images and start the services in detached mode. Docker Compose will automatically detect and merge `docker-compose.override.yml`, ensuring the `web` service is built locally and source code volumes are mounted for live reloading.

    ```bash
    docker compose --env-file ./.env up --build -d
    ```

    The application will be available at `https://localhost` (self-signed cert in dev).

    To verify:
    ```bash
    curl -k -I https://localhost/
    ```

### 4. Seed the Database

Run the following commands to initialize the database by executing the scripts inside the running `web` container.

```bash
# 1. Drop existing database (optional, for a clean start)
docker compose exec web /app/.venv/bin/python scripts/drop_db.py

# 2. Create the initial admin user (credentials from .env)
docker compose exec web /app/.venv/bin/python scripts/create_admin.py

# 3. Seed initial data (sample posts)
docker compose exec web /app/.venv/bin/python scripts/seed_db.py
```

To stop the services, run:
```bash
docker compose down
```

## Usage

### Public Blog

Navigate to `https://localhost`. The SPA will fetch and display a list of blog posts. Click on a post to view its full content.

### Admin Panel

1.  Go to `https://localhost/#login`.
2.  Log in with the admin credentials set in your `.env` file.
3.  Upon successful login, a JWT will be stored by the frontend, and you will be redirected to the admin dashboard to manage posts.

## Project Structure

```
. # Project Root
+-- src/                      # Main application source code
¦   +-- models/               # MongoEngine database models (Post, User)
¦   +-- routes/               # Flask blueprints for API routes
¦   +-- schemas.py            # Pydantic schemas for API validation
¦   +-- exceptions.py         # Custom application exception classes
¦   +-- events.py             # Blinker signal definitions
¦   +-- listeners.py          # Blinker signal listeners
¦   +-- extensions.py         # Centralized Flask extension instances
¦   +-- utils/                # Utility functions (e.g., logger)
¦   +-- server.py             # Flask app factory and configuration
+-- scripts/                  # Utility scripts (seeding, admin creation)
+-- static/                   # Frontend static files (JS, CSS)
+-- templates/                # Base Jinja2 template for the SPA shell
+-- docker/                   # Docker assets (nginx config, mongo init)
¦   +-- nginx/nginx.conf       # TLS proxy config
¦   +-- mongo/mongo-init.js    # Mongo init script
+-- certs/                    # TLS certs (self-signed for dev/CI)
+-- .env                      # Environment variables (local, sensitive)
+-- .env.template             # Template for .env
+-- config.env                # Non-secret defaults shared across envs
+-- docker-compose.yml        # Main Docker Compose (prod-like)
+-- docker-compose.override.yml.template # Optional dev overrides
+-- Dockerfile                # Dockerfile for the Flask application
+-- main.py                   # Main application entry point (gunicorn)
+-- pyproject.toml            # Poetry project configuration
+-- pytest.ini                # Pytest configuration
+-- README.md                 # This file
```

## Contributing

Contributions are welcome! Please fork the repository, create a feature branch, and open a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

*   Special thanks to Google and the Gemini team for the development and assistance provided through the Gemini CLI.


