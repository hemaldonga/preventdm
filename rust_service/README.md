# PreventDM Validation Service

The Rust Axum service for the PreventDM population health decision support platform. In the full system this service sits downstream of the Python FastAPI backend and provides input validation, multi-score clinical risk computation, and the Rust-side performance-critical path. It communicates with the Python ML inference service for model predictions.

This is **Phase Four** of the build: a minimal, production-quality skeleton with one health endpoint, environment-driven configuration, and structured tracing output. Validation logic, clinical score computation, inter-service communication, and database access are added in later phases.

The Python FastAPI backend (Phase Three) runs on port 8000. This service runs on port 8001 to avoid collision.

## Prerequisites

- [Rust toolchain](https://rustup.rs/) — install via `rustup` if not already present:

  ```bash
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
  ```

  The `rust-toolchain.toml` file in this directory pins the toolchain to a specific stable version. `rustup` will download and activate it automatically on first use.

- `cargo` is bundled with the Rust toolchain and requires no separate installation.

## Building

From the `rust_service/` directory:

```bash
cargo build
```

For a release build:

```bash
cargo build --release
```

## Configuration

Copy the example environment file and edit it as needed:

```bash
cp .env.example .env
```

| Variable      | Default                        | Description                                                              |
|---------------|--------------------------------|--------------------------------------------------------------------------|
| `APP_NAME`    | `PreventDM Validation Service` | Display name returned in health responses                                |
| `APP_ENV`     | `development`                  | Runtime environment: `development`, `staging`, or `production`           |
| `LOG_LEVEL`   | `info`                         | Log verbosity: `trace`, `debug`, `info`, `warn`, or `error`             |
| `SERVER_PORT` | `8001`                         | TCP port to bind; must not collide with port 8000 used by the Python backend |

The service reads directly from environment variables. To load a `.env` file before running, either source it in your shell (`export $(cat .env | xargs)`) or use a tool such as `direnv`.

## Running locally

```bash
cargo run
```

The server binds to `0.0.0.0:8001` by default and logs a startup message:

```
INFO preventdm_rust_service: server started service="PreventDM Validation Service" address=0.0.0.0:8001
```

To use a different port:

```bash
SERVER_PORT=9001 cargo run
```

## Verifying the service

**Health endpoint** — confirms the service is running and shows its identity:

```bash
curl http://localhost:8001/health
```

Expected response:

```json
{"status":"ok","service":"PreventDM Validation Service","environment":"development","version":"0.1.0"}
```

## Formatting

Check that code matches the project style without applying changes:

```bash
cargo fmt --check
```

Apply formatting in place:

```bash
cargo fmt
```

## Linting

Run Clippy in pedantic mode (all lints treated as errors):

```bash
cargo clippy --all-targets --all-features -- -D warnings
```

## Project structure

```
rust_service/
├── Cargo.toml              # Package manifest and dependency versions
├── Cargo.lock              # Locked dependency graph — commit this file
├── rust-toolchain.toml     # Pinned Rust toolchain version for rustup
├── .env.example            # Documented template for local environment variables
└── src/
    ├── main.rs             # Tokio entry point: loads config, starts server
    ├── config.rs           # Config struct read from environment variables
    ├── error.rs            # ConfigError and AppError types
    └── routes/
        ├── mod.rs          # Re-exports router for use in main.rs
        └── health.rs       # GET /health handler and HealthResponse struct
```

## What is deliberately excluded from Phase Four

- Validation logic (input schema checks, business rules)
- Clinical risk score computations (FINDRISC, ADA screening, etc.)
- Inter-service HTTP communication (Python FastAPI backend, ML inference service)
- Database integration (PostgreSQL, Redis)
- Authentication and authorisation
- Docker / docker-compose
- Tests beyond the standard toolchain
- CI configuration

These are all added in subsequent phases once the skeleton is verified working.
