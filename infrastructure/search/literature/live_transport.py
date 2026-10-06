"""Supervised credential-free HTTP and local-model workers with byte receipts."""

from __future__ import annotations

import argparse
import ipaddress
import socket
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from infrastructure.search.literature.live_contract import (
    LiteratureBlocked,
    LiteratureFailed,
    LiveSession,
    exact_json,
    sha256,
    verify_platform,
    write_json,
)

SOURCE_PATH = "infrastructure/search/literature/live_transport.py"


def validate_public_url(url: str, *, allow_loopback: bool = False) -> str:
    """Reject credentials, private addresses, and non-HTTP transports before any request."""
    if not isinstance(url, str) or len(url) > 8192:
        raise LiteratureFailed("HTTP URL must be a bounded string")
    parsed = urlsplit(url)
    if (
        not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
        or parsed.scheme not in {"http", "https"}
    ):
        raise LiteratureFailed("literature URL has an unsupported scheme, credentials, or fragment")
    try:
        addresses = {ipaddress.ip_address(row[4][0]) for row in socket.getaddrinfo(parsed.hostname, parsed.port or 443)}
    except (OSError, ValueError) as exc:
        raise LiteratureBlocked("literature host cannot be resolved") from exc
    loopback = allow_loopback and addresses and all(address.is_loopback for address in addresses)
    if not loopback and (parsed.scheme != "https" or any(not address.is_global for address in addresses)):
        raise LiteratureFailed("literature URLs must use public HTTPS; loopback HTTP is test-only")
    return url


class _ValidatedRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, allow_loopback: bool) -> None:
        self.allow_loopback = allow_loopback
        self.redirects: list[str] = []

    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> Any:
        if len(self.redirects) >= 3:
            raise LiteratureFailed("literature response exceeded three redirects")
        validate_public_url(newurl, allow_loopback=self.allow_loopback)
        self.redirects.append(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _http_worker(invocation: dict[str, Any], directory: Path) -> int:
    """Download only bounded public bytes under a caller-enforced process deadline."""
    url = validate_public_url(invocation["url"], allow_loopback=invocation["allow_loopback"])
    deadline = time.monotonic() + invocation["timeout_seconds"]
    handler = _ValidatedRedirect(invocation["allow_loopback"])
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), handler)
    request = urllib.request.Request(
        url, headers={"User-Agent": "template-literature-acceptance/4.0 (unpaid bounded research)"}
    )
    metadata: dict[str, Any] = {"requested_url": url, "status": "incomplete"}
    write_json(directory / "http.json", metadata)
    try:
        with opener.open(request, timeout=invocation["timeout_seconds"]) as response:
            chunks: list[bytes] = []
            size = 0
            while True:
                if time.monotonic() >= deadline:
                    raise TimeoutError("HTTP response read deadline exceeded")
                chunk = response.read1(65536)
                if not chunk:
                    break
                size += len(chunk)
                if size > invocation["max_bytes"]:
                    raise LiteratureFailed("literature response exceeds byte ceiling")
                chunks.append(chunk)
            raw = b"".join(chunks)
            if not raw:
                raise LiteratureFailed("literature provider returned an empty response")
            (directory / "body.bin").write_bytes(raw)
            metadata.update(
                status="passed",
                status_code=response.status,
                final_url=response.geturl(),
                redirects=handler.redirects,
                size_bytes=len(raw),
                sha256=sha256(raw),
                content_type=response.headers.get("Content-Type", ""),
            )
            write_json(directory / "http.json", metadata)
    except urllib.error.HTTPError as exc:
        metadata.update(status="blocked", status_code=exc.code, redirects=handler.redirects)
        write_json(directory / "http.json", metadata)
        raise LiteratureBlocked(f"unpaid HTTP provider returned status {exc.code}") from exc
    return 0


def _model_worker(invocation: dict[str, Any], directory: Path) -> int:
    from infrastructure.llm.core.local_ollama import (
        LocalModelResponseError,
        LocalModelUnavailable,
        generate_local_review,
    )

    try:
        identity, request, response = generate_local_review(
            invocation["prompt"],
            invocation["model"],
            invocation["budget"],
            endpoint=invocation["endpoint"],
            format_schema=invocation["format_schema"],
        )
    except LocalModelUnavailable as exc:
        raise LiteratureBlocked(str(exc)) from exc
    except LocalModelResponseError as exc:
        raise LiteratureFailed(str(exc)) from exc
    (directory / "request.json").write_text(request, encoding="utf-8")
    (directory / "response.json").write_text(response, encoding="utf-8")
    write_json(directory / "model.json", {"model": invocation["model"], "model_sha256": identity})
    return 0


