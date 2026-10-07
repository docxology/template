"""Real browser controls; no synthetic DOM or replacement process providers."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from infrastructure.core.execution_boundary import build_bounded_env
from infrastructure.reporting.native_format_acceptance_checks import NativeToolUnavailable
from infrastructure.reporting.native_format_observer_dispatch import _chrome as native_chrome
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


def test_configured_native_browser_preserves_actual_selection_and_refuses_missing_files(tmp_path: Path) -> None:
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
