"""Shared fixtures for template_active_inference tests."""

from __future__ import annotations

import os
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TESTS = Path(__file__).resolve().parent
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

os.environ.setdefault("MPLBACKEND", "Agg")


def pytest_sessionstart(session: pytest.Session) -> None:
    """Pre-warm the gate-artifact bootstrap before any per-test timeout starts.

    ``ensure_gate_artifacts`` (see ``gate_support.py``) memoizes its expensive
    full rebuild (pymdp policy sampling, figure generation, sheaf
    consolidation, GIF rendering) behind a content-signature cache that is
    genuinely fast (~0.01s) on every call *after* the first. But the first
    call alone measured ~250s on this machine -- well past the repo's real
    per-test timeout (``infrastructure.core.test_runner.DEFAULT_TIMEOUT =
    120``, forwarded as pytest's ``--timeout``). Whichever test happens to run
    first pays that cost inside its own timeout window and gets killed before
    the bootstrap finishes, so its cache marker never gets set -- the *next*
    test then retries the same never-completing bootstrap, cascading the
    failure across every test in the file (this is what made
    ``test_aggregate_forgery_controls.py`` fail wholesale rather than just its
    first test).

    ``pytest_sessionstart`` runs once, before pytest-timeout's per-item timer
    starts, so the cold bootstrap can run to completion here. If pymdp is
    unavailable, ``ensure_gate_artifacts`` calls ``pytest.skip(...)``, which
    is only meaningful inside a test's execution -- swallow it here and let
    each test's own ``ensure_gate_artifacts()`` call skip normally.

    The bootstrap (``compose_all_sections`` etc.) hydrates tracked
    ``manuscript/**/*.md`` sources as a side effect -- exactly what the
    ``_restore_mutable_project_sources`` fixture below exists to undo after
    each test. But that fixture's snapshot is only taken lazily, on the
    *first test's* setup phase; running the pre-warm here, before any test
    has started, would hydrate those files before the snapshot captures
    "original" content, permanently drifting the git-tracked source. Snapshot
    and restore the same mutable-source set around the pre-warm call so the
    real snapshot fixture still captures pristine content afterward. The
    signature cache this pre-warm populates is keyed on ``output/`` artifacts
    only (see ``_REQUIRED_GATE_ARTIFACTS``), not manuscript source, so
    restoring the manuscript files does not invalidate it.
    """

    if getattr(session.config.option, "collectonly", False):
        return

    try:
        from gate_support import ensure_gate_artifacts

        snapshots = {path: path.read_bytes() for path in _iter_mutable_project_sources()}
        try:
            ensure_gate_artifacts(PROJECT_ROOT)
        finally:
            _restore_snapshots(snapshots)
    except pytest.skip.Exception:
        pass
    except AssertionError as exc:
        pytest.exit(str(exc), returncode=1)


# Tracked source files whose composed/regenerated content embeds live output/
# artifact state. Gate tests call compose_all_sections / ensure_coverage_artifacts
# on the real project root, and negative controls temporarily mutate source
# contracts such as GNN and ontology files. Restore these files after every test
# so long full-suite runs do not let one mutation or compose pass leak into the
# next test.
_MUTABLE_PROJECT_SOURCE_GLOBS = (
    "manuscript/**/*.md",
    "manuscript/**/*.yaml",
    "gnn/**/*.md",
    "lean/**/*.lean",
)
_MUTABLE_PROJECT_SOURCE_FILES = (
    "data/claim_ledger.yaml",
    "pymdp.yaml",
    "src/roadmap_tracks/__init__.py",
    "tracks.yaml",
)
_MUTABLE_PROJECT_OUTPUT_GLOBS = (
    "output/data/**/*",
    "output/figures/*",
    "output/logs/**/*",
    "output/manuscript/**/*.md",
    "output/reports/**/*",
)


def _iter_mutable_project_sources() -> Iterator[Path]:
    seen: set[Path] = set()
    for pattern in _MUTABLE_PROJECT_SOURCE_GLOBS:
        for path in sorted(PROJECT_ROOT.glob(pattern)):
            if path.is_file() and path not in seen:
                seen.add(path)
                yield path
    for rel in _MUTABLE_PROJECT_SOURCE_FILES:
        path = PROJECT_ROOT / rel
        if path.is_file() and path not in seen:
            seen.add(path)
            yield path


def _iter_mutable_project_outputs() -> Iterator[Path]:
    seen: set[Path] = set()
    for pattern in _MUTABLE_PROJECT_OUTPUT_GLOBS:
        for path in sorted(PROJECT_ROOT.glob(pattern)):
            if path.is_file() and path not in seen:
                seen.add(path)
                yield path


def _snapshot_paths(paths: Iterator[Path]) -> dict[Path, bytes]:
    snapshots: dict[Path, bytes] = {}
    for path in paths:
        try:
            snapshots[path] = path.read_bytes()
        except OSError:
            continue
    return snapshots


def _restore_snapshots(snapshots: dict[Path, bytes]) -> None:
    for path, original in snapshots.items():
        try:
            if path.read_bytes() == original:
                continue
        except OSError:
            pass
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(original)


@pytest.fixture(scope="session")
def _mutable_project_source_snapshots() -> dict[Path, bytes]:
    return _snapshot_paths(_iter_mutable_project_sources())


@pytest.fixture(scope="session")
def _mutable_project_output_snapshots() -> dict[Path, bytes]:
    return _snapshot_paths(_iter_mutable_project_outputs())


@pytest.fixture(autouse=True)
def _restore_mutable_project_state(
    _mutable_project_source_snapshots: dict[Path, bytes],
    _mutable_project_output_snapshots: dict[Path, bytes],
) -> Iterator[None]:
    yield
    _restore_snapshots(_mutable_project_source_snapshots)
    _restore_snapshots(_mutable_project_output_snapshots)


@pytest.fixture
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture
def tmp_output(tmp_path: Path) -> Path:
    out = tmp_path / "output"
    for sub in ("data", "figures", "simulations", "reports", "web"):
        (out / sub).mkdir(parents=True, exist_ok=True)
    return out
