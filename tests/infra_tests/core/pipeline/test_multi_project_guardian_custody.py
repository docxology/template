"""Real copied-runtime guardian failures cannot escape multi-project cleanup."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from tests.infra_tests.core.test_bounded_run_guardian import _run_copy
from tests.infra_tests.orchestration._pipeline_fixture import scaffold_pipeline

pytestmark = [pytest.mark.timeout(60), pytest.mark.skipif(os.name == "nt", reason="POSIX guardian contract")]


def test_c4_startup_custody_is_blocked_without_launching_worker(tmp_path: Path) -> None:
    repository = tmp_path.resolve() / "repository"
    scaffold_pipeline(repository, ("templates/alpha",))
    result = _run_copy(
        tmp_path,
        r"""
import json,time
report_stdout=sys.stdout;sys.stdout=sys.stderr
from pathlib import Path
from infrastructure.core.pipeline.multi_project_runtime import freeze_project_plans,execute_frozen_specs
root=Path(sys.argv[1])
specs=freeze_project_plans(('templates/alpha',),root,mode='core',resume=False,timeout=20)
source=Path(sys.path[0])/'infrastructure/core/_bounded_kill.py'
source.write_bytes(source.read_bytes()+b'\n# changed actual guardian source before startup\n')
rows,runs=execute_frozen_specs(specs,workers=1,deadline=time.monotonic()+20)
run=runs['templates/alpha']
assert run.exit_code==75 and not run.complete
assert run.expected_stage_keys==('analysis',)
assert rows['templates/alpha'][0].outcome.child_exit_code is None
assert not (root/'process_order.log').exists()
print(json.dumps({'exit':run.exit_code,'no_child':True,'expected':list(run.expected_stage_keys)}),file=report_stdout)
""",
        str(repository),
    )
    assert result == {"exit": 75, "no_child": True, "expected": ["analysis"]}


@pytest.mark.parametrize(
    "worker_exit,custody_change,parent_interrupted",
    [
        (130, False, False),
        (-2, True, False),
        (124, False, False),
        pytest.param(124, False, True, id="parent-interrupted-worker-timeout"),
    ],
)
def test_actual_worker_control_exit_without_receipt_keeps_precedence(
    tmp_path: Path, worker_exit: int, custody_change: bool, parent_interrupted: bool
) -> None:
    """A genuine interrupted/timed-out worker needs no success receipt to fail truthfully."""
    repository = tmp_path.resolve() / "repository"
    scaffold_pipeline(repository, ("templates/alpha",))
    result = _run_copy(
        tmp_path,
        r'''
import json,subprocess,time
report_stdout=sys.stdout;sys.stdout=sys.stderr
from pathlib import Path
from infrastructure.core._bounded_run_guardian import start_bounded_run_guardian
from infrastructure.core.execution_boundary import build_bounded_env,build_bounded_run_env
from infrastructure.core.pipeline.multi_project_runtime import _Running,_finish,freeze_project_plans
from infrastructure.core.pipeline.multi_project_output import BoundedWorkerOutput
from infrastructure.core.pipeline.outcomes import StageStatus
root=Path(sys.argv[1]); observed_code=int(sys.argv[2]); change=sys.argv[3]=='True'; interrupted=sys.argv[4]=='True'
spec=freeze_project_plans(('templates/alpha',),root,mode='core',resume=False,timeout=20)[0]
environment=build_bounded_env(); process_env,token=build_bounded_run_env(environment)
deadline=time.monotonic()+20
guardian=start_bounded_run_guardian(environment,deadline_monotonic=deadline)
assert guardian is not None
source=Path(sys.path[0])/'infrastructure/core/_bounded_kill.py'
receipt=Path.cwd()/'absent-worker-receipt.json'
program=r"""
import os,signal,sys,time
from pathlib import Path
time.sleep(.1)
if sys.argv[2]=='True':
 source=Path(sys.argv[1]);source.write_bytes(source.read_bytes()+b'\n# changed actual cleanup source\n')
code=int(sys.argv[3])
if code==-2:
 os.kill(os.getpid(),signal.SIGINT)
