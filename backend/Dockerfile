# =============================================================================
# Build stage: install Python dependencies using uv
#
# We use a two-stage build so the final runtime image contains only the
# installed packages and application code, not uv itself, the lock file, or
# any build-time tooling.
# =============================================================================
FROM python:3.12-slim AS builder

WORKDIR /app

# Copy the uv binary from the official image. This is the recommended pattern
# for getting uv into a container without running an install script.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Tell uv to use only the Python already present in the base image and never
# attempt to download a managed Python version.
ENV UV_PYTHON_PREFERENCE=only-system

# Copy dependency manifests first. Because these files change far less often
# than application code, Docker caches the dependency installation layer
# independently. A code-only change will reuse this layer on the next build.
COPY pyproject.toml uv.lock README.md ./

# Install runtime dependencies into /app/.venv.
#   --frozen          : respect the lock file exactly; never update it
#   --no-install-project : skip installing the project package itself at this
#                       stage (the app/ directory is not present yet)
#   --no-dev          : exclude dev-only groups such as ruff and mypy
RUN uv sync --frozen --no-dev

# Copy application code in a separate step. This layer is invalidated only
# when src files change, not when pyproject.toml or uv.lock change.
COPY app/ ./app/


# =============================================================================
# Runtime stage: minimal image that only runs the service
# =============================================================================
FROM python:3.12-slim AS runtime

# Send Python output directly to the container's stdout without buffering.
# Essential for real-time log streaming in container environments.
ENV PYTHONUNBUFFERED=1

# Prevent Python from writing .pyc bytecode files inside the container.
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Create a non-root system user with no home directory and no login shell.
# Running containers as root is a security anti-pattern; this follows the
# principle of least privilege.
RUN useradd --system --no-create-home --shell /bin/false appuser

# Copy the populated virtual environment from the build stage and set
# ownership so the non-root user can read all files.
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy application source code with correct ownership.
COPY --chown=appuser:appuser app/ ./app/

# Add the virtual environment's bin directory to PATH so that uvicorn and all
# other installed entry points are resolved without an explicit path prefix.
ENV PATH="/app/.venv/bin:$PATH"

# Switch to the non-root user for all subsequent instructions and at runtime.
USER appuser

# Document the port this service listens on.
EXPOSE 8000

# Start uvicorn bound to all interfaces (0.0.0.0) so the container port is
# reachable from the host via the -p flag. JSON array form avoids spawning an
# intermediate shell process.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
