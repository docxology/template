"""Real-process whole-collection, selected-runtime and custody matrix controls."""

from __future__ import annotations

import json
import os
import py_compile
import sys
from pathlib import Path
from dataclasses import asdict

import pytest

from infrastructure.core.testing.project_test_matrix import ProjectTestTask, run_project_test_matrix
from infrastructure.core.testing.pytest_profiles import TEST_RUNNER_BASE_DEPS
from infrastructure.project.public_acceptance import _probe_runtime, _record_cell, run_public_acceptance
from infrastructure.project.public_acceptance_evidence import (
    aggregate_pytest,
    bootstrap_command,
    cell_environment,
    evidence_directory,
    runtime_identity,
    write_json,
)
from infrastructure.project.public_acceptance_cases import project_python_hashes
from infrastructure.reporting.readiness_receipts import deliverable_identity, project_source_identity
from infrastructure.reporting.release_readiness_profile import Requirement

ROOT = Path(__file__).resolve().parents[3]
PROJECT = "templates/template_code_project"
pytestmark = pytest.mark.timeout(240)


def _cell(
    tmp_path: Path,
    body: str,
    *,
    extra: str = "",
    addopts: str = "",
    timeout: int = 90,
    planner: str | None = None,
    metadata_prefix: str = "",
    root_conftest: str | None = None,
) -> dict:
    project = tmp_path / "projects" / PROJECT
    (project / "src").mkdir(parents=True, exist_ok=True)
    (project / "tests").mkdir(exist_ok=True)
    (project / "src/model.py").write_text("def absolute(x):\n    if x < 0:\n        return -x\n    return x\n")
    (project / "tests/test_model.py").write_text(body)
    if root_conftest is not None:
        (project / "conftest.py").write_text(root_conftest)
    if planner is not None:
        (project / "src/partition.py").write_text(planner)
        extra += 'acceptance_test_groups="partition:groups"\n'
    (project / "pyproject.toml").write_text(
        metadata_prefix + '[tool.pytest.ini_options]\npythonpath=["src"]\naddopts=' + json.dumps(addopts) + "\n"
        '[tool.coverage.run]\nsource=["src"]\nbranch=true\n[tool.template]\n' + extra
    )
    directory = tmp_path / "output/readiness/cell"
    spec = {
        "root": str(tmp_path),
        "scope": PROJECT,
        "directory": directory.relative_to(tmp_path).as_posix(),
        "run_id": "fresh-cell",
        "runtime": runtime_identity(),
        "source_identity": project_source_identity(tmp_path, PROJECT),
        "deliverables_identity": deliverable_identity(tmp_path, PROJECT),
        "test_files": [f"projects/{PROJECT}/tests/test_model.py"],
        "timeout_seconds": timeout,
        "test_timeout_seconds": 2,
    }
    spec_binding = write_json(tmp_path, directory / "spec.json", spec)
    command = bootstrap_command(
        Path(sys.executable),
        tmp_path,
        "infrastructure.project.public_acceptance_worker",
        "--root",
        str(tmp_path),
        "--spec",
        str(directory / "spec.json"),
        "--spec-sha256",
        spec_binding["sha256"],
    )
    result = run_project_test_matrix(
        [
            ProjectTestTask(
                # The cell budget covers fresh collection, execution and final
                # custody. The outer observer also allows finite guardian cleanup.
                0,
                PROJECT,
                command,
                tmp_path,
                cell_environment(Path(sys.executable), directory),
                timeout + 60,
                True,
            )
        ],
        workers=1,
    )[0]
    assert not result.timed_out, result
    write_json(
        tmp_path,
        directory / "cell-process.json",
        {
            **asdict(result),
            "command": list(command),
            "run_id": "fresh-cell",
            "spec_artifact": spec_binding,
        },
    )
    raw = json.loads((directory / "cell.json").read_text())
    return {"process": result, "raw": raw, "directory": directory, "command": command}


GOOD = "from model import absolute\ndef test_positive():\n    assert absolute(1)==1\ndef test_negative():\n    assert absolute(-1)==1\n"


