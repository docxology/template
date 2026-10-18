"""Source-bound supervision for genuine auxiliary acceptance producers."""

from __future__ import annotations

import hashlib
import json
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Sequence

from infrastructure.project.public_acceptance_evidence import (
    evidence_directory,
    gate_payload,
    read_json,
    write_json,
)
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.project.public_acceptance_auxiliary_parallel import (
    AuxiliaryDeadlineExceeded,
    AuxiliaryOperation,
    AuxiliaryProcess,
    execute_auxiliary_operations,
)
from infrastructure.project.public_acceptance_auxiliary_validation import (
    validate_sandbox_transfer,
)
from infrastructure.reporting.readiness_receipts import SCHEMA_VERSION, source_fingerprint
from infrastructure.reporting.release_readiness_profile import Requirement, required_profile
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.reporting.release_readiness_validators import validate_acceptance

from infrastructure.project.public_acceptance_auxiliary_supervision import (
    PROCESS_SCHEMA as PROCESS_SCHEMA,
    complete_auxiliary_observation,
    supervise as supervise,
)

ROOT_GATES = (
    "root:roster",
    "root:docs_lint",
    "root:methods",
    "root:macos:process",
    "root:macos:rendering",
    "root:sandbox:transfer",
)


def _auxiliary_gate_operation(
    root: Path,
    requirement: Requirement,
    index: int,
    directory: Path,
    python: Path,
    deadline: float,
    fingerprint: str,
    producer_inputs: dict[str, dict[str, Any]] | None,
) -> AuxiliaryOperation:
    """Prepare and admit one genuine gate entirely on the controller thread."""
    gate = requirement.id
    cell = directory / f"{index:03d}"
    status, details, blockers = "blocked", {}, []
    if gate == "root:sandbox:transfer":
        blockers = [
            {
                "tool": "authorized remote sandbox",
                "reason": "select exact provider, sandbox destination and existing authorization; "
                "independently retrieve the admitted Root export",
            }
        ]
    elif not python.is_file():
        blockers = [
            {
                "tool": "selected installed interpreter",
                "reason": "explicit executable is unavailable; acquisition is disabled",
            }
        ]
    elif time.monotonic() >= deadline:
        blockers = [{"tool": "auxiliary deadline", "reason": "whole-run deadline exhausted before child launch"}]
    else:
        before = source_fingerprint(root)
        raw_path = cell / "facts.json"
        spec = write_json(
            root,
            cell / "spec.json",
            {
                "gate": gate,
                "budget": max(1, int(deadline - time.monotonic())),
                "raw_path": raw_path.relative_to(root).as_posix(),
                "producer_inputs": (producer_inputs or {}).get(requirement.scope, {}),
                **(
                    {
                        "run_id": uuid.uuid4().hex,
                        "operation_deadline": deadline,
                        "parent_pid": __import__("os").getpid(),
                    }
                    if gate == "root:macos:rendering"
                    else {}
                ),
            },
        )
        from infrastructure.project.public_acceptance_auxiliary_bootstrap import (
            WORKER,
            prepare_audited_auxiliary_command,
        )

        command, payload = prepare_audited_auxiliary_command(
            python, root, WORKER, ("--spec", str(root / spec["path"])), cell / "execution"
        )
        print_originals: list[Any] = []
        process = yield AuxiliaryProcess(command, root, cell / "execution", deadline, payload, print_originals)
        after = source_fingerprint(root)
        raw = read_json(root, raw_path) if raw_path.is_file() else {}
        raw_binding = (
            {
                "path": raw_path.relative_to(root).as_posix(),
                "sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
            }
            if raw
            else None
        )
        process.update(
            gate=gate,
            source_fingerprint=fingerprint,
            source_before=before,
            source_after=after,
            raw_artifact=raw_binding,
            spec_artifact=spec,
        )
        binding = write_json(root, cell / "process.json", process)
        details = {
            **raw.get("details", {}),
            "command": command,
            "process_artifact": binding,
            "raw_artifact": raw_binding,
            "execution_exit_code": process["exit_code"],
        }
        status = (
            "pass"
            if process["exit_code"] == 0 and raw.get("status") == "pass"
            else "blocked"
            if process["exit_code"] == 75
            else "fail"
        )
        if (
            not complete_auxiliary_observation(process)
            or process["timed_out"]
            or process["output_limit_exceeded"]
            or before != fingerprint
            or after != fingerprint
            or raw.get("exit_code") != process["exit_code"]
        ):
            status = "fail"
        if status == "blocked":
            blockers = [{"tool": gate, "reason": raw.get("diagnostic", "actual auxiliary provider unavailable")}]
        if status == "fail":
            details["original_failure"] = {
                "diagnostic": raw.get("diagnostic", "actual auxiliary child failed before raw facts"),
                "failure_class": raw.get("failure_class"),
                "original_pipeline_failure": raw.get("original_pipeline_failure"),
                "original_exit_code": process["exit_code"],
                "timed_out": process["timed_out"],
            }
        if (
            status == "pass"
            and requirement.kind in {"docs", "oracle", "platform", "domain", "live"}
            and not details.get("negative_controls")
        ):
            negative = write_json(
                root,
                cell / "negative-spec.json",
                {
                    "gate": gate,
                    "negative": True,
                    "budget": 10,
                    "raw_path": (cell / "negative-facts.json").relative_to(root).as_posix(),
                },
            )
            negative_command, negative_payload = prepare_audited_auxiliary_command(
                python, root, WORKER, ("--spec", str(root / negative["path"])), cell / "negative-execution"
            )
            negative_process = yield AuxiliaryProcess(
                negative_command, root, cell / "negative-execution", deadline, negative_payload
            )
            facts_path = cell / "negative-facts.json"
            facts = read_json(root, facts_path) if facts_path.is_file() else {}
            control = write_json(
                root,
                cell / "negative.json",
                {
                    **negative_process,
                    "gate": gate,
                    "source_fingerprint": fingerprint,
                    "spec_artifact": negative,
                    "raw_artifact": {
                        "path": facts_path.relative_to(root).as_posix(),
                        "sha256": hashlib.sha256(facts_path.read_bytes()).hexdigest(),
                    }
                    if facts
                    else None,
                    "raw_facts": facts,
                },
            )
            if (
                not complete_auxiliary_observation(negative_process)
                or negative_process["exit_code"] != 23
                or facts.get("exit_code") != 23
                or negative_process["timed_out"]
            ):
                status = "fail"
            details["negative_controls"] = [
                {
                    "name": f"{gate}:invalid-input",
                    "expected_exit_code": 23,
                    "observed_exit_code": negative_process["exit_code"],
                    "artifact": control,
                }
            ]
        if status == "pass":
            try:
                from infrastructure.reporting.native_auxiliary_print_custody import AuxiliaryPrintReaderOperation

                print_operation = (
                    AuxiliaryPrintReaderOperation(print_originals[0], root, deadline)
                    if gate == "root:macos:rendering" and len(print_originals) == 1
                    else None
                )
                validate_acceptance(
                    requirement,
                    gate_payload(requirement, fingerprint, status, details, []),
                    SnapshotReader(root, operation_deadline=deadline, native_control_operation=print_operation),
                )
            except (OSError, ValueError, TypeError, KeyError, TimeoutError) as error:
                status = "fail"
                details["diagnostic"] = str(error)
    payload = gate_payload(requirement, fingerprint, status, details, blockers)
    bound = write_json(root, cell / "gate.json", payload)
    return gate, {
        "status": status,
        "command": details.get("command", ["auxiliary-preflight", gate]),
        "artifact": bound["path"],
        "artifact_sha256": bound["sha256"],
    }


