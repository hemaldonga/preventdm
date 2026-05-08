//! PreventDM validation service entry point.

use std::net::SocketAddr;

use tracing::info;
use tracing_subscriber::EnvFilter;

mod config;
mod error;
mod routes;

use config::Config;

/// Start the PreventDM validation service.
///
/// Reads configuration from environment variables, initialises structured
/// stdout logging, assembles the Axum router, and starts the HTTP server.
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let config = Config::from_env()?;

    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::new(&config.log_level))
        .init();

    let addr = SocketAddr::from(([0, 0, 0, 0], config.server_port));
    let listener = tokio::net::TcpListener::bind(addr).await?;

    let app = routes::router().with_state(config.clone());

    info!(service = %config.app_name, address = %addr, "server started");

    axum::serve(listener, app).await?;

    Ok(())
}
