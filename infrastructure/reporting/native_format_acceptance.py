"""Supervised fresh native rendering; incomplete visual acceptance stays blocked."""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Sequence

from infrastructure.core.execution_boundary import run_bounded_subprocess
from infrastructure.project.public_acceptance_cli import positive_int
from infrastructure.project.public_acceptance_evidence import (
    bootstrap_command,
    evidence_directory,
    gate_payload,
    read_json,
    write_json,
)
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.native_format_acceptance_contracts import (
    NATIVE_SCHEMA,
    PROCESS_SCHEMA,
    WORKER_MODULE,
    native_environment,
    public_source_digest,
    create_private_native_directory,
    native_deadline_guard,
    NativeDeadlineExpired,
    NativeDeadlineUnavailable,
)
from infrastructure.reporting.native_format_acceptance_validation import (
    validate_native_acceptance,
    validate_native_conformance,
)
from infrastructure.reporting.readiness_receipts import SCHEMA_VERSION, source_fingerprint
from infrastructure.reporting.release_readiness_profile import required_profile
from infrastructure.reporting.release_readiness_profile import Requirement
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def _finalize_profile(root: Path, before: str) -> tuple[bool, str, tuple[Requirement, ...]]:
    """Derive final identities only after actual regeneration has settled."""
    current = public_source_digest(root) == before
    fingerprint = source_fingerprint(root)
    requirements, faults = required_profile(root, SnapshotReader(root), fingerprint)
    if faults:
        raise ValueError("final source-owned readiness metadata is invalid or incomplete")
    return current, fingerprint, requirements


def _executed_failure_exit(codes: list[int]) -> int:
    """Post-execution finalization failures preserve stronger actual outcomes."""
    return 130 if 130 in codes else 124 if 124 in codes else 1