def test_fresh_bootstrap_cannot_consume_valid_timestamp_poisoned_source_cache(tmp_path: Path) -> None:
    module = tmp_path / "scientific_model.py"
    original = b"VALUE=17\n" + b" " * 100
    module.write_bytes(original)
    metadata = module.stat()
    malicious = b"raise SystemExit(77)\n".ljust(len(original), b" ")
    module.write_bytes(malicious)
    os.utime(module, ns=(metadata.st_atime_ns, metadata.st_mtime_ns))
    py_compile.compile(str(module), doraise=True, invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP)
    module.write_bytes(original)
    os.utime(module, ns=(metadata.st_atime_ns, metadata.st_mtime_ns))
    (tmp_path / "probe.py").write_text(
        "from scientific_model import VALUE\nfrom pathlib import Path\n"
        "assert VALUE==17\nPath('observed.txt').write_text(str(VALUE))\n"
    )
    env = cell_environment(Path(sys.executable), tmp_path / "evidence")
    ordinary = (
        sys.executable,
        "-I",
        "-c",
        "import sys;sys.path.insert(0,sys.argv[1]);import scientific_model",
        str(tmp_path),
    )
    first = run_project_test_matrix([ProjectTestTask(0, "poison-control", ordinary, tmp_path, env, 10, True)])[0]
    assert first.returncode == 77 and not first.timed_out
    fresh = bootstrap_command(Path(sys.executable), tmp_path, "probe")
    second = run_project_test_matrix([ProjectTestTask(0, "fresh-control", fresh, tmp_path, env, 10, True)])[0]
    assert second.returncode == 0 and not second.timed_out, second.output_tail
    assert (tmp_path / "observed.txt").read_text() == "17"
    assert module.read_bytes() == original


def test_real_cell_passes_complete_cases_and_own_branch_coverage(tmp_path: Path) -> None:
    observed = _cell(tmp_path, GOOD)
    assert observed["process"].returncode == 0
    raw = observed["raw"]
    assert raw["status"] == "pass"
    assert (raw["collected"], raw["passed"], raw["groups"]) == (2, 2, 1)
    assert raw["coverage"]["percent"] == 100
    assert raw["coverage"]["branch_coverage"] is True
    assert raw["source_identity_after"] == raw["source_identity"]


def test_root_conftest_is_admitted_audited_and_executes_in_genuine_cell(tmp_path: Path) -> None:
    marker = tmp_path / "output/readiness/root-conftest.txt"
    conftest = f"from pathlib import Path\nPath({str(marker)!r}).write_text('original root conftest')\n"
    observed = _cell(tmp_path, GOOD, root_conftest=conftest)
    assert observed["process"].returncode == 0, observed["process"].output_tail
    assert observed["raw"]["status"] == "pass"
    assert marker.read_text() == "original root conftest"
    relative = f"projects/{PROJECT}/conftest.py"
    hashes = project_python_hashes(tmp_path, PROJECT)
    assert relative in hashes
    for name in ("collection.json", "chunk-001.json"):
        receipt = json.loads((observed["directory"] / name).read_text())
        assert receipt["pytest_exit_code"] == receipt["exit_code"] == 0
        assert receipt["source_hashes_before"][relative] == hashes[relative]
        assert receipt["source_hashes_after"][relative] == hashes[relative]


def test_restored_root_conftest_bytes_cannot_hide_actual_changed_execution(tmp_path: Path) -> None:
    marker = tmp_path / "output/readiness/changed-root-conftest.txt"
    replacement = f"from pathlib import Path\nPath({str(marker)!r}).write_text('changed root code executed')\n"
    conftest = (
        "import importlib.util\nfrom pathlib import Path\n"
        "owned=Path(__file__)\noriginal=owned.read_bytes()\n"
        f"owned.write_text({replacement!r})\n"
        "try:\n"
        "    spec=importlib.util.spec_from_file_location('_transient_root_conftest',owned)\n"
        "    module=importlib.util.module_from_spec(spec)\n"
        "    spec.loader.exec_module(module)\n"
        "finally:\n    owned.write_bytes(original)\n"
    )
    observed = _cell(tmp_path, GOOD, root_conftest=conftest)
    assert marker.read_text() == "changed root code executed", "the genuine replacement import must have executed"
    assert (tmp_path / "projects" / PROJECT / "conftest.py").read_text() == conftest
    assert observed["raw"]["source_identity_after"] == observed["raw"]["source_identity"]
    assert observed["process"].returncode == 1 and observed["raw"]["status"] == "fail"
    receipt = json.loads((observed["directory"] / "collection.json").read_text())
    assert receipt["pytest_exit_code"] == 0, "collection itself succeeds; executed-bytecode custody must refuse"
    assert receipt["exit_code"] == 1
    assert "executed public module differs" in receipt["diagnostic"] or "execution-time bytes" in receipt["diagnostic"]


