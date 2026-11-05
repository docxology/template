"""Portable original observations; receipt hashes do not authenticate origin.

Executable bytes are observed twice on the producer and are never redistributed
or reopened on a reader. These transcripts retain the same local receipt trust
boundary as original process outcomes, not a remote execution attestation.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.project.public_acceptance_evidence import bootstrap_command

CUSTODY_SCHEMA = "template-native-producer-custody-v1"
EXECUTABLE_SCHEMA = "template-native-executable-observation-v1"


def _absolute(value: object) -> Path:
    if not isinstance(value, str) or "\\" in value or "\0" in value:
        raise ValueError("producer custody requires a canonical absolute path")
    path = Path(value)
    if not path.is_absolute() or ".." in path.parts or str(path) != value:
        raise ValueError("producer custody requires a canonical absolute path")
    return path


def executable_observation(executable: Path) -> dict[str, str]:
    """Observe exact installed bytes without copying executable distributions."""
    path = executable.resolve(strict=True)
    digest = hashlib.sha256(read_bytes_confined(path.parent, path, max_bytes=512 * 1024 * 1024)).hexdigest()
    return {"schema_version": EXECUTABLE_SCHEMA, "path": str(executable.absolute()), "sha256": digest}


def validate_executable_observation(raw: object, executable: str, digest: object) -> None:
    _absolute(executable)
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise ValueError("original executable digest is invalid")
    if raw != {"schema_version": EXECUTABLE_SCHEMA, "path": executable, "sha256": digest}:
        raise ValueError("original executable observation changed")


def producer_custody(root: Path, runtime: dict[str, Any], source_digest: str) -> dict[str, str]:
    return {
        "schema_version": CUSTODY_SCHEMA,
        "root": str(root.resolve()),
        "implementation_root": str(Path(__file__).resolve().parents[1]),
        "runtime_digest": canonical_digest(runtime),
        "source_digest": source_digest,
    }


def validate_producer_custody(raw: object, runtime: dict[str, Any], source_digest: str) -> dict[str, str]:
    names = {"schema_version", "root", "implementation_root", "runtime_digest", "source_digest"}
    if not isinstance(raw, dict) or set(raw) != names or raw.get("schema_version") != CUSTODY_SCHEMA:
        raise ValueError("versioned original producer custody is required")
    from infrastructure.core.testing.pytest_profiles import TEST_RUNNER_BASE_DEPS
    from infrastructure.project.public_acceptance_evidence import RUNTIME_SCHEMA

    runtime_names = {
        "schema_version",
        "python_version",
        "python_full_version",
        "implementation",
        "executable",
        "interpreter_sha256",
        "packages",
        "missing",
    }
    packages = runtime.get("packages")
    if (
        set(runtime) != runtime_names
        or runtime.get("schema_version") != RUNTIME_SCHEMA
        or runtime.get("missing") != []
        or runtime.get("implementation") != "CPython"
        or not isinstance(packages, dict)
        or set(packages) != set((*TEST_RUNNER_BASE_DEPS, "coverage"))
        or any(not isinstance(value, str) or not value for value in packages.values())
        or not isinstance(runtime.get("python_full_version"), str)
        or not runtime["python_full_version"].startswith(str(runtime.get("python_version")) + ".")
    ):
        raise ValueError("original prepared runtime observation is invalid")
    _absolute(raw["root"])
    _absolute(raw["implementation_root"])
    if raw["runtime_digest"] != canonical_digest(runtime) or raw["source_digest"] != source_digest:
        raise ValueError("original producer source/runtime custody changed")
    return raw


def producer_path(custody: dict[str, str], reader_root: Path, path: Path) -> Path:
    """Project an admitted reader path; never resolve or read a producer path."""
    return _absolute(custody["root"]) / path.relative_to(reader_root)


def producer_bootstrap(
    custody: dict[str, str], reader_root: Path, runtime: dict[str, Any], module: str, *args: str
) -> list[str]:
    return list(
        bootstrap_command(
            Path(runtime["executable"]),
            reader_root,
            module,
            *args,
            command_root=_absolute(custody["root"]),
            implementation_root=_absolute(custody["implementation_root"]),
        )
    )
