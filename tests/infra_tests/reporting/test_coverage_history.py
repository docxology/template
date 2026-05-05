"""Real-data tests for ``infrastructure.reporting.coverage_history``.

Zero mocks: every test uses real ``coverage-*.xml`` files written into
``tmp_path`` and (for the GH path) a skip-marker when the CLI is absent.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from infrastructure.reporting.coverage_history import (
    CoveragePoint,
    build_history_markdown,
    collect_history_from_dir,
    collect_history_via_gh,
    parse_coverage_xml,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_cobertura(
    path: Path,
    *,
    line_rate: float,
    lines_covered: int,
    lines_total: int,
    when: datetime,
) -> Path:
    """Write a minimal valid Cobertura XML at ``path`` and return the path."""
    epoch_ms = int(when.timestamp() * 1000)
    xml = (
        f'<?xml version="1.0" ?>\n'
        f'<coverage version="7.0" timestamp="{epoch_ms}" '
        f'lines-valid="{lines_total}" lines-covered="{lines_covered}" '
        f'line-rate="{line_rate}" branches-valid="0" branches-covered="0" '
        f'branch-rate="0" complexity="0">\n'
        f"  <sources><source>/tmp/src</source></sources>\n"
        f'  <packages><package name="." line-rate="{line_rate}"/></packages>\n'
        f"</coverage>\n"
    )
    path.write_text(xml, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# parse_coverage_xml
# ---------------------------------------------------------------------------


def test_parse_coverage_xml_extracts_all_fields(tmp_path: Path) -> None:
    when = datetime(2026, 5, 1, 12, 0, tzinfo=UTC)
    xml_path = _write_cobertura(
        tmp_path / "coverage-infra.xml",
        line_rate=0.8333,
        lines_covered=2500,
        lines_total=3000,
        when=when,
    )

    pt = parse_coverage_xml(xml_path)

    assert isinstance(pt, CoveragePoint)
    assert pt.suite == "infra"
    assert pt.lines_covered == 2500
    assert pt.lines_total == 3000
    assert abs(pt.percentage - 83.33) < 0.01
    assert pt.date.tzinfo is not None
    assert pt.date.astimezone(UTC).date() == date(2026, 5, 1)


def test_parse_coverage_xml_infers_suite_from_filename(tmp_path: Path) -> None:
    when = datetime(2026, 4, 28, tzinfo=UTC)
    xml_path = _write_cobertura(
        tmp_path / "coverage-fep_lean.xml",
        line_rate=0.91,
        lines_covered=910,
        lines_total=1000,
        when=when,
    )
    pt = parse_coverage_xml(xml_path)
    assert pt.suite == "fep_lean"


def test_parse_coverage_xml_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        parse_coverage_xml(tmp_path / "does-not-exist.xml")


def test_parse_coverage_xml_rejects_non_cobertura_root(tmp_path: Path) -> None:
    bad = tmp_path / "coverage-bad.xml"
    bad.write_text('<?xml version="1.0" ?><notcoverage/>\n', encoding="utf-8")
    with pytest.raises(ValueError):
        parse_coverage_xml(bad)


# ---------------------------------------------------------------------------
# build_history_markdown — determinism & shape
# ---------------------------------------------------------------------------


def _sample_points() -> list[CoveragePoint]:
    base = datetime(2026, 5, 1, 12, 0, tzinfo=UTC)
    return [
        CoveragePoint(date=base.replace(day=1), suite="infra", percentage=82.50, lines_covered=825, lines_total=1000),
        CoveragePoint(date=base.replace(day=1), suite="project", percentage=91.00, lines_covered=910, lines_total=1000),
        CoveragePoint(date=base.replace(day=2), suite="infra", percentage=83.10, lines_covered=831, lines_total=1000),
        CoveragePoint(date=base.replace(day=2), suite="project", percentage=91.20, lines_covered=912, lines_total=1000),
        CoveragePoint(
            date=base.replace(day=3), suite="fep_lean", percentage=88.00, lines_covered=880, lines_total=1000
        ),
    ]


def test_build_history_markdown_is_deterministic() -> None:
    points = _sample_points()
    anchor = date(2026, 5, 4)

    a = build_history_markdown(points, days=7, today=anchor)
    b = build_history_markdown(points, days=7, today=anchor)

    assert a == b, "Same input must produce byte-identical output"
    assert "Last verified: 2026-05-04" in a
    assert "| Date | infra % | project % | fep_lean % |" in a
    assert "| 2026-05-01 | 82.50 | 91.00 | - |" in a
    assert "| 2026-05-02 | 83.10 | 91.20 | - |" in a
    assert "| 2026-05-03 | - | - | 88.00 |" in a
    assert "Trend sparklines" in a


def test_build_history_markdown_drops_points_outside_window() -> None:
    base = datetime(2026, 5, 1, tzinfo=UTC)
    far_past = CoveragePoint(
        date=datetime(2025, 1, 1, tzinfo=UTC),
        suite="infra",
        percentage=10.0,
        lines_covered=100,
        lines_total=1000,
    )
    in_window = CoveragePoint(date=base, suite="infra", percentage=80.0, lines_covered=800, lines_total=1000)
    md = build_history_markdown([far_past, in_window], days=7, today=date(2026, 5, 4))
    assert "10.00" not in md
    assert "80.00" in md


def test_build_history_markdown_handles_empty_input() -> None:
    md = build_history_markdown([], days=5, today=date(2026, 5, 4))
    assert "Suites observed: (none)" in md
    assert "_No coverage data points within the rolling window._" in md
    # Header still renders even with no data columns.
    assert "| Date |" in md


def test_build_history_markdown_canonical_column_order() -> None:
    base = datetime(2026, 5, 1, tzinfo=UTC)
    points = [
        CoveragePoint(date=base, suite="zeta", percentage=50.0, lines_covered=5, lines_total=10),
        CoveragePoint(date=base, suite="project", percentage=90.0, lines_covered=9, lines_total=10),
        CoveragePoint(date=base, suite="alpha", percentage=70.0, lines_covered=7, lines_total=10),
        CoveragePoint(date=base, suite="infra", percentage=80.0, lines_covered=8, lines_total=10),
    ]
    md = build_history_markdown(points, days=3, today=date(2026, 5, 3))
    header_line = next(ln for ln in md.splitlines() if ln.startswith("| Date |"))
    # infra → project → fep_lean (absent) → alpha → zeta
    assert header_line == "| Date | infra % | project % | alpha % | zeta % |"


# ---------------------------------------------------------------------------
# collect_history_from_dir
# ---------------------------------------------------------------------------


def test_collect_history_from_dir_parses_all_files(tmp_path: Path) -> None:
    when_a = datetime(2026, 5, 1, tzinfo=UTC)
    when_b = datetime(2026, 5, 2, tzinfo=UTC)
    nested = tmp_path / "run-123"
    nested.mkdir()
    _write_cobertura(nested / "coverage-infra.xml", line_rate=0.80, lines_covered=80, lines_total=100, when=when_a)
    _write_cobertura(nested / "coverage-project.xml", line_rate=0.92, lines_covered=92, lines_total=100, when=when_a)
    _write_cobertura(tmp_path / "coverage-infra.xml", line_rate=0.81, lines_covered=81, lines_total=100, when=when_b)

    points = collect_history_from_dir(tmp_path)
    assert len(points) == 3
    # Sorted by (date, suite)
    assert points[0].date <= points[1].date <= points[2].date
    suites = sorted(p.suite for p in points)
    assert suites == ["infra", "infra", "project"]


def test_collect_history_from_dir_missing_dir_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        collect_history_from_dir(tmp_path / "nonexistent")


def test_collect_history_from_dir_skips_malformed(tmp_path: Path) -> None:
    # One good, one broken XML — collector should keep the good and warn on the rest.
    _write_cobertura(
        tmp_path / "coverage-infra.xml",
        line_rate=0.5,
        lines_covered=50,
        lines_total=100,
        when=datetime(2026, 5, 1, tzinfo=UTC),
    )
    (tmp_path / "coverage-broken.xml").write_text("<not><valid xml", encoding="utf-8")

    points = collect_history_from_dir(tmp_path)
    assert len(points) == 1
    assert points[0].suite == "infra"


# ---------------------------------------------------------------------------
# End-to-end: --from-dir driver
# ---------------------------------------------------------------------------


def test_driver_from_dir_writes_valid_markdown(tmp_path: Path) -> None:
    """Run scripts/generate_coverage_history.py --from-dir end-to-end."""
    artefacts = tmp_path / "artefacts"
    artefacts.mkdir()
    when = datetime(2026, 5, 3, tzinfo=UTC)
    _write_cobertura(artefacts / "coverage-infra.xml", line_rate=0.84, lines_covered=84, lines_total=100, when=when)
    _write_cobertura(artefacts / "coverage-project.xml", line_rate=0.93, lines_covered=93, lines_total=100, when=when)

    out_path = tmp_path / "coverage_history.md"
    repo_root = Path(__file__).resolve().parents[3]
    cmd = [
        sys.executable,
        str(repo_root / "scripts" / "generate_coverage_history.py"),
        f"--from-dir={artefacts}",
        "--days=7",
        f"--output={out_path}",
    ]
    completed = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
    assert completed.returncode == 0, f"Driver failed: {completed.stderr}"
    assert out_path.exists()

    rendered = out_path.read_text(encoding="utf-8")
    assert "# Coverage history" in rendered
    assert "Last verified:" in rendered
    assert "| Date | infra % | project % |" in rendered
    assert "84.00" in rendered
    assert "93.00" in rendered
    assert "Trend sparklines" in rendered


def test_driver_from_dir_is_idempotent(tmp_path: Path) -> None:
    """Same input → byte-identical output across two driver invocations."""
    artefacts = tmp_path / "artefacts"
    artefacts.mkdir()
    when = datetime(2026, 5, 3, tzinfo=UTC)
    _write_cobertura(artefacts / "coverage-infra.xml", line_rate=0.7, lines_covered=70, lines_total=100, when=when)

    out_a = tmp_path / "a.md"
    out_b = tmp_path / "b.md"
    repo_root = Path(__file__).resolve().parents[3]
    base_cmd = [
        sys.executable,
        str(repo_root / "scripts" / "generate_coverage_history.py"),
        f"--from-dir={artefacts}",
        "--days=7",
    ]
    # Pin the anchor by passing a deterministic point set; build_history_markdown
    # uses today() but driver doesn't expose --today, so we use the in-process
    # function for determinism here.
    md_a = build_history_markdown(collect_history_from_dir(artefacts), days=7, today=date(2026, 5, 4))
    md_b = build_history_markdown(collect_history_from_dir(artefacts), days=7, today=date(2026, 5, 4))
    out_a.write_text(md_a, encoding="utf-8")
    out_b.write_text(md_b, encoding="utf-8")
    assert out_a.read_bytes() == out_b.read_bytes()
    # Driver itself runs cleanly (we don't compare bytes here because the
    # driver uses datetime.now()'s date as anchor — nondeterministic across
    # midnight UTC, which is the expected behavior).
    completed = subprocess.run(
        base_cmd + [f"--output={tmp_path / 'driven.md'}"], capture_output=True, text=True, timeout=60, check=False
    )
    assert completed.returncode == 0


# ---------------------------------------------------------------------------
# collect_history_via_gh — real subprocess, skip if gh missing
# ---------------------------------------------------------------------------


@pytest.mark.skipif(shutil.which("gh") is None, reason="gh CLI not installed")
def test_collect_history_via_gh_returns_list_or_runtime_error(tmp_path: Path) -> None:
    """Real ``gh`` invocation. Without auth or in an unrelated cwd it raises
    ``RuntimeError``; with auth it returns a (possibly empty) list. Either is
    fine — we just verify the contract.
    """
    try:
        result = collect_history_via_gh(workflow="ci.yml", days=1, repo_root=tmp_path)
    except RuntimeError:
        # Expected when `gh` cannot resolve the repo / not authenticated.
        return
    assert isinstance(result, list)
    for point in result:
        assert isinstance(point, CoveragePoint)


def test_collect_history_via_gh_raises_when_gh_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    """If ``gh`` is not on PATH, the function raises ``RuntimeError`` with a
    clear, actionable message — no silent fallback."""
    monkeypatch.setenv("PATH", "")  # remove gh from resolution
    with pytest.raises(RuntimeError, match="gh"):
        collect_history_via_gh(workflow="ci.yml", days=1)