@pytest.mark.parametrize(
    "body,reason",
    [
        (GOOD + "def test_failure():\n    assert False\n", "failed"),
        (GOOD + "import pytest\ndef test_unavailable():\n    pytest.skip('missing actual tool')\n", "skipped"),
        ("import missing_real_module\n", "collection"),
        ("VALUE=1\n", "empty"),
        (
            "import pytest\n@pytest.fixture\ndef broken():\n    yield\n    raise RuntimeError('real teardown')\n"
            "def test_teardown(broken):\n    pass\n",
            "failed",
        ),
    ],
)
def test_real_cell_cannot_hide_failed_skipped_empty_or_partial_cases(tmp_path: Path, body: str, reason: str) -> None:
    observed = _cell(tmp_path, body)
    assert observed["process"].returncode != 0
    assert observed["raw"]["status"] == "fail"
    assert reason in observed["raw"]["diagnostic"].lower()


def test_source_owned_addopts_cannot_silently_exclude_a_failing_case(tmp_path: Path) -> None:
    observed = _cell(tmp_path, GOOD + "def test_bad():\n    assert False\n", addopts="-k positive")
    assert observed["raw"]["collected"] == 3
    assert observed["raw"]["failed"] == 1
    assert observed["raw"]["deselected"] == 0
    assert observed["raw"]["status"] == "fail"


@pytest.mark.parametrize(
    "groups",
    [
        "[('positive',['tests/test_model.py::test_positive'])]",
        "[('one',['tests/test_model.py']),('duplicate',['tests/test_model.py'])]",
    ],
)
def test_declared_real_chunk_planner_cannot_omit_or_duplicate_cases(tmp_path: Path, groups: str) -> None:
    observed = _cell(tmp_path, GOOD, planner="def groups(root):\n    return " + groups + "\n")
    assert observed["raw"]["status"] == "fail"
    assert "omit, duplicate" in observed["raw"]["diagnostic"]


def test_parent_oracle_reads_real_case_union_and_rejects_foreign_coverage_scope(tmp_path: Path) -> None:
    observed = _cell(tmp_path, GOOD)
    raw = observed["raw"]
    directory = observed["directory"]
    probe = _probe_runtime(tmp_path, tmp_path / "output/readiness/probe", raw["python_version"], Path(sys.executable))
    common = {
        "scope": PROJECT,
        "version": "1.0.0",
        "platform_version": "4.0.0",
        "source_identity": raw["source_identity"],
        "deliverables_identity": raw["deliverables_identity"],
        "python_version": raw["python_version"],
        "test_files": tuple(raw["test_files"]),
    }
    runtime = Requirement("runtime", "runtime", source_files=(f"projects/{PROJECT}/src/model.py",), **common)
    coverage = Requirement("coverage", "coverage", source_files=(f"projects/{PROJECT}/src/model.py",), **common)
    first, second, summary = _record_cell(
        tmp_path,
        directory,
        runtime,
        coverage,
        "a" * 64,
        observed["command"],
        0,
        probe,
        "fresh-cell",
    )
    assert first["status"] == second["status"] == summary["status"] == "pass"
    foreign = Requirement(
        "coverage", "coverage", source_files=("projects/templates/template_other/src/model.py",), **common
    )
    first, second, summary = _record_cell(
        tmp_path, directory, runtime, foreign, "a" * 64, ["actual-command"], 0, probe, "fresh-cell"
    )
    assert first["status"] == "pass" and second["status"] == "fail" and summary["status"] == "fail"
    first, second, summary = _record_cell(
        tmp_path, directory, runtime, coverage, "a" * 64, ["actual-command"], 0, probe, "stale-run"
    )
    assert first["status"] == second["status"] == summary["status"] == "fail"


