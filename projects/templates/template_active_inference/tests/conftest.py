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

# Tracked manuscript files whose composed/regenerated content embeds live
# output/ artifact state (e.g. the "Generated status" table in
# 08_methods_sheaf.md and the 00_00_sheaf_coverage.md page). The gate tests
# call compose_all_sections / ensure_coverage_artifacts on the real project
# root, which legitimately rewrites these tracked files to reflect whatever
# artifacts the suite produced (pymdp present vs absent, etc.). That left the
# working tree dirty after a run, so a contributor's `git commit -a` could
# commit degraded values. We snapshot every tracked manuscript/*.md before the
# session and restore the byte-for-byte original afterward so the suite always
# leaves the working tree clean. The session-scoped finalizer below is the
# single guarantee — individual tests need not reason about it.
_MANUSCRIPT_DIR = PROJECT_ROOT / "manuscript"


@pytest.fixture(scope="session", autouse=True)
def _restore_tracked_manuscript() -> Iterator[None]:
    """Snapshot tracked manuscript markdown, restore it at session end.

    Yields nothing; its only job is the teardown restore so the test suite
    never mutates git-tracked manuscript sources (EX-2).
    """
    snapshots: dict[Path, str] = {}
    if _MANUSCRIPT_DIR.is_dir():
        for md in sorted(_MANUSCRIPT_DIR.rglob("*.md")):
            try:
                snapshots[md] = md.read_text(encoding="utf-8")
            except OSError:
                continue
    yield
    for path, original in snapshots.items():
        try:
            if path.read_text(encoding="utf-8") != original:
                path.write_text(original, encoding="utf-8")
        except OSError:
            # File removed by a test it owns; recreate the tracked original.
            path.write_text(original, encoding="utf-8")


@pytest.fixture
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture
def tmp_output(tmp_path: Path) -> Path:
    out = tmp_path / "output"
    for sub in ("data", "figures", "simulations", "reports", "web"):
        (out / sub).mkdir(parents=True, exist_ok=True)
    return out
