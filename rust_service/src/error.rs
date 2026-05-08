//! Error types for the PreventDM validation service.

use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use serde_json::json;
use thiserror::Error;

/// Error arising from reading or validating application configuration.
///
/// Returned by [`crate::config::Config::from_env`] when a required
/// environment variable is absent or holds an unrecognised value.
#[derive(Debug, Error)]
pub enum ConfigError {
    /// An environment variable held an invalid or unrecognised value.
    #[error("{0}")]
    InvalidValue(String),
}

/// Top-level error type returned from Axum request handlers.
///
/// Implements [`IntoResponse`] so that handler functions can return
/// `Result<T, AppError>` and Axum will automatically convert failures
/// into JSON HTTP error responses.
///
/// Variants are defined in full for the API surface; request handlers
/// that use them are wired up in later phases.
#[allow(dead_code)]
#[derive(Debug, Error)]
pub enum AppError {
    /// A configuration value was missing or invalid.
    #[error("configuration error: {0}")]
    ConfigError(String),

    /// An unexpected internal error occurred.
    #[error("internal error: {0}")]
    InternalError(String),
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let message = match self {
            AppError::ConfigError(msg) | AppError::InternalError(msg) => msg,
        };
        let body = Json(json!({ "error": message }));
        (StatusCode::INTERNAL_SERVER_ERROR, body).into_response()
    }
}
