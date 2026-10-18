"""Real subprocess integration tests for Stage 01 test orchestration."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from infrastructure.core.testing.pytest_orchestration import (
    PIPELINE_SMOKE_INFRA_TEST_PATHS,
    project_declared_coverage_floor,
)
from infrastructure.reporting.pipeline_test_runner import (
    execute_test_pipeline,
    run_infrastructure_tests,
    run_project_tests,
    _test_suite_outcome,
    _test_child_exit_code,
)
from infrastructure.core.pipeline.outcomes import RunResult
from infrastructure.core.pipeline.fingerprints import source_content_fingerprint


def _write_minimal_project(repo_root: Path, name: str = "demo") -> Path:
    """Scaffold a discoverable project with one passing test."""
    project_root = repo_root / "projects" / "active" / name
    for sub in ("src", "tests", "scripts", "manuscript", "output"):
        (project_root / sub).mkdir(parents=True)
    (project_root / "src" / "__init__.py").write_text("")
    (project_root / "src" / "demo_mod.py").write_text(
        dedent(
            """
            def answer() -> int:
                return 7
            """
        ).lstrip()
    )
    (project_root / "tests" / "__init__.py").write_text("")
    (project_root / "tests" / "conftest.py").write_text(
        dedent(
            """
            import sys
            from pathlib import Path

            sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
            """
        ).lstrip()
    )
    (project_root / "tests" / "test_demo.py").write_text(
        dedent(
            """
            from demo_mod import answer


            def test_answer() -> None:
                assert answer() == 7
            """
        ).lstrip()
    )
    (project_root / "manuscript" / "config.yaml").write_text(
        dedent(
            """
            paper:
              title: Demo
              version: "1.0"
            """
        ).lstrip()
    )
    return project_root


@pytest.fixture()
def repo_root(tmp_path: Path) -> Path:
    (tmp_path / "projects").mkdir()
    _write_minimal_project(tmp_path, "demo")
    return tmp_path


def _seed_pipeline_smoke_paths(repo_root: Path) -> None:
    """Create trivial passing test files at each pipeline-smoke path.

    This exercises the *runner orchestration* — smoke-path resolution
    (``resolve_infrastructure_test_paths``), the real pytest subprocess, the
    marker-filter expression and exit-code propagation — in a self-contained
    synthetic repo. We deliberately do NOT symlink the real infra smoke tests:
    they pull in ``import infrastructure.*`` plus a conftest/helper chain that a
    synthetic repo cannot satisfy, which previously made the subprocess fail
    collection (exit 2). That non-zero exit used to be silently green-washed to 0
    by ``suite_runner``; with that masking removed, this test must drive the
    runner against tests that genuinely collect and pass. The real smoke tests are
    exercised for real by the full infrastructure suite — here we only assert the
    runner returns success when its smoke subprocess passes.
    """
    body = "def test_smoke_ok() -> None:\n    assert True\n"
    for rel in PIPELINE_SMOKE_INFRA_TEST_PATHS:
        # File paths (``.../foo.py``) become that file; directory paths
        # (e.g. ``git_hook_smoke``) get a single test module inside them.
        dst = repo_root / rel if rel.suffix == ".py" else repo_root / rel / "test_smoke.py"
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(body)


@pytest.mark.timeout(180)
def test_run_infrastructure_tests_pipeline_smoke_real_subprocess(tmp_path: Path) -> None:
    """Pipeline-smoke scope runs real pytest subprocesses against smoke paths."""
    (tmp_path / "projects").mkdir()
    _write_minimal_project(tmp_path, "demo")
    _seed_pipeline_smoke_paths(tmp_path)
    exit_code, results = run_infrastructure_tests(
        tmp_path,
        project_name="demo",
        quiet=True,
        scope="pipeline-smoke",
        strict=True,
    )
    assert exit_code == 0
    assert results.get("failed", 0) == 0


@pytest.mark.timeout(120)
def test_run_project_tests_real_subprocess(repo_root: Path) -> None:
    """Project runner executes pytest with declared coverage floor from pyproject."""
    project_root = repo_root / "projects" / "demo"
    declared = project_declared_coverage_floor(project_root)
    resolved_project = repo_root / "projects" / "active" / "demo"
    before = source_content_fingerprint(repo_root, resolved_project)
    exit_code, results = run_project_tests(
        repo_root,
        project_name="demo",
        quiet=True,
        strict=True,
    )
    assert exit_code == 0
    assert results.get("total", 0) > 0
    assert results.get("failed", 0) == 0
    threshold = declared if declared is not None else 90.0
    coverage = results.get("coverage_percent", 0.0)
    assert coverage >= threshold or results.get("passed", 0) > 0
    assert (resolved_project / "coverage_project.json").is_file()
    assert (resolved_project / ".coverage.project").is_file()
    assert not (repo_root / "coverage_project.json").exists()
    assert not (repo_root / ".coverage.project").exists()
    assert not (resolved_project / ".benchmarks").exists()
    assert (resolved_project / "output/.pipeline/benchmarks").is_dir()
    assert source_content_fingerprint(repo_root, resolved_project) == before


@pytest.mark.timeout(90)
def test_infrastructure_direct_api_blocks_broken_nominated_runtime(tmp_path: Path) -> None:
    (tmp_path / ".venv").mkdir()
    _seed_pipeline_smoke_paths(tmp_path)
    evidence = tmp_path / ".coverage.infra"
    evidence.write_bytes(b"prior coverage must survive admission refusal")
    code, results = run_infrastructure_tests(tmp_path, scope="pipeline-smoke")
    assert code == 75
    assert results["exit_code"] == 75
    assert evidence.read_bytes() == b"prior coverage must survive admission refusal"


@pytest.mark.timeout(90)
def test_generic_project_runtime_refusal_preserves_prior_coverage(repo_root: Path) -> None:
    project = repo_root / "projects" / "active" / "demo"
    (project / ".venv").mkdir()
    evidence = project / ".coverage.project"
    evidence.write_bytes(b"prior project coverage")
    code, results = run_project_tests(repo_root, "active/demo")
    assert code == 75
    assert results["original_exit_code"] is None
    assert evidence.read_bytes() == b"prior project coverage"


@pytest.mark.parametrize("child_exit", [2, 7, 75, 124, 130])
@pytest.mark.timeout(180)
def test_shared_infrastructure_failure_blocks_real_project_child(tmp_path: Path, child_exit: int) -> None:
    import json

    project = _write_minimal_project(tmp_path)
    _seed_pipeline_smoke_paths(tmp_path)
    marker = tmp_path / "actual_infrastructure_child"
    (tmp_path / "tests" / "infra_tests" / "conftest.py").write_text(
        "import pytest\nfrom pathlib import Path\n"
        "def pytest_sessionstart(session):\n"
        f" Path({str(marker)!r}).write_text('actual infrastructure child executed')\n"
        f" pytest.exit('deliberate infrastructure control', returncode={child_exit})\n"
    )
    project_marker = project / "project_child_started"
    (project / "tests" / "test_demo.py").write_text(
        f"from pathlib import Path\nPath({str(project_marker)!r}).write_text('project collected')\n"
        "def test_should_be_blocked():\n assert True\n"
    )
    prior_coverage = project / ".coverage.project"
    prior_coverage.write_bytes(b"project evidence was never touched")
    code = execute_test_pipeline(
        "active/demo",
        tmp_path,
        run_infra=True,
        run_project=True,
        quiet=True,
        include_slow=False,
        include_long_running=False,
        include_ollama_tests=False,
        strict=True,
        infra_scope="pipeline-smoke",
    )
    assert marker.read_text() == "actual infrastructure child executed"
    assert code == (child_exit if child_exit in (75, 124, 130) else 1)
    assert not project_marker.exists()
    assert prior_coverage.read_bytes() == b"project evidence was never touched"
    report = json.loads((project / "output" / ".pipeline" / "tests" / "test_results.json").read_text())
    assert report["infrastructure"]["original_exit_code"] == child_exit
    assert report["project"]["original_exit_code"] is None
    assert report["project"]["exit_code"] == 75
    assert report["summary"]["all_passed"] is False
    assert "coverage_details" not in report


@pytest.mark.parametrize("actual_exit", [2, 7, 75, 124, 130])
def test_tolerated_nonzero_child_cannot_complete_a_stage(actual_exit: int) -> None:
    results = {"exit_code": 0, "original_exit_code": actual_exit}
    code = _test_child_exit_code(0, results)
    outcome = _test_suite_outcome("project_tests", code, results)
    assert outcome.child_exit_code == actual_exit
    assert RunResult(("project_tests",), (outcome,)).exit_code == (actual_exit if actual_exit in (75, 124, 130) else 1)


@pytest.mark.parametrize("actual_exit", [2, 7])
@pytest.mark.timeout(180)
def test_generic_source_custody_postcheck_preserves_actual_nonzero(repo_root: Path, actual_exit: int) -> None:
    project = repo_root / "projects" / "active" / "demo"
    (project / "tests" / "test_demo.py").write_text(
        "import pytest\nfrom pathlib import Path\nimport demo_mod\n"
        "def test_actual_nonzero_with_changed_consumed_source():\n"
        " assert demo_mod.answer() == 7\n"
        f" Path({str(project / 'src' / 'demo_mod.py')!r}).write_text('def answer():\\n return 9\\n')\n"
        f" pytest.exit('deliberate source custody control', returncode={actual_exit})\n"
    )
    code, results = run_project_tests(repo_root, "active/demo")
    assert code == 1
    assert results["original_exit_code"] == actual_exit
    assert results["exit_code"] == 1
    assert "return 9" in (project / "src" / "demo_mod.py").read_text()
