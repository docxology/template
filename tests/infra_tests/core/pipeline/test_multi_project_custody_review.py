"""Independent typed-result coherence and private aggregate output controls."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from infrastructure.core.pipeline.multi_project import (
    MultiProjectResult,
    format_multi_project_outcome_lines,
    validated_project_run,
)
from infrastructure.core.pipeline.multi_project_parallel import ParallelRunResult
from infrastructure.core.pipeline.multi_project_summary import write_summary_reports
from infrastructure.core.pipeline.multi_project_support import SharedInfrastructureResult
from infrastructure.core.pipeline.outcomes import RunResult, StageOutcome, StageStatus
from infrastructure.core.pipeline.types import PipelineStageResult
from infrastructure.project.project_info import ProjectInfo
from infrastructure.reporting.multi_project_reporter import _build_summary_dict


def _row(status: StageStatus, code: int) -> PipelineStageResult:
    outcome = StageOutcome("analysis", status, code)
    return PipelineStageResult(1, "Analysis", outcome.complete, 0.1, code, stage_key="analysis", outcome=outcome)


def test_serial_result_and_display_refuse_contradictory_typed_project_claim() -> None:
    name = "templates/demo"
    rows = [_row(StageStatus.FAILED, 2)]
    claimed = RunResult.from_results([_row(StageStatus.SUCCEEDED, 0)], ("analysis",))
    result = MultiProjectResult({name: rows}, expected_projects=(name,), run_results={name: claimed})
    project = ProjectInfo("demo", Path("/unused/projects/templates/demo"), True, True, True, True, program="templates")
    assert validated_project_run(result, name) is None
    assert result.exit_code == 1
    lines = format_multi_project_outcome_lines([project], result)
    assert "Succeeded:" not in lines and "Failed:" in lines


def test_parallel_result_refuses_contradictory_typed_project_claim() -> None:
    name = "templates/demo"
    claimed = RunResult.from_results([_row(StageStatus.SUCCEEDED, 0)], ("analysis",))
    result = ParallelRunResult(
        [name], [], 0.1, (name,), {name: claimed}, project_results={name: [_row(StageStatus.FAILED, 2)]}
    )
    assert result.exit_code == 1


@pytest.mark.parametrize("contradiction", ["rows", "identity", "aggregate"])
def test_public_shared_result_and_summary_refuse_contradictory_claim(contradiction: str) -> None:
    name = "templates/demo"
    rows = [_row(StageStatus.SUCCEEDED, 0)]
    success = StageOutcome("infra_tests", StageStatus.SUCCEEDED, 0)
    failure = StageOutcome("infra_tests", StageStatus.FAILED, 2)
    actual = failure if contradiction in {"rows", "aggregate"} else _row(StageStatus.SUCCEEDED, 0).outcome
    assert actual is not None
    shared_row = PipelineStageResult(
        1,
        "Shared infrastructure",
        actual.complete,
        0.1,
        actual.child_exit_code or 0,
        stage_key=actual.stage_key,
        outcome=actual,
    )
    claimed = RunResult((actual.stage_key,), (success if contradiction == "rows" else actual,))
    shared = SharedInfrastructureResult((shared_row,), claimed)
    result = MultiProjectResult(
        {name: rows},
        expected_projects=(name,),
        run_results={name: RunResult.from_results(rows, ("analysis",))},
        shared_infrastructure_result=shared,
    )
    project = ProjectInfo("demo", Path("/unused/projects/templates/demo"), True, True, True, True, program="templates")
    parallel = ParallelRunResult(
        [name], [], 0.1, (name,), result.run_results, project_results={name: rows}, shared_infrastructure_result=shared
    )
    assert result.exit_code == parallel.exit_code == 1
    assert _build_summary_dict(result, [project])["shared_infrastructure"] is None


@pytest.mark.timeout(90)
def test_actual_shared_child_two_is_retained_in_supervised_summary(tmp_path: Path) -> None:
    import json

    import yaml

    from infrastructure.core.pipeline.multi_project import MultiProjectConfig, MultiProjectOrchestrator
    from tests.infra_tests.orchestration._pipeline_fixture import scaffold_pipeline

    name = "templates/alpha"
    scaffold_pipeline(tmp_path, (name,), infra_exit=2, canonical_gate=False)
    # The canonical test target is a real thin adapter to the original exit-2
    # producer. A stable stage label alone cannot admit an arbitrary shared gate.
    gate = tmp_path / "scripts/pipeline/stage_01_test.py"
    gate.parent.mkdir()
    gate.write_text(
        "import argparse, runpy, sys\n"
        "parser = argparse.ArgumentParser()\n"
        "parser.add_argument('--infra-only', action='store_true', required=True)\n"
        "parser.add_argument('--project', required=True)\n"
        "args = parser.parse_args()\n"
        "sys.argv = ['scripts/stage.py', 'infra', '--project', args.project]\n"
        "runpy.run_path('scripts/stage.py', run_name='__main__')\n",
        encoding="utf-8",
    )
    declaration = tmp_path / "infrastructure/core/pipeline/pipeline.yaml"
    document = yaml.safe_load(declaration.read_text())
    shared_stage = next(stage for stage in document["stages"] if stage["key"] == "infra_tests")
    shared_stage.update(script="scripts/pipeline/stage_01_test.py", args=["--infra-only"])
    declaration.write_text(yaml.safe_dump(document), encoding="utf-8")
    project = ProjectInfo("alpha", tmp_path / "projects" / name, True, True, True, True, program="templates")
    result = MultiProjectOrchestrator(MultiProjectConfig(tmp_path, [project])).execute_all_projects()
    assert result.exit_code == 1 and result.project_results == {}
    assert (tmp_path / "process_order.log").read_text().splitlines() == [f"{name}:infra"]
    assert not (project.path / "output/data/analysis.json").exists()
    actual = result.shared_infrastructure_result
    assert actual is not None and actual.exit_code == 1
    assert actual.run_result.outcomes[0].child_exit_code == 2
    assert actual.run_result.outcomes[0].attempt_exit_codes == (2,)
    assert write_summary_reports(result, [project], tmp_path, deadline=time.monotonic() + 70) == 0
    directory = tmp_path / "output/multi_project_summary"
    summary = json.loads((directory / "multi_project_summary.json").read_text())
    shared = summary["shared_infrastructure"]
    assert shared["expected_stage_keys"] == ["infra_tests"] and shared["exit_code"] == 1
    assert shared["outcomes"][0]["status"] == "failed" and shared["outcomes"][0]["child_exit_code"] == 2
    assert "original child exit 2" in (directory / "multi_project_summary.md").read_text()
    assert "original child exit 2" in (directory / "last-run-summary.md").read_text()


def test_noncanonical_shared_gate_is_refused_before_any_real_child(tmp_path: Path) -> None:
    from infrastructure.core.pipeline.multi_project import MultiProjectConfig, MultiProjectOrchestrator
    from tests.infra_tests.orchestration._pipeline_fixture import scaffold_pipeline

    name = "templates/alpha"
    scaffold_pipeline(tmp_path, (name,), infra_exit=2, canonical_gate=False)
    project = ProjectInfo("alpha", tmp_path / "projects" / name, True, True, True, True, program="templates")
    with pytest.raises(ValueError, match="Prepared shared infrastructure policy differs from the canonical gate"):
        MultiProjectOrchestrator(MultiProjectConfig(tmp_path, [project])).execute_all_projects()
    assert not (tmp_path / "process_order.log").exists()
    assert not (project.path / "output/data/analysis.json").exists()
    assert not (tmp_path / "output").exists()


@pytest.mark.timeout(90)
def test_private_aggregate_summary_preserves_tracked_historical_doc(tmp_path: Path) -> None:
    historical = tmp_path / "docs/_generated/last-run-summary.md"
    historical.parent.mkdir(parents=True)
    historical.write_text("Preserved historical public execution evidence.\n")
    original = historical.read_bytes()
    name = "active/private_fixture_name"
    project = ProjectInfo(
        "private_fixture_name", tmp_path / "projects" / name, True, True, True, True, program="active"
    )
    rows = [_row(StageStatus.FAILED, 2)]
    result = MultiProjectResult(
        {name: rows},
        successful_projects=0,
        failed_projects=1,
        expected_projects=(name,),
        run_results={name: RunResult.from_results(rows, ("analysis",))},
    )
    code = write_summary_reports(result, [project], tmp_path, deadline=time.monotonic() + 70)
    assert code == 0
    assert historical.read_bytes() == original
    assert name not in historical.read_text()
    runtime = tmp_path / "output/multi_project_summary/last-run-summary.md"
    assert runtime.is_file() and name in runtime.read_text()
