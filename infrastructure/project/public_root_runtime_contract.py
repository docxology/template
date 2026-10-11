"""Exact source, interpreter and finite budget contract for a Root v2 runtime cohort."""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

from infrastructure.project.public_acceptance_evidence import bootstrap_command, evidence_directory, runtime_identity
from infrastructure.project.public_acceptance_scope import RuntimeScope
from infrastructure.project.public_root_case_admission import load_policy
from infrastructure.project.public_root_case_contract import _json, _root_identity
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader

SPEC_SCHEMA = "template-root-runtime-launch-v3"
CELL_SCHEMA = "template-root-runtime-cohort-v3"
PROCESS_SCHEMA = "template-root-runtime-native-v3"
BUNDLE_ROLE = "actual-root-runtime-cohort"
_RUNTIME_KEYS = frozenset(
    {
        "schema_version",
        "python_version",
        "python_full_version",
        "implementation",
        "executable",
        "interpreter_sha256",
        "packages",
        "missing",
    }
)


def worker_command(interpreter: Path, root: Path, spec: ArtifactSnapshot, *, origin: Any = None) -> tuple[str, ...]:
    launch = (
        (lambda module, *args: origin.bootstrap(root, module, *args))
        if origin
        else (lambda module, *args: bootstrap_command(interpreter, root, module, *args))
    )
    return launch(
        "infrastructure.project.public_root_runtime_worker",
        "--root",
        str(root),
        "--spec",
        str(spec.path),
        "--spec-sha256",
        spec.sha256,
    )


def reader_command(interpreter: Path, root: Path, bundle: ArtifactSnapshot) -> tuple[str, ...]:
    return bootstrap_command(
        interpreter,
        root,
        "infrastructure.project.public_root_runtime_readback",
        "--root",
        str(root),
        "--bundle",
        str(bundle.path),
        "--bundle-sha256",
        bundle.sha256,
    )


def runtime_projection(probe: object) -> dict[str, Any]:
    if not isinstance(probe, dict) or not _RUNTIME_KEYS.issubset(probe):
        raise ValueError("Root runtime cohort requires the actual complete selected interpreter probe")
    actual = {key: probe[key] for key in _RUNTIME_KEYS}
    if (
        actual["missing"] != []
        or actual["python_version"] not in {"3.12", "3.13", "3.14"}
        or not isinstance(actual["executable"], str)
        or not Path(actual["executable"]).is_absolute()
        or not isinstance(actual["interpreter_sha256"], str)
        or re.fullmatch(r"[0-9a-f]{64}", actual["interpreter_sha256"]) is None
    ):
        raise ValueError("Root runtime interpreter probe is missing dependencies or has an invalid identity")
    return actual


def remaining(deadline: float, now: float) -> int:
    value = math.floor(deadline - now)
    if value < 1:
        raise TimeoutError("Root runtime whole deadline exhausted")
    return value


def selection(reader: SnapshotReader, snapshot: ArtifactSnapshot, *, origin: Any = None) -> dict[str, Any]:
    """Reconstruct the complete source-owned selection in the actual selected runtime."""
    spec = _json(snapshot)
    if (
        set(spec)
        != {
            "schema_version",
            "root",
            "root_identity",
            "directory",
            "run_id",
            "nonce",
            "runtime",
            "source_identity",
            "deliverables_identity",
            "mode",
            "timeout_seconds",
            "census_timeout_seconds",
            "test_timeout_seconds",
            "policy_artifact",
            "prerequisites_artifact",
        }
        or spec["schema_version"] != SPEC_SCHEMA
        or spec["root"] != str(origin.root if origin else reader.root)
        or spec["root_identity"] != (origin.identity if origin else _root_identity(reader.root))
        or not isinstance(spec["root_identity"], list)
        or any(type(value) is not int for value in spec["root_identity"])
        or spec["mode"] not in {"core", "live"}
        or any(
            type(spec[key]) is not int or not 1 <= spec[key] <= 14400
            for key in ("timeout_seconds", "test_timeout_seconds", "census_timeout_seconds")
        )
        or spec["census_timeout_seconds"] > 3600
        or spec["census_timeout_seconds"] >= spec["timeout_seconds"]
        or any(
            not isinstance(spec[key], str) or re.fullmatch(r"[0-9a-f]{32}", spec[key]) is None
            for key in ("run_id", "nonce")
        )
        or spec["runtime"] != (origin.runtime if origin else runtime_identity())
        or runtime_projection(spec["runtime"]) != spec["runtime"]
        or not isinstance(spec["directory"], str)
    ):
        raise ValueError("Root runtime cohort differs from its exact original selected source/runtime specification")
    directory = evidence_directory(reader.root, reader.root / spec["directory"])
    if snapshot.path != directory / "runtime-spec.json":
        raise ValueError("Root runtime specification is outside its original cohort directory")
    scope = RuntimeScope(reader.root, "root")
    _, policy_binding, prerequisites_binding, _ = load_policy(reader)
    if (
        spec["source_identity"] != scope.source_identity()
        or spec["deliverables_identity"] != scope.deliverables_identity()
        or spec["policy_artifact"] != policy_binding
        or spec["prerequisites_artifact"] != prerequisites_binding
        or not reader.unchanged()
    ):
        raise ValueError("Root runtime source, deliverables or source-owned complete policy changed")
    return spec
