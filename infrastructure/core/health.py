#!/usr/bin/env python3
"""Blocking static repository health check command.

This module wires together the repository's deterministic static quality
gates. Platform matrices, behavioral test suites, and coverage remain separate
CI jobs. It is a *thin orchestrator* — each
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
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

from infrastructure.core.health_gates import build_gate_specs

__all__ = [
    "GateResult",
    "HealthReport",
    "GATE_NAMES",
    "build_gate_specs",
    "gate_spec_sha256",
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
        total_elapsed_ms: Sum of per-gate ``elapsed_ms`` values. This is useful
            for capacity profiling but is not the user-visible wall time when
            gates run concurrently.
        wall_elapsed_ms: Wall-clock duration for the complete sweep.
    """

    results: list[GateResult]
    passed: bool
    total_elapsed_ms: float
    wall_elapsed_ms: float
    schema_version: int = 1
    workers: int = 1
    repo_commit: str | None = None
    clean_checkout: bool | None = None
    gate_spec_sha256: str = ""


# ---------------------------------------------------------------------------
# Gate registry
# ---------------------------------------------------------------------------

# Tail of captured combined stdout/stderr stored in ``GateResult.output``
# for diagnostics. Sized to keep JSON reports compact while still being
# useful for triage.
_OUTPUT_TAIL_BYTES = 4000
_GATE_TIMEOUT_SECONDS = 300.0

# Per-gate timeout overrides (seconds). Gates whose runtime legitimately
# exceeds the default ceiling — because they re-derive measured facts from
# every public exemplar via per-project pytest collection subprocesses — get
# an explicit, documented budget instead of failing spuriously on slower or
# loaded machines. Every value here must remain a hard ceiling: the gate is
# still expected to finish, only with more headroom than the 300s default.
_GATE_TIMEOUT_OVERRIDES: dict[str, float] = {
    # ``counts.py --check`` collects each public exemplar serially in its own
    # declared environment; observed wall time exceeds 20 minutes locally.
    "counts": 1800.0,
    # ``lint_docs.py`` renders every discovered Mermaid block (268+ as of
    # 2026-08) through real headless-Chrome subprocesses; observed local wall
    # time exceeds the 300s default on loaded machines.
    "docs-lint": 900.0,
    # ``bandit`` scans every infrastructure/script/public-exemplar source
    # file; observed local wall time on a loaded workstation exceeds 10
    # minutes (12 min measured 2026-08-21).
    "bandit": 1200.0,
}


def _gate_timeout_seconds(name: str) -> float:
    """Return the effective timeout for *name*, honouring the env override."""
    override = os.environ.get("TEMPLATE_HEALTH_GATE_TIMEOUT")
    if override:
        try:
            parsed = float(override)
        except ValueError as exc:
            raise ValueError(
                f"Invalid TEMPLATE_HEALTH_GATE_TIMEOUT value {override!r}: expected a number of seconds"
            ) from exc
        if parsed <= 0:
            raise ValueError(f"TEMPLATE_HEALTH_GATE_TIMEOUT must be positive, got {parsed}")
        return parsed
    return _GATE_TIMEOUT_OVERRIDES.get(name, _GATE_TIMEOUT_SECONDS)


# Canonical, stable list of gate names (used by ``--gates`` parsing and
# tests). Generated once at import time from a sentinel ``Path(".")`` —
# the names do not depend on the repo root.
GATE_NAMES: tuple[str, ...] = tuple(name for name, _ in build_gate_specs(Path(".")))


