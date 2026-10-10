"""Finite Code token meanings from checked CSV math and authored config DATA.

The enclosing existing Source join supplies genuine read/write and occurrence
custody. These pure projections cannot create that custody or native positions.
Stability-grid truth, inventories and live runtime/time labels remain separate.
"""

from __future__ import annotations

import hashlib
from typing import Any

import yaml

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_code_metadata_domains import METADATA_KEYS
from infrastructure.reporting.native_format_html_source_metadata import require_unambiguous_yaml

CONFIG_POINTERS = {
    "CONFIG_NUM_STEP_SIZES": ("/experiment/step_sizes",),
    "CONFIG_STEP_SIZES_CSV": ("/experiment/step_sizes",),
    "CONFIG_MIN_STEP_SIZE": ("/experiment/step_sizes",),
    "CONFIG_MAX_STEP_SIZE": ("/experiment/step_sizes",),
    "CONFIG_STEP_SIZES_BULLETS": ("/experiment/step_sizes",),
    "CONFIG_INITIAL_POINT": ("/experiment/initial_point",),
    "CONFIG_MAX_ITERATIONS": ("/experiment/max_iterations",),
    "CONFIG_TOLERANCE": ("/experiment/tolerance",),
    "CONFIG_CONVERGENCE_TOL": ("/experiment/convergence_tolerance",),
    "CONFIG_QUADRATIC_A": ("/experiment/quadratic_A",),
    "CONFIG_QUADRATIC_B": ("/experiment/quadratic_b",),
    "CONFIG_NUM_STABILITY_STARTS": ("/experiment/stability_starting_points",),
    "CONFIG_NUM_STABILITY_STEPS": ("/experiment/stability_step_sizes",),
    "CONFIG_STABILITY_CELLS": ("/experiment/stability_starting_points", "/experiment/stability_step_sizes"),
    "CONFIG_STABILITY_MIN_STEP": ("/experiment/stability_step_sizes",),
    "CONFIG_STABILITY_MAX_STEP": ("/experiment/stability_step_sizes",),
    "CONFIG_BENCHMARK_DIMS": ("/experiment/benchmark_dimensions",),
    "CONFIG_BENCHMARK_MIN_DIM": ("/experiment/benchmark_dimensions",),
    "CONFIG_BENCHMARK_MAX_DIM": ("/experiment/benchmark_dimensions",),
}
CSV_COLUMNS = {
    "RESULT_OPTIMUM_X": (),
    "RESULT_OPTIMUM_F": (),
    "RESULT_MIN_ITERATIONS": ("iterations",),
    "RESULT_MAX_ITERATIONS": ("iterations",),
    "RESULT_AVG_ITERATIONS": ("iterations",),
    "RESULT_ALL_CONVERGED": ("converged",),
    "RESULT_NUM_CONVERGED": ("converged",),
    "RESULT_CONVERGED_STEP_SIZES": ("step_size", "converged"),
    "RESULT_DIVERGED_STEP_SIZES": ("step_size", "converged"),
    "RESULT_BEST_STEP_SIZE": ("step_size", "iterations"),
    "RESULT_WORST_STEP_SIZE": ("step_size", "iterations"),
    "RESULT_TABLE_ROWS": ("step_size", "solution", "objective_value", "iterations", "converged", "termination_reason"),
    "RESULT_CONVERGENCE_FACTORS": ("step_size",),
}
METADATA_POINTERS = {
    "CONFIG_VERSION": ("/paper/version",),
    "CONFIG_FIRST_AUTHOR": ("/authors/0/name",),
    "CONFIG_KEYWORDS": ("/keywords",),
    "CONFIG_HASH": ("",),
}
SCALAR_KEYS = frozenset(CONFIG_POINTERS) | frozenset(CSV_COLUMNS)
SUPPORTED_KEYS = SCALAR_KEYS | frozenset(METADATA_POINTERS)
COLUMNS = ("step_size", "solution", "objective_value", "iterations", "converged", "gradient_norm", "termination_reason")


