# ACEest Fitness &amp; Gym — CI/CD Pipeline

A Flask web application for **ACEest Fitness & Gym** with a complete,
automated DevOps workflow: version control (Git/GitHub), unit testing
(Pytest), containerization (Docker), a Jenkins BUILD stage, and a fully
automated CI/CD pipeline using GitHub Actions.

The application exposes the gym's core domain — **training programs**,
**client management**, and **workout tracking** — through a web page and a
small JSON REST API.

---

## Project Structure

```
.
├── aceest_fitness/            # Application package
│   ├── __init__.py            # Exposes the create_app() factory
│   ├── app.py                 # Flask factory + HTTP routes + error handling
│   ├── service.py             # Framework-agnostic domain/business logic
│   └── templates/
│       └── index.html         # Landing page
├── tests/                     # Pytest suite
│   ├── conftest.py            # Shared fixtures (isolated service per test)
│   ├── test_service.py        # Unit tests for the domain logic
│   └── test_api.py            # Integration tests for the HTTP endpoints
├── wsgi.py                    # WSGI entry point (used by Gunicorn)
├── requirements.txt           # Runtime dependencies
├── requirements-dev.txt       # Test/lint dependencies
├── Dockerfile                 # Production container image
├── .dockerignore
├── Jenkinsfile                # Jenkins BUILD pipeline
├── .github/workflows/main.yml # GitHub Actions CI/CD pipeline
├── pytest.ini
└── README.md
```

---

## Local Setup & Execution

### Prerequisites
- Python 3.12+
- (Optional) Docker for containerized runs

### 1. Create a virtual environment and install dependencies

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt -r requirements-dev.txt
```

### 2. Run the application (development)

```bash
python wsgi.py
```

The app starts on <http://localhost:5000>.

### 3. Run the application (production-style with Gunicorn)

```bash
gunicorn --bind 0.0.0.0:5000 wsgi:app
```

---

## Running the Tests Manually

The project uses **Pytest**. From the project root:

```bash
pytest
```

This runs both the unit tests (`tests/test_service.py`) covering the domain
logic and the integration tests (`tests/test_api.py`) covering every HTTP
endpoint, including validation, duplicate, and not-found error paths.

Lint the code with:

```bash
flake8 aceest_fitness wsgi.py --select=E9,F63,F7,F82
```

---

## Running with Docker

Build the image:

```bash
docker build -t aceest-fitness:latest .
```

Run the container:

```bash
docker run --rm -p 5000:5000 aceest-fitness:latest
```

Verify it is healthy:

```bash
curl http://localhost:5000/health
# {"service":"ACEest Fitness & Gym","status":"ok"}
```

The image is built on `python:3.12-slim`, runs as a non-root user, uses
layer caching for dependencies, and ships with a container `HEALTHCHECK`
for an optimized, secure footprint.

---

## API Reference

| Method | Endpoint                          | Description                        |
| ------ | --------------------------------- | ---------------------------------- |
| GET    | `/`                               | Landing page (HTML)                |
| GET    | `/health`                         | Health check (JSON)                |
| GET    | `/api/programs`                   | List all training programs         |
| GET    | `/api/programs/<name>`            | Get a single program               |
| GET    | `/api/clients`                    | List all clients                   |
| POST   | `/api/clients`                    | Add a client `{name, program?}`    |
| GET    | `/api/clients/<name>`             | Get a single client                |
| POST   | `/api/clients/<name>/program`     | Assign a program `{program}`       |
| GET    | `/api/clients/<name>/workouts`    | List a client's workouts           |
| POST   | `/api/clients/<name>/workouts`    | Log a workout                      |

Example — add a client and log a workout:

```bash
curl -X POST http://localhost:5000/api/clients \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","program":"Muscle Gain"}'

curl -X POST http://localhost:5000/api/clients/Alice/workouts \
  -H "Content-Type: application/json" \
  -d '{"workout_type":"Strength","duration_min":60,"notes":"Leg day"}'
```

---

## CI/CD & Jenkins Integration Overview

The project uses **two complementary automation layers**:

### 1. GitHub Actions — Continuous Integration/Delivery
Defined in [.github/workflows/main.yml](.github/workflows/main.yml) and
triggered on **every push and pull request**. Stages:

1. **Build & Lint** — set up Python, install dependencies, and run `flake8`
   to catch syntax errors and undefined names.
2. **Automated Testing** — run the full Pytest suite.
3. **Docker Image Assembly** — build the Docker image (`docker` job, runs
   only after build/test succeeds).
4. **Containerized Testing & Smoke Test** — run Pytest *inside* the built
   container and hit the `/health` endpoint of the running container to
   confirm the image is deployable.

### 2. Jenkins — BUILD & Quality Gate
Defined in the [Jenkinsfile](Jenkinsfile), a Jenkins project pulls the
latest code from GitHub and performs a clean build as a secondary
validation layer. Stages: `Checkout → Set up Python → Lint → Test →
Build Docker Image → Verify Image`. The `post` block always cleans up the
container and virtual environment, and reports BUILD SUCCESS/FAILURE.

**How they work together:** GitHub Actions provides fast, per-commit CI
feedback for every developer and pull request, while Jenkins acts as the
controlled, authoritative BUILD/quality gate that recreates the
environment from scratch and verifies the final Docker artifact before
delivery.

---

## Design Notes

- **Modularity:** Business logic lives in `service.py`, decoupled from
  Flask, so it is independently unit-testable. The app uses the
  application-factory pattern (`create_app`) for clean configuration and
  test isolation.
- **Error handling:** Domain errors map to proper HTTP status codes
  (`400` validation, `404` not found, `409` duplicate).
- **State:** An in-memory, thread-safe store keeps the service
  container-friendly and free of external dependencies for CI.
