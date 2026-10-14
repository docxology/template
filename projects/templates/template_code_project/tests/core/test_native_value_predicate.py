"""Independent numeric controls using the real Code producers and real bodies.

Written for later execution in the admitted resource interval. No result,
native operation, expected status, mathematical callback or worker is replaced.
"""

from __future__ import annotations

import json
import time
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

from infrastructure.reporting.native_code_value_predicate import (
    CSV_HEADER,
    ScalarQuadraticConfig,
    validate_explicit_scalar_config,
    validate_scalar_csv,
    validate_scalar_variables,
)
from template_code_project.analysis.experiments import run_convergence_experiment, save_optimization_results
from template_code_project.core.experiment_config import ExperimentConfig, load_experiment_config
from template_code_project.core.manuscript_variables import generate_variables
from template_code_project.core.project_paths import project_root_context

PROJECT = Path(__file__).resolve().parents[2]


def _normalize(value: ExperimentConfig) -> ScalarQuadraticConfig:
    return ScalarQuadraticConfig(
        step_sizes=value.step_sizes,
        coefficient=value.quadratic_A[0][0],
        linear=value.quadratic_b[0],
        initial_point=value.initial_point,
        max_iterations=value.max_iterations,
        tolerance=value.tolerance,
        convergence_tolerance=value.convergence_tolerance,
        stability_starting_points=value.stability_starting_points,
        stability_step_sizes=value.stability_step_sizes,
        benchmark_dimensions=value.benchmark_dimensions,
    )


@pytest.fixture
def actual_code_bodies(tmp_path: Path) -> tuple[ScalarQuadraticConfig, bytes, dict[str, str]]:
    """Run the actual complete authored grid and actual CSV/variable writers."""
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "config.yaml").write_bytes((PROJECT / "manuscript/config.yaml").read_bytes())
    config = load_experiment_config(tmp_path)
    with project_root_context(tmp_path):
        results = run_convergence_experiment(config=config)
        body = save_optimization_results(results).read_bytes()
        variables = generate_variables(tmp_path, require_analysis_outputs=True)
    return _normalize(config), body, variables


def test_entire_actual_scalar_grid_and_variable_mapping(actual_code_bodies) -> None:
    config, body, variables = actual_code_bodies
    rows = validate_scalar_csv(config, body)
    assert tuple(float(row[0]) for row in rows) == config.step_sizes
    assert rows[-1][3:] == ("876", "False", "1.80e+154", "non_finite")
    assert rows[-1][1].startswith("-")
    assert rows[-1][2].startswith("162500937139598269")
    assert rows[0][3:] == ("1000", "False", "4.32e-05", "max_iterations")
    assert rows[3][3:] == ("1", "True", "0.00e+00", "converged")
    checked = validate_scalar_variables(config, body, variables)
    assert "RESULT_TABLE_ROWS" in checked
    assert "RESULT_CONVERGENCE_FACTORS" in checked
    assert "CONFIG_STABILITY_CELLS" in checked
    assert "STABILITY_SCORE" not in checked
    assert "GENERATION_TIMESTAMP" not in checked
    last_display = variables["RESULT_TABLE_ROWS"].splitlines()[-1]
    assert "-1.8028e+154" in last_display
    assert "1.6250e+308" in last_display
    assert len(last_display) < 150
    with pytest.raises(ValueError, match="RESULT_TABLE_ROWS"):
        validate_scalar_variables(
            config,
            body,
            {**variables, "RESULT_TABLE_ROWS": variables["RESULT_TABLE_ROWS"].replace("1.6250e+308", "1.6251e+308")},
        )


@pytest.mark.parametrize("field", range(7))
def test_every_signed_late_csv_field_is_independently_checked(actual_code_bodies, field: int) -> None:
    config, body, _ = actual_code_bodies
    lines = body.decode().splitlines()
    row = lines[-1].split(",")
    corruptions = ("2.6", row[1].removeprefix("-"), "-" + row[2], "875", "True", "1.80e+155", "converged")
    row[field] = corruptions[field]
    lines[-1] = ",".join(row)
    with pytest.raises(ValueError, match="entire independent configured recurrence"):
        validate_scalar_csv(config, ("\n".join(lines) + "\n").encode())


