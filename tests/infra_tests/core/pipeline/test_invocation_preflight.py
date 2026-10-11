"""Real entry points reject invalid producer plans before runtime artifacts."""

from __future__ import annotations

import io
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from infrastructure.core.execution_boundary import build_bounded_env
from infrastructure.core.pipeline.run_matrix import RunConfigError, parse_run_config, resolve_run_plan
from infrastructure.core.pipeline.single_stage import execute_single_stage
from infrastructure.orchestration.pipeline_runner import MultiProjectInvocation, PipelineInvocation, PipelineRunner
from scripts.runner.execute_pipeline import execute_pipeline
from tests.infra_tests.orchestration._pipeline_fixture import scaffold_pipeline

_ENTRY_POINTS = ("canonical", "single", "matrix", "runner", "multi")
_REPOSITORY = Path(__file__).absolute().parents[4]


def _output_snapshot(root: Path) -> dict[str, bytes | None]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes() if path.is_file() else None
        for output in (root / "output", root / "projects/demo/output")
        if output.exists()
        for path in (output, *output.rglob("*"))
    }


def _invoke(root: Path, entry_point: str) -> int:
    runner = PipelineRunner(root, stream=io.StringIO())
    if entry_point == "canonical":
        return execute_pipeline("demo", root, resume=True)
    if entry_point == "single":
        return execute_single_stage("analysis", "demo", root)
    if entry_point == "matrix":
        config = parse_run_config("runs:\n  - project: demo\n    stages: [analysis]\n")
        with pytest.raises(RunConfigError):
            resolve_run_plan(config, root)
        return 2
    if entry_point == "runner":
        return runner.run(PipelineInvocation("demo", resume=True))
    return runner.run_multi(MultiProjectInvocation())


@pytest.fixture
def repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("ANALYSIS_SCRIPT_TIMEOUT_SEC", "60")
    scaffold_pipeline(tmp_path)
    previous = tmp_path / "projects/demo/output/.pipeline/execution.json"
    previous.parent.mkdir()
    previous.write_bytes(b'{"historical_control_evidence":true}\n')
    return tmp_path


@pytest.mark.parametrize("entry_point", _ENTRY_POINTS)
@pytest.mark.parametrize("timeout", ["0", "NaN", "inf", "unlimited", "-1"])
def test_invalid_analysis_timeout_precedes_all_runtime_writes(
    repository: Path, monkeypatch: pytest.MonkeyPatch, entry_point: str, timeout: str
) -> None:
    before = _output_snapshot(repository)
    monkeypatch.setenv("ANALYSIS_SCRIPT_TIMEOUT_SEC", timeout)
    assert _invoke(repository, entry_point) == 2
    assert _output_snapshot(repository) == before
    assert not (repository / "process_order.log").exists()


@pytest.mark.parametrize("entry_point", _ENTRY_POINTS)
@pytest.mark.parametrize("scripts", [["missing.py"], [17], ["../escaped.py"]])
def test_invalid_declared_analysis_producers_precede_all_runtime_writes(
    repository: Path, entry_point: str, scripts: list[object]
) -> None:
    config = repository / "projects/demo/manuscript/config.yaml"
    config.write_text(yaml.safe_dump({"analysis": {"scripts": scripts}}))
    before = _output_snapshot(repository)
    assert _invoke(repository, entry_point) == 2
    assert _output_snapshot(repository) == before
    assert not (repository / "process_order.log").exists()


def test_matrix_preflight_is_read_only_for_valid_selected_plan(repository: Path) -> None:
    before = _output_snapshot(repository)
    config = parse_run_config("runs:\n  - project: demo\n    stages: [analysis]\n")
    plan = resolve_run_plan(config, repository)
    assert tuple(step.stage for step in plan.steps) == ("analysis",)
    assert _output_snapshot(repository) == before
    assert not (repository / "process_order.log").exists()


