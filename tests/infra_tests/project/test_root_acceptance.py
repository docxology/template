"""Genuine root cells and independent source/spec/case/coverage controls."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shlex
import sys
import time
from dataclasses import asdict, replace
from pathlib import Path

import pytest

from infrastructure.core.testing.project_test_matrix import ProjectTestTask, run_project_test_matrix
from infrastructure.core.files.project_lock import project_output_lock
from infrastructure.project.public_acceptance import _probe_runtime, _record_cell, run_public_acceptance
from infrastructure.project.public_acceptance_cases import project_python_hashes
from infrastructure.project.public_acceptance_evidence import bootstrap_command, cell_environment, write_json
from infrastructure.project.public_acceptance_root import run_root_acceptance
from infrastructure.project.public_acceptance_scope import RuntimeScope
from infrastructure.reporting.readiness_receipts import source_fingerprint
from infrastructure.reporting.release_readiness_profile import required_profile
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.reporting.release_readiness_validators import validate_acceptance
from tests.infra_tests.reporting.test_required_readiness import _declarations

pytestmark = pytest.mark.timeout(240)

_TEST = """import importlib.util
from pathlib import Path

def test_owned_root_branches():
    path = Path(__file__).resolve().parents[1] / 'infrastructure/probe.py'
    spec = importlib.util.spec_from_file_location('_owned_root_probe', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.score(True) == 1
    assert module.score(False) == 0
"""


def _owned_root(root: Path, *, policy: bool = True, conftest: str | None = None, uncovered: bool = False) -> None:
    _declarations(root)
    metadata = (root / "pyproject.toml").read_text()
    metadata += '[tool.coverage.run]\nbranch=true\nsource=["infrastructure"]\nomit=["infrastructure/_version.py"]\n'
    if policy:
        metadata += '[tool.template.root_acceptance]\nschema_version=1\nselection="complete-offline"\n'
    (root / "pyproject.toml").write_text(metadata)
    (root / "tests").mkdir()
    (root / "tests/test_owned.py").write_text(_TEST)
    module = "def score(value):\n    if value:\n        return 1\n    return 0\n"
    if uncovered:
        module += "\n".join(
            f"def unused_{index}(value):\n    if value:\n        return {index}\n    return -1\n" for index in range(40)
        )
    (root / "infrastructure/probe.py").write_text(module)
    if conftest is not None:
        (root / "conftest.py").write_text(conftest)


def _launch(root: Path, *, fault: str = "", timeout: int = 120, independent_lock: bool = False) -> dict:
    scope = RuntimeScope(root, "root")
    directory = root / "output/readiness/actual-root-cell"
    probe = _probe_runtime(
        root,
        root / "output/readiness/probe",
        f"{sys.version_info.major}.{sys.version_info.minor}",
        Path(sys.executable),
    )
    assert probe["status"] == "pass", probe
    spec = {
        "root": str(root),
        "scope": "root",
        "directory": directory.relative_to(root).as_posix(),
        "run_id": "actual-owned-root",
        "runtime": probe["runtime"],
        "source_identity": scope.source_identity(),
        "deliverables_identity": scope.deliverables_identity(),
        "test_files": list(scope.test_files()),
        "timeout_seconds": timeout,
        "test_timeout_seconds": 60,
        "dependency_providers": {},
    }
    if fault == "wrong-minor":
        spec["runtime"] = {
            **spec["runtime"],
            "python_version": "3.12" if spec["runtime"]["python_version"] != "3.12" else "3.13",
        }
    if fault == "missing-case":
        spec["test_files"] = []
    binding = write_json(root, directory / "spec.json", spec)
    if fault == "changed-spec":
        write_json(root, directory / "spec.json", {**spec, "run_id": "substituted-root-spec"})
    args = ["--root", str(root), "--spec", str(root / binding["path"])]
    if fault != "missing-sha":
        args += ["--spec-sha256", binding["sha256"]]
    command = bootstrap_command(Path(sys.executable), root, "infrastructure.project.public_acceptance_worker", *args)
    env = cell_environment(Path(sys.executable), directory, repo_root=root)
    if independent_lock:
        env = {key: value for key, value in env.items() if not key.startswith("TEMPLATE_PROJECT_LOCK_")}
    task = ProjectTestTask(0, "root", command, root, env, 150, True)
    observed = run_project_test_matrix([task], workers=1)[0]
    write_json(
        root,
        directory / "cell-process.json",
        {**asdict(observed), "command": list(command), "run_id": spec["run_id"], "spec_artifact": binding},
    )
    raw = json.loads((directory / "cell.json").read_text()) if (directory / "cell.json").exists() else None
    return {"process": observed, "command": command, "directory": directory, "probe": probe, "raw": raw}


@pytest.fixture(scope="module")
def actual_root_evidence(tmp_path_factory):
    root = tmp_path_factory.mktemp("genuine-root-runtime").resolve()
    marker = root / "output/readiness/root-conftest-marker.txt"
    _owned_root(root, conftest=f"from pathlib import Path\nPath({str(marker)!r}).write_text('actual root conftest')\n")
    observed = _launch(root)
    assert observed["process"].returncode == 0, observed["process"].output_tail
    assert marker.read_text() == "actual root conftest"
    fingerprint = source_fingerprint(root)
    requirements, faults = required_profile(root, SnapshotReader(root), fingerprint)
    assert not faults
    runtime = next(
        item for item in requirements if item.id == f"root:runtime:{observed['probe']['runtime']['python_version']}"
    )
    coverage = next(item for item in requirements if item.id == "root:coverage")
    first, second, summary = _record_cell(
        root,
        observed["directory"],
        runtime,
        replace(coverage, python_version=runtime.python_version),
        fingerprint,
        observed["command"],
        observed["process"].returncode,
        observed["probe"],
        "actual-owned-root",
    )
    assert first["status"] == second["status"] == summary["status"] == "pass"
    return (
        root,
        runtime,
        coverage,
        [json.loads((root / entry["artifact"]).read_text())["details"] for entry in (first, second)],
    )


def test_actual_complete_root_runtime_and_source_selected_coverage(actual_root_evidence) -> None:
    root, runtime, coverage, details = actual_root_evidence
    reader = SnapshotReader(root)
    validate_acceptance(runtime, {"details": details[0]}, reader)
    assert coverage.python_version == "3.14"
    if runtime.python_version == coverage.python_version:
        validate_acceptance(coverage, {"details": details[1]}, reader)
    else:
        with pytest.raises(ValueError):
            validate_acceptance(coverage, {"details": details[1]}, reader)
    assert reader.unchanged()
    hashes = project_python_hashes(root, "root")
    assert {"conftest.py", "tests/test_owned.py", "infrastructure/probe.py"} <= set(hashes)
    assert not any(path.startswith("projects/root/") for path in hashes)


def test_nominated_root_infrastructure_refuses_poison_in_actual_fresh_cache(tmp_path: Path) -> None:
    root = tmp_path / "candidate"
    root.mkdir()
    marker = tmp_path / "stale-code-executed"
    probe = root / "infrastructure/probe.py"
    injected = (
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('stale candidate code')\nraise SystemExit(77)\n"
    ).encode()
    # An owned conftest writes poison into the interpreter's selected fresh
    # prefix, then restores source bytes and timestamps before actual execution.
    # A source-only snapshot cannot distinguish this from original code.
    conftest = (
        "import importlib.util,os,py_compile\nfrom pathlib import Path\n"
        f"probe=Path({str(probe)!r})\noriginal=probe.read_bytes(); observed=probe.stat()\n"
        f"injected={injected!r}\nassert len(injected)<len(original)\n"
        "probe.write_bytes(injected.ljust(len(original),b' '))\n"
        "os.utime(probe,ns=(observed.st_atime_ns,observed.st_mtime_ns))\n"
        "py_compile.compile(str(probe),doraise=True,invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP)\n"
        "probe.write_bytes(original)\n"
        "os.utime(probe,ns=(observed.st_atime_ns,observed.st_mtime_ns))\n"
        "spec=importlib.util.spec_from_file_location('_owned_candidate_probe',probe)\n"
        "module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)\n"
    )
    _owned_root(root, conftest=conftest)
    probe.write_bytes(probe.read_bytes() + b"\n#" + b"x" * 1024 + b"\n")
    original = probe.read_bytes()
    fingerprint = source_fingerprint(root)
    environment = cell_environment(Path(sys.executable), tmp_path / "ordinary-evidence", repo_root=root)
    ordinary = (
        sys.executable,
        "-I",
        "-X",
        f"pycache_prefix={tmp_path / 'ordinary-prefix'}",
        "-c",
        "import runpy,sys;runpy.run_path(sys.argv[1])",
        str(root / "conftest.py"),
    )
    first = run_project_test_matrix([ProjectTestTask(0, "ordinary-poison", ordinary, root, environment, 20, True)])[0]
    assert first.returncode == 77 and not first.timed_out and marker.read_text() == "stale candidate code"
    marker.unlink()
    observed = _launch(root)
    assert observed["process"].returncode != 0 and not observed["process"].timed_out
    assert not marker.exists() and probe.read_bytes() == original
    assert source_fingerprint(root) == fingerprint
    receipt = json.loads((observed["directory"] / "collection.json").read_text())
    process = json.loads((observed["directory"] / "collection-process.json").read_text())
    assert receipt["pytest_exit_code"] == receipt["exit_code"] == process["exit_code"] == 4
    assert "executed public module differs from current source bytes: probe.py" in process["output_tail"]
    assert "outside the pre-import audit roots" not in process["output_tail"]
    raw = observed["raw"]
    assert raw["observed_child_exit_codes"] == [4]
    assert raw["source_identity_after"] == raw["source_identity"]
    assert raw["deliverables_identity_after"] == raw["deliverables_identity"]


@pytest.mark.parametrize("fault", ["wrong-minor", "missing-case", "changed-spec", "missing-sha"])
def test_root_child_refuses_incoherent_admission_before_owned_conftest(tmp_path: Path, fault: str) -> None:
    root = tmp_path.resolve()
    marker = root / "output/readiness/must-not-execute.txt"
    _owned_root(root, conftest=f"from pathlib import Path\nPath({str(marker)!r}).write_text('unadmitted')\n")
    observed = _launch(root, fault=fault)
    assert observed["process"].returncode != 0
    assert not marker.exists()


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
    result = run_root_acceptance(root, {minor: selected})
    assert result["exit_code"] == 75
    assert result["root_matrix"]["counts"] == {"pass": 0, "fail": 0, "blocked": 3, "unknown": 0}
    assert result["root_matrix"]["source_current"] is True
    assert not marker.exists() and not probe_marker.exists()
    assert source_fingerprint(root) == fingerprint
    receipt = json.loads((root / result["receipt"]["path"]).read_text())
    assert set(receipt["gates"]) == {"root:runtime:3.12", "root:runtime:3.13", "root:runtime:3.14", "root:coverage"}
    diagnostic = "ROOT-ACCEPTANCE-CASE-POLICY-1: reviewed root offline case policy is missing"
    for gate, entry in receipt["gates"].items():
        assert entry["status"] == "blocked"
        assert entry["command"] == ["unavailable-selected-interpreter"]
        payload = json.loads((root / entry["artifact"]).read_text())
        assert payload["gate"] == gate and payload["status"] == "blocked" and payload["scope"] == "root"
        assert payload["details"]["diagnostic"] == diagnostic
        assert payload["blockers"] == [{"tool": "root case policy", "reason": diagnostic}]
        assert not {"runtime_artifact", "execution_exit_code", "timed_out"}.intersection(payload["details"])
    assert not list((root / "output/readiness").rglob("cell-process.json"))
    assert not list((root / "output/readiness").rglob("collection-process.json"))
    for runtime in ("3.14", "3.15"):
        assert not list((root / "output/readiness").rglob(f"runtime-{runtime}.json"))
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
    assert matrix["counts"] == {"pass": 0, "fail": 1, "blocked": 2, "unknown": 0}
    failed = next(row for row in matrix["results"] if row["status"] == "fail")
    assert failed["execution_exit_code"] == code
    assert failed["timed_out"] is (fault == "supervised-timeout")
    receipt = json.loads((root / result["receipt"]["path"]).read_text())
    gate = receipt["gates"][f"{'root' if producer == 'root' else 'templates/template_code_project'}:runtime:{minor}"]
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
    assert matrix["counts"] == {"pass": 0, "fail": 0, "blocked": 3, "unknown": 0}
    assert all("execution_exit_code" not in row and "timed_out" not in row for row in matrix["results"])
    receipt = json.loads((root / result["receipt"]["path"]).read_text())
    for entry in receipt["gates"].values():
        assert entry["status"] == "blocked"
        assert entry["command"] == ["unavailable-selected-interpreter"]
        details = json.loads((root / entry["artifact"]).read_text())["details"]
        assert not {"runtime_artifact", "execution_exit_code", "timed_out"}.intersection(details)
    for runtime in ("3.14", "3.15"):
        assert not list((root / "output/readiness").rglob(f"runtime-{runtime}.json"))
    assert not list((root / "output/readiness").rglob("cell-process.json"))
    assert not list((root / "output/readiness").rglob("collection-process.json"))


def test_actual_root_cell_own_lock_deadline_retains_timeout_without_inventing_pytest_exit(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    marker = root / "output/readiness/must-not-execute.txt"
    _owned_root(root, conftest=f"from pathlib import Path\nPath({str(marker)!r}).write_text('unsafe')\n")
    with project_output_lock(root, timeout=5):
        observed = _launch(root, timeout=1, independent_lock=True)
    assert observed["process"].returncode == 124, observed["process"].output_tail
    assert not observed["process"].timed_out
    assert observed["raw"]["status"] == "fail"
    assert observed["raw"]["cell_exit_code"] == 124
    assert "execution_exit_code" not in observed["raw"]
    assert not (observed["directory"] / "collection-process.json").exists()
    assert not marker.exists()


@pytest.mark.parametrize("exit_code", [130, 124])
def test_actual_interrupted_root_child_receipt_retains_original_exit_before_outcome_validation(
    tmp_path: Path, exit_code: int
) -> None:
    root = tmp_path.resolve()
    marker = root / "output/readiness/actual-interrupted-test.txt"
    conftest = (
        "def pytest_sessionfinish(session, exitstatus):\n"
        "    if not session.config.option.collectonly:\n"
        f"        session.exitstatus = {exit_code}\n"
    )
    _owned_root(root, conftest=conftest)
    (root / "tests/test_owned.py").write_text(
        _TEST
        + f"    Path({str(marker)!r}).write_text('actual interrupted pytest call')\n"
        + "    raise KeyboardInterrupt('owned interrupted child')\n"
    )
    observed = _launch(root)
    assert marker.read_text() == "actual interrupted pytest call"
    assert observed["process"].returncode == exit_code, observed["process"].output_tail
    assert not observed["process"].timed_out
    assert observed["raw"]["status"] == "fail"
    assert observed["raw"]["execution_exit_code"] == exit_code
    assert observed["raw"]["observed_child_exit_codes"] == [0, exit_code]
    assert "cell_exit_code" not in observed["raw"]
    process = json.loads((observed["directory"] / "chunk-001-process.json").read_text())
    receipt_bytes = (observed["directory"] / "chunk-001.json").read_bytes()
    receipt = json.loads(receipt_bytes)
    assert process["exit_code"] == receipt["exit_code"] == receipt["pytest_exit_code"] == exit_code
    assert process["timed_out"] is False
    assert receipt["outcomes"] and set(receipt["outcomes"].values()) == {"incomplete"}
    assert process["receipt_sha256"] == hashlib.sha256(receipt_bytes).hexdigest()
    assert not (observed["directory"] / "chunk-002-process.json").exists()


def test_complete_offline_declaration_cannot_admit_known_opt_in_cases(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    marker = root / "output/readiness/must-not-execute.txt"
    _owned_root(root, conftest=f"from pathlib import Path\nPath({str(marker)!r}).write_text('unsafe')\n")
    (root / "tests/test_live.py").write_text(
        "import pytest\n@pytest.mark.requires_credentials\ndef test_paid_surface():\n"
        "    raise AssertionError('must not execute')\n"
    )
    result = run_root_acceptance(root, {})
    assert result["exit_code"] == 75
    assert result["root_matrix"]["counts"]["blocked"] == 3
    assert not marker.exists()


def test_root_coverage_default_is_bound_to_actual_source_metadata(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    _owned_root(root)
    (root / ".python-version").write_text("3.12\n")
    requirements, faults = required_profile(root, SnapshotReader(root), source_fingerprint(root))
    assert requirements == ()
    assert any(item.id == "root:metadata" and item.state == "fail" for item in faults)


def test_actual_root_branch_coverage_below_sixty_refuses_success(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    _owned_root(root, uncovered=True)
    observed = _launch(root)
    assert observed["process"].returncode == 1, observed["process"].output_tail
    assert observed["raw"]["coverage"]["percent"] < 60
    assert observed["raw"]["status"] == "fail"


def test_actual_root_empty_collection_cannot_pass(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    _owned_root(root)
    (root / "tests/test_owned.py").unlink()
    observed = _launch(root)
    assert observed["process"].returncode != 0
    assert observed["raw"]["status"] == "fail"


def test_restored_root_conftest_cannot_hide_actual_substituted_execution(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    marker = root / "output/readiness/substituted-root-conftest.txt"
    replacement = f"from pathlib import Path\nPath({str(marker)!r}).write_text('changed root code executed')\n"
    conftest = (
        "import importlib.util\nfrom pathlib import Path\n"
        "owned=Path(__file__)\noriginal=owned.read_bytes()\n"
        f"owned.write_text({replacement!r})\n"
        "try:\n"
        "    spec=importlib.util.spec_from_file_location('_changed_root_conftest',owned)\n"
        "    module=importlib.util.module_from_spec(spec)\n"
        "    spec.loader.exec_module(module)\n"
        "finally:\n    owned.write_bytes(original)\n"
    )
    _owned_root(root, conftest=conftest)
    identity = RuntimeScope(root, "root").source_identity()
    observed = _launch(root)
    assert marker.read_text() == "changed root code executed"
    assert RuntimeScope(root, "root").source_identity() == identity
    assert observed["process"].returncode == 1
    assert observed["raw"]["status"] == "fail"


def test_actual_early_zero_root_child_cannot_replay_complete_previous_receipts(actual_root_evidence) -> None:
    root, requirement, _, originals = actual_root_evidence
    details = copy.deepcopy(originals[0])
    original = json.loads((root / details["cell_process_artifact"]["path"]).read_text())
    command = list(original["command"])
    index = command.index("-c") + 1
    command[index] = "raise SystemExit(0)\n" + command[index]
    task = ProjectTestTask(
        0,
        "root",
        tuple(command),
        root,
        cell_environment(Path(command[0]), root / "output/readiness/early-zero", repo_root=root),
        60,
        True,
    )
    observed = run_project_test_matrix([task], workers=1)[0]
    assert observed.returncode == 0 and not observed.timed_out
    details["cell_process_artifact"] = write_json(
        root,
        root / "output/readiness/early-zero/process.json",
        {
            **asdict(observed),
            "command": command,
            "run_id": original["run_id"],
            "spec_artifact": original["spec_artifact"],
        },
    )
    with pytest.raises(ValueError):
        validate_acceptance(requirement, {"details": details}, SnapshotReader(root))


@pytest.mark.parametrize("scope", ["working/private", "templates/unknown", "../root", "projects/root"])
def test_root_runtime_scope_refuses_private_and_invented_projects(tmp_path: Path, scope: str) -> None:
    with pytest.raises(ValueError):
        RuntimeScope(tmp_path, scope)


@pytest.mark.parametrize("fault", ["source", "minor", "missing-case", "replayed-process"])
def test_independent_root_reader_refuses_source_case_and_original_process_tampering(
    actual_root_evidence, fault: str
) -> None:
    root, requirement, _, originals = actual_root_evidence
    details = copy.deepcopy(originals[0])
    if fault == "source":
        path = root / "conftest.py"
        original = path.read_bytes()
        path.write_bytes(original + b"\nCHANGED_SOURCE = True\n")
        try:
            with pytest.raises(ValueError):
                validate_acceptance(requirement, {"details": details}, SnapshotReader(root))
        finally:
            path.write_bytes(original)
        return
    if fault == "minor":
        details["python_version"] = "3.12" if requirement.python_version != "3.12" else "3.13"
    elif fault == "missing-case":
        details["case_artifacts"] = []
    else:
        details["cell_process_artifact"] = details["pytest_process_artifacts"][0]
    with pytest.raises(ValueError):
        validate_acceptance(requirement, {"details": details}, SnapshotReader(root))
