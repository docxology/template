"""Actual direct-shell startup refuses normal-cache poison and missing tools."""

from __future__ import annotations

import json
import os
import py_compile
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

PROJECT = Path(__file__).resolve().parents[1]
PLATFORM_VERSION = tomllib.loads((PROJECT / "pyproject.toml").read_text())["tool"]["template"]["platform_version"]


def _project(destination: Path) -> Path:
    for leaf in ("src", "formal", "scripts"):
        shutil.copytree(
            PROJECT / leaf,
            destination / leaf,
            ignore=shutil.ignore_patterns("__pycache__", ".lake", "states", "*TTrace*"),
        )
    shutil.copyfile(PROJECT / "pyproject.toml", destination / "pyproject.toml")
    return destination


@pytest.mark.timeout(180)
def test_actual_canonical_shell_ignores_timestamp_valid_poisoned_tool_cache(tmp_path: Path) -> None:
    root = _project(tmp_path / "project")
    source = root / "src/template_formal/tool_acceptance.py"
    marker = tmp_path / "normal-cache-side-effect"
    original = source.read_bytes() + b"\n#" + b"x" * 512
    injected = source.read_bytes().replace(
        b"import argparse\n",
        f"import argparse\nfrom pathlib import Path as _CachePath\n_CachePath({str(marker)!r}).touch()\n".encode(),
        1,
    )
    assert len(injected) < len(original)
    source.write_bytes(injected + b"\n#" + b"x" * (len(original) - len(injected) - 2))
    # Poison the ordinary ``__pycache__`` entry that an isolated interpreter
    # without a pycache prefix reads. The audited Stage 01 runner sets
    # ``sys.pycache_prefix`` for this pytest process, so the default ``cfile``
    # would land in that private prefix and the poison would never be visible.
    ordinary_cache = source.parent / "__pycache__" / f"{source.stem}.{sys.implementation.cache_tag}.pyc"
    py_compile.compile(
        str(source),
        cfile=str(ordinary_cache),
        doraise=True,
        invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP,
    )
    observation = source.stat()
    source.write_bytes(original)
    os.utime(source, ns=(observation.st_atime_ns, observation.st_mtime_ns))
    ordinary = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "import sys;sys.path.insert(0,sys.argv[1]);import template_formal.tool_acceptance",
            str(root / "src"),
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert ordinary.returncode == 0 and marker.is_file(), (ordinary.returncode, marker.is_file(), ordinary.stderr)
    marker.unlink()
    receipt = root / "output/.pipeline/formal_tools/receipt.json"
    environment = dict(os.environ, FORMAL_PYTHON_BIN=sys.executable)
    result = subprocess.run(
        ["bash", str(root / "scripts/check_formal_specs.sh"), "--timeout", "120", "--receipt", str(receipt)],
        env=environment,
        capture_output=True,
        text=True,
        timeout=150,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(receipt.read_text())
    assert payload["status"] == "passed" and payload["source_unchanged"] is True
    assert payload["tool_launcher"] == {
        "execution_binding": "preimport-audited-fresh-prefix",
        "controller_execution_binding": "fresh-prefix",
        "platform_version": PLATFORM_VERSION,
    }
    assert not marker.exists() and source.read_bytes() == original
    assert not (root / "formal/lean/.lake").exists()


def test_missing_optional_platform_blocks_before_native_tools(tmp_path: Path) -> None:
    root = _project(tmp_path / "project")
    receipt = root / "output/.pipeline/receipt.json"
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-S",
            str(root / "src/template_formal/_tool_launcher.py"),
            "--project-root",
            str(root),
            "--receipt",
            str(receipt),
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 75 and "formal-tools" in result.stderr
    assert not receipt.exists() and not (root / "formal/lean/.lake").exists()


def test_launcher_invalid_timeout_cannot_run_or_emit_receipt(tmp_path: Path) -> None:
    root = _project(tmp_path / "project")
    receipt = root / "output/.pipeline/receipt.json"
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            str(root / "src/template_formal/_tool_launcher.py"),
            "--project-root",
            str(root),
            "--timeout",
            "0",
            "--receipt",
            str(receipt),
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 2 and "timeout" in result.stderr
    assert not receipt.exists() and not (root / "formal/lean/.lake").exists()


def test_expired_launcher_without_optional_platform_keeps_timeout_and_no_receipt(tmp_path: Path) -> None:
    root = _project(tmp_path / "project")
    receipt = root / "output/.pipeline/receipt.json"
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-S",
            str(root / "src/template_formal/_tool_launcher.py"),
            "--project-root",
            str(root),
            "--timeout",
            "0.000000001",
            "--receipt",
            str(receipt),
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 124, result.stdout + result.stderr
    assert not receipt.exists() and not (root / "formal/lean/.lake").exists()
