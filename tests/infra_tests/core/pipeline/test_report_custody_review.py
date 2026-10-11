"""Independent real report caller and source-change closure controls."""

from pathlib import Path

import pytest

from infrastructure.core.pipeline.executor import PipelineExecutor
from infrastructure.core.pipeline.report_finalization import finalize_execution_reports
from infrastructure.core.pipeline.types import PipelineConfig
from infrastructure.reporting.pipeline_io import _atomic_write_text
from tests.infra_tests.orchestration._pipeline_fixture import scaffold_pipeline


def test_report_caller_refuses_a_link_above_its_nominated_root(tmp_path: Path) -> None:
    external = tmp_path / "external" / "nested"
    external.mkdir(parents=True)
    sentinel = external / "pipeline_report.json"
    sentinel.write_text("private sentinel")
    link = tmp_path / "redirect"
    link.symlink_to(external.parent, target_is_directory=True)
    with pytest.raises((OSError, ValueError)):
        _atomic_write_text(link / "nested" / sentinel.name, "unapproved")
    assert sentinel.read_text() == "private sentinel"
    assert {path.name for path in external.iterdir()} == {sentinel.name}


@pytest.mark.timeout(90)
def test_real_source_change_before_reporting_launch_preserves_previous_receipt(tmp_path: Path) -> None:
    scaffold_pipeline(tmp_path)
    executor = PipelineExecutor(PipelineConfig("demo", tmp_path, clean=False, skip_infra=True, run_timeout_seconds=90))
    results = executor.execute_pipeline()
    assert executor.run_result(results).complete
    project = executor.config.project_dir
    receipt = project / "output/.pipeline/report_finalization.json"
    original = receipt.read_bytes()
    (project / "src/new_model.py").write_text("SCIENTIFIC_CHANGE=1\n")
    refused = finalize_execution_reports(executor, results)
    assert executor.run_result(refused).exit_code == 75
    assert refused[-1].outcome is not None and refused[-1].outcome.child_exit_code is None
    assert receipt.read_bytes() == original


@pytest.mark.parametrize("child_code,aggregate", [(7, 1), (124, 124), (130, 130)])
@pytest.mark.timeout(90)
def test_actual_reporting_exit_cannot_be_demoted_by_absent_receipt(
    tmp_path: Path, child_code: int, aggregate: int
) -> None:
    from tests.infra_tests.core.test_bounded_run_guardian import _run_copy

    repository = tmp_path.resolve() / "repository"
    scaffold_pipeline(repository)
    result = _run_copy(
        tmp_path,
        r"""
import json
from pathlib import Path
report_stdout=sys.stdout;sys.stdout=sys.stderr
code=int(sys.argv[2])
worker=Path(sys.path[0])/'infrastructure/core/pipeline/report_worker.py'
worker.write_text(f'raise SystemExit({code})\n')
from infrastructure.core.pipeline.executor import PipelineExecutor
from infrastructure.core.pipeline.types import PipelineConfig
executor=PipelineExecutor(PipelineConfig('demo',Path(sys.argv[1]),clean=False,skip_infra=True,run_timeout_seconds=60))
rows=executor.execute_pipeline()
run=executor.run_result(rows)
last=rows[-1].outcome
assert not run.complete and last is not None
print(json.dumps({'exit':run.exit_code,'child':last.child_exit_code,'attempts':list(last.attempt_exit_codes)}),file=report_stdout)
""",
        str(repository),
        str(child_code),
        observer_timeout=85,
    )
    assert result == {"exit": aggregate, "child": child_code, "attempts": [child_code]}
