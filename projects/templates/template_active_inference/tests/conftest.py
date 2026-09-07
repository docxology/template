"""Shared fixtures for template_active_inference tests.

Gate-negative-control overhead (cold gate ~250s) is the single largest
wall-time cost. Use the fast dev loop to skip it entirely:

    uv run bash scripts/run_ai_direct_fast.sh

That runs only the test_*_direct.py family (105+ tests, ~25-40s).
The full release profile keeps the real-tree artifact and publication gates
explicitly marked as slow; it remains the lane to run before release.
"""

from __future__ import annotations

import os
import stat
import sys
from collections.abc import Callable, Iterator
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


def pytest_collection_modifyitems(
    session: pytest.Session,
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Pre-warm gate artifacts only when the collected selection can use them.

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

    Collection hooks run before pytest-timeout's per-item timer starts, so the
    cold bootstrap can run to completion here. If pymdp is
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
    Gate-consuming tests opt into the ``requires_gate_artifacts`` marker. This
    keeps the prewarm tied to the actual consumer rather than to the filename
    of every non-direct test. Gate consumers are also marked ``slow``; a quick
    profile therefore skips both the tests and their prewarm, while release and
    unfiltered diagnostic runs retain the one-time bootstrap.
    """

    # The repo wrapper performs a separate ``pytest --collect-only`` probe
    # before the real run. Guard at the hook boundary so discovery can never
    # pay the expensive artifact-prewarm cost, even if pytest changes how the
    # session option object is exposed to the helper.
    if getattr(config.option, "collectonly", False):
        return
    markexpr = str(getattr(config.option, "markexpr", "") or "")
    if _selection_needs_gate_prewarm(items, markexpr=markexpr):
        _prewarm_gate_artifacts(session)


def _selection_needs_gate_prewarm(items: list[pytest.Item], *, markexpr: str = "") -> bool:
    """Return whether selected items explicitly consume real gate artifacts.

    ``pytest_collection_modifyitems`` can run before another plugin applies a
    ``-m`` deselection, so account for the quick profile here as well. This
    prevents a slow gate's prewarm from leaking into the quick lane while
    still allowing an unfiltered or release run to prepare the shared cache.
    """
    for item in items:
        marker_getter = getattr(item, "get_closest_marker", None)
        if marker_getter is None or marker_getter("requires_gate_artifacts") is None:
            continue
        if "not slow" in markexpr and marker_getter("slow") is not None:
            continue
        return True
    return False


def _prewarm_gate_artifacts(
    session: pytest.Session,
    *,
    source_iterator: Callable[[], Iterator[Path]] | None = None,
) -> None:
    """Prewarm helper with an injectable source iterator for contract tests."""
    if getattr(session.config.option, "collectonly", False):
        return

    try:
        from gate_support import ensure_gate_artifacts

        iterator = _iter_mutable_project_sources if source_iterator is None else source_iterator
        initial_paths, snapshots = _capture_snapshots(iterator())
        try:
            ensure_gate_artifacts(PROJECT_ROOT)
        finally:
            _remove_new_regular_files(PROJECT_ROOT, initial_paths, iterator())
            _restore_snapshots(PROJECT_ROOT, snapshots)
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
    "docs/reference/method-inventory.md",
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


def _is_confined_regular_file(
    root: Path,
    path: Path,
    *,
    allow_missing_leaf: bool = False,
) -> bool:
    """Return whether *path* is a regular file below *root* without symlinks."""
    lexical_root = root.absolute()
    lexical_path = path.absolute()
    try:
        relative = lexical_path.relative_to(lexical_root)
        root_metadata = lexical_root.lstat()
    except (OSError, ValueError):
        return False
    if not relative.parts or stat.S_ISLNK(root_metadata.st_mode):
        return False
    if not stat.S_ISDIR(root_metadata.st_mode):
        return False

    current = lexical_root
    final_index = len(relative.parts) - 1
    for index, part in enumerate(relative.parts):
        current /= part
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            return allow_missing_leaf and index == final_index
        except OSError:
            return False
        if stat.S_ISLNK(metadata.st_mode):
            return False
        if index < final_index and not stat.S_ISDIR(metadata.st_mode):
            return False
        if index == final_index and not stat.S_ISREG(metadata.st_mode):
            return False
    return True


def _iter_declared_mutable_files(
    root: Path,
    patterns: tuple[str, ...],
    explicit_files: tuple[str, ...] = (),
) -> Iterator[Path]:
    """Yield only bounded regular files selected by the declared surfaces."""
    lexical_root = root.absolute()
    seen: set[Path] = set()
    for pattern in patterns:
        pattern_path = Path(pattern)
        if pattern_path.is_absolute() or ".." in pattern_path.parts:
            raise ValueError(f"mutable-file pattern escapes project root: {pattern}")
        for path in sorted(lexical_root.glob(pattern)):
            if _is_confined_regular_file(lexical_root, path) and path not in seen:
                seen.add(path)
                yield path
    for rel in explicit_files:
        rel_path = Path(rel)
        if rel_path.is_absolute() or ".." in rel_path.parts:
            raise ValueError(f"mutable-file path escapes project root: {rel}")
        path = lexical_root / rel_path
        if _is_confined_regular_file(lexical_root, path) and path not in seen:
            seen.add(path)
            yield path


def _iter_mutable_project_sources() -> Iterator[Path]:
    yield from _iter_declared_mutable_files(
        PROJECT_ROOT,
        _MUTABLE_PROJECT_SOURCE_GLOBS,
        _MUTABLE_PROJECT_SOURCE_FILES,
    )


def _iter_mutable_project_outputs() -> Iterator[Path]:
    yield from _iter_declared_mutable_files(PROJECT_ROOT, _MUTABLE_PROJECT_OUTPUT_GLOBS)


def _snapshot_paths(paths: Iterator[Path]) -> dict[Path, bytes]:
    snapshots: dict[Path, bytes] = {}
    for path in paths:
        try:
            snapshots[path] = path.read_bytes()
        except OSError:
            continue
    return snapshots


def _capture_snapshots(paths: Iterator[Path]) -> tuple[frozenset[Path], dict[Path, bytes]]:
    """Record every initial path even when reading one file fails."""
    initial_paths = frozenset(paths)
    return initial_paths, _snapshot_paths(iter(sorted(initial_paths)))


def _remove_new_regular_files(
    root: Path,
    initial_paths: frozenset[Path],
    current_paths: Iterator[Path],
) -> None:
    """Remove newly created regular files, confined to the caller's declared scan."""
    for path in sorted(set(current_paths) - initial_paths, reverse=True):
        if not _is_confined_regular_file(root, path):
            continue
        try:
            path.unlink()
        except FileNotFoundError:
            continue


def _restore_snapshots(root: Path, snapshots: dict[Path, bytes]) -> None:
    for path, original in snapshots.items():
        if not _is_confined_regular_file(root, path, allow_missing_leaf=True):
            continue
        try:
            if path.read_bytes() == original:
                continue
        except OSError:
            pass
        try:
            path.write_bytes(original)
        except OSError:
            continue


_MutableFileSnapshot = tuple[frozenset[Path], dict[Path, bytes]]


@pytest.fixture(scope="session")
def _mutable_project_source_snapshots() -> _MutableFileSnapshot:
    return _capture_snapshots(_iter_mutable_project_sources())


@pytest.fixture(scope="session")
def _mutable_project_output_snapshots() -> _MutableFileSnapshot:
    return _capture_snapshots(_iter_mutable_project_outputs())


@pytest.fixture(autouse=True)
def _restore_mutable_project_state(
    _mutable_project_source_snapshots: _MutableFileSnapshot,
    _mutable_project_output_snapshots: _MutableFileSnapshot,
) -> Iterator[None]:
    yield
    source_paths, source_snapshots = _mutable_project_source_snapshots
    output_paths, output_snapshots = _mutable_project_output_snapshots
    _remove_new_regular_files(PROJECT_ROOT, source_paths, _iter_mutable_project_sources())
    _remove_new_regular_files(PROJECT_ROOT, output_paths, _iter_mutable_project_outputs())
    _restore_snapshots(PROJECT_ROOT, source_snapshots)
    _restore_snapshots(PROJECT_ROOT, output_snapshots)


@pytest.fixture
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture
def tmp_output(tmp_path: Path) -> Path:
    out = tmp_path / "output"
    for sub in ("data", "figures", "simulations", "reports", "web"):
        (out / sub).mkdir(parents=True, exist_ok=True)
    return out
