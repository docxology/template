"""Independent real CLI custody refusals for local manuscript review."""

from __future__ import annotations

import json
import subprocess
import sys
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest


@contextmanager
def _provider(*, mutate: Path | None = None) -> Iterator[tuple[str, list[str]]]:
    consumed: list[str] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self._send({"models": [{"name": "custody:fixture", "digest": "b" * 64}]})

        def do_POST(self) -> None:
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            consumed.append(request["prompt"])
            if mutate is not None:
                mutate.write_text("Source changed during actual provider execution.")
            self._send(
                {
                    "model": request["model"],
                    "eval_count": 3,
                    "done": True,
                    "response": "Bounded observations with explicit limitations.",
                }
            )

        def _send(self, payload: object) -> None:
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", consumed
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def _manuscript(project: Path) -> Path:
    source = project / "manuscript/00_abstract.md"
    source.parent.mkdir(parents=True)
    source.write_text("The original reproducible manuscript has bounded claims.")
    return source


def _invoke(project: Path, endpoint: str) -> subprocess.CompletedProcess[str]:
    repository = Path(__file__).resolve().parents[3]
    script = repository / "projects/templates/template_prose_project/scripts/_run_local_review.py"
    return subprocess.run(
        [
            sys.executable,
            "-I",
            str(script),
            "--mode",
            "live",
            "--model",
            "custody:fixture",
            "--project-root",
            str(project),
            "--endpoint",
            endpoint,
            "--timeout",
            "60",
        ],
        cwd=project.parent,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )


@pytest.mark.parametrize("linked_root", [False, True])
def test_input_links_refuse_before_provider_consumes_external_bytes(tmp_path: Path, linked_root: bool) -> None:
    external = tmp_path / "external"
    source = _manuscript(external)
    project = tmp_path / "project"
    if linked_root:
        project.symlink_to(external, target_is_directory=True)
    else:
        project.mkdir()
        (project / "manuscript").symlink_to(external / "manuscript", target_is_directory=True)
    original = source.read_bytes()
    with _provider() as (endpoint, consumed):
        result = _invoke(project, endpoint)
    assert result.returncode != 0, result.stdout
    assert consumed == []
    assert source.read_bytes() == original
    assert not (external / "output").exists()


def test_receipt_link_preserves_external_sentinel_without_a_generation(tmp_path: Path) -> None:
    project = tmp_path / "project"
    _manuscript(project)
    sentinel = tmp_path / "external-receipt.json"
    sentinel.write_text("private receipt sentinel")
    receipt = project / "output/.pipeline/prose_review/execution.json"
    receipt.parent.mkdir(parents=True)
    receipt.symlink_to(sentinel)
    with _provider() as (endpoint, consumed):
        result = _invoke(project, endpoint)
    assert result.returncode != 0, result.stdout
    assert consumed == []
    assert sentinel.read_text() == "private receipt sentinel"
    assert not (receipt.parent / "latest.json").exists()


@pytest.mark.timeout(100)
def test_source_change_during_real_generation_cannot_publish_success(tmp_path: Path) -> None:
    project = tmp_path / "project"
    source = _manuscript(project)
    original = source.read_text()
    with _provider(mutate=source) as (endpoint, consumed):
        result = _invoke(project, endpoint)
    assert consumed and original in consumed[0]
    assert result.returncode == 75, result.stderr
    current = project / "output/.pipeline/prose_review/latest.json"
    assert not current.exists()
    receipt = json.loads((current.parent / "execution.json").read_text())
    assert receipt["status"] == "blocked" and receipt["child_exit_code"] == 75
    assert receipt["transcript_digest"] == ""
