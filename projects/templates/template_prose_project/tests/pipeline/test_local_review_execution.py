"""Real local HTTP execution and byte/source custody controls."""

from __future__ import annotations

import json
import threading
import subprocess
import sys
import time
from contextlib import contextmanager
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from collections.abc import Iterator

import pytest

from infrastructure.llm.core.local_ollama import generate_local_review, validate_local_endpoint
from template_prose_project.pipeline.config import LLMReviewConfig
from template_prose_project.pipeline.llm_review import produce_local_review, build_llm_review_receipt


@contextmanager
def local_server(
    *,
    missing: bool = False,
    incomplete: bool = False,
    mutate: Path | None = None,
    model: str | None = None,
    eval_count: object = 3,
    delay: float = 0,
) -> Iterator[str]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            payload = {"models": [] if missing else [{"name": "fixture:latest", "digest": "a" * 64}]}
            self._send(payload)

        def do_POST(self) -> None:
            body = self.rfile.read(int(self.headers["Content-Length"]))
            request = json.loads(body)
            if mutate:
                mutate.write_text("concurrently changed")
            time.sleep(delay)
            self._send(
                {
                    "model": model or request["model"],
                    "eval_count": eval_count,
                    "done": not incomplete,
                    "response": "Scoped editorial observations.",
                }
            )

        def _send(self, payload: object) -> None:
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            try:
                self.wfile.write(body)
            except ConnectionError:
                pass

        def log_message(self, format: str, *args: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def source_tree(tmp_path: Path) -> Path:
    source = tmp_path / "manuscript" / "abstract.md"
    source.parent.mkdir()
    source.write_text("A reproducible prose manuscript with stated limitations.")
    return source


def test_real_provider_preserves_bytes_and_rejects_tampering(tmp_path: Path) -> None:
    source = source_tree(tmp_path)
    with local_server() as endpoint:
        transcript = produce_local_review(
            project_root=tmp_path,
            reviewed_paths=("manuscript/abstract.md",),
            model="fixture:latest",
            provider=partial(generate_local_review, endpoint=endpoint),
        )
    config = LLMReviewConfig(True, "ollama", "fixture:latest")
    receipt = build_llm_review_receipt(config, project_root=tmp_path)
    assert receipt["model_digest"] == "a" * 64
    original = transcript.read_text()
    payload = json.loads(original)
    assert source.read_text() in payload["prompt"]
    payload["response"] = "forged response"
    transcript.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="digest"):
        build_llm_review_receipt(config, project_root=tmp_path)
    transcript.write_text(original)
    source.write_text("changed after generation")
    with pytest.raises(ValueError, match="source differs"):
        build_llm_review_receipt(config, project_root=tmp_path)


@pytest.mark.parametrize("missing,incomplete", [(True, False), (False, True)])
def test_real_provider_missing_or_incomplete_cannot_produce_receipt(
    tmp_path: Path, missing: bool, incomplete: bool
) -> None:
    source_tree(tmp_path)
    with local_server(missing=missing, incomplete=incomplete) as endpoint:
        with pytest.raises(ValueError):
            produce_local_review(
                project_root=tmp_path,
                reviewed_paths=("manuscript/abstract.md",),
                model="fixture:latest",
                provider=partial(generate_local_review, endpoint=endpoint),
            )
    assert not (tmp_path / "output" / ".pipeline" / "prose_review" / "latest.json").exists()


def test_actual_source_change_during_generation_fails(tmp_path: Path) -> None:
    source = source_tree(tmp_path)
    with local_server(mutate=source) as endpoint:
        with pytest.raises(ValueError, match="changed during generation"):
            produce_local_review(
                project_root=tmp_path,
                reviewed_paths=("manuscript/abstract.md",),
                model="fixture:latest",
                provider=partial(generate_local_review, endpoint=endpoint),
            )
    assert not (tmp_path / "output" / ".pipeline" / "prose_review" / "latest.json").exists()


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://example.org",
        "http://127.0.0.1:80@evil.invalid",
        "http://127.0.0.1:80/a",
        "http://127.0.0.1:80?secret=x",
        "http://localhost:80",
        "file:///etc/passwd",
    ],
)
def test_provider_endpoint_cannot_leave_loopback(endpoint: str) -> None:
    with pytest.raises(ValueError):
        validate_local_endpoint(endpoint)


