"""Explicit, bounded local Ollama generation with byte-level custody.

The caller supervises the entire operation with the process guardian. Socket
and read budgets provide additional bounds; no model acquisition is performed.
"""

from __future__ import annotations

import ipaddress
import json
import math
import re
import time
import urllib.request
from collections.abc import Mapping
from urllib.parse import urlsplit
from typing import Any


class LocalModelUnavailable(ValueError):
    """The selected installed model is unavailable for this operation."""


class LocalModelResponseError(ValueError):
    """A responding provider failed its generation or identity contract."""


def validate_local_endpoint(endpoint: str) -> str:
    """Require a literal loopback HTTP endpoint without URL credentials or redirects."""
    parsed = urlsplit(endpoint)
    try:
        local = ipaddress.ip_address(parsed.hostname or "").is_loopback
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Ollama endpoint must be a literal loopback address") from exc
    if (
        not local
        or parsed.scheme != "http"
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
        or port is None
    ):
        raise ValueError("Ollama endpoint must be http://loopback:port without other URL components")
    return endpoint.rstrip("/")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
        raise ValueError("Local model requests cannot redirect")


def _request(endpoint: str, path: str, *, deadline: float, body: str | None = None) -> str:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("Local model run deadline expired")
    request = urllib.request.Request(
        endpoint + path, data=body.encode() if body else None, headers={"Content-Type": "application/json"}
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
    with opener.open(request, timeout=remaining) as response:
        chunks: list[bytes] = []
        size = 0
        while True:
            if time.monotonic() >= deadline:
                raise TimeoutError("Local model run deadline expired during response")
            chunk = response.read1(65536)
            if not chunk:
                break
            size += len(chunk)
            if size > 8 * 1024 * 1024:
                raise ValueError("Local model response exceeds 8 MiB")
            chunks.append(chunk)
    return b"".join(chunks).decode("utf-8")


def _validated_format_schema(schema: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(schema, Mapping) or not schema:
        raise ValueError("Local model format schema must be a nonempty mapping")

    def validate(value: Any) -> Any:
        if isinstance(value, Mapping):
            if any(not isinstance(key, str) for key in value):
                raise ValueError("Local model schema keys must be strings")
            return {key: validate(item) for key, item in value.items()}
        if isinstance(value, list):
            return [validate(item) for item in value]
        if value is None or type(value) in {str, bool, int}:
            return value
        if type(value) is float and math.isfinite(value):
            return value
        raise ValueError("Local model schema must contain finite JSON values")

    result: dict[str, Any] = validate(schema)
    if len(json.dumps(result, allow_nan=False).encode("utf-8")) > 65536:
        raise ValueError("Local model schema exceeds 64 KiB")
    return result


def generate_local_review(
    prompt: str,
    model: str,
    budget: dict[str, int | float],
    *,
    endpoint: str = "http://127.0.0.1:11434",
    format_schema: Mapping[str, Any] | None = None,
) -> tuple[str, str, str]:
    """Return installed model digest and exact request/response JSON bytes as text."""
    endpoint = validate_local_endpoint(endpoint)
    timeout = budget.get("timeout_seconds", 120.0)
    if (
        type(timeout) not in {int, float}
        or not math.isfinite(timeout)
        or not 0 < timeout <= 600
        or set(budget) != {"timeout_seconds", "num_predict", "seed", "temperature"}
        or type(budget.get("num_predict")) is not int
        or not 0 < budget["num_predict"] <= 4096
        or type(budget.get("seed")) is not int
        or budget["seed"] != 0
        or type(budget.get("temperature")) not in {int, float}
        or budget["temperature"] != 0
    ):
        raise ValueError("Local model deadline and deterministic generation budgets are invalid")
    schema = _validated_format_schema(format_schema) if format_schema is not None else None
    deadline = time.monotonic() + timeout
    listing = json.loads(_request(endpoint, "/api/tags", deadline=deadline))
    rows = listing.get("models", []) if isinstance(listing, dict) else []
    matches = [row for row in rows if isinstance(row, dict) and row.get("name") == model]
    if len(matches) != 1 or not isinstance(matches[0].get("digest"), str):
        raise LocalModelUnavailable(f"Configured local model is not uniquely installed: {model}")
    identity = matches[0]["digest"]
    if not re.fullmatch(r"[0-9a-f]{64}", identity):
        raise LocalModelResponseError("Installed model digest is not SHA-256")
    request_payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {key: budget[key] for key in ("seed", "temperature", "num_predict")},
    }
    if schema is not None:
        request_payload["format"] = schema
    request_json = json.dumps(request_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    response_json = _request(endpoint, "/api/generate", deadline=deadline, body=request_json)
    response = json.loads(response_json)
    if (
        not isinstance(response, dict)
        or response.get("done") is not True
        or not isinstance(response.get("response"), str)
        or not response["response"].strip()
        or response.get("model") != model
        or type(response.get("eval_count")) is not int
        or response["eval_count"] <= 0
    ):
        raise LocalModelResponseError(
            "Local model generation has an incomplete response, wrong model, or invalid token count"
        )
    refreshed = json.loads(_request(endpoint, "/api/tags", deadline=deadline))
    after = refreshed.get("models", []) if isinstance(refreshed, dict) else []
    installed = [row for row in after if isinstance(row, dict) and row.get("name") == model]
    if len(installed) != 1 or installed[0].get("digest") != identity:
        raise LocalModelResponseError("Local model identity changed during generation")
    return identity, request_json, response_json


__all__ = ["LocalModelUnavailable", "LocalModelResponseError", "generate_local_review", "validate_local_endpoint"]
