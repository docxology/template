"""Real controller API, receipt promotion, and refusal contracts."""

from __future__ import annotations

import json
import os
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
    shutil.copyfile(PROJECT / "pyproject.toml", destination / "pyproject.toml")
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


@pytest.mark.skipif(
    os.name != "posix" or not hasattr(os, "O_PATH") or os.geteuid() == 0,
    reason="requires real nonroot search-only ancestor traversal",
)
def test_receipt_invalidation_and_rollback_traverse_search_only_project_ancestors(tmp_path: Path) -> None:
    ancestor = tmp_path.resolve() / "search-only"
    root = _project(ancestor / "project")
    receipt = root / "output/receipt.json"
    receipt.parent.mkdir()
    receipt.write_text("stale receipt must be invalidated\n")
    external_directory = ancestor / "external-receipts"
    external_directory.mkdir()
    external_kept = external_directory / "kept.json"
    external_kept.write_text("unrelated external bytes\n")
    external_alias = ancestor / "external-alias"
    external_alias.symlink_to(external_directory, target_is_directory=True)
    ancestor.chmod(0o111)
    try:
        with pytest.raises(PermissionError):
            list(ancestor.iterdir())
        with _owned_interpreter_state():
            arguments = launcher._arguments(_arguments(root, receipt))
            assert launcher._launch(arguments, time.monotonic() - 1) == 124
            assert not receipt.exists() and not (root / "formal/lean/.lake").exists()
            receipt.write_text("expired promoted receipt\n")
            arguments.receipt_promoted = True
            launcher._discard_promoted_receipt(arguments)
            assert not arguments.receipt_promoted and not receipt.exists()
            # An external target below the same search-only ancestor must use
            # a readable destination root, including missing nested parents.
            from infrastructure.core.files.secure_write import atomic_write_text_confined

            external_nested = external_directory / "nested/receipt.json"
            external_arguments = launcher._arguments(_arguments(root, external_nested))
            assert launcher._receipt_root(external_arguments) == external_directory
            atomic_write_text_confined(
                launcher._receipt_root(external_arguments), external_nested, "stale external receipt\n"
            )
            assert launcher._launch(external_arguments, time.monotonic() - 1) == 124
            assert not external_nested.exists()
            external_nested.write_text("expired promoted external receipt\n")
            external_arguments.receipt_promoted = True
            launcher._discard_promoted_receipt(external_arguments)
            assert not external_arguments.receipt_promoted and not external_nested.exists()
            launcher._discard_promoted_receipt(external_arguments)
            assert external_kept.read_text() == "unrelated external bytes\n"

            # Root selection must not resolve a symlink or normalize a parent
            # traversal before the existing confined writer can refuse it.
            alias_receipt = external_alias / "kept.json"
            alias_arguments = launcher._arguments(_arguments(root, alias_receipt))
            assert launcher._launch(alias_arguments, time.monotonic() - 1) == 2
            assert external_kept.read_text() == "unrelated external bytes\n"
            traversal = external_directory / "nested/../kept.json"
            traversal_arguments = launcher._arguments(_arguments(root, traversal))
            with pytest.raises(ValueError, match="parent traversal"):
                launcher._receipt_root(traversal_arguments)
            assert external_kept.read_text() == "unrelated external bytes\n"
    finally:
        ancestor.chmod(0o700)
    # Explicit destinations outside the project remain supported and confined.
    external = tmp_path / "external-receipt.json"
    external.write_text("expired external receipt\n")
    with _owned_interpreter_state():
        arguments = launcher._arguments(_arguments(root, external))
        arguments.receipt_promoted = True
        launcher._discard_promoted_receipt(arguments)
        assert not arguments.receipt_promoted and not external.exists()


