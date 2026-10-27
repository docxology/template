"""Source-bound root and public-exemplar installed-wheel runtime matrix."""

from __future__ import annotations

import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Mapping, Sequence

from infrastructure.project.installed_acceptance_worker import run_installed_cell
from infrastructure.project.installed_acceptance_runtime import declared_local_dependencies, local_dependency_closure
from infrastructure.project.public_acceptance_evidence import evidence_directory, gate_payload, write_json
from infrastructure.project.public_capabilities import CANONICAL_CI_PYTHON_VERSIONS
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.readiness_receipts import SCHEMA_VERSION, aggregate_state, source_fingerprint
from infrastructure.reporting.release_readiness_profile import Requirement, required_profile
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.reporting.release_readiness_validators import validate_acceptance


def _gate(
    root: Path,
    directory: Path,
    requirement: Requirement,
    fingerprint: str,
    status: str,
    details: dict[str, Any],
    blockers: list[dict[str, str]],
) -> dict[str, Any]:
    payload = gate_payload(requirement, fingerprint, status, details, blockers)
    if status == "pass":
        try:
            validate_acceptance(requirement, payload, SnapshotReader(root))
        except (OSError, ValueError, TypeError, KeyError) as error:
            status = "fail"
            payload = gate_payload(
                requirement, fingerprint, status, {**details, "diagnostic": f"gate admission failed: {error}"}, blockers
            )
    binding = write_json(root, directory / f"{requirement.kind}-gate.json", payload)
    return {
        "status": status,
        "command": details.get("command", ["source-bound-installed-matrix"]),
        "artifact": binding["path"],
        "artifact_sha256": binding["sha256"],
    }


def run_installed_acceptance(
    root: Path,
    interpreters: Mapping[str, Path],
    *,
    projects: Sequence[str] | None = None,
    project_workers: int = 1,
    timeout_seconds: int = 600,
    evidence_dir: Path | None = None,
) -> dict[str, Any]:
    """Execute three sequential runtime waves, with at most three package cells in flight."""
    if (
        type(project_workers) is not int
        or not 1 <= project_workers <= 3
        or type(timeout_seconds) is not int
        or timeout_seconds <= 0
    ):
        raise ValueError("installed workers must be 1..3 and the deadline a positive integer")
    if set(interpreters) - set(CANONICAL_CI_PYTHON_VERSIONS):
        raise ValueError("selected runtime is outside the supported public contract")
    scopes = ("root", *PUBLIC_PROJECT_NAMES) if projects is None else tuple(projects)
    if not scopes or len(set(scopes)) != len(scopes) or set(scopes) - {"root", *PUBLIC_PROJECT_NAMES}:
        raise ValueError("installed selection must contain unique canonical public scopes")
    root = root.resolve()
    prerequisites = {provider for scope in scopes for provider in local_dependency_closure(root, scope)}
    scopes = (
        *(scope for scope in ("root", *PUBLIC_PROJECT_NAMES) if scope in prerequisites and scope not in scopes),
        *scopes,
    )
    dependencies = {scope: set(declared_local_dependencies(root, scope)) for scope in scopes}
    run_id = uuid.uuid4().hex
    directory = evidence_directory(root, evidence_dir or root / "output/readiness" / f"installed-{run_id}", fresh=True)
    fingerprint = source_fingerprint(root)
    profile, faults = required_profile(root, SnapshotReader(root), fingerprint)
    if faults:
        raise ValueError("source-owned installed acceptance profile is invalid")
    requirements = {requirement.id: requirement for requirement in profile}
    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix=f"template-installed-{run_id}-") as temporary:
        scratch = Path(temporary).resolve()
        for runtime in CANONICAL_CI_PYTHON_VERSIONS:
            provider_wheels: dict[str, tuple[dict[str, str], Requirement]] = {}
            work = [
                (scope, scratch / f"{scope.replace('/', '_')}-{runtime}", directory / scope / runtime)
                for scope in scopes
            ]

            def execute(item: tuple[str, Path, Path]) -> dict[str, Any]:
                scope, cell_scratch, cell_directory = item
                return run_installed_cell(
                    root,
                    requirements[f"{scope}:installed"],
                    runtime,
                    interpreters.get(runtime),
                    cell_scratch,
                    cell_directory,
                    timeout_seconds=timeout_seconds,
                    provider_wheels=dict(provider_wheels),
                )

            completed: set[str] = set()
            with ThreadPoolExecutor(max_workers=project_workers) as workers:
                while work:
                    ready = [item for item in work if dependencies[item[0]] <= completed]
                    if not ready:
                        raise ValueError("canonical provider graph has no admissible topological wave")
                    observed = list(workers.map(execute, ready))
                    results.extend(observed)
                    for cell in observed:
                        scope = cell["scope"]
                        completed.add(scope)
                        if cell["status"] == "pass":
                            provider_wheels[scope] = (
                                dict(cell["details"]["wheel_artifact"]),
                                requirements[f"{scope}:installed"],
                            )
                    work = [item for item in work if item[0] not in completed]
    try:
        current = source_fingerprint(root) == fingerprint
    except (OSError, ValueError):
        current = False
    gates = {}
    for scope in scopes:
        cells = [cell for cell in results if cell["scope"] == scope]
        status = aggregate_state(tuple(cell["status"] for cell in cells))
        if not current:
            status = "fail"
        blockers = [blocker for cell in cells for blocker in cell.get("blockers", [])]
        details = {
            **cells[-1].get("details", {}),
            "runtime_observations": cells,
            "tested_python_versions": list(CANONICAL_CI_PYTHON_VERSIONS),
            "source_current": current,
        }
        if status != "pass":
            details["diagnostic"] = "; ".join(cell.get("diagnostic", "") for cell in cells)
        gates[f"{scope}:installed"] = _gate(
            root, directory / scope, requirements[f"{scope}:installed"], fingerprint, status, details, blockers
        )
        exported = [cell for cell in cells if cell.get("export")]
        export_status = (
            "pass"
            if len(exported) == len(cells) and current
            else "blocked"
            if current and status == "blocked"
            else "fail"
        )
        gates[f"{scope}:export"] = _gate(
            root,
            directory / scope,
            requirements[f"{scope}:export"],
            fingerprint,
            export_status,
            exported[-1]["export"] if exported else {},
            blockers if export_status == "blocked" else [],
        )
    counts = {status: sum(cell["status"] == status for cell in results) for status in ("pass", "fail", "blocked")}
    exit_code = (
        1
        if not current or counts["fail"] or any(gate["status"] == "fail" for gate in gates.values())
        else 75
        if counts["blocked"]
        else 0
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "platform_version": requirements["root:installed"].version,
        "source_fingerprint": fingerprint,
        "roster": list(PUBLIC_PROJECT_NAMES),
        "gates": gates,
        "installed_matrix": {
            "run_id": run_id,
            "expected_cells": 3 * (len(PUBLIC_PROJECT_NAMES) + 1),
            "observed_cells": len(results),
            "source_current": current,
            "counts": counts,
            "matrix_complete": scopes == ("root", *PUBLIC_PROJECT_NAMES),
            "results": results,
        },
        "exit_code": exit_code,
    }
    binding = write_json(root, directory / "receipt.json", report)
    return {**report, "receipt": binding}
