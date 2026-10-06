"""Supervise explicit local review producers over frozen public input bytes."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from infrastructure.core.execution_boundary import build_bounded_env, run_bounded_subprocess
from infrastructure.core.files.project_lock import project_output_lock
from infrastructure.core.files.secure_write import (
    atomic_write_bytes_confined,
    atomic_write_text_confined,
    read_bytes_confined,
    unlink_confined,
)
from infrastructure.core.implementation_custody import (
    bytecode_audit_bootstrap,
    capture_implementation_custody,
    source_file_digest,
    source_file_manifest,
    verify_fresh_module_bytecode,
)
from infrastructure.core.logging.utils import get_logger
from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.llm.core.local_ollama import LocalModelUnavailable, generate_local_review

SCHEMA = "template-local-review-execution/1"
TRANSCRIPT = Path("output/.pipeline/prose_review/latest.json")
RECEIPT = Path("output/.pipeline/prose_review/execution.json")
_BOOTSTRAP = "import runpy,sys;runpy.run_path(sys.argv.pop(1),run_name='__main__')"
Producer = Callable[..., Path]
Validator = Callable[[dict[str, Any]], None]
logger = get_logger(__name__)


class OperationCustodyError(ValueError):
    """Actual consumed source or operation identity differs from the controller."""


def _snapshot(project: Path, producer_root: Path, script: Path, paths: tuple[str, ...]) -> dict[str, Any]:
    sources: dict[str, str] = {}
    for relative in paths:
        candidate = Path(relative)
        if candidate.is_absolute() or ".." in candidate.parts or "\\" in relative:
            raise ValueError("Reviewed inputs require confined relative paths")
        sources[relative] = hashlib.sha256(
            read_bytes_confined(project, project / candidate, max_bytes=1024 * 1024)
        ).hexdigest()
    if not paths or len(set(paths)) != len(paths):
        raise ValueError("Review requires nonempty unique source paths")
    prefix = Path(sys.pycache_prefix or "")
    if sys.pycache_prefix is None:
        raise ValueError("Local review requires a fresh launcher-owned bytecode prefix")
    implementation = capture_implementation_custody(fresh_pycache_prefix=prefix)
    verify_fresh_module_bytecode(producer_root / "src", prefix)
    verify_fresh_module_bytecode(producer_root / "scripts", prefix)
    metadata: dict[str, dict[str, str | None]] = {}
    for label, root in (("project", project), ("producer", producer_root)):
        metadata[label] = {}
        for name in ("pyproject.toml", "uv.lock", ".python-version", "pipeline.yaml", "pipeline_plugins.yaml"):
            try:
                content = read_bytes_confined(root, root / name)
            except FileNotFoundError:
                metadata[label][name] = None
            else:
                metadata[label][name] = hashlib.sha256(content).hexdigest()
    return {
        "implementation": implementation,
        "producer": source_file_digest(script),
        "producer_source": source_file_manifest(producer_root / "src", frozenset({".py"})),
        "project_source": source_file_manifest(project / "src", frozenset({".py"})),
        "manuscript_source": source_file_manifest(project / "manuscript", frozenset({".md", ".yaml", ".bib"})),
        "metadata": metadata,
        "reviewed_sources": sources,
    }


def _verify(spec: dict[str, Any], project: Path, producer_root: Path, script: Path) -> None:
    try:
        current = _snapshot(project, producer_root, script, tuple(spec["paths"]))
    except (OSError, ValueError) as exc:
        raise OperationCustodyError(f"Current review custody cannot be verified: {exc}") from exc
    if current != spec["custody"]:
        raise OperationCustodyError("Reviewed inputs or actual implementation changed")


def _validate_produced_transcript(spec: dict[str, Any], raw: bytes, validator: Validator) -> None:
    transcript = json.loads(raw)
    validator(transcript)
    configuration = spec["configuration"]
    if (
        transcript["provider"] != "ollama"
        or transcript["model"] != configuration["model"]
        or transcript["reviewed_sources"] != spec["custody"]["reviewed_sources"]
        or transcript["budget"]
        != {
            "timeout_seconds": configuration["timeout_seconds"],
            "num_predict": configuration["num_predict"],
            "seed": 0,
            "temperature": 0.0,
        }
    ):
        raise OperationCustodyError("Produced transcript differs from the resolved review")


def _archive(project: Path, relative: Path) -> None:
    target = project / relative
    try:
        content = read_bytes_confined(project, target)
    except FileNotFoundError:
        return
    digest = hashlib.sha256(content).hexdigest()
    atomic_write_bytes_confined(
        project, project / "output/.pipeline/review_history" / digest / target.name, content, mode=0o600
    )
    unlink_confined(project, target)


def _clear(project: Path, relative: Path) -> None:
    try:
        unlink_confined(project, project / relative)
    except FileNotFoundError:
        pass


def _record(
    project: Path,
    spec: dict[str, Any],
    *,
    status: str,
    child_code: int | None,
    diagnostic: str = "",
    transcript_digest: str = "",
) -> None:
    payload = {
        "schema_version": SCHEMA,
        "run_id": spec["run_id"],
        "spec_digest": canonical_digest(spec),
        "mode": "live",
        "status": status,
        "child_exit_code": child_code,
        "configuration": spec["configuration"],
        "custody": spec["custody"],
        "transcript_digest": transcript_digest,
        "diagnostic": diagnostic,
    }
    atomic_write_text_confined(project, project / RECEIPT, json.dumps(payload, sort_keys=True) + "\n", mode=0o600)


def run_review_worker(
    *,
    project: Path,
    producer_root: Path,
    script: Path,
    request: Path,
    expected_digest: str,
    producer: Producer,
    validator: Validator,
) -> int:
    """Produce in a private snapshot and publish only current, validated bytes."""
    scratch = request.parent
    spec = json.loads(read_bytes_confined(scratch, request))
    if (
        not isinstance(spec, dict)
        or canonical_digest(spec) != expected_digest
        or spec.get("schema_version") != SCHEMA
        or spec.get("project") != str(project)
        or spec.get("producer_root") != str(producer_root)
        or spec.get("script") != str(script)
    ):
        raise OperationCustodyError("Worker request differs from the controller")
    _verify(spec, project, producer_root, script)
    frozen = scratch / "frozen_inputs"
    frozen.mkdir(mode=0o700)
    for relative, digest in spec["custody"]["reviewed_sources"].items():
        raw = read_bytes_confined(project, project / relative, max_bytes=1024 * 1024)
        if hashlib.sha256(raw).hexdigest() != digest:
            raise OperationCustodyError("Reviewed input changed before snapshot consumption")
        atomic_write_bytes_confined(frozen, frozen / relative, raw, mode=0o600)
    configuration = spec["configuration"]
    from functools import partial

    generated = producer(
        project_root=frozen,
        reviewed_paths=tuple(spec["paths"]),
        model=configuration["model"],
        timeout_seconds=configuration["timeout_seconds"],
        num_predict=configuration["num_predict"],
        provider=partial(generate_local_review, endpoint=configuration["endpoint"]),
    )
    if generated != frozen / TRANSCRIPT:
        raise OperationCustodyError("Producer wrote outside its expected frozen output")
    raw = read_bytes_confined(frozen, generated)
    _validate_produced_transcript(spec, raw, validator)
    _verify(spec, project, producer_root, script)
    if time.monotonic() >= spec["deadline_monotonic"]:
        raise TimeoutError("Review deadline expired before transcript admission")
    atomic_write_bytes_confined(project, project / TRANSCRIPT, raw, mode=0o600)
    # The parent owns the final receipt after validating cleanup, source, output
    # and its whole-run deadline. A worker exit alone never authorizes acceptance.
    return 0


def supervise_local_review(
    *,
    project: Path,
    producer_root: Path,
    script: Path,
    paths: tuple[str, ...],
    configuration: dict[str, Any],
    validator: Validator,
) -> int:
    """Require a fresh supervised generation and preserve failed attempts honestly."""
    deadline = time.monotonic() + configuration["timeout_seconds"]
    with project_output_lock(project, timeout=configuration["timeout_seconds"]):
        _archive(project, TRANSCRIPT)
        _archive(project, RECEIPT)
        spec = {
            "schema_version": SCHEMA,
            "run_id": uuid.uuid4().hex,
            "project": str(project),
            "producer_root": str(producer_root),
            "script": str(script),
            "paths": list(paths),
            "configuration": configuration,
            "deadline_monotonic": deadline,
            "custody": _snapshot(project, producer_root, script, paths),
        }
        code: int | None = None
        status, diagnostic = "failed", ""
        try:
            with tempfile.TemporaryDirectory(prefix="template-local-review-") as temporary:
                scratch = Path(temporary).resolve()
                cache = scratch / "bytecode"
                cache.mkdir(mode=0o700)
                request = scratch / "request.json"
                atomic_write_text_confined(scratch, request, json.dumps(spec, sort_keys=True), mode=0o600)
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("Review deadline expired before worker launch")
                implementation = Path(__file__).absolute().parents[2]
                bootstrap = (
                    bytecode_audit_bootstrap(
                        (
                            implementation,
                            implementation.parent / "scripts",
                            producer_root / "src",
                            producer_root / "scripts",
                        ),
                        cache,
                    )
                    + _BOOTSTRAP
                )
                child = run_bounded_subprocess(
                    [
                        sys.executable,
                        "-I",
                        "-X",
                        f"pycache_prefix={cache}",
                        "-c",
                        bootstrap,
                        str(script),
                        "--mode",
                        "live",
                        "--model",
                        configuration["model"],
                        "--project-root",
                        str(project),
                        "--endpoint",
                        configuration["endpoint"],
                        "--timeout",
                        str(configuration["timeout_seconds"]),
                        "--num-predict",
                        str(configuration["num_predict"]),
                        "--worker-request",
                        str(request),
                        "--request-digest",
                        canonical_digest(spec),
                    ],
                    cwd=project,
                    env=build_bounded_env(),
                    timeout=remaining,
                )
            code = child.original_returncode if child.original_returncode is not None else child.returncode
            diagnostic = child.command_error or child.stderr[-2048:] or child.stdout[-2048:]
            if child.timed_out:
                raise TimeoutError("Local review exceeded its whole-run deadline")
            if child.command_error or child.returncode != 0:
                status = (
                    "blocked"
                    if child.custody_refused or child.returncode == 75
                    else "interrupted"
                    if child.returncode in {130, -2}
                    else "timed_out"
                    if child.returncode == 124
                    else "failed"
                )
            else:
                _verify(spec, project, producer_root, script)
                raw = read_bytes_confined(project, project / TRANSCRIPT)
                _validate_produced_transcript(spec, raw, validator)
                if time.monotonic() >= deadline:
                    raise TimeoutError("Review deadline expired during final custody validation")
                _record(
                    project,
                    spec,
                    status="succeeded",
                    child_code=code,
                    transcript_digest=hashlib.sha256(raw).hexdigest(),
                )
                if time.monotonic() >= deadline:
                    raise TimeoutError("Review deadline expired during receipt publication")
                return 0
        except KeyboardInterrupt:
            status, diagnostic = "interrupted", "Local review interrupted"
        except TimeoutError as exc:
            status, diagnostic = "timed_out", str(exc)
        except OperationCustodyError as exc:
            status, diagnostic = "blocked", str(exc)
        except (OSError, ValueError) as exc:
            status, diagnostic = "blocked" if isinstance(exc, LocalModelUnavailable) else "failed", str(exc)
        _clear(project, TRANSCRIPT)
        _record(project, spec, status=status, child_code=code, diagnostic=diagnostic)
        logger.error("Local review %s: %s", status, diagnostic)
        return {"interrupted": 130, "timed_out": 124, "blocked": 75}.get(status, 1)


__all__ = ["run_review_worker", "supervise_local_review", "OperationCustodyError"]
