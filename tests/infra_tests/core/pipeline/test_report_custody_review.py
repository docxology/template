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


@pytest.mark.parametrize(
    "child_code,aggregate,custody_change",
    [
        pytest.param(7, 1, False, id="7-1"),
        pytest.param(124, 124, False, id="124-124"),
        pytest.param(130, 130, False, id="130-130"),
        pytest.param(75, 75, False, id="75-75"),
        pytest.param(75, 75, True, id="cleanup-custody-original75"),
        pytest.param(7, 1, True, id="failure-precedes-cleanup-custody"),
    ],
)
@pytest.mark.timeout(90)
def test_actual_reporting_exit_cannot_be_demoted_by_absent_receipt(
    tmp_path: Path, child_code: int, aggregate: int, custody_change: bool
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
code=int(sys.argv[2]); change=sys.argv[3]=='True'
worker=Path(sys.path[0])/'infrastructure/core/pipeline/report_worker.py'
source=Path(sys.path[0])/'infrastructure/core/_bounded_kill.py'
mutation=(
 "from pathlib import Path\n"
 f"source=Path({str(source)!r})\n"
 "source.write_bytes(source.read_bytes()+b'\\n# actual report cleanup custody change\\n')\n"
) if change else ""
worker.write_text(mutation+f'raise SystemExit({code})\n')
from infrastructure.core.pipeline.executor import PipelineExecutor
from infrastructure.core.pipeline.types import PipelineConfig
executor=PipelineExecutor(PipelineConfig('demo',Path(sys.argv[1]),clean=False,skip_infra=True,run_timeout_seconds=60))
rows=executor.execute_pipeline()
run=executor.run_result(rows)
last=rows[-1].outcome
assert not run.complete and last is not None
assert not (executor.config.runtime_output_dir/'.pipeline/report_finalization.json').exists()
print(json.dumps({'exit':run.exit_code,'child':last.child_exit_code,'attempts':list(last.attempt_exit_codes)}),file=report_stdout)
""",
        str(repository),
        str(child_code),
        str(custody_change),
        observer_timeout=85,
    )
    assert result == {"exit": aggregate, "child": child_code, "attempts": [child_code]}


@pytest.mark.parametrize("receipt_change,aggregate", [("none", 75), ("selection", 1), ("selection-cleanup", 1)])
@pytest.mark.timeout(120)
def test_actual_report_worker_custody_receipt_is_blocked_not_accepted(
    tmp_path: Path, receipt_change: str, aggregate: int
) -> None:
    from tests.infra_tests.core.test_bounded_run_guardian import _run_copy

    repository = tmp_path.resolve() / "repository"
    scaffold_pipeline(repository, ("templates/alpha",))
    result = _run_copy(
        tmp_path,
        r"""
import json,os
from pathlib import Path
report_stdout=sys.stdout;sys.stdout=sys.stderr
root=Path(sys.argv[1]); change=sys.argv[2]; expected=int(sys.argv[3])
source=root/'projects/templates/alpha/src/__init__.py'
worker=Path(sys.path[0])/'infrastructure/core/pipeline/report_worker.py'
cleanup_source=Path(sys.path[0])/'infrastructure/core/_bounded_kill.py'
actual=worker.with_name('_actual_custody_report_worker.py')
worker.rename(actual)
# A real launch adapter changes the owned fixture Source, then executes the
# unchanged report worker. Neither the refusal nor its receipt is fabricated.
worker.write_text(
 "import json,os,runpy\nfrom pathlib import Path\n"
 f"Path({str(source)!r}).write_text('CHANGED_AT_REPORT_LAUNCH = True\\n')\n"
 "try:\n"
 f" runpy.run_path({str(actual)!r},run_name='__main__')\n"
 "except SystemExit as exc:\n"
 f" if exc.code==75 and {change!r}.startswith('selection'):\n"
 "  receipt=Path(os.environ['ACTUAL_REPORT_TEST_RECEIPT'])\n"
 "  payload=json.loads(receipt.read_text())\n"
 "  payload['expected_stage_keys']=['analysis']\n"
 "  receipt.write_text(json.dumps(payload))\n"
 f" if exc.code==75 and {change!r}=='selection-cleanup':\n"
 f"  source=Path({str(cleanup_source)!r})\n"
 "  source.write_bytes(source.read_bytes()+b'\\n# actual report cleanup custody change\\n')\n"
 " raise\n")
from infrastructure.core.pipeline.types import PipelineConfig
config=PipelineConfig('templates/alpha',root,clean=False,shared_infrastructure=True,
 pipeline_path=root/'infrastructure/core/pipeline/pipeline.yaml',run_timeout_seconds=90)
output=config.runtime_output_dir
receipt=output/'.pipeline/report_finalization.json'
os.environ['ACTUAL_REPORT_TEST_RECEIPT']=str(receipt)
from infrastructure.core.pipeline.executor import PipelineExecutor
from infrastructure.core.pipeline.plan import compile_execution_plan
from infrastructure.core.pipeline.worker_transport import results_from_payload
from infrastructure.core.pipeline.outcomes import RunResult,StageStatus
from infrastructure.core.pipeline import report_finalization as reporting
observations=[]
def observe_guardian(frame,event,arg):
 if frame.f_code is reporting.run_bounded_subprocess.__code__:
  if event=='return' and arg is not None:observations.append(arg)
  return observe_guardian
 return None
plan=compile_execution_plan(config,target_stage='infra_tests')
executor=PipelineExecutor(config)
previous=sys.gettrace()
try:
 if change=='selection-cleanup':sys.settrace(observe_guardian)
 rows=executor.execute_plan(plan)
finally:sys.settrace(previous)
if change=='selection-cleanup':
 assert any(child.custody_refused and child.returncode==75 for child in observations), observations
run=executor.run_result(rows)
assert not run.complete and run.exit_code==expected, (rows,run)
assert run.expected_stage_keys==('infra_tests',)
assert rows[0].outcome.status is StageStatus.SUCCEEDED and rows[0].outcome.child_exit_code==0
last=rows[-1].outcome
assert last is not None and last.stage_key=='report_finalization'
assert last.child_exit_code==75 and last.attempt_exit_codes==(75,)
payload=json.loads(receipt.read_text())
assert payload['status']=='blocked' and payload['files']=={}
assert payload['project']==plan.project and payload['plan_digest']==plan.digest
refusals=results_from_payload(payload['stage_results'])
refusal_run=RunResult.from_results(refusals,plan.expected_stage_keys)
assert not refusal_run.complete and refusal_run.exit_code==75
assert len(refusals)==1 and refusals[0].outcome.child_exit_code is None
assert refusals[0].outcome.attempt_exit_codes==()
diagnostic=refusals[0].outcome.diagnostic
observation=json.loads(diagnostic.split('fingerprint_diagnostics=',1)[1])
assert observation['expected_total']==plan.source_identity
assert observation['observed_total']!=plan.source_identity
assert set(observation['components'])=={'source','python','tools'}
if change=='none':
 assert last.status is StageStatus.BLOCKED and last.diagnostic==diagnostic
 assert payload['expected_stage_keys']==list(plan.expected_stage_keys)
else:
 assert last.status is StageStatus.FAILED
assert not any((output/'reports'/name).exists() for name in
 ('pipeline_report.json','pipeline_report.html','pipeline_report.md'))
record=json.loads((output/'.pipeline/execution.json').read_text())
assert record['complete'] is False and record['exit_code']==expected
assert record['expected_stage_keys']==['infra_tests']
assert (root/'process_order.log').read_text().splitlines()==['templates/alpha:infra']
print(json.dumps({'exit':run.exit_code,'complete':run.complete,'actual_report_child':last.child_exit_code,
 'inner_child':refusals[0].outcome.child_exit_code,'receipt_status':payload['status'],
 'no_report_acceptance':True}),file=report_stdout)
""",
        str(repository),
        receipt_change,
        str(aggregate),
        observer_timeout=110,
    )
    assert result == {
        "exit": aggregate,
        "complete": False,
        "actual_report_child": 75,
        "inner_child": None,
        "receipt_status": "blocked",
        "no_report_acceptance": True,
    }
