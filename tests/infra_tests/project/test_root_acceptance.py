"""Current root producer admission and original negative-runtime aggregation controls."""

from __future__ import annotations

import hashlib
import json
import os
import shlex
import sys
import time
from pathlib import Path

import pytest

from infrastructure.core.testing.project_test_matrix import ProjectTestTask, run_project_test_matrix
from infrastructure.project.public_acceptance import run_public_acceptance
from infrastructure.project.public_acceptance_evidence import cell_environment
from infrastructure.project.public_acceptance_root import run_root_acceptance
from infrastructure.project.public_acceptance_scope import MissingRootCasePolicy, RuntimeScope
from infrastructure.reporting.readiness_receipts import source_fingerprint
from infrastructure.reporting.release_readiness_profile import required_profile
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from tests.infra_tests.reporting.test_required_readiness import _declarations

pytestmark = pytest.mark.timeout(240)


def _owned_root(root: Path, *, policy: bool = True, conftest: str | None = None) -> None:
    """Declare current policy for controls that must refuse before collection."""
    _declarations(root)
    if not policy:
        metadata = root / "pyproject.toml"
        metadata.write_text(metadata.read_text().split("[tool.template.root_acceptance]", 1)[0])
    if conftest is not None:
        (root / "conftest.py").write_text(conftest)


def test_root_producer_blocks_missing_policy_without_test_or_probe_execution(tmp_path: Path) -> None:
    root = tmp_path / "candidate"
    root.mkdir()
    marker = root / "output/readiness/must-not-execute.txt"
    _owned_root(root, policy=False, conftest=f"from pathlib import Path\nPath({str(marker)!r}).write_text('unsafe')\n")
    environment = cell_environment(Path(sys.executable), tmp_path / "setup-evidence", repo_root=root)
    isolated = tmp_path / "selected-python"
    created = run_project_test_matrix(
        [
            ProjectTestTask(
                0,
                "owned-runtime-venv",
                (sys.executable, "-I", "-m", "venv", "--without-pip", str(isolated)),
                root,
                environment,
                30,
                True,
            )
        ]
    )[0]
    assert created.returncode == 0 and not created.timed_out, created
    selected = isolated / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    discovered = run_project_test_matrix(
        [
            ProjectTestTask(
                0,
                "owned-runtime-site",
                (str(selected), "-I", "-c", "import sysconfig;print(sysconfig.get_path('purelib'))"),
                root,
                environment,
                15,
                True,
            )
        ]
    )[0]
    assert discovered.returncode == 0 and not discovered.timed_out, discovered
    purelib = Path(discovered.output_tail).resolve()
    assert purelib.is_dir() and purelib.is_relative_to(isolated.resolve())
    probe_marker = tmp_path / "selected-runtime-executed.txt"
    (purelib / "sitecustomize.py").write_text(
        f"from pathlib import Path\nPath({str(probe_marker)!r}).write_text('actual selected runtime')\n"
    )
    fingerprint = source_fingerprint(root)
    minor = f"{sys.version_info.major}.{sys.version_info.minor}"
    with pytest.raises(MissingRootCasePolicy):
        run_root_acceptance(root, {minor: selected})
    assert not marker.exists() and not probe_marker.exists()
    assert source_fingerprint(root) == fingerprint
    assert not list((root / "output/readiness").rglob("*process.json"))
    assert not list((root / "output/readiness").rglob("runtime-*.json"))
    # Prove the marker is live under the producer's actual isolated invocation;
    # an absent marker cannot establish nonexecution if its fixture never runs.
    executed = run_project_test_matrix(
        [ProjectTestTask(0, "owned-runtime-marker", (str(selected), "-I", "-c", "pass"), root, environment, 15, True)]
    )[0]
    assert executed.returncode == 0 and not executed.timed_out, executed
    assert probe_marker.read_text() == "actual selected runtime"


