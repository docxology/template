"""Real browser controls; no synthetic DOM or replacement process providers."""

from __future__ import annotations

import shutil
import time
from pathlib import Path

import pytest

from infrastructure.core.execution_boundary import build_bounded_env
from infrastructure.reporting.native_format_browser_oracles import (
    BROWSER_CONTROL_CODES,
    audit_browser_html,
    browser_control_bytes,
    browser_control_contract,
    require_browser_control_result,
)


def _chrome() -> str:
    installed = shutil.which("chromium") or shutil.which("google-chrome")
    mac = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    if installed:
        return installed
    if mac.is_file():
        return str(mac)
    pytest.skip("actual native Chromium browser not installed")


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
