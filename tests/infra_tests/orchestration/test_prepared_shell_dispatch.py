"""Real shell/selected-Python dispatch without automatic provisioning."""

from __future__ import annotations

import importlib.util
import json
import marshal
import os
import signal
import shlex
import shutil
import stat
import struct
import subprocess
import sys
import sysconfig
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
pytestmark = pytest.mark.timeout(90)


def _copy_dispatch(root: Path, *, public_package: bool = False) -> None:
    root.mkdir()
    for name in ("run.sh", "secure_run.sh", "pyproject.toml"):
        shutil.copy2(ROOT / name, root / name)
    (root / "scripts/shell").mkdir(parents=True)
    shutil.copy2(ROOT / "scripts/shell/shell_bootstrap.sh", root / "scripts/shell/shell_bootstrap.sh")
    if public_package:
        shutil.copytree(
            ROOT / "infrastructure", root / "infrastructure", ignore=shutil.ignore_patterns("__pycache__", "*.pyc")
        )
        shutil.copytree(
            ROOT / "scripts",
            root / "scripts",
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )


def _environment(root: Path) -> dict[str, str]:
    env = dict(os.environ)
    for key in ("TEMPLATE_ROOT_PYTHON", "PYTHONPATH", "PYTHONPYCACHEPREFIX"):
        env.pop(key, None)
    env.update(
        TEMPLATE_SKIP_LINK_SYNC="1",
        TEMPLATE_SKIP_FOND_LINK_SYNC="1",
        TEMPLATE_SKIP_RULE_LINK_SYNC="1",
        TEMPLATE_SKIP_TOOL_LINK_SYNC="1",
    )
    env["TMPDIR"] = str(root.parent)
    return env


