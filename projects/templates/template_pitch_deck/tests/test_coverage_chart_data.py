"""No-mocks tests for src/coverage_chart_data.py — real COUNTS.md content."""

from __future__ import annotations

from pathlib import Path

import pytest

from coverage_chart_data import read_all_exemplar_coverage
from paths import locate_repo_root, project_root


@pytest.fixture(scope="module")
def repo_root():
    return locate_repo_root(project_root())


def test_read_all_exemplar_coverage_returns_real_rows(repo_root):
    rows = read_all_exemplar_coverage(repo_root)
    assert len(rows) > 5
    names = {name for name, _, _ in rows}
    assert "template_pitch_deck" in names
    assert "template_template" in names


def test_read_all_exemplar_coverage_values_are_plausible(repo_root):
    rows = read_all_exemplar_coverage(repo_root)
    for name, test_count, coverage_pct in rows:
        assert test_count > 0, f"{name} has non-positive test count"
        assert 0.0 <= coverage_pct <= 100.0, f"{name} coverage out of range: {coverage_pct}"


def test_read_all_exemplar_coverage_sorted_descending(repo_root):
    rows = read_all_exemplar_coverage(repo_root)
    coverages = [coverage for _, _, coverage in rows]
    assert coverages == sorted(coverages, reverse=True)


def test_read_all_exemplar_coverage_parses_real_synthetic_table(tmp_path: Path):
    fake_root = tmp_path
    generated = fake_root / "docs" / "_generated"
    generated.mkdir(parents=True)
    (generated / "COUNTS.md").write_text(
        "| `alpha` | 10 | 90.00 % |\n| `beta` | 20 | 99.99 % |\n| `gamma` | 5 | 50.50 % |\n",
        encoding="utf-8",
    )
    rows = read_all_exemplar_coverage(fake_root)
    assert rows == [("beta", 20, 99.99), ("alpha", 10, 90.0), ("gamma", 5, 50.5)]


def test_read_all_exemplar_coverage_raises_on_missing_file(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        read_all_exemplar_coverage(tmp_path)
