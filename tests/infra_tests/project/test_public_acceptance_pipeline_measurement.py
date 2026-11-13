"""Real pytest/coverage bytes and explicit portable-coordinate refusal controls.

These are component DATA checks, not a complete pipeline/process acceptance.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from infrastructure.core.testing.project_test_measurement import measurement_path, publish_measurement
from infrastructure.project.public_acceptance_auxiliary_pipeline import (
    _child_relative,
    _retain_pipeline_streams,
    _validate_pipeline_streams,
)
from infrastructure.project.public_acceptance_pipeline_measurement import (
    SCHEMA,
    capture_project_measurement,
    retain_project_measurement,
    validate_retained_project_measurement,
)
from infrastructure.project.installed_acceptance_artifacts import write_binary
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.reporting.required_candidate_transport import _graph_paths
from tests.infra_tests.core.test_project_test_measurement import _original

SCOPE = "templates/template_code_project"


def _hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def test_capture_checks_real_original_bytes_and_externally_held_context(tmp_path: Path) -> None:
    project, env, observation = _original(tmp_path)
    anchor = publish_measurement(observation, original_exit_code=0)
    execution = {"run_id": env["PIPELINE_RUN_ID"], "plan_digest": env["PIPELINE_PLAN_DIGEST"]}
    context = (str(project), execution["run_id"], execution["plan_digest"])
    # Functional holder DATA from a real pytest/coverage observation. This test
    # does not assert a whole PipelineExecutor launch or acceptance capability.
    holder = SimpleNamespace(config=SimpleNamespace(project_dir=project), _project_measurement=(context, anchor))
    captured = capture_project_measurement(holder, execution)
    assert captured is not None and captured["anchor_sha256"] == anchor and captured["passed"] == 1
    for bad in (None, (context, "0" * 64), ((str(project), "foreign", context[2]), anchor)):
        holder._project_measurement = bad
        with pytest.raises(ValueError):
            capture_project_measurement(holder, execution)


def _produce_portable_data(producer: Path, reader_root: Path, state: Path) -> None:
    import infrastructure

    assert Path(infrastructure.__file__).resolve() == producer / "infrastructure/__init__.py"
    assert _original.__globals__["ROOT"] == producer
    project, env, observation = _original(producer, scope=SCOPE)
    anchor = publish_measurement(observation, original_exit_code=0)
    measurement = measurement_path(project, env["PIPELINE_RUN_ID"])
    raw = measurement.read_bytes()
    value = json.loads(raw)
    current_project = reader_root / "projects" / SCOPE
    current_project.mkdir(parents=True)
    for name in ("src", "tests"):
        shutil.copytree(project / name, current_project / name)
    shutil.copyfile(project / "pyproject.toml", current_project / "pyproject.toml")
    directory = reader_root / "output/readiness/auxiliary-linux/template_code_project/000"
    directory.mkdir(parents=True)
    outputs = []
    total = 0
    for path in sorted((project / "output").rglob("*")):
        if not path.is_file():
            continue
        content = path.read_bytes()
        relative = path.relative_to(project / "output").as_posix()
        total += len(content)
        outputs.append(
            {
                "relative": relative,
                "sha256": _hash(content),
                "binding": write_binary(reader_root, directory / "pipeline-outputs" / relative, content),
            }
        )
    facts = {
        "producer_root": str(producer),
        "execution": {"run_id": env["PIPELINE_RUN_ID"], "plan_digest": env["PIPELINE_PLAN_DIGEST"]},
        "runtime": {"python_version": sys.version},
        "project_test_measurement": {
            "schema": SCHEMA,
            "context": [str(project), env["PIPELINE_RUN_ID"], env["PIPELINE_PLAN_DIGEST"]],
            "anchor_sha256": anchor,
            "measurement_project_path": measurement.relative_to(project).as_posix(),
            "passed": 1,
        },
    }
    process = {
        "selected_interpreter": value["interpreter"],
        "executable": value["runtime"]["resolved_executable"],
        "executable_sha256": value["runtime"]["binary_sha256"],
    }
    retention = retain_project_measurement(reader_root, directory, producer, SCOPE, facts, outputs, total)
    assert measurement.read_bytes() == raw
    state.write_text(
        json.dumps(
            {
                "custody": {"output_after": outputs, "project_test_measurement": retention},
                "facts": facts,
                "process": process,
                "value": value,
            }
        )
    )


def _validate_loaded_root(root: Path) -> None:
    import infrastructure

    assert Path(infrastructure.__file__).resolve() == root / "infrastructure/__init__.py"
    value = json.loads((root / "output/readiness/validation-request.json").read_bytes())
    validate_retained_project_measurement(
        SCOPE,
        value["custody"],
        value["facts"],
        value["process"],
        SnapshotReader(root, operation_deadline=time.monotonic() + 30),
        Path(value["directory"]),
    )


@pytest.fixture
def portable(tmp_path: Path):
    import subprocess

    producer, reader_root = tmp_path / "producer", tmp_path / "reader"
    source = Path(__file__).resolve().parents[3]
    for root in (producer, reader_root):
        root.mkdir()
        for name in ("infrastructure", "scripts"):
            shutil.copytree(source / name, root / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        for name in ("pyproject.toml", "uv.lock", ".python-version", "pipeline.yaml"):
            if (source / name).is_file():
                shutil.copyfile(source / name, root / name)
        for relative in (
            "tests/infra_tests/core/test_project_test_measurement.py",
            "tests/infra_tests/project/test_public_acceptance_pipeline_measurement.py",
        ):
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / relative, destination)
            for parent in destination.parents:
                if parent == root:
                    break
                initial = parent / "__init__.py"
                if initial.exists():
                    continue
                actual = source / initial.relative_to(root)
                initial.write_bytes(actual.read_bytes() if actual.is_file() else b"")
    state = tmp_path / "observed-portable-data.json"
    body = (
        "import sys;from pathlib import Path;"
        "root=Path(sys.argv[1]);sys.path.insert(0,str(root));"
        "from tests.infra_tests.project.test_public_acceptance_pipeline_measurement import _produce_portable_data;"
        "_produce_portable_data(root,Path(sys.argv[2]),Path(sys.argv[3]))"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", body, str(producer), str(reader_root), str(state)],
        stdin=subprocess.DEVNULL,
        env={
            **os.environ,
            "PYTEST_XDIST_WORKER": "gw-parent",
            "PYTEST_XDIST_WORKER_COUNT": "8",
            "PYTEST_XDIST_TESTRUNUID": "parent-session",
        },
        capture_output=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr.decode()
    observed = json.loads(state.read_bytes())
    directory = reader_root / "output/readiness/auxiliary-linux/template_code_project/000"
    return (
        reader_root,
        directory,
        observed["custody"],
        observed["facts"],
        observed["process"],
        observed["value"],
        producer,
    )


def _validate(root: Path, directory: Path, custody: dict, facts: dict, process: dict) -> None:
    import subprocess

    path = root / "output/readiness/validation-request.json"
    path.write_text(json.dumps({"directory": str(directory), "custody": custody, "facts": facts, "process": process}))
    body = (
        "import sys;from pathlib import Path;"
        "root=Path(sys.argv[1]);sys.path.insert(0,str(root));"
        "from tests.infra_tests.project.test_public_acceptance_pipeline_measurement import _validate_loaded_root;"
        "_validate_loaded_root(root)"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", body, str(root)], stdin=subprocess.DEVNULL, capture_output=True, timeout=45
    )
    if result.returncode:
        raise ValueError(result.stderr.decode())


def test_real_measurement_export_reads_every_original_and_complete_graph(portable) -> None:
    root, directory, custody, facts, process, value, producer = portable
    _validate(root, directory, custody, facts, process)
    retention = custody["project_test_measurement"]
    expected = [*value["receipts"], value["coverage"], value["database"]]
    assert {row["project_path"] for row in retention["artifacts"]} == {row["project_path"] for row in expected}
    for row in retention["artifacts"]:
        assert (root / row["binding"]["path"]).read_bytes() == (
            producer / "projects" / SCOPE / row["project_path"]
        ).read_bytes()
    envelope = directory / "measurement-closure.json"
    envelope.write_text(json.dumps(retention))
    label = envelope.relative_to(root).as_posix()
    for strict in (True, False):
        independent = SnapshotReader(root, operation_deadline=time.monotonic() + 30)
        paths = _graph_paths(root, label, independent, deadline=independent.operation_deadline, strict_bindings=strict)
        assert len(paths) == len(expected) + 2
        assert {row["binding"]["path"] for row in retention["artifacts"]}.issubset(paths)
        assert independent.unchanged()


@pytest.mark.parametrize(
    "fault",
    [
        "missing-database",
        "changed-coverage",
        "changed-receipt",
        "omitted-reference",
        "extra-reference",
        "sibling-binding",
        "sibling-receipt-both",
        "sibling-measurement-both",
        "held-anchor",
        "context",
        "source",
        "floor",
        "count",
        "runtime",
        "legacy-v1",
    ],
)
def test_portable_measurement_refuses_changed_originals_or_context(portable, fault: str) -> None:
    root, directory, original_custody, original_facts, original_process, _, _ = portable
    custody, facts, process = (
        copy.deepcopy(original_custody),
        copy.deepcopy(original_facts),
        copy.deepcopy(original_process),
    )
    retention = custody["project_test_measurement"]
    if fault in {"missing-database", "changed-coverage", "changed-receipt"}:
        role = (
            ".coverage.project"
            if fault == "missing-database"
            else "coverage_project.json"
            if fault == "changed-coverage"
            else None
        )
        row = (
            next(row for row in retention["artifacts"] if row["project_path"] == role)
            if role
            else retention["artifacts"][0]
        )
        path = root / row["binding"]["path"]
        if fault == "missing-database":
            path.unlink()
        else:
            path.write_bytes(path.read_bytes() + b"\nchanged original\n")
    elif fault == "omitted-reference":
        retention["artifacts"].pop()
    elif fault == "extra-reference":
        retention["artifacts"].append(copy.deepcopy(retention["artifacts"][0]))
    elif fault == "sibling-binding":
        row = retention["artifacts"][-1]
        source = root / row["binding"]["path"]
        sibling = directory.parent / "001/copied-database"
        sibling.parent.mkdir()
        sibling.write_bytes(source.read_bytes())
        row["binding"]["path"] = sibling.relative_to(root).as_posix()
    elif fault in {"sibling-receipt-both", "sibling-measurement-both"}:
        if fault == "sibling-receipt-both":
            entry = next(row for row in retention["artifacts"] if row["project_path"].startswith("output/"))
            binding = entry["binding"]
            output = next(
                row
                for row in custody["output_after"]
                if row["relative"] == entry["project_path"].removeprefix("output/")
            )
        else:
            binding = retention["measurement_artifact"]
            output = next(row for row in custody["output_after"] if row["relative"].endswith("/measurement.json"))
        sibling = directory.parent / "001" / Path(binding["path"]).name
        sibling.parent.mkdir()
        sibling.write_bytes((root / binding["path"]).read_bytes())
        changed = {"path": sibling.relative_to(root).as_posix(), "sha256": binding["sha256"]}
        output["binding"] = changed
        if fault == "sibling-receipt-both":
            entry["binding"] = changed
        else:
            retention["measurement_artifact"] = changed
    elif fault == "held-anchor":
        facts["project_test_measurement"]["anchor_sha256"] = "0" * 64
    elif fault == "context":
        facts["project_test_measurement"]["context"][1] = "foreign-run"
    elif fault == "runtime":
        process["executable_sha256"] = "0" * 64
    else:
        path = root / retention["measurement_artifact"]["path"]
        value = json.loads(path.read_bytes())
        if fault == "legacy-v1":
            value["schema"] = "template-project-test-measurement/v1"
            for reference in [*value["receipts"], value["coverage"], value["database"]]:
                reference["path"] = reference.pop("project_path")
        else:
            value[fault if fault != "count" else "passed"] = "foreign" if fault == "source" else 0
        raw = json.dumps(value).encode()
        path.write_bytes(raw)
        digest = _hash(raw)
        retention["measurement_artifact"]["sha256"] = digest
        facts["project_test_measurement"]["anchor_sha256"] = digest
    with pytest.raises((ValueError, OSError, KeyError, TypeError)):
        _validate(root, directory, custody, facts, process)


def test_real_stream_export_uses_same_birth_coordinate_and_refuses_splicing(tmp_path: Path) -> None:
    root, copied = tmp_path / "reader", tmp_path / "producer"
    root.mkdir()
    copied.mkdir()
    directory = root / "output/readiness/auxiliary-linux/template_code_project/000"
    directory.mkdir(parents=True)
    child = _child_relative(root, directory)
    process = {"streams": {}}
    for name in ("stdout", "stderr"):
        path = copied / child / "execution" / (name + ".txt")
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = (name + " original bytes\n").encode()
        path.write_bytes(raw)
        process["streams"][name] = {"path": path.relative_to(copied).as_posix(), "sha256": _hash(raw)}
    bindings = _retain_pipeline_streams(root, directory, copied, process)
    assert bindings == process["streams"]
    _validate_pipeline_streams({"retained_streams": bindings}, process, SnapshotReader(root), child)
    sibling = copy.deepcopy(bindings)
    sibling["stdout"]["path"] = sibling["stdout"]["path"].replace("/000/", "/001/")
    with pytest.raises(ValueError, match="coordinate"):
        _validate_pipeline_streams({"retained_streams": sibling}, process, SnapshotReader(root), child)
    old = copy.deepcopy(process)
    old["streams"]["stdout"]["path"] = "output/readiness/pipeline-child/execution/stdout.txt"
    with pytest.raises(ValueError, match="born"):
        _retain_pipeline_streams(root, directory, copied, old)
    (root / bindings["stdout"]["path"]).write_bytes(b"changed retained bytes")
    with pytest.raises(ValueError, match="bytes"):
        _validate_pipeline_streams({"retained_streams": bindings}, process, SnapshotReader(root), child)


@pytest.mark.parametrize("strict", [True, False])
def test_legacy_project_paths_remain_rejected_by_the_actual_graph(portable, strict: bool) -> None:
    root, directory, custody, _, _, _, _ = portable
    original = root / custody["project_test_measurement"]["measurement_artifact"]["path"]
    value = json.loads(original.read_bytes())
    value["schema"] = "template-project-test-measurement/v1"
    for row in [*value["receipts"], value["coverage"], value["database"]]:
        row["path"] = row.pop("project_path")
    legacy = directory / "legacy-measurement.json"
    legacy.write_text(json.dumps(value))
    with pytest.raises((ValueError, OSError)):
        _graph_paths(
            root,
            legacy.relative_to(root).as_posix(),
            SnapshotReader(root),
            deadline=time.monotonic() + 30,
            strict_bindings=strict,
        )
