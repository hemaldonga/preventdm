//! Health check route for liveness verification.

use axum::{extract::State, routing::get, Json, Router};
use serde::Serialize;

use crate::config::Config;

/// Response body returned by `GET /health`.
#[derive(Debug, Serialize)]
pub struct HealthResponse {
    /// Always `"ok"` when the service is running.
    pub status: String,

    /// Human-readable service name from [`Config::app_name`].
    pub service: String,

    /// Deployment environment from [`Config::app_env`].
    pub environment: String,

    /// Package version baked in at compile time via `CARGO_PKG_VERSION`.
    pub version: String,
}

/// Build the health router.
///
/// Registers `GET /health` and expects [`Config`] to be provided as Axum
/// application state via [`Router::with_state`].
pub fn router() -> Router<Config> {
    Router::new().route("/health", get(health_check))
}

async fn health_check(State(config): State<Config>) -> Json<HealthResponse> {
    Json(HealthResponse {
        status: "ok".to_owned(),
        service: config.app_name,
        environment: config.app_env,
        version: env!("CARGO_PKG_VERSION").to_owned(),
    })
}