def _pdf_worker(invocation: dict[str, Any], directory: Path) -> int:
    from infrastructure.search.literature.live_providers import _pdf_text

    path = Path(invocation["source"])
    if path.is_symlink() or not path.is_file():
        raise LiteratureFailed("PDF source must be a regular file")
    raw = path.read_bytes()
    if len(raw) > 16 * 1024 * 1024 or sha256(raw) != invocation["source_sha256"]:
        raise LiteratureFailed("PDF source changed before extraction")
    text = _pdf_text(raw, invocation["doi"])
    (directory / "text.txt").write_text(text, encoding="utf-8")
    write_json(
        directory / "extraction.json",
        {"source_sha256": sha256(raw), "doi": invocation["doi"], "text_sha256": sha256(text.encode("utf-8"))},
    )
    return 0


def _supervise(session: LiveSession, directory: Path, invocation: dict[str, Any], kind: str) -> None:
    from infrastructure.core.implementation_custody import bytecode_audit_bootstrap
    from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy

    verify_platform(session.platform_sources, session.environment, session.implementation)
    invocation.update(
        platform_sources=session.platform_sources,
        runtime_environment=session.environment,
        implementation_custody=session.implementation,
    )
    directory.mkdir()
    invocation_path = directory / "invocation.json"
    write_json(invocation_path, invocation)
    platform_root = Path(__file__).resolve().parents[3]
    bootstrap = (
        "import runpy,sys;sys.path.insert(0,sys.argv.pop(1));"
        "runpy.run_module('infrastructure.search.literature.live_transport',run_name='__main__')"
    )
    with tempfile.TemporaryDirectory(prefix="template-literature-worker-cache-") as cache:
        prefix = Path(cache).resolve()
        audited_bootstrap = bytecode_audit_bootstrap(
            (platform_root / "infrastructure", platform_root / "scripts"), prefix
        )
        invocation["fresh_pycache_prefix"] = str(prefix)
        write_json(invocation_path, invocation)
        invocation_bytes = session.consume(invocation_path)
        result = run_with_policy(
            [
                sys.executable,
                "-I",
                "-X",
                f"pycache_prefix={prefix}",
                "-c",
                audited_bootstrap + bootstrap,
                str(platform_root),
                "--kind",
                kind,
                "--invocation",
                str(invocation_path),
                "--directory",
                str(directory),
            ],
            cwd=directory,
            env=None,
            policy=SubprocessPolicy(
                policy_id="literature-unpaid-worker",
                source_path=SOURCE_PATH,
                timeout_seconds=session.timeout(),
                capture_output=True,
                credential_free=True,
            ),
        )
    write_json(
        directory / "execution.json",
        {
            "returncode": result.returncode,
            "timed_out": result.timed_out,
            "bytecode_binding": "fresh-owned-prefix",
            "cache_prefix_created_empty_before_imports": True,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "deadline_seconds": invocation.get("timeout_seconds", invocation.get("budget", {}).get("timeout_seconds")),
        },
    )
    if invocation_path.read_bytes() != invocation_bytes:
        raise LiteratureFailed("worker invocation changed during execution")
    if result.timed_out or result.returncode == 75:
        raise LiteratureBlocked("unpaid worker unavailable or deadline exceeded; execution.json retains diagnostics")
    if result.returncode:
        raise LiteratureFailed("unpaid worker failed; execution.json retains diagnostics")
    verify_platform(session.platform_sources, session.environment, session.implementation)


def fetch_bytes(
    session: LiveSession, url: str, label: str, *, max_bytes: int = 8 * 1024 * 1024, allow_loopback: bool = False
) -> tuple[bytes, dict[str, Any]]:
    """Retain exact requested URL, redirects, media metadata, and consumed response bytes."""
    if type(max_bytes) is not int or not 1 <= max_bytes <= 16 * 1024 * 1024:
        raise LiteratureFailed("HTTP byte ceiling must be an exact integer between 1 and 16 MiB")
    if not label or not label.replace("_", "").isalnum():
        raise LiteratureFailed("HTTP artifact label must be a safe component")
    directory = session.directory / label
    _supervise(
        session,
        directory,
        {"url": url, "timeout_seconds": session.timeout(), "max_bytes": max_bytes, "allow_loopback": allow_loopback},
        "http",
    )
    body = session.consume(directory / "body.bin")
    metadata = exact_json(session.consume(directory / "http.json"))
    if metadata.get("sha256") != sha256(body) or metadata.get("size_bytes") != len(body):
        raise LiteratureFailed("HTTP metadata does not identify consumed response bytes")
    return body, metadata


