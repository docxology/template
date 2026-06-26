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
    snapshots: dict[Path, bytes] = {}
    for path in _iter_mutable_project_sources():
        try:
            snapshots[path] = path.read_bytes()
        except OSError:
            continue
    return snapshots


@pytest.fixture(autouse=True)
def _restore_mutable_project_sources(_mutable_project_source_snapshots: dict[Path, bytes]) -> Iterator[None]:
    yield
    _restore_snapshots(_mutable_project_source_snapshots)


@pytest.fixture
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture
def tmp_output(tmp_path: Path) -> Path:
    out = tmp_path / "output"
    for sub in ("data", "figures", "simulations", "reports", "web"):
        (out / sub).mkdir(parents=True, exist_ok=True)
    return out
