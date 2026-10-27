"""Genuine canonical cells and original-child/source/spec refusal controls."""

from __future__ import annotations

import copy
import json
import os
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from infrastructure.core.testing.project_test_matrix import ProjectTestTask, run_project_test_matrix
from infrastructure.project.public_acceptance import _probe_runtime, _record_cell
from infrastructure.project.public_acceptance_cases import project_python_hashes, pytest_command
from infrastructure.project.public_acceptance_evidence import bootstrap_command, cell_environment, write_json
from infrastructure.reporting.release_readiness_profile import Requirement, required_profile
from infrastructure.reporting.readiness_receipts import project_source_identity, source_fingerprint
from tests.infra_tests.reporting.test_required_readiness import _declarations
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.reporting.release_readiness_validators import validate_acceptance
from tests.infra_tests.project.test_public_acceptance import GOOD, PROJECT, _cell

pytestmark = pytest.mark.timeout(240)


def _produce_runtime_case_evidence(root: Path):
    _declarations(root)
    observed = _cell(
        root,
        GOOD,
        metadata_prefix='[project]\nname="exemplar"\nversion="2.0.0"\n',
        extra='platform_version="4.0.1"\ntested_python_versions=["3.14","3.15"]\nrequired_unpaid_capabilities=[]\n',
    )
    assert observed["process"].returncode == 0, observed["process"].output_tail
    raw, directory = observed["raw"], observed["directory"]
    probe = _probe_runtime(root, root / "output/readiness/probe", raw["python_version"], Path(observed["command"][0]))
    fingerprint = source_fingerprint(root)
    requirements, faults = required_profile(root, SnapshotReader(root), fingerprint)
    assert not faults
    requirement = next(
        item
        for item in requirements
        if item.scope == PROJECT and item.kind == "runtime" and item.python_version == raw["python_version"]
    )
    coverage = next(
        item
        for item in requirements
        if item.scope == PROJECT and item.kind == "coverage" and item.python_version == raw["python_version"]
    )
    first, second, summary = _record_cell(
        root,
        directory,
        requirement,
        coverage,
        fingerprint,
        observed["command"],
        observed["process"].returncode,
        probe,
        "fresh-cell",
    )
    assert first["status"] == second["status"] == summary["status"] == "pass"
    details = [json.loads((root / entry["artifact"]).read_text())["details"] for entry in (first, second)]
    return root, requirement, details


@pytest.fixture(scope="module")
def runtime_case_evidence(tmp_path_factory):
    with pytest.MonkeyPatch.context() as environment:
        if "SOURCE_DATE_EPOCH" not in os.environ:
            environment.setenv("SOURCE_DATE_EPOCH", "1700000000")
        return _produce_runtime_case_evidence(tmp_path_factory.mktemp("actual-runtime-reader").resolve())


def _validate(root: Path, requirement: Requirement, details: dict) -> None:
    reader = SnapshotReader(root)
    validate_acceptance(requirement, {"details": details}, reader)
    assert reader.unchanged()


def test_genuine_complete_case_evidence_grants_runtime_and_coverage_without_provider(runtime_case_evidence) -> None:
    root, requirement, details = runtime_case_evidence
    _validate(root, requirement, details[0])
    _validate(root, replace(requirement, kind="coverage"), details[1])


@pytest.mark.parametrize(
    "fault", ["collection", "cases", "processes", "cell", "spec", "cell-process", "run", "counts", "duplicate", "minor"]
)
def test_missing_or_false_case_evidence_cannot_grant_either_gate(runtime_case_evidence, fault: str) -> None:
    root, requirement, originals = runtime_case_evidence
    for kind, original in zip(("runtime", "coverage"), originals, strict=True):
        details = copy.deepcopy(original)
        key = {
            "collection": "collection_artifact",
            "cases": "case_artifacts",
            "processes": "pytest_process_artifacts",
            "cell": "cell_artifact",
            "spec": "cell_spec_artifact",
            "cell-process": "cell_process_artifact",
        }.get(fault)
        if key:
            details.pop(key)
        elif fault == "run":
            details["run_id"] = "unrelated"
        elif fault == "counts":
            if kind == "coverage":
                details.pop("case_artifacts")
            else:
                details["passed"] += 1
                details["collected"] += 1
        elif fault == "duplicate":
            details["case_artifacts"] *= 2
        else:
            details["python_version"] = "3.12" if requirement.python_version != "3.12" else "3.13"
        with pytest.raises(ValueError):
            _validate(root, replace(requirement, kind=kind), details)


