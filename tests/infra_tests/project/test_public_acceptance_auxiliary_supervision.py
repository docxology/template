"""Real bounded children, detached descendants and auxiliary cleanup custody."""

from __future__ import annotations

import hashlib
import json
import os
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


def test_original_failure_streams_binary_and_bootstrap_are_preserved(tmp_path: Path) -> None:
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
    )
    assert type(observation["pid"]) is int
    assert observation["exit_code"] == 17
    assert complete_auxiliary_observation(observation) is True
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
