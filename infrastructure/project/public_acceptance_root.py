"""Source-bound root runtime cells; unresolved root case policy blocks execution."""

from __future__ import annotations

import argparse
import json
import tomllib
import uuid
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any, Mapping

from infrastructure.core.testing.project_test_matrix import ProjectTestTask, run_project_test_matrix
from infrastructure.project.public_acceptance import _entry, _probe_runtime, _record_cell
from infrastructure.project.public_acceptance_cli import interpreter, positive_int
from infrastructure.project.public_acceptance_evidence import (
    bootstrap_command,
    cell_environment,
    evidence_directory,
    write_json,
)
from infrastructure.project.public_acceptance_scope import MissingRootCasePolicy, RuntimeScope
from infrastructure.project.public_capabilities import CANONICAL_CI_PYTHON_VERSIONS
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.readiness_receipts import SCHEMA_VERSION, source_fingerprint
from infrastructure.reporting.release_readiness_profile import required_profile
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def run_root_acceptance(
    root: Path,
    interpreters: Mapping[str, Path],
    *,
    evidence_dir: Path | None = None,
    timeout_seconds: int = 7200,
    test_timeout_seconds: int = 120,
    mode: str = "core",
) -> dict[str, Any]:
    """Reuse original cell supervision serially, without altering the exemplar matrix."""
    if any(type(value) is not int or value <= 0 for value in (timeout_seconds, test_timeout_seconds)):
        raise ValueError("root cell/test deadlines must be finite positive integers")
    if set(interpreters) - set(CANONICAL_CI_PYTHON_VERSIONS):
        raise ValueError("root interpreter selection contains an unsupported runtime")
    if mode not in {"core", "live"}:
        raise ValueError("Root acceptance mode must be core or live")
    declared_reader = SnapshotReader(root.resolve(strict=True))
    metadata = tomllib.loads(declared_reader.read("pyproject.toml").content.decode())
    contract = metadata.get("tool", {}).get("template", {}).get("root_acceptance")
    if isinstance(contract, dict) and contract.get("schema_version") in {2, 3}:
        from infrastructure.project.public_root_case_acceptance import run_root_case_acceptance

        return run_root_case_acceptance(
            root,
            interpreters,
            evidence_dir=evidence_dir,
            mode=mode,
            timeout_seconds=timeout_seconds,
            test_timeout_seconds=test_timeout_seconds,
        )
    if mode != "core":
        raise ValueError("Root schema1 supports only its exact complete-offline execution contract")
    resolved = RuntimeScope(root, "root")
    root = resolved.root
    run_id = uuid.uuid4().hex
    directory = evidence_directory(root, evidence_dir or root / "output/readiness" / f"root-{run_id}", fresh=True)
    fingerprint = source_fingerprint(root)
    profile_reader = SnapshotReader(root)
    requirements, faults = required_profile(root, profile_reader, fingerprint)
    if faults:
        raise ValueError("source-owned required acceptance declarations are incomplete or invalid")
    lookup = {item.id: item for item in requirements}
    coverage = lookup["root:coverage"]
    policy_blocker = ""
    try:
        resolved.require_case_policy(profile_reader)
    except MissingRootCasePolicy as error:
        policy_blocker = str(error)
    gates: dict[str, Any] = {}
    summaries = []
    child_codes = []
    for minor in CANONICAL_CI_PYTHON_VERSIONS:
        cell_dir = directory / minor
        requirement = lookup[f"root:runtime:{minor}"]
        probe: dict[str, Any]
        if policy_blocker:
            probe = {
                "status": "blocked",
                "command": [],
                "diagnostic": policy_blocker,
                "blockers": [{"tool": "root case policy", "reason": policy_blocker}],
            }
        else:
            probe = _probe_runtime(root, directory, minor, interpreters.get(minor))
        if type(probe.get("execution_exit_code")) is int:
            child_codes.append(probe["execution_exit_code"])
        if probe["status"] != "pass":
            details = {"python_version": minor, "diagnostic": probe.get("diagnostic", "selected runtime unavailable")}
            details.update({key: probe[key] for key in ("execution_exit_code", "timed_out") if key in probe})
            if probe.get("binding") is not None:
                details["runtime_artifact"] = probe["binding"]
            gates[requirement.id] = _entry(
                root,
                cell_dir,
                requirement,
                fingerprint,
                probe["status"],
                probe["command"],
                details,
                probe.get("blockers"),
            )
            if minor == coverage.python_version:
                gates[coverage.id] = _entry(
                    root,
                    cell_dir,
                    coverage,
                    fingerprint,
                    probe["status"],
                    probe["command"],
                    details,
                    probe.get("blockers"),
                )
            summaries.append({"scope": "root", "status": probe["status"], **details})
            continue
        spec = {
            "root": str(root),
            "scope": "root",
            "directory": cell_dir.relative_to(root).as_posix(),
            "run_id": run_id,
            "runtime": probe["runtime"],
            "source_identity": requirement.source_identity,
            "deliverables_identity": requirement.deliverables_identity,
            "test_files": list(requirement.test_files),
            "timeout_seconds": timeout_seconds,
            "test_timeout_seconds": test_timeout_seconds,
            "dependency_providers": {},
        }
        binding = write_json(root, cell_dir / "spec.json", spec)
        command = bootstrap_command(
            probe["interpreter"],
            root,
            "infrastructure.project.public_acceptance_worker",
            "--root",
            str(root),
            "--spec",
            str(root / binding["path"]),
            "--spec-sha256",
            binding["sha256"],
        )
        task = ProjectTestTask(
            0,
            "root",
            command,
            root,
            cell_environment(probe["interpreter"], cell_dir, repo_root=root),
            timeout_seconds + 30,
            True,
        )
        observed = run_project_test_matrix([task], workers=1)[0]
        child_codes.append(observed.returncode)
        write_json(
            root,
            cell_dir / "cell-process.json",
            {
                **asdict(observed),
                "command": list(command),
                "run_id": run_id,
                "spec_artifact": binding,
            },
        )
        runtime_entry, coverage_entry, summary = _record_cell(
            root,
            cell_dir,
            requirement,
            replace(coverage, python_version=minor),
            fingerprint,
            command,
            observed.returncode,
            probe,
            run_id,
        )
        gates[requirement.id] = runtime_entry
        if minor == coverage.python_version:
            gates[coverage.id] = coverage_entry
        summaries.append(summary)
    current = profile_reader.unchanged() and source_fingerprint(root) == fingerprint
    counts = {
        state: sum(item["status"] == state for item in summaries) for state in ("pass", "fail", "blocked", "unknown")
    }
    expected = len(CANONICAL_CI_PYTHON_VERSIONS)
    matrix = {
        "run_id": run_id,
        "expected_cells": expected,
        "observed_cells": len(summaries),
        "source_current": current,
        "counts": counts,
        "results": summaries,
    }
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
    )
    exit_code = (
        130
        if 130 in child_codes
        else 124
        if 124 in child_codes
        else 0
        if current and counts["pass"] == expected
        else 75
        if current and not counts["fail"]
        else 1
    )
    return {"receipt": receipt, "root_matrix": matrix, "exit_code": exit_code}


def main(argv: list[str] | None = None) -> int:
    """Run prepared supported interpreters; policy/tool blockers are explicit."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--python", action="append", type=interpreter, default=[])
    parser.add_argument("--evidence-dir", type=Path)
    parser.add_argument("--timeout", type=positive_int, default=7200)
    parser.add_argument("--test-timeout", type=positive_int, default=120)
    parser.add_argument("--mode", choices=("core", "live"), default="core")
    args = parser.parse_args(argv)
    if len(dict(args.python)) != len(args.python):
        parser.error("each root runtime may select only one prepared interpreter")
    try:
        result = run_root_acceptance(
            args.repo_root,
            dict(args.python),
            evidence_dir=args.evidence_dir,
            timeout_seconds=args.timeout,
            test_timeout_seconds=args.test_timeout,
            mode=args.mode,
        )
    except RuntimeError:
        return 1
    except MissingRootCasePolicy:
        print(json.dumps({"exit_code": 75, "diagnostic": "required source-owned Root case policy is unavailable"}))
        return 75
    except OSError, ValueError, TypeError, KeyError:
        parser.error("Root acceptance source-owned invocation/configuration is invalid")
    print(json.dumps(result, indent=2, sort_keys=True))
    return int(result["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
