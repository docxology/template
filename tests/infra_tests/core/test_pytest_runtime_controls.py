"""Genuine loaded/disabled benchmark plugin sessions preserve Source and choice."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest

import infrastructure.core.testing._pytest_runtime_controls as controls

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("mode", ["present", "blocked", "autoload-disabled", "explicit-custom"])
@pytest.mark.timeout(60)
def test_actual_plugin_storage_is_default_only_and_optional(tmp_path: Path, mode: str) -> None:
    nominated = tmp_path / "output/.pipeline/benchmarks"
    explicit = tmp_path / "custom-user-storage"
    enabled = mode in {"present", "explicit-custom"}
    expected = explicit if mode == "explicit-custom" else nominated
    if enabled:
        body = (
            "def test_real_benchmark(benchmark, pytestconfig):\n"
            "    assert benchmark(lambda: sum(range(4))) == 6\n"
            f"    assert pytestconfig.option.benchmark_storage == {'file://' + str(expected)!r}\n"
        )
    else:
        body = (
            "def test_plugin_absent(pytestconfig):\n    assert not hasattr(pytestconfig.option, 'benchmark_storage')\n"
        )
    (tmp_path / "test_actual.py").write_text(body)
    arguments = ["-p", controls.__name__, f"--template-benchmark-storage={nominated}", "-q", "test_actual.py"]
    if enabled:
        arguments.extend(
            [
                "-p",
                "pytest_benchmark.plugin",
                "--benchmark-min-rounds=1",
                "--benchmark-min-time=0.000001",
                "--benchmark-max-time=0.001",
                "--benchmark-warmup=off",
            ]
        )
    elif mode == "blocked":
        arguments.extend(["-p", "no:benchmark"])
    if mode == "explicit-custom":
        arguments.append("--benchmark-storage=file://" + str(explicit))
    environment = {**os.environ, "PYTEST_ADDOPTS": ""}
    environment.pop("PYTEST_PLUGINS", None)
    if mode != "blocked":
        environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    else:
        environment.pop("PYTEST_DISABLE_PLUGIN_AUTOLOAD", None)
    bootstrap = (
        f"import sys,runpy;sys.path.insert(0,{str(ROOT)!r});"
        "sys.argv=['pytest',*sys.argv[1:]];runpy.run_module('pytest',run_name='__main__')"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-c", bootstrap, *arguments],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 passed" in result.stdout
    assert not (tmp_path / ".benchmarks").exists()
    assert expected.is_dir() is enabled
    if mode == "explicit-custom":
        assert not nominated.exists()
