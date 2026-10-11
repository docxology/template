"""Real controller API, receipt promotion, and refusal contracts."""

from __future__ import annotations

import json
import shutil
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

from template_formal import _tool_launcher as launcher


PROJECT = Path(__file__).resolve().parents[1]


@contextmanager
def _owned_interpreter_state() -> Iterator[None]:
    """Restore the real caller state after invoking a standalone controller."""
    prefix = sys.pycache_prefix
    dont_write = sys.dont_write_bytecode
    paths = list(sys.path)
    arguments = list(sys.argv)
    try:
        yield
    finally:
        sys.pycache_prefix = prefix
        sys.dont_write_bytecode = dont_write
        sys.path[:] = paths
        sys.argv[:] = arguments


def _project(destination: Path) -> Path:
    shutil.copytree(
        PROJECT / "formal",
        destination / "formal",
        ignore=shutil.ignore_patterns(".lake", "states", "*TTrace*"),
    )
    return destination


def _arguments(root: Path, receipt: Path, timeout: str = "120") -> list[str]:
    return ["--project-root", str(root), "--timeout", timeout, "--receipt", str(receipt)]


@pytest.mark.timeout(180)
def test_actual_main_api_checks_cached_tools_and_preserves_caller_and_sources(tmp_path: Path) -> None:
    root = _project(tmp_path / "project")
    receipt = root / "output/receipt.json"
    before = {path.relative_to(root): path.read_bytes() for path in (root / "formal").rglob("*") if path.is_file()}
    caller = (sys.pycache_prefix, sys.dont_write_bytecode, list(sys.path))
    with _owned_interpreter_state():
        assert launcher.main(_arguments(root, receipt)) == 0
    assert (sys.pycache_prefix, sys.dont_write_bytecode, list(sys.path)) == caller
    payload = json.loads(receipt.read_text())
    assert payload["status"] == "passed" and payload["source_unchanged"] is True
    checks = {check["name"]: check for check in payload["checks"]}
    assert checks["lean-build"]["exit_code"] == 0
    assert checks["tlc-AntProtocolFaultyNegControl"]["exit_code"] == 12
    assert payload["tool_launcher"]["execution_binding"] == "preimport-audited-fresh-prefix"
    assert {
        path.relative_to(root): path.read_bytes() for path in (root / "formal").rglob("*") if path.is_file()
    } == before
    assert not (root / "formal/lean/.lake").exists()


@pytest.mark.timeout(180)
def test_actual_launch_promotion_can_be_rolled_back_once(tmp_path: Path) -> None:
    root = _project(tmp_path / "project")
    receipt = root / "output/receipt.json"
    with _owned_interpreter_state():
        arguments = launcher._arguments(_arguments(root, receipt))
        assert launcher._launch(arguments, time.monotonic() + 120) == 0
        assert arguments.receipt_promoted and json.loads(receipt.read_text())["status"] == "passed"
        launcher._discard_promoted_receipt(arguments)
        assert not arguments.receipt_promoted and not receipt.exists()
        launcher._discard_promoted_receipt(arguments)
        assert not receipt.exists()


@pytest.mark.parametrize("timeout", ["0", "-1", "nan", "inf", "601"])
def test_api_invalid_budget_refuses_before_execution(tmp_path: Path, timeout: str) -> None:
    root = tmp_path / "never-materialized"
    receipt = root / "output/receipt.json"
    with _owned_interpreter_state(), pytest.raises(SystemExit) as caught:
        launcher.main(_arguments(root, receipt, timeout))
    assert caught.value.code == 2
    assert not root.exists()


def test_api_receipt_cannot_replace_admitted_source(tmp_path: Path) -> None:
    source = tmp_path / "src/author.py"
    source.parent.mkdir()
    source.write_bytes(b"author_source = True\n")
    with _owned_interpreter_state(), pytest.raises(SystemExit) as caught:
        launcher._arguments(_arguments(tmp_path, source))
    assert caught.value.code == 2 and source.read_bytes() == b"author_source = True\n"


def test_api_symlink_receipt_parent_is_refused_before_model_execution(tmp_path: Path) -> None:
    root = _project(tmp_path / "project")
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "receipt.json"
    sentinel.write_bytes(b"preserve unrelated evidence\n")
    (root / "output").symlink_to(outside, target_is_directory=True)
    with _owned_interpreter_state():
        assert launcher.main(_arguments(root, root / "output/receipt.json")) == 2
    assert sentinel.read_bytes() == b"preserve unrelated evidence\n"
    assert not (root / "formal/lean/.lake").exists()


@pytest.mark.parametrize("timeout", ["0.000000001", "0.01"])
def test_api_expired_total_budget_cannot_promote_success(tmp_path: Path, timeout: str) -> None:
    root = _project(tmp_path / "project")
    receipt = root / "output/receipt.json"
    started = time.monotonic()
    with _owned_interpreter_state():
        assert launcher.main(_arguments(root, receipt, timeout)) == 124
    assert not receipt.exists() and not (root / "formal/lean/.lake").exists()
    assert time.monotonic() - started < 30


def test_parent_worker_without_preimport_custody_is_blocked(tmp_path: Path) -> None:
    root = _project(tmp_path / "project")
    pending = tmp_path / "pending.json"
    with _owned_interpreter_state():
        sys.argv[:] = ["formal-worker", *_arguments(root, root / "output/receipt.json")]
        assert launcher.worker_main(tmp_path / "unadmitted-prefix", time.monotonic() + 120, pending) == 75
    assert not pending.exists() and not (root / "output").exists()