def test_real_cell_refuses_source_edits_even_after_tests_pass(tmp_path: Path) -> None:
    observed = _cell(
        tmp_path,
        GOOD + "from pathlib import Path\ndef test_mutation():\n"
        "    Path('src/model.py').write_text('def altered(): return 4\\n')\n",
    )
    assert observed["raw"]["status"] == "fail"
    assert "changed during runtime cell" in observed["raw"]["diagnostic"]


def test_real_cell_deadline_fails_without_granting_partial_acceptance(tmp_path: Path) -> None:
    observed = _cell(tmp_path, "import time\ndef test_hang():\n    time.sleep(20)\n", timeout=5)
    assert observed["process"].returncode != 0
    assert observed["raw"]["status"] == "fail"


def test_real_runtime_probe_matches_minor_and_missing_python_is_blocked(tmp_path: Path) -> None:
    minor = f"{sys.version_info.major}.{sys.version_info.minor}"
    valid = _probe_runtime(tmp_path, tmp_path / "output/readiness/probe", minor, Path(sys.executable))
    assert valid["status"] == "pass"
    assert valid["runtime"]["executable"] == sys.executable
    mismatch = _probe_runtime(tmp_path, tmp_path / "output/readiness/wrong", "3.9", Path(sys.executable))
    assert mismatch["status"] == "fail"
    missing = _probe_runtime(tmp_path, tmp_path / "output/readiness/missing", "3.12", None)
    assert missing["status"] == "blocked"
    assert missing["blockers"][0]["tool"] == "Python 3.12"


def test_bare_real_environment_records_missing_test_tools_without_installing(tmp_path: Path) -> None:
    env_path = tmp_path / "bare"
    result = run_project_test_matrix(
        [
            ProjectTestTask(
                0, "bare-env", (sys.executable, "-m", "venv", "--without-pip", str(env_path)), tmp_path, {}, 30, True
            )
        ],
        workers=1,
    )[0]
    assert result.returncode == 0
    minor = f"{sys.version_info.major}.{sys.version_info.minor}"
    observed = _probe_runtime(tmp_path, tmp_path / "output/readiness/bare", minor, env_path / "bin/python")
    assert observed["status"] == "blocked"
    assert {row["tool"] for row in observed["blockers"]} == {*TEST_RUNNER_BASE_DEPS, "coverage"}


def test_case_union_refuses_duplicate_or_missing_chunks() -> None:
    baseline = {
        "schema_version": "template-public-pytest-v2",
        "run_id": "new",
        "exit_code": 0,
        "nodeids": ["a", "b"],
        "collection_errors": [],
        "collection_skips": [],
        "deselected": [],
    }
    group = {**baseline, "nodeids": ["a"], "outcomes": {"a": "passed"}}
    with pytest.raises(ValueError, match="omit, duplicate"):
        aggregate_pytest(baseline, [group], "new")
    with pytest.raises(ValueError, match="omit, duplicate"):
        aggregate_pytest(baseline, [group, group], "new")
    with pytest.raises(ValueError, match="stale"):
        aggregate_pytest(baseline, [group], "old")


def test_evidence_preflight_refuses_traversal_and_symlink_before_any_write(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    with pytest.raises(ValueError, match="canonical"):
        evidence_directory(root, root / "output/readiness/../../infrastructure/new-dir", fresh=True)
    external = root / "external"
    external.mkdir()
    readiness = root / "output/readiness"
    readiness.parent.mkdir()
    readiness.symlink_to(external, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        write_json(root, readiness / "escaped.json", {"status": "fixture"})
    assert list(external.iterdir()) == []


@pytest.mark.parametrize(
    "kwargs",
    [
        {"project_workers": 4},
        {"project_workers": True},
        {"timeout_seconds": 0},
        {"test_timeout_seconds": float("inf")},
        {"projects": []},
        {"projects": ["working/private"]},
    ],
)
def test_matrix_rejects_unbounded_or_nonpublic_selection_before_execution(tmp_path: Path, kwargs: dict) -> None:
    with pytest.raises(ValueError):
        run_public_acceptance(tmp_path, {}, **kwargs)
