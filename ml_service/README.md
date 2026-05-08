# PreventDM ML Inference Service

The Python FastAPI ML inference service for the PreventDM population health decision support platform. In the full system this service sits downstream of the Python FastAPI backend and provides diabetes risk probability estimates, SHAP-based feature explanations, and confidence intervals for individual patient assessments.

This is **Phase Five** of the build: a minimal, production-quality skeleton with one health endpoint, environment-driven configuration, and structured JSON logging. **No machine learning code exists yet.** Model loading, inference, feature preprocessing, and SHAP explanations are all added in later phases.

The Python FastAPI backend (Phase Three) runs on port 8000. The Rust validation service (Phase Four) runs on port 8001. This service runs on port 8002.

## Prerequisites

- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) — install with `pip install uv` or via the [official installer](https://docs.astral.sh/uv/getting-started/installation/)

## Installation

From the `ml_service/` directory:

```bash
uv sync --all-extras
```

This creates `.venv/`, installs all production and development dependencies, and installs the `preventdm-ml-service` package in editable mode so `importlib.metadata` can read its version.

## Configuration

Copy the example environment file and edit it as needed:

```bash
cp .env.example .env
```

| Variable    | Default                | Description                                                         |
|-------------|------------------------|---------------------------------------------------------------------|
| `APP_NAME`  | `PreventDM ML Service` | Display name returned in API responses and OpenAPI docs title       |
| `APP_ENV`   | `development`          | Runtime environment: `development`, `staging`, or `production`      |
| `LOG_LEVEL` | `INFO`                 | Log verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`  |
| `PORT`      | `8002`                 | Documented default port; pass to uvicorn via `--port` on the CLI    |

## Running locally

```bash
uv run uvicorn app.main:app --reload --port 8002
```

The service will be available at `http://localhost:8002`.

## Verifying the service

**Health endpoint** — confirms the service is running and shows its identity:

```bash
curl http://localhost:8002/health
```

Expected response:

```json
{"status":"ok","service":"PreventDM ML Service","environment":"development","version":"0.1.0"}
```

**Interactive API documentation** — FastAPI generates OpenAPI docs automatically:

```
http://localhost:8002/docs
```

## Linting

```bash
uv run ruff check .
uv run ruff format --check .
```

## Type checking

```bash
uv run mypy app
```

## Project structure

```
ml_service/
├── pyproject.toml          # Package metadata, dependencies, ruff and mypy configuration
├── uv.lock                 # Locked dependency graph — commit this file
├── .env.example            # Documented template for local environment variables
├── .python-version         # Python version pin for uv
└── app/
    ├── __init__.py
    ├── main.py             # Application factory (create_app) and uvicorn entry point
    ├── config.py           # Settings class backed by environment variables
    └── routers/
        ├── __init__.py
        └── health.py       # GET /health endpoint with typed response model
```

## What is deliberately excluded from Phase Five

- Machine learning model loading and inference (scikit-learn, XGBoost, LightGBM)
- SHAP feature explanation computation
- Feature preprocessing and validation pipelines
- Prediction endpoints (`POST /predict`, etc.)
- Database integration (PostgreSQL, Redis)
- Inter-service HTTP communication (FastAPI backend, Rust service)
- Authentication and authorisation
- Docker / docker-compose
- Tests and testing dependencies
- CI configuration

These are all added in subsequent phases once the skeleton is verified working.
