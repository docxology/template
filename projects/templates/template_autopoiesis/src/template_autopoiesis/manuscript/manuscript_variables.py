"""Manuscript variable generation for template_autopoiesis."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Any
from ..core.common import DERIVED_SEED_BITS, HASH_PREFIX_HEX_LENGTH
from ..core.grammar import load_grammar, KNOWN_DOMAINS, RESERVED_SLOTS
from ..primitives.graph import PAGERANK_ITERATIONS
from ..primitives.optimization import (
    OPTIMIZATION_EXAMPLE_LEARNING_RATE,
    OPTIMIZATION_EXAMPLE_STEPS,
)
from ..primitives.signal import SIGNAL_SAMPLE_POINTS

_PASSED_RE = re.compile(r"(\d+) passed")


def measure_test_summary(
    project_root: str | Path,
    full_report_out: str | Path | None = None,
) -> tuple[int | str, str]:
    """Run this project's own test suite with coverage and return real numbers.

    Returns ``(test_count, coverage_pct)`` derived from an actual pytest +
    coverage run against ``project_root/tests`` and ``project_root/src`` — never
    a hardcoded literal. Standalone execution or parse failures return
    ``("pending", "pending")`` rather than fabricating a plausible-looking value.

    A present executor-held same-run Project Tests measurement is validated
    and consumed; altered present evidence raises rather than rerunning tests.
    Otherwise the standalone path executes pytest with ``--cov-branch``, matching
    this project's branch-enabled coverage configuration. The percentage combines
    statements and branch exits; it is not a pure branch-exit percentage.

    If *full_report_out* is given, the complete per-module coverage JSON from
    that same measurement is copied there for the figure producer.

    Standalone measurement uses the caller's selected interpreter, preserving
    the project environment chosen by the launcher. It never discovers another
    checkout's environment. Runtime identity must be recorded separately for
    own-lock qualification.
    """
    project_root = Path(project_root)
    if "PIPELINE_TEST_MEASUREMENT_SHA256" in os.environ:
        from infrastructure.core.testing.project_test_measurement import consume_measurement

        measured = consume_measurement(project_root, Path(full_report_out) if full_report_out is not None else None)
        if measured is not None:
            return measured
    tests_dir = project_root / "tests"
    src_dir = project_root / "src"
    with tempfile.TemporaryDirectory() as tmp:
        cov_json = Path(tmp) / "coverage.json"
        # Isolate coverage so this inner pytest never inherits or pollutes the
        # parent process's COVERAGE_FILE. When run inside the multi-project
        # union gate (``stage_01_test.py --all-projects --public-projects``) the
        # parent sets COVERAGE_FILE to the shared aggregate data file; without
        # an isolated value, this subprocess would append a trace for the
        # synthetic fixture project's ``src/__init__.py`` (under a tmp_path that
        # is torn down) into that shared file, and the later ``coverage report``
        # would fail with "No source for code: .../src/__init__.py". Pointing
        # COVERAGE_FILE at a private, discarded file severs that leak; this
        # function only reads its own percentage from the JSON report.
        isolated_env = os.environ.copy()
        isolated_env["COVERAGE_FILE"] = str(Path(tmp) / ".coverage.iso")
        isolated_env.pop("COV_CORE_DATAFILE", None)
        existing_pp = isolated_env.get("PYTHONPATH", "")
        isolated_env["PYTHONPATH"] = str(src_dir) + (os.pathsep + existing_pp if existing_pp else "")
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    str(tests_dir),
                    f"--cov={src_dir}",
                    "--cov-branch",
                    f"--cov-report=json:{cov_json}",
                    "-q",
                ],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=120,
                env=isolated_env,
            )
            match = _PASSED_RE.search(result.stdout)
            if result.returncode != 0 or not match or not cov_json.is_file():
                print(
                    "measure_test_summary: inner pytest run did not produce "
                    f"a parseable summary or coverage JSON (rc={result.returncode})\n"
                    f"stdout tail: {result.stdout[-500:]}\n"
                    f"stderr tail: {result.stderr[-500:]}",
                    file=sys.stderr,
                )
                return "pending", "pending"
            test_count = int(match.group(1))
            coverage_data = json.loads(cov_json.read_text())
            coverage_pct = f"{coverage_data['totals']['percent_covered']:.2f}"
            if full_report_out is not None:
                full_report_out = Path(full_report_out)
                full_report_out.parent.mkdir(parents=True, exist_ok=True)
                full_report_out.write_text(cov_json.read_text())
            return test_count, coverage_pct
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError, KeyError):
            print(
                "measure_test_summary: subprocess/parse failure; reporting "
                f"'pending' ({traceback.format_exc(limit=2)})",
                file=sys.stderr,
            )
            return "pending", "pending"


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    """Render a simple Markdown table."""
    sep = "|".join(["---"] * len(headers))
    header_row = "| " + " | ".join(headers) + " |"
    sep_row = "| " + sep + " |"
    body_rows = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join([header_row, sep_row] + body_rows) + "\n"


def generate_variables(
    project_root: str | Path,
    test_count: int | str | None = None,
    coverage_pct: str | None = None,
) -> dict[str, Any]:
    """Generate all manuscript token values from the project config.

    ``test_count``/``coverage_pct`` should be supplied by the caller from a
    real ``measure_test_summary()`` run (see ``scripts/02_measure_test_coverage.py``).
    When omitted, both default to ``"pending"`` — never a fabricated literal.
    """
    project_root = Path(project_root)
    grammar = load_grammar(project_root)

    variables: dict[str, Any] = {}

    # Domain counts
    variables["DOMAIN_COUNT"] = len(KNOWN_DOMAINS)
    variables["DOMAIN_LIST"] = ", ".join(KNOWN_DOMAINS)
    variables["DOMAIN_BULLETS"] = "\n".join(f"- {d}" for d in KNOWN_DOMAINS)

    # Product sizes
    variables["PRODUCT_SIZE"] = grammar.product_size
    variables["EFFECTIVE_PRODUCT_SIZE"] = grammar.effective_product_size

    # Slot info
    variables["SLOT_COUNT"] = len(grammar.slots)
    variables["EFFECTIVE_SLOT_COUNT"] = len(grammar.effective_slots)
    variables["RESERVED_SLOT_COUNT"] = len(RESERVED_SLOTS)
    variables["RESERVED_SLOT_NAMES"] = ", ".join(RESERVED_SLOTS)

    # Dep info
    variables["DEP_COUNT"] = len(grammar.deps)
    variables["DEP_LIST"] = ", ".join(grammar.deps) if grammar.deps else "none"

    # Grammar hash
    variables["GRAMMAR_HASH"] = grammar.grammar_hash
    variables["GRAMMAR_SEED"] = grammar.seed

    # Slot table
    slot_rows = [[s.name, str(len(s.options)), ", ".join(s.options)] for s in grammar.slots]
    variables["SLOT_TABLE"] = _md_table(["Slot", "Options", "Values"], slot_rows)

    # Effective slot table (excludes reserved)
    eff_rows = [[s.name, str(len(s.options)), ", ".join(s.options)] for s in grammar.effective_slots]
    variables["EFFECTIVE_SLOT_TABLE"] = _md_table(["Slot", "Options", "Values"], eff_rows)

    # Test / coverage info — sourced from a real run by the caller, never hardcoded.
    variables["TEST_COUNT"] = test_count if test_count is not None else "pending"
    variables["COVERAGE_PCT"] = coverage_pct if coverage_pct is not None else "pending"

    # Published example parameters come from the executable primitive specs,
    # not parallel literals in the manuscript.
    variables["OPTIMIZATION_EXAMPLE_STEPS"] = OPTIMIZATION_EXAMPLE_STEPS
    variables["OPTIMIZATION_EXAMPLE_LEARNING_RATE"] = OPTIMIZATION_EXAMPLE_LEARNING_RATE
    variables["SIGNAL_SAMPLE_POINTS"] = SIGNAL_SAMPLE_POINTS
    variables["PAGERANK_ITERATIONS"] = PAGERANK_ITERATIONS
    variables["HASH_PREFIX_HEX_LENGTH"] = HASH_PREFIX_HEX_LENGTH
    variables["DERIVED_SEED_BITS"] = DERIVED_SEED_BITS

    return variables


def save_variables(variables: dict[str, Any], out_path: str | Path) -> Path:
    """Write *variables* as JSON to *out_path*."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(variables, indent=2, sort_keys=True))
    return out