raise SystemExit(code)
"""
process=subprocess.Popen([sys.executable,'-I','-c',program,str(source),str(change),str(observed_code)],
 env=process_env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
assert process.stdout is not None
output=BoundedWorkerOutput(process.stdout)
running=_Running(spec,process,guardian,token,'actual-control-exit',receipt,Path.cwd(),output)
try:
 guardian.arm(root_pid=process.pid,run_token=token,deadline_monotonic=deadline)
 process.wait(timeout=5)
 assert process.returncode==observed_code and not receipt.exists()
 rows,run=_finish(running,deadline,StageStatus.INTERRUPTED if interrupted else None)
 expected=124 if observed_code==124 and not interrupted else 130
 assert run.exit_code==expected and not run.complete, (rows,run)
 assert run.expected_stage_keys==('analysis',) and len(rows)==1
 outcome=rows[0].outcome
 assert outcome.stage_key=='multi_project_runtime' and outcome.child_exit_code==observed_code
 assert outcome.status.value==('timed_out' if expected==124 else 'interrupted')
 assert not output.thread.is_alive() and guardian.process.poll() is not None and guardian.cache is None
 assert not receipt.exists() and not (root/'process_order.log').exists()
 print(json.dumps({'exit':run.exit_code,'worker_child':outcome.child_exit_code,'no_receipt':True,
  'cleanup_finished':True}),file=report_stdout)
finally:
 try: running.close(terminate=True)
 except Exception: pass
 output.close()
''',
        str(repository),
        str(worker_exit),
        str(custody_change),
        str(parent_interrupted),
    )
    assert result == {
        "exit": 124 if worker_exit == 124 and not parent_interrupted else 130,
        "worker_child": worker_exit,
        "no_receipt": True,
        "cleanup_finished": True,
    }


@pytest.mark.parametrize("stage_exit,aggregate_exit", [(0, 75), (7, 1)])
def test_c4_cleanup_custody_retains_real_child_evidence_and_reaps_descendants(
    tmp_path: Path,
    stage_exit: int,
    aggregate_exit: int,
) -> None:
    repository = tmp_path.resolve() / "repository"
    scaffold_pipeline(repository, ("templates/alpha",))
    result = _run_copy(
        tmp_path,
        r'''
import json,os,subprocess,time
from dataclasses import asdict
report_stdout=sys.stdout;sys.stdout=sys.stderr
from pathlib import Path
from infrastructure.core._bounded_run_guardian import start_bounded_run_guardian
from infrastructure.core.execution_boundary import build_bounded_env,build_bounded_run_env
from infrastructure.core.pipeline.multi_project_runtime import WORKER_SCHEMA,_Running,_finish,freeze_project_plans
from infrastructure.core.pipeline.multi_project_output import BoundedWorkerOutput
from infrastructure.core.pipeline.types import PipelineStageResult
from infrastructure.core.pipeline.outcomes import StageOutcome,StageStatus
root=Path(sys.argv[1]); stage_code=int(sys.argv[2]); expected=int(sys.argv[3])
spec=freeze_project_plans(('templates/alpha',),root,mode='core',resume=False,timeout=20)[0]
environment=build_bounded_env(); process_env,token=build_bounded_run_env(environment)
deadline=time.monotonic()+20
guardian=start_bounded_run_guardian(environment,deadline_monotonic=deadline)
assert guardian is not None
source=Path(sys.path[0])/'infrastructure/core/_bounded_kill.py'
marker=Path.cwd()/'detached-leak'
receipt=Path.cwd()/'actual-worker-result.json'
binding={'schema_version':WORKER_SCHEMA,'nonce':'actual-control','project':spec.plan.project,
 'shared_infrastructure':False,
 'plan_digest':spec.plan.digest,'source_identity':spec.plan.source_identity,
 'environment_identity':spec.plan.environment_identity,'expected_stage_keys':list(spec.plan.expected_stage_keys)}
binding['stage_results']=[asdict(PipelineStageResult(1,'Actual measured computation',True,.1,
 stage_key='analysis',outcome=StageOutcome('analysis',StageStatus.SUCCEEDED,0)))]
descendant="import time;from pathlib import Path;time.sleep(1.5);Path("+repr(str(marker))+").write_text('leaked')"
program=r"""
import json,subprocess,sys,time
from pathlib import Path
time.sleep(.1)
subprocess.Popen([sys.executable,'-I','-c',sys.argv[1]],start_new_session=True)
source=Path(sys.argv[2]);source.write_bytes(source.read_bytes()+b'\n# actual concurrent guardian source mutation\n')
code=int(sys.argv[3])
observed=subprocess.run([sys.executable,'-I','-c',f'assert 2+2==4;raise SystemExit({code})'],timeout=5).returncode
assert observed==code
payload=json.loads(sys.argv[5])
status='succeeded' if observed==0 else 'failed'
row=payload['stage_results'][0]
row.update(success=observed==0,exit_code=observed,stage_completed=observed==0)
row['outcome'].update(status=status,child_exit_code=observed,attempt_exit_codes=[observed])
payload['exit_code']=0 if observed==0 else 1
Path(sys.argv[4]).write_text(json.dumps(payload))
time.sleep(.1)
raise SystemExit(payload['exit_code'])
"""
process=subprocess.Popen([sys.executable,'-I','-c',program,descendant,str(source),str(stage_code),str(receipt),
 json.dumps(binding)],env=process_env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
 start_new_session=True)
assert process.stdout is not None
output=BoundedWorkerOutput(process.stdout)
running=_Running(spec,process,guardian,token,'actual-control',receipt,Path.cwd(),output)
try:
 guardian.arm(root_pid=process.pid,run_token=token,deadline_monotonic=deadline)
 process.wait(timeout=10)
 rows,run=_finish(running,deadline)
 assert run.exit_code==expected and not run.complete, (rows,run)
 assert len(rows)==2 and rows[0].outcome.child_exit_code==stage_code, rows
 assert rows[1].outcome.status.value=='blocked' and rows[1].outcome.child_exit_code==process.returncode
 assert not output.thread.is_alive() and guardian.process.poll() is not None and guardian.cache is None
 time.sleep(1.6)
 assert not marker.exists()
 print(json.dumps({'exit':run.exit_code,'child':process.returncode,'stage_child':rows[0].outcome.child_exit_code,
  'detached_reaped':True,'output_drained':True}),file=report_stdout)
finally:
 try: running.close(terminate=True)
 except Exception: pass
 output.close()
''',
        str(repository),
        str(stage_exit),
        str(aggregate_exit),
    )
    assert result == {
        "exit": aggregate_exit,
        "child": 0 if stage_exit == 0 else 1,
        "stage_child": stage_exit,
        "detached_reaped": True,
        "output_drained": True,
    }


def test_sigint_during_stopped_guardian_cleanup_still_sweeps_actual_detached_writer(tmp_path: Path) -> None:
    repository = tmp_path.resolve() / "repository"
    scaffold_pipeline(repository, ("templates/alpha",))
    result = _run_copy(
        tmp_path,
        r"""
