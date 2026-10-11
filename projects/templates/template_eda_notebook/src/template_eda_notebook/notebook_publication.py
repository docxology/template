"""Portable scientific summary of a completed, locally retained kernel receipt."""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


def public_execution_summary(receipt: dict[str, Any], project_root: Path) -> dict[str, Any]:
    """Publish observed computations and relative custody without machine paths.

    The interpreter hash identifies the exact recorded path string, not its
    executable bytes. The full path, kernel PID and module origins remain in
    the local execution receipt; no replacement path is invented.
    """
    if (
        receipt.get("schema_version") != "template-eda-notebook-execution-v1"
        or receipt.get("status") != "passed"
        or receipt.get("source_execution_audit") != "passed"
    ):
        raise ValueError("publication requires a completed notebook execution receipt")
    custody = receipt["custody_sha256"]
    for relative, digest in custody.items():
        path = PurePosixPath(relative)
        if (
            path.is_absolute()
            or PureWindowsPath(relative).is_absolute()
            or ".." in path.parts
            or path.as_posix() != relative
        ):
            raise ValueError(f"notebook custody needs a portable relative path: {relative!r}")
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError(f"notebook custody needs a SHA-256 identity: {relative!r}")
    if receipt["notebook"] not in custody:
        raise ValueError("published notebook has no relative custody identity")
    root = Path(receipt.get("consumed_project_root", project_root)).absolute()
    if ".." in root.parts:
        raise ValueError("consumed source root cannot contain parent traversal")
    sources = {}
    for module, origin in receipt["loaded_sources"].items():
        if not isinstance(module, str) or not all(part.isidentifier() for part in module.split(".")):
            raise ValueError(f"loaded source needs an actual module name: {module!r}")
        relative = Path(origin).resolve().relative_to(root).as_posix()
        if relative not in custody:
            raise ValueError(f"loaded notebook source has no custody identity: {module!r}")
        sources[module] = relative
    return {
        "schema_version": "template-eda-notebook-summary-v1",
        "status": "passed",
        "notebook": receipt["notebook"],
        "custody_sha256": copy.deepcopy(custody),
        "loaded_sources": sources,
        "limits_seconds": copy.deepcopy(receipt["limits_seconds"]),
        "code_cells_executed": receipt["code_cells_executed"],
        "source_execution_audit": receipt["source_execution_audit"],
        "observations": copy.deepcopy(receipt["observations"]),
        "kernel": {
            "mode": "fresh-audited-selected-interpreter",
            "interpreter_path_sha256": hashlib.sha256(receipt["interpreter"].encode("utf-8")).hexdigest(),
        },
    }


__all__ = ["public_execution_summary"]