def run_auxiliary_acceptance(
    root: Path,
    *,
    gates: Sequence[str] | None = None,
    timeout_seconds: int = 600,
    evidence_dir: Path | None = None,
    interpreter: Path | None = None,
    producer_inputs: dict[str, dict[str, Any]] | None = None,
    workers: int = 1,
) -> dict[str, Any]:
    """Run a complete bounded selection with serial Source admission per scope."""
    if type(workers) is not int or workers not in (1, 2, 3):
        raise ValueError("auxiliary workers must be one, two or three")
    if type(timeout_seconds) is not int or timeout_seconds <= 0:
        raise ValueError("auxiliary deadline must be a positive integer")
    deadline = time.monotonic() + timeout_seconds
    root = root.resolve(strict=True)
    fingerprint = source_fingerprint(root)
    requirements, faults = required_profile(root, SnapshotReader(root), fingerprint)
    if faults:
        raise ValueError("source-owned auxiliary profile is invalid")
    available = {
        req.id: req
        for req in requirements
        if req.kind in {"roster", "docs", "oracle", "platform", "transfer", "pipeline", "domain", "live"}
    }
    selection = tuple(ROOT_GATES if gates is None else gates)
    if not selection or len(set(selection)) != len(selection) or set(selection) - set(available):
        raise ValueError("auxiliary selection must contain unique declared gate IDs")
    directory = evidence_directory(
        root, evidence_dir or root / "output/readiness" / f"auxiliary-{uuid.uuid4().hex}", fresh=True
    )
    python = (interpreter or Path(sys.executable)).absolute()
    operations = [
        (
            available[gate].scope,
            _auxiliary_gate_operation(
                root, available[gate], index, directory, python, deadline, fingerprint, producer_inputs
            ),
        )
        for index, gate in enumerate(selection)
    ]
    batches = (
        [operations]
        if workers == 1
        else [
            [item for item in operations if item[0] == "root"],
            [item for item in operations if item[0] != "root"],
        ]
    )
    observed = []
    interrupted: dict[int, list[dict[str, Any]]] = {}
    original_indices = {id(operation): index for index, (_, operation) in enumerate(operations)}
    for batch in batches:
        try:
            observed += execute_auxiliary_operations(
                batch, workers=1 if batch is batches[0] else workers, deadline=deadline
            )
        except AuxiliaryDeadlineExceeded as error:
            observed += error.results
            interrupted = {
                original_indices[id(batch[index][1])]: children for index, children in error.observations.items()
            }
            break
    by_gate = dict(observed)
    for index, gate in enumerate(selection):
        if gate in by_gate:
            continue
        cell = directory / f"{index:03d}"
        children = [
            write_json(root, cell / f"interrupted-process-{ordinal}.json", child)
            for ordinal, child in enumerate(interrupted.get(index, []))
        ]
        bound = write_json(
            root,
            cell / "gate.json",
            gate_payload(
                available[gate],
                fingerprint,
                "fail",
                {
                    "diagnostic": "original auxiliary deadline exhausted before complete gate admission",
                    "original_process_artifacts": children,
                },
                [],
            ),
        )
        by_gate[gate] = {
            "status": "fail",
            "command": ["auxiliary-deadline", gate],
            "artifact": bound["path"],
            "artifact_sha256": bound["sha256"],
        }
    output = {gate: by_gate[gate] for gate in selection}
    current = source_fingerprint(root) == fingerprint
    expired = time.monotonic() >= deadline
    report = {
        "schema_version": SCHEMA_VERSION,
        "platform_version": requirements[0].platform_version,
        "source_fingerprint": fingerprint,
        "roster": list(PUBLIC_PROJECT_NAMES),
        "gates": output,
        "source_current": current,
        "auxiliary_workers": workers,
        "deadline_exhausted": expired,
        "exit_code": 1
        if expired or not current or any(item["status"] == "fail" for item in output.values())
        else 75
        if any(item["status"] == "blocked" for item in output.values())
        else 0,
    }
    receipt = write_json(root, directory / "receipt.json", report)
    if time.monotonic() >= deadline and not report["deadline_exhausted"]:
        # Retention may finish late, but it can retain only a failed outcome.
        # Same-run collection occurs after this producer's actual job outcome.
        report.update(deadline_exhausted=True, exit_code=1)
        receipt = write_json(root, directory / "receipt.json", report)
    return {**report, "receipt": receipt}


