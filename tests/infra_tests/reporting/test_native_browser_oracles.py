"""Real browser controls; no synthetic DOM or replacement process providers."""

from __future__ import annotations

import time
import signal
import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.core.execution_boundary import build_bounded_env
from infrastructure.reporting.native_format_acceptance_checks import (
    NativeToolUnavailable,
)
from infrastructure.reporting.native_format_observer_dispatch import (
    _chrome as native_chrome,
)
from infrastructure.reporting.native_format_browser_oracles import (
    BROWSER_CONTROL_CODES,
    audit_browser_html,
    browser_control_bytes,
    browser_control_contract,
    require_browser_control_result,
)
from tests.infra_tests.reporting._audited_browser_child import audited_browser_control


def _chrome() -> str:
    try:
        return native_chrome(build_bounded_env())
    except NativeToolUnavailable as error:
        pytest.fail(str(error))


def test_configured_native_browser_preserves_actual_selection_and_refuses_missing_files(
    tmp_path: Path,
) -> None:
    actual = Path(_chrome())
    assert native_chrome({"CHROME_EXECUTABLE_PATH": str(actual), "PATH": str(tmp_path)}) == str(actual)
    # Exercise the actual ambient environment in a separate interpreter. Native
    # admission removes this legacy TeX font route, while the explicitly prepared
    # browser selection survives the same bounded environment construction.
    script = (
        "import os,pathlib,sys\n"
        "sys.path.insert(0,sys.argv[1])\n"
        "from infrastructure.core.execution_boundary import build_bounded_env\n"
        "from infrastructure.reporting.native_format_acceptance_contracts import native_environment\n"
        "from infrastructure.reporting.native_format_observer_dispatch import _chrome\n"
        "assert build_bounded_env()['TTFONTS']==sys.argv[4]\n"
        "env=native_environment(pathlib.Path(sys.argv[1]),pathlib.Path(sys.executable),pathlib.Path(sys.argv[2]))\n"
        "assert 'TTFONTS' not in env\n"
        "assert env['CHROME_EXECUTABLE_PATH']==sys.argv[3] and _chrome(env)==sys.argv[3]\n"
    )
    root = Path(__file__).resolve().parents[3]
    result = subprocess.run(
        [sys.executable, "-I", "-c", script, str(root), str(tmp_path), str(actual), str(tmp_path / "ambient-fonts")],
        cwd=tmp_path,
        env={**build_bounded_env(), "TTFONTS": str(tmp_path / "ambient-fonts"), "CHROME_EXECUTABLE_PATH": str(actual)},
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    ordinary = tmp_path / "ordinary-file"
    ordinary.write_text("not an executable browser")
    for invalid in (tmp_path / "missing", tmp_path, ordinary, Path("relative-browser")):
        with pytest.raises(NativeToolUnavailable, match="actual executable file"):
            native_chrome({"CHROME_EXECUTABLE_PATH": str(invalid), "PATH": str(tmp_path)})


def test_unaudited_parent_cannot_hold_html_child_custody(tmp_path: Path) -> None:
    """A pytest worker never installed the preimport audit, so it cannot launch."""
    directory = tmp_path / "output" / "readiness" / "evidence"
    directory.mkdir(mode=0o700, parents=True)
    with pytest.raises(ValueError, match="actually preimport-audited SDK package"):
        audit_browser_html(
            tmp_path,
            directory,
            browser_control_bytes("baseline"),
            browser_control_contract(),
            chrome=_chrome(),
            env=build_bounded_env(),
            deadline=time.monotonic() + 30,
            run_id="c" * 32,
        )
    assert not list(directory.glob("browser-result-*"))


@pytest.mark.timeout(240)
@pytest.mark.parametrize("name", tuple(BROWSER_CONTROL_CODES))
def test_valid_native_browser_control(tmp_path: Path, name: str) -> None:
    # The HTML parent custodian requires an interpreter that installed the
    # executed-bytecode audit before importing the SDK, as trusted launchers do.
    directory = tmp_path / "output" / "readiness" / "evidence"
    directory.mkdir(mode=0o700, parents=True)
    observed = audited_browser_control(
        tmp_path,
        directory,
        name,
        workspace=tmp_path / "audited-child",
        deadline=time.monotonic() + 120,
        run_id="c" * 32,
    )
    assert require_browser_control_result(name, observed) == (0 if name == "baseline" else 1)
    assert all(item["screenshot"]["height_px"] >= item["dom"]["height"] for item in observed["viewports"])


@pytest.mark.timeout(30)
@pytest.mark.parametrize("publish_complete", [True, False])
def test_actual_endpoint_partial_write_waits_for_complete_publication(tmp_path: Path, publish_complete: bool) -> None:
    """A genuine child publishes an empty then partial endpoint; no process provider replacement."""
    from infrastructure.reporting.native_format_browser_driver import _browser_endpoint

    endpoint = tmp_path / "DevToolsActivePort"
    ready = tmp_path / "created-empty-endpoint"
    release = tmp_path / "publish-complete-endpoint"
    program = (
        "from pathlib import Path; import sys,time\n"
        "endpoint,ready,release=map(Path,sys.argv[1:])\n"
        "endpoint.write_text(''); ready.write_text('ready')\n"
        "deadline=time.monotonic()+10\n"
        "while not release.exists() and time.monotonic()<deadline: time.sleep(.01)\n"
        "endpoint.write_text('12345\\n'); time.sleep(.1)\n"
        "endpoint.write_text('12345\\n/devtools/browser/owned-control')\n"
        "time.sleep(10)\n"
    )
    child = subprocess.Popen([sys.executable, "-I", "-c", program, str(endpoint), str(ready), str(release)])
    try:
        startup = time.monotonic() + 10
        while not ready.exists():
            assert child.poll() is None and time.monotonic() < startup
            time.sleep(0.01)
        assert endpoint.read_bytes() == b""
        if publish_complete:
            release.write_text("publish")
            assert _browser_endpoint(endpoint, child, time.monotonic() + 5) == (
                12345,
                "/devtools/browser/owned-control",
            )
        else:
            started = time.monotonic()
            with pytest.raises(TimeoutError, match="original deadline") as expired:
                _browser_endpoint(endpoint, child, started + 0.2)
            assert "signed exit" not in str(expired.value)
            assert time.monotonic() - started < 2
            assert endpoint.read_bytes() == b"" and child.poll() is None
    finally:
        child.terminate()
        child.wait(timeout=5)


@pytest.mark.timeout(30)
@pytest.mark.parametrize("outcome", ["nonzero", "signal", "zero"])
def test_actual_endpoint_early_signed_exit_retains_bounded_owned_stderr(tmp_path: Path, outcome: str) -> None:
    """Actual OS exits and actual private-file IO; no browser/process replacement."""
    from infrastructure.reporting.native_format_browser_driver import _browser_endpoint

    endpoint = tmp_path / "DevToolsActivePort"
    program = (
        "import os,signal,sys\n"
        "sys.stderr.write('excluded-startup-prefix'+('x'*5000)+'original-startup-diagnostic');sys.stderr.flush()\n"
        "if sys.argv[1]=='signal': os.kill(os.getpid(),signal.SIGTERM)\n"
        "os._exit(17 if sys.argv[1]=='nonzero' else 0)\n"
    )
    expected = -signal.SIGTERM if outcome == "signal" else (17 if outcome == "nonzero" else 0)
    with (tmp_path / "actual-startup.stderr").open("xb+") as stderr:
        child = subprocess.Popen([sys.executable, "-I", "-c", program, outcome], stderr=stderr)
        try:
            with pytest.raises(RuntimeError, match=f"original signed exit={expected}") as failed:
                _browser_endpoint(endpoint, child, time.monotonic() + 10, stderr_fd=stderr.fileno())
            assert child.wait(timeout=5) == expected
            diagnostic = str(failed.value)
            assert "original-startup-diagnostic" in diagnostic
            assert "excluded-startup-prefix" not in diagnostic
            assert len(diagnostic) < 2200
            assert not endpoint.exists()
        finally:
            if child.poll() is None:
                child.terminate()
            child.wait(timeout=5)
