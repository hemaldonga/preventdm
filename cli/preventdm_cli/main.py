"""PreventDM CLI entry point — health check and end-to-end pipeline test commands."""

from __future__ import annotations

import time

import typer

from preventdm_cli import reporter
from preventdm_cli.checks import (
    CheckResult,
    check_assessment_retrieval,
    check_assessment_submission,
    check_backend_health,
    check_data_consistency,
    check_error_handling,
    check_invalid_id,
    check_malformed_id,
    check_ml_health,
    check_rust_health,
)
from preventdm_cli.client import PreventDMClient

app = typer.Typer(
    name="preventdm-cli",
    help="PreventDM stack verification tool — checks service health and the full assessment pipeline.",
    add_completion=False,
)


# ---------------------------------------------------------------------------
# health command
# ---------------------------------------------------------------------------


@app.command()
def health(
    backend_url: str = typer.Option("http://localhost:8000", help="Backend service URL"),
    rust_url: str = typer.Option("http://localhost:8001", help="Rust service URL"),
    ml_url: str = typer.Option("http://localhost:8002", help="ML service URL"),
    timeout: float = typer.Option(10.0, help="Request timeout in seconds"),
) -> None:
    """Check whether all three services respond to GET /health with status 'ok'."""
    reporter.print_header("Health Check")

    client = PreventDMClient(backend_url, rust_url, ml_url, timeout)
    services = [
        ("backend", backend_url),
        ("rust_service", rust_url),
        ("ml_service", ml_url),
    ]

    all_healthy = True
    for service_name, url in services:
        ok, status, body = client.health_check(service_name, url)
        healthy = ok and status == 200 and body.get("status") == "ok"
        reporter.print_service_health(service_name, url, healthy, status)
        if not healthy:
            all_healthy = False

    reporter.print_info("")
    if all_healthy:
        reporter.print_info("  [bold green]All services are healthy.[/bold green]")
    else:
        reporter.print_info("  [bold red]One or more services are unhealthy.[/bold red]")
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# test-pipeline command
# ---------------------------------------------------------------------------


def _run_pipeline(client: PreventDMClient, patient_id: str) -> list[CheckResult]:
    """Execute all nine checks in order, stopping on the first failure.

    Returns the list of CheckResult objects for every check that was run.
    Each result is printed immediately via the reporter as it completes.
    """
    results: list[CheckResult] = []

    def add(r: CheckResult) -> bool:
        results.append(r)
        reporter.print_check_result(r)
        return r.passed

    if not add(check_backend_health(client)):
        return results
    if not add(check_rust_health(client)):
        return results
    if not add(check_ml_health(client)):
        return results

    r4 = check_assessment_submission(client, patient_id)
    if not add(r4):
        return results

    assessment_id: str = str(r4.data.get("assessment_id", ""))

    r5 = check_assessment_retrieval(client, assessment_id)
    if not add(r5):
        return results

    if not add(check_data_consistency(r4.data, r5.data)):
        return results
    if not add(check_error_handling(client)):
        return results
    if not add(check_invalid_id(client)):
        return results

    add(check_malformed_id(client))
    return results


@app.command(name="test-pipeline")
def test_pipeline(
    backend_url: str = typer.Option("http://localhost:8000", help="Backend service URL"),
    rust_url: str = typer.Option("http://localhost:8001", help="Rust service URL"),
    ml_url: str = typer.Option("http://localhost:8002", help="ML service URL"),
    timeout: float = typer.Option(10.0, help="Request timeout in seconds"),
    patient_id: str = typer.Option(
        "PREVENTDM-CLI-TEST",
        help="External patient ID used in the test payload (avoids colliding with real data)",
    ),
) -> None:
    """Run the full nine-check end-to-end pipeline against the PreventDM stack."""
    reporter.print_header("End-to-End Pipeline Test")

    client = PreventDMClient(backend_url, rust_url, ml_url, timeout)
    pipeline_start = time.monotonic()

    results = _run_pipeline(client, patient_id)

    total_elapsed = time.monotonic() - pipeline_start
    reporter.print_summary(results, total_elapsed)

    all_passed = len(results) == 9 and all(r.passed for r in results)
    raise typer.Exit(code=0 if all_passed else 1)