import json,os,signal,subprocess,time
report_stdout=sys.stdout;sys.stdout=sys.stderr
from pathlib import Path
from infrastructure.core._bounded_run_guardian import start_bounded_run_guardian
from infrastructure.core.execution_boundary import build_bounded_env,build_bounded_run_env,terminate_bounded_run_processes
from infrastructure.core.pipeline.multi_project_runtime import _Running,_finish,freeze_project_plans
from infrastructure.core.pipeline.multi_project_output import BoundedWorkerOutput
spec=freeze_project_plans(('templates/alpha',),Path(sys.argv[1]),mode='core',resume=False,timeout=20)[0]
environment=build_bounded_env();process_env,token=build_bounded_run_env(environment)
deadline=time.monotonic()+20
guardian=start_bounded_run_guardian(environment,deadline_monotonic=deadline)
assert guardian is not None
marker=Path.cwd()/'must-not-survive-cleanup'
pid_path=Path.cwd()/'actual-detached-pid'
descendant="import os,time;from pathlib import Path;time.sleep(1.5);Path("+repr(str(marker))+").write_text('survived')"
program="import subprocess,sys,time;from pathlib import Path;child=subprocess.Popen([sys.executable,'-I','-c',sys.argv[1]],start_new_session=True);Path(sys.argv[2]).write_text(str(child.pid));time.sleep(.2)"
process=subprocess.Popen([sys.executable,'-I','-c',program,descendant,str(pid_path)],env=process_env,
 stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
assert process.stdout is not None
output=BoundedWorkerOutput(process.stdout)
running=_Running(spec,process,guardian,token,'cleanup-control',Path.cwd()/'absent-receipt',Path.cwd(),output)
sender=None
try:
 guardian.arm(root_pid=process.pid,run_token=token,deadline_monotonic=deadline)
 os.kill(guardian.process.pid,signal.SIGSTOP)
 process.wait(timeout=5)
 assert process.returncode==0 and pid_path.exists()
 sender=subprocess.Popen([sys.executable,'-I','-c',
  'import os,signal,sys,time;time.sleep(.1);os.kill(int(sys.argv[1]),signal.SIGINT)',str(os.getpid())],
  stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 rows,run=_finish(running,deadline)
 assert run.exit_code==130 and rows[0].outcome.child_exit_code==0, (rows,run)
 assert not output.thread.is_alive()
 time.sleep(1.6)
 assert not marker.exists(), 'actual detached writer survived interrupted guardian cleanup'
 assert guardian.process.poll() is not None and guardian.cache is None
 print(json.dumps({'exit':run.exit_code,'original_child':process.returncode,'detached_reaped':True}),file=report_stdout)
finally:
 # The pre-repair control must never leave its deliberately stopped guardian
 # or bounded writer alive, even when the observed production boundary fails.
 terminate_bounded_run_processes(token)
 guardian.close()
 if process.poll() is None:
  process.kill();process.wait(timeout=5)
 if sender is not None:
  sender.wait(timeout=5)
 output.finish();output.close()
""",
        str(repository),
    )
    assert result == {"exit": 130, "original_child": 0, "detached_reaped": True}
