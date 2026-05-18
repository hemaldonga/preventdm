# PreventDM CLI

A developer-facing test harness that verifies the PreventDM assessment pipeline end-to-end by sending real HTTP requests to the running service stack.

## What it does

The CLI provides two commands:

- **health** — checks that all three services (backend, rust_service, ml_service) respond to `GET /health` with HTTP 200 and `{"status": "ok"}`.
- **test-pipeline** — runs a numbered sequence of nine checks against the live stack, stops on the first failure (because later checks depend on earlier ones), prints a per-check result as each one completes, and finishes with a summary table and an overall PASSED/FAILED verdict.

The tool exits with code **0** on full success and **non-zero** on any failure, making it safe to use in CI pipelines.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- A running PreventDM stack (`docker compose up -d` from the project root)

## Installation

From inside the `cli/` directory:

```bash
uv sync
```

This creates a `.venv` and installs all runtime and dev dependencies.

## Usage

All commands are run from inside `cli/` using `uv run`.

### Health check

```bash
uv run preventdm-cli health
```

By default the command targets services at their standard local ports.  Override with options:

```bash
uv run preventdm-cli health \
  --backend-url http://localhost:8000 \
  --rust-url    http://localhost:8001 \
  --ml-url      http://localhost:8002 \
  --timeout     10.0
```

### End-to-end pipeline test

```bash
uv run preventdm-cli test-pipeline
```

Available options:

| Option | Default | Description |
|---|---|---|
| `--backend-url` | `http://localhost:8000` | Backend service URL |
| `--rust-url` | `http://localhost:8001` | Rust service URL |
| `--ml-url` | `http://localhost:8002` | ML service URL |
| `--timeout` | `10.0` | Per-request timeout in seconds |
| `--patient-id` | `PREVENTDM-CLI-TEST` | External patient ID used in test data |

The `--patient-id` option lets you avoid colliding with real patient records when running the harness against a non-empty database.

## The nine pipeline checks

| # | Name | What it verifies |
|---|---|---|
| 1 | Backend health | `GET /health` → HTTP 200, `status="ok"` |
| 2 | Rust service health | `GET /health` → HTTP 200, `status="ok"` |
| 3 | ML service health | `GET /health` → HTTP 200, `status="ok"` |
| 4 | Assessment submission | `POST /assess` → HTTP 200, response has `assessment_id`, `patient_external_id`, timestamp, `validated_features`, `clinical_scores`, `ml_prediction` |
| 5 | Assessment retrieval | `GET /assess/{id}` → HTTP 200, all three score types present, probability in [0, 1] |
| 6 | Data consistency | Fields in the POST response match fields in the GET response (patient ID, timestamp, probability, risk categories) |
| 7 | Upstream error handling | `POST /assess` with empty payload → HTTP 422 with `detail` field |
| 8 | Invalid ID handling | `GET /assess/00000000-0000-0000-0000-000000000000` → HTTP 404 |
| 9 | Malformed ID handling | `GET /assess/not-a-valid-uuid` → HTTP 422 |

## Development

Run linting and type checks from inside `cli/`:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy preventdm_cli
```

Auto-fix import ordering:

```bash
uv run ruff check . --fix
uv run ruff format .
```