@pytest.mark.parametrize("fault", ["failed", "omitted", "stale-schema", "source", "nonce", "runtime", "selection"])
def test_valid_byte_case_tampering_refuses_original_positive_assertions(runtime_case_evidence, fault: str) -> None:
    root, requirement, originals = runtime_case_evidence
    binding = originals[0]["case_artifacts"][0]
    path = root / binding["path"]
    original = path.read_bytes()
    process_path = root / originals[0]["pytest_process_artifacts"][1]["path"]
    original_process = process_path.read_bytes()
    receipt = json.loads(original)
    if fault == "failed":
        receipt["outcomes"][receipt["nodeids"][0]] = "failed"
    elif fault == "omitted":
        node = receipt["nodeids"].pop()
        receipt["outcomes"].pop(node)
    elif fault == "stale-schema":
        receipt["schema_version"] = "template-public-pytest-v1"
    elif fault == "source":
        receipt["source_hashes_after"] = {}
    elif fault == "nonce":
        receipt["nonce"] = "b" * 32
    elif fault == "runtime":
        receipt["runtime"]["python_full_version"] = "3.12.1" if requirement.python_version != "3.12" else "3.14.1"
    else:
        old = receipt["nodeids"][0]
        receipt["nodeids"][0] = "tests/invented.py::test_unexecuted"
        receipt["outcomes"][receipt["nodeids"][0]] = receipt["outcomes"].pop(old)
    try:
        changed = write_json(root, path, receipt)
        process = json.loads(original_process)
        process["receipt_sha256"] = changed["sha256"]
        changed_process = write_json(root, process_path, process)
        for kind, details in zip(("runtime", "coverage"), originals, strict=True):
            altered = copy.deepcopy(details)
            altered["case_artifacts"] = [changed]
            altered["pytest_process_artifacts"][1] = changed_process
            with pytest.raises(ValueError):
                _validate(root, replace(requirement, kind=kind), altered)
    finally:
        path.write_bytes(original)
        process_path.write_bytes(original_process)


@pytest.mark.parametrize("code", [0, 7])
def test_actual_early_child_cannot_reuse_a_real_prior_case_receipt(runtime_case_evidence, code: int) -> None:
    root, requirement, originals = runtime_case_evidence
    process_binding = originals[0]["pytest_process_artifacts"][1]
    path = root / process_binding["path"]
    original = path.read_bytes()
    prior = json.loads(original)
    command = list(prior["command"])
    # Retain the entire original suffix: only exact admitted execution may pass.
    command[3] = f"raise SystemExit({code})\n" + command[3]
    observed = run_project_test_matrix(
        [
            ProjectTestTask(
                0,
                "actual-early-child",
                tuple(command),
                root,
                cell_environment(Path(command[0]), path.parent),
                20,
                True,
            )
        ]
    )[0]
    assert observed.returncode == code and not observed.timed_out, observed.output_tail
    try:
        changed = write_json(
            root,
            path,
            {
                **prior,
                "command": command,
                "exit_code": observed.returncode,
                "timed_out": observed.timed_out,
                "duration_seconds": observed.duration_seconds,
                "diagnostic": observed.detail,
                "output_tail": observed.output_tail,
            },
        )
        for kind, details in zip(("runtime", "coverage"), originals, strict=True):
            altered = copy.deepcopy(details)
            altered["pytest_process_artifacts"][1] = changed
            with pytest.raises(ValueError, match="actual pytest/cell process"):
                _validate(root, replace(requirement, kind=kind), altered)
    finally:
        path.write_bytes(original)


def test_current_owned_source_change_refuses_real_previous_cases(runtime_case_evidence) -> None:
    root, requirement, originals = runtime_case_evidence
    path = root / f"projects/{PROJECT}/tests/test_model.py"
    original = path.read_bytes()
    try:
        path.write_bytes(original + b"\n# changed owned test input\n")
        for kind, details in zip(("runtime", "coverage"), originals, strict=True):
            with pytest.raises(ValueError, match="source/deliverables"):
                _validate(root, replace(requirement, kind=kind), details)
    finally:
        path.write_bytes(original)