@pytest.mark.skipif(os.name == "nt", reason="owned negative executable probe uses a POSIX launcher")
@pytest.mark.parametrize("producer", ["root", "public"])
@pytest.mark.parametrize("fault", ["interrupted", "native-timeout-exit", "supervised-timeout"])
def test_actual_negative_probe_preserves_original_outcome_in_root_and_public_aggregation(
    tmp_path: Path, producer: str, fault: str
) -> None:
    root = tmp_path.resolve()
    test_marker = root / "output/readiness/must-not-execute.txt"
    _owned_root(root, conftest=f"from pathlib import Path\nPath({str(test_marker)!r}).write_text('unsafe')\n")
    program = root / "output/readiness/negative-probe-program"
    program.mkdir(parents=True)
    probe_marker = program / "actual-negative-probe.txt"
    code = 130 if fault == "interrupted" else 124
    body = (
        "import os,time\nfrom pathlib import Path\n"
        f"Path({str(probe_marker)!r}).write_text(str(os.getpid()))\n"
        "print('owned invalid runtime probe; cannot establish acceptance', flush=True)\n"
        + ("time.sleep(180)\n" if fault == "supervised-timeout" else "")
        + f"raise SystemExit({code})\n"
    )
    launcher = program / "negative-probe.sh"
    launcher.write_text(f"#!/bin/sh\nexec {shlex.quote(sys.executable)} -I -c {shlex.quote(body)}\n")
    launcher.chmod(0o700)
    minor = f"{sys.version_info.major}.{sys.version_info.minor}"
    selected = {minor: launcher}
    started = time.monotonic()
    result = (
        run_root_acceptance(root, selected)
        if producer == "root"
        else run_public_acceptance(root, selected, projects=("templates/template_code_project",))
    )
    assert time.monotonic() - started < 170
    assert result["exit_code"] == code
    assert not test_marker.exists()
    assert not list((root / "output/readiness").rglob("collection-process.json"))
    pid = int(probe_marker.read_text())
    assert pid != os.getpid()
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)
    matrix = result["root_matrix" if producer == "root" else "matrix"]
    expected = matrix["expected_cells"]
    if producer == "public":
        assert matrix["matrix_complete"] is False
        assert expected == 50 and matrix["selected_cells"] == 2
        expected = matrix["selected_cells"]
    assert matrix["counts"] == {"pass": 0, "fail": 1, "blocked": expected - 1, "unknown": 0}
    failed = next(row for row in matrix["results"] if row["status"] == "fail")
    if producer == "public":
        assert failed["execution_exit_code"] == code
        assert failed["timed_out"] is (fault == "supervised-timeout")
    receipt = json.loads((root / result["receipt"]["path"]).read_text())
    gate = (
        receipt["gates"][failed["gate"]]
        if producer == "root"
        else receipt["gates"][f"templates/template_code_project:runtime:{minor}"]
    )
    details = json.loads((root / gate["artifact"]).read_text())["details"]
    assert details["execution_exit_code"] == code
    assert details["timed_out"] is (fault == "supervised-timeout")
    probe_bytes = (root / details["runtime_artifact"]["path"]).read_bytes()
    assert hashlib.sha256(probe_bytes).hexdigest() == details["runtime_artifact"]["sha256"]
    probe = json.loads(probe_bytes)
    assert probe["status"] == "fail"
    assert probe["execution_exit_code"] == code
    assert probe["timed_out"] is (fault == "supervised-timeout")
    assert all("execution_exit_code" not in row for row in matrix["results"] if row["status"] == "blocked")


@pytest.mark.parametrize("producer", ["root", "public"])
def test_missing_selected_interpreters_remain_blocked_without_invented_child_exits(
    tmp_path: Path, producer: str
) -> None:
    root = tmp_path.resolve()
    _owned_root(root)
    result = (
        run_root_acceptance(root, {})
        if producer == "root"
        else run_public_acceptance(root, {}, projects=("templates/template_code_project",))
    )
    assert result["exit_code"] == 75
    matrix = result["root_matrix" if producer == "root" else "matrix"]
    expected = matrix["expected_cells"]
    if producer == "public":
        assert matrix["matrix_complete"] is False
        assert expected == 50 and matrix["selected_cells"] == 2
        expected = matrix["selected_cells"]
    assert matrix["counts"] == {"pass": 0, "fail": 0, "blocked": expected, "unknown": 0}
    assert all("execution_exit_code" not in row and "timed_out" not in row for row in matrix["results"])
    receipt = json.loads((root / result["receipt"]["path"]).read_text())
    for entry in receipt["gates"].values():
        assert entry["status"] == "blocked"
        assert entry["command"] in (["unavailable-selected-interpreter"], ["unavailable-complete-root-cohort"])
        details = json.loads((root / entry["artifact"]).read_text())["details"]
        assert not {"runtime_artifact", "execution_exit_code", "timed_out"}.intersection(details)
    for runtime in ("3.14", "3.15"):
        assert not list((root / "output/readiness").rglob(f"runtime-{runtime}.json"))
    assert not list((root / "output/readiness").rglob("cell-process.json"))
    assert not list((root / "output/readiness").rglob("collection-process.json"))


def test_root_coverage_default_is_bound_to_actual_source_metadata(tmp_path: Path) -> None:
    _owned_root(tmp_path)
    (tmp_path / ".python-version").write_text("3.12\n")
    requirements, faults = required_profile(tmp_path, SnapshotReader(tmp_path), source_fingerprint(tmp_path))
    assert not requirements and faults and faults[0].state == "fail"


@pytest.mark.parametrize("scope", ["working/private", "templates/unknown", "../root", "projects/root"])
def test_root_runtime_scope_refuses_private_and_invented_projects(tmp_path: Path, scope: str) -> None:
    with pytest.raises(ValueError):
        RuntimeScope(tmp_path, scope)


@pytest.mark.parametrize("schema", [None, 1, 2])
def test_absent_or_unsupported_policy_cannot_restore_root_runtime_profile(tmp_path: Path, schema: int | None) -> None:
    _owned_root(tmp_path, policy=False)
    if schema is not None:
        with (tmp_path / "pyproject.toml").open("a") as stream:
            stream.write(f"[tool.template.root_acceptance]\nschema_version={schema}\n")
    requirements, faults = required_profile(tmp_path, SnapshotReader(tmp_path), source_fingerprint(tmp_path))
    assert any(item.id == "root:case-policy" for item in requirements)
    assert not any(item.scope == "root" and item.kind == "runtime" for item in requirements)
    assert any(item.id == "root:case-declaration" for item in faults)


def test_generic_exemplar_reader_and_worker_refuse_root_scope_before_execution(tmp_path: Path) -> None:
    from infrastructure.project.public_acceptance_worker import run_cell
    from infrastructure.reporting.release_readiness_profile import Requirement
    from infrastructure.reporting.release_readiness_runtime import validate_runtime_cases

    with pytest.raises(ValueError, match="complete case-policy"):
        run_cell({"root": str(tmp_path), "scope": "root"}, {})
    requirement = Requirement("root:invented", "runtime", "root", "4.4.0", "4.4.0", "0" * 64)
    with pytest.raises(ValueError, match="complete case-policy"):
        validate_runtime_cases(requirement, {}, SnapshotReader(tmp_path))
