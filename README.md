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
*   **Dockerized Environment**: Easy setup and deployment using Docker Compose for both the Flask application and MongoDB.

## Technologies Used

*   **Backend**: Flask (Python)
*   **Database**: MongoDB with Flask-MongoEngine
*   **API Validation**: Pydantic
*   **Authentication**: Flask-JWT-Extended, Flask-Bcrypt
*   **Event Handling**: Blinker
*   **Security**: Flask-Limiter, Bleach
*   **Dependency Management**: Poetry
*   **Containerization**: Docker, Docker Compose
*   **Testing**: Pytest, pytest-flask
*   **Frontend**: HTML, CSS, JavaScript (Vanilla SPA)

## Setup and Installation

Follow these steps to get the project up and running on your local machine.

### Prerequisites

*   [Docker Desktop](https://www.docker.com/products/docker-desktop)
*   [Python 3.10+](https://www.python.org/downloads/)
*   [Poetry](https://python-poetry.org/docs/#installation)

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/your-repo-name.git # Replace with your actual repo URL
cd FlaskWeb_Project_Root
```

### 2. Set up Environment Variables

Create a `.env` file in the project root from the template.

```bash
cp .env.template .env
```

Edit the `.env` file and fill in the necessary values. **Ensure `MONGO_URI`, `ADMIN_USERNAME`, and `ADMIN_PASSWORD` are set.** A strong `SECRET_KEY` is critical for security.

### 3. Build and Run Docker Containers

Start the MongoDB database container first, followed by the main application container.

```bash
docker-compose -f docker-compose.db.yml up -d
docker-compose up -d
```

### 4. Install Python Dependencies

Install the project's Python dependencies using Poetry.

```bash
poetry install
```

### 5. Seed the Database

Run the following scripts to initialize the database, create the admin user, and seed sample data.

```bash
# 1. Drop existing database (optional, for a clean start)
poetry run python scripts/drop_db.py

# 2. Create the initial admin user (credentials from .env)
poetry run python scripts/create_admin.py

# 3. Seed initial data (sample posts)
poetry run python scripts/seed_db.py
```

### 6. Access the Application

Run the Flask application using the Poetry environment.

```bash
poetry run python main.py
```

The application will be available at `http://localhost:5000`.

## Usage

### Public Blog

Navigate to the home page. The SPA will fetch and display a list of blog posts. Click on a post to view its full content.

### Admin Panel

1.  Go to `http://localhost:5000/#login`.
2.  Log in with the admin credentials set in your `.env` file.
3.  Upon successful login, a JWT will be stored by the frontend, and you will be redirected to the admin dashboard to manage posts.

## Project Structure

```
. # Project Root
├── src/                    # Main application source code
│   ├── models/             # MongoEngine database models (Post, User)
│   ├── routes/             # Flask blueprints for API and web routes
│   ├── schemas.py          # Pydantic schemas for API validation
│   ├── exceptions.py       # Custom application exception classes
│   ├── events.py           # Blinker signal definitions
│   ├── listeners.py        # Blinker signal listeners
│   ├── extensions/         # Centralized Flask extension instances
│   ├── utils/              # Utility functions (e.g., logger)
│   └── __init__.py         # Flask app factory and configuration
├── scripts/                # Utility scripts (seeding, admin creation)
├── static/                 # Frontend static files (JS, CSS)
├── templates/              # Base Jinja2 template for the SPA shell
├── .env                    # Environment variables (local, sensitive)
├── .env.template           # Template for .env
├── docker-compose.db.yml   # Docker Compose for MongoDB
├── docker-compose.yml      # Docker Compose for the Flask app
├── Dockerfile              # Dockerfile for the Flask application
├── main.py                 # Main application entry point
├── pyproject.toml          # Poetry project configuration
├── pytest.ini              # Pytest configuration
├── README.md               # This file
└── .gitignore              # Git ignore rules
```

## Contributing

Contributions are welcome! Please fork the repository, create a feature branch, and open a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

*   **Special thanks to Google and the Gemini team for the development and assistance provided through the Gemini CLI.**