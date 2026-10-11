"""Typed guardian refusals preserve child evidence and always finish cleanup."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from tests.infra_tests.core.test_bounded_run_guardian import _run_copy

pytestmark = [pytest.mark.timeout(60), pytest.mark.skipif(os.name == "nt", reason="POSIX guardian contract")]


def test_actual_source_custody_refuses_before_command_launch(tmp_path: Path) -> None:
    result = _run_copy(
        tmp_path,
        r"""
import json, os
from pathlib import Path
from infrastructure.core.execution_boundary import run_bounded_subprocess
source = Path(sys.path[0]) / 'infrastructure/core/_bounded_kill.py'
source.write_text(source.read_text() + '\n# changed before guardian admission\n')
marker = Path.cwd() / 'must-not-launch'
body = "from pathlib import Path;Path(" + repr(str(marker)) + ").write_text('unapproved')"
result = run_bounded_subprocess([sys.executable, '-I', '-c', body], cwd=Path.cwd(), env=dict(os.environ), timeout=5)
assert result.returncode == 75 and result.custody_refused and result.original_returncode is None
assert not marker.exists()
print(json.dumps({'exit':result.returncode,'original':result.original_returncode,'custody':result.custody_refused}))
""",
    )
    assert result == {"exit": 75, "original": None, "custody": True}


def test_actual_cleanup_custody_refusal_preserves_child_seven_and_reaps_detached(tmp_path: Path) -> None:
    result = _run_copy(
        tmp_path,
        r"""
import json, os, time
from pathlib import Path
from infrastructure.core.execution_boundary import run_bounded_subprocess
source = Path(sys.path[0]) / 'infrastructure/core/_bounded_kill.py'
marker = Path.cwd() / 'detached-leak'
descendant = "import time;from pathlib import Path;time.sleep(1.5);Path(" + repr(str(marker)) + ").write_text('leaked')"
body = ("import subprocess,sys,time;from pathlib import Path;"
        "subprocess.Popen([sys.executable,'-I','-c',sys.argv[1]],start_new_session=True);"
        "p=Path(sys.argv[2]);p.write_text(p.read_text()+'\\n# actual concurrent change\\n');"
        "time.sleep(.2);raise SystemExit(7)")
result = run_bounded_subprocess([sys.executable, '-I', '-c', body, descendant, str(source)],
                                cwd=Path.cwd(), env=dict(os.environ), timeout=8)
assert result.returncode == 75 and result.custody_refused and result.original_returncode == 7, result
time.sleep(1.6)
assert not marker.exists()
print(json.dumps({'exit':result.returncode,'original':result.original_returncode,'custody':result.custody_refused,
                  'detached_reaped':True}))
""",
    )
    assert result == {"exit": 75, "original": 7, "custody": True, "detached_reaped": True}


def test_expired_budget_refuses_guardian_and_child_launch(tmp_path: Path) -> None:
    result = _run_copy(
        tmp_path,
        r"""
import json, os, math
from pathlib import Path
from infrastructure.core.execution_boundary import run_bounded_subprocess
scratch = Path.cwd() / 'startup-scratch'
scratch.mkdir(mode=0o700)
os.environ['TMPDIR'] = str(scratch)
marker = Path.cwd() / 'must-not-launch'
body = "from pathlib import Path;Path(" + repr(str(marker)) + ").write_text('late')"
result = run_bounded_subprocess([sys.executable, '-I', '-c', body], cwd=Path.cwd(), env=dict(os.environ),
                                timeout=math.nextafter(0.0, 1.0))
assert result.returncode == 124 and result.timed_out and result.original_returncode is None
assert not marker.exists() and not tuple(scratch.iterdir())
print(json.dumps({'exit':result.returncode,'timed_out':True,'no_child_or_guardian':True}))
""",
    )
    assert result == {"exit": 124, "timed_out": True, "no_child_or_guardian": True}


# Whole-operation budget for the SIGINT-during-cleanup control. Guardian
# startup (source admission plus a fresh audited bytecode cache) is charged to
# this same deadline, and it grows with the audited package. The observer must
# stop the armed guardian before the deadline expires, otherwise the guardian
# completes cleanup first and there is no cleanup wait left to interrupt.
# Hosted runners under ``-n auto`` load have consumed most of a 3.5 s budget in
# startup alone, so the budget leaves several seconds of margin.
_SIGINT_CLEANUP_BUDGET_SECONDS = 12.0


@pytest.mark.timeout(120)
def test_timeout_cleanup_sigint_reaps_actual_root_and_detached_writer(tmp_path: Path) -> None:
    result = _run_copy(
        tmp_path,
        r'''
import json, os, signal, subprocess, time
from pathlib import Path
from infrastructure.core.execution_boundary import run_bounded_subprocess,terminate_bounded_run_processes
budget=float(sys.argv[1])
directory=Path.cwd();pids=directory/'actual-timeout-pids.json'
stopped=directory/'guardian-stopped';signalled=directory/'cleanup-interrupted';marker=directory/'detached-survived'
observer_body=r"""
import json,os,signal,subprocess,sys,time
from pathlib import Path
directory=Path(sys.argv[1]);controller=int(sys.argv[2]);pids=directory/'actual-timeout-pids.json'
deadline=time.monotonic()+float(sys.argv[3])
while not pids.exists() and time.monotonic()<deadline: time.sleep(.01)
assert pids.exists(), 'actual bounded root did not start'
root=json.loads(pids.read_text())['root']
# The actual root has launched; allow the independent guardian to finish ARM.
time.sleep(.5)
rows=subprocess.run(['/bin/ps','-axo','pid=,ppid=,command='],capture_output=True,text=True,timeout=3).stdout
guardians=[]
for row in rows.splitlines():
 parts=row.split(None,2)
 if len(parts)==3 and int(parts[1])==controller and int(parts[0]) not in {os.getpid(),root} and 'template-guardian-bytecode-' in parts[2]:
  guardians.append(int(parts[0]))