def gate_spec_sha256(specs: Sequence[tuple[str, Sequence[str]]]) -> str:
    """Return a content digest binding gate names to exact argv contracts."""

    payload = [(name, list(argv)) for name, argv in specs]
    encoded = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def _repository_state(repo_root: Path) -> tuple[str | None, bool | None]:
    """Return current commit and cleanliness, or unknown outside a Git checkout."""

    try:
        commit = subprocess.run(  # noqa: S603 - fixed git executable and argv.
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        status = subprocess.run(  # noqa: S603 - fixed git executable and argv.
            ["git", "status", "--porcelain", "--untracked-files=normal"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except OSError:
        # A missing or unexecutable git binary is the same contract as being
        # outside a Git checkout: the repository state is simply unknown.
        return None, None
    if commit.returncode != 0 or status.returncode != 0:
        return None, None
    return commit.stdout.strip(), not bool(status.stdout.strip())


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
    # Require the generator's complete summary rather than treating arbitrary
    # exit-zero output (including an empty/crashed-before-work path) as proof.
    summaries = re.findall(
        r"Would update\s+(\d+)\s*;\s*up-to-date\s+(\d+)",
        combined_output,
        flags=re.IGNORECASE,
    )
    if len(summaries) != 1:
        return False
    changed, unchanged = (int(value) for value in summaries[0])
    if changed != 0 or unchanged == 0:
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
    workers: int | None = None,
) -> HealthReport:
    """Run every configured gate (or a subset) and aggregate results.

    Args:
        repo_root: Repository root the gates should run against. Each
            subprocess is launched with ``cwd=repo_root``.
        gates: Optional subset of gate names to run. ``None`` runs every
            gate in :data:`GATE_NAMES`. Unknown names raise ``ValueError``.
        json_output: Reserved for symmetry with the CLI; the report is
            always returned as a typed object regardless.
        workers: Maximum number of independent gate subprocesses. ``None``
            uses four workers for the full local sweep, or one worker for a
            single-gate subset. Passing ``1`` retains the serial diagnostic
            mode. Values below one raise ``ValueError``.

    Returns:
        :class:`HealthReport` aggregating per-gate results.
    """

    del json_output  # CLI-only; the dataclass is the canonical artefact.
    if workers is not None and workers < 1:
        raise ValueError("workers must be at least 1")
    specs = build_gate_specs(repo_root)
    if gates is not None:
        wanted = list(gates)
        if not wanted:
            raise ValueError("at least one gate must be selected")
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

    selected_workers = workers if workers is not None else (4 if len(specs) > 1 else 1)
    spec_digest = gate_spec_sha256(specs)
    commit_before, clean_before = _repository_state(repo_root)
    start = time.perf_counter()
    if selected_workers == 1 or len(specs) == 1:
        results = [
            _run_single_gate(name, argv, repo_root, timeout_seconds=_gate_timeout_seconds(name)) for name, argv in specs
        ]
    else:
        # Gates are subprocess boundaries and do not share mutable Python
        # state. A bounded thread pool overlaps their I/O while preserving
        # the canonical registry order through ``executor.map``.
        with ThreadPoolExecutor(max_workers=min(selected_workers, len(specs))) as executor:
            results = list(
                executor.map(
                    lambda spec: _run_single_gate(
                        spec[0], spec[1], repo_root, timeout_seconds=_gate_timeout_seconds(spec[0])
                    ),
                    specs,
                )
            )

    total_ms = sum(r.elapsed_ms for r in results)
    wall_ms = (time.perf_counter() - start) * 1000.0
    commit_after, clean_after = _repository_state(repo_root)
    # ``specs`` is non-empty for the default registry and empty explicit
    # subsets are rejected above. Keep the aggregate fail-closed if that
    # invariant is ever broken by a future registry change.
    overall = bool(results) and all(r.passed for r in results)
    return HealthReport(
        results=results,
        passed=overall,
        total_elapsed_ms=total_ms,
        wall_elapsed_ms=wall_ms,
        workers=selected_workers,
        repo_commit=commit_before if commit_before == commit_after else None,
        clean_checkout=(clean_before is True and clean_after is True),
        gate_spec_sha256=spec_digest,
    )


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
    wall_s = report.wall_elapsed_ms / 1000.0
    lines.append(
        f"Overall: {overall_colored}  ({wall_s:.2f}s wall, {total_s:.2f}s gate-time, {len(report.results)} gates)"
    )
    return "\n".join(lines)


def _report_to_dict(report: HealthReport) -> dict[str, object]:
    """Convert ``HealthReport`` to a JSON-serialisable dict."""

    return {
        "schema_version": report.schema_version,
        "passed": report.passed,
        "workers": report.workers,
        "repo_commit": report.repo_commit,
        "clean_checkout": report.clean_checkout,
        "gate_spec_sha256": report.gate_spec_sha256,
        "total_elapsed_ms": report.total_elapsed_ms,
        "wall_elapsed_ms": report.wall_elapsed_ms,
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
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help=("Maximum concurrent gate subprocesses (default: 4 for a full sweep; use 1 for serial diagnostics)."),
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
        report = run_health_checks(repo_root, gates=gates, workers=args.workers)
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
