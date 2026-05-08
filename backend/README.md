# PreventDM Backend

The Python FastAPI backend service for the PreventDM population health decision support platform. This service is the primary orchestration layer, sitting between the Flutter frontend and the downstream Rust validation and Python ML inference services. It handles authentication, business logic, and request routing across the system.

This is **Phase Three** of the build: a minimal, production-quality skeleton with one health endpoint, structured JSON logging, and environment-driven configuration. Database connectivity, authentication, inter-service communication, and business logic are added in later phases.

## Prerequisites

- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) — install with `pip install uv` or via the [official installer](https://docs.astral.sh/uv/getting-started/installation/)

## Installation

From the `backend/` directory, install all dependencies (production and dev) into a managed virtual environment:

```bash
uv sync --all-extras
```

This creates `.venv/`, installs everything declared in `pyproject.toml`, and installs the `preventdm-backend` package itself in editable mode so `importlib.metadata` can read its version.

## Configuration

Copy the example environment file and edit it as needed:

```bash
cp .env.example .env
```

| Variable    | Default             | Description                                                         |
|-------------|---------------------|---------------------------------------------------------------------|
| `APP_NAME`  | `PreventDM Backend` | Display name returned in API responses and OpenAPI docs title       |
| `APP_ENV`   | `development`       | Runtime environment: `development`, `staging`, or `production`      |
| `LOG_LEVEL` | `INFO`              | Log verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`  |

Settings are read from environment variables first, then from `.env` if present. Do not commit `.env` — it is listed in `.gitignore`.

## Running locally

Start the development server with hot-reload from the `backend/` directory:

```bash
uv run uvicorn app.main:app --reload
```

The service binds to `http://localhost:8000` by default.

## Verifying the service

**Health endpoint** — confirms the service is running and shows its identity:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok","service":"PreventDM Backend","environment":"development","version":"0.1.0"}
```

**Interactive API documentation** — FastAPI generates OpenAPI docs automatically:

```
http://localhost:8000/docs
```

The health endpoint will be listed there with its request and response schema.

## Linting

Check for lint issues:

```bash
uv run ruff check .
```

Auto-fix any fixable issues:

```bash
uv run ruff check --fix .
```

Check that formatting matches the project style (no changes applied):

```bash
uv run ruff format --check .
```

Apply formatting in place:

```bash
uv run ruff format .
```

## Type checking

Run mypy in strict mode against the application package:

```bash
uv run mypy app
```

## Project structure

```
backend/
├── pyproject.toml          # Package metadata, dependencies, ruff and mypy configuration
├── uv.lock                 # Locked dependency graph — commit this file
├── .env.example            # Documented template for local environment variables
├── .python-version         # Python version pin consumed by uv
└── app/
    ├── __init__.py
    ├── main.py             # Application factory (create_app) and uvicorn entry point
    ├── config.py           # Settings class backed by environment variables via pydantic-settings
    └── routers/
        ├── __init__.py
        └── health.py       # GET /health endpoint with typed response model
```

## What is deliberately excluded from Phase Three

- Database integration (PostgreSQL, Redis)
- Authentication and user management
- Inter-service HTTP communication (Rust validation service, ML inference service)
- Business logic (risk assessments, scoring, recommendations)
- Docker / docker-compose
- Tests and testing dependencies
- CI configuration

These are all added in subsequent phases once the skeleton is verified working.
