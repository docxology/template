"""Pytest configuration for template_pitch_deck project tests."""

import hashlib
import importlib.util
import os
import shutil
import stat
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

# Force headless backend for matplotlib in tests
os.environ.setdefault("MPLBACKEND", "Agg")

ROOT = Path(__file__).resolve().parent.parent
TESTS = Path(__file__).resolve().parent

# SDK selection precedes own namespace registration; no DATA root is import authority.
_bootstrap_spec = importlib.util.spec_from_file_location("pitch_test_bootstrap", ROOT / "scripts/_bootstrap.py")
if _bootstrap_spec is None or _bootstrap_spec.loader is None:
    raise ImportError("actual own project bootstrap is unavailable")
_bootstrap = importlib.util.module_from_spec(_bootstrap_spec)
_bootstrap_spec.loader.exec_module(_bootstrap)
_bootstrap.bootstrap_project(ROOT)
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))


def _output_state(root: Path) -> dict[str, tuple[object, ...]] | None:
    """Compare fixture outputs without following links or changing held files."""
    if root.is_symlink() or not root.is_dir():
        return None
    rows: dict[str, tuple[object, ...]] = {".": ("directory", stat.S_IMODE(root.lstat().st_mode))}
    for directory, names, files in os.walk(root, followlinks=False):
        for name in sorted(names + files):
            path = Path(directory) / name
            metadata = path.lstat()
            mode = stat.S_IMODE(metadata.st_mode)
            relative = path.relative_to(root).as_posix()
            if stat.S_ISLNK(metadata.st_mode):
                rows[relative] = ("link", mode, os.readlink(path))
            elif stat.S_ISDIR(metadata.st_mode):
                rows[relative] = ("directory", mode)
            elif stat.S_ISREG(metadata.st_mode):
                rows[relative] = ("file", mode, metadata.st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
            else:
                raise ValueError("unsupported project output fixture member")
    return rows


@pytest.fixture(scope="session", autouse=True)
def _preserve_project_output(
    tmp_path_factory: pytest.TempPathFactory,
) -> Iterator[None]:
    """Restore real generated decks after the suite proves in-place rendering."""
    output = ROOT / "output"
    snapshot = tmp_path_factory.mktemp("pitch-deck-output") / "output"
    existed = output.is_dir()
    if existed:
        shutil.copytree(output, snapshot, symlinks=True)

    yield

    # A focused suite may only read outputs. Replacing those identical files
    # would change their physical custody despite preserving every byte.
    if existed and _output_state(output) == _output_state(snapshot):
        return
    if output.exists():
        shutil.rmtree(output)
    if existed:
        shutil.copytree(snapshot, output, symlinks=True)


@pytest.fixture(scope="session", autouse=True)
def _verify_bound_source_data() -> Iterator[None]:
    """Keep the declared DATA reference separate from SDK and own source imports."""
    from template_pitch_deck.paths import data_repo_root, verify_reference_inputs

    data_repo_root(ROOT)
    yield
    verify_reference_inputs()
