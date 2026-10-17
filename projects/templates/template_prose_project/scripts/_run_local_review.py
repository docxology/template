#!/usr/bin/env python3
"""Explicit local review operation; excluded from ordinary analysis discovery."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
import hashlib
import importlib.util
import os
import stat

# Establish an empty private cache namespace before importing platform or domain code.
if getattr(sys, "_template_executed_bytecode_audit", None) is None:
    _CACHE = tempfile.TemporaryDirectory(prefix="template-prose-launch-")
    sys.pycache_prefix = str(Path(_CACHE.name).resolve())

import argparse
import math

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

if getattr(sys, "_template_executed_bytecode_audit", None) is None:
    # Startup I/O admits the selected platform's stdlib-only hook before public imports.
    _audit_spec = importlib.util.find_spec("infrastructure")
    if _audit_spec is None or _audit_spec.origin is None:
        raise SystemExit("the declared platform distribution is unavailable")
    _platform_source = Path(_audit_spec.origin).absolute().parent
    _audit_path = _platform_source / "core/bytecode_audit.py"
    _audit_directory = os.open(_audit_path.anchor, getattr(os, "O_PATH", os.O_RDONLY) | os.O_DIRECTORY)
    _audit_directories = [_audit_directory]
    _audit_bindings = []
    try:
        for _name in _audit_path.parts[1:-1]:
            _child = os.open(
                _name, getattr(os, "O_PATH", os.O_RDONLY) | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=_audit_directory
            )
            _audit_bindings.append((_audit_directory, _name, os.fstat(_child)))
            _audit_directories.append(_child)
            _audit_directory = _child
        _audit_descriptor = os.open(
            _audit_path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=_audit_directory
        )
        try:
            _before = os.fstat(_audit_descriptor)
            _audit_bytes = os.read(_audit_descriptor, 65537)
            _after = os.fstat(_audit_descriptor)
            _current = os.stat(_audit_path.name, dir_fd=_audit_directory, follow_symlinks=False)
            _fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
            if (
                not stat.S_ISREG(_before.st_mode)
                or len(_audit_bytes) > 65536
                or len(_audit_bytes) != _before.st_size
                or any(
                    getattr(_before, field) != getattr(_after, field)
                    or getattr(_after, field) != getattr(_current, field)
                    for field in _fields
                )
            ):
                raise SystemExit("the selected audit source changed or is not bounded regular bytes")
            for _parent, _name, _metadata in _audit_bindings:
                _current_directory = os.stat(_name, dir_fd=_parent, follow_symlinks=False)
                if not stat.S_ISDIR(_current_directory.st_mode) or (
                    _current_directory.st_dev,
                    _current_directory.st_ino,
                ) != (_metadata.st_dev, _metadata.st_ino):
                    raise SystemExit("the selected audit source ancestor changed during admission")
        finally:
            os.close(_audit_descriptor)
    finally:
        for _directory in reversed(_audit_directories):
            os.close(_directory)
    _audit_scope = {"__name__": "_template_bytecode_audit", "__file__": str(_audit_path)}
    # Execute the selected local hook only after bounded, no-follow source admission.
    exec(compile(_audit_bytes, str(_audit_path), "exec", dont_inherit=True), _audit_scope)  # nosec B102
    _audit_scope["install_bytecode_audit"](
        tuple(
            str(root.absolute())
            for root in (
                PROJECT_ROOT / "src",
                PROJECT_ROOT / "scripts",
                _platform_source,
                _platform_source.parent / "scripts",
            )
        ),
        fresh_pycache_prefix=sys.pycache_prefix,
        source_sha256=hashlib.sha256(_audit_bytes).hexdigest(),
        startup_code=sys._getframe().f_code,
    )

from template_prose_project.pipeline.llm_review import produce_local_review, validate_transcript
from infrastructure.llm.core.local_ollama import validate_local_endpoint, LocalModelUnavailable
from infrastructure.llm.core.local_review_operation import (
    OperationCustodyError,
    run_review_worker,
    supervise_local_review,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a supervised local prose review")
    parser.add_argument("--mode", choices=["live"], required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--endpoint", default="http://127.0.0.1:11434")
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--num-predict", type=int, default=1024)
    parser.add_argument("--worker-request", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--request-digest", help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        validate_local_endpoint(args.endpoint)
        if (
            not args.model.strip()
            or not math.isfinite(args.timeout)
            or not 0 < args.timeout <= 600
            or not 0 < args.num_predict <= 4096
        ):
            raise ValueError("Select a model, finite timeout within 600 seconds, and token budget within 4096")
    except ValueError as exc:
        parser.error(str(exc))
    try:
        project = args.project_root.absolute()
        script = Path(__file__).absolute()
        if args.worker_request is not None:
            if not args.request_digest:
                parser.error("Worker transport requires the parent request digest")
            return run_review_worker(
                project=project,
                producer_root=PROJECT_ROOT,
                script=script,
                request=args.worker_request,
                expected_digest=args.request_digest,
                producer=produce_local_review,
                validator=validate_transcript,
            )
        if args.request_digest is not None:
            parser.error("Worker transport requires the parent request")
        sources = tuple(
            path.relative_to(project).as_posix() for path in sorted((project / "manuscript").glob("[0-9][0-9]_*.md"))
        )
        return supervise_local_review(
            project=project,
            producer_root=PROJECT_ROOT,
            script=script,
            paths=sources,
            validator=validate_transcript,
            configuration={
                "model": args.model,
                "endpoint": args.endpoint,
                "timeout_seconds": args.timeout,
                "num_predict": args.num_predict,
            },
        )
    except TimeoutError as exc:
        print(f"Local review timed out: {exc}", file=sys.stderr)
        return 124
    except (OSError, LocalModelUnavailable, OperationCustodyError) as exc:
        print(f"Local review blocked: {exc}", file=sys.stderr)
        return 75
    except ValueError as exc:
        print(f"Local review failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
