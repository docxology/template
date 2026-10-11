"""Bounded loopback-only Ollama transport, executed by the supervised parent."""

from __future__ import annotations

import argparse
import http.client
import json
import re
from pathlib import Path
from urllib.parse import urlsplit


def ollama_generate(endpoint: str, request: dict[str, object], identity_path: Path | None = None) -> dict[str, object]:
    """Send one nonstreaming request; redirects, remote hosts, and oversized bodies fail."""
    url = urlsplit(endpoint)
    if (
        url.scheme != "http"
        or url.hostname not in {"127.0.0.1", "::1"}
        or url.username
        or url.password
        or url.path not in {"", "/"}
        or url.query
        or url.fragment
    ):
        raise ValueError("Ollama endpoint must be an HTTP loopback origin without credentials")
    connection = http.client.HTTPConnection(url.hostname, url.port or 11434, timeout=60)
    try:
        model = request.get("model")
        if not isinstance(model, str) or not model.strip():
            raise ValueError("a nonempty selected model name is required")

        def installed_digest() -> str:
            connection.request("GET", "/api/tags")
            tags_response = connection.getresponse()
            if tags_response.status != 200:
                raise ConnectionError(f"Ollama model inventory failed with HTTP {tags_response.status}")
            tags_raw = tags_response.read(65537)
            if len(tags_raw) > 65536:
                raise ValueError("Ollama model inventory exceeds the 64KiB receipt limit")
            tags = json.loads(tags_raw)
            entries = tags.get("models") if isinstance(tags, dict) else None
            if not isinstance(entries, list):
                raise ConnectionError("Ollama model inventory is unavailable")
            matches = [entry for entry in entries if isinstance(entry, dict) and entry.get("name") == model]
            if len(matches) != 1:
                raise ConnectionError("the selected installed model must have exactly one inventory identity")
            digest = matches[0].get("digest")
            if not isinstance(digest, str) or not re.fullmatch(r"(?:sha256:)?[0-9a-f]{64}", digest):
                raise ValueError("installed model digest must identify SHA-256 bytes")
            return digest.removeprefix("sha256:")

        before = installed_digest()
        identity: dict[str, object] = {"model": model, "before_sha256": before, "status": "incomplete"}
        if identity_path is not None:
            identity_path.write_text(json.dumps(identity, indent=2) + "\n", encoding="utf-8")
        connection.request(
            "POST",
            "/api/generate",
            body=json.dumps(request).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        if response.status != 200:
            raise ConnectionError(f"Ollama request failed with HTTP {response.status}")
        raw = response.read(65537)
        if len(raw) > 65536:
            raise ValueError("Ollama response exceeds the 64KiB receipt limit")
        payload = json.loads(raw)
        if not isinstance(payload, dict) or payload.get("error"):
            raise ConnectionError("Ollama returned an invalid or unavailable-model response")
        if payload.get("done") is not True or payload.get("model") != request["model"]:
            raise ValueError("Ollama response must identify the selected model and a completed generation")
        if type(payload.get("eval_count")) is not int or payload["eval_count"] < 1:
            raise ValueError("Ollama response lacks nonempty generation evidence")
        after = installed_digest()
        identity.update(after_sha256=after, status="passed" if before == after else "failed")
        if identity_path is not None:
            identity_path.write_text(json.dumps(identity, indent=2) + "\n", encoding="utf-8")
        if before != after:
            raise ValueError("selected installed model digest changed during generation")
        return payload
    finally:
        connection.close()


def main(argv: list[str] | None = None) -> int:
    """Read a source-owned public request and persist the actual provider response."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--response", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        request = json.loads(args.request.read_text(encoding="utf-8"))
        response = ollama_generate(args.endpoint, request, args.response.with_name("model_identity.json"))
    except (OSError, ConnectionError, http.client.HTTPException) as exc:
        print(f"local model unavailable: {type(exc).__name__}: {exc}")
        return 75
    except (ValueError, KeyError, TypeError) as exc:
        print(f"model response rejected: {exc}")
        return 1
    args.response.write_text(json.dumps(response, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
