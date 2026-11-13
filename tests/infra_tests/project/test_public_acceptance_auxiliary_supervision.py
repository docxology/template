"""Real bounded children, detached descendants and auxiliary cleanup custody."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import psutil
import pytest

from infrastructure.core._bounded_kill import observe_bounded_run_processes
from infrastructure.core.execution_boundary import build_bounded_run_env
from infrastructure.project.public_acceptance_auxiliary_supervision import (
    MAX_STREAM_BYTES,
    complete_auxiliary_observation,
    supervise,
    supervise_sandbox_transfer_api,
)


def _running(pid: int) -> bool:
    """Observe live work; a zombie is exited, not evidence that it was reaped."""
    try:
        process = psutil.Process(pid)
        return bool(process.is_running() and process.status() != psutil.STATUS_ZOMBIE)
    except psutil.NoSuchProcess:
        return False


def _remove_owned_control(pid: int, command: str) -> None:
    """Keep a failing control safe without touching a reused unrelated PID."""
    try:
        process = psutil.Process(pid)
        if process.cmdline()[-1:] == [command]:
            process.kill()
    except (psutil.NoSuchProcess, psutil.ZombieProcess):
        pass


def _stream(root: Path, observation: dict[str, Any], channel: str) -> bytes:
    binding = observation["streams"][channel]
    path = binding["path"]
    assert isinstance(path, str)
    contents = (root / path).read_bytes()
    assert hashlib.sha256(contents).hexdigest() == binding["sha256"]
    return contents


def test_expired_deadline_never_launches_a_child(tmp_path: Path) -> None:
    marker = tmp_path / "forbidden-launch"
    deadline = time.monotonic() - 1
    observation = supervise(
        [sys.executable, "-I", "-c", f"from pathlib import Path; Path({str(marker)!r}).touch()"],
        tmp_path,
        tmp_path / "output/readiness/expired",
        deadline,
    )
    assert not marker.exists()
    assert observation["pid"] is observation["exit_code"] is None
    assert observation["timed_out"] is True
    assert observation["accepted"] is observation["cleanup"]["verified"] is False
    assert observation["cleanup"]["guardian_pid"] is None
    assert observation["original_deadline_monotonic"] == deadline
    assert _stream(tmp_path, observation, "stdout") == _stream(tmp_path, observation, "stderr") == b""
    with pytest.raises(TimeoutError, match="original bounded-run census deadline exhausted"):
        observe_bounded_run_processes(uuid.uuid4().hex, deadline=deadline)


@pytest.mark.parametrize("deadline", [float("inf"), float("nan"), True])
def test_deadline_must_be_finite_before_evidence_or_launch(tmp_path: Path, deadline: float) -> None:
    with pytest.raises(ValueError, match="deadline must be finite"):
        supervise(
            [sys.executable, "-I", "-c", "pass"],
            tmp_path,
            tmp_path / "output/readiness/invalid",
            deadline,
        )
    with pytest.raises(ValueError, match="finite original deadline"):
        observe_bounded_run_processes(uuid.uuid4().hex, deadline=deadline)
    assert not (tmp_path / "output").exists()


def test_scoped_transfer_requires_explicit_token_without_ambient_auth_fallback(tmp_path: Path) -> None:
    source_root = Path(__file__).resolve().parents[3]
    sentinel = "harmless-" + uuid.uuid4().hex
    program = """import os,sys,time
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from infrastructure.project.public_acceptance_auxiliary import run_sandbox_transfer
from infrastructure.project.public_acceptance_auxiliary_supervision import supervise_sandbox_transfer_api
root=Path(sys.argv[2])
def no_launch(event,args):
 if event=='subprocess.Popen':raise AssertionError('missing nomination launched a process')
sys.addaudithook(no_launch)
for token in (None,''):
 try:
  supervise_sandbox_transfer_api([sys.executable,'api','--hostname','github.com','repos/docxology/template'],
   root,root/'output/readiness/forbidden',time.monotonic()+10,
   repository='docxology/template',artifact_id='1',gh_token=token)
 except ValueError as error:
  assert 'explicit existing GH_TOKEN nomination' in str(error)
 else:raise AssertionError('ambient credential replaced explicit nomination')
try:
 run_sandbox_transfer(root/'missing-source-root',export_receipt=root/'missing.json',
  upload_outputs=root/'missing-outputs.json',downloaded_directory=root/'output/readiness/download',
  repository='docxology/template',run_id='1',source_commit='a'*40,
  evidence_dir=root/'output/readiness/transfer')
except FileNotFoundError:pass
else:raise AssertionError('missing Source root was admitted')
assert 'GH_TOKEN' not in os.environ
try:
 run_sandbox_transfer(root,export_receipt=root/'missing.json',upload_outputs=root/'missing-outputs.json',
  downloaded_directory=root/'output/readiness/download',repository='docxology/template',run_id='1',
  source_commit='a'*40,evidence_dir=root/'output/readiness/transfer')
except ValueError as error:
 assert 'explicit existing GH_TOKEN nomination' in str(error)
else:raise AssertionError('GITHUB_TOKEN or local gh state replaced missing GH_TOKEN')
assert not (root/'output').exists()
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", program, str(source_root), str(tmp_path)],
        env={"PATH": os.environ.get("PATH", os.defpath), "GH_TOKEN": sentinel, "GITHUB_TOKEN": sentinel},
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert sentinel not in result.stdout + result.stderr
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize(
    "fault", ["command", "executable", "hostname", "owner", "artifact", "download", "absolute", "method", "query"]
)
def test_scoped_transfer_refuses_arbitrary_commands_hosts_and_endpoints(tmp_path: Path, fault: str) -> None:
    gh = shutil.which("gh")
    if gh is None:
        pytest.skip("requires the existing gh CLI, never a replacement executable")
    command = [gh, "api", "--hostname", "github.com", "repos/docxology/template/actions/artifacts/1"]
    if fault == "command":
        command = [sys.executable, "-I", "-c", "raise AssertionError('forbidden launch')"]
    elif fault == "executable":
        command[0] = sys.executable
    elif fault == "hostname":
        command[3] = "example.invalid"
    elif fault == "owner":
        command[-1] = "repos/another/owner/actions/artifacts/1"
    elif fault == "artifact":
        command[-1] = "repos/docxology/template/actions/artifacts/2"
    elif fault == "download":
        command[-1] += "/zip"
    elif fault == "absolute":
        command[-1] = "https://example.invalid/leak"
    elif fault == "method":
        command[1:1] = ["--method", "POST"]
    elif fault == "query":
        command[-1] += "?per_page=100"
    with pytest.raises(ValueError, match="arbitrary commands, hosts or endpoints"):
        supervise_sandbox_transfer_api(
            command,
            tmp_path,
            tmp_path / "output/readiness/forbidden",
            time.monotonic() + 10,
            repository="docxology/template",
            artifact_id="1",
            gh_token="harmless-" + uuid.uuid4().hex,
        )
    assert not (tmp_path / "output").exists()


@pytest.mark.timeout(90)
def test_actual_scoped_transfer_only_fixed_api_children_receive_nominated_token(tmp_path: Path) -> None:
    """Real gh, kernel environments and a refusing loopback proxy; no remote success claim."""
    if shutil.which("gh") is None:
        pytest.skip("requires the existing gh CLI, never a replacement executable")
    source_root = Path(__file__).resolve().parents[3]
    sentinel = "harmless-" + uuid.uuid4().hex
    program = """import json,os,shutil,socketserver,sys,threading,time
from pathlib import Path
import psutil
sys.path.insert(0,sys.argv[1])
from infrastructure.project.public_acceptance_auxiliary_supervision import (
 complete_auxiliary_observation,supervise,supervise_sandbox_transfer_api)
root=Path(sys.argv[2])
nominated=os.environ.pop('GH_TOKEN')
os.environ['GH_TOKEN']='ambient-not-nominated'
protected={'GH_TOKEN','GITHUB_TOKEN','GH_ENTERPRISE_TOKEN','UNRELATED_TOKEN'}
gh=shutil.which('gh')
git=shutil.which('git')
assert gh is not None and git is not None
commands=[
 [gh,'api','--hostname','github.com','repos/docxology/template/actions/artifacts/1'],
 [gh,'api','--hostname','github.com','repos/docxology/template']]
ordinary=[sys.executable,'-I','-c',
 "import os; assert {'GH_TOKEN','GITHUB_TOKEN','GH_ENTERPRISE_TOKEN','UNRELATED_TOKEN'}.isdisjoint(os.environ)"]
checkout=[git,'rev-parse','HEAD']
launches=[]
def audit(event,args):
 if event!='subprocess.Popen':return
 _,argv,_,environment=args
 argv=list(argv)
 guardian=argv[1:4]==['-I','-S','-c']
 if argv in commands:
  assert environment is not None and environment.get('GH_TOKEN')==nominated
  assert (protected-{'GH_TOKEN'}).isdisjoint(environment)
  launches.append('api')
 elif argv in (ordinary,checkout) or guardian:
  assert environment is not None and protected.isdisjoint(environment)
  launches.append('guardian' if guardian else 'ordinary')
sys.addaudithook(audit)
deadline=time.monotonic()+60
records=[
 supervise(ordinary,root,root/'output/readiness/ordinary',deadline),
 supervise(checkout,root,root/'output/readiness/checkout',deadline)]
assert records[0]['exit_code']==0
assert all(complete_auxiliary_observation(record) for record in records)
observed=[]
errors=[]
class RefusingProxy(socketserver.BaseRequestHandler):
 def handle(self):
  try:
   self.request.settimeout(5)
   request=b''
   while b'\\r\\n\\r\\n' not in request and len(request)<8192:
    block=self.request.recv(4096)
    if not block:break
    request+=block
   assert request.startswith(b'CONNECT api.github.com:443 HTTP/1.1\\r\\n')
   assert nominated.encode() not in request
   children=psutil.Process().children()
   api=[process for process in children if process.cmdline() in commands]
   guardians=[process for process in children if process.cmdline()[1:4]==['-I','-S','-c']]
   assert len(api)==len(guardians)==1
   environment=api[0].environ()
   assert environment.get('GH_TOKEN')==nominated
   assert (protected-{'GH_TOKEN'}).isdisjoint(environment)
   assert protected.isdisjoint(guardians[0].environ())
   observed.append((api[0].pid,api[0].cmdline()))
  except BaseException as error:
   errors.append(error)
  finally:
   try:
    self.request.sendall(b'HTTP/1.1 502 Bad Gateway\\r\\nContent-Length: 0\\r\\nConnection: close\\r\\n\\r\\n')
   except OSError:pass
with socketserver.TCPServer(('127.0.0.1',0),RefusingProxy) as proxy:
 address='http://127.0.0.1:'+str(proxy.server_address[1])
 for key in ('HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','http_proxy','https_proxy','all_proxy'):
  os.environ[key]=address
 os.environ['NO_PROXY']=os.environ['no_proxy']=''
 thread=threading.Thread(target=proxy.serve_forever,kwargs={'poll_interval':0.02},daemon=True)
 thread.start()
 try:
  for label,command in zip(('artifact','repository'),commands,strict=True):
   record=supervise_sandbox_transfer_api(command,root,root/'output/readiness'/label,deadline,
    repository='docxology/template',artifact_id='1',gh_token=nominated)
   records.append(record)
   assert complete_auxiliary_observation(record),record
   assert record['exit_code'] not in (0,4)
   assert record['command']==command
   assert record['original_deadline_monotonic']==deadline
   assert record['executable_sha256_before']==record['executable_sha256_after']
 finally:
  proxy.shutdown()
  thread.join(timeout=5)
assert not thread.is_alive()
if errors:raise errors[0]
assert observed==[(record['pid'],record['command']) for record in records[2:]]
assert launches.count('api')==2 and launches.count('guardian')==4 and launches.count('ordinary')==2
assert nominated not in json.dumps(records)
assert all(nominated.encode() not in path.read_bytes() for path in root.rglob('*') if path.is_file())
assert os.environ['GH_TOKEN']=='ambient-not-nominated'
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", program, str(source_root), str(tmp_path)],
        env={
            "PATH": os.environ.get("PATH", os.defpath),
            "HOME": str(tmp_path / "home"),
            "GH_CONFIG_DIR": str(tmp_path / "gh-config"),
            "GH_PROMPT_DISABLED": "1",
            "SOURCE_DATE_EPOCH": "1700000000",
            "GH_TOKEN": sentinel,
            "GITHUB_TOKEN": "unselected-control",
            "GH_ENTERPRISE_TOKEN": "unselected-control",
            "UNRELATED_TOKEN": "unselected-control",
        },
        capture_output=True,
        text=True,
        timeout=75,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert sentinel not in result.stdout + result.stderr


@pytest.mark.parametrize("forward", [False, True])
def test_original_failure_streams_binary_and_bootstrap_are_preserved(tmp_path: Path, capsys, forward: bool) -> None:
    from infrastructure.project.public_acceptance_auxiliary_validation import _supervision_diagnostic

    bootstrap = {"declared": "actual control"}
    observation = supervise(
        [
            sys.executable,
            "-I",
            "-c",
            "import sys; sys.stdout.buffer.write(b'actual\\x00stdout'); "
            "sys.stderr.buffer.write(b'actual\\x00stderr'); raise SystemExit(17)",
        ],
        tmp_path,
        tmp_path / "output/readiness/original-failure",
        time.monotonic() + 20,
        bootstrap_payload=bootstrap,
        stream_diagnostics=forward,
    )
    assert type(observation["pid"]) is int
    assert observation["exit_code"] == 17
    complete = complete_auxiliary_observation(observation)
    assert complete is True, _supervision_diagnostic(observation)
    for incomplete in (
        observation | {"accepted": False},
        observation | {"cleanup": {"verified": False}},
        observation | {"cleanup": observation["cleanup"] | {"final_census_succeeded": False}},
        observation | {"cleanup": observation["cleanup"] | {"final_census_matched_pids": [observation["pid"]]}},
        observation | {"pid": None},
        observation | {"pid": True},
        observation | {"exit_code": None},
        observation | {"timed_out": True},
        observation | {"schema_version": "template-auxiliary-process-v2"},
    ):
        assert complete_auxiliary_observation(incomplete) is False
    assert observation["timed_out"] is observation["output_limit_exceeded"] is False
    assert observation["accepted"] is observation["cleanup"]["verified"] is True
    assert observation["cleanup"]["root_reaped"] is True
    assert observation["cleanup"]["guardian_finished"] is True
    assert observation["cleanup"]["final_token_sweep_matched_pids"] == []
    assert observation["cleanup"]["final_census_succeeded"] is True
    assert observation["cleanup"]["final_census_matched_pids"] == []
    assert observation["bootstrap_payload"] == bootstrap
    digest = hashlib.sha256(Path(sys.executable).resolve().read_bytes()).hexdigest()
    assert observation["executable_sha256_before"] == observation["executable_sha256_after"] == digest
    assert _stream(tmp_path, observation, "stdout") == b"actual\x00stdout"
    assert _stream(tmp_path, observation, "stderr") == b"actual\x00stderr"
    captured = capsys.readouterr()
    if forward:
        assert "actual\x00stdout" in captured.out
        assert "actual\x00stderr" in captured.err


@pytest.mark.parametrize("root_waits", [False, True], ids=["root-exit", "original-deadline"])
@pytest.mark.timeout(40)
def test_detached_descendants_cannot_survive_or_kill_a_foreign_sibling(tmp_path: Path, root_waits: bool) -> None:
    marker = tmp_path / "detached-writer"
    detached = f"import time; from pathlib import Path; time.sleep(30); Path({str(marker)!r}).touch()"
    command = (
        "import json,os,subprocess,sys,time; "
        f"p=subprocess.Popen([sys.executable,'-I','-c',{detached!r}],start_new_session=True); "
        "print(json.dumps({'pid':p.pid,'pgid':os.getpgid(p.pid)}),flush=True); "
        + ("time.sleep(30)" if root_waits else "raise SystemExit(0)")
    )
    foreign = subprocess.Popen([sys.executable, "-I", "-c", "import time; time.sleep(30)"], start_new_session=True)
    descendant_pid = None
    try:
        deadline = time.monotonic() + (10 if root_waits else 20)
        observation = supervise(
            [sys.executable, "-I", "-c", command],
            tmp_path,
            tmp_path / f"output/readiness/detached-{root_waits}",
            deadline,
        )
        child = json.loads(_stream(tmp_path, observation, "stdout"))
        descendant_pid = child["pid"]
        assert child["pgid"] == descendant_pid != observation["pid"]
        assert not _running(descendant_pid)
        assert not marker.exists()
        assert foreign.poll() is None
        assert observation["original_deadline_monotonic"] == deadline
        assert observation["timed_out"] is root_waits
        if root_waits:
            assert type(observation["exit_code"]) is int and observation["exit_code"] < 0
            assert observation["accepted"] is observation["cleanup"]["verified"] is False
            assert observation["cleanup"]["deadline_exceeded"] is True
        else:
            assert observation["exit_code"] == 0
            assert observation["accepted"] is observation["cleanup"]["verified"] is True
    finally:
        if descendant_pid is not None:
            _remove_owned_control(descendant_pid, detached)
        foreign.kill()
        foreign.wait(timeout=5)


def test_concurrent_supervisors_have_distinct_tokens_without_environment_mutation(tmp_path: Path) -> None:
    environment = {"PATH": os.defpath, "CONTROL_VALUE": "unchanged"}
    original = dict(environment)
    inherited = os.environ.get("TEMPLATE_BOUNDED_RUN_IDS")

    def execute(index: int) -> dict[str, Any]:
        return supervise(
            [
                sys.executable,
                "-I",
                "-c",
                "import os,time; print(os.environ['TEMPLATE_BOUNDED_RUN_IDS'],flush=True); time.sleep(0.2)",
            ],
            tmp_path,
            tmp_path / f"output/readiness/concurrent-{index}",
            time.monotonic() + 20,
            environment=environment,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        observations = list(executor.map(execute, range(2)))
    tokens = [_stream(tmp_path, observation, "stdout").strip() for observation in observations]
    assert len(set(tokens)) == 2
    assert all(len(token) == 32 for token in tokens)
    assert all(observation["accepted"] is True and observation["exit_code"] == 0 for observation in observations)
    assert environment == original
    assert os.environ.get("TEMPLATE_BOUNDED_RUN_IDS") == inherited


def test_oversized_actual_stream_is_bounded_and_cannot_pass(tmp_path: Path) -> None:
    observation = supervise(
        [
            sys.executable,
            "-I",
            "-c",
            f"import sys,time; sys.stdout.buffer.write(b'x'*{MAX_STREAM_BYTES + 1}); "
            "sys.stdout.buffer.flush(); time.sleep(30)",
        ],
        tmp_path,
        tmp_path / "output/readiness/stream-limit",
        time.monotonic() + 20,
    )
    assert observation["output_limit_exceeded"] is True
    assert observation["accepted"] is False
    assert observation["timed_out"] is False
    assert type(observation["exit_code"]) is int and observation["exit_code"] < 0
    assert len(_stream(tmp_path, observation, "stdout")) == MAX_STREAM_BYTES


def test_strict_census_observes_token_holders_without_killing_them() -> None:
    environment, token = build_bounded_run_env({"PATH": os.defpath})
    holder = subprocess.Popen(
        [sys.executable, "-I", "-c", "import time; time.sleep(30)"],
        env=environment,
        start_new_session=True,
    )
    try:
        assert observe_bounded_run_processes(token, deadline=time.monotonic() + 5) == {holder.pid}
        assert holder.poll() is None
        for invalid in ("", "not-a-token", "a" * 33, "A" * 32):
            with pytest.raises(ValueError, match="exact generated run token"):
                observe_bounded_run_processes(invalid, deadline=time.monotonic() + 5)
    finally:
        holder.kill()
        holder.wait(timeout=5)
    assert observe_bounded_run_processes(token, deadline=time.monotonic() + 5) == set()

    if sys.platform == "linux":
        import errno
        import select
        import stat

        from infrastructure.project.public_acceptance_auxiliary_supervision import _census_error_diagnostic

        environment, token = build_bounded_run_env({"PATH": os.defpath})
        body = """
import ctypes,os,time
libc=ctypes.CDLL(None,use_errno=True)
libc.prctl.argtypes=[ctypes.c_int,*([ctypes.c_ulong]*4)]
libc.prctl.restype=ctypes.c_int
if libc.prctl(4,0,0,0,0)!=0:
    raise OSError(ctypes.get_errno(),'PR_SET_DUMPABLE failed')
print(os.getpid(),flush=True)
time.sleep(30)
"""
        deadline = time.monotonic() + 5
        restricted = subprocess.Popen(
            [sys.executable, "-I", "-c", body],
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        try:
            assert restricted.stdout is not None
            ready = bytearray()
            while b"\n" not in ready:
                remaining = deadline - time.monotonic()
                assert remaining > 0, "owned non-dumpable child did not become ready inside its original deadline"
                assert select.select([restricted.stdout], [], [], remaining)[0]
                chunk = os.read(restricted.stdout.fileno(), 64)
                assert chunk, "owned non-dumpable child exited before readiness"
                ready.extend(chunk)
                assert len(ready) <= 64
            assert ready == f"{restricted.pid}\n".encode()
            assert restricted.poll() is None
            identity = psutil.Process(restricted.pid)
            birth = identity.create_time()
            assert identity.ppid() == os.getpid()
            proc = Path(f"/proc/{restricted.pid}")
            environ = proc / "environ"
            try:
                environ.read_bytes()
            except PermissionError as denied:
                assert denied.errno == errno.EACCES
                assert denied.filename == str(environ)
                with pytest.raises(RuntimeError) as refused:
                    observe_bounded_run_processes(token, deadline=deadline)
                cause = refused.value.__cause__
                if not isinstance(cause, PermissionError) or cause.filename != str(environ):
                    pytest.fail("strict census refusal preempted the owned Linux permission control")
                assert cause.errno == errno.EACCES
                diagnostic = _census_error_diagnostic(refused.value, deadline)
                assert set(diagnostic) == {"type", "cause", "errno", "procfs"}
                assert diagnostic["type"] == "RuntimeError"
                assert diagnostic["cause"] == "PermissionError"
                assert type(diagnostic["errno"]) is int and diagnostic["errno"] == errno.EACCES
                status_bytes = (proc / "status").read_bytes()
                assert len(status_bytes) <= 16 * 1024
                status = dict(line.split(":", 1) for line in status_bytes.decode().splitlines() if ":" in line)
                uid, gid = (
                    [int(value) for value in status["Uid"].split()],
                    [int(value) for value in status["Gid"].split()],
                )
                assert len(uid) == len(gid) == 4
                ownership = environ.stat()
                expected = {
                    "pid": restricted.pid,
                    "caller_uid": os.getuid(),
                    "caller_euid": os.geteuid(),
                    "caller_gid": os.getgid(),
                    "caller_egid": os.getegid(),
                    "ppid": int(status["PPid"]),
                    "tracer_pid": int(status["TracerPid"]),
                    "cap_prm": int(status["CapPrm"], 16),
                    "cap_eff": int(status["CapEff"], 16),
                    "environ_uid": ownership.st_uid,
                    "environ_gid": ownership.st_gid,
                    "environ_mode": stat.S_IMODE(ownership.st_mode),
                    **{
                        f"uid_{name}": value
                        for name, value in zip(("real", "effective", "saved", "fs"), uid, strict=True)
                    },
                    **{
                        f"gid_{name}": value
                        for name, value in zip(("real", "effective", "saved", "fs"), gid, strict=True)
                    },
                }
                observed = diagnostic["procfs"]
                assert set(observed) == {*expected, "comm", "probe_status"}
                assert all(type(observed[key]) is int and observed[key] == value for key, value in expected.items())
                assert observed["probe_status"] == "collected"
                comm = (proc / "comm").read_bytes()
                assert len(comm) <= 64
                python_names = {"python", "python3", "python3.12", "python3.13", "python3.14"}
                assert observed["comm"] == ("python" if comm.decode().strip() in python_names else "other")
                assert len(json.dumps(diagnostic)) <= 2048
                assert restricted.poll() is None and identity.create_time() == birth
            else:
                # A privileged caller may read this real process; that is not a refusal.
                assert observe_bounded_run_processes(token, deadline=deadline) == {restricted.pid}
                assert restricted.poll() is None and identity.create_time() == birth
        finally:
            # This retained, unreaped direct child cannot be a reused foreign PID.
            if restricted.poll() is None:
                restricted.kill()
            restricted.wait(timeout=5)
            if restricted.stdout is not None:
                restricted.stdout.close()


@pytest.mark.timeout(40)
def test_real_fd_exhaustion_cannot_turn_failed_census_into_cleanup_acceptance(tmp_path: Path) -> None:
    source_root = Path(__file__).resolve().parents[3]
    driver = r"""
