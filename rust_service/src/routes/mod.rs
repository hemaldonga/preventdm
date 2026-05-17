//! HTTP route modules for the PreventDM validation service.

pub mod health;
pub mod score;

use axum::Router;

use crate::config::Config;

/// Assemble the complete application router by merging all route modules.
pub fn router() -> Router<Config> {
    health::router().merge(score::router())
}
