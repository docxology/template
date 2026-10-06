"""Actual guardian imports, poisoned caches, and cleanup custody controls."""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


def _run_copy(tmp_path: Path, body: str, *args: str, observer_timeout: float = 35) -> dict:
    """Exercise current public bytes in a copied package layout, outside the checkout."""
    root = tmp_path / "package-layout/lib/python/site-packages"
    root.mkdir(parents=True)
    shutil.copytree(
        ROOT / "infrastructure",
        root / "infrastructure",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".mypy_cache", ".ruff_cache"),
    )
    prefix = tmp_path / "parent-bytecode"
    prefix.mkdir(mode=0o700)
    command = [
        sys.executable,
        "-I",
        "-X",
        f"pycache_prefix={prefix.resolve()}",
        "-c",
        "import sys; sys.path.insert(0,sys.argv.pop(1));\n" + body,
        str(root),
        *args,
    ]
    result = subprocess.run(
        command, cwd=tmp_path, capture_output=True, text=True, timeout=observer_timeout, check=False
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
    return json.loads(result.stdout)


@pytest.mark.skipif(os.name == "nt", reason="independent guardian is POSIX-only")
@pytest.mark.parametrize(
    "target", ["core/_bounded_run_guardian.py", "core/_bounded_kill.py", "core/implementation_custody.py"]
)
def test_normal_valid_poison_cache_is_ignored_by_actual_guardian(tmp_path: Path, target: str) -> None:
    result = _run_copy(
        tmp_path,
        r"""
import importlib.util, json, marshal, os, struct, subprocess, uuid
from pathlib import Path
from infrastructure.core._bounded_run_guardian import start_bounded_run_guardian
source = Path(sys.path[0]) / 'infrastructure' / sys.argv[1]
marker = Path.cwd() / 'poison-executed'
metadata = source.stat()
code = compile(f"from pathlib import Path\nPath({str(marker)!r}).write_text('poison')\nraise SystemExit(77)\n",
               str(source), 'exec')
cache = source.parent / '__pycache__' / (source.stem + '.' + sys.implementation.cache_tag + '.pyc')
cache.parent.mkdir(exist_ok=True)
cache.write_bytes(importlib.util.MAGIC_NUMBER + struct.pack('<III', 0, int(metadata.st_mtime), metadata.st_size)
                  + marshal.dumps(code))
module = 'infrastructure.' + sys.argv[1][:-3].replace('/', '.')
normal = subprocess.run([sys.executable, '-I', '-c',
                        "import importlib,sys; sys.path.insert(0,sys.argv[1]); importlib.import_module(sys.argv[2])",
                        sys.path[0], module], cwd=Path.cwd(), capture_output=True, timeout=10)
assert normal.returncode == 77 and marker.read_text() == 'poison'
marker.unlink()
env = dict(os.environ, PYTHONPYCACHEPREFIX=str(cache.parent), PYTHONPATH='/untrusted/fixture/path')
guardian = start_bounded_run_guardian(env)
assert guardian is not None and guardian.cache is not None
fresh = Path(guardian.cache.name).resolve()
assert fresh.is_dir() and fresh != cache.parent and fresh.stat().st_mode & 0o777 == 0o700
child = subprocess.Popen([sys.executable, '-I', '-c', 'import time; time.sleep(.1)'], env=env)
try:
    guardian.arm(root_pid=child.pid, run_token=uuid.uuid4().hex)
    child.wait(timeout=5)
    guardian.wait_for_cleanup()
finally:
    if child.poll() is None:
        child.kill()
        child.wait(timeout=5)
    guardian.close()
assert not fresh.exists() and guardian.cache is None and not marker.exists()
assert cache.is_file()
print(json.dumps({'normal_exit':normal.returncode, 'guardian_exit':guardian.process.returncode,
                  'fresh_removed':not fresh.exists(), 'poison_executed':marker.exists()}))
""",
        target,
    )
    assert result == {"normal_exit": 77, "guardian_exit": 0, "fresh_removed": True, "poison_executed": False}


@pytest.mark.skipif(os.name == "nt", reason="independent guardian is POSIX-only")
def test_ready_unarmed_guardian_close_reaps_and_removes_cache(tmp_path: Path) -> None:
    result = _run_copy(
        tmp_path,
        r"""
import json, os
from pathlib import Path
from infrastructure.core._bounded_run_guardian import start_bounded_run_guardian
guardian = start_bounded_run_guardian(dict(os.environ))
assert guardian is not None and guardian.cache is not None
cache = Path(guardian.cache.name).resolve()
guardian.close()
guardian.close()
assert guardian.process.poll() is not None and not cache.exists() and guardian.cache is None
assert guardian.control_fd == guardian.status_fd == -1
print(json.dumps({'reaped':True, 'cache_removed':True}))
""",
    )
    assert result == {"reaped": True, "cache_removed": True}


@pytest.mark.skipif(os.name == "nt", reason="independent guardian is POSIX-only")
def test_source_change_still_cleans_detached_child_and_refuses_success(tmp_path: Path) -> None:
    result = _run_copy(
        tmp_path,
        r"""
import json, os, subprocess, time, uuid
from pathlib import Path
from infrastructure.core._bounded_run_guardian import GuardianCustodyError, start_bounded_run_guardian
guardian = start_bounded_run_guardian(dict(os.environ))
assert guardian is not None and guardian.cache is not None
cache = Path(guardian.cache.name).resolve()
token = uuid.uuid4().hex
marker = Path.cwd() / 'detached-leak'
child_code = f"import time; from pathlib import Path; time.sleep(1.5); Path({str(marker)!r}).write_text('leaked')"
root_code = "import subprocess,sys,time; subprocess.Popen([sys.executable,'-I','-c',sys.argv[1]],start_new_session=True); time.sleep(.2)"
child = subprocess.Popen([sys.executable,'-I','-c',root_code,child_code],
                         env=dict(os.environ,TEMPLATE_BOUNDED_RUN_IDS=token))
refused = False
try:
    guardian.arm(root_pid=child.pid, run_token=token)
    source = Path(sys.path[0]) / 'infrastructure/core/_bounded_kill.py'
    source.write_bytes(source.read_bytes()+b'\n# actual concurrent source change\n')
    child.wait(timeout=5)
    try:
        guardian.wait_for_cleanup()
    except GuardianCustodyError:
        refused = True
finally:
    if child.poll() is None:
        child.kill()
        child.wait(timeout=5)
    guardian.close()
time.sleep(1.6)
assert refused and not marker.exists() and not cache.exists()
print(json.dumps({'refused':refused,'detached_survived':marker.exists(),'cache_removed':not cache.exists()}))
""",
    )
    assert result == {"refused": True, "detached_survived": False, "cache_removed": True}


@pytest.mark.skipif(os.name == "nt", reason="independent guardian is POSIX-only")
def test_failed_ready_handshake_removes_private_cache(tmp_path: Path) -> None:
    result = _run_copy(
        tmp_path,
        r"""
import json, os, subprocess, tempfile
from pathlib import Path
from infrastructure.core._bounded_run_guardian import BoundedRunGuardian, GuardianCustodyError, _BOOTSTRAP, _READY, _expect_status
from infrastructure.core.implementation_custody import bytecode_audit_bootstrap
cache = tempfile.TemporaryDirectory(prefix='template-guardian-bytecode-')
prefix = Path(cache.name).resolve()
control_read, control_write = os.pipe()
status_read, status_write = os.pipe()
audit = bytecode_audit_bootstrap((Path(sys.path[0])/'infrastructure',),prefix)
process = subprocess.Popen([sys.executable,'-I','-S','-c',_BOOTSTRAP,str(prefix),json.dumps(sys.path),sys.path[0],audit,
                            str(control_read),str(status_write),'0'*64],
                           pass_fds=(control_read,status_write),stdin=subprocess.DEVNULL,
                           stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
os.close(control_read)
os.close(status_write)
guardian = BoundedRunGuardian(process,control_write,status_read,cache=cache)
refused = False
try:
    try:
        _expect_status(status_read,_READY,timeout=10)
    except GuardianCustodyError:
        refused = True
finally:
    guardian.close()
assert refused and process.poll() is not None and not prefix.exists() and guardian.cache is None
print(json.dumps({'refused':refused,'cache_removed':not prefix.exists(),'reaped':True}))
""",
    )
    assert result == {"refused": True, "cache_removed": True, "reaped": True}


@pytest.mark.skipif(os.name == "nt", reason="independent guardian is POSIX-only")
def test_changed_loaded_source_is_typed_refusal_before_private_startup(tmp_path: Path) -> None:
    result = _run_copy(
        tmp_path,
        r"""
import json, os
from pathlib import Path
from infrastructure.core._bounded_run_guardian import GuardianCustodyError, start_bounded_run_guardian
scratch = Path.cwd() / 'owned-startup-scratch'
scratch.mkdir(mode=0o700)
os.environ['TMPDIR'] = str(scratch)
source = Path(sys.path[0]) / 'infrastructure/core/_bounded_kill.py'
source.write_bytes(source.read_bytes()+b'\n# actual source change before guardian startup\n')
refused = False
try:
    start_bounded_run_guardian(dict(os.environ))
except GuardianCustodyError:
    refused = True
assert refused and not tuple(scratch.iterdir())
print(json.dumps({'typed_refusal':refused,'scratch_untouched':True}))
""",
    )
    assert result == {"typed_refusal": True, "scratch_untouched": True}


@pytest.mark.skipif(os.name == "nt", reason="independent guardian is POSIX-only")
def test_abrupt_caller_exit_still_cleans_descendant_and_own_cache(tmp_path: Path) -> None:
    result = _run_copy(
        tmp_path,
        r"""
import json, os, subprocess, uuid
from pathlib import Path
from infrastructure.core._bounded_run_guardian import start_bounded_run_guardian
guardian = start_bounded_run_guardian(dict(os.environ))
assert guardian is not None and guardian.cache is not None
token = uuid.uuid4().hex
marker = Path.cwd() / 'dead-caller-detached-leak'
child_code = f"import time; from pathlib import Path; time.sleep(1.5); Path({str(marker)!r}).write_text('leaked')"
root_code = "import subprocess,sys,time; subprocess.Popen([sys.executable,'-I','-c',sys.argv[1]],start_new_session=True); time.sleep(.25)"
child = subprocess.Popen([sys.executable,'-I','-c',root_code,child_code],
                         env=dict(os.environ,TEMPLATE_BOUNDED_RUN_IDS=token),
                         stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
guardian.arm(root_pid=child.pid,run_token=token)
print(json.dumps({'cache':str(Path(guardian.cache.name).resolve()),'root_pid':child.pid}),flush=True)
os._exit(0)
""",
    )
    import time

    cache = Path(result["cache"])
    try:
        deadline = time.monotonic() + 10
        while cache.exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        assert not cache.exists(), "orphan guardian did not remove its owned bytecode scratch"
        time.sleep(1.6)
        assert not (tmp_path / "dead-caller-detached-leak").exists()
    finally:
        try:
            os.kill(result["root_pid"], signal.SIGKILL)
        except ProcessLookupError:
            pass


def test_expired_deadline_refuses_startup_without_creating_guardian_scratch(tmp_path: Path) -> None:
    result = _run_copy(
        tmp_path,
        r"""
import json, os, time
from pathlib import Path
from infrastructure.core._bounded_run_guardian import start_bounded_run_guardian
scratch = Path.cwd() / 'deadline-scratch'
scratch.mkdir(mode=0o700)
os.environ['TMPDIR'] = str(scratch)
try:
    start_bounded_run_guardian(dict(os.environ), deadline_monotonic=time.monotonic() - 1)
except TimeoutError:
    pass
else:
    raise AssertionError('expired budget launched a guardian')
assert not tuple(scratch.iterdir())
print(json.dumps({'refused':True,'scratch_untouched':True}))
""",
    )
    assert result == {"refused": True, "scratch_untouched": True}


@pytest.mark.skipif(os.name == "nt", reason="independent guardian is POSIX-only")
def test_expired_arming_keeps_control_unbound_and_reaps_guardian(tmp_path: Path) -> None:
    result = _run_copy(
        tmp_path,
        r"""
import json, os, time, uuid
from pathlib import Path
from infrastructure.core._bounded_run_guardian import start_bounded_run_guardian
guardian = start_bounded_run_guardian(dict(os.environ), deadline_monotonic=time.monotonic()+15)
assert guardian is not None and guardian.cache is not None
cache = Path(guardian.cache.name).resolve()
try:
    try:
        guardian.arm(root_pid=os.getpid(),run_token=uuid.uuid4().hex,deadline_monotonic=time.monotonic()-1)
    except TimeoutError:
        pass
    else:
        raise AssertionError('expired arming budget bound a running root')
    assert not guardian.armed and guardian.control_fd >= 0
finally:
    guardian.close()
assert not cache.exists() and guardian.process.poll() is not None
print(json.dumps({'refused':True,'reaped':True,'cache_removed':True}))
""",
    )
    assert result == {"refused": True, "reaped": True, "cache_removed": True}


def test_handshake_uses_original_deadline_with_a_real_pipe(tmp_path: Path) -> None:
    result = _run_copy(
        tmp_path,
        r"""
import json, os, time
from infrastructure.core._bounded_run_guardian import _READY, _expect_status, _start_wait_timeout
reader, writer = os.pipe()
start = time.monotonic()
deadline = start + .04
try:
    try:
        _expect_status(reader,_READY,timeout=_start_wait_timeout(deadline),deadline_monotonic=deadline)
    except TimeoutError:
        pass
    else:
        raise AssertionError('unresponsive guardian exceeded its admitted budget')
finally:
    os.close(reader)
    os.close(writer)
elapsed = time.monotonic()-start
assert .03 <= elapsed < .8
print(json.dumps({'refused':True,'bounded':True}))
""",
    )
    assert result == {"refused": True, "bounded": True}