def _run_native_format_acceptance(
    root: Path,
    *,
    projects: Sequence[str] | None = None,
    timeout_seconds: int = 14400,
    evidence_dir: Path | None = None,
    epubcheck_jar: Path | None = None,
    java_executable: Path | None = None,
    _state: dict[str, Any],
) -> dict[str, Any]:
    """Run fresh whole-core project plans serially under one admission deadline.

    The generated partial receipt owns only format gates. It neither merges
    old evidence nor grants runtime, domain, installed-package or publication
    acceptance. Pure source is frozen before execution; mutable deliverables
    enter the final readiness fingerprint only after regeneration settles.
    """
    started = _state["started"]
    try:
        valid_timeout = type(timeout_seconds) is int and timeout_seconds > 0 and math.isfinite(timeout_seconds)
    except OverflowError:
        valid_timeout = False
    if not valid_timeout:
        raise ValueError("native acceptance requires a positive finite whole-run timeout")
    root = root.resolve()
    selected = tuple(projects) if projects is not None else PUBLIC_PROJECT_NAMES
    if (
        not selected
        or len(set(selected)) != len(selected)
        or any(scope not in PUBLIC_PROJECT_NAMES for scope in selected)
    ):
        raise ValueError("native acceptance requires unique canonical public project names")
    if (epubcheck_jar is None) != (java_executable is None):
        raise ValueError("native EPUB tools require both the reviewed JAR and actual Java executable")
    for tool in (epubcheck_jar, java_executable):
        if tool is not None and (not isinstance(tool, Path) or not tool.is_absolute() or ".." in tool.parts):
            raise ValueError("native EPUB tools require explicit absolute paths without traversal")
    run_id = uuid.uuid4().hex
    directory = evidence_directory(root, evidence_dir or root / "output/readiness" / f"native-{run_id}", fresh=True)
    observer_tools: dict[str, str | None] = {
        "epubcheck_jar": str(epubcheck_jar) if epubcheck_jar else None,
        "java_executable": str(java_executable) if java_executable else None,
        "frozen_epub_engine": None,
    }
    if epubcheck_jar is not None and java_executable is not None:
        from infrastructure.reporting.native_epub_observer import bind_epubcheck_engine, freeze_epubcheck_bundle

        engine = bind_epubcheck_engine(epubcheck_jar, java_executable, deadline=started + timeout_seconds)
        frozen = freeze_epubcheck_bundle(root, directory, engine, deadline=started + timeout_seconds)
        observer_tools["frozen_epub_engine"] = frozen.parent.relative_to(root).as_posix()
    before = public_source_digest(root)
    deadline = started + timeout_seconds
    initial_fingerprint = source_fingerprint(root)
    requirements, faults = required_profile(root, SnapshotReader(root), initial_fingerprint)
    if faults:
        raise ValueError("source-owned readiness metadata is invalid or incomplete")
    lookup = {item.scope: item for item in requirements if item.kind == "formats"}
    if set(selected) - set(lookup):
        raise ValueError("selected projects lack declared native format requirements")
    admitted: list[dict[str, Any]] = _state["admitted"]
    _state.update(
        root=root,
        directory=directory,
        before=before,
        fingerprint=initial_fingerprint,
        deadline=deadline,
        run_id=run_id,
        selected=selected,
        platform_version=requirements[0].platform_version,
    )
    for scope in selected:
        cell = directory / scope
        # Native inputs and local transcripts are private until explicitly
        # selected for a separate reviewed publication operation.
        create_private_native_directory(root, cell)
        spec = {
            "scope": scope,
            "run_id": run_id,
            "directory": cell.relative_to(root).as_posix(),
            "formats": list(lookup[scope].formats),
            "source_digest": before,
            "timeout_seconds": timeout_seconds,
            "deadline_monotonic": deadline,
            "observer_tools": observer_tools,
        }
        specification = write_json(root, cell / "spec.json", spec)
        command = list(
            bootstrap_command(
                Path(sys.executable), root, WORKER_MODULE, "--root", str(root), "--spec", str(cell / "spec.json")
            )
        )
        remaining = deadline - time.monotonic()
        observation: dict[str, Any] = {
            "schema_version": PROCESS_SCHEMA,
            "run_id": run_id,
            "command": command,
            "exit_code": 124,
            "original_exit_code": None,
            "timed_out": True,
            "custody_refused": False,
            "diagnostic": "whole native deadline expired before worker launch",
        }
        item: dict[str, Any] = {
            "scope": scope,
            "directory": cell,
            "command": command,
            "process": None,
            "observation": observation,
            "specification": specification,
            "raw_binding": None,
            "raw": {},
        }
        admitted.append(item)
        _state["executed"] = True
        if remaining > 0:
            observation.update(
                exit_code=1, timed_out=False, diagnostic="native attempt did not return an observed outcome"
            )
            try:
                result = run_bounded_subprocess(
                    command, cwd=root, env=native_environment(root, Path(sys.executable), cell), timeout=remaining
                )
                observation.update(
                    exit_code=result.returncode,
                    original_exit_code=result.original_returncode,
                    timed_out=result.timed_out,
                    custody_refused=result.custody_refused,
                    diagnostic=result.command_error,
                    stdout=result.stdout[-12000:],
                    stderr=result.stderr[-12000:],
                )
            except KeyboardInterrupt:
                observation.update(
                    exit_code=130, original_exit_code=None, timed_out=False, diagnostic="native supervisor interrupted"
                )
        process = write_json(root, cell / "process.json", observation)
        item["process"] = process
        raw_binding: dict[str, str] | None = None
        raw: dict[str, Any] = {}
        try:
            raw = read_json(root, cell / "native-execution.json")
            snapshot = SnapshotReader(root).read((cell / "native-execution.json").relative_to(root).as_posix())
            raw_binding = {"path": snapshot.relative, "sha256": snapshot.sha256}
        except (OSError, ValueError):
            pass
        item.update(raw_binding=raw_binding, raw=raw)
        if observation["exit_code"] in {124, 130}:
            break
    try:
        current, fingerprint, final_requirements = _finalize_profile(root, before)
    except (OSError, ValueError, TypeError, KeyError) as error:
        # After launch, failed source custody/finalization is executed failure.
        # Preserve original interruption/timeout precedence and private attempts;
        # parser.error(2) is exclusively a pre-execution configuration result.
        codes = [item["observation"]["exit_code"] for item in admitted]
        code = _executed_failure_exit(codes)
        summary = {
            "run_id": run_id,
            "source_digest": before,
            "source_current": False,
            "complete_selection": selected == PUBLIC_PROJECT_NAMES,
            "selected_projects": list(selected),
            "observed_projects": len(admitted),
            "diagnostic": str(error),
            "results": [
                {
                    "project": item["scope"],
                    "status": "fail",
                    "execution_exit_code": item["observation"]["exit_code"],
                    "process_artifact": item["process"],
                    "native_execution_artifact": item["raw_binding"],
                }
                for item in admitted
            ],
        }
        payload = {
            "schema_version": SCHEMA_VERSION,
            "platform_version": requirements[0].platform_version,
            "source_fingerprint": initial_fingerprint,
            "roster": list(PUBLIC_PROJECT_NAMES),
            "gates": {},
            "native_formats": summary,
        }
        binding = write_json(root, directory / "receipt.json", payload)
        return {"receipt": binding, "native_formats": summary, "exit_code": code}
    final_lookup = {item.scope: item for item in final_requirements if item.kind == "formats"}
    gates: dict[str, Any] = {}
    summaries = []
    for item in admitted:
        scope, raw, observed = item["scope"], item["raw"], item["observation"]
        requirement = final_lookup[scope]
        details = {
            "schema_version": NATIVE_SCHEMA,
            "run_id": run_id,
            "execution_exit_code": observed["exit_code"],
            "specification_artifact": item["specification"],
            "process_artifact": item["process"],
            "native_execution_artifact": item["raw_binding"],
            "formats": raw.get("formats", {}),
            "conformance_validated": False,
            "diagnostic": raw.get("diagnostic") or observed.get("diagnostic", ""),
        }
        status, blockers = "fail", []
        matching = (
            current
            and raw.get("schema_version") == NATIVE_SCHEMA
            and raw.get("scope") == scope
            and raw.get("run_id") == run_id
            and raw.get("source_digest_before") == before
            and raw.get("source_digest_after") == before
            and raw.get("execution_exit_code") == observed["exit_code"]
            and (
                not raw.get("pipeline")
                or raw.get("deliverables_identity_after") in {"", requirement.deliverables_identity}
            )
            and observed["original_exit_code"] == observed["exit_code"]
            and not observed["timed_out"]
            and not observed["custody_refused"]
        )
        if matching and raw.get("status") == "blocked" and observed["exit_code"] == 75:
            declared = raw.get("blockers")
            if (
                isinstance(declared, list)
                and declared
                and all(
                    isinstance(row, dict)
                    and isinstance(row.get("tool"), str)
                    and row["tool"]
                    and isinstance(row.get("reason"), str)
                    and row["reason"]
                    for row in declared
                )
            ):
                status, blockers = "blocked", declared
        if current and observed["custody_refused"] and observed["exit_code"] == 75:
            status, blockers = "blocked", [{"tool": "native process guardian", "reason": observed["diagnostic"]}]
        if matching and raw.get("status") in {"pass", "blocked"}:
            try:
                reader = SnapshotReader(root)
                validate_native_conformance(requirement, details, reader)
                details["conformance_validated"] = True
                if raw["status"] == "pass":
                    validate_native_acceptance(requirement, details, reader)
                    status = "pass"
            except (OSError, ValueError, TypeError, KeyError) as error:
                details["diagnostic"] = str(error)
                if raw["status"] == "pass":
                    status = "fail"
        binding = write_json(
            root,
            item["directory"] / "formats-gate.json",
            gate_payload(requirement, fingerprint, status, details, blockers),
        )
        gates[requirement.id] = {
            "status": status,
            "command": item["command"],
            "artifact": binding["path"],
            "artifact_sha256": binding["sha256"],
        }
        summaries.append(
            {
                "project": scope,
                "status": status,
                "execution_exit_code": observed["exit_code"],
                "conformance_validated": details["conformance_validated"],
                "diagnostic": details["diagnostic"],
                "blockers": blockers,
            }
        )
    codes = [item["observation"]["exit_code"] for item in admitted]
    states = [item["status"] for item in summaries]
    exit_code = (
        130
        if 130 in codes
        else 124
        if 124 in codes or time.monotonic() >= deadline
        else 1
        if not current or "fail" in states or len(admitted) != len(selected)
        else 75
        if "blocked" in states
        else 0
    )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "platform_version": final_requirements[0].platform_version,
        "source_fingerprint": fingerprint,
        "roster": list(PUBLIC_PROJECT_NAMES),
        "gates": gates,
        "native_formats": {
            "run_id": run_id,
            "source_digest": before,
            "source_current": current,
            "complete_selection": selected == PUBLIC_PROJECT_NAMES,
            "selected_projects": list(selected),
            "observed_projects": len(admitted),
            "results": summaries,
        },
    }
    binding = write_json(root, directory / "receipt.json", payload)
    return {"receipt": binding, "native_formats": payload["native_formats"], "exit_code": exit_code}