@pytest.mark.parametrize("timeout,tokens", [(float("inf"), 1024), (0, 1024), (120, 0), (120, 5000)])
def test_invalid_budgets_fail_before_execution(tmp_path: Path, timeout: float, tokens: int) -> None:
    with pytest.raises(ValueError):
        produce_local_review(
            project_root=tmp_path,
            reviewed_paths=("manuscript/abstract.md",),
            model="fixture:latest",
            provider=generate_local_review,
            timeout_seconds=timeout,
            num_predict=tokens,
        )


@pytest.mark.parametrize("model,count", [("different-model", 3), (None, 0), (None, True), (None, "3")])
def test_provider_rejects_wrong_model_and_non_generation(tmp_path: Path, model: str | None, count: object) -> None:
    source_tree(tmp_path)
    with local_server(model=model, eval_count=count) as endpoint:
        with pytest.raises(ValueError, match="wrong model, or invalid token count"):
            produce_local_review(
                project_root=tmp_path,
                reviewed_paths=("manuscript/abstract.md",),
                model="fixture:latest",
                provider=partial(generate_local_review, endpoint=endpoint),
            )
    assert not (tmp_path / "output/.pipeline/prose_review/latest.json").exists()


def _cli(root: Path, endpoint: str, *extra: str) -> subprocess.CompletedProcess[str]:
    script = Path(__file__).resolve().parents[2] / "scripts/_run_local_review.py"
    return subprocess.run(
        [
            sys.executable,
            str(script),
            "--mode",
            "live",
            "--model",
            "fixture:latest",
            "--project-root",
            str(root),
            "--endpoint",
            endpoint,
            *extra,
        ],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )


def test_real_cli_success_failed_attempt_preserves_history_without_reuse(tmp_path: Path) -> None:
    source_tree(tmp_path).rename(tmp_path / "manuscript/00_abstract.md")
    current = tmp_path / "output/.pipeline/prose_review/latest.json"
    with local_server() as endpoint:
        good = _cli(tmp_path, endpoint)
    execution = tmp_path / "output/.pipeline/prose_review/execution.json"
    assert good.returncode == 0, (
        good.returncode,
        good.stdout,
        good.stderr,
        json.loads(execution.read_text()).get("diagnostic") if execution.is_file() else "execution receipt absent",
    )
    operation = json.loads((tmp_path / "output/.pipeline/prose_review/execution.json").read_text())
    assert operation["status"] == "succeeded" and operation["child_exit_code"] == 0
    assert operation["custody"]["implementation"]["bytecode_binding"] == "fresh-owned-prefix"
    assert operation["transcript_digest"] == __import__("hashlib").sha256(current.read_bytes()).hexdigest()
    config = LLMReviewConfig(True, "ollama", "fixture:latest")
    assert build_llm_review_receipt(config, project_root=tmp_path)["status"] == "verified"
    original = current.read_bytes()
    with local_server(model="wrong-model") as endpoint:
        failed = _cli(tmp_path, endpoint)
    assert failed.returncode == 1, failed.stderr
    assert not current.exists()
    archived = [path.read_bytes() for path in (tmp_path / "output/.pipeline/review_history").rglob("*.json")]
    assert original in archived
    assert len(archived) == 2
    failure = json.loads((tmp_path / "output/.pipeline/prose_review/execution.json").read_text())
    assert failure["status"] == "failed" and failure["child_exit_code"] == 1
    with pytest.raises(ValueError, match="requires transcript"):
        build_llm_review_receipt(config, project_root=tmp_path)


def test_real_cli_deadline_and_invalid_invocation(tmp_path: Path) -> None:
    source_tree(tmp_path).rename(tmp_path / "manuscript/00_abstract.md")
    with local_server(delay=10) as endpoint:
        started = time.monotonic()
        result = _cli(tmp_path, endpoint, "--timeout", "2")
        assert result.returncode == 124, result.stderr
        # The process guardian includes its finite descendant-reaping grace.
        # Coverage-instrumented guardians also have finite startup/reaping budgets.
        assert time.monotonic() - started < 40
        invalid = _cli(tmp_path, endpoint, "--num-predict", "0")
    assert invalid.returncode == 2
    assert not (tmp_path / "output/.pipeline/prose_review/latest.json").exists()
