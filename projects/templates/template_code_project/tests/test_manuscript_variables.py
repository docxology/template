"""Tests for src.manuscript_variables (template_code_project).

Includes a live cross-reference test that reads the actual manuscript files
and asserts every {{TOKEN}} they contain is produced by generate_variables().
This test is the enforcement mechanism: if a manuscript token drifts out of
sync with the generator it will fail immediately rather than silently
producing a PDF with literal {{...}} placeholders.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import pytest
import yaml

from src.manuscript_variables import (
    _format_sci,
    _step_agency_label,
    generate_variables,
    save_variables,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DOC_ONLY = frozenset({"AGENTS.md", "README.md", "SYNTAX.md"})
_TOKEN_RE = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")


def _make_minimal_project(tmp_path: Path, *, with_results: bool = True) -> Path:
    """Build a minimal project tree to exercise generate_variables()."""
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir(parents=True)
    (manuscript / "config.yaml").write_text(
        yaml.dump(
            {
                "paper": {"title": "Test Paper", "version": "1.0"},
                "authors": [{"name": "Alice"}],
                "keywords": ["optimization", "gradient"],
                "experiment": {
                    "step_sizes": [0.1, 0.5, 1.0],
                    "initial_point": 0.0,
                    "max_iterations": 100,
                    "tolerance": 1e-6,
                    "convergence_tolerance": 1e-8,
                    "quadratic_A": [[2.0]],
                    "quadratic_b": [4.0],
                    "stability_starting_points": [-10.0, 0.0, 10.0],
                    "stability_step_sizes": [0.1, 0.5],
                    "benchmark_dimensions": [1, 5, 10],
                },
            }
        ),
        encoding="utf-8",
    )

    if with_results:
        data_dir = tmp_path / "output" / "data"
        data_dir.mkdir(parents=True)
        reports_dir = tmp_path / "output" / "reports"
        reports_dir.mkdir(parents=True)

        with (data_dir / "optimization_results.csv").open("w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["step_size", "solution", "objective_value", "iterations", "converged"],
            )
            writer.writeheader()
            writer.writerows(
                [
                    _result_row("0.1", iterations="50"),
                    _result_row("0.5", iterations="10"),
                    _result_row("1.0", iterations="1"),
                ]
            )

        (reports_dir / "stability_analysis.json").write_text(
            json.dumps({"stability_score": 0.95, "function_name": "quadratic_function"}),
            encoding="utf-8",
        )
    return tmp_path


def _result_row(step_size: str, *, iterations: str, converged: str = "True") -> dict[str, str]:
    return {
        "step_size": step_size,
        "solution": "2.0",
        "objective_value": "-4.0",
        "iterations": iterations,
        "converged": converged,
    }


# ---------------------------------------------------------------------------
# generate_variables — structure and key coverage
# ---------------------------------------------------------------------------


def test_all_keys_present_with_results(tmp_path):
    root = _make_minimal_project(tmp_path)
    variables = generate_variables(root)
    assert isinstance(variables, dict)
    assert all(isinstance(k, str) and k == k.upper() for k in variables), "All keys must be UPPERCASE_SNAKE"


def test_all_keys_present_without_results(tmp_path):
    """generate_variables must return the full key set even when data files are absent."""
    root_with = _make_minimal_project(tmp_path / "with_results")
    root_without = _make_minimal_project(tmp_path / "without", with_results=False)

    keys_with = set(generate_variables(root_with))
    keys_without = set(generate_variables(root_without))

    assert keys_with == keys_without, f"Missing keys in fallback run: {sorted(keys_with - keys_without)}"


def test_load_config_missing_file(tmp_path):
    root = tmp_path / "empty"
    root.mkdir()
    from src.manuscript_variables import _load_config

    assert _load_config(root) == {}


def test_load_optimization_results_missing_csv(tmp_path):
    from src.manuscript_variables import _load_optimization_results

    assert _load_optimization_results(tmp_path) == []


def test_config_derived_values(tmp_path):
    root = _make_minimal_project(tmp_path)
    v = generate_variables(root)

    assert v["CONFIG_NUM_STEP_SIZES"] == "3"
    assert v["CONFIG_MIN_STEP_SIZE"] == "0.1"
    assert v["CONFIG_MAX_STEP_SIZE"] == "1.0"
    assert v["CONFIG_NUM_STABILITY_STARTS"] == "3"
    assert v["CONFIG_NUM_STABILITY_STEPS"] == "2"
    assert v["CONFIG_STABILITY_CELLS"] == "6"  # 3 × 2
    assert v["CONFIG_FIRST_AUTHOR"] == "Alice"
    assert "optimization" in v["CONFIG_KEYWORDS"]
    assert v["CONFIG_VERSION"] == "1.0"


def test_config_step_sizes_match_project_yaml():
    """Real config.yaml defines six step sizes for the exemplar pipeline."""
    project_root = Path(__file__).resolve().parent.parent
    v = generate_variables(project_root)
    assert v["CONFIG_NUM_STEP_SIZES"] == "6"


def test_result_derived_values(tmp_path):
    root = _make_minimal_project(tmp_path)
    v = generate_variables(root)

    assert v["RESULT_NUM_CONVERGED"] == "3"
    assert v["RESULT_ALL_CONVERGED"] == "Yes"
    assert v["RESULT_MIN_ITERATIONS"] == "1"
    assert v["RESULT_MAX_ITERATIONS"] == "50"
    assert v["RESULT_BEST_STEP_SIZE"] == "1.0"
    assert v["RESULT_TABLE_ROWS"] != "| N/A | N/A | N/A | N/A | N/A |"


def test_stability_derived(tmp_path):
    root = _make_minimal_project(tmp_path)
    v = generate_variables(root)

    assert v["STABILITY_SCORE"] == "0.95"
    assert v["STABILITY_FUNCTION"] == "quadratic_function"


def test_fallback_sentinels_when_no_results(tmp_path):
    root = _make_minimal_project(tmp_path, with_results=False)
    v = generate_variables(root)

    assert v["RESULT_NUM_CONVERGED"] == "N/A"
    assert v["RESULT_TABLE_ROWS"] == "| N/A | N/A | N/A | N/A | N/A |"
    assert v["RESULT_CONVERGENCE_FACTORS"] == "- No data available"
    assert v["STABILITY_SCORE"] == "0.00"


def test_provenance_keys_populated(tmp_path):
    root = _make_minimal_project(tmp_path)
    v = generate_variables(root)

    assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", v["GENERATION_TIMESTAMP"])
    assert re.match(r"\d+\.\d+\.\d+", v["PYTHON_VERSION"])
    assert len(v["CONFIG_HASH"]) == 16


# ---------------------------------------------------------------------------
# save_variables
# ---------------------------------------------------------------------------


def test_save_variables_round_trip(tmp_path):
    root = _make_minimal_project(tmp_path)
    variables = generate_variables(root)
    out = tmp_path / "vars.json"
    save_variables(variables, out)

    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded["CONFIG_NUM_STEP_SIZES"] == "3"
    assert loaded["CONFIG_FIRST_AUTHOR"] == "Alice"


def test_save_variables_creates_parent_dir(tmp_path):
    root = _make_minimal_project(tmp_path)
    v = generate_variables(root)
    deep = tmp_path / "a" / "b" / "c" / "vars.json"
    save_variables(v, deep)
    assert deep.exists()


# ---------------------------------------------------------------------------
# Live cross-reference: every {{TOKEN}} in the actual manuscript must be
# produced by generate_variables()
# ---------------------------------------------------------------------------


def _make_project_with_rows(tmp_path: Path, rows: list[dict]) -> Path:
    """Build a minimal project with custom optimization CSV rows."""
    root = _make_minimal_project(tmp_path, with_results=False)
    data_dir = root / "output" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    reports_dir = root / "output" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    with (data_dir / "optimization_results.csv").open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["step_size", "solution", "objective_value", "iterations", "converged"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    (reports_dir / "stability_analysis.json").write_text(
        '{"stability_score": 0.8, "function_name": "f"}', encoding="utf-8"
    )
    return root


# ---------------------------------------------------------------------------
# _format_sci — pure-function branch coverage
# ---------------------------------------------------------------------------


def test_format_sci_zero():
    assert _format_sci(0.0) == "0"
    assert _format_sci(0) == "0"


def test_format_sci_exact_power_of_ten():
    result = _format_sci(1e-6)
    assert result == "10^{-6}"


def test_format_sci_exact_power_of_ten_negative_exp():
    result = _format_sci(1e-8)
    assert result == "10^{-8}"


def test_format_sci_non_unit_coeff():
    result = _format_sci(2.5e-4)
    assert "\\times" in result
    assert "10^{" in result


# ---------------------------------------------------------------------------
# _step_agency_label — all four return branches
# ---------------------------------------------------------------------------


def test_step_agency_label_conservative():
    assert _step_agency_label(0.1) == "conservative"
    assert _step_agency_label(0.0) == "conservative"


def test_step_agency_label_near_optimal():
    assert _step_agency_label(0.5) == "near-optimal"
    assert _step_agency_label(1.0) == "near-optimal"


def test_step_agency_label_aggressive():
    assert _step_agency_label(1.5) == "aggressive"
    assert _step_agency_label(1.99) == "aggressive"


def test_step_agency_label_divergent():
    result = _step_agency_label(2.0)
    assert "divergent" in result
    assert _step_agency_label(3.0) == _step_agency_label(2.0)


# ---------------------------------------------------------------------------
# generate_variables — missing-config fallback (covers lines 45-46, 72)
# ---------------------------------------------------------------------------


def test_generate_variables_no_config(tmp_path):
    """generate_variables must return all keys even with no manuscript/config.yaml."""
    root_with = _make_minimal_project(tmp_path / "with_config")
    keys_with = set(generate_variables(root_with))

    empty_root = tmp_path / "no_config"
    empty_root.mkdir()
    keys_without = set(generate_variables(empty_root))

    assert keys_with == keys_without, f"Missing keys without config: {sorted(keys_with - keys_without)}"
    v = generate_variables(empty_root)
    assert v["CONFIG_HASH"] == "N/A"


def test_generate_variables_require_analysis_outputs_raises(tmp_path):
    root = _make_minimal_project(tmp_path / "draft", with_results=False)
    with pytest.raises(FileNotFoundError, match="optimization_results"):
        generate_variables(root, require_analysis_outputs=True)


def test_generate_variables_require_analysis_outputs_passes_with_csv(tmp_path):
    root = _make_minimal_project(tmp_path / "ready", with_results=True)
    variables = generate_variables(root, require_analysis_outputs=True)
    assert variables["RESULT_OPTIMUM_X"] != "N/A"


# ---------------------------------------------------------------------------
# generate_variables — partial convergence (RESULT_ALL_CONVERGED == "No")
# ---------------------------------------------------------------------------


def test_result_not_all_converged(tmp_path):
    rows = [
        {"step_size": "0.5", "solution": "2.0", "objective_value": "-4.0", "iterations": "10", "converged": "True"},
        {
            "step_size": "2.5",
            "solution": "50.0",
            "objective_value": "100.0",
            "iterations": "1000",
            "converged": "False",
        },
    ]
    root = _make_project_with_rows(tmp_path, rows)
    v = generate_variables(root)

    assert v["RESULT_ALL_CONVERGED"] == "No"
    assert v["RESULT_NUM_CONVERGED"] == "1"
    assert "2.5" in v["RESULT_DIVERGED_STEP_SIZES"]
    assert "0.5" in v["RESULT_CONVERGED_STEP_SIZES"]


# ---------------------------------------------------------------------------
# generate_variables — rho ≥ 1 convergence factor (line 252)
# ---------------------------------------------------------------------------


def test_convergence_factor_rho_ge_1(tmp_path):
    """Step size α = 2.0 → ρ = |1 − 2| = 1 ≥ 1 → 'divergent' bullet."""
    rows = [
        {"step_size": "2.0", "solution": "0.0", "objective_value": "0.0", "iterations": "1000", "converged": "False"},
        {"step_size": "0.5", "solution": "2.0", "objective_value": "-4.0", "iterations": "10", "converged": "True"},
    ]
    root = _make_project_with_rows(tmp_path, rows)
    v = generate_variables(root)

    assert "divergent" in v["RESULT_CONVERGENCE_FACTORS"]


def test_all_manuscript_tokens_are_generated(tmp_path):
    """Regression guard: every {{TOKEN}} used in manuscript/*.md must be
    produced by generate_variables() so no placeholder can appear in a
    rendered PDF.

    This test reads the *real* manuscript source tree (not tmp_path) so it
    catches drift introduced by manuscript edits.
    """
    # generate_variables with any valid root produces the full key set
    root = _make_minimal_project(tmp_path, with_results=False)
    produced = set(generate_variables(root))

    project_root = Path(__file__).resolve().parent.parent
    manuscript_dir = project_root / "manuscript"
    if not manuscript_dir.is_dir():
        pytest.skip("manuscript/ directory not found; skipping cross-reference check")

    unresolved: dict[str, list[str]] = {}
    for md_file in sorted(manuscript_dir.glob("*.md")):
        if md_file.name in _DOC_ONLY:
            continue
        text = md_file.read_text(encoding="utf-8")
        for token in _TOKEN_RE.findall(text):
            if token not in produced:
                unresolved.setdefault(token, []).append(md_file.name)

    assert not unresolved, "Manuscript tokens not produced by generate_variables():\n" + "\n".join(
        f"  {{{{{{t}}}}}}: {files}" for t, files in sorted(unresolved.items())
    )


class TestImportFallback:
    def test_logger_fallback_without_infrastructure(self) -> None:
        """Import path when infrastructure logging is unavailable."""
        import subprocess
        import sys

        project_root = Path(__file__).resolve().parent.parent
        code = """
import builtins
import importlib.util
import sys
from pathlib import Path

project_root = Path(sys.argv[1])
real_import = builtins.__import__

def _block_infra(name, globals=None, locals=None, fromlist=(), level=0):
    if name == "infrastructure" or name.startswith("infrastructure."):
        raise ImportError("infrastructure unavailable")
    return real_import(name, globals, locals, fromlist, level)

builtins.__import__ = _block_infra
sys.path.insert(0, str(project_root / "src"))

spec = importlib.util.spec_from_file_location(
    "manuscript_variables_isolated",
    project_root / "src" / "manuscript_variables.py",
)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)
assert mod.logger.name == "manuscript_variables_isolated"
"""
        result = subprocess.run(
            [sys.executable, "-c", code, str(project_root)],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, result.stderr or result.stdout


def test_step_sensitivity_caption_numbers_match_sweep():
    """Pin the #fig:step_sensitivity caption's hardcoded numbers to the sweep the
    figure is generated from, so prose cannot drift from the computation."""
    from src.experiment_config import load_experiment_config
    from src.sweeps import sensitivity_sweep

    sweep = sensitivity_sweep(load_experiment_config())
    n_points = len(sweep.alphas)
    first_iters = sweep.iterations[0]
    last_iters = sweep.iterations[-1]

    caption = (Path(__file__).resolve().parent.parent / "manuscript" / "03_results.md").read_text(
        encoding="utf-8"
    )
    assert f"({n_points} points)" in caption
    assert f"{first_iters} iterations at the smallest" in caption
    assert f"to {last_iters} iterations at" in caption