def admitted_root_export(root: Path, receipt_path: Path, reader: SnapshotReader | None = None) -> dict[str, str]:
    """Discover only Root ZIP bytes independently admitted against current source."""
    reader = reader or SnapshotReader(root)
    fingerprint = source_fingerprint(root)
    profile, faults = required_profile(root, reader, fingerprint)
    if faults:
        raise ValueError("Root export profile is invalid")
    requirement = next(item for item in profile if item.id == "root:export")
    receipt = reader.read(receipt_path.relative_to(root).as_posix()).json_object()
    entry = receipt["gates"]["root:export"]
    snapshot = reader.read(entry["artifact"])
    payload = snapshot.json_object()
    expected = gate_payload(requirement, fingerprint, "pass", payload.get("details", {}), [])
    if (
        entry.get("status") != "pass"
        or entry.get("artifact_sha256") != snapshot.sha256
        or any(payload.get(key) != value for key, value in expected.items() if key != "details")
    ):
        raise ValueError("Root export receipt is stale or not source-bound passing evidence")
    validate_acceptance(requirement, payload, reader)
    return dict(payload["details"]["bundle_artifact"])


def run_sandbox_transfer(
    root: Path,
    *,
    export_receipt: Path,
    upload_outputs: Path,
    downloaded_directory: Path,
    repository: str,
    run_id: str,
    source_commit: str,
    evidence_dir: Path,
    timeout_seconds: int = 60,
) -> dict[str, Any]:
    """Admit actual official upload/API facts and independently retrieved Root bytes."""
    import re

    if (
        re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) is None
        or re.fullmatch(r"[1-9][0-9]*", run_id) is None
        or re.fullmatch(r"[0-9a-f]{40}", source_commit) is None
    ):
        raise ValueError("sandbox transfer requires an exact repository, run ID and source commit")
    root = root.resolve(strict=True)
    reader = SnapshotReader(root)
    export = admitted_root_export(root, export_receipt.absolute(), reader)
    upload_snapshot = reader.read(upload_outputs.absolute().relative_to(root).as_posix())
    outputs = upload_snapshot.json_object()
    if set(outputs) != {"artifact-id", "artifact-digest", "artifact-url"}:
        raise ValueError("sandbox transfer requires original official upload outputs")
    artifact_id = outputs["artifact-id"]
    if not isinstance(artifact_id, str) or re.fullmatch(r"[1-9][0-9]*", artifact_id) is None:
        raise ValueError("official upload omitted its exact artifact ID")
    if outputs["artifact-url"] != f"https://github.com/{repository}/actions/runs/{run_id}/artifacts/{artifact_id}":
        raise ValueError("official uploaded artifact URL belongs to another repository/run/artifact")
    directory = evidence_directory(root, evidence_dir, fresh=True)
    fingerprint = source_fingerprint(root)
    deadline = time.monotonic() + timeout_seconds
    import shutil

    gh = shutil.which("gh")
    if gh is None:
        raise ValueError("actual scoped artifact API read requires existing gh CLI")
    observations = {}
    git = shutil.which("git")
    if git is None:
        raise ValueError("actual source commit observation requires existing git")
    revision_process = supervise([git, "rev-parse", "HEAD"], root, directory / "revision", deadline)
    revision_bytes = reader.read(revision_process["streams"]["stdout"]["path"]).content
    if (
        not complete_auxiliary_observation(revision_process)
        or revision_process["exit_code"] != 0
        or revision_bytes.decode().strip() != source_commit
    ):
        raise ValueError("actual checkout commit differs from nominated same-run source SHA")
    for label, endpoint in (
        ("artifact", f"repos/{repository}/actions/artifacts/{artifact_id}"),
        ("repository", f"repos/{repository}"),
    ):
        process = supervise([gh, "api", "--hostname", "github.com", endpoint], root, directory / label, deadline)
        if not complete_auxiliary_observation(process) or process["exit_code"] != 0:
            raise ValueError("actual scoped GitHub artifact API read failed")
        data = json.loads(reader.read(process["streams"]["stdout"]["path"]).content)
        observations[label] = {"data": data, "process": write_json(root, directory / f"{label}-process.json", process)}
    metadata = observations["artifact"]["data"]
    repo = observations["repository"]["data"]
    workflow = metadata.get("workflow_run", {})
    if (
        metadata.get("id") != int(artifact_id)
        or metadata.get("name") != "root-candidate-export"
        or metadata.get("expired") is not False
        or workflow.get("id") != int(run_id)
        or workflow.get("head_sha") != source_commit
        or repo.get("full_name") != repository
        or workflow.get("repository_id") != repo.get("id")
        or workflow.get("head_repository_id") != repo.get("id")
        or metadata.get("digest") != "sha256:" + outputs["artifact-digest"]
    ):
        raise ValueError("actual upload metadata differs from the exact repository/run/source/artifact digest")
    downloaded = evidence_directory(root, downloaded_directory.absolute())
    retrieved_path = downloaded / Path(export["path"]).name
    if sorted(path.relative_to(downloaded).as_posix() for path in downloaded.rglob("*") if path.is_file()) != [
        retrieved_path.name
    ]:
        raise ValueError("official download must contain exactly the admitted Root ZIP")
    retrieved = reader.read(retrieved_path.relative_to(root).as_posix())
    if retrieved.sha256 != export["sha256"] or source_fingerprint(root) != fingerprint:
        raise ValueError("retrieved Root export differs or source changed during remote observation")
    raw = write_json(
        root,
        directory / "transfer-facts.json",
        {
            "schema_version": "template-github-sandbox-transfer-v1",
            "repository": repository,
            "run_id": run_id,
            "source_commit": source_commit,
            "upload_outputs": outputs,
            "upload_outputs_artifact": {"path": upload_snapshot.relative, "sha256": upload_snapshot.sha256},
            "checkout_process": write_json(root, directory / "checkout-process.json", revision_process),
            "api_observations": observations,
            "export_artifact": export,
            "retrieved_artifact": {"path": retrieved.relative, "sha256": retrieved.sha256},
        },
    )
    profile, faults = required_profile(root, SnapshotReader(root), fingerprint)
    if faults:
        raise ValueError("sandbox transfer source profile became invalid")
    requirement = next(item for item in profile if item.id == "root:sandbox:transfer")
    details = {
        "execution_exit_code": 0,
        "destination_kind": "sandbox",
        "remote_verified": True,
        "export_artifact": export,
        "retrieved_artifact": {"path": retrieved.relative, "sha256": retrieved.sha256},
        "transfer_artifact": raw,
        "command": ["official-github-artifact-roundtrip", repository, run_id, artifact_id],
    }
    validate_sandbox_transfer(details, reader)
    validate_acceptance(requirement, gate_payload(requirement, fingerprint, "pass", details, []), reader)
    binding = write_json(root, directory / "gate.json", gate_payload(requirement, fingerprint, "pass", details, []))
    report = {
        "schema_version": SCHEMA_VERSION,
        "platform_version": requirement.platform_version,
        "source_fingerprint": fingerprint,
        "roster": list(PUBLIC_PROJECT_NAMES),
        "gates": {
            requirement.id: {
                "status": "pass",
                "command": details["command"],
                "artifact": binding["path"],
                "artifact_sha256": binding["sha256"],
            }
        },
        "exit_code": 0,
    }
    return {**report, "receipt": write_json(root, directory / "receipt.json", report)}


