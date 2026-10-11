"""Real frozen-plan workers, exact completion and whole-run process boundaries."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest
import yaml

from infrastructure.core.pipeline.multi_project_parallel import (
    ENV_MULTI_PROJECT_WORKERS,
    _resolve_max_workers,
    run_projects_in_parallel,
)
from infrastructure.core.pipeline.multi_project_runtime import execute_frozen_specs, freeze_project_plans
from tests.infra_tests.orchestration._pipeline_fixture import scaffold_pipeline

pytestmark = pytest.mark.timeout(120)


def _install_sleeping_stage(root: Path) -> None:
    script = root / "scripts/stage.py"
    script.write_text(
        "import json,os,subprocess,sys,time\nfrom pathlib import Path\n"
        "project=sys.argv[sys.argv.index('--project')+1]\n"
        "output=Path('projects')/project/'output/data';output.mkdir(parents=True,exist_ok=True)\n"
        "child=subprocess.Popen([sys.executable,'-I','-c','import time;time.sleep(30)'],start_new_session=True)\n"
        "(output/'running.json').write_text(json.dumps({'pid':os.getpid(),'detached':child.pid}))\n"
        "time.sleep(30)\n"
    )


def _assert_dead(pid: int) -> None:
    result = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True, timeout=5)
    assert not result.stdout.strip() or result.stdout.strip().startswith("Z"), (pid, result.stdout)


@pytest.mark.parametrize("workers", [0, -1, True, 1.5])
def test_invalid_worker_override_refused(workers: int) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        _resolve_max_workers(2, workers)


def test_worker_count_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_MULTI_PROJECT_WORKERS, "2")
    assert _resolve_max_workers(3, None) == 2
    assert _resolve_max_workers(3, 5) == 3
    monkeypatch.setenv(ENV_MULTI_PROJECT_WORKERS, "invalid")
    assert 1 <= _resolve_max_workers(3, None) <= 3


def test_all_plans_validated_before_shared_gate(tmp_path: Path) -> None:
    names = ("templates/alpha", "templates/beta")
    scaffold_pipeline(tmp_path, names)
    declaration = tmp_path / "projects/templates/beta/pipeline.yaml"
    declaration.write_text("stages: [{name: Bad, key: bad, script: scripts/stage.py, method: missing}]\n")
    with pytest.raises(ValueError):
        run_projects_in_parallel(names, repo_root=tmp_path)
    assert not (tmp_path / "process_order.log").exists()


def test_frozen_plan_refuses_later_definition_change(tmp_path: Path) -> None:
    names = ("templates/alpha",)
    scaffold_pipeline(tmp_path, names)
    specs = freeze_project_plans(names, tmp_path, mode="core", resume=False, timeout=15)
    path = tmp_path / "infrastructure/core/pipeline/pipeline.yaml"
    document = yaml.safe_load(path.read_text())
    document["stages"][1]["key"] = "replacement"
    path.write_text(yaml.safe_dump(document))
    rows, runs = execute_frozen_specs(specs, workers=1, deadline=time.monotonic() + 15)
    assert runs[names[0]].exit_code == 75 and not runs[names[0]].complete
    assert runs[names[0]].expected_stage_keys == ("analysis",)
    assert not (tmp_path / "process_order.log").exists()
    assert any("source changed" in row.error_message.lower() for row in rows[names[0]])


def test_child_two_is_failed_without_losing_other_project(tmp_path: Path) -> None:
    names = ("templates/pass", "templates/fail")
    scaffold_pipeline(tmp_path, names)
    script = tmp_path / "scripts/stage.py"
    text = script.read_text().replace(
        "step = sys.argv[1]", "step = sys.argv[1]; print(sys.argv[sys.argv.index('--project')+1], flush=True)"
    )
    script.write_text(text)
    result = run_projects_in_parallel(names, repo_root=tmp_path, max_workers=2, run_infra_tests=False)
    assert result.exit_code == 1 and result.succeeded == ["templates/pass"]
    assert result.failed == ["templates/fail"]
    assert result.run_results["templates/fail"].outcomes[0].child_exit_code == 2
    for name in names:
        log = (tmp_path / "projects" / name / "output/logs/multi_project_worker.log").read_text()
        assert name in log and names[1 if name == names[0] else 0] not in log


def test_small_total_budget_cannot_launch_late_stage_or_unlaunched_queue(tmp_path: Path) -> None:
    names = ("templates/alpha", "templates/beta")
    scaffold_pipeline(tmp_path, names)
    _install_sleeping_stage(tmp_path)
    started = time.monotonic()
    result = run_projects_in_parallel(
        names, repo_root=tmp_path, max_workers=1, run_infra_tests=False, run_timeout_seconds=4
    )
    assert result.exit_code == 124 and time.monotonic() - started < 15
    assert set(result.run_results) == set(names)
    assert all(run.expected_stage_keys == ("analysis",) and run.exit_code == 124 for run in result.run_results.values())
    marker = tmp_path / "projects/templates/alpha/output/data/running.json"
    if marker.exists():
        observed = json.loads(marker.read_text())
        _assert_dead(observed["pid"])
        _assert_dead(observed["detached"])
    assert not (tmp_path / "projects/templates/beta/output/data/running.json").exists()


def test_total_deadline_kills_actual_started_stage_detached_children_and_queue(tmp_path: Path) -> None:
    names = ("templates/alpha", "templates/beta")
    scaffold_pipeline(tmp_path, names)
    _install_sleeping_stage(tmp_path)
    started = time.monotonic()
    result = run_projects_in_parallel(
        names, repo_root=tmp_path, max_workers=1, run_infra_tests=False, run_timeout_seconds=12
    )
    assert result.exit_code == 124 and time.monotonic() - started < 22
    assert set(result.run_results) == set(names)
    assert all(run.expected_stage_keys == ("analysis",) and run.exit_code == 124 for run in result.run_results.values())
    observed = json.loads((tmp_path / "projects/templates/alpha/output/data/running.json").read_text())
    _assert_dead(observed["pid"])
    _assert_dead(observed["detached"])
    assert not (tmp_path / "projects/templates/beta/output/data/running.json").exists()


def test_interrupt_cleans_actual_worker_and_detached_child(tmp_path: Path) -> None:
    scaffold_pipeline(tmp_path, ("templates/alpha",))
    _install_sleeping_stage(tmp_path)
    implementation = Path(__file__).resolve().parents[5]
    code = (
        "import sys;sys.pycache_prefix=sys.argv.pop(1);sys.dont_write_bytecode=True;"
        "sys.path.insert(0,sys.argv.pop(1));from pathlib import Path;"
        "from infrastructure.core.pipeline.multi_project_parallel import run_projects_in_parallel;"
        "raise SystemExit(run_projects_in_parallel(('templates/alpha',),repo_root=Path(sys.argv[1]),"
        "run_infra_tests=False,run_timeout_seconds=30).exit_code)"
    )
    process = subprocess.Popen(
        [sys.executable, "-I", "-c", code, str(tmp_path / "outer-bytecode"), str(implementation), str(tmp_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    marker = tmp_path / "projects/templates/alpha/output/data/running.json"
    try:
        deadline = time.monotonic() + 12
        while not marker.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.025)
        assert marker.exists(), process.communicate(timeout=5)
        observed = json.loads(marker.read_text())
        os.kill(process.pid, signal.SIGINT)
        stdout, stderr = process.communicate(timeout=12)
        assert process.returncode == 130, (stdout, stderr)
        _assert_dead(observed["pid"])
        _assert_dead(observed["detached"])
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)


def test_actual_workers_run_shared_infrastructure_once(tmp_path: Path) -> None:
    import json
    from tests.infra_tests.orchestration._pipeline_fixture import scaffold_pipeline

    names = ("templates/alpha", "templates/beta")
    scaffold_pipeline(tmp_path, names)
    result = run_projects_in_parallel(names, repo_root=tmp_path, max_workers=2)
    assert result.exit_code == 0 and result.expected_projects == names
    assert result.shared_infrastructure_result is not None
    assert result.shared_infrastructure_result.run_result.expected_stage_keys == ("infra_tests",)
    assert result.shared_infrastructure_result.run_result.outcomes[0].child_exit_code == 0
    rows = (tmp_path / "process_order.log").read_text().splitlines()
    assert rows[0] == "templates/alpha:infra"
    assert sum(row.endswith(":infra") for row in rows) == 1
    assert sorted(rows[1:]) == ["templates/alpha:analysis", "templates/beta:analysis"]
    pids = set()
    for name in names:
        output = tmp_path / "projects" / name / "output"
        pids.add(json.loads((output / "data/analysis.json").read_text())["pid"])
        assert (output / "logs/pipeline.log").is_file()
        assert result.run_results[name].expected_stage_keys == ("analysis",)
    assert len(pids) == 2 and os.getpid() not in pids


def test_actual_parallel_shared_failure_prevents_worker_submission(tmp_path: Path) -> None:
    from tests.infra_tests.orchestration._pipeline_fixture import scaffold_pipeline

    names = ("templates/alpha", "templates/beta")
    scaffold_pipeline(tmp_path, names, infra_exit=2)
    result = run_projects_in_parallel(names, repo_root=tmp_path, max_workers=2)
    assert result.exit_code == 1 and result.shared_infrastructure_exit_code == 1
    assert result.shared_infrastructure_result is not None
    assert result.shared_infrastructure_result.run_result.outcomes[0].child_exit_code == 2
    assert result.run_results == {} and result.failed == list(names)
    assert (tmp_path / "process_order.log").read_text().splitlines() == ["templates/alpha:infra"]
    for name in names:
        assert not (tmp_path / "projects" / name / "output/data/analysis.json").exists()
    # The shared check legitimately logs under its selected project's output.
    # The other project gets no executor or worker log.
    assert not (tmp_path / "projects/templates/beta/output/logs/pipeline.log").exists()


def test_actual_parallel_stage_intervals_overlap(tmp_path: Path) -> None:
    names = ("templates/alpha", "templates/beta")
    scaffold_pipeline(tmp_path, names)
    (tmp_path / "scripts/stage.py").write_text(
        "import json,os,sys,time\nfrom pathlib import Path\n"
        "project=sys.argv[sys.argv.index('--project')+1]\n"
        "output=Path('projects')/project/'output/data';output.mkdir(parents=True,exist_ok=True)\n"
        "(output/'ready.json').write_text(json.dumps({'pid':os.getpid()}))\n"
        "ready=[Path('projects')/name/'output/data/ready.json' for name in ('templates/alpha','templates/beta')]\n"
        "deadline=time.monotonic()+10\n"
        "while not all(path.is_file() for path in ready):\n"
        "    if time.monotonic()>=deadline: raise TimeoutError('actual parallel worker rendezvous not reached')\n"
        "    time.sleep(.01)\n"
        "start=time.monotonic();time.sleep(1.2)\n"
        "(output/'interval.json').write_text(json.dumps({'start':start,'end':time.monotonic(),'pid':os.getpid()}))\n"
    )
    result = run_projects_in_parallel(names, repo_root=tmp_path, max_workers=2, run_infra_tests=False)
    assert result.exit_code == 0
    intervals = [json.loads((tmp_path / "projects" / name / "output/data/interval.json").read_text()) for name in names]
    assert max(row["start"] for row in intervals) < min(row["end"] for row in intervals)
    assert intervals[0]["pid"] != intervals[1]["pid"]


def test_worker_lock_wait_uses_remaining_outer_budget(tmp_path: Path) -> None:
    scaffold_pipeline(tmp_path, ("templates/alpha",))
    project = tmp_path / "projects/templates/alpha"
    implementation = Path(__file__).resolve().parents[5]
    marker = project / "output/holder-ready"
    code = (
        "import sys,time;sys.path.insert(0,sys.argv.pop(1));from pathlib import Path;"
        "from infrastructure.core.files.project_lock import project_output_lock;"
        "\nwith project_output_lock(Path(sys.argv[1])):\n"
        " Path(sys.argv[2]).write_text('holder');time.sleep(30)\n"
    )
    holder = subprocess.Popen(
        [sys.executable, "-I", "-c", code, str(implementation), str(project), str(marker)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        deadline = time.monotonic() + 5
        while not marker.exists() and holder.poll() is None and time.monotonic() < deadline:
            time.sleep(0.025)
        assert marker.exists()
        result = run_projects_in_parallel(
            ("templates/alpha",), repo_root=tmp_path, run_infra_tests=False, run_timeout_seconds=4
        )
        assert result.exit_code == 124 and holder.poll() is None
        assert not (tmp_path / "process_order.log").exists()
        assert marker.read_text() == "holder"
    finally:
        if holder.poll() is None:
            os.killpg(holder.pid, signal.SIGKILL)
        holder.communicate(timeout=5)