@pytest.mark.parametrize("mutation", ("missing", "repeated", "reordered", "extra", "header", "unit", "nan"))
def test_complete_csv_roster_and_units_fail_closed(actual_code_bodies, mutation: str) -> None:
    config, body, _ = actual_code_bodies
    lines = body.decode().splitlines()
    if mutation == "missing":
        lines.pop()
    elif mutation == "repeated":
        lines[-1] = lines[-2]
    elif mutation == "reordered":
        lines[-1], lines[-2] = lines[-2], lines[-1]
    elif mutation == "extra":
        lines.append(lines[-1])
    elif mutation == "header":
        lines.insert(2, lines[0])
    elif mutation == "unit":
        lines[-1] = lines[-1].replace("1.80e+154", "1.80e+154 m/s")
    else:
        lines[-1] = lines[-1].replace("1.80e+154", "nan")
    with pytest.raises(ValueError, match="entire independent configured recurrence"):
        validate_scalar_csv(config, ("\n".join(lines) + "\n").encode())


@pytest.mark.parametrize(
    ("name", "replacement"),
    (
        ("RESULT_OPTIMUM_F", "0.5"),
        ("RESULT_OPTIMUM_X", "-1.0"),
        ("RESULT_MAX_ITERATIONS", "999"),
        ("RESULT_AVG_ITERATIONS", "352"),
        ("RESULT_NUM_CONVERGED", "6"),
        ("RESULT_BEST_STEP_SIZE", "2.5"),
        ("RESULT_WORST_STEP_SIZE", "1.0"),
        ("CONFIG_TOLERANCE", "10^{-7}"),
        ("CONFIG_QUADRATIC_A", "[(2.0,)]"),
        ("CONFIG_STABILITY_CELLS", "49"),
        ("CONFIG_BENCHMARK_MAX_DIM", "500"),
    ),
)
def test_numeric_variables_sign_grid_and_units_are_independent(actual_code_bodies, name, replacement) -> None:
    config, body, variables = actual_code_bodies
    altered = {**variables, name: replacement}
    with pytest.raises(ValueError, match=name):
        validate_scalar_variables(config, body, altered)


def test_repeated_and_late_consumed_table_occurrences_are_checked(actual_code_bodies) -> None:
    config, body, variables = actual_code_bodies
    lines = variables["RESULT_TABLE_ROWS"].splitlines()
    lines[-1] = lines[-2]
    with pytest.raises(ValueError, match="RESULT_TABLE_ROWS"):
        validate_scalar_variables(config, body, {**variables, "RESULT_TABLE_ROWS": "\n".join(lines)})
    lines = variables["RESULT_CONVERGENCE_FACTORS"].splitlines()
    lines[-1] = lines[-1].replace("1.50", "0.50")
    with pytest.raises(ValueError, match="RESULT_CONVERGENCE_FACTORS"):
        validate_scalar_variables(config, body, {**variables, "RESULT_CONVERGENCE_FACTORS": "\n".join(lines)})


def test_malformed_signed_zero_and_serialization_are_not_tolerated() -> None:
    config = _normalize(ExperimentConfig(step_sizes=(1.0,), max_iterations=2))
    body = (CSV_HEADER + "1.0,1.000000,-0.500000,1,True,0.00e+00,converged\n").encode()
    assert validate_scalar_csv(config, body)[0][2] == "-0.500000"
    for wrong in (
        body.replace(b"0.00e+00", b"-0.00e+00"),
        body.replace(b"1.000000", b"1.0"),
        body.replace(b"True", b"true"),
        body.replace(b"\n", b"\r\n"),
        body + b"\n",
    ):
        with pytest.raises(ValueError):
            validate_scalar_csv(config, wrong)


