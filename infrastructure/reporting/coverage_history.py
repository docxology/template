"""Coverage trend dashboard generator (MED3).

Parses Cobertura-style ``coverage-*.xml`` files (the output of
``pytest --cov --cov-report=xml`` and what Codecov ingests), aggregates
per-suite percentages, and renders a deterministic Markdown report that
shows a rolling N-day window with ASCII sparklines per suite.

The module exposes three pure functions and one I/O-driven collector:

- :func:`parse_coverage_xml` — single-file XML → :class:`CoveragePoint`.
- :func:`build_history_markdown` — list of points → final Markdown string.
- :func:`collect_history_via_gh` — real ``gh run list`` + ``gh run download``
  invocations (no mocks; raises ``RuntimeError`` if the CLI is missing).

Two driver modes are supported by the orchestrator script
``scripts/generate_coverage_history.py``:

* ``--from-dir=PATH`` — read every ``coverage-*.xml`` under ``PATH``.
* ``--from-gh`` — call :func:`collect_history_via_gh` (requires the GitHub
  CLI to be installed and authenticated).

Determinism: given the same input set, ``build_history_markdown`` produces
byte-identical output. We sort points by ``(date, suite)`` and format
floats with a fixed precision so commits stay diff-friendly.

Security: XML parsing uses :mod:`defusedxml.ElementTree` (bandit B314
fires on stdlib :mod:`xml.etree`). Subprocess calls use ``shell=False``
and a list-form argv.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Sequence

import defusedxml.ElementTree as ET

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Public data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CoveragePoint:
    """A single coverage measurement for one suite at a specific timestamp.

    Attributes:
        date: Timestamp of the underlying CI run (UTC, tz-aware).
        suite: Logical suite name — ``"infra"``, ``"project"``, or
            ``"fep_lean"``. Anything else passes through verbatim.
        percentage: Coverage in ``[0.0, 100.0]`` (Cobertura ``line-rate`` × 100).
        lines_covered: Total covered lines reported by Cobertura.
        lines_total: Total considered lines reported by Cobertura.
    """

    date: datetime
    suite: str
    percentage: float
    lines_covered: int
    lines_total: int


# ---------------------------------------------------------------------------
# XML parsing
# ---------------------------------------------------------------------------

# ``coverage-{suite}.xml`` is the convention used by ``ci.yml`` (e.g.
# ``coverage-infra.xml``, ``coverage-project.xml``). We accept any
# alphanumeric / underscore suffix.
_SUITE_FROM_FILENAME = re.compile(r"^coverage-(?P<suite>[a-zA-Z0-9_]+)\.xml$")


def _suite_from_filename(path: Path) -> str:
    """Infer the suite name from ``coverage-<suite>.xml`` style filenames.

    Falls back to the file stem if the name doesn't match the convention,
    so this never raises on unrecognised inputs.
    """
    match = _SUITE_FROM_FILENAME.match(path.name)
    if match:
        return match.group("suite")
    return path.stem


def _parse_timestamp(raw: str | None) -> datetime:
    """Parse Cobertura's ``timestamp`` attribute (Unix epoch in milliseconds).

    Falls back to ``datetime.now(UTC)`` if the attribute is missing or
    unparseable — we'd rather emit an approximate point than skip data.
    """
    if not raw:
        return datetime.now(UTC)
    try:
        # Cobertura ships milliseconds; ``coverage.py`` uses milliseconds too.
        epoch_ms = int(raw)
        return datetime.fromtimestamp(epoch_ms / 1000.0, tz=UTC)
    except (ValueError, TypeError, OSError):
        # Some toolchains write seconds instead of milliseconds; try that next.
        try:
            return datetime.fromtimestamp(float(raw), tz=UTC)
        except (ValueError, TypeError, OSError):
            logger.warning("Coverage XML at unparseable timestamp %r; using now()", raw)
            return datetime.now(UTC)


def parse_coverage_xml(path: Path) -> CoveragePoint:
    """Parse a Cobertura-style ``coverage-*.xml`` file into a :class:`CoveragePoint`.

    Args:
        path: Path to a Cobertura XML file produced by ``pytest --cov-report=xml``.

    Returns:
        A frozen :class:`CoveragePoint`.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
        ValueError: If the root element is not ``<coverage>`` (i.e. not Cobertura).
    """
    if not path.exists():
        raise FileNotFoundError(f"Coverage XML not found: {path}")

    tree = ET.parse(str(path))
    root = tree.getroot()
    if root.tag != "coverage":
        raise ValueError(f"Expected <coverage> root, got <{root.tag}> in {path}")

    line_rate = float(root.attrib.get("line-rate", "0") or "0")
    lines_covered = int(root.attrib.get("lines-covered", "0") or "0")
    lines_total = int(root.attrib.get("lines-valid", "0") or "0")

    suite_attr = root.attrib.get("suite")
    suite = suite_attr if suite_attr else _suite_from_filename(path)

    return CoveragePoint(
        date=_parse_timestamp(root.attrib.get("timestamp")),
        suite=suite,
        percentage=line_rate * 100.0,
        lines_covered=lines_covered,
        lines_total=lines_total,
    )


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

_SPARKLINE_BLOCKS = "▁▂▃▄▅▆▇█"


def _sparkline(values: Sequence[float]) -> str:
    """Render a Unicode block-character sparkline of ``values``.

    Empty / single-value inputs return ``"-"`` so the table cell still
    aligns. Constant series render as a flat bottom row.
    """
    if not values:
        return "-"
    lo = min(values)
    hi = max(values)
    if hi - lo < 1e-9:
        return _SPARKLINE_BLOCKS[0] * len(values)
    span = hi - lo
    chars: list[str] = []
    bucket_count = len(_SPARKLINE_BLOCKS) - 1
    for v in values:
        # Map [lo, hi] linearly onto block character indices.
        idx = int(round((v - lo) / span * bucket_count))
        chars.append(_SPARKLINE_BLOCKS[max(0, min(bucket_count, idx))])
    return "".join(chars)


def _format_pct(value: float | None) -> str:
    """Format a percentage cell. ``None`` collapses to ``-`` for readability."""
    if value is None:
        return "-"
    return f"{value:.2f}"


def _bucket_by_day(points: Sequence[CoveragePoint]) -> dict[date, dict[str, float]]:
    """Group points by UTC date → suite → percentage (latest wins per day)."""
    by_day: dict[date, dict[str, float]] = {}
    # Sort so that "latest wins" is deterministic.
    for pt in sorted(points, key=lambda p: (p.date, p.suite)):
        day = pt.date.astimezone(UTC).date()
        by_day.setdefault(day, {})[pt.suite] = pt.percentage
    return by_day


def build_history_markdown(
    points: Sequence[CoveragePoint],
    *,
    days: int = 30,
    today: date | None = None,
) -> str:
    """Render a deterministic Markdown coverage-history report.

    Args:
        points: Coverage measurements to plot. May span any time range —
            anything outside the rolling window is dropped.
        days: Width of the rolling window in days (default 30).
        today: Override the "today" anchor — used by tests to pin output.
            Defaults to the current UTC date.

    Returns:
        A Markdown document string. The function is pure and idempotent:
        calling it twice with identical inputs returns identical output.
    """
    anchor = today if today is not None else datetime.now(UTC).date()
    cutoff = anchor - timedelta(days=days - 1)

    # Filter to window + bucket per day.
    in_window = [p for p in points if cutoff <= p.date.astimezone(UTC).date() <= anchor]
    by_day = _bucket_by_day(in_window)

    # Discover which suites appear, then stabilise their order:
    # canonical suites first (infra → project → fep_lean), then any extras
    # alphabetically. Keeps the table column order deterministic across runs.
    canonical_order = ["infra", "project", "fep_lean"]
    seen = {p.suite for p in in_window}
    suites: list[str] = [s for s in canonical_order if s in seen]
    suites.extend(sorted(s for s in seen if s not in canonical_order))

    # Build the table rows oldest-first.
    header_cells = ["Date"] + [f"{s} %" for s in suites]
    sep_cells = ["---"] * len(header_cells)
    table_lines: list[str] = [
        "| " + " | ".join(header_cells) + " |",
        "| " + " | ".join(sep_cells) + " |",
    ]
    for offset in range(days):
        d = cutoff + timedelta(days=offset)
        row = by_day.get(d, {})
        cells = [d.isoformat()] + [_format_pct(row.get(s)) for s in suites]
        table_lines.append("| " + " | ".join(cells) + " |")

    # Sparkline per suite (chronological, missing days skipped).
    spark_lines: list[str] = []
    for suite in suites:
        series = [
            by_day[d][suite]
            for offset in range(days)
            for d in [cutoff + timedelta(days=offset)]
            if d in by_day and suite in by_day[d]
        ]
        spark_lines.append(f"- `{suite:<10}`  {_sparkline(series)}  (n={len(series)})")

    if not suites:
        spark_lines.append("- _No coverage data points within the rolling window._")

    document = [
        "# Coverage history",
        "",
        "This file is **generated** by",
        "`scripts/generate_coverage_history.py`. Do not edit by hand.",
        "",
        f"Last verified: {anchor.isoformat()}",
        f"Rolling window: {days} day(s) — {cutoff.isoformat()} → {anchor.isoformat()}",
        f"Suites observed: {', '.join(suites) if suites else '(none)'}",
        "",
        "## Daily coverage table",
        "",
        *table_lines,
        "",
        "## Trend sparklines",
        "",
        *spark_lines,
        "",
        "## Regenerate",
        "",
        "```bash",
        "uv run python scripts/generate_coverage_history.py --from-dir=<dir>",
        "# or, with `gh` authenticated:",
        "uv run python scripts/generate_coverage_history.py --from-gh --days=30",
        "```",
        "",
    ]
    return "\n".join(document)


# ---------------------------------------------------------------------------
# GitHub CLI collector (real subprocess, zero mocks)
# ---------------------------------------------------------------------------


def _require_gh_cli() -> str:
    """Return the resolved path of ``gh`` or raise a clear error."""
    resolved = shutil.which("gh")
    if not resolved:
        raise RuntimeError(
            "`gh` CLI not found on PATH. Install from https://cli.github.com/ "
            "and authenticate (`gh auth login`) to use --from-gh."
        )
    return resolved


def _run_gh(argv: list[str], *, cwd: Path | None = None, timeout: int = 60) -> str:
    """Execute ``gh`` with a list-form argv (``shell=False``). Returns stdout text."""
    gh = _require_gh_cli()
    cmd = [gh, *argv]
    logger.debug("Running %s", " ".join(cmd))
    completed = subprocess.run(  # noqa: S603 — argv is list-form, gh resolved via which
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"`gh {' '.join(argv)}` exited {completed.returncode}: "
            f"{completed.stderr.strip() or completed.stdout.strip()}"
        )
    return completed.stdout


def collect_history_via_gh(
    workflow: str = "ci.yml",
    *,
    days: int = 30,
    repo_root: Path | None = None,
) -> list[CoveragePoint]:
    """Collect coverage points from the last ``days`` of CI artefacts via ``gh``.

    For each successful run of ``workflow`` in the window, this:

    1. Runs ``gh run list --workflow=<workflow> --limit=<heuristic> --json …``.
    2. Filters runs by ``createdAt`` against the ``days`` window.
    3. For each in-window run, calls
       ``gh run download <run-id> --pattern 'coverage-*.xml' --dir <tmp>``.
    4. Parses every file found via :func:`parse_coverage_xml`.

    The function never mocks: it really shells out. If ``gh`` is missing,
    not authenticated, or rate-limited, ``RuntimeError`` is raised — let
    the caller decide whether to fall back.

    Args:
        workflow: GitHub Actions workflow file name (default ``ci.yml``).
        days: Rolling window in days (default 30).
        repo_root: Optional working directory; ``gh`` will resolve the
            repo from the cwd's git remote.

    Returns:
        Coverage points sorted by ``(date, suite)``.
    """
    _require_gh_cli()
    cutoff = datetime.now(UTC) - timedelta(days=days)
    # Heuristic limit: assume ≤8 successful runs per day, capped at 250 (gh max).
    limit = min(250, max(20, days * 8))

    # JSON output keeps parsing trivial and avoids fragile column scraping.
    listing = _run_gh(
        [
            "run",
            "list",
            f"--workflow={workflow}",
            f"--limit={limit}",
            "--json",
            "databaseId,createdAt,conclusion,status",
        ],
        cwd=repo_root,
        timeout=60,
    )

    import json as _json  # local import keeps the module top clean

    try:
        runs = _json.loads(listing)
    except _json.JSONDecodeError as exc:
        raise RuntimeError(f"Could not parse `gh run list` JSON output: {exc}") from exc

    points: list[CoveragePoint] = []
    with tempfile.TemporaryDirectory(prefix="coverage-history-") as tmp:
        tmp_path = Path(tmp)
        for run in runs:
            created_at = str(run.get("createdAt", ""))
            try:
                created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except ValueError:
                continue
            if created < cutoff:
                continue
            if str(run.get("conclusion") or "") != "success":
                continue

            run_id = str(run.get("databaseId") or "")
            if not run_id:
                continue

            run_dir = tmp_path / run_id
            run_dir.mkdir(parents=True, exist_ok=True)
            try:
                _run_gh(
                    [
                        "run",
                        "download",
                        run_id,
                        "--pattern",
                        "coverage-*.xml",
                        "--dir",
                        str(run_dir),
                    ],
                    cwd=repo_root,
                    timeout=120,
                )
            except RuntimeError as exc:
                logger.warning("gh run download %s failed: %s", run_id, exc)
                continue

            for xml_path in sorted(run_dir.rglob("coverage-*.xml")):
                try:
                    points.append(parse_coverage_xml(xml_path))
                except (ValueError, FileNotFoundError, ET.ParseError) as exc:
                    logger.warning("Skipping malformed coverage XML %s: %s", xml_path, exc)

    points.sort(key=lambda p: (p.date, p.suite))
    return points


# ---------------------------------------------------------------------------
# Directory-mode collector (offline, used by the CI artifact step)
# ---------------------------------------------------------------------------


def collect_history_from_dir(directory: Path) -> list[CoveragePoint]:
    """Recursively parse every ``coverage-*.xml`` under ``directory``.

    Sorted by ``(date, suite)`` for deterministic downstream output.
    """
    if not directory.exists():
        raise FileNotFoundError(f"Coverage directory not found: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")

    points: list[CoveragePoint] = []
    for xml_path in sorted(directory.rglob("coverage-*.xml")):
        try:
            points.append(parse_coverage_xml(xml_path))
        except (ValueError, FileNotFoundError, ET.ParseError) as exc:
            logger.warning("Skipping malformed coverage XML %s: %s", xml_path, exc)
    points.sort(key=lambda p: (p.date, p.suite))
    return points


__all__ = [
    "CoveragePoint",
    "build_history_markdown",
    "collect_history_from_dir",
    "collect_history_via_gh",
    "parse_coverage_xml",
]
