"""All required Root v2 case cells, original prepared-runtime execution and truthful gates."""

from __future__ import annotations

import sys
import uuid
from pathlib import Path
from typing import Any, Mapping

from infrastructure.project.public_acceptance import _entry as _unbound_entry, _probe_runtime
from infrastructure.project.public_acceptance_evidence import evidence_directory, write_json
from infrastructure.project.public_acceptance_scope import RuntimeScope
from infrastructure.project.public_capabilities import CANONICAL_CI_PYTHON_VERSIONS
from infrastructure.project.public_root_case_admission import load_policy
from infrastructure.project.public_root_case_contract import _root_identity
from infrastructure.project.public_root_case_units import declared_units, optional_external_records
from infrastructure.project.public_root_runtime_producer import produce_runtime_cohort, read_selected_runtime
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.readiness_receipts import SCHEMA_VERSION
from infrastructure.reporting.release_readiness_profile import Requirement, required_profile
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.reporting.release_readiness_validators import validate_acceptance


def _details(
    probe: dict[str, Any], bundle_artifact: dict[str, str], observed: dict[str, Any], policy_sha256: str
) -> dict[str, Any]:
    runtime = observed["runtime"]
    return {
        "execution_exit_code": 0,
        "python_version": runtime["python_version"],
        "python_full_version": runtime["python_full_version"],
        "implementation": runtime["implementation"],
        "interpreter": runtime["executable"],
        "runtime_artifact": probe["binding"],
        "root_case_bundle_artifact": bundle_artifact,
        "case_policy_sha256": policy_sha256,
        "policy_artifact_sha256": observed["policy_artifact"]["sha256"],
    }


def _entry(
    root: Path,
    directory: Path,
    requirement: Requirement,
    fingerprint: str,
    status: str,
    command: list[str],
    details: dict[str, Any],
    blockers: list[dict[str, str]] | None = None,
    *,
    identity: tuple[int, int],
) -> dict[str, Any]:
    """An admitted run cannot write evidence into a replacement physical Root."""
    try:
        return _unbound_entry(
            root,
            directory,
            requirement,
            fingerprint,
            status,
            command,
            details,
            blockers,
            expected_root_identity=identity,
        )
    except (OSError, ValueError) as error:
        raise RuntimeError("original Root evidence write refused after run admission") from error


def _verified_gate(
    root: Path,
    directory: Path,
    requirement: Requirement,
    fingerprint: str,
    command: list[str],
    details: dict[str, Any],
    identity: tuple[int, int],
) -> tuple[dict[str, Any], str, int]:
    from infrastructure.project.public_acceptance_evidence import gate_payload

    try:
        reader = SnapshotReader(root)
        validate_acceptance(requirement, gate_payload(requirement, fingerprint, "pass", details), reader)
        if not reader.unchanged():
            raise ValueError("Root acceptance consumed source changed")
        status, code = "pass", 0
    except KeyboardInterrupt:
        status, code = "fail", 130
        details = {**details, "execution_exit_code": code, "diagnostic": "original Root case readback interrupted"}
    except TimeoutError:
        status, code = "fail", 124
        details = {
            **details,
            "execution_exit_code": code,
            "diagnostic": "original Root case readback deadline exhausted",
        }
    except (OSError, ValueError, TypeError, KeyError, RuntimeError):
        status, code = "fail", 1
        details = {
            **details,
            "execution_exit_code": code,
            "diagnostic": "original Root case or coverage readback refused",
        }
    return _entry(root, directory, requirement, fingerprint, status, command, details, identity=identity), status, code


