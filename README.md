# Flask Web Project

## Description

This project is a personal website and blog built using the Flask web framework, MongoDB as the database, and a JavaScript Single Page Application (SPA) for the frontend. It features a public-facing blog, **JWT-based user authentication with role-based access control (RBAC)**, and an administrative panel for managing blog posts. The backend incorporates an **Observer design pattern** for decoupled event handling.

## Features

*   **Blog**: Display blog posts with titles, summaries, content, and publication dates.
*   **User Authentication**: Secure **JWT-based** login with **Role-Based Access Control (RBAC)** for administrators and other user roles.
*   **Admin Panel**: Create, edit, and delete blog posts.
*   **Single Page Application (SPA)**: Dynamic content loading without full page reloads, providing a smooth user experience.
*   **Dockerized Environment**: Easy setup and deployment using Docker Compose for both the Flask application and MongoDB.
*   **Event-Driven Architecture**: Backend utilizes an **Observer design pattern** for decoupled and extensible event handling (e.g., logging, future notifications).

## Technologies Used

*   **Backend**: Flask (Python)
*   **Database**: MongoDB
*   **Authentication**: Flask-JWT-Extended, Flask-Bcrypt
*   **Database Driver**: Flask-MongoEngine
*   **Dependency Management**: Poetry
*   **Containerization**: Docker, Docker Compose
*   **Event Handling**: Custom Observer Pattern Implementation
*   **Frontend**: HTML, CSS (Bootstrap), JavaScript (Vanilla SPA)

## Setup and Installation

Follow these steps to get the project up and running on your local machine.

### Prerequisites

*   [Docker Desktop](https://www.docker.com/products/docker-desktop) (includes Docker Engine and Docker Compose)
*   [Python 3.10+](https://www.python.org/downloads/)
*   [Poetry](https://python-poetry.org/docs/#installation) (Python package manager)

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/your-repo-name.git # Replace with your actual repo URL
cd FlaskWeb_Project_Root
```

### 2. Set up Environment Variables

Create a `.env` file in the project root directory (`FlaskWeb_Project_Root/`) based on `.env.template`.

```bash
cp .env.template .env
```

Edit the `.env` file and fill in the necessary values. **Ensure `MONGO_URI`, `ADMIN_USERNAME`, and `ADMIN_PASSWORD` are set.**

```dotenv
SECRET_KEY=your_flask_secret_key_here # IMPORTANT: Change this to a strong, random key (used for Flask sessions and JWT signing)
PORT=5000

ADMIN_USERNAME=admin # Default admin username for seeding
ADMIN_PASSWORD=admin # Default admin password for seeding

MONGO_URI=mongodb://mongo:27017/appdb # Connection string for MongoDB (used by Flask-MongoEngine)

# Optional: External API keys if your project expands
KAGGLE_API_KEY=
LINKEDIN_API_TOKEN=
LEETCODE_SESSION=
HTB_TOKEN=
```

### 3. Build and Run Docker Containers

Navigate to the project root directory in your terminal and start the Docker containers:

```bash
docker-compose -f docker-compose.db.yml up -d
docker-compose up -d
```

### 4. Install Python Dependencies

Install the project's Python dependencies using Poetry:

```bash
poetry install
```

### 5. Seed the Database

Run the seeding script to populate the MongoDB with initial data (e.g., a sample blog post and an admin user).

```bash
# Ensure your MongoDB container is running: docker-compose up -d mongo

# 1. Drop existing database (optional, but recommended for a clean start)
poetry run python scripts/drop_db.py

# 2. Create the initial admin user
poetry run python scripts/create_admin.py

# 3. Seed initial data (sample posts)
poetry run python scripts/seed_db.py
```

### 6. Access the Application

Once all services are up and the database is seeded, you can access the application in your web browser:

```bash
# Run the Flask application (ensure your venv is activated)
poetry run python main.py
```

```
http://localhost:5000
```

## Usage

### Public Blog

Navigate to the home page. You should see the blog posts listed. Click on a post to view its full content.

### Admin Panel

1.  Go to `http://localhost:5000/#login`.
2.  Log in with the admin credentials set in your `.env` file (default: `username=admin`, `password=admin`).
3.  Log in with the admin credentials set in your `.env` file (default: `username=admin`, `password=admin`). Upon successful login, a JWT (JSON Web Token) will be issued and managed by the frontend. You will then be redirected to the admin dashboard where you can manage posts.

## Project Structure

```
. # Project Root
├── src/                    # Main application source code
│   ├── models/             # Database models (Post, User)
│   ├── routes/             # Flask blueprints for API and web routes
│   ├── utils/              # Utility functions (e.g., logger)
│   ├── extensions/         # Centralized Flask extension instances (db, bcrypt, jwt)
│   ├── events/             # Event definitions for Observer pattern
│   ├── listeners/          # Event listeners for Observer pattern
│   └── __init__.py         # Flask app creation and configuration
├── scripts/                # Utility scripts
│   ├── create_admin.py     # Script to create initial admin user
│   ├── seed_db.py          # Script to seed initial data
│   ├── clear_applog.py     # Script to clear application log file
│   └── drop_db.py          # Script to drop the entire database
├── static/                 # Frontend static files (JS, CSS, images)
├── templates/              # Jinja2 templates for the base HTML structure
├── .env                    # Environment variables (local, sensitive)
├── .env.template           # Template for .env
├── docker-compose.db.yml   # Docker Compose configuration for MongoDB
├── docker-compose.yml      # Docker Compose configuration for the Flask app
├── Dockerfile              # Dockerfile for the Flask application
├── main.py                 # Main application entry point (formerly app.py)
├── pyproject.toml          # Poetry project configuration
├── poetry.lock             # Poetry lock file for consistent dependencies
├── pytest.ini              # Pytest configuration
├── README.md               # Project README file
└── .gitignore              # Git ignore rules
```

## Contributing

Contributions are welcome! Please follow these steps:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'feat: Add new feature'`).
5.  Push to the branch (`git push origin feature/your-feature-name`).
6.  Open a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

*   [Start Bootstrap - Creative Theme](https://startbootstrap.com/theme/creative) for the base HTML/CSS template.
*   [Flask](https://flask.palletsprojects.com/) for the web framework.
*   [MongoDB](https://www.mongodb.com/) for the database.
*   **Special thanks to Google and the Gemini team for the development and assistance provided through the [Gemini CLI](https://github.com/google/generative-ai-docs).**
