"""Root marker declarations discriminate optional suites without plugin assistance."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path


def test_root_marker_defaults_select_baseline_and_reject_unknown_marks(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[3]
    options = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["pytest"]["ini_options"]
    configuration = tmp_path / "pyproject.toml"
    configuration.write_text(
        "[tool.pytest.ini_options]\n"
        f"addopts = {json.dumps(options['addopts'])}\n"
        f"strict_markers = {json.dumps(options['strict_markers'])}\n"
        f"markers = {json.dumps(options['markers'])}\n",
        encoding="utf-8",
    )
    cases = tmp_path / "test_selection.py"
    cases.write_text(
        "import pytest\n\ndef test_baseline():\n    assert True\n"
        + "".join(
            f"\n@pytest.mark.{marker}\ndef test_{marker}():\n    pytest.fail('optional suite was selected')\n"
            for marker in ("requires_docker", "benchmark", "performance", "long_running")
        ),
        encoding="utf-8",
    )
    environment = os.environ.copy()
    environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    for name in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS"):
        environment.pop(name, None)
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-c",
        str(configuration),
        "--confcutdir",
        str(tmp_path),
        "-p",
        "no:cacheprovider",
        "-q",
        str(cases),
    ]
    selected = subprocess.run(
        command,
        cwd=tmp_path,
        env=environment,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert selected.returncode == 0, selected.stdout + selected.stderr
    assert "1 passed, 4 deselected" in selected.stdout

    with cases.open("a", encoding="utf-8") as stream:
        stream.write("\n@pytest.mark.unregistered_control\ndef test_unknown():\n    assert True\n")
    rejected = subprocess.run(
        command,
        cwd=tmp_path,
        env=environment,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert rejected.returncode == 2, rejected.stdout + rejected.stderr
    assert "unregistered_control" in rejected.stdout + rejected.stderr
