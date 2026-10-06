"""Real portable bundled execution, deadlines, and descendant cleanup."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from template_pools_rules_tools.tools.tools_invoker import get_tools_root


def _command() -> list[str]:
    return [
        sys.executable,
        "-I",
        str(get_tools_root() / "template_code_executor/src/code_executor.py"),
    ]


def _run(payload: dict[str, object]) -> tuple[int, dict[str, object]]:
    result = subprocess.run(
        _command(),
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    return result.returncode, json.loads(result.stdout)


def test_actual_python_and_nonzero_child_results() -> None:
    outer, result = _run({"code": "print(2+2)", "timeout_s": 5})
    assert outer == 0
    assert result == {
        "exit_code": 0,
        "child_exit_code": 0,
        "timed_out": False,
        "output_truncated": False,
        "stdout": "4\n",
        "stderr": "",
    }
    outer, result = _run({"code": "raise SystemExit(3)", "timeout_s": 5})
    assert outer == 0 and result["exit_code"] == result["child_exit_code"] == 3


def test_sleep_deadline_is_finite_and_preserves_real_child_code() -> None:
    started = time.monotonic()
    outer, result = _run({"code": "import time; time.sleep(60)", "timeout_s": 0.5})
    assert time.monotonic() - started < 10
    assert outer == 0 and result["exit_code"] == 124 and result["timed_out"] is True
    assert type(result["child_exit_code"]) is int and result["child_exit_code"] != 0


@pytest.mark.parametrize("timeout", [True, 0, -1, float("nan"), float("inf"), 301])
def test_invalid_budget_cannot_execute(tmp_path: Path, timeout: object) -> None:
    target = tmp_path / "must-not-exist"
    outer, result = _run({"code": f"open({str(target)!r},'w').write('bad')", "timeout_s": timeout})
    assert outer == result["exit_code"] == 2 and not target.exists()


@pytest.mark.parametrize("wait", [False, True])
def test_detached_descendant_cannot_outlive_exit_or_timeout(tmp_path: Path, wait: bool) -> None:
    target = tmp_path / "escaped"
    nested = f"import time; time.sleep(2); open({str(target)!r},'w').write('bad')"
    code = (
        "import subprocess,sys,time; "
        f"subprocess.Popen([sys.executable,'-I','-c',{nested!r}],start_new_session=True); "
        + ("time.sleep(60)" if wait else "print('done')")
    )
    outer, result = _run({"code": code, "timeout_s": 0.5 if wait else 5})
    assert outer == 0 and result["exit_code"] == (124 if wait else 0)
    time.sleep(2.1)
    assert not target.exists()


def test_independent_guardian_cleans_after_parent_termination(tmp_path: Path) -> None:
    started, target = tmp_path / "started", tmp_path / "escaped"
    nested = f"import time; time.sleep(2); open({str(target)!r},'w').write('bad')"
    code = (
        "import subprocess,sys,time; "
        f"subprocess.Popen([sys.executable,'-I','-c',{nested!r}],start_new_session=True); "
        f"open({str(started)!r},'w').write('ready'); time.sleep(60)"
    )
    parent = subprocess.Popen(
        _command(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    try:
        assert parent.stdin is not None
        parent.stdin.write(json.dumps({"code": code, "timeout_s": 10}).encode())
        parent.stdin.close()
        deadline = time.monotonic() + 5
        while not started.exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        assert started.exists()
        parent.kill()
        parent.wait(timeout=5)
        time.sleep(2.1)
        assert not target.exists()
    finally:
        if parent.poll() is None:
            parent.kill()
            parent.wait(timeout=5)
        for stream in (parent.stdout, parent.stderr):
            if stream is not None:
                stream.close()


def test_credentials_are_not_inherited_by_executed_code() -> None:
    environment = {**os.environ, "TEMPLATE_TEST_API_KEY": "private-sentinel"}
    child = subprocess.run(
        _command(),
        input=json.dumps(
            {"code": "import os;print(os.getenv('TEMPLATE_TEST_API_KEY'))", "timeout_s": 5}
        ),
        env=environment,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert child.returncode == 0
    assert json.loads(child.stdout)["stdout"] == "None\n"
    assert "private-sentinel" not in child.stdout + child.stderr


def test_output_is_bounded_and_overflow_fails() -> None:
    outer, result = _run({"code": "import sys;sys.stdout.write('x'*(4*1024*1024))", "timeout_s": 5})
    assert outer == 0 and result["exit_code"] != 0 and result["output_truncated"] is True
    assert len(str(result["stdout"])) == 1024 * 1024


def test_stdin_without_eof_has_a_finite_deadline() -> None:
    parent = subprocess.Popen(
        _command(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    try:
        parent.wait(timeout=10)
        assert parent.returncode == 2
        assert parent.stdout is not None and "stdin deadline" in parent.stdout.read().decode()
    finally:
        if parent.poll() is None:
            parent.kill()
            parent.wait(timeout=5)
        for stream in (parent.stdin, parent.stdout, parent.stderr):
            if stream is not None:
                stream.close()