def run_root_case_acceptance(
    root: Path,
    interpreters: Mapping[str, Path],
    *,
    evidence_dir: Path | None = None,
    mode: str = "core",
    timeout_seconds: int = 7200,
    test_timeout_seconds: int = 120,
) -> dict[str, Any]:
    """Execute prepared interpreters serially; all other required cells remain explicit.

    Source-owned v2 classification is mandatory. Publication, paid operations and
    runtime acquisition are unavailable here. An enclosing program supervises
    synchronous API admission/readback if it requires a hard overall deadline.
    """
    if mode not in {"core", "live"} or set(interpreters) - set(CANONICAL_CI_PYTHON_VERSIONS):
        raise ValueError("Root v2 requires explicit core/live mode and only supported prepared interpreters")
    if any(type(value) is not int or not 1 <= value <= 14400 for value in (timeout_seconds, test_timeout_seconds)):
        raise ValueError("Root runtime/case deadlines must be finite positive integers")
    if timeout_seconds <= 660:
        raise ValueError("Root runtime whole budget must exceed its canonical 660-second collection allowance")
    resolved = RuntimeScope(root, "root")
    root = resolved.root
    admitted_root = _root_identity(root)
    identity = (admitted_root[0], admitted_root[1])
    run_id = uuid.uuid4().hex
    directory = evidence_directory(root, evidence_dir or root / "output/readiness" / f"root-v2-{run_id}", fresh=True)
    reader = SnapshotReader(root)
    policy, _, _, prerequisites = load_policy(reader)
    units = declared_units(policy, prerequisites)
    resolved.require_case_units(reader)
    fingerprint = resolved.source_identity()
    requirements, faults = required_profile(root, reader, fingerprint)
    if faults:
        raise ValueError("Root v2 required source/profile declarations are invalid or unavailable")
    lookup = {item.id: item for item in requirements}
    cells = [item for item in requirements if item.kind == "root-case"]
    policy_requirement, coverage_requirement = lookup["root:case-policy"], lookup["root:coverage"]
    gates: dict[str, Any] = {}
    summaries: list[dict[str, Any]] = []
    child_codes: list[int] = []
    policy_proof: tuple[dict[str, Any], list[str]] | None = None
    coverage_proof: tuple[dict[str, Any], list[str]] | None = None
    for minor in CANONICAL_CI_PYTHON_VERSIONS:
        cell_directory = directory / minor
        try:
            probe = _probe_runtime(
                root, cell_directory, minor, interpreters.get(minor), expected_root_identity=identity
            )
        except (OSError, ValueError, TypeError) as error:
            raise RuntimeError("original Root runtime probe refused after run admission") from error
        if type(probe.get("execution_exit_code")) is int:
            child_codes.append(probe["execution_exit_code"])
        status, original_code = probe["status"], probe.get("execution_exit_code", 75)
        command = probe["command"]
        observation = None
        bundle_artifact = None
        if status == "pass":
            try:
                if _root_identity(root) != admitted_root:
                    raise RuntimeError("original Root changed before runtime cohort launch")
                produced = produce_runtime_cohort(
                    root,
                    cell_directory / "cohort",
                    interpreter=probe["interpreter"],
                    runtime_probe=probe["runtime"],
                    mode=mode,
                    timeout_seconds=timeout_seconds,
                    test_timeout_seconds=test_timeout_seconds,
                )
                bundle_artifact = produced["bundle_artifact"]
                original_code = produced["bundle"]["exit_code"]
                child_codes.append(original_code)
                native = reader.read(produced["bundle"]["process_artifact"]["path"]).json_object()
                command = native["command"]
                status = "pass" if original_code == 0 else "blocked" if original_code == 75 else "fail"
                if status == "pass":
                    observation = read_selected_runtime(reader, bundle_artifact)
            except KeyboardInterrupt:
                status, original_code = "fail", 130
                child_codes.append(original_code)
            except TimeoutError:
                status, original_code = "fail", 124
                child_codes.append(original_code)
            except (OSError, ValueError, TypeError, KeyError, RuntimeError):
                status, original_code = "fail", 1
                child_codes.append(original_code)
        if observation is not None and bundle_artifact is not None:
            details = _details(probe, bundle_artifact, observation, policy.sha256)
            details["portable_root_artifact"] = produced["portable_artifact"]
            policy_proof = policy_proof or (details, command)
            if minor == coverage_requirement.python_version:
                coverage_proof = (
                    {
                        **details,
                        "coverage_artifact": observation["coverage_artifact"],
                        "branch_coverage": True,
                        "percent": observation["coverage"]["totals"]["percent_covered"],
                    },
                    command,
                )
        for index, requirement in enumerate(item for item in cells if item.python_version == minor):
            unit = next(unit for unit in units if unit.id == requirement.case_unit)
            reason = (
                "required applicable target platform unavailable"
                if requirement.case_platform != sys.platform
                else "explicit live mode required"
                if mode == "core" and unit.lane not in {"core", "offline-benchmark"}
                else ""
            )
            gate_directory = cell_directory / f"gate-{index:03d}"
            if reason or status == "blocked":
                why = reason or "selected interpreter or required execution prerequisite unavailable"
                gates[requirement.id] = _entry(
                    root,
                    gate_directory,
                    requirement,
                    fingerprint,
                    "blocked",
                    command,
                    {"python_version": minor, "execution_exit_code": 75, "diagnostic": why},
                    [{"tool": requirement.case_unit, "reason": why}],
                    identity=identity,
                )
                observed_state = "blocked"
            elif status != "pass" or observation is None or bundle_artifact is None:
                gates[requirement.id] = _entry(
                    root,
                    gate_directory,
                    requirement,
                    fingerprint,
                    "fail",
                    command,
                    {
                        "python_version": minor,
                        "execution_exit_code": original_code,
                        "diagnostic": "original prepared-runtime cohort or independent reader failed",
                    },
                    identity=identity,
                )
                observed_state = "fail"
            else:
                details = {
                    **_details(probe, bundle_artifact, observation, policy.sha256),
                    "collected": len(requirement.case_nodes),
                    "passed": len(requirement.case_nodes),
                    "failed": 0,
                    "errors": 0,
                    "skipped": 0,
                    "deselected": 0,
                    "test_files": list(requirement.test_files),
                }
                gates[requirement.id], observed_state, verification_code = _verified_gate(
                    root, gate_directory, requirement, fingerprint, command, details, identity
                )
                child_codes.append(verification_code)
                if verification_code in {124, 130}:
                    original_code = verification_code if original_code != 130 else 130
                    status = "fail"
            summaries.append({"gate": requirement.id, "status": observed_state})
        if original_code in {124, 130}:
            break
    # A stopped runtime never erases remaining supported targets or opt-in obligations.
    for requirement in cells:
        if requirement.id not in gates:
            gates[requirement.id] = _entry(
                root,
                directory / "unobserved" / str(len(gates)),
                requirement,
                fingerprint,
                "blocked",
                ["unobserved-required-root-runtime"],
                {"execution_exit_code": 75, "diagnostic": "Root runtime stopped before required cell"},
                [{"tool": requirement.id, "reason": "required cell remains unobserved"}],
                identity=identity,
            )
            summaries.append({"gate": requirement.id, "status": "blocked"})
    for requirement, proof in ((policy_requirement, policy_proof), (coverage_requirement, coverage_proof)):
        if proof is None or any(code in {124, 130} for code in child_codes):
            gates[requirement.id] = _entry(
                root,
                directory / requirement.kind,
                requirement,
                fingerprint,
                "blocked",
                ["unavailable-complete-root-cohort"],
                {"execution_exit_code": 75},
                [{"tool": requirement.id, "reason": "no successful original required Root cohort"}],
                identity=identity,
            )
            state = "blocked"
        else:
            details, command = proof
            gates[requirement.id], state, verification_code = _verified_gate(
                root, directory / requirement.kind, requirement, fingerprint, command, details, identity
            )
            child_codes.append(verification_code)
        summaries.append({"gate": requirement.id, "status": state})
    current = reader.unchanged() and resolved.source_identity() == fingerprint and _root_identity(root) == admitted_root
    counts = {
        state: sum(item["status"] == state for item in summaries) for state in ("pass", "fail", "blocked", "unknown")
    }
    matrix = {
        "run_id": run_id,
        "selection": "source-declared-root-v2-case-units",
        "mode": mode,
        "expected_cells": len(cells) + 2,
        "observed_cells": len(summaries),
        "source_current": current,
        "counts": counts,
        "results": summaries,
        "optional_external": optional_external_records(policy),
    }
    try:
        receipt = write_json(
            root,
            directory / "receipt.json",
            {
                "schema_version": SCHEMA_VERSION,
                "platform_version": requirements[0].platform_version,
                "source_fingerprint": fingerprint,
                "roster": list(PUBLIC_PROJECT_NAMES),
                "gates": gates,
                "root_matrix": matrix,
            },
            expected_root_identity=identity,
        )
    except (OSError, ValueError) as error:
        raise RuntimeError("original Root final receipt write refused after run admission") from error
    code = (
        130
        if 130 in child_codes
        else 124
        if 124 in child_codes
        else 1
        if not current or counts["fail"]
        else 75
        if counts["blocked"] or counts["unknown"]
        else 0
    )
    return {"receipt": receipt, "root_matrix": matrix, "exit_code": code}
