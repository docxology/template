"""Reusable argument contracts for public diagnostics and runtime acceptance."""

from __future__ import annotations

import argparse
from pathlib import Path

from infrastructure.core.testing.pytest_orchestration import parse_project_workers
from infrastructure.project.public_capabilities import CANONICAL_CI_PYTHON_VERSIONS
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES


def positive_int(raw: str) -> int:
    """Parse a strictly positive finite integer subprocess timeout."""
    try:
        value = int(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if value <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return value


def project_workers(raw: str) -> int:
    """Use the canonical bounded outer-worker selection contract."""
    try:
        return parse_project_workers(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def interpreter(raw: str) -> tuple[str, Path]:
    """Require a supported minor and explicit installed environment executable."""
    runtime, separator, path = raw.partition("=")
    if not separator or runtime not in CANONICAL_CI_PYTHON_VERSIONS or not Path(path).is_absolute():
        raise argparse.ArgumentTypeError("use a supported minor=/absolute/environment/bin/python")
    return runtime, Path(path)


def provider_wheel(raw: str) -> tuple[str, Path]:
    """Require an exact canonical public provider and explicit wheel location."""
    scope, separator, path = raw.partition("=")
    if not separator or scope not in PUBLIC_PROJECT_NAMES or not Path(path).is_absolute():
        raise argparse.ArgumentTypeError("use a canonical provider scope=/absolute/output/readiness/provider.whl")
    return scope, Path(path)


__all__ = ["positive_int", "project_workers", "interpreter", "provider_wheel"]