assert len(guardians)==1, guardians
os.kill(guardians[0],signal.SIGSTOP)
(directory/'guardian-stopped').write_text(str(guardians[0]))
while time.monotonic()<deadline:
 state=subprocess.run(['/bin/ps','-o','state=','-p',str(root)],capture_output=True,text=True,timeout=3).stdout.strip()
 if state.startswith('Z'):
  (directory/'cleanup-interrupted').write_text('root killed while guardian cleanup waits')
  os.kill(controller,signal.SIGINT)
  break
 time.sleep(.01)
else: raise AssertionError('actual root did not reach killed, unreaped timeout state')
"""
observer=subprocess.Popen([sys.executable,'-I','-c',observer_body,str(directory),str(os.getpid()),repr(budget+10)],
 stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
descendant="import time;from pathlib import Path;time.sleep("+repr(budget+1.5)+");Path("+repr(str(marker))+").write_text('leaked')"
body="import json,os,subprocess,sys,time;from pathlib import Path;child=subprocess.Popen([sys.executable,'-I','-c',sys.argv[1]],start_new_session=True);Path(sys.argv[2]).write_text(json.dumps({'root':os.getpid(),'detached':child.pid}));time.sleep(30)"
interruption=None;proc=None;guardian=None;token=None
try:
 try:
  run_bounded_subprocess([sys.executable,'-I','-c',body,descendant,str(pids)],cwd=directory,
                         env=dict(os.environ),timeout=budget)
 except KeyboardInterrupt as exc:
  # Retain the real traceback so Popen.__del__ cannot hide missing explicit reaping.
  interruption=exc;trace=exc.__traceback__
  while trace is not None:
   if trace.tb_frame.f_code.co_name=='run_bounded_subprocess':
    proc=trace.tb_frame.f_locals['proc'];guardian=trace.tb_frame.f_locals['guardian'];token=trace.tb_frame.f_locals['run_token']
   trace=trace.tb_next
 if interruption is None or not (stopped.exists() and signalled.exists()):
  try: observer.wait(timeout=5)
  except subprocess.TimeoutExpired: pass
  raise AssertionError(('timeout cleanup was not interrupted while waiting for the stopped guardian',
                        interruption is not None, stopped.exists(), signalled.exists(), observer.poll(),
                        observer.stderr.read() if observer.poll() is not None else 'observer still running'))
 observed=json.loads(pids.read_text())
 assert proc is not None and proc.returncode==-signal.SIGKILL, 'actual timeout root was not explicitly reaped'
 try: os.waitpid(observed['root'],os.WNOHANG)
 except ChildProcessError: pass
 else: raise AssertionError('interrupted timeout returned an unreaped direct child')
 assert guardian is not None and guardian.process.poll() is not None and guardian.cache is None
 try: os.kill(observed['detached'],0)
 except ProcessLookupError: pass
 else:
  state=subprocess.run(['/bin/ps','-o','state=','-p',str(observed['detached'])],capture_output=True,text=True,timeout=3).stdout.strip()
  assert not state or state.startswith('Z'), 'actual detached writer remains running'
 assert not marker.exists()
 observer.wait(timeout=5)
 assert observer.returncode==0, observer.stderr.read()
 print(json.dumps({'interrupted_exit':130,'original_child':proc.returncode,'root_reaped':True,'detached_reaped':True}))
finally:
 if token is not None: terminate_bounded_run_processes(token)
 if guardian is not None: guardian.close()
 if proc is not None and proc.poll() is None: proc.kill();proc.wait(timeout=5)
 if observer.poll() is None: observer.kill();observer.wait(timeout=5)
 if observer.stderr is not None: observer.stderr.close()
''',
        repr(_SIGINT_CLEANUP_BUDGET_SECONDS),
        observer_timeout=_SIGINT_CLEANUP_BUDGET_SECONDS + 45,
    )
    assert result == {"interrupted_exit": 130, "original_child": -9, "root_reaped": True, "detached_reaped": True}
