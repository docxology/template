"""Actual lock waiting and child execution share the supervising deadline."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from infrastructure.core.files.project_lock import _lock_key, _lock_path
from infrastructure.core.pipeline.execution_session import compose_run_deadline
from infrastructure.core.pipeline.executor import PipelineExecutor
from infrastructure.core.pipeline.plan import compile_execution_plan
from infrastructure.core.pipeline.types import PipelineConfig
from tests.infra_tests.orchestration._pipeline_fixture import scaffold_pipeline

pytestmark = pytest.mark.timeout(90)


@pytest.mark.parametrize("invalid", [True, float("inf"), float("nan"), "later"])
def test_supervising_deadline_has_no_type_coercion(invalid: object) -> None:
    with pytest.raises(ValueError, match="finite"):
        compose_run_deadline(90, invalid)  # type: ignore[arg-type]


def _executor(root: Path) -> PipelineExecutor:
    scaffold_pipeline(root)
    return PipelineExecutor(PipelineConfig("demo", root, clean=False, skip_infra=True, run_timeout_seconds=90))


def test_expired_outer_deadline_does_not_execute_or_overwrite_active_record(tmp_path: Path) -> None:
    executor = _executor(tmp_path)
    plan = compile_execution_plan(executor.config)
    record = executor.config.project_dir / "output/.pipeline/execution.json"
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text("active holder's evidence")
    results = executor.execute_plan(plan, deadline_monotonic=time.monotonic() - 1)
    assert executor.run_result(results).exit_code == 124
    assert results[0].outcome is not None and results[0].outcome.child_exit_code is None
    assert record.read_text() == "active holder's evidence"
    assert not (tmp_path / "process_order.log").exists()
    assert executor.execution_plan is not None and executor.execution_plan.digest == plan.digest
    assert executor.execution_plan == plan and plan.run_timeout_seconds == 90


def test_real_lock_contention_consumes_outer_budget_and_preserves_holder(tmp_path: Path) -> None:
    import fcntl

    executor = _executor(tmp_path)
    plan = compile_execution_plan(executor.config)
    record = executor.config.project_dir / "output/.pipeline/execution.json"
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text("active holder's evidence")
    lock = _lock_path(_lock_key(executor.config.project_dir))
    started = time.monotonic()
    with lock.open("a") as held:
        fcntl.flock(held, fcntl.LOCK_EX)
        results = executor.execute_plan(plan, deadline_monotonic=started + 0.5)
    assert executor.run_result(results).exit_code == 124
    assert time.monotonic() - started < 3
    assert record.read_text() == "active holder's evidence"
    assert not (tmp_path / "process_order.log").exists()


@pytest.mark.timeout(60)
def test_child_cannot_restart_a_frozen_plan_budget(tmp_path: Path) -> None:
    executor = _executor(tmp_path)
    (tmp_path / "scripts/stage.py").write_text(
        "import time\nfrom pathlib import Path\n"
        "Path('child-launched').write_text('actual child execution')\n"
        "time.sleep(90)\n"
    )
    plan = compile_execution_plan(executor.config)
    started = time.monotonic()
    results = executor.execute_plan(plan, deadline_monotonic=started + 30)
    assert executor.run_result(results).exit_code == 124
    assert time.monotonic() - started < 40
    assert (tmp_path / "child-launched").read_text() == "actual child execution"
    assert executor.execution_plan is not None and executor.execution_plan.digest == plan.digest
    assert executor.execution_plan == plan and plan.run_timeout_seconds == 90
    assert results[0].outcome is not None and results[0].outcome.child_exit_code is not None