def _executed_failure_result(state: dict[str, Any], error: BaseException) -> dict[str, Any]:
    """Preserve attempts even when every subsequent confined write refuses."""
    codes = [item["observation"]["exit_code"] for item in state["admitted"]]
    if isinstance(error, KeyboardInterrupt):
        codes.append(130)
    if isinstance(error, (TimeoutError, NativeDeadlineExpired)) or time.monotonic() >= state["deadline"]:
        codes.append(124)
    summary = {
        "run_id": state["run_id"],
        "source_digest": state["before"],
        "source_current": False,
        "complete_selection": state["selected"] == PUBLIC_PROJECT_NAMES,
        "selected_projects": list(state["selected"]),
        "observed_projects": len(state["admitted"]),
        "diagnostic": str(error),
        "results": [
            {
                "project": item["scope"],
                "status": "fail",
                "observation": item["observation"],
                "process_artifact": item["process"],
                "native_execution_artifact": item["raw_binding"],
            }
            for item in state["admitted"]
        ],
    }
    payload = {
        "schema_version": SCHEMA_VERSION,
        "platform_version": state["platform_version"],
        "source_fingerprint": state["fingerprint"],
        "roster": list(PUBLIC_PROJECT_NAMES),
        "gates": {},
        "native_formats": summary,
    }
    binding = None
    try:
        if time.monotonic() < state["deadline"]:
            with native_deadline_guard(state["deadline"]):
                binding = write_json(state["root"], state["directory"] / "receipt.json", payload)
    except NativeDeadlineExpired as persistence_error:
        summary["persistence_diagnostic"] = str(persistence_error)
        codes.append(124)
    except Exception as persistence_error:  # noqa: BLE001 - original outcomes survive failed evidence persistence
        summary["persistence_diagnostic"] = str(persistence_error)
    if time.monotonic() >= state["deadline"]:
        codes.append(124)
    return {"receipt": binding, "native_formats": summary, "exit_code": _executed_failure_exit(codes)}


