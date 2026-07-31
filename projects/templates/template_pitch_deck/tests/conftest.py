"""Pytest configuration for template_pitch_deck project tests."""

import os
import shutil
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

# Force headless backend for matplotlib in tests
os.environ.setdefault("MPLBACKEND", "Agg")

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
TESTS = Path(__file__).resolve().parent
for path in (SRC, TESTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

# Add repo root so `infrastructure` is importable (deck_tokens.py, content_loader.py
# import infrastructure.project.public_scope / infrastructure.rendering.slide_deck)
# regardless of which pyproject.toml pytest picks as its rootdir/configfile —
# a standalone single-test-file invocation resolves rootdir to this project's
# own pyproject.toml, which only puts "." and "src" on pythonpath.
from paths import locate_repo_root  # noqa: E402

REPO_ROOT = locate_repo_root(ROOT)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


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

    if output.exists():
        shutil.rmtree(output)
    if existed:
        shutil.copytree(snapshot, output, symlinks=True)
