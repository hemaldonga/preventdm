//! Application configuration loaded from environment variables.

use std::env;

use crate::error::ConfigError;

/// Valid values for the `APP_ENV` environment variable.
const VALID_ENVS: &[&str] = &["development", "staging", "production"];

/// Valid values for the `LOG_LEVEL` environment variable.
const VALID_LOG_LEVELS: &[&str] = &["trace", "debug", "info", "warn", "error"];

/// Runtime configuration for the PreventDM validation service.
///
/// Constructed once at startup via [`Config::from_env`] and shared across
/// request handlers as Axum application state.
#[derive(Debug, Clone)]
pub struct Config {
    /// Human-readable service name returned in health responses.
    pub app_name: String,

    /// Deployment environment: `development`, `staging`, or `production`.
    pub app_env: String,

    /// Minimum tracing level: `trace`, `debug`, `info`, `warn`, or `error`.
    pub log_level: String,

    /// TCP port the HTTP server binds to.
    pub server_port: u16,
}

impl Config {
    /// Read configuration from environment variables, applying defaults for
    /// missing variables and returning an error for invalid values.
    ///
    /// # Errors
    ///
    /// Returns [`ConfigError::InvalidValue`] if `APP_ENV` or `LOG_LEVEL`
    /// contains an unrecognised value, or if `SERVER_PORT` cannot be parsed
    /// as a `u16`.
    pub fn from_env() -> Result<Self, ConfigError> {
        let app_name =
            env::var("APP_NAME").unwrap_or_else(|_| "PreventDM Validation Service".to_owned());

        let app_env = env::var("APP_ENV").unwrap_or_else(|_| "development".to_owned());
        if !VALID_ENVS.contains(&app_env.as_str()) {
            return Err(ConfigError::InvalidValue(format!(
                "APP_ENV must be one of {VALID_ENVS:?}, got {app_env:?}"
            )));
        }

        let log_level = env::var("LOG_LEVEL").unwrap_or_else(|_| "info".to_owned());
        if !VALID_LOG_LEVELS.contains(&log_level.to_lowercase().as_str()) {
            return Err(ConfigError::InvalidValue(format!(
                "LOG_LEVEL must be one of {VALID_LOG_LEVELS:?}, got {log_level:?}"
            )));
        }

        let server_port = env::var("SERVER_PORT")
            .unwrap_or_else(|_| "8001".to_owned())
            .parse::<u16>()
            .map_err(|e| {
                ConfigError::InvalidValue(format!("SERVER_PORT is not a valid port number: {e}"))
            })?;

        Ok(Self {
            app_name,
            app_env,
            log_level,
            server_port,
        })
    }
}
