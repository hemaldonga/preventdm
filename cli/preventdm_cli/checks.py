"""Individual check functions for the PreventDM CLI test harness.

Each function runs one numbered check, measures elapsed time, and returns a
CheckResult.  Functions never print anything — all output is handled by the
reporter module.  Exceptions are caught inside each function so that a single
failing check does not crash the runner.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, cast

from preventdm_cli.client import PreventDMClient
from preventdm_cli.sample_data import get_sample_payload


def _empty_dict() -> dict[str, Any]:
    return {}


@dataclass
class CheckResult:
    """Result of a single numbered pipeline check."""

    number: int
    name: str
    passed: bool
    message: str
    elapsed_seconds: float
    data: dict[str, Any] = field(default_factory=_empty_dict)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _make(
    number: int,
    name: str,
    passed: bool,
    message: str,
    start: float,
    data: dict[str, Any] | None = None,
) -> CheckResult:
    """Construct a CheckResult, computing elapsed time from ``start``."""
    return CheckResult(
        number=number,
        name=name,
        passed=passed,
        message=message,
        elapsed_seconds=time.monotonic() - start,
        data=data if data is not None else {},
    )


def _health(
    number: int,
    name: str,
    client: PreventDMClient,
    url: str,
) -> CheckResult:
    """Shared logic for the three health checks."""
    start = time.monotonic()
    try:
        ok, status, body = client.health_check(name, url)
        if not ok:
            return _make(number, name, False, f"Service unreachable at {url}", start)
        if status != 200:
            return _make(number, name, False, f"HTTP {status} (expected 200)", start)
        if body.get("status") != "ok":
            return _make(
                number, name, False, f"status field is {body.get('status')!r}, expected 'ok'", start
            )
        return _make(number, name, True, f"HTTP {status} - status ok", start)
    except Exception as exc:
        return _make(number, name, False, f"Unexpected error: {exc}", start)


# ---------------------------------------------------------------------------
# Checks 1-3: service health
# ---------------------------------------------------------------------------


def check_backend_health(client: PreventDMClient) -> CheckResult:
    """Check 1 — GET /health on the backend; expect HTTP 200 and status='ok'."""
    return _health(1, "Backend health", client, client._backend_url)


def check_rust_health(client: PreventDMClient) -> CheckResult:
    """Check 2 — GET /health on the rust_service; expect HTTP 200 and status='ok'."""
    return _health(2, "Rust service health", client, client._rust_url)


def check_ml_health(client: PreventDMClient) -> CheckResult:
    """Check 3 — GET /health on the ml_service; expect HTTP 200 and status='ok'."""
    return _health(3, "ML service health", client, client._ml_url)


# ---------------------------------------------------------------------------
# Check 4: assessment submission
# ---------------------------------------------------------------------------


def check_assessment_submission(client: PreventDMClient, patient_id: str) -> CheckResult:
    """Check 4 — POST /assess; validate response shape and store body in data."""
    number, name = 4, "Assessment submission"
    start = time.monotonic()
    try:
        payload = get_sample_payload(patient_id)
        ok, status, body = client.post_assess(payload)
        if not ok:
            return _make(number, name, False, "Network error calling POST /assess", start)
        if status != 200:
            return _make(number, name, False, f"HTTP {status} (expected 200)", start)

        assessment_id = body.get("assessment_id")
        if not assessment_id:
            return _make(number, name, False, "Response missing assessment_id", start)

        if body.get("patient_external_id") != patient_id:
            return _make(
                number,
                name,
                False,
                f"patient_external_id mismatch: got {body.get('patient_external_id')!r}",
                start,
            )

        if not body.get("assessment_timestamp_utc"):
            return _make(number, name, False, "Response missing assessment_timestamp_utc", start)

        for key in ("validated_features", "clinical_scores", "ml_prediction"):
            if key not in body:
                return _make(number, name, False, f"Response missing key: {key}", start)

        return _make(
            number,
            name,
            True,
            f"assessment_id={assessment_id}",
            start,
            data=body,
        )
    except Exception as exc:
        return _make(number, name, False, f"Unexpected error: {exc}", start)


# ---------------------------------------------------------------------------
# Check 5: assessment retrieval
# ---------------------------------------------------------------------------


def check_assessment_retrieval(client: PreventDMClient, assessment_id: str) -> CheckResult:
    """Check 5 — GET /assess/{id}; validate shape, scores, and probability range."""
    number, name = 5, "Assessment retrieval"
    start = time.monotonic()
    try:
        ok, status, body = client.get_assess(assessment_id)
        if not ok:
            return _make(number, name, False, "Network error calling GET /assess/{id}", start)
        if status != 200:
            return _make(number, name, False, f"HTTP {status} (expected 200)", start)

        if str(body.get("assessment_id")) != assessment_id:
            return _make(number, name, False, "assessment_id in response does not match", start)

        for key in (
            "patient_external_id",
            "validated_features",
            "clinical_scores",
            "ml_prediction",
        ):
            if key not in body:
                return _make(number, name, False, f"Response missing key: {key}", start)

        clinical = cast(dict[str, Any], body.get("clinical_scores") or {})
        for score_type in ("findrisc", "ada", "cambridge"):
            if score_type not in clinical:
                return _make(number, name, False, f"clinical_scores missing {score_type}", start)

        ml = cast(dict[str, Any], body.get("ml_prediction") or {})
        prob = ml.get("probability")
        if not isinstance(prob, (int, float)) or not (0.0 <= float(prob) <= 1.0):
            return _make(
                number, name, False, f"probability out of range or missing: {prob!r}", start
            )

        return _make(number, name, True, f"probability={prob}", start, data=body)
    except Exception as exc:
        return _make(number, name, False, f"Unexpected error: {exc}", start)


# ---------------------------------------------------------------------------
# Check 6: data consistency
# ---------------------------------------------------------------------------


def check_data_consistency(post_body: dict[str, Any], get_body: dict[str, Any]) -> CheckResult:
    """Check 6 — compare the POST and GET response bodies field by field."""
    number, name = 6, "Data consistency"
    start = time.monotonic()

    def fail(msg: str) -> CheckResult:
        return _make(number, name, False, msg, start)

    try:
        if post_body.get("patient_external_id") != get_body.get("patient_external_id"):
            return fail("patient_external_id differs between POST and GET")

        if post_body.get("assessment_timestamp_utc") != get_body.get("assessment_timestamp_utc"):
            return fail("assessment_timestamp_utc differs between POST and GET")

        post_ml = cast(dict[str, Any], post_body.get("ml_prediction") or {})
        get_ml = cast(dict[str, Any], get_body.get("ml_prediction") or {})
        if post_ml.get("probability") != get_ml.get("probability"):
            return fail(
                f"probability differs: POST={post_ml.get('probability')!r} "
                f"GET={get_ml.get('probability')!r}"
            )

        post_cs = cast(dict[str, Any], post_body.get("clinical_scores") or {})
        get_cs = cast(dict[str, Any], get_body.get("clinical_scores") or {})
        for score_type in ("findrisc", "ada", "cambridge"):
            post_score = cast(dict[str, Any], post_cs.get(score_type) or {})
            get_score = cast(dict[str, Any], get_cs.get(score_type) or {})
            if post_score.get("risk_category") != get_score.get("risk_category"):
                return fail(
                    f"{score_type}.risk_category differs: "
                    f"POST={post_score.get('risk_category')!r} "
                    f"GET={get_score.get('risk_category')!r}"
                )

        return _make(number, name, True, "POST and GET responses are fully consistent", start)
    except Exception as exc:
        return _make(number, name, False, f"Unexpected error: {exc}", start)


# ---------------------------------------------------------------------------
# Check 7: upstream error handling
# ---------------------------------------------------------------------------


def check_error_handling(client: PreventDMClient) -> CheckResult:
    """Check 7 — POST a malformed payload; expect HTTP 422 with a detail field."""
    number, name = 7, "Upstream error handling"
    start = time.monotonic()
    try:
        # Missing all required fields — Pydantic should reject this with 422.
        ok, status, body = client.post_assess({})
        if not ok:
            return _make(number, name, False, "Network error calling POST /assess", start)
        if status != 422:
            return _make(number, name, False, f"HTTP {status} (expected 422)", start)
        if "detail" not in body:
            return _make(number, name, False, "Response body missing 'detail' field", start)
        return _make(number, name, True, "HTTP 422 received with detail field", start)
    except Exception as exc:
        return _make(number, name, False, f"Unexpected error: {exc}", start)


# ---------------------------------------------------------------------------
# Check 8: invalid UUID
# ---------------------------------------------------------------------------


def check_invalid_id(client: PreventDMClient) -> CheckResult:
    """Check 8 — GET a valid-UUID that does not exist; expect HTTP 404."""
    number, name = 8, "Invalid ID handling"
    start = time.monotonic()
    nil_uuid = "00000000-0000-0000-0000-000000000000"
    try:
        ok, status, _ = client.get_assess(nil_uuid)
        if not ok:
            return _make(number, name, False, "Network error calling GET /assess/{id}", start)
        if status != 404:
            return _make(number, name, False, f"HTTP {status} (expected 404)", start)
        return _make(number, name, True, "HTTP 404 for nil UUID as expected", start)
    except Exception as exc:
        return _make(number, name, False, f"Unexpected error: {exc}", start)


# ---------------------------------------------------------------------------
# Check 9: malformed UUID
# ---------------------------------------------------------------------------


def check_malformed_id(client: PreventDMClient) -> CheckResult:
    """Check 9 — GET with a non-UUID path segment; expect HTTP 422."""
    number, name = 9, "Malformed ID handling"
    start = time.monotonic()
    try:
        ok, status, _ = client.get_assess("not-a-valid-uuid")
        if not ok:
            return _make(number, name, False, "Network error calling GET /assess/{id}", start)
        if status != 422:
            return _make(number, name, False, f"HTTP {status} (expected 422)", start)
        return _make(number, name, True, "HTTP 422 for malformed UUID as expected", start)
    except Exception as exc:
        return _make(number, name, False, f"Unexpected error: {exc}", start)
