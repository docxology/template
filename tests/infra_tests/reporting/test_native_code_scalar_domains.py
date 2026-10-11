"""Actual bounded math/byte DATA controls, never a fabricated native owner."""

from __future__ import annotations

import copy
import hashlib
import time
from pathlib import Path

import pytest

from infrastructure.rendering.manuscript_hydration_replay import require_shared_hydration
from infrastructure.reporting.native_code_consumed_value_join import _binding, _selected_occurrences
from infrastructure.reporting.native_code_scalar_domains import (
    SCALAR_KEYS,
    SUPPORTED_KEYS,
    code_consumed_value_meaning,
    selected_code_domains,
)
from infrastructure.reporting.native_code_value_predicate import (
    ScalarQuadraticConfig,
    validate_scalar_values,
    validate_scalar_variables,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

CONFIG = b"paper: {version: '1.2'}\nauthors: [{name: 'A researcher'}]\nkeywords: ['math', 'code']\n"
CSV = (
    b"step_size,solution,objective_value,iterations,converged,gradient_norm,termination_reason\n"
    b"1.0,1.000000,-0.500000,1,True,0.00e+00,converged\n"
)
# For a=b=1, alpha=1, x0=0: one update reaches x*=1, f*=-1/2.
# This finite golden map independently fixes precision, signs and spellings.
VALUES = {
    "CONFIG_NUM_STEP_SIZES": "1",
    "CONFIG_STEP_SIZES_CSV": "1.0",
    "CONFIG_MIN_STEP_SIZE": "1.0",
    "CONFIG_MAX_STEP_SIZE": "1.0",
    "CONFIG_STEP_SIZES_BULLETS": "- $\\alpha = 1.0$ (near-optimal)",
    "CONFIG_INITIAL_POINT": "0.0",
    "CONFIG_MAX_ITERATIONS": "2",
    "CONFIG_TOLERANCE": "10^{-6}",
    "CONFIG_CONVERGENCE_TOL": "10^{-6}",
    "CONFIG_QUADRATIC_A": "[(1.0,)]",
    "CONFIG_QUADRATIC_B": "[1.0]",
    "CONFIG_NUM_STABILITY_STARTS": "1",
    "CONFIG_NUM_STABILITY_STEPS": "1",
    "CONFIG_STABILITY_CELLS": "1",
    "CONFIG_STABILITY_MIN_STEP": "0.5",
    "CONFIG_STABILITY_MAX_STEP": "0.5",
    "CONFIG_BENCHMARK_DIMS": "1",
    "CONFIG_BENCHMARK_MIN_DIM": "1",
    "CONFIG_BENCHMARK_MAX_DIM": "1",
    "RESULT_OPTIMUM_X": "1.0",
    "RESULT_OPTIMUM_F": "-0.5",
    "RESULT_MIN_ITERATIONS": "1",
    "RESULT_MAX_ITERATIONS": "1",
    "RESULT_AVG_ITERATIONS": "1",
    "RESULT_ALL_CONVERGED": "Yes",
    "RESULT_NUM_CONVERGED": "1",
    "RESULT_CONVERGED_STEP_SIZES": "1.0",
    "RESULT_DIVERGED_STEP_SIZES": "",
    "RESULT_BEST_STEP_SIZE": "1.0",
    "RESULT_WORST_STEP_SIZE": "1.0",
    "RESULT_TABLE_ROWS": (
        "| 1.00          | 1.0000           | -0.5000          | 1          | Yes       | converged        |"
    ),
    "RESULT_CONVERGENCE_FACTORS": "- $\\alpha = 1.0$: $\\rho \\approx 0.00$, converges in one step ($\\rho = 0$)",
}


def _config() -> ScalarQuadraticConfig:
    return ScalarQuadraticConfig((1.0,), 1.0, 1.0, 0.0, 2, 1e-6, 1e-6, (0.0,), (0.5,), (1,))


def _variables() -> dict[str, str]:
    return {
        **VALUES,
        "CONFIG_VERSION": "1.2",
        "CONFIG_FIRST_AUTHOR": "A researcher",
        "CONFIG_KEYWORDS": "math, code",
        "CONFIG_HASH": hashlib.sha256(CONFIG).hexdigest()[:16],
    }


def test_full_scalar_return_preserves_existing_api_and_golden_complete_recurrence() -> None:
    rows, values = validate_scalar_values(_config(), CSV, VALUES)
    assert rows == (("1.0", "1.000000", "-0.500000", "1", "True", "0.00e+00", "converged"),)
    assert values == VALUES and set(values) == SCALAR_KEYS
    assert validate_scalar_variables(_config(), CSV, VALUES) == tuple(values)


@pytest.mark.parametrize("mutation", ["iterations", "sign", "extra-row", "mean", "config-coefficient"])
def test_complete_csv_and_independent_variable_mutations_fail(mutation: str) -> None:
    csv, values = CSV, dict(VALUES)
    if mutation == "iterations":
        csv = csv.replace(b",1,True,", b",2,True,")
    elif mutation == "sign":
        csv = csv.replace(b"-0.500000", b"0.500000")
    elif mutation == "extra-row":
        csv += CSV.splitlines(keepends=True)[1]
    elif mutation == "mean":
        values["RESULT_AVG_ITERATIONS"] = "2"
    else:
        values["CONFIG_QUADRATIC_A"] = "[(2.0,)]"
    with pytest.raises(ValueError, match="independent"):
        validate_scalar_values(_config(), csv, values)


def test_all_thirty_six_selected_domains_keep_actual_field_and_cell_dependencies() -> None:
    variables = _variables()
    rows, checked = validate_scalar_values(_config(), CSV, variables)
    domains = selected_code_domains(CONFIG, rows, checked, variables, SUPPORTED_KEYS, deadline=time.monotonic() + 10)
    assert set(domains) == SUPPORTED_KEYS and len(domains) == 36
    assert all(row["payload"] == variables[key] for key, row in domains.items())
    assert domains["RESULT_AVG_ITERATIONS"]["csv_cells"] == [{"row": 1, "column": "iterations", "serialized": "1"}]
    assert domains["CONFIG_CONVERGENCE_TOL"]["config_pointers"] == ["/experiment/convergence_tolerance"]
    assert domains["CONFIG_FIRST_AUTHOR"]["config_pointers"] == ["/authors/0/name"]
    assert domains["CONFIG_HASH"]["payload"] == hashlib.sha256(CONFIG).hexdigest()[:16]
    assert not any("native_position" in row or "passed" in row for row in domains.values())


@pytest.mark.parametrize("key", ["CONFIG_VERSION", "CONFIG_FIRST_AUTHOR", "CONFIG_KEYWORDS", "CONFIG_HASH"])
def test_selected_authored_metadata_payload_drift_fails(key: str) -> None:
    variables = _variables()
    rows, checked = validate_scalar_values(_config(), CSV, variables)
    variables[key] += "changed"
    with pytest.raises(ValueError, match=key):
        selected_code_domains(CONFIG, rows, checked, variables, frozenset({key}), deadline=time.monotonic() + 10)


def test_unknown_runtime_and_report_values_never_become_supported_domains() -> None:
    variables = {**_variables(), "STABILITY_SCORE": "1.00", "PYTHON_VERSION": "unproven", "FUTURE_METRIC": "1"}
    rows, checked = validate_scalar_values(_config(), CSV, variables)
    assert (
        selected_code_domains(
            CONFIG,
            rows,
            checked,
            variables,
            frozenset({"STABILITY_SCORE", "PYTHON_VERSION", "FUTURE_METRIC"}),
            deadline=time.monotonic() + 10,
        )
        == {}
    )


def test_equal_payloads_keep_distinct_source_keys_ordinals_and_output_intervals(tmp_path: Path) -> None:
    project = tmp_path / "projects/templates/template_code_project"
    authored = project / "manuscript/03_results.md"
    consumed = project / "output/manuscript/03_results.md"
    authored.parent.mkdir(parents=True)
    consumed.parent.mkdir(parents=True)
    raw = b"{{RESULT_MIN_ITERATIONS}} {{RESULT_MAX_ITERATIONS}} {{STABILITY_SCORE}}\n"
    variables = {"RESULT_MIN_ITERATIONS": "1", "RESULT_MAX_ITERATIONS": "1", "STABILITY_SCORE": "1"}
    output = b"1 1 1\n"
    authored.write_bytes(raw)
    consumed.write_bytes(output)
    reader = SnapshotReader(tmp_path)
    source, held = (reader.read(path.relative_to(tmp_path).as_posix()) for path in (authored, consumed))
    graph = {
        "ordered_inputs": [
            {
                "source": _binding(source),
                "consumed": _binding(held),
                "transformation": "shared-uppercase-token-hydration",
                "hydration": require_shared_hydration(raw, variables, output).data(),
            }
        ]
    }
    selected, residuals = _selected_occurrences(
        graph, reader, deadline=time.monotonic() + 10, supported_keys=SUPPORTED_KEYS
    )
    assert [(row["key"], row["ordinal"], row["output_start_byte"]) for row in selected] == [
        ("RESULT_MIN_ITERATIONS", 1, 0),
        ("RESULT_MAX_ITERATIONS", 2, 2),
    ]
    assert len(residuals) == 1 and residuals[0].endswith(":3:STABILITY_SCORE")
    assert reader.unchanged()


def test_full_meaning_projection_compares_each_selected_occurrence_not_only_minimum() -> None:
    variables = _variables()
    rows, checked = validate_scalar_values(_config(), CSV, variables)
    domains = selected_code_domains(
        CONFIG, rows, checked, variables, frozenset({"RESULT_MAX_ITERATIONS"}), deadline=time.monotonic() + 10
    )
    row = domains["RESULT_MAX_ITERATIONS"]
    body = {
        "values": [
            {
                **row,
                "selected_occurrences": [
                    {
                        "source": {"path": "projects/templates/template_code_project/manuscript/03_results.md"},
                        "ordinal": 2,
                        "source_start_byte": 26,
                        "source_end_byte": 51,
                        "consumed": {
                            "path": "projects/templates/template_code_project/output/manuscript/03_results.md"
                        },
                        "output_start_byte": 2,
                        "output_end_byte": 3,
                        "replacement_sha256": hashlib.sha256(b"1").hexdigest(),
                    }
                ],
            }
        ]
    }
    changed = copy.deepcopy(body)
    changed["values"][0]["selected_occurrences"][0]["ordinal"] = 1
    deadline = time.monotonic() + 10
    assert code_consumed_value_meaning(body, deadline=deadline) != code_consumed_value_meaning(
        changed, deadline=deadline
    )