def test_unselected_analysis_configuration_does_not_change_matrix_selection(
    repository: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ANALYSIS_SCRIPT_TIMEOUT_SEC", "unlimited")
    before = _output_snapshot(repository)
    config = parse_run_config("runs:\n  - project: demo\n    stages: [infra_tests]\n")
    plan = resolve_run_plan(config, repository)
    assert tuple(step.stage for step in plan.steps) == ("infra_tests",)
    assert _output_snapshot(repository) == before
    assert not (repository / "process_order.log").exists()


def test_multi_empty_project_selection_precedes_runtime_logging(repository: Path) -> None:
    declaration = repository / "infrastructure/core/pipeline/pipeline.yaml"
    document = yaml.safe_load(declaration.read_text())
    document["stages"] = document["stages"][:1]
    declaration.write_text(yaml.safe_dump(document))
    before = _output_snapshot(repository)
    assert PipelineRunner(repository, stream=io.StringIO()).run_multi(MultiProjectInvocation()) == 2
    assert _output_snapshot(repository) == before
    assert not (repository / "process_order.log").exists()


@pytest.mark.parametrize("invalid", ["timeout", "producer"])
def test_actual_matrix_dry_run_cli_refuses_before_runtime_writes(
    repository: Path, tmp_path: Path, invalid: str
) -> None:
    config = repository / "run.config"
    config.write_text("runs:\n  - project: demo\n    stages: [analysis]\n")
    environment = build_bounded_env()
    if invalid == "timeout":
        environment["ANALYSIS_SCRIPT_TIMEOUT_SEC"] = "unlimited"
    else:
        (repository / "projects/demo/manuscript/config.yaml").write_text("analysis:\n  scripts: [missing.py]\n")
    before = _output_snapshot(repository)
    cache = tmp_path / "cli-bytecode"
    cache.mkdir(mode=0o700)
    bootstrap = (
        "import sys;sys.path.insert(0,sys.argv.pop(1));"
        "from scripts.runner.run_matrix import main;raise SystemExit(main(sys.argv[1:]))"
    )
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-X",
            f"pycache_prefix={cache}",
            "-c",
            bootstrap,
            str(_REPOSITORY),
            "--repo-root",
            str(repository),
            "--config",
            str(config),
            "--dry-run",
        ],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 2, result.stdout + result.stderr
    assert "ERROR:" in result.stderr
    assert _output_snapshot(repository) == before
    assert not (repository / "process_order.log").exists()


@pytest.mark.parametrize(
    ("kind", "method"),
    [
        ("missing", None),
        ("non_python", None),
        ("linked", None),
        ("method", "run_analysis"),
        ("method", "_run_script"),
        ("method", "config"),
        ("ignored_args", "_run_clean_outputs"),
        ("ignored_args", "run_project_tests"),
        ("ignored_args", "run_infrastructure_tests"),
    ],
)
@pytest.mark.timeout(90)
def test_actual_canonical_cli_rejects_unavailable_targets_and_ignored_method_args_before_writes(
    repository: Path, tmp_path: Path, kind: str, method: str | None
) -> None:
    # Execute an exact copy of the actual thin CLI so its own location nominates
    # this disposable repository. No runtime dependency or function is replaced.
    entry = repository / "scripts/runner/execute_pipeline.py"
    entry.parent.mkdir()
    shutil.copyfile(_REPOSITORY / "scripts/runner/execute_pipeline.py", entry)
    assert entry.read_bytes() == (_REPOSITORY / "scripts/runner/execute_pipeline.py").read_bytes()
    stage: dict[str, object] = {"name": "Domain", "key": "domain"}
    if method is not None:
        stage["method"] = method
        if kind == "ignored_args":
            stage["args"] = ["ignored-before-4"]
    else:
        target = repository / ("scripts/target.sh" if kind == "non_python" else "scripts/target.py")
        if kind == "linked":
            external = tmp_path / "unadmitted.py"
            external.write_text("from pathlib import Path\nPath('forbidden-child').touch()\n")
            target.symlink_to(external)
        elif kind == "non_python":
            target.write_text("from pathlib import Path\nPath('forbidden-child').touch()\n")
        stage["script"] = target.relative_to(repository).as_posix()
    definition = repository / "projects/demo/pipeline.yaml"
    definition.write_text(yaml.safe_dump({"stages": [stage]}))
    before = _output_snapshot(repository)
    cache = tmp_path / "canonical-cli-bytecode"
    cache.mkdir(mode=0o700)
    bootstrap = (
        "import runpy,sys;sys.path.insert(0,sys.argv.pop(1));"
        "entry=sys.argv.pop(1);sys.argv[0]=entry;runpy.run_path(entry,run_name='__main__')"
    )
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-X",
            f"pycache_prefix={cache}",
            "-c",
            bootstrap,
            str(_REPOSITORY),
            str(entry),
            "--project",
            "demo",
            "--stage",
            "domain",
            "--pipeline-yaml",
            str(definition),
        ],
        cwd=repository,
        env=build_bounded_env(),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 2, result.stdout + result.stderr
    assert "Invalid stage invocation:" in result.stdout + result.stderr
    assert _output_snapshot(repository) == before
    assert not (repository / "process_order.log").exists()
    assert not (repository / "forbidden-child").exists()