def test_external_receipt_walk_creates_only_missing_destination_descendants(tmp_path: Path) -> None:
    from infrastructure.core.files.secure_write import atomic_write_text_confined

    root = _project(tmp_path / "project")
    external = tmp_path / "external"
    external.mkdir()
    kept = external / "kept.json"
    kept.write_bytes(b"unrelated external evidence\n")
    destination = external / "missing/deeper/receipt.json"
    project_receipt = root / "output/nested/receipt.json"
    with _owned_interpreter_state():
        project_arguments = launcher._arguments(_arguments(root, project_receipt))
        assert launcher._receipt_root(project_arguments) == root
        arguments = launcher._arguments(_arguments(root, destination))
        assert launcher._receipt_root(arguments) == external
        assert not destination.parent.exists() and not (root / "output").exists()
        atomic_write_text_confined(
            launcher._receipt_root(arguments), destination, "stale external receipt\n", mode=0o600
        )
        assert destination.read_text() == "stale external receipt\n"
        assert destination.stat().st_mode & 0o777 == 0o600
        assert launcher._receipt_root(arguments) == destination.parent
        assert launcher._launch(arguments, time.monotonic() - 1) == 124
        assert not destination.exists() and not arguments.receipt_promoted
        destination.write_text("expired promoted external receipt\n")
        arguments.receipt_promoted = True
        launcher._discard_promoted_receipt(arguments)
        assert not arguments.receipt_promoted and not destination.exists()
        launcher._discard_promoted_receipt(arguments)
    assert kept.read_bytes() == b"unrelated external evidence\n"
    assert not (root / "formal/lean/.lake").exists() and not (root / "output").exists()


def test_missing_external_receipt_rollback_is_idempotent_without_creating_parents(tmp_path: Path) -> None:
    root = _project(tmp_path / "project")
    missing = tmp_path / "never-created/nested/receipt.json"
    with _owned_interpreter_state():
        arguments = launcher._arguments(_arguments(root, missing))
        assert launcher._receipt_root(arguments) == tmp_path
        arguments.receipt_promoted = True
        launcher._discard_promoted_receipt(arguments)
        assert not arguments.receipt_promoted and not missing.parent.exists()
        launcher._discard_promoted_receipt(arguments)
    assert not (tmp_path / "never-created").exists()
    assert not (root / "formal/lean/.lake").exists()


@pytest.mark.parametrize("unsafe", ["parent-symlink", "leaf-symlink", "parent-traversal", "parent-file"])
def test_external_receipt_refusal_preserves_unrelated_evidence(
    tmp_path: Path, unsafe: str, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _project(tmp_path / "project")
    external = tmp_path / "external"
    external.mkdir()
    kept = external / "kept.json"
    kept.write_bytes(b"unrelated evidence must survive refusal\n")
    alias = tmp_path / "external-alias"
    alias.symlink_to(external, target_is_directory=True)
    linked_receipt = external / "linked-receipt.json"
    linked_receipt.symlink_to(kept)
    blocked = external / "not-a-directory"
    blocked.write_bytes(b"keep this regular parent too\n")
    destinations = {
        "parent-symlink": alias / "kept.json",
        "leaf-symlink": linked_receipt,
        "parent-traversal": external / "nested/../kept.json",
        "parent-file": blocked / "receipt.json",
    }
    destination = destinations[unsafe]
    with _owned_interpreter_state():
        arguments = launcher._arguments(_arguments(root, destination))
        if unsafe == "parent-traversal":
            with pytest.raises(ValueError, match="parent traversal"):
                launcher._receipt_root(arguments)
        assert launcher._launch(arguments, time.monotonic() - 1) == 2
        arguments.receipt_promoted = True
        launcher._discard_promoted_receipt(arguments)
        assert not arguments.receipt_promoted
        launcher._discard_promoted_receipt(arguments)
    diagnostic = capsys.readouterr().err
    assert "Invalid Formal receipt destination:" in diagnostic
    assert "Expired Formal receipt cleanup refused:" in diagnostic
    assert kept.read_bytes() == b"unrelated evidence must survive refusal\n"
    assert blocked.read_bytes() == b"keep this regular parent too\n"
    assert alias.is_symlink() and linked_receipt.is_symlink()
    assert not (root / "formal/lean/.lake").exists() and not (root / "output").exists()
