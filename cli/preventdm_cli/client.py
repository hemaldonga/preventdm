"""Synchronous HTTP client wrapper for the PreventDM service stack."""

from __future__ import annotations

from typing import Any, cast

import httpx


def _parse_json(response: httpx.Response) -> dict[str, Any]:
    """Parse a JSON response body; return an empty dict on parse failure."""
    try:
        return cast(dict[str, Any], response.json())
    except Exception:
        return {}


class PreventDMClient:
    """Thin synchronous HTTP client for the three PreventDM services.

    All methods return a three-tuple of (request_succeeded, status_code, body).
    ``request_succeeded`` is False only when a network-level error prevents any
    response from being received; a 404 or 422 still counts as succeeded=True.
    """

    def __init__(
        self,
        backend_url: str,
        rust_url: str,
        ml_url: str,
        timeout: float = 10.0,
    ) -> None:
        """Initialise the client with base URLs for each service."""
        self._backend_url = backend_url.rstrip("/")
        self._rust_url = rust_url.rstrip("/")
        self._ml_url = ml_url.rstrip("/")
        self._client = httpx.Client(timeout=timeout)

    def health_check(self, service: str, url: str) -> tuple[bool, int, dict[str, Any]]:
        """GET {url}/health and return (succeeded, status_code, body).

        Returns (False, 0, {}) on network failure.
        The ``service`` parameter is accepted for API symmetry and caller logging.
        """
        try:
            response = self._client.get(f"{url}/health")
            return True, response.status_code, _parse_json(response)
        except httpx.RequestError:
            return False, 0, {}

    def post_assess(self, payload: dict[str, Any]) -> tuple[bool, int, dict[str, Any]]:
        """POST payload to /assess on the backend and return (succeeded, status_code, body)."""
        try:
            response = self._client.post(f"{self._backend_url}/assess", json=payload)
            return True, response.status_code, _parse_json(response)
        except httpx.RequestError:
            return False, 0, {}

    def get_assess(self, assessment_id: str) -> tuple[bool, int, dict[str, Any]]:
        """GET /assess/{assessment_id} from the backend and return (succeeded, status_code, body)."""
        try:
            response = self._client.get(f"{self._backend_url}/assess/{assessment_id}")
            return True, response.status_code, _parse_json(response)
        except httpx.RequestError:
            return False, 0, {}
