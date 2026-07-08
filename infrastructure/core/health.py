#!/usr/bin/env python3
"""Unified repository health check command.

This module wires together every quality gate that lives behind its own
CLI today (mypy, ruff, ruff format, bandit, the no-mocks verifier, the
``__all__`` audit, the docs linter, and the doc-generator idempotence
checks) into a single entry point.  It is a *thin orchestrator* — each
gate is invoked as a subprocess against the live tree, and the gate's
**exit code** is the only source of truth for pass/fail.  Stdout and
stderr are captured for diagnostic purposes only.

CLI:

    uv run python -m infrastructure.core.health
    uv run python -m infrastructure.core.health --json
    uv run python -m infrastructure.core.health --gates=ruff,mypy
    uv run python -m infrastructure.core.health --quiet
    uv run python -m infrastructure.core.health --repo-root=/path/to/repo

Programmatic:

    from infrastructure.core.health import run_health_checks
    report = run_health_checks(Path("."))
    assert report.passed

The module deliberately avoids new third-party dependencies: the colored
table uses bare ANSI escape codes, falling back to plain text when stdout
is not a TTY.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

from infrastructure.project.public_scope import public_ci_source_paths

__all__ = [
    "GateResult",
    "HealthReport",
    "GATE_NAMES",
    "build_gate_specs",
    "run_health_checks",
    "format_report_table",
    "main",
]

# ---------------------------------------------------------------------------
# Public dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GateResult:
    """Outcome of a single quality gate.

    Attributes:
        name: Short canonical gate identifier (e.g. ``"mypy"``).
        passed: ``True`` iff the underlying subprocess exited 0.
        elapsed_ms: Wall-clock duration in milliseconds.
        output: Short tail of combined stdout/stderr captured for
            diagnostics. Never used to decide pass/fail.
    """

    name: str
    passed: bool
    elapsed_ms: float
    output: str


@dataclass(frozen=True)
class HealthReport:
    """Aggregate outcome of running a (sub)set of quality gates.

    Attributes:
        results: Per-gate results in execution order.
        passed: ``True`` iff every gate in ``results`` passed.
        total_elapsed_ms: Sum of per-gate ``elapsed_ms`` values.
    """

    results: list[GateResult]
    passed: bool
    total_elapsed_ms: float


# ---------------------------------------------------------------------------
# Gate registry
# ---------------------------------------------------------------------------

# Tail of captured combined stdout/stderr stored in ``GateResult.output``
# for diagnostics. Sized to keep JSON reports compact while still being
# useful for triage.
_OUTPUT_TAIL_BYTES = 4000
_GATE_TIMEOUT_SECONDS = 300.0


def _public_source_targets(repo_root: Path) -> list[str]:
    """Return public CI source paths for linting and type checks."""
    return [path.as_posix() for path in public_ci_source_paths(repo_root)]


def build_gate_specs(repo_root: Path) -> list[tuple[str, list[str]]]:
    """Return the canonical ``(name, argv)`` list for every gate.

    The list is parameterised on ``repo_root`` so callers can run health
    checks against any checkout (the live tree, a temp clone, a CI
    workspace, etc.). The architecture-overview gate falls back to a
    presence check on the generated SVG when no CLI is available.

    Args:
        repo_root: Repository root used to resolve relative paths in the
            invoked commands.

    Returns:
        Ordered list of ``(gate_name, argv)`` tuples.
    """

    arch_svg = repo_root / "docs" / "_generated" / "architecture_overview.svg"
    # The architecture overview module currently has no CLI ``__main__``;
    # fall back to a portable presence check via the standard library so
    # the gate is still meaningful on a clean tree.
    arch_overview_argv = [
        sys.executable,
        "-c",
        (
            "import sys, pathlib;"
            f" p = pathlib.Path({str(arch_svg)!r});"
            " sys.exit(0 if p.is_file() and p.stat().st_size > 0 else 1)"
        ),
    ]

    public_targets = _public_source_targets(repo_root)

    return [
        ("mypy", ["uv", "run", "python", "-m", "mypy", *public_targets]),
        (
            "ruff",
            ["uvx", "ruff", "check", *public_targets],
        ),
        (
            "ruff-format",
            ["uvx", "ruff", "format", "--check", *public_targets],
        ),
        (
            "bandit",
            [
                "uv",
                "run",
                "python",
                "-m",
                "bandit",
                "-r",
                "-ll",
                "-c",
                "bandit.yaml",
                "infrastructure/",
                "scripts/",
                "--exclude",
                "projects/working,projects/ongoing,projects/published,projects/archive,projects/other",
            ],
        ),
        (
            "no-mocks",
            ["uv", "run", "python", "scripts/audit/verify_no_mocks.py"],
        ),
        (
            "all-exports",
            [
                "uv",
                "run",
                "python",
                "-m",
                "infrastructure.skills",
                "check-all-exports",
            ],
        ),
        (
            "docs-lint",
            ["uv", "run", "python", "scripts/audit/lint_docs.py", "--quiet"],
        ),
        (
            "stage-table",
            [
                "uv",
                "run",
                "python",
                "scripts/docgen/stage_table.py",
            ],
        ),
        (
            "api-reference",
            [
                "uv",
                "run",
                "python",
                "scripts/docgen/api_reference.py",
                "--check",
            ],
        ),
        ("architecture-overview", arch_overview_argv),
        (
            "module-line-count",
            [
                "uv",
                "run",
                "python",
                "scripts/gates/module_line_count_check.py",
            ],
        ),
    ]


# Canonical, stable list of gate names (used by ``--gates`` parsing and
# tests). Generated once at import time from a sentinel ``Path(".")`` —
# the names do not depend on the repo root.
GATE_NAMES: tuple[str, ...] = tuple(name for name, _ in build_gate_specs(Path(".")))

# ---------------------------------------------------------------------------
# Special-case post-processing
# ---------------------------------------------------------------------------


def _stage_table_passed(returncode: int, combined_output: str) -> bool:
    """Decide whether the stage-table gate passed.

    ``scripts/docgen/stage_table.py`` is idempotent: it exits 0 in
    both ``no-op`` and ``would-update`` cases. For health-check purposes
    the gate must fail when the script reports any pending updates, so
    we scan its output for drift — but ``Would update 0`` is the
    idempotent success summary and must NOT trigger a failure.
    """

    if returncode != 0:
        return False
    # "Would update N" with N > 0 signals real drift. "Would update 0" is the
    # success-with-summary path.
    drift_re = re.compile(r"Would update (\d+)", re.IGNORECASE)
    for match in drift_re.finditer(combined_output):
        if int(match.group(1)) > 0:
            return False
    # Active mutation markers always signal drift.
    if "Updating " in combined_output:
        return False
    return True


# Map of gate-name → custom pass predicate. Anything not listed here
# defers to ``returncode == 0``.
_CUSTOM_PASS_PREDICATES = {
    "stage-table": _stage_table_passed,
}

# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------


def _run_single_gate(
    name: str,
    argv: Sequence[str],
    repo_root: Path,
    *,
    timeout_seconds: float = _GATE_TIMEOUT_SECONDS,
) -> GateResult:
    """Execute one gate and capture its outcome."""

    start = time.perf_counter()
    try:
        proc = subprocess.run(  # noqa: S603 — argv list, no shell.
            list(argv),
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
        combined = (proc.stdout or "") + (proc.stderr or "")
        predicate = _CUSTOM_PASS_PREDICATES.get(name)
        if predicate is not None:
            passed = predicate(proc.returncode, combined)
        else:
            passed = proc.returncode == 0
        tail = combined[-_OUTPUT_TAIL_BYTES:].rstrip()
    except FileNotFoundError as exc:
        passed = False
        tail = f"executable not found: {exc}"
    except subprocess.TimeoutExpired as exc:
        passed = False
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode(errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode(errors="replace")
        combined = str(stdout) + str(stderr)
        output_tail = combined[-_OUTPUT_TAIL_BYTES:].rstrip()
        tail = f"gate timed out after {timeout_seconds:g}s"
        if output_tail:
            tail = f"{tail}\n{output_tail}"
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    return GateResult(name=name, passed=passed, elapsed_ms=elapsed_ms, output=tail)


def run_health_checks(
    repo_root: Path,
    *,
    gates: Sequence[str] | None = None,
    json_output: bool = False,
) -> HealthReport:
    """Run every configured gate (or a subset) and aggregate results.

    Args:
        repo_root: Repository root the gates should run against. Each
            subprocess is launched with ``cwd=repo_root``.
        gates: Optional subset of gate names to run. ``None`` runs every
            gate in :data:`GATE_NAMES`. Unknown names raise ``ValueError``.
        json_output: Reserved for symmetry with the CLI; the report is
            always returned as a typed object regardless.

    Returns:
        :class:`HealthReport` aggregating per-gate results.
    """

    del json_output  # CLI-only; the dataclass is the canonical artefact.
    specs = build_gate_specs(repo_root)
    if gates is not None:
        wanted = list(gates)
        known = {name for name, _ in specs}
        unknown = [name for name in wanted if name not in known]
        if unknown:
            raise ValueError(f"unknown gate(s): {', '.join(sorted(unknown))}; valid gates: {', '.join(GATE_NAMES)}")
            # ``valid`` only matters for the error message; preserve the
            # caller-supplied order otherwise.
        order = {name: idx for idx, name in enumerate(wanted)}
        specs = sorted(
            (spec for spec in specs if spec[0] in order),
            key=lambda spec: order[spec[0]],
        )

    results: list[GateResult] = []
    for name, argv in specs:
        results.append(_run_single_gate(name, argv, repo_root))

    total_ms = sum(r.elapsed_ms for r in results)
    overall = all(r.passed for r in results) if results else True
    return HealthReport(results=results, passed=overall, total_elapsed_ms=total_ms)


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

_ANSI_RESET = "\033[0m"
_ANSI_GREEN = "\033[32m"
_ANSI_RED = "\033[31m"
_ANSI_BOLD = "\033[1m"
_ANSI_DIM = "\033[2m"


def _supports_color(stream: object) -> bool:
    """Return ``True`` iff ``stream`` looks like a colour-capable TTY.

    Honours the de-facto ``NO_COLOR`` environment variable and the
    ``PY_COLORS`` opt-in used by pytest/CI.
    """

    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("PY_COLORS") == "1":
        return True
    isatty = getattr(stream, "isatty", None)
    return bool(callable(isatty) and isatty())


def format_report_table(report: HealthReport, *, color: bool = True) -> str:
    """Render ``report`` as a single colored ASCII table.

    Args:
        report: The aggregate report to render.
        color: When ``True``, embed ANSI escape codes for status. Disable
            for log files, CI artefacts, or pipes.

    Returns:
        Multi-line string suitable for printing directly.
    """

    def colorize(text: str, code: str) -> str:
        """Wrap text with ANSI color codes for terminal output."""
        return f"{code}{text}{_ANSI_RESET}" if color else text

    rows: list[tuple[str, str, str]] = []
    name_width = max((len(r.name) for r in report.results), default=8)
    name_width = max(name_width, len("Gate"))

    for result in report.results:
        status = "PASS" if result.passed else "FAIL"
        status_colored = colorize(status, _ANSI_GREEN if result.passed else _ANSI_RED)
        elapsed = f"{result.elapsed_ms / 1000.0:6.2f}s"
        rows.append((result.name, status_colored, elapsed))

    header_name = colorize("Gate".ljust(name_width), _ANSI_BOLD)
    header_status = colorize("Status".ljust(6), _ANSI_BOLD)
    header_elapsed = colorize("Elapsed", _ANSI_BOLD)
    sep = colorize("─" * (name_width + 6 + 8 + 4), _ANSI_DIM)

    lines = [
        f"{header_name}  {header_status}  {header_elapsed}",
        sep,
    ]
    for name, status, elapsed in rows:
        lines.append(f"{name.ljust(name_width)}  {status.ljust(6 + (len(status) - 4))}  {elapsed}")
    lines.append(sep)
    overall = "PASS" if report.passed else "FAIL"
    overall_colored = colorize(overall, _ANSI_GREEN if report.passed else _ANSI_RED)
    total_s = report.total_elapsed_ms / 1000.0
    lines.append(f"Overall: {overall_colored}  ({total_s:.2f}s total, {len(report.results)} gates)")
    return "\n".join(lines)


def _report_to_dict(report: HealthReport) -> dict[str, object]:
    """Convert ``HealthReport`` to a JSON-serialisable dict."""

    return {
        "passed": report.passed,
        "total_elapsed_ms": report.total_elapsed_ms,
        "results": [asdict(r) for r in report.results],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m infrastructure.core.health",
        description=(
            "Run every repository quality gate and print a colored status table. Exit code is 0 iff every gate passes."
        ),
    )
    parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Emit the report as JSON instead of a colored table.",
    )
    parser.add_argument(
        "--gates",
        type=str,
        default=None,
        help=(f"Comma-separated subset of gate names to run (choices: {', '.join(GATE_NAMES)})."),
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the human-readable table (useful with --json).",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root (default: current working directory).",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colour even when stdout is a TTY.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for ``python -m infrastructure.core.health``."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    repo_root = (args.repo_root or Path.cwd()).resolve()
    gates: list[str] | None = None
    if args.gates:
        gates = [g.strip() for g in args.gates.split(",") if g.strip()]

    try:
        report = run_health_checks(repo_root, gates=gates)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json_output:
        json.dump(_report_to_dict(report), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    if not args.quiet and not args.json_output:
        color = _supports_color(sys.stdout) and not args.no_color
        print(format_report_table(report, color=color))
        # Surface captured diagnostics for every failing gate, so a FAIL row is
        # actionable instead of an opaque "FAIL 0.03s" (a gate that fails to
        # spawn, times out, or reports real errors all print their tail here).
        for result in report.results:
            if not result.passed and result.output:
                print(f"\n── {result.name} ──\n{result.output}", file=sys.stderr)

    return 0 if report.passed else 1


if __name__ == "__main__":  # pragma: no cover — exercised via subprocess in tests.
    raise SystemExit(main())
