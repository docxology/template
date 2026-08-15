"""Negative-control tests for the bounded subprocess execution boundary.

Implements the acceptance evidence for SECURE-RUN-1 and
PROJECT-EXECUTION-BOUNDARY-1:

* Traversal / symlink policy — a hook that escapes the project root is
  rejected; an intentional lifecycle link that stays inside is allowed.
* Secret stripping — a hostile hook cannot read credential-like env vars.
* Root confinement — a hook path outside the hook root is rejected.
* Process-group cleanup — a timed-out hook's whole process group is
  killed, so it cannot outlive a failed run.
* Egress policy — an egress callback can refuse execution before launch.

No-Mocks policy: every test uses real files, real symlinks, and real
subprocesses.
"""

from __future__ import annotations

import contextlib
import os
import platform
import signal
import stat
import subprocess
import sys
import time
from pathlib import Path

import pytest

from infrastructure.core.execution_boundary import (
    build_bounded_env,
    classify_lifecycle_link,
    run_bounded_subprocess,
    validate_hook_root,
)

POSIX = platform.system() != "Windows"


def _write_executable(path: Path, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


# --------------------------------------------------------------------------- #
# classify_lifecycle_link                                                     #
# --------------------------------------------------------------------------- #


class TestClassifyLifecycleLink:
    def test_lifecycle_link_inside_root_is_allowed(self, tmp_path: Path) -> None:
        root = tmp_path / "projects" / "demo"
        target_dir = root / "src"
        target_dir.mkdir(parents=True)
        link = root / "scripts" / "linked"
        (root / "scripts").mkdir(parents=True)
        (target_dir / "module.py").write_text("x = 1\n", encoding="utf-8")
        link.symlink_to(target_dir / "module.py")

        result = classify_lifecycle_link(link, allowed_roots=[root])
        assert result.allowed
        assert result.kind == "lifecycle"

    def test_escape_link_outside_root_is_rejected(self, tmp_path: Path) -> None:
        root = tmp_path / "projects" / "demo"
        outside = tmp_path / "outside"
        outside.mkdir(parents=True)
        (outside / "secret.py").write_text("secret\n", encoding="utf-8")
        (root / "scripts").mkdir(parents=True)
        link = root / "scripts" / "evil"
        link.symlink_to(outside / "secret.py")

        result = classify_lifecycle_link(link, allowed_roots=[root])
        assert not result.allowed
        assert result.kind == "escape"


# --------------------------------------------------------------------------- #
# validate_hook_root                                                          #
# --------------------------------------------------------------------------- #


class TestValidateHookRoot:
    def test_hook_inside_root_is_returned(self, tmp_path: Path) -> None:
        root = tmp_path / "project"
        scripts = root / "scripts"
        scripts.mkdir(parents=True)

        resolved = validate_hook_root(scripts / "setup_hook.py", hook_root=scripts)
        assert resolved == (scripts / "setup_hook.py").resolve()

    def test_traversal_outside_root_is_rejected(self, tmp_path: Path) -> None:
        root = tmp_path / "project"
        (root / "scripts").mkdir(parents=True)
        outside = tmp_path / "elsewhere.py"
        outside.write_text("x\n", encoding="utf-8")

        with pytest.raises(ValueError, match="hook must resolve inside"):
            validate_hook_root(
                (root / "scripts" / ".." / ".." / "elsewhere.py"),
                hook_root=root / "scripts",
            )

    def test_absolute_escape_is_rejected(self, tmp_path: Path) -> None:
        root = tmp_path / "project"
        (root / "scripts").mkdir(parents=True)
        with pytest.raises(ValueError, match="hook must resolve inside"):
            validate_hook_root(tmp_path / "bin" / "evil.sh", hook_root=root / "scripts")


# --------------------------------------------------------------------------- #
# build_bounded_env                                                           #
# --------------------------------------------------------------------------- #


class TestBuildBoundedEnv:
    def test_strips_credential_vars(self) -> None:
        env = {
            "OPENAI_API_KEY": "sk-secret",
            "PATH": "/usr/bin",
            "SECRET_TOKEN": "abc",
            "HOME": "/home/user",
        }
        bounded = build_bounded_env(env)
        assert "OPENAI_API_KEY" not in bounded
        assert "SECRET_TOKEN" not in bounded
        assert bounded["PATH"] == "/usr/bin"
        assert bounded["HOME"] == "/home/user"

    def test_explicit_allowlist_keeps_named_secret(self) -> None:
        env = {"HF_TOKEN": "hf_x", "OPENAI_API_KEY": "sk"}
        bounded = build_bounded_env(env, allow_secret_names=["HF_TOKEN"])
        assert bounded["HF_TOKEN"] == "hf_x"
        assert "OPENAI_API_KEY" not in bounded

    def test_passthrough_keeps_var(self) -> None:
        env = {"MY_API_KEY": "keep", "PATH": "/usr/bin"}
        bounded = build_bounded_env(env, passthrough=["MY_API_KEY"])
        assert bounded["MY_API_KEY"] == "keep"
        assert "PATH" in bounded


# --------------------------------------------------------------------------- #
# run_bounded_subprocess                                                      #
# --------------------------------------------------------------------------- #


class TestRunBoundedSubprocess:
    def test_runs_command_and_captures_output(self, tmp_path: Path) -> None:
        result = run_bounded_subprocess(
            [sys.executable, "-c", "print('hello')"],
            cwd=tmp_path,
            env=build_bounded_env(),
            timeout=30,
        )
        assert result.returncode == 0
        assert not result.timed_out
        assert "hello" in result.stdout

    @pytest.mark.skipif(not POSIX, reason="killpg is POSIX-only")
    def test_timeout_kills_process_group(self, tmp_path: Path) -> None:
        # Spawn a child that sleeps forever AND spawns a grandchild that also
        # sleeps; both are in the same process group and must be killed on
        # timeout so neither outlives the run.
        script = tmp_path / "bomb.py"
        _write_executable(
            script,
            "import subprocess, time\nsubprocess.Popen(['sleep', '300'])\ntime.sleep(300)\n",
        )
        result = run_bounded_subprocess(
            [sys.executable, str(script)],
            cwd=tmp_path,
            env=build_bounded_env(),
            timeout=1,
        )
        assert result.timed_out
        assert result.returncode == -signal.SIGKILL

        # No `sleep 300` descendant may survive the timed-out run.
        import subprocess as sp

        leftover = sp.run(["pgrep", "-f", "sleep 300"], capture_output=True, text=True)
        assert "sleep 300" not in leftover.stdout

    @pytest.mark.skipif(not POSIX, reason="process-group timeout semantics are POSIX-only")
    def test_timeout_without_capture_still_kills_process_group(self, tmp_path: Path) -> None:
        """The analysis-script mode cannot leave descendants when output is uncaptured."""
        marker = tmp_path / "leaked.txt"
        pid_file = tmp_path / "root.pid"
        child_body = f"import pathlib,time; time.sleep(2); pathlib.Path({str(marker)!r}).write_text('leaked')"
        script = tmp_path / "uncaptured_timeout.py"
        _write_executable(
            script,
            "import os,pathlib,subprocess,sys,time\n"
            f"pathlib.Path({str(pid_file)!r}).write_text(str(os.getpid()), encoding='utf-8')\n"
            f"subprocess.Popen([sys.executable, '-c', {child_body!r}])\n"
            "time.sleep(30)\n",
        )

        result = run_bounded_subprocess(
            [sys.executable, str(script)],
            cwd=tmp_path,
            env=build_bounded_env(),
            timeout=1,
            capture_output=False,
        )

        assert result.timed_out
        assert result.returncode == -signal.SIGKILL
        import time as _time

        _time.sleep(2.2)
        assert not marker.exists()
        root_pid = int(pid_file.read_text(encoding="utf-8"))
        with pytest.raises(ChildProcessError):
            os.waitpid(root_pid, os.WNOHANG)

    @pytest.mark.skipif(not POSIX, reason="detached POSIX session regression")
    @pytest.mark.parametrize("capture_output", [True, False])
    def test_early_root_exit_cannot_leak_reparented_tagged_child(
        self,
        tmp_path: Path,
        capture_output: bool,
    ) -> None:
        """Run identity cleanup covers the PPID/process-group blind spot."""
        import time as _time

        marker = tmp_path / "reparented-child-finished"
        child_code = (
            "import pathlib,time; "
            "time.sleep(1.5); "
            f"pathlib.Path({str(marker)!r}).write_text('leaked', encoding='utf-8')"
        )
        parent_code = (
            "import subprocess,sys; subprocess.Popen([sys.executable, '-c', sys.argv[1]], start_new_session=True)"
        )

        started = _time.monotonic()
        run_bounded_subprocess(
            [sys.executable, "-c", parent_code, child_code],
            cwd=tmp_path,
            env=build_bounded_env(),
            timeout=0.3,
            capture_output=capture_output,
        )
        assert _time.monotonic() - started < 1.5
        _time.sleep(1.6)
        assert not marker.exists()

    @pytest.mark.skipif(not POSIX, reason="SIGINT process cleanup is POSIX-only")
    def test_keyboard_interrupt_kills_and_reaps_detached_process_tree(self, tmp_path: Path) -> None:
        """An operator interrupt cannot orphan the bounded root or a detached writer."""
        marker = tmp_path / "interrupt-leaked-child"
        root_pid_path = tmp_path / "interrupt-root.pid"
        child_pid_path = tmp_path / "interrupt-child.pid"
        interrupted_path = tmp_path / "interrupt-observed"
        child_code = (
            "import pathlib,time; "
            "time.sleep(2.0); "
            f"pathlib.Path({str(marker)!r}).write_text('leaked', encoding='utf-8')"
        )
        root_code = (
            "import os,pathlib,subprocess,sys,time; "
            f"pathlib.Path({str(root_pid_path)!r}).write_text(str(os.getpid()), encoding='utf-8'); "
            "child=subprocess.Popen([sys.executable, '-c', sys.argv[1]], "
            "start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); "
            f"pathlib.Path({str(child_pid_path)!r}).write_text(str(child.pid), encoding='utf-8'); "
            "time.sleep(30)"
        )
        helper_code = (
            "import pathlib,sys; "
            "from infrastructure.core.execution_boundary import build_bounded_env,run_bounded_subprocess; "
            "target_cwd=pathlib.Path(sys.argv[1]); "
            "\ntry:\n"
            " run_bounded_subprocess([sys.executable, '-c', sys.argv[2], sys.argv[3]], "
            "cwd=target_cwd, env=build_bounded_env(), timeout=30, capture_output=False)\n"
            "except KeyboardInterrupt:\n"
            f" pathlib.Path({str(interrupted_path)!r}).write_text('yes', encoding='utf-8')\n"
            " raise SystemExit(77)\n"
            "raise SystemExit(78)\n"
        )
        repo_root = Path(__file__).resolve().parents[3]
        helper = subprocess.Popen(
            [sys.executable, "-c", helper_code, str(tmp_path), root_code, child_code],
            cwd=repo_root,
            env=os.environ.copy(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        root_pid: int | None = None
        child_pid: int | None = None
        cleanup_needed = True
        try:
            deadline = time.monotonic() + 10
            while not (root_pid_path.is_file() and child_pid_path.is_file()):
                if helper.poll() is not None:
                    pytest.fail(f"interrupt helper exited before its process tree was ready: {helper.returncode}")
                if time.monotonic() >= deadline:
                    pytest.fail("interrupt helper did not publish child PIDs")
                time.sleep(0.02)
            root_pid = int(root_pid_path.read_text(encoding="utf-8"))
            child_pid = int(child_pid_path.read_text(encoding="utf-8"))

            os.kill(helper.pid, signal.SIGINT)
            assert helper.wait(timeout=10) == 77
            assert interrupted_path.read_text(encoding="utf-8") == "yes"

            for pid in (root_pid, child_pid):
                state = subprocess.run(
                    ["ps", "-o", "stat=", "-p", str(pid)],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=5,
                ).stdout.strip()
                assert not state or state.startswith("Z"), f"PID {pid} survived interrupt cleanup in state {state}"
            cleanup_needed = False
            time.sleep(2.2)
            assert not marker.exists()
        finally:
            if helper.poll() is None:
                helper.kill()
                helper.wait(timeout=5)
            if cleanup_needed and root_pid is not None:
                with contextlib.suppress(ProcessLookupError):
                    os.kill(root_pid, signal.SIGKILL)
            if cleanup_needed and child_pid is not None:
                with contextlib.suppress(ProcessLookupError):
                    os.kill(child_pid, signal.SIGKILL)

    def test_egress_check_can_refuse_launch(self, tmp_path: Path) -> None:
        def _refuse(argv, cwd, env):
            raise RuntimeError("egress blocked")

        result = run_bounded_subprocess(
            [sys.executable, "-c", "print('never')"],
            cwd=tmp_path,
            env=build_bounded_env(),
            timeout=30,
            egress_check=_refuse,
        )
        assert result.command_error.startswith("refused by egress policy")
        assert result.returncode == 1
        assert "never" not in result.stdout

    def test_missing_executable_reports_failure(self, tmp_path: Path) -> None:
        result = run_bounded_subprocess(
            ["/definitely/not/a/real/binary_xyz"],
            cwd=tmp_path,
            env=build_bounded_env(),
            timeout=30,
        )
        assert result.returncode == 1
        assert "failed to launch" in result.command_error


# --------------------------------------------------------------------------- #
# End-to-end: a hostile hook cannot read credentials or escape                #
# --------------------------------------------------------------------------- #


class TestHostileHookBoundary:
    def test_hostile_hook_has_no_credential_env(self, tmp_path: Path) -> None:
        """A hook run through the boundary cannot see credential env vars."""
        env = build_bounded_env({"OPENAI_API_KEY": "sk-secret", "PATH": os.environ.get("PATH", "")})
        script = tmp_path / "sniff.py"
        _write_executable(
            script,
            "import os\nprint('HAS_TOKEN' if 'OPENAI_API_KEY' in os.environ else 'CLEAN')\n",
        )
        result = run_bounded_subprocess(
            [sys.executable, str(script)],
            cwd=tmp_path,
            env=env,
            timeout=30,
        )
        assert result.returncode == 0
        assert "CLEAN" in result.stdout
        assert "HAS_TOKEN" not in result.stdout

    def test_hostile_hook_cannot_escape_hook_root(self, tmp_path: Path) -> None:
        """Traversal from a project hook toward the repo root is rejected."""
        root = tmp_path / "project"
        scripts = root / "scripts"
        scripts.mkdir(parents=True)
        trap = tmp_path / "trap.sh"
        trap.write_text("echo compromised > /tmp/should_not_happen\n", encoding="utf-8")

        with pytest.raises(ValueError, match="hook must resolve inside"):
            validate_hook_root(
                (scripts / ".." / ".." / "trap.sh"),
                hook_root=scripts,
            )
