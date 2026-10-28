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
import tempfile
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

    Collection and execution share one disposable project tree. Even an
    explicitly enabled rebuild writes only that copy, preserving the admitted
    source's bytes and physical identity throughout the enclosing pipeline.
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

        root = _session_project_root(session.config)
        iterator = (lambda: _iter_mutable_project_sources(root)) if source_iterator is None else source_iterator
        initial_paths, snapshots = _capture_snapshots(iterator())
        try:
            ensure_gate_artifacts(root)
        finally:
            _remove_new_regular_files(root, initial_paths, iterator())
            _restore_snapshots(root, snapshots)
    except pytest.skip.Exception:
        pass
    except AssertionError as exc:
        pytest.exit(str(exc), returncode=1)


# Gate controls and composition operate on the shared disposable project copy.
# Restore its mutable inputs between tests so one control cannot affect another.
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


def _iter_mutable_project_sources(root: Path = PROJECT_ROOT) -> Iterator[Path]:
    yield from _iter_declared_mutable_files(
        root,
        _MUTABLE_PROJECT_SOURCE_GLOBS,
        _MUTABLE_PROJECT_SOURCE_FILES,
    )


def _iter_mutable_project_outputs(root: Path = PROJECT_ROOT) -> Iterator[Path]:
    yield from _iter_declared_mutable_files(root, _MUTABLE_PROJECT_OUTPUT_GLOBS)


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


def _stat_signature(path: Path) -> tuple[int, int, int, int, int] | None:
    """Witness unchanged bytes cheaply, including replacement and backdated writes."""
    try:
        metadata = path.stat()
    except OSError:
        return None
    return (metadata.st_dev, metadata.st_ino, metadata.st_size, metadata.st_mtime_ns, metadata.st_ctime_ns)


def _restore_snapshots(
    root: Path,
    snapshots: dict[Path, bytes],
    stats: dict[Path, tuple[int, int, int, int, int]] | None = None,
) -> None:
    for path, original in snapshots.items():
        if not _is_confined_regular_file(root, path, allow_missing_leaf=True):
            continue
        recorded = stats.get(path) if stats is not None else None
        if recorded is not None and _stat_signature(path) == recorded:
            continue
        try:
            if path.read_bytes() == original:
                if stats is not None:
                    stats[path] = _stat_signature(path) or (0, 0, 0, 0, 0)
                continue
        except OSError:
            pass
        try:
            path.write_bytes(original)
            if stats is not None:
                stats[path] = _stat_signature(path) or (0, 0, 0, 0, 0)
        except OSError:
            continue


_MutableFileSnapshot = tuple[frozenset[Path], dict[Path, bytes]]
_MutableFileStats = dict[Path, tuple[int, int, int, int, int]]
_MutableProjectState = tuple[Path, _MutableFileSnapshot, _MutableFileSnapshot, _MutableFileStats, _MutableFileStats]


def _capture_stat_signatures(snapshots: dict[Path, bytes]) -> _MutableFileStats:
    return {path: sig for path in snapshots for sig in (_stat_signature(path),) if sig is not None}


@pytest.fixture(scope="session")
def _mutable_project_source_snapshots(project_root: Path, pytestconfig: pytest.Config) -> _MutableFileSnapshot:
    return _session_mutable_project_state(pytestconfig)[1]


@pytest.fixture(scope="session")
def _mutable_project_output_snapshots(project_root: Path, pytestconfig: pytest.Config) -> _MutableFileSnapshot:
    return _session_mutable_project_state(pytestconfig)[2]


@pytest.fixture(scope="session")
def _mutable_project_source_stats(
    _mutable_project_source_snapshots: _MutableFileSnapshot,
    pytestconfig: pytest.Config,
) -> _MutableFileStats:
    return _session_mutable_project_state(pytestconfig)[3]


@pytest.fixture(scope="session")
def _mutable_project_output_stats(
    _mutable_project_output_snapshots: _MutableFileSnapshot,
    pytestconfig: pytest.Config,
) -> _MutableFileStats:
    return _session_mutable_project_state(pytestconfig)[4]


def _standard_fixture_ownership(request: pytest.FixtureRequest) -> bool:
    """Use actual pytest fixture ownership; unknown collectors stay conservative."""
    try:
        return (
            isinstance(request.node, pytest.Function)
            and isinstance(request.fixturenames, list)
            and all(type(name) is str for name in request.fixturenames)
        )
    except Exception:  # noqa: BLE001 - unavailable ownership requires conservative restoration
        return False


@pytest.fixture(autouse=True)
def _restore_mutable_project_state(
    request: pytest.FixtureRequest,
) -> Iterator[None]:
    state = None if _standard_fixture_ownership(request) else _session_mutable_project_state(request.config)
    yield
    if state is None:
        # fixturenames includes transitive dependencies and actual dynamic
        # getfixturevalue requests made after this autouse fixture yielded.
        if _standard_fixture_ownership(request) and "project_root" not in request.fixturenames:
            return
        if _PROJECT_STATE not in request.config.stash:
            raise RuntimeError("shared project mutation has no pre-execution restoration baseline")
        state = request.config.stash[_PROJECT_STATE]
    project_root, source_state, output_state, source_stats, output_stats = state
    source_paths, source_snapshots = source_state
    output_paths, output_snapshots = output_state
    _remove_new_regular_files(project_root, source_paths, _iter_mutable_project_sources(project_root))
    _remove_new_regular_files(project_root, output_paths, _iter_mutable_project_outputs(project_root))
    _restore_snapshots(project_root, source_snapshots, source_stats)
    _restore_snapshots(project_root, output_snapshots, output_stats)


_PROJECT_COPY = pytest.StashKey[Path]()
_PROJECT_STATE = pytest.StashKey[_MutableProjectState]()


def _session_project_root(config: pytest.Config) -> Path:
    """Share one owned copy between collection prewarm and test fixtures."""
    if _PROJECT_COPY not in config.stash:
        from direct_recompute_support import copy_project_tree

        temporary = tempfile.TemporaryDirectory(prefix="active-gate-project-")
        config.add_cleanup(temporary.cleanup)
        config.stash[_PROJECT_COPY] = copy_project_tree(Path(temporary.name).resolve() / PROJECT_ROOT.name)
    return config.stash[_PROJECT_COPY]


def _session_mutable_project_state(config: pytest.Config) -> _MutableProjectState:
    """Capture the baseline before any caller receives the shared project copy."""
    if _PROJECT_STATE not in config.stash:
        root = _session_project_root(config)
        sources = _capture_snapshots(_iter_mutable_project_sources(root))
        outputs = _capture_snapshots(_iter_mutable_project_outputs(root))
        config.stash[_PROJECT_STATE] = (
            root,
            sources,
            outputs,
            _capture_stat_signatures(sources[1]),
            _capture_stat_signatures(outputs[1]),
        )
    return config.stash[_PROJECT_STATE]


@pytest.fixture(scope="session")
def project_root(pytestconfig: pytest.Config) -> Path:
    """Keep destructive gate controls outside admitted source and publication bytes."""
    return _session_mutable_project_state(pytestconfig)[0]


@pytest.fixture
def tmp_output(tmp_path: Path) -> Path:
    out = tmp_path / "output"
    for sub in ("data", "figures", "simulations", "reports", "web"):
        (out / sub).mkdir(parents=True, exist_ok=True)
    return out
