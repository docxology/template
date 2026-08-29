"""Monid HTTP API client — discover, inspect, run, and wallet balance.

Monid is a unified gateway to hundreds of data endpoints. This client wraps the
HTTP API documented at https://monid.ai/docs/api/overview.md. Importing this
package is side-effect free; use :meth:`MonidClient.from_env` to read
``MONID_API_KEY``.
"""

from __future__ import annotations

import time
from typing import Any, Mapping

from infrastructure.search.monid.config import MonidConfig
from infrastructure.search.monid.errors import MonidError
from infrastructure.search.monid.http import MonidHttpClient, UrllibMonidHttpClient
from infrastructure.search.monid.models import (
    DiscoverResponse,
    InspectResponse,
    RunRecord,
    WalletBalance,
)

_TERMINAL_STATUSES = frozenset({"COMPLETED", "FAILED", "BLOCKED", "STOPPED", "TIMED_OUT"})


class MonidClient:
    """Thin client for the Monid REST API."""

    def __init__(self, config: MonidConfig, *, http_client: MonidHttpClient | None = None) -> None:
        self.config = config
        self.http: MonidHttpClient = http_client or UrllibMonidHttpClient()

    @classmethod
    def from_env(cls, *, base_url: str | None = None, http_client: MonidHttpClient | None = None) -> MonidClient:
        """Construct from ``MONID_API_KEY``."""
        return cls(MonidConfig.from_env(base_url=base_url), http_client=http_client)

    def _json(
        self,
        method: str,
        path: str,
        payload: Mapping[str, Any] | None = None,
        *,
        ok_statuses: frozenset[int] = frozenset({200}),
    ) -> dict[str, Any]:
        url = f"{self.config.base_url}/{path.lstrip('/')}"
        resp = self.http.request(
            method,
            url,
            json=payload,
            headers=self.config.auth_headers(),
            timeout=self.config.timeout,
        )
        if resp.status_code not in ok_statuses:
            raise MonidError(
                f"Monid {method} {path} returned HTTP {resp.status_code}",
                status=resp.status_code,
                body=resp.text[:1000],
            )
        data = resp.json()
        if not isinstance(data, dict):
            raise MonidError(f"Monid {method} {path} returned a non-object JSON body", status=resp.status_code)
        return data

    def discover(self, query: str, *, limit: int = 5, min_score: float | None = None) -> DiscoverResponse:
        """Search endpoints with natural language (``POST /v1/discover``)."""
        text = query.strip()
        if not text:
            raise MonidError("discover query must be non-empty")
        payload: dict[str, Any] = {"query": text, "limit": limit}
        if min_score is not None:
            payload["minScore"] = min_score
        return DiscoverResponse.from_dict(self._json("POST", "/v1/discover", payload))

    def inspect(self, provider: str, endpoint: str) -> InspectResponse:
        """Fetch endpoint schema and pricing (``POST /v1/inspect``)."""
        if not provider.strip() or not endpoint.strip():
            raise MonidError("provider and endpoint are required")
        payload = {"provider": provider, "endpoint": endpoint}
        return InspectResponse.from_dict(self._json("POST", "/v1/inspect", payload))

    def run(
        self,
        provider: str,
        endpoint: str,
        input_params: Mapping[str, Any] | None = None,
        *,
        wait: bool = False,
    ) -> RunRecord:
        """Execute an endpoint (``POST /v1/run``). Poll when the API returns 202."""
        if not provider.strip() or not endpoint.strip():
            raise MonidError("provider and endpoint are required")
        payload = {
            "provider": provider,
            "endpoint": endpoint,
            "input": dict(input_params or {}),
        }
        data = self._json("POST", "/v1/run", payload, ok_statuses=frozenset({200, 202}))
        record = RunRecord.from_dict(data)
        if wait and not record.is_terminal and record.run_id:
            return self.poll_run(record.run_id)
        return record

    def get_run(self, run_id: str) -> RunRecord:
        """Fetch run status (``GET /v1/runs/:runId``)."""
        if not run_id.strip():
            raise MonidError("run_id is required")
        return RunRecord.from_dict(self._json("GET", f"/v1/runs/{run_id}"))

    def poll_run(self, run_id: str) -> RunRecord:
        """Poll until the run reaches a terminal status."""
        record = self.get_run(run_id)
        attempts = 0
        while not record.is_terminal and attempts < self.config.max_poll_attempts:
            time.sleep(self.config.poll_interval_seconds)
            record = self.get_run(run_id)
            attempts += 1
        if not record.is_terminal:
            raise MonidError(
                f"run {run_id} did not reach a terminal status after {attempts} polls",
                status=None,
            )
        return record

    def balance(self) -> WalletBalance:
        """Return workspace wallet balance (``GET /v1/wallet/balance``)."""
        return WalletBalance.from_dict(self._json("GET", "/v1/wallet/balance", None))


__all__ = ["MonidClient"]
