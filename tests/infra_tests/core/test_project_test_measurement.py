"""Real original pytest/coverage measurement composition and refusal controls."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from infrastructure.core.pipeline.stages import build_stage_subprocess_env
from infrastructure.core.runtime.python_binding import analysis_runtime_binding
from infrastructure.core.testing.project_test_measurement import (
    ANCHOR_ENV,
    MeasurementIneligible,
    consume_measurement,
    measurement_path,
    prepare_measurement,
    publish_measurement,
    observe_measurement_publication,
    validate_measurement,
)

ROOT = Path(__file__).resolve().parents[3]
# Each new integration case owns a real child with a 30-second process bound.
pytestmark = pytest.mark.timeout(90)


def _original(root: Path, fault: str = "none"):
    project = root / "projects/demo"
    (project / "src").mkdir(parents=True)
    (project / "tests").mkdir()
    (project / "pyproject.toml").write_text(
        '[tool.pytest.ini_options]\ntestpaths = ["tests"]\n[tool.coverage.report]\nfail_under = 90\n'
    )
    (project / "src/owned.py").write_text("def twice(number):\n    return number * 2\n")
    body = "from owned import twice\ndef test_actual():\n    assert twice(3) == 6\n"
    if fault == "skip":
        body += "def test_skipped():\n    import pytest\n    pytest.skip('actual skip')\n"
    elif fault == "collection-skip":
        (project / "tests/test_skipped.py").write_text(
            "import pytest\npytest.skip('actual collection skip', allow_module_level=True)\n"
        )
    (project / "tests/test_owned.py").write_text(body)
    env = {
        **os.environ,
        "PYTEST_ADDOPTS": "",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "PIPELINE_STAGE_KEY": "project_tests",
        "PIPELINE_RUN_ID": "original-run",
        "PIPELINE_PLAN_DIGEST": "a" * 64,
    }
    bootstrap = (
        "import sys,runpy;"
        f"sys.path[:0]={[str(ROOT), str(project / 'src')]!r};"
        "sys.argv=['pytest',*sys.argv[1:]];runpy.run_module('pytest',run_name='__main__')"
    )
    cmd = [
        sys.executable,
        "-I",
        "-B",
        "-c",
        bootstrap,
        "tests",
        "-q",
        "-p",
        "pytest_cov",
        f"--cov={project / 'src'}",
        f"--cov-report=json:{project / 'coverage_project.json'}",
    ]
    if fault != "statement-only":
        cmd.append("--cov-branch")
    if fault == "deselect":
        cmd.extend(["-k", "actual"])
        with (project / "tests/test_owned.py").open("a") as stream:
            stream.write("def test_omitted():\n    assert False\n")
    env["COVERAGE_FILE"] = str(project / ".coverage.project")
    selected = Path(sys.executable).absolute()
    observation = prepare_measurement(
        root,
        project,
        selected,
        analysis_runtime_binding(project, interpreter=selected),
        cmd,
        env,
        floor=90,
        deadline=time.monotonic() + 60,
    )
    assert observation is not None
    result = subprocess.run(cmd, cwd=project, env=env, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    return project, env, observation


@pytest.fixture(scope="module")
def original(tmp_path_factory: pytest.TempPathFactory):
    project, env, observation = _original(tmp_path_factory.mktemp("actual-project-measurement"))
    with observe_measurement_publication() as publication:
        anchor = publish_measurement(observation, original_exit_code=0)
    assert publication == {"sha256": anchor}
    return project, env, observation, anchor


def test_actual_same_run_measurement_and_external_anchor(original, monkeypatch: pytest.MonkeyPatch) -> None:
    project, env, _, anchor = original
    count, report = validate_measurement(project, env, anchor)
    assert count == 1 and report["meta"]["branch_coverage"] is True
    assert report["totals"]["percent_covered"] == 100
    for name, value in env.items():
        if name.startswith("PIPELINE_"):
            monkeypatch.setenv(name, value)
    monkeypatch.delenv(ANCHOR_ENV, raising=False)
    assert consume_measurement(project) is None
    monkeypatch.setenv(ANCHOR_ENV, anchor)
    output = project / "output/data/coverage_full.json"
    assert consume_measurement(project, output) == (1, "100.00")
    assert json.loads(output.read_bytes()) == report
    # A caller's ambient hash cannot seed a new executor's environment.
    assert ANCHOR_ENV not in build_stage_subprocess_env(project.parents[1], project)


@pytest.mark.parametrize(
    "fault",
    [
        "anchor",
        "run",
        "plan",
        "source",
        "coverage",
        "database",
        "receipt",
        "symlink",
        "receipt-symlink",
        "duplicate-controller",
    ],
)
def test_current_measurement_refuses_real_changed_inputs(original, fault: str) -> None:
    project, original_env, observation, original_anchor = original
    env = dict(original_env)
    anchor = original_anchor
    target = None
    backup = None
    created = None
    if fault == "anchor":
        anchor = "0" * 64
    elif fault in {"run", "plan"}:
        env["PIPELINE_RUN_ID" if fault == "run" else "PIPELINE_PLAN_DIGEST"] = "different"
    else:
        targets = {
            "source": project / "src/owned.py",
            "coverage": project / "coverage_project.json",
            "database": project / ".coverage.project",
            "receipt": next(observation.directory.glob("execution-*.json")),
            "symlink": measurement_path(project, env["PIPELINE_RUN_ID"]),
            "receipt-symlink": next(observation.directory.glob("execution-*.json")),
            "duplicate-controller": next(observation.directory.glob("execution-*.json")),
        }
        target = targets[fault]
        backup = target.read_bytes()
        if fault in {"symlink", "receipt-symlink"}:
            created = target.with_name(target.name + ".outside")
            created.write_bytes(backup)
            target.unlink()
            target.symlink_to(created)
        elif fault == "duplicate-controller":
            created = target.with_name("execution-duplicate.json")
            created.write_bytes(backup)
        else:
            target.write_bytes(backup + b"\n# real mutation\n")
    try:
        with pytest.raises((ValueError, OSError, KeyError, TypeError)):
            validate_measurement(project, env, anchor)
    finally:
        if target is not None and backup is not None:
            if target.is_symlink():
                target.unlink()
            target.write_bytes(backup)
        if created is not None:
            created.unlink()


@pytest.mark.parametrize("fault", ["skip", "collection-skip", "deselect", "statement-only"])
def test_actual_ineligible_original_never_publishes(tmp_path: Path, fault: str) -> None:
    project, env, observation = _original(tmp_path, fault)
    with pytest.raises(ValueError):
        publish_measurement(observation, original_exit_code=0)
    assert not measurement_path(project, env["PIPELINE_RUN_ID"]).exists()


@pytest.mark.parametrize("fault", ["missing-callback", "changed-invocation"])
def test_original_custody_failure_is_not_optional_selection(tmp_path: Path, fault: str) -> None:
    _, _, observation = _original(tmp_path)
    receipt = next(observation.directory.glob("execution-*.json"))
    if fault == "missing-callback":
        receipt.unlink()
    else:
        value = json.loads(receipt.read_bytes())
        value["selection_profile"]["arguments"].append("--collect-only")
        receipt.write_text(json.dumps(value))
    with pytest.raises(ValueError) as refused:
        publish_measurement(observation, original_exit_code=0)
    assert not isinstance(refused.value, MeasurementIneligible)


def test_invalid_present_measurement_does_not_fall_back(original, monkeypatch: pytest.MonkeyPatch) -> None:
    project, env, _, _ = original
    monkeypatch.setenv("PIPELINE_RUN_ID", env["PIPELINE_RUN_ID"])
    monkeypatch.setenv("PIPELINE_PLAN_DIGEST", env["PIPELINE_PLAN_DIGEST"])
    monkeypatch.setenv(ANCHOR_ENV, hashlib.sha256(b"not-original").hexdigest())
    with pytest.raises(ValueError, match="executor-held"):
        consume_measurement(project)


@pytest.mark.parametrize("resign_before_return", [False, True])
def test_actual_stage_completion_carries_original_publication(tmp_path: Path, resign_before_return: bool) -> None:
    from infrastructure.core.pipeline.fingerprints import source_fingerprint
    from infrastructure.core.pipeline.stage_launch import launch_python_stage

    repo = tmp_path.resolve()
    project = repo / "projects/demo"
    (project / "src").mkdir(parents=True)
    (project / "tests").mkdir()
    (repo / "scripts").mkdir()
    (project / "src/owned.py").write_text("def twice(number):\n    return number * 2\n")
    (project / "tests/test_owned.py").write_text(
        "from owned import twice\ndef test_actual():\n    assert twice(3) == 6\n"
    )
    (project / "pyproject.toml").write_text("[tool.coverage.report]\nfail_under = 90\n")
    script = repo / "scripts/actual_stage.py"
    body = (
        "from pathlib import Path\n"
        "from infrastructure.reporting.pipeline_test_runner import run_project_tests\n"
        f"code, results = run_project_tests(Path({str(repo)!r}), 'demo')\n"
    )
    if resign_before_return:
        body += (
            "import hashlib,json,os\n"
            "from infrastructure.core.testing.project_test_measurement import measurement_path\n"
            f"project = Path({str(project)!r})\n"
            "path = measurement_path(project, os.environ['PIPELINE_RUN_ID'])\n"
            "record = json.loads(path.read_bytes())\n"
            "report_path = project / record['coverage']['path']\n"
            "report = json.loads(report_path.read_bytes())\n"
            "report['meta']['timestamp'] = 're-signed after original publication'\n"
            "report_path.write_text(json.dumps(report))\n"
            "record['coverage']['sha256'] = hashlib.sha256(report_path.read_bytes()).hexdigest()\n"
            "path.write_text(json.dumps(record, sort_keys=True) + '\\n')\n"
        )
    script.write_text(body + "raise SystemExit(code)\n")
    env = build_stage_subprocess_env(repo, project)
    env.update(
        PIPELINE_RUN_ID="actual-stage",
        PIPELINE_STAGE_KEY="project_tests",
        PIPELINE_PLAN_DIGEST="a" * 64,
        SOURCE_DATE_EPOCH="1700000000",
        PYTEST_ADDOPTS="",
    )
    publication: dict[str, str] = {}
    source_before = source_fingerprint(repo, project)
    outcome = launch_python_stage(
        repo=repo,
        project=project,
        argv=[sys.executable, str(script)],
        env=env,
        deadline=time.monotonic() + 60,
        stage_key="project_tests",
        run_id="actual-stage",
        source_digest=source_before,
        definition=None,
        skip_path=project / "output/unused.json",
        allow_skip=False,
        project_test_measurement=publication,
    )
    assert outcome.complete, outcome.diagnostic
    assert source_fingerprint(repo, project) == source_before
    assert not (project / ".benchmarks").exists()
    measurement = json.loads(measurement_path(project, env["PIPELINE_RUN_ID"]).read_bytes())
    arguments = measurement["arguments"]
    hook = "infrastructure.core.testing._pytest_runtime_controls"
    assert arguments.count(hook) == 1 and arguments[arguments.index(hook) - 1] == "-p"
    assert arguments.count(f"--template-benchmark-storage={project / 'output/.pipeline/benchmarks'}") == 1
    assert len(publication["sha256"]) == 64
    if resign_before_return:
        with pytest.raises(ValueError, match="executor-held"):
            validate_measurement(project, env, publication["sha256"])
    else:
        assert validate_measurement(project, env, publication["sha256"])[0] == 1