def selected_code_domains(
    config_content: bytes,
    rows: tuple[tuple[str, ...], ...],
    checked_values: dict[str, str],
    variables: dict[str, Any],
    selected_keys: frozenset[str],
    *,
    deadline: float,
) -> dict[str, dict[str, Any]]:
    """Bind every selected supported name to its existing independent formatter.

    checked_values/rows must be the direct validate_scalar_values return in the
    fixed genuine join. No caller-provided projection constitutes admission.
    Metadata predicates are Source bytes/declared labels, never scientific
    grid, report, runtime or clock claims.
    """
    remaining(deadline)
    if set(checked_values) != SCALAR_KEYS or any(not isinstance(value, str) for value in checked_values.values()):
        raise ValueError("Code domain map differs from the complete fixed independent scalar formatter")
    expected = dict(checked_values)
    metadata = selected_keys & frozenset(METADATA_POINTERS)
    if metadata:
        require_unambiguous_yaml(config_content)
        settings = yaml.safe_load(config_content)
        if not isinstance(settings, dict):
            raise ValueError("Code metadata requires the exact authored config object")
        if "CONFIG_VERSION" in metadata:
            paper = settings.get("paper")
            if not isinstance(paper, dict) or not isinstance(paper.get("version"), str):
                raise ValueError("Code selected version requires its explicit authored string")
            expected["CONFIG_VERSION"] = paper["version"]
        if "CONFIG_FIRST_AUTHOR" in metadata:
            authors = settings.get("authors")
            if not isinstance(authors, list) or not authors or not isinstance(authors[0], dict):
                raise ValueError("Code selected first author requires its explicit authored record")
            author = authors[0].get("name")
            if not isinstance(author, str):
                raise ValueError("Code selected first author requires its explicit authored name")
            expected["CONFIG_FIRST_AUTHOR"] = author
        if "CONFIG_KEYWORDS" in metadata:
            keywords = settings.get("keywords")
            if not isinstance(keywords, list) or any(not isinstance(item, str) for item in keywords):
                raise ValueError("Code selected keywords require the exact authored ordered string roster")
            expected["CONFIG_KEYWORDS"] = ", ".join(keywords)
        if "CONFIG_HASH" in metadata:
            expected["CONFIG_HASH"] = hashlib.sha256(config_content).hexdigest()[:16]
    values: dict[str, dict[str, Any]] = {}
    for key in sorted(selected_keys & SUPPORTED_KEYS):
        remaining(deadline)
        payload = expected[key]
        if variables.get(key) != payload:
            raise ValueError(f"selected Code token {key} differs from its independent domain/formatted meaning")
        columns = CSV_COLUMNS.get(key, ())
        pointers = CONFIG_POINTERS.get(key, METADATA_POINTERS.get(key, ()))
        if key in CSV_COLUMNS:
            pointers = (
                ("/experiment/quadratic_A", "/experiment/quadratic_b")
                if key.startswith("RESULT_OPTIMUM_")
                else ("/experiment",)
            )
        cells = []
        for ordinal, row in enumerate(rows, 1):
            remaining(deadline)
            for name in columns:
                cells.append({"row": ordinal, "column": name, "serialized": row[COLUMNS.index(name)]})
        values[key] = {
            "key": key,
            "json_pointer": "/" + key,
            "payload": payload,
            "payload_sha256": hashlib.sha256(payload.encode()).hexdigest(),
            "config_pointers": list(pointers),
            "csv_cells": cells,
            "fixed_source_transform": (
                "native_code_value_predicate._expected_variables:" + key
                if key in SCALAR_KEYS
                else "Source-code-manuscript-config-projection:" + key
            ),
            "claim_boundary": (
                "scalar CSV/config or authored metadata meaning; no grid/report/native-location authority"
            ),
        }
    remaining(deadline)
    return values


def code_consumed_value_meaning(body: dict[str, Any], *, deadline: float) -> tuple[tuple[Any, ...], ...]:
    """Compare every actual selected domain return across Original/Current roots."""
    result: list[tuple[Any, ...]] = []
    contextual = any(row["key"] in METADATA_KEYS for row in body["values"])
    for row in body["values"]:
        remaining(deadline)
        occurrences = []
        for item in row["selected_occurrences"]:
            remaining(deadline)
            identity = (
                item["source"]["path"],
                item["ordinal"],
                item["source_start_byte"],
                item["source_end_byte"],
                item["consumed"]["path"],
            )
            # A genuinely checked contextual value can shift later output
            # intervals. Exact per-run intervals/replacements were already
            # checked by the direct join; authored identity stays invariant.
            occurrences.append(
                identity
                if contextual
                else identity
                + (
                    item["output_start_byte"],
                    item["output_end_byte"],
                    item["replacement_sha256"],
                )
            )
        result.append(
            (
                row["key"],
                row["json_pointer"],
                row["config_pointers"],
                row["csv_cells"],
                ("actual-Source-metadata-role:" + row["key"] if row["key"] in METADATA_KEYS else row["payload_sha256"]),
                row["fixed_source_transform"],
                occurrences,
            )
        )
    remaining(deadline)
    return tuple(result)
