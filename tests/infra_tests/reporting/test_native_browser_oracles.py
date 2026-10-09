"""Real browser controls; no synthetic DOM or replacement process providers."""

from __future__ import annotations

import time
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
    ordinary = tmp_path / "ordinary-file"
    ordinary.write_text("not an executable browser")
    for invalid in (tmp_path / "missing", tmp_path, ordinary, Path("relative-browser")):
        with pytest.raises(NativeToolUnavailable, match="actual executable file"):
            native_chrome({"CHROME_EXECUTABLE_PATH": str(invalid), "PATH": str(tmp_path)})


@pytest.mark.timeout(240)
@pytest.mark.parametrize("name", tuple(BROWSER_CONTROL_CODES))
def test_valid_native_browser_control(tmp_path: Path, name: str) -> None:
    directory = tmp_path / "output" / "readiness" / "evidence"
    directory.mkdir(mode=0o700, parents=True)
    observed = audit_browser_html(
        tmp_path,
        directory,
        browser_control_bytes(name),
        browser_control_contract(),
        chrome=_chrome(),
        env=build_bounded_env(),
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
            with pytest.raises(TimeoutError, match="original deadline"):
                _browser_endpoint(endpoint, child, started + 0.2)
            assert time.monotonic() - started < 2
            assert endpoint.read_bytes() == b"" and child.poll() is None
    finally:
        child.terminate()
        child.wait(timeout=5)