import errno,json,os,resource,subprocess,sys,time
import psutil
sys.path.insert(0,sys.argv[1])
from infrastructure.core._bounded_kill import observe_bounded_run_processes
from infrastructure.core._bounded_run_guardian import start_bounded_run_guardian
from infrastructure.core.execution_boundary import build_bounded_env,build_bounded_run_env
from infrastructure.project.public_acceptance_auxiliary_supervision import _cleanup
deadline=time.monotonic()+20
environment=build_bounded_env(dict(os.environ))
child_environment,token=build_bounded_run_env(environment)
guardian=start_bounded_run_guardian(environment,deadline_monotonic=deadline)
assert guardian is not None
root=holder=None
try:
    root=subprocess.Popen([sys.executable,'-I','-c','raise SystemExit(17)'],env=child_environment,
                          stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                          start_new_session=True)
    guardian.arm(root_pid=root.pid,run_token=token,deadline_monotonic=deadline)
    assert root.wait(timeout=5)==17
    assert guardian.process.wait(timeout=5)==0
    # The real guardian has completed; this later actual token holder makes
    # affirmative final absence depend on the caller's independent census.
    holder=subprocess.Popen([sys.executable,'-I','-c','import time; time.sleep(30)'],
                            env=child_environment,start_new_session=True)
    birth=psutil.Process(holder.pid).create_time()
    limits=resource.getrlimit(resource.RLIMIT_NOFILE)
    strict_errno=None
    try:
        resource.setrlimit(resource.RLIMIT_NOFILE,(3,limits[1]))
        try:
            observe_bounded_run_processes(token,deadline=deadline)
        except OSError as error:
            strict_errno=error.errno
        cleanup=_cleanup(root,guardian,token,deadline)
    finally:
        resource.setrlimit(resource.RLIMIT_NOFILE,limits)
    assert strict_errno==errno.EMFILE
    assert root.returncode==17 and cleanup['root_reaped']
    assert cleanup['guardian_armed'] and cleanup['guardian_finished'] and cleanup['guardian_exit_code']==0
    assert cleanup['final_token_sweep_matched_pids']==[]
    assert cleanup['final_census_succeeded'] is False and cleanup['final_census_matched_pids'] is None
    assert cleanup['verified'] is False and not cleanup['deadline_exceeded']
    assert len(cleanup['diagnostics'])==1 and cleanup['diagnostics'][0].startswith('final census OSError:')
    assert holder.poll() is None and psutil.Process(holder.pid).create_time()==birth
    assert observe_bounded_run_processes(token,deadline=deadline)=={holder.pid}
    holder.kill()
    assert holder.wait(timeout=5)<0
    assert observe_bounded_run_processes(token,deadline=deadline)==set()
    print(json.dumps({'strict_errno':strict_errno,'root_exit':root.returncode,
                      'holder_pid':holder.pid,'holder_exit':holder.returncode,'cleanup':cleanup}))