def test_independent_scalar_recurrence_handles_negative_solution_and_nonidentity_quadratic(tmp_path: Path) -> None:
    config = ExperimentConfig(
        step_sizes=(0.1, 0.5, 1.0, 2.0),
        quadratic_A=((2.0,),),
        quadratic_b=(-4.0,),
        initial_point=3.0,
        max_iterations=20,
    )
    with project_root_context(tmp_path):
        body = save_optimization_results(run_convergence_experiment(config=config)).read_bytes()
    rows = validate_scalar_csv(_normalize(config), body)
    assert rows[1][1:5] == ("-2.000000", "-4.000000", "1", "True")
    assert rows[2][4] == "False"
    assert rows[3][1].startswith("-") is False


def test_shared_original_deadline_refuses_even_known_correct_data(actual_code_bodies) -> None:
    config, body, variables = actual_code_bodies
    expired = time.monotonic() - 1
    with pytest.raises(TimeoutError, match="original deadline"):
        validate_scalar_csv(config, body, deadline=expired)
    with pytest.raises(TimeoutError, match="original deadline"):
        validate_scalar_variables(config, body, variables, deadline=expired)


def test_declaration_data_cannot_replace_missing_or_malformed_numeric_inputs(actual_code_bodies) -> None:
    config, body, variables = actual_code_bodies
    for bad_config in (
        {"step_sizes": list(config.step_sizes), "status": "pass"},
        None,
    ):
        with pytest.raises(ValueError):
            validate_scalar_csv(bad_config, body)
    for malformed in (b"", json.dumps({"status": "pass", "rows": "complete"}).encode()):
        with pytest.raises(ValueError):
            validate_scalar_csv(config, malformed)
    with pytest.raises(ValueError, match="CONFIG_NUM_STEP_SIZES"):
        validate_scalar_variables(config, body, {})
    with pytest.raises(ValueError, match="flat string-valued"):
        validate_scalar_variables(config, body, {**variables, "RESULT_OPTIMUM_X": 1.0})
    with pytest.raises(ValueError, match="repeats"):
        replace(config, step_sizes=(0.1, 0.1))
    with pytest.raises(ValueError, match="finite"):
        replace(config, tolerance=float("nan"))
    with pytest.raises(ValueError, match="positive"):
        replace(config, coefficient=-1.0)


def test_actual_typed_loader_data_is_bound_to_every_explicit_authored_field(actual_code_bodies) -> None:
    config, _, _ = actual_code_bodies
    experiment = yaml.safe_load((PROJECT / "manuscript/config.yaml").read_bytes())["experiment"]
    validate_explicit_scalar_config(config, experiment)
    alterations = {
        "step_sizes": (0.1,),
        "coefficient": 2.0,
        "linear": -1.0,
        "initial_point": 1.0,
        "max_iterations": 999,
        "tolerance": 1e-7,
        "convergence_tolerance": 1e-7,
        "stability_starting_points": (0.0,),
        "stability_step_sizes": (0.1,),
        "benchmark_dimensions": (1,),
    }
    for field, value in alterations.items():
        with pytest.raises(ValueError, match="independently held authored experiment"):
            validate_explicit_scalar_config(replace(config, **{field: value}), experiment)
    with pytest.raises(ValueError, match="independently held authored experiment"):
        validate_explicit_scalar_config(replace(config, initial_point=-0.0), experiment)


def test_authored_config_fallback_and_malformed_declarations_do_not_qualify(actual_code_bodies) -> None:
    config, _, _ = actual_code_bodies
    experiment = yaml.safe_load((PROJECT / "manuscript/config.yaml").read_bytes())["experiment"]
    for field in tuple(experiment):
        incomplete = {key: value for key, value in experiment.items() if key != field}
        with pytest.raises(ValueError, match="every explicit authored experiment field"):
            validate_explicit_scalar_config(config, incomplete)
    for field, value in (
        ("tolerance", "1e-8"),
        ("initial_point", []),
        ("max_iterations", True),
        ("quadratic_A", [[1.0, 0.0]]),
        ("quadratic_b", [1.0, 0.0]),
        ("step_sizes", [0.1, 0.1]),
        ("stability_step_sizes", [float("nan")]),
        ("benchmark_dimensions", [1.5]),
    ):
        with pytest.raises(ValueError):
            validate_explicit_scalar_config(config, {**experiment, field: value})