def extract_pdf_text(session: LiveSession, source: Path, doi: str, label: str) -> str:
    """Parse actual PDF bytes under the same whole-process deadline and retain its input binding."""
    raw = session.consume(source)
    directory = session.directory / label
    _supervise(
        session,
        directory,
        {"source": str(source), "source_sha256": sha256(raw), "doi": doi, "timeout_seconds": session.timeout()},
        "pdf",
    )
    metadata = exact_json(session.consume(directory / "extraction.json"))
    text_bytes = session.consume(directory / "text.txt")
    if metadata != {"source_sha256": sha256(raw), "doi": doi, "text_sha256": sha256(text_bytes)}:
        raise LiteratureFailed("PDF extraction receipt is not bound to consumed source bytes")
    return text_bytes.decode("utf-8")


class LocalGenerator:
    """A bounded sequence of actual local generations with one immutable installed model."""

    def __init__(self, session: LiveSession, *, max_calls: int = 10) -> None:
        if type(max_calls) is not int or not 1 <= max_calls <= 10:
            raise LiteratureFailed("local generation ceiling must be an exact integer in [1, 10]")
        self.session, self.max_calls = session, max_calls
        self.calls: list[dict[str, Any]] = []
        self.model_sha256: str | None = None
        session.receipt["local_generation_calls"] = self.calls
        session.receipt["max_local_generations"] = max_calls
        session.receipt["generation_token_ceiling"] = session.settings.num_predict

    def generate(self, prompt: str, schema: dict[str, Any]) -> Any:
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 32000:
            raise LiteratureFailed("model prompt must be nonempty and at most 32000 characters")
        if len(self.calls) >= self.max_calls:
            raise LiteratureFailed("local generation ceiling exhausted")
        settings = self.session.settings
        invocation: dict[str, Any] = {
            "prompt": prompt,
            "model": settings.model,
            "endpoint": settings.endpoint,
            "format_schema": schema,
            "budget": {
                "timeout_seconds": self.session.timeout(),
                "num_predict": settings.num_predict,
                "seed": 0,
                "temperature": 0,
            },
        }
        directory = self.session.directory / f"model_{len(self.calls) + 1}"
        self.calls.append({"status": "incomplete", "directory": directory.name})
        _supervise(self.session, directory, invocation, "model")
        request = exact_json(self.session.consume(directory / "request.json"))
        expected = {
            "model": invocation["model"],
            "prompt": prompt,
            "stream": False,
            "format": schema,
            "options": {key: invocation["budget"][key] for key in ("seed", "temperature", "num_predict")},
        }
        if request != expected:
            raise LiteratureFailed("actual model request differs from the bounded source input")
        response = exact_json(self.session.consume(directory / "response.json"))
        identity = exact_json(self.session.consume(directory / "model.json"))["model_sha256"]
        if self.model_sha256 is not None and self.model_sha256 != identity:
            raise LiteratureFailed("installed model changed between generations")
        self.model_sha256 = identity
        if type(response["eval_count"]) is not int or response["eval_count"] > settings.num_predict:
            raise LiteratureFailed("model exceeded its exact token ceiling")
        self.calls[-1].update(status="passed", model_sha256=identity, eval_count=response["eval_count"])
        return exact_json(response["response"])


def main(argv: list[str] | None = None) -> int:
    """Worker entry point; providers unavailable=75, malformed producers=1."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=("http", "model", "pdf"), required=True)
    parser.add_argument("--invocation", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        invocation = exact_json(args.invocation.read_bytes())
        verify_platform(
            invocation["platform_sources"],
            invocation["runtime_environment"],
            invocation["implementation_custody"],
            fresh_prefix=Path(invocation["fresh_pycache_prefix"]),
        )
        worker = {"http": _http_worker, "model": _model_worker, "pdf": _pdf_worker}[args.kind]
        result = worker(invocation, args.directory)
        verify_platform(
            invocation["platform_sources"],
            invocation["runtime_environment"],
            invocation["implementation_custody"],
            fresh_prefix=Path(invocation["fresh_pycache_prefix"]),
        )
        return result
    except (LiteratureBlocked, OSError, TimeoutError) as exc:
        print(f"unpaid provider blocked: {type(exc).__name__}: {exc}")  # noqa: T201 - standalone worker diagnostics
        return 75
    except (LiteratureFailed, ValueError, KeyError, TypeError) as exc:
        print(f"unpaid producer rejected: {type(exc).__name__}: {exc}")  # noqa: T201 - standalone worker diagnostics
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