finally:
    for child in (root,holder):
        if child is not None and child.poll() is None:
            child.kill()
            child.wait(timeout=5)
    guardian.close()
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", driver, str(source_root)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
    facts = json.loads(result.stdout)
    assert facts["strict_errno"] == 24
    assert facts["root_exit"] == 17 and facts["holder_exit"] < 0
    assert facts["cleanup"]["verified"] is False
    assert not _running(facts["holder_pid"])


@pytest.mark.timeout(45)
def test_interrupted_supervisor_still_cleans_detached_owned_children(tmp_path: Path) -> None:
    directory = tmp_path / "output/readiness/interrupted"
    detached = f"import time; time.sleep(30); print({str(tmp_path)!r})"
    command = (
        "import json,os,subprocess,sys,time; "
        f"p=subprocess.Popen([sys.executable,'-I','-c',{detached!r}],start_new_session=True); "
        "print(json.dumps([os.getpid(),p.pid]),flush=True); time.sleep(30)"
    )
    source_root = Path(__file__).resolve().parents[3]
    driver = (
        "import sys,time; from pathlib import Path; "
        f"sys.path.insert(0,{str(source_root)!r}); "
        "from infrastructure.project.public_acceptance_auxiliary_supervision import supervise; "
        f"supervise({[sys.executable, '-I', '-c', command]!r},Path({str(tmp_path)!r}),"
        f"Path({str(directory)!r}),time.monotonic()+30)"
    )
    wrapper = subprocess.Popen([sys.executable, "-I", "-c", driver], start_new_session=True)
    owned_pids: list[int] = []
    try:
        until = time.monotonic() + 20
        while time.monotonic() < until:
            stdout = directory / "stdout.txt"
            if stdout.is_file() and stdout.stat().st_size:
                owned_pids = json.loads(stdout.read_bytes())
                break
            assert wrapper.poll() is None, "the actual supervisor exited before its child control started"
            time.sleep(0.02)
        assert len(owned_pids) == 2
        wrapper.send_signal(signal.SIGINT)
        assert wrapper.wait(timeout=15) in (-signal.SIGINT, 130)
        assert all(not _running(pid) for pid in owned_pids)
    finally:
        if wrapper.poll() is None:
            wrapper.kill()
            wrapper.wait(timeout=5)
        for pid, code in zip(owned_pids, (command, detached), strict=False):
            _remove_owned_control(pid, code)