def admitted_runtime_providers(root: Path, receipt_path: Path) -> dict[str, Any]:
    """Discover current providers from independently admitted installed evidence."""
    from infrastructure.project.public_package_dependencies import local_dependency_closure
    from infrastructure.project.installed_acceptance_artifacts import inspect_wheel_bytes

    reader = SnapshotReader(root)
    fingerprint = source_fingerprint(root)
    profile, faults = required_profile(root, reader, fingerprint)
    if faults:
        raise ValueError("runtime provider source profile is invalid")
    requirements = {item.id: item for item in profile}
    receipt = reader.read(receipt_path.absolute().relative_to(root).as_posix()).json_object()
    scopes = sorted(
        {
            provider
            for scope in PUBLIC_PROJECT_NAMES
            for provider in local_dependency_closure(root, scope, reader=reader)
            if provider != "root"
        }
    )
    providers = {}
    for scope in scopes:
        requirement = requirements[f"{scope}:installed"]
        entry = receipt["gates"][requirement.id]
        snapshot = reader.read(entry["artifact"])
        payload = snapshot.json_object()
        expected = gate_payload(requirement, fingerprint, "pass", payload.get("details", {}), [])
        if (
            entry.get("status") != "pass"
            or entry.get("artifact_sha256") != snapshot.sha256
            or any(payload.get(key) != value for key, value in expected.items() if key != "details")
        ):
            raise ValueError("runtime provider installed evidence is incomplete or stale")
        validate_acceptance(requirement, payload, reader)
        binding = payload["details"]["wheel_artifact"]
        wheel = reader.read(binding["path"])
        if wheel.sha256 != binding["sha256"]:
            raise ValueError("runtime provider wheel differs from exact admitted installed bytes")
        inspect_wheel_bytes(root, requirement, wheel.content, reader=reader)
        providers[scope] = binding
    if not reader.unchanged() or source_fingerprint(root) != fingerprint:
        raise ValueError("runtime provider source/evidence changed during admission")
    return {
        "providers": providers,
        "provider_wheel_arguments": [
            argument
            for scope, binding in providers.items()
            for argument in ("--provider-wheel", f"{scope}={root / binding['path']}")
        ],
    }