@pytest.mark.parametrize("wrapper", ["run.sh", "secure_run.sh"])
@pytest.mark.parametrize("nomination", [None, "relative/python", "/template-missing-nominated-python", "/usr/bin/true"])
def test_missing_or_invalid_runtime_blocks_without_acquisition(
    tmp_path: Path, wrapper: str, nomination: str | None
) -> None:
    root = tmp_path / "repo"
    _copy_dispatch(root)
    env = _environment(root)
    if nomination is not None:
        env["TEMPLATE_ROOT_PYTHON"] = nomination
    env["UV_CACHE_DIR"] = str(root / "must-not-create-uv-cache")
    env["MPLCONFIGDIR"] = str(root / "must-not-create-mpl-cache")
    before = {str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*") if path.is_file()}
    child = subprocess.run(
        ["/bin/bash", str(root / wrapper), "--help"],
        env=env,
        cwd=root,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert child.returncode == 75, (child.stdout, child.stderr)
    assert "uv sync --locked" in child.stderr
    assert before == {str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*") if path.is_file()}
    assert not (root / ".venv").exists() and not (root / "uv.lock").exists()
    assert not (root / "must-not-create-uv-cache").exists() and not (root / "must-not-create-mpl-cache").exists()


@pytest.mark.parametrize("wrapper", ["run.sh", "secure_run.sh"])
def test_actual_prepared_help_ignores_valid_poisoned_cache(tmp_path: Path, wrapper: str) -> None:
    search_only = tmp_path / "search-only"
    search_only.mkdir()
    root = search_only / "repo"
    _copy_dispatch(root, public_package=True)
    source = root / "infrastructure/core/runtime/prepared_dispatch.py"
    marker = root / "poison-executed"
    metadata = source.stat()
    poison = compile(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('poison')\nraise SystemExit(77)\n",
        str(source),
        "exec",
    )
    cache = source.parent / "__pycache__" / f"{source.stem}.{sys.implementation.cache_tag}.pyc"
    cache.parent.mkdir()
    cache.write_bytes(
        importlib.util.MAGIC_NUMBER
        + struct.pack("<III", 0, int(metadata.st_mtime), metadata.st_size)
        + marshal.dumps(poison)
    )
    normal = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "import sys;sys.path.insert(0,sys.argv[1]);import infrastructure.core.runtime.prepared_dispatch",
            str(root),
        ],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert normal.returncode == 77 and marker.read_text() == "poison"
    marker.unlink()
    env = _environment(root)
    env["TMPDIR"] = str(tmp_path)
    env["TEMPLATE_ROOT_PYTHON"] = sys.executable
    env["TEMPLATE_DISPATCH_TIMEOUT_SECONDS"] = "60"
    original_mode = search_only.stat().st_mode & 0o7777
    try:
        # Existing audited search-only traversal is supported through O_PATH.
        # Other platforms still exercise both original poisoned-cache help cases.
        if hasattr(os, "O_PATH"):
            search_only.chmod(0o111)
        result = subprocess.run(
            ["/bin/bash", str(root / wrapper), "--help"],
            env=env,
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=75,
            check=False,
        )
    finally:
        search_only.chmod(original_mode)
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert "usage:" in result.stdout and not marker.exists()
    assert not (root / ".venv").exists() and not (root / "uv.lock").exists()
    assert not tuple(tmp_path.glob("template-prepared-*"))


def test_prepared_selected_runtime_missing_requirement_is_blocked(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _copy_dispatch(root, public_package=True)
    (root / "pyproject.toml").write_text(
        '[project]\nname="fixture"\nversion="0.0.0"\ndependencies=["template-deliberately-missing-prepared-requirement"]\n'
    )
    env = _environment(root)
    env["TEMPLATE_ROOT_PYTHON"] = sys.executable
    child = subprocess.run(
        ["/bin/bash", str(root / "run.sh"), "--help"],
        env=env,
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )
    assert child.returncode == 75, (child.stdout, child.stderr)
    assert "template-deliberately-missing" in child.stderr
    assert not (root / ".venv").exists() and not (root / "uv.lock").exists()


def test_prepared_dispatch_preserves_actual_invocation_two(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _copy_dispatch(root, public_package=True)
    env = _environment(root)
    env["TEMPLATE_ROOT_PYTHON"] = sys.executable
    result = subprocess.run(
        ["/bin/bash", str(root / "run.sh"), "--unsupported-real-option"],
        env=env,
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=75,
        check=False,
    )
    assert result.returncode == 2, (result.stdout, result.stderr)
    assert "unrecognized arguments" in result.stderr
    assert not (root / "output").exists()


def _disposable_prepared_venv(tmp_path: Path) -> tuple[Path, Path]:
    """Create an offline venv with existing package bytes, without pip/resolution."""
    environment = tmp_path / "prepared"
    created = subprocess.run(
        [sys.executable, "-I", "-S", "-m", "venv", "--without-pip", str(environment)],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert created.returncode == 0, (created.stdout, created.stderr)
    site = Path(sysconfig.get_path("purelib", scheme="posix_prefix", vars={"base": str(environment)}))
    # Only package/metadata availability is claimed. These explicit local links
    # reuse this test process's prepared dependencies and perform no acquisition.
    for source in Path(sysconfig.get_path("purelib")).iterdir():
        if source.suffix != ".pth" and not (site / source.name).exists():
            (site / source.name).symlink_to(source, target_is_directory=source.is_dir())
    return environment / "bin/python", site


@pytest.mark.parametrize("wrapper", ["run.sh", "secure_run.sh"])
def test_site_startup_occurs_once_inside_guardian_and_detached_child_is_reaped(tmp_path: Path, wrapper: str) -> None:
    root = tmp_path / "repo"
    _copy_dispatch(root, public_package=True)
    (root / "pyproject.toml").write_text('[project]\nname="fixture"\nversion="0.0.0"\ndependencies=[]\n')
    interpreter, site = _disposable_prepared_venv(tmp_path)
    counter, pid_file, escaped = (tmp_path / name for name in ("site-startups", "detached-pid", "escaped"))
    descendant = (
        "import os,time;from pathlib import Path;"
        f"Path({str(pid_file)!r}).write_text(str(os.getpid())+'\\n'+repr(time.monotonic()+8));"
        f"time.sleep(8);Path({str(escaped)!r}).write_text('survived');time.sleep(15)"
    )
    (site / "template-delayed-startup.pth").write_text(
        "import pathlib,subprocess,sys,time;"
        f"pathlib.Path({str(counter)!r}).open('a').write('startup\\n');"
        f"subprocess.Popen([sys.executable,'-I','-S','-c',{descendant!r}],start_new_session=True);"
        "time.sleep(20)\n"
    )
    env = _environment(root)
    env["TEMPLATE_ROOT_PYTHON"] = str(interpreter)
    env["TEMPLATE_DISPATCH_TIMEOUT_SECONDS"] = "5"
    try:
        result = subprocess.run(
            ["/bin/bash", str(root / wrapper), "--help"],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=25,
            check=False,
        )
        assert result.returncode == 124, (result.stdout, result.stderr)
        assert counter.read_text() == "startup\n"
        assert pid_file.is_file(), "The real startup descendant must have executed before the deadline"
        # Cross the descendant's actual write deadline to prove detached cleanup,
        # rather than inferring cleanup solely from the direct child's exit.
        deadline = float(pid_file.read_text().splitlines()[1])
        observation_delay = max(0.0, deadline + 0.5 - time.monotonic())
        assert observation_delay <= 9, "The fixture observation must retain a finite bound"
        time.sleep(observation_delay)
        assert not escaped.exists()
        assert not tuple(tmp_path.glob("template-prepared-*"))
        assert not tuple(tmp_path.glob("template-guardian-bytecode-*"))
    finally:
        if pid_file.is_file():
            try:
                os.kill(int(pid_file.read_text().splitlines()[0]), signal.SIGKILL)
            except ProcessLookupError:
                pass


def test_normal_site_startup_is_retained_for_actual_cli_child(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _copy_dispatch(root, public_package=True)
    interpreter, site = _disposable_prepared_venv(tmp_path)
    counter = tmp_path / "site-startups"
    (site / "template-observed-startup.pth").write_text(
        "import json,os,pathlib,sys;"
        f"pathlib.Path({str(counter)!r}).open('a').write(json.dumps({{'pid':os.getpid(),'executable':sys.executable,"
        "'no_site':sys.flags.no_site,'frames':[(sys._getframe(i).f_code.co_name,"
        "sys._getframe(i).f_code.co_filename) for i in range(5)]})+'\\n')\n"
    )
    # Native site processing differs across CPython versions. In 3.14.4 the
    # venv and main paths both process .pth; compare the actual selected native
    # interpreter rather than imposing a platform-invented startup count.
    control = subprocess.run(
        [str(interpreter), "-I", "-c", "import os;print(os.getpid())"],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    assert control.returncode == 0, (control.stdout, control.stderr)
    native_receipts = [json.loads(line) for line in counter.read_text().splitlines()]
    assert native_receipts and all(receipt["pid"] == int(control.stdout) for receipt in native_receipts)
    counter.unlink()
    worker_marker = tmp_path / "actual-cli-worker"
    dispatch_source = root / "infrastructure/core/runtime/prepared_dispatch.py"
    source = dispatch_source.read_text()
    needle = "    from infrastructure.orchestration.cli import main"
    assert source.count(needle) == 1
    dispatch_source.write_text(
        source.replace(needle, f"    Path({str(worker_marker)!r}).write_text(str(os.getpid()))\n" + needle)
    )
    env = _environment(root)
    env["TEMPLATE_ROOT_PYTHON"] = str(interpreter)
    result = subprocess.run(
        ["/bin/bash", str(root / "run.sh"), "--help"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert counter.is_file(), result.stderr
    receipts = [json.loads(line) for line in counter.read_text().splitlines()]
    assert "usage:" in result.stdout and receipts
    assert all(receipt["pid"] == int(worker_marker.read_text()) for receipt in receipts)
    assert all(receipt["no_site"] == 0 and receipt["executable"] == str(interpreter) for receipt in receipts)
    assert [receipt["frames"] for receipt in receipts] == [receipt["frames"] for receipt in native_receipts]


@pytest.mark.parametrize("value", ["", "0", "-1", "nan", "inf", "1e999", "not-a-number"])
def test_parent_rejects_invalid_budget_before_native_launch(tmp_path: Path, value: str) -> None:
    root = tmp_path / "repo"
    _copy_dispatch(root)
    env = _environment(root)
    env["TEMPLATE_DISPATCH_TIMEOUT_SECONDS"] = value
    child = subprocess.run(
        ["/bin/bash", str(root / "run.sh"), "--help"],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    assert child.returncode == 2, (child.stdout, child.stderr)
    assert "positive and finite" in child.stderr
    assert not tuple(tmp_path.glob("template-root-python.*"))
    assert not (root / ".venv").exists()


@pytest.mark.parametrize("budget", ["0.05", "5e-2"])
def test_tiny_positive_budget_does_not_receive_fresh_time(tmp_path: Path, budget: str) -> None:
    root = tmp_path / "repo"
    _copy_dispatch(root, public_package=True)
    env = _environment(root)
    env["TEMPLATE_ROOT_PYTHON"] = sys.executable
    env["TEMPLATE_DISPATCH_TIMEOUT_SECONDS"] = budget
    child = subprocess.run(
        ["/bin/bash", str(root / "run.sh"), "--help"],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    assert child.returncode == 124, (child.stdout, child.stderr)
    assert "usage:" not in child.stdout
    assert not tuple(tmp_path.glob("template-root-python.*"))


@pytest.mark.parametrize("wrapper", ["run.sh", "secure_run.sh"])
def test_native_cfg_fifo_is_bounded_before_python_receipt(tmp_path: Path, wrapper: str) -> None:
    root = tmp_path / "repo"
    _copy_dispatch(root, public_package=True)
    interpreter, _site = _disposable_prepared_venv(tmp_path)
    configuration = interpreter.parent.parent / "pyvenv.cfg"
    configuration.unlink()
    os.mkfifo(configuration)
    env = _environment(root)
    env["TEMPLATE_ROOT_PYTHON"] = str(interpreter)
    env["TEMPLATE_DISPATCH_TIMEOUT_SECONDS"] = "2"
    started = time.monotonic()
    child = subprocess.run(
        ["/bin/bash", str(root / wrapper), "--help"],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=7,
        check=False,
    )
    assert child.returncode == 124, (child.stdout, child.stderr)
    assert time.monotonic() - started < 5
    assert "native prepared interpreter" in child.stderr
    assert not tuple(tmp_path.glob("template-root-python.*"))
    assert not tuple(tmp_path.glob("template-prepared-*"))
    assert not (root / "uv.lock").exists()


def test_same_native_process_refuses_cfg_fifo_after_ready(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _copy_dispatch(root, public_package=True)
    interpreter, _site = _disposable_prepared_venv(tmp_path)
    configuration = interpreter.parent.parent / "pyvenv.cfg"
    original = configuration.read_bytes()
    control = root / "scripts/shell/shell_bootstrap.sh"
    marker = tmp_path / "actual-ready-pid"
    # A real copied-shell phase barrier changes only the disposable selected
    # venv after its valid timer-armed receipt. No transport/runtime replacement.
    needle = "        printf '%s\\t%s\\t%s\\n'"
    injected = (
        f"        printf '%s\\n' \"$observed_pid\" > {shlex.quote(str(marker))}\n"
        f"        rm {shlex.quote(str(configuration))}\n"
        f"        mkfifo {shlex.quote(str(configuration))}\n"
    )
    source = control.read_text()
    assert source.count(needle) == 1
    control.write_text(source.replace(needle, injected + needle))
    env = _environment(root)
    env["TEMPLATE_ROOT_PYTHON"] = str(interpreter)
    env["TEMPLATE_DISPATCH_TIMEOUT_SECONDS"] = "30"
    try:
        child = subprocess.run(
            ["/bin/bash", str(root / "run.sh"), "--help"],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        assert marker.is_file() and int(marker.read_text()) > 0, "The actual READY barrier must have executed"
        assert stat.S_ISFIFO(configuration.lstat().st_mode)
        assert child.returncode == 75, (child.stdout, child.stderr)
        assert "regular no-follow pyvenv.cfg" in child.stderr
        assert "usage:" not in child.stdout
        assert not tuple(tmp_path.glob("template-root-python.*"))
    finally:
        configuration.unlink()
        configuration.write_bytes(original)


@pytest.mark.parametrize("outcome", ["parent_int", "child130", "startup_timeout"])
def test_single_admission_pid_seed_identity_and_controls(tmp_path: Path, outcome: str) -> None:
    root = tmp_path / "repo"
    _copy_dispatch(root, public_package=True)
    seed = root / "scripts/runner/prepared_dispatch.py"
    marker = tmp_path / "actual-seed-pid"
    needle = "            configure_prepared_site(_selected, observed_prefix=_observed_prefix)"
    # The copied, audited seed records the admission PID retained by the actual
    # in-process transition, then waits so parent-only SIGINT is deterministic.
    injected = (
        f"            Path({str(marker)!r}).write_text(str(os.getpid()) + '\\n' + str(globals().get('pid')) + '\\n' + sys.executable)\n"
        + ("            raise SystemExit(130)\n" if outcome == "child130" else "            time.sleep(30)\n")
    )
    source = seed.read_text()
    assert source.count(needle) == 1
    seed.write_text(source.replace(needle, injected + needle))
    env = _environment(root)
    env["TEMPLATE_ROOT_PYTHON"] = sys.executable
    env["TEMPLATE_DISPATCH_TIMEOUT_SECONDS"] = "5" if outcome == "startup_timeout" else "60"
    child = subprocess.Popen(
        ["/bin/bash", str(root / "run.sh"), "--help"],
        cwd=root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.monotonic() + 10
        while not marker.exists() and child.poll() is None and time.monotonic() < deadline:
            time.sleep(0.05)
        assert marker.is_file(), "The actual seed must execute before interruption"
        seed_pid, admission_pid, selected = marker.read_text().splitlines()
        assert seed_pid == admission_pid and selected == sys.executable
        if outcome == "parent_int":
            os.kill(child.pid, signal.SIGINT)
        stdout, stderr = child.communicate(timeout=10)
        assert child.returncode == (124 if outcome == "startup_timeout" else 130), (stdout, stderr)
        assert not tuple(tmp_path.glob("template-root-python.*"))
    finally:
        if child.poll() is None:
            child.kill()
            child.communicate(timeout=5)


def test_seed_keeps_original_startup_deadline_instead_of_resetting(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _copy_dispatch(root, public_package=True)
    bootstrap = root / "scripts/shell/shell_bootstrap.sh"
    source = bootstrap.read_text()
    assert source.count("startup_deadline = started + min(30, budget)") == 1
    # The actual copied admission producer declares a shorter startup cap,
    # while whole-dispatch remains 60s. Resetting the seed timer would succeed.
    bootstrap.write_text(
        source.replace("startup_deadline = started + min(30, budget)", "startup_deadline = started + 4")
    )
    seed = root / "scripts/runner/prepared_dispatch.py"
    source = seed.read_text()
    needle = "            configure_prepared_site(_selected, observed_prefix=_observed_prefix)"
    marker = tmp_path / "actual-startup-delay"
    injected = f"            Path({str(marker)!r}).write_text('executed')\n            time.sleep(6)\n"
    assert source.count(needle) == 1
    seed.write_text(source.replace(needle, injected + needle))
    env = _environment(root)
    env["TEMPLATE_ROOT_PYTHON"] = sys.executable
    env["TEMPLATE_DISPATCH_TIMEOUT_SECONDS"] = "60"
    started = time.monotonic()
    result = subprocess.run(
        ["/bin/bash", str(root / "run.sh"), "--help"],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert marker.read_text() == "executed", "The actual seed delay must run to test timer composition"
    assert result.returncode == 124, (result.stdout, result.stderr)
    assert time.monotonic() - started < 8
    assert "usage:" not in result.stdout
    assert not tuple(tmp_path.glob("template-prepared-*"))
