"""Owned real-process fixtures prove startup before accepting cleanup evidence."""

from __future__ import annotations

import contextlib
import json
import math
import os
import signal
import subprocess
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType
from typing import Any


@dataclass(frozen=True)
class OwnedProcessFixture:
    """One detached child with its own identity and a delayed write obligation."""

    command: tuple[str, ...]
    child_receipt: Path
    parent_receipt: Path
    marker: Path
    token: str
    write_delay_seconds: float
    detached: bool

    def __enter__(self) -> OwnedProcessFixture:
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, traceback: TracebackType | None
    ) -> bool:
        try:
            self.cleanup_owned_child()
        except BaseException:
            if exc is None:
                raise
            # Preserve the original test/operator exception while still trying
            # ownership-checked cleanup. No cleanup success is inferred here.
        return False

    def observed(self) -> dict[str, Any]:
        """Require child self-observation and the parent's successful live native probe."""
        child = json.loads(self.child_receipt.read_text(encoding="utf-8"))
        parent = json.loads(self.parent_receipt.read_text(encoding="utf-8"))
        assert set(child) == {"pid", "ppid", "session_id", "token", "started", "write_deadline"}
        assert all(type(child[key]) is int and child[key] > 0 for key in ("pid", "ppid", "session_id"))
        assert child["token"] == self.token
        assert all(type(child[key]) is float and math.isfinite(child[key]) for key in ("started", "write_deadline"))
        assert child["write_deadline"] - child["started"] == self.write_delay_seconds
        assert parent["child"] == child and parent["root_pid"] == child["ppid"] != child["pid"]
        assert type(parent["root_session_id"]) is int and parent["root_session_id"] > 0
        expected_session = child["pid"] if self.detached else parent["root_session_id"]
        assert child["session_id"] == expected_session
        if self.detached:
            assert child["session_id"] != parent["root_session_id"]
        assert type(parent["native_returncode"]) is int and parent["native_returncode"] == 0
        assert parent["native_stderr"] == ""
        fields = parent["native_stdout"].split()
        assert len(fields) == 3
        assert [int(fields[0]), int(fields[1])] == [child["pid"], child["ppid"]]
        assert fields[2] and not fields[2].startswith("Z"), fields
        return child

    def assert_cleaned(self) -> None:
        """An observed live child must be genuinely absent or a native zombie."""
        child = self.observed()
        result = subprocess.run(
            ["ps", "-o", "pid=,stat=", "-p", str(child["pid"])],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        fields = result.stdout.split()
        absent = result.returncode == 1 and not fields and not result.stderr
        zombie = (
            result.returncode == 0
            and len(fields) == 2
            and not result.stderr
            and int(fields[0]) == child["pid"]
            and fields[1].startswith("Z")
        )
        assert absent or zombie, (result.returncode, result.stdout, result.stderr)
        # The real child's scheduled write was observed before the root wait/exit.
        # Native absence/zombie proves that it cannot perform that future write;
        # no sleep measured from producer startup can substitute for this proof.
        assert not self.marker.exists(), "the owned delayed write escaped the real boundary"

    def cleanup_owned_child(self) -> None:
        """Only terminate an owned still-live PID whose native argv retains its token."""
        if not self.child_receipt.is_file():
            return
        child = json.loads(self.child_receipt.read_text(encoding="utf-8"))
        assert child["token"] == self.token and type(child["pid"]) is int and child["pid"] > 0
        probe = subprocess.run(
            ["ps", "-ww", "-o", "args=", "-p", str(child["pid"])],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if probe.returncode == 1 and not probe.stdout.strip() and not probe.stderr:
            return
        assert probe.returncode == 0 and not probe.stderr, (probe.returncode, probe.stderr)
        # A zombie cannot execute further writes, and a reused PID without this
        # exact owned token is not ours to terminate.
        if self.token in probe.stdout:
            with contextlib.suppress(ProcessLookupError):
                os.kill(child["pid"], signal.SIGKILL)


def assert_process_exited(pid: int) -> None:
    """Native proof that ``pid`` is absent or a terminated zombie.

    Hosts whose PID 1 does not reap orphans (common in containers) keep a
    killed detached descendant as a zombie; it can execute nothing further.
    """
    result = subprocess.run(
        ["ps", "-o", "pid=,stat=", "-p", str(pid)],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    fields = result.stdout.split()
    absent = result.returncode == 1 and not fields and not result.stderr
    zombie = (
        result.returncode == 0
        and len(fields) == 2
        and not result.stderr
        and int(fields[0]) == pid
        and fields[1].startswith("Z")
    )
    assert absent or zombie, (pid, result.returncode, result.stdout, result.stderr)


def owned_process_fixture(
    root: Path, *, early_root_exit: bool = False, detached: bool = True, write_delay_seconds: float = 30.0
) -> OwnedProcessFixture:
    """Build stdlib-only real child/parent code; never replace a production dependency."""
    token = uuid.uuid4().hex
    child_receipt, parent_receipt = root / "actual-child.json", root / "actual-parent.json"
    marker = root / "owned-child-delayed-write"
    child_program = (
        "import json,os,sys,time\nfrom pathlib import Path\n"
        "started=time.monotonic()\n"
        f"record={{'pid':os.getpid(),'ppid':os.getppid(),'session_id':os.getsid(0),'token':sys.argv[1],"
        f"'started':started,'write_deadline':started+{write_delay_seconds!r}}}\n"
        f"Path({str(child_receipt)!r}).write_text(json.dumps(record),encoding='utf-8')\n"
        "print(json.dumps(record),flush=True)\n"
        "time.sleep(max(0.0,record['write_deadline']-time.monotonic()))\n"
        f"Path({str(marker)!r}).write_text('owned delayed write escaped',encoding='utf-8')\n"
    )
    parent_program = (
        "import json,os,subprocess,sys,time\nfrom pathlib import Path\n"
        "child=subprocess.Popen([sys.executable,'-I','-c',sys.argv[1],sys.argv[2]],"
        f"start_new_session={detached!r},stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)\n"
        "assert child.stdout is not None\n"
        "try:\n"
        " record=json.loads(child.stdout.readline())\n"
        " assert record['pid']==child.pid and record['ppid']==os.getpid()\n"
        " native=subprocess.run(['ps','-o','pid=,ppid=,stat=','-p',str(child.pid)],\n"
        "  capture_output=True,text=True,timeout=5,check=False)\n"
        " fields=native.stdout.split()\n"
        " assert native.returncode==0 and not native.stderr and len(fields)==3\n"
        " assert [int(fields[0]),int(fields[1])]==[child.pid,os.getpid()] and not fields[2].startswith('Z')\n"
        f" Path({str(parent_receipt)!r}).write_text(json.dumps({{'root_pid':os.getpid(),"
        "'root_session_id':os.getsid(0),'child':record,"
        "'native_returncode':native.returncode,'native_stdout':native.stdout,'native_stderr':native.stderr}),encoding='utf-8')\n"
        "finally:\n child.stdout.close()\n" + ("raise SystemExit(0)\n" if early_root_exit else "time.sleep(300)\n")
    )
    return OwnedProcessFixture(
        (sys.executable, "-I", "-c", parent_program, child_program, token),
        child_receipt,
        parent_receipt,
        marker,
        token,
        write_delay_seconds,
        detached,
    )