@pytest.mark.parametrize("boundary", ["worker", "pytest"])
@pytest.mark.parametrize("bind_original_sha", [True, False], ids=["substituted-spec", "missing-admission-sha"])
def test_actual_child_refuses_substituted_spec_before_owned_code(
    runtime_case_evidence, boundary: str, bind_original_sha: bool
) -> None:
    root, _, originals = runtime_case_evidence
    project = root / "projects" / PROJECT
    metadata_path, test_path = project / "pyproject.toml", project / "tests/test_model.py"
    metadata, test_source = metadata_path.read_bytes(), test_path.read_bytes()
    planner = project / "src/substituted_planner.py"
    directory = root / f"output/readiness/admission-{boundary}-{bind_original_sha}"
    marker = directory / "owned-code-launched.txt"
    spec_path, receipt = directory / "spec.json", directory / "fresh.json"
    if boundary == "worker":
        spec = json.loads((root / originals[0]["cell_spec_artifact"]["path"]).read_text())
    else:
        prior_case = json.loads((root / originals[0]["case_artifacts"][0]["path"]).read_text())
        spec = json.loads((root / prior_case["spec_artifact"]["path"]).read_text())
        spec.update(receipt=receipt.relative_to(root).as_posix(), nonce="c" * 32)
    spec.update(directory=directory.relative_to(root).as_posix(), run_id="actual-substituted-admission")
    original_binding = write_json(root, spec_path, spec)
    try:
        # Both replacement specs truthfully describe the replacement source.
        # Only the separately admitted original spec hash can stop its execution.
        test_path.write_text(f"from pathlib import Path\nPath({str(marker)!r}).write_text('test imported')\n" + GOOD)
        metadata_path.write_bytes(metadata + b'acceptance_test_groups="substituted_planner:groups"\n')
        planner.write_text(
            f"from pathlib import Path\nPath({str(marker)!r}).write_text('planner imported')\n"
            "def groups(project):\n    return [('whole', ['tests/test_model.py'])]\n"
        )
        spec["source_identity"] = project_source_identity(root, PROJECT)
        if boundary == "pytest":
            spec["source_hashes"] = project_python_hashes(root, PROJECT)
        replacement = write_json(root, spec_path, spec)
        assert replacement["sha256"] != original_binding["sha256"]
        if boundary == "worker":
            admission = ("--spec-sha256", original_binding["sha256"]) if bind_original_sha else ()
            command = bootstrap_command(
                Path(sys.executable),
                root,
                "infrastructure.project.public_acceptance_worker",
                "--root",
                str(root),
                "--spec",
                str(spec_path),
                *admission,
            )
        else:
            write_json(root, directory / "dependency-spec.json", {})
            command = pytest_command(
                Path(sys.executable),
                root,
                directory,
                spec["run_id"],
                PROJECT,
                receipt,
                spec_path,
                spec["selectors"],
                spec_sha256=original_binding["sha256"],
                collect=spec["collect"],
                test_timeout=spec["test_timeout_seconds"],
            )
            if not bind_original_sha:
                arguments = list(command)
                index = arguments.index("--execution-spec-sha256")
                del arguments[index : index + 2]
                command = tuple(arguments)
        observed = run_project_test_matrix(
            [
                ProjectTestTask(
                    0,
                    "original-spec-admission",
                    command,
                    root,
                    cell_environment(Path(sys.executable), directory),
                    30,
                    True,
                )
            ]
        )[0]
        assert not observed.timed_out, observed.output_tail
        assert observed.returncode == (1 if bind_original_sha else 2), observed.output_tail
        if bind_original_sha:
            assert "specification hash differs from its original admission" in observed.output_tail
        assert not marker.exists(), "the substituted planner/test executed before original spec admission"
        assert not receipt.exists() and not (directory / "cell.json").exists()
        assert not (directory / "collection.json").exists()
    finally:
        metadata_path.write_bytes(metadata)
        test_path.write_bytes(test_source)
        planner.unlink(missing_ok=True)
