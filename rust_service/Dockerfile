# =============================================================================
# Build stage: compile the Rust binary
#
# We use a two-stage build so the final runtime image is a minimal Debian
# image containing only the compiled binary, not the Rust toolchain (~1 GB).
# =============================================================================
FROM rust:1.85-slim-bookworm AS builder

WORKDIR /app

# Copy Cargo manifests first. The dependency compilation step below is cached
# as long as these two files do not change, which is the common case.
COPY Cargo.toml Cargo.lock ./

# Copy .cargo/config.toml. This file configures the MinGW-w64 linker used on
# the Windows development machine. The [target.x86_64-pc-windows-gnu] section
# is silently ignored on Linux and has no effect on this build.
COPY .cargo/ ./.cargo/

# Pre-compile all crate dependencies using a minimal stub binary.
# The stub compiles cleanly and caches the heavy dependency build layer.
# We then delete the stub artifacts so the next cargo build compiles the
# real application code on top of the already-compiled dependency objects.
RUN mkdir -p src && \
    echo "fn main() {}" > src/main.rs && \
    cargo build --release && \
    rm -rf src target/release/.fingerprint/preventdm-rust-service*

# Copy the real application source code.
COPY src/ ./src/

# Recompile. Only the application crate is rebuilt; all dependency object
# files are reused from the cached layer above. The touch ensures Cargo
# recognises src/main.rs as changed relative to the stub.
RUN touch src/main.rs && cargo build --release


# =============================================================================
# Runtime stage: minimal Debian image with just the compiled binary
# =============================================================================
FROM debian:bookworm-slim AS runtime

# Install TLS root certificates so HTTPS connections work in future phases.
# Clean up the apt cache immediately to keep the image layer small.
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root system user with no home directory and no login shell.
RUN useradd --system --no-create-home --shell /bin/false appuser

# Copy only the compiled binary from the build stage. Everything else —
# the Rust toolchain, source code, and intermediate objects — is discarded.
COPY --from=builder --chown=appuser:appuser \
    /app/target/release/preventdm-rust-service \
    /usr/local/bin/preventdm-rust-service

# Switch to the non-root user for all subsequent instructions and at runtime.
USER appuser

# Document the port this service listens on.
EXPOSE 8001

# Run the compiled binary directly. JSON array form avoids spawning a shell.
CMD ["preventdm-rust-service"]