@pytest.mark.skipif(sys.platform != "linux", reason="procfs is required for the non-dumpable control")
def test_preexisting_non_dumpable_process_is_outside_guardian_start_scope() -> None:
    import select

    environment, token = build_bounded_run_env({"PATH": os.defpath})
    body = """
import ctypes,os,time
libc=ctypes.CDLL(None,use_errno=True)
libc.prctl.argtypes=[ctypes.c_int,*([ctypes.c_ulong]*4)]
libc.prctl.restype=ctypes.c_int
if libc.prctl(4,0,0,0,0)!=0:
    raise OSError(ctypes.get_errno(),'PR_SET_DUMPABLE failed')
print(os.getpid(),flush=True)
time.sleep(30)
"""
    restricted = subprocess.Popen(
        [sys.executable, "-I", "-c", body],
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    try:
        assert restricted.stdout is not None
        ready = bytearray()
        deadline = time.monotonic() + 10
        while b"\n" not in ready:
            remaining = deadline - time.monotonic()
            assert remaining > 0, "non-dumpable child did not become ready"
            assert select.select([restricted.stdout], [], [], remaining)[0]
            chunk = os.read(restricted.stdout.fileno(), 64)
            assert chunk, "non-dumpable child exited before readiness"
            ready.extend(chunk)
            assert len(ready) <= 64
        assert ready == f"{restricted.pid}\n".encode()
        assert restricted.poll() is None
        birth = time.monotonic()
        # A pre-existing non-dumpable daemon cannot hold this run's token and is
        # outside the guardian start scope, so it cannot fail final census.
        assert (
            observe_bounded_run_processes(
                token,
                deadline=time.monotonic() + 10,
                started_monotonic=birth + 5,
            )
            == set()
        )
        # The same unreadable newer child remains a strict refusal when it is
        # inside the guardian start scope.
        with pytest.raises(RuntimeError) as refused:
            observe_bounded_run_processes(token, deadline=time.monotonic() + 10, started_monotonic=birth - 1)
        assert isinstance(refused.value.__cause__, PermissionError)
        assert refused.value.__cause__.errno == 13
    finally:
        if restricted.stdout is not None:
            restricted.stdout.close()
        restricted.kill()
        restricted.wait(timeout=5)