def run_native_format_acceptance(
    root: Path,
    *,
    projects: Sequence[str] | None = None,
    timeout_seconds: int = 14400,
    evidence_dir: Path | None = None,
    epubcheck_jar: Path | None = None,
    java_executable: Path | None = None,
) -> dict[str, Any]:
    """Keep invocation faults separate from the entire actual executed phase."""
    try:
        valid_timeout = type(timeout_seconds) is int and timeout_seconds > 0 and math.isfinite(timeout_seconds)
    except OverflowError:
        valid_timeout = False
    if not valid_timeout:
        raise ValueError("native acceptance requires a positive finite whole-run timeout")
    started = time.monotonic()
    state: dict[str, Any] = {
        "executed": False,
        "admitted": [],
        "started": started,
        "deadline": started + timeout_seconds,
    }
    try:
        with native_deadline_guard(state["deadline"]):
            result = _run_native_format_acceptance(
                root,
                projects=projects,
                timeout_seconds=timeout_seconds,
                evidence_dir=evidence_dir,
                epubcheck_jar=epubcheck_jar,
                java_executable=java_executable,
                _state=state,
            )
        if result["exit_code"] != 130 and time.monotonic() >= state["deadline"]:
            return _executed_failure_result(
                state, NativeDeadlineExpired("original native deadline expired during finalization")
            )
        return result
    except NativeDeadlineUnavailable as error:
        return {
            "receipt": None,
            "native_formats": {
                "diagnostic": str(error),
                "blockers": [{"tool": "POSIX main-thread real-time deadline", "reason": str(error)}],
            },
            "exit_code": 75,
        }
    except NativeDeadlineExpired as error:
        if not state["executed"]:
            return {
                "receipt": None,
                "native_formats": {"diagnostic": str(error), "observed_projects": 0, "results": []},
                "exit_code": 124,
            }
        return _executed_failure_result(state, error)
    except KeyboardInterrupt as error:
        if not state["executed"]:
            raise
        return _executed_failure_result(state, error)
    except Exception as error:  # noqa: BLE001 - every unexpected post-launch failure is an executed outcome
        if not state["executed"]:
            raise
        return _executed_failure_result(state, error)


def main(argv: list[str] | None = None) -> int:
    """Run the public native producer without dependency acquisition or publication."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).absolute().parents[2])
    parser.add_argument("--project", action="append", choices=PUBLIC_PROJECT_NAMES)
    parser.add_argument(
        "--timeout", type=positive_int, default=14400, help="Whole admission/execution/observer budget in seconds"
    )
    parser.add_argument("--evidence-dir", type=Path)
    parser.add_argument("--epubcheck-jar", type=Path)
    parser.add_argument("--java-executable", type=Path)
    args = parser.parse_args(argv)
    try:
        result = run_native_format_acceptance(
            args.repo_root,
            projects=args.project,
            timeout_seconds=args.timeout,
            evidence_dir=args.evidence_dir,
            epubcheck_jar=args.epubcheck_jar,
            java_executable=args.java_executable,
        )
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2, sort_keys=True))
    return int(result["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
