"""Real candidate epochs and fail-closed canonical execution policy."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from infrastructure.core.execution_policy import apply_execution_policy
from infrastructure.core.pipeline.execution_environment import effective_environment_identity
from infrastructure.core.pipeline.executor import PipelineExecutor
from infrastructure.core.pipeline.types import PipelineConfig


def _candidate(root: Path) -> str:
    root.mkdir(exist_ok=True)
    environment = dict(
        os.environ, GIT_AUTHOR_DATE="2023-11-14T22:13:20 +0000", GIT_COMMITTER_DATE="2023-11-14T22:13:20 +0000"
    )
    for command in (
        ["git", "init"],
        ["git", "config", "user.email", "fixture@example.invalid"],
        ["git", "config", "user.name", "Fixture"],
    ):
        subprocess.run(command, cwd=root, env=environment, check=True, capture_output=True, timeout=10)
    (root / "candidate.txt").write_text("reference candidate\n")
    subprocess.run(["git", "add", "candidate.txt"], cwd=root, env=environment, check=True, timeout=10)
    subprocess.run(
        ["git", "commit", "-m", "Reference candidate"],
        cwd=root,
        env=environment,
        check=True,
        capture_output=True,
        timeout=10,
    )
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, env=environment, check=True, capture_output=True, text=True, timeout=10
    )
    return result.stdout.strip()


def test_default_execution_uses_exact_nominated_candidate_and_ignores_ambient_git(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate"
    revision = _candidate(candidate)
    foreign = tmp_path / "foreign"
    _candidate(foreign)
    environment = {"PATH": os.environ["PATH"], "GIT_DIR": str(foreign / ".git"), "GIT_WORK_TREE": str(foreign)}
    policy = apply_execution_policy(environment, candidate)
    assert policy["SOURCE_DATE_EPOCH"] == "1700000000"
    assert policy["TEMPLATE_BUILD_EPOCH_SOURCE"] == "git:" + revision
    assert policy["TEMPLATE_EXECUTION_MODE"] == "core"
    assert policy["TEMPLATE_DETERMINISTIC"] == "1"
    assert apply_execution_policy(environment, candidate) == policy
    assert environment.get("SOURCE_DATE_EPOCH") is None


def test_export_cannot_borrow_parent_git_epoch(tmp_path: Path) -> None:
    _candidate(tmp_path)
    exported = tmp_path / "export"
    exported.mkdir()
    with pytest.raises(ValueError, match="set SOURCE_DATE_EPOCH explicitly"):
        apply_execution_policy({"PATH": os.environ["PATH"]}, exported)
    assert (
        apply_execution_policy({"SOURCE_DATE_EPOCH": "1700000000"}, exported)["TEMPLATE_BUILD_EPOCH_SOURCE"]
        == "explicit"
    )


def test_replacement_refs_cannot_change_the_original_candidate_epoch(tmp_path: Path) -> None:
    from infrastructure.documentation.counts_coverage import _run_coverage_git

    candidate = tmp_path / "candidate"
    original = _candidate(candidate)
    native_tree = subprocess.run(
        ["git", "rev-parse", "HEAD^{tree}"], cwd=candidate, text=True, capture_output=True, check=True, timeout=10
    ).stdout.strip()
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update(GIT_AUTHOR_DATE="2023-11-14T22:13:21 +0000", GIT_COMMITTER_DATE="2023-11-14T22:13:21 +0000")
    (candidate / "candidate.txt").write_text("owned replacement candidate\n")
    commands = (["add", "candidate.txt"], ["commit", "-m", "Owned replacement candidate"])
    for command in commands:
        subprocess.run(["git", *command], cwd=candidate, env=environment, capture_output=True, check=True, timeout=10)
    replacement = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=candidate,
        env=environment,
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    ).stdout.strip()
    for command in (["replace", original, replacement], ["update-ref", "HEAD", original]):
        subprocess.run(["git", *command], cwd=candidate, env=environment, capture_output=True, check=True, timeout=10)
    observed = subprocess.run(
        ["git", "show", "-s", "--format=%ct", "HEAD"],
        cwd=candidate,
        env=environment,
        text=True,
        capture_output=True,
        check=True,
        timeout=10,
    )
    assert observed.stdout.strip() == "1700000001"  # Genuine counterfactual object view.
    policy = apply_execution_policy({"PATH": os.environ["PATH"], "GIT_NO_REPLACE_OBJECTS": "0"}, candidate)
    assert policy["SOURCE_DATE_EPOCH"] == "1700000000"
    assert policy["TEMPLATE_BUILD_EPOCH_SOURCE"] == "git:" + original
    assert (
        _run_coverage_git(
            ["git", "-C", str(candidate), "rev-parse", "HEAD^{tree}"],
            cwd=candidate,
            action="reading actual candidate tree",
        )
        == native_tree
    )


@pytest.mark.parametrize("epoch", ["bad", "NaN", "inf", "-1", "99999999999999999999999999999"])
def test_invalid_epoch_never_substitutes_wallclock(tmp_path: Path, epoch: str) -> None:
    with pytest.raises(ValueError, match="SOURCE_DATE_EPOCH"):
        apply_execution_policy({"SOURCE_DATE_EPOCH": epoch}, tmp_path)


@pytest.mark.parametrize("disable", ["0", "false", "off", "wrong"])
def test_retired_clock_disable_refuses(tmp_path: Path, disable: str) -> None:
    with pytest.raises(ValueError, match="retired clock-disable"):
        apply_execution_policy({"SOURCE_DATE_EPOCH": "1700000000", "TEMPLATE_DETERMINISTIC": disable}, tmp_path)


def test_mode_and_epoch_are_effective_execution_inputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project = tmp_path / "projects/demo"
    project.mkdir(parents=True)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    core = effective_environment_identity(tmp_path, project, mode="core")
    assert effective_environment_identity(tmp_path, project, mode="live") != core
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000001")
    assert effective_environment_identity(tmp_path, project, mode="core") != core


@pytest.mark.timeout(120)
def test_real_stage_consumes_pinned_epoch_and_explicit_live_policy(tmp_path: Path) -> None:
    project = tmp_path / "projects/demo"
    project.mkdir(parents=True)
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "child.py").write_text(
        "import os\nfrom pathlib import Path\n"
        "from infrastructure.core.determinism import resolve_build_timestamp\n"
        "Path('projects/demo/output/clock.txt').write_text(resolve_build_timestamp() + ':' + os.environ['TEMPLATE_EXECUTION_MODE'])\n"
    )
    (project / "pipeline.yaml").write_text(
        yaml.safe_dump(
            {
                "stages": [{"name": "Clock", "key": "clock", "script": "scripts/child.py"}],
                "telemetry": {"enabled": False},
            }
        )
    )
    executor = PipelineExecutor(PipelineConfig("demo", tmp_path, clean=False, mode="live", run_timeout_seconds=90))
    results = executor.execute_pipeline()
    assert executor.run_result(results).exit_code == 0
    first = (project / "output/clock.txt").read_bytes()
    assert first == b"2023-11-14T22:13:20Z:live"
    results = executor.execute_pipeline()
    assert executor.run_result(results).exit_code == 0
    assert (project / "output/clock.txt").read_bytes() == first


def test_actual_child_sees_explicit_export_epoch(tmp_path: Path) -> None:
    environment = apply_execution_policy(dict(os.environ, SOURCE_DATE_EPOCH="1700000000"), tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "import os;print(os.environ['SOURCE_DATE_EPOCH'] + ':' + os.environ['TEMPLATE_EXECUTION_MODE'])",
        ],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0 and result.stdout.strip() == "1700000000:core"
