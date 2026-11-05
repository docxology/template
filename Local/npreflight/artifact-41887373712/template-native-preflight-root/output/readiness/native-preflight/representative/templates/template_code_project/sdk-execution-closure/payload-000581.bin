"""Exact Root v2 lane admission and source-owned pytest invocations."""

from __future__ import annotations

import os
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from infrastructure.core.execution_boundary import build_bounded_env
from infrastructure.core.execution_policy import apply_execution_policy
from infrastructure.core.files.secure_write import atomic_write_text_confined
from infrastructure.project.public_acceptance_evidence import bootstrap_command, cell_environment, evidence_directory
from infrastructure.project.public_root_case_admission import (
    PINNED_MODEL_ENVIRONMENT_KEY,
    RootCaseAdmission,
    admit_plan,
)
from infrastructure.project.public_root_case_units import RootCaseUnit, admitted_units
from infrastructure.project.public_root_case_contract import _artifact, _json, _root_identity
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader

LAUNCH_SCHEMA = "template-root-lane-launch-v2"
COORDINATOR_SCHEMA = "template-root-lane-coordinator-v2"
COORDINATOR_PROCESS_SCHEMA = "template-root-lane-coordinator-process-v2"
CHUNK_SCHEMA = "template-root-lane-chunk-v2"
LANE_SCHEMA = "template-root-lane-result-v2"
PROCESS_SCHEMA = "template-root-lane-native-process-v2"


def write(root: Path, path: Path, payload: object, identity: list[int]) -> dict[str, str]:
    """Hold every lane write to the originally admitted physical Root directory."""
    if len(identity) != 2 or any(type(value) is not int for value in identity):
        raise ValueError("Root lane write requires the original physical directory identity")
    target = evidence_directory(root, path.parent) / path.name
    text = json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    atomic_write_text_confined(root, target, text, expected_root_identity=(identity[0], identity[1]))
    return {"path": target.relative_to(root).as_posix(), "sha256": hashlib.sha256(text.encode()).hexdigest()}


def selection(admitted: RootCaseAdmission, unit_id: str) -> RootCaseUnit:
    """Resolve an exact source-required applicability unit, never filter a caller subset."""
    selected = next((unit for unit in admitted_units(admitted) if unit.id == unit_id), None)
    if selected is None:
        raise ValueError("Root execution requires an exact nonempty source-required applicability unit")
    return selected


def groups(nodeids: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
    if not nodeids or len(set(nodeids)) != len(nodeids):
        raise ValueError("Root lane execution requires a nonempty unique exact case set")
    return tuple(nodeids[index : index + 100] for index in range(0, len(nodeids), 100))


def lane_command(
    root: Path, spec: ArtifactSnapshot, *, chunk: int | None = None, origin: Any = None
) -> tuple[str, ...]:
    arguments = ["--root", str(root), "--spec", str(spec.path), "--spec-sha256", spec.sha256]
    if chunk is not None:
        arguments.extend(["--chunk", str(chunk)])
    if origin:
        return tuple(origin.bootstrap(root, "infrastructure.project.public_root_lane_worker", *arguments))
    return bootstrap_command(Path(sys.executable), root, "infrastructure.project.public_root_lane_worker", *arguments)


def arguments(root: Path, directory: Path, nodes: tuple[str, ...], timeout: int) -> list[str]:
    return [
        "-c",
        str(root / "pyproject.toml"),
        "--rootdir",
        str(root),
        "--confcutdir",
        str(root),
        "-o",
        "addopts=",
        "--import-mode=importlib",
        "--assert=plain",
        "--strict-markers",
        "-p",
        "no:cacheprovider",
        "--timeout=" + str(timeout),
        "--timeout-method=signal",
        "--timeout-disable-debugger-detection",
        "--benchmark-storage=" + str(directory / "benchmarks"),
        "-q",
        "--tb=short",
        *nodes,
    ]


def prepared_model_environment(env: dict[str, str]) -> dict[str, str]:
    """Keep Root acceptance on prepared models after every prerequisite overlay.

    Root lanes never acquire local models: the pin is applied last, so neither a
    caller value (unset or ``0``) nor a declared prerequisite overlay can enable a
    model download. Missing declared preparation still blocks before execution.
    """
    return dict(env, **{PINNED_MODEL_ENVIRONMENT_KEY: "1"})


def environment(admission: RootCaseAdmission, lane_id: str, root: Path, directory: Path, mode: str) -> dict[str, str]:
    env = build_bounded_env(cell_environment(Path(sys.executable), directory, repo_root=root))
    env = apply_execution_policy(env, root, mode=mode)
    selected = selection(admission, lane_id)
    if mode == "live":
        for prerequisite in admission.prerequisites:
            if prerequisite.id in selected.obligations:
                for key in prerequisite.environment_keys:
                    if key in os.environ:
                        env[key] = os.environ[key]
    # Propagate only the actual coordinator's acquired lock identity.
    env.update({key: value for key, value in os.environ.items() if key.startswith("TEMPLATE_PROJECT_LOCK_")})
    return prepared_model_environment(env)


def admission(
    reader: SnapshotReader, snapshot: ArtifactSnapshot, *, origin: Any = None
) -> tuple[dict[str, Any], RootCaseAdmission]:
    spec = _json(snapshot)
    if (
        set(spec)
        != {
            "schema_version",
            "root",
            "directory",
            "run_id",
            "nonce",
            "lane",
            "mode",
            "timeout_seconds",
            "test_timeout_seconds",
            "census_bundle_artifact",
            "root_identity",
        }
        or spec["schema_version"] != LAUNCH_SCHEMA
        or spec["root"] != str(origin.root if origin else reader.root)
        or not isinstance(spec["root_identity"], list)
        or len(spec["root_identity"]) != 2
        or any(type(value) is not int for value in spec["root_identity"])
        or spec["root_identity"] != (origin.identity if origin else _root_identity(reader.root))
        or not isinstance(spec["mode"], str)
        or not isinstance(spec["lane"], str)
        or spec["mode"] not in {"core", "live"}
        or any(
            type(spec[key]) is not int or not 1 <= spec[key] <= 14400
            for key in ("timeout_seconds", "test_timeout_seconds")
        )
    ):
        raise ValueError("Root lane launch differs from its immutable source-owned contract")
    for key in ("run_id", "nonce"):
        if (
            not isinstance(spec[key], str)
            or len(spec[key]) != 32
            or any(char not in "0123456789abcdef" for char in spec[key])
        ):
            raise ValueError("Root lane identities must be original fresh run/nonce tokens")
    if not isinstance(spec["directory"], str):
        raise ValueError("Root lane directory must be an exact public evidence path")
    directory = evidence_directory(reader.root, reader.root / spec["directory"])
    if snapshot.path != directory / "lane-spec.json":
        raise ValueError("Root lane specification is outside its original run directory")
    bundle = _json(_artifact(reader, spec["census_bundle_artifact"]))
    admitted = admit_plan(reader, bundle, origin=origin)
    selection(admitted, spec["lane"])
    return spec, admitted
