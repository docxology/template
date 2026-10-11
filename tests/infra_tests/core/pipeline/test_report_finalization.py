"""Real final-report workers preserve completion and custody contracts."""

from __future__ import annotations

import json
import time
import hashlib
from pathlib import Path

import pytest

from infrastructure.core.pipeline.executor import PipelineExecutor
from infrastructure.core.pipeline.fingerprints import paths_digest
from infrastructure.core.pipeline.outcomes import StageStatus
from infrastructure.core.pipeline.report_finalization import finalize_execution_reports
from infrastructure.core.pipeline.types import PipelineConfig
from tests.infra_tests.orchestration._pipeline_fixture import scaffold_pipeline

pytestmark = pytest.mark.timeout(90)


def _executor(root: Path) -> PipelineExecutor:
    scaffold_pipeline(root)
    return PipelineExecutor(PipelineConfig("demo", root, clean=False, skip_infra=True, run_timeout_seconds=90))


def test_actual_finalizer_receipt_binds_run_plan_and_three_formats(tmp_path: Path) -> None:
    executor = _executor(tmp_path)
    results = executor.execute_pipeline()
    assert executor.run_result(results).complete
    output = executor.config.project_dir / "output"
    receipt = json.loads((output / ".pipeline/report_finalization.json").read_text())
    assert receipt["run_id"] == executor.run_id
    assert executor.execution_plan is not None
    assert receipt["plan_digest"] == executor.execution_plan.digest
    assert (
        receipt["execution_record_digest"]
        == hashlib.sha256((output / ".pipeline/execution.json").read_bytes()).hexdigest()
    )
    assert set(receipt["files"]) == {"pipeline_report.json", "pipeline_report.html", "pipeline_report.md"}
    inventory = paths_digest((output,), stable_output=True)
    (output / "reports/pipeline_report.html").write_text("changed runtime view")
    assert paths_digest((output,), stable_output=True) == inventory
    authored = output / "data/pipeline_report.html"
    authored.write_text("scientific data")
    assert paths_digest((output,), stable_output=True) != inventory


def test_finalizer_symlink_refuses_completion_and_preserves_sentinel(tmp_path: Path) -> None:
    executor = _executor(tmp_path)
    output = executor.config.project_dir / "output"
    target = output / ".pipeline/report_finalization.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    sentinel = tmp_path / "private.json"
    sentinel.write_text("unapproved sentinel")
    target.symlink_to(sentinel)
    results = executor.execute_pipeline()
    assert executor.run_result(results).exit_code == 1
    assert results[-1].outcome is not None and results[-1].outcome.status is StageStatus.FAILED
    assert results[-1].outcome.attempt_exit_codes == (1,)
    assert sentinel.read_text() == "unapproved sentinel"
    record = json.loads((output / ".pipeline/execution.json").read_text())
    assert record["complete"] is False and record["exit_code"] == 1


def test_no_reporting_launch_after_run_deadline(tmp_path: Path) -> None:
    executor = _executor(tmp_path)
    executor.preview_stage_names()
    executor._run_deadline = time.monotonic() - 1
    results = finalize_execution_reports(executor, [])
    assert executor.run_result(results).exit_code == 124
    assert results[-1].outcome is not None and results[-1].outcome.child_exit_code is None
    assert not (executor.config.project_dir / "output/.pipeline/report_finalization.json").exists()


def test_forged_current_record_cannot_authorize_final_reporting(tmp_path: Path) -> None:
    executor = _executor(tmp_path)
    results = executor.execute_pipeline()
    output = executor.config.project_dir / "output"
    target = output / ".pipeline/execution.json"
    record = json.loads(target.read_text())
    record["stage_results"][0]["duration"] += 1
    target.write_text(json.dumps(record))
    original = (output / ".pipeline/report_finalization.json").read_bytes()
    refused = finalize_execution_reports(executor, results)
    assert executor.run_result(refused).exit_code == 1
    assert refused[-1].outcome is not None and refused[-1].outcome.child_exit_code is None
    assert "current outcomes" in refused[-1].error_message
    assert (output / ".pipeline/report_finalization.json").read_bytes() == original


def test_reports_directory_link_cannot_create_external_reports(tmp_path: Path) -> None:
    executor = _executor(tmp_path)
    output = executor.config.project_dir / "output"
    external = tmp_path / "external"
    external.mkdir()
    sentinel = external / "pipeline_report.json"
    sentinel.write_text("external sentinel")
    (output / "reports").symlink_to(external, target_is_directory=True)
    results = executor.execute_pipeline()
    assert executor.run_result(results).exit_code != 0
    assert sentinel.read_text() == "external sentinel"
    assert not (external / "pipeline_report.html").exists()
