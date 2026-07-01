"""Regression pins for the EDA notebook exemplar result claims.

Every value is re-derived from the deterministic ``src/eda`` functions against
the shipped ``data/measurements.csv`` and compared to committed ground truth in
``tests/regression/pinned_values/template_eda_notebook.json``. Nothing here is
transcribed from prose — the manuscript claims in
``projects/templates/template_eda_notebook/manuscript/03_results.md`` are bound
to source computation, per ``docs/maintenance/regression-testing.md``.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]
PROJECT_ROOT = REPO_ROOT / "projects" / "templates" / "template_eda_notebook"


_PKG_ALIAS = "_eda_notebook_src"


def _load_eda_package() -> ModuleType:
    """Load the exemplar's ``src`` package under a project-unique alias.

    Every public exemplar ships a top-level ``src`` package, so a bare
    ``sys.path.insert`` + ``from src...`` (the single-project pattern) collides
    on ``sys.modules['src']`` once a second project joins this tier. Registering
    the package under a namespaced key ``_eda_notebook_src`` and importing its
    submodules through it keeps the *real* tested functions in scope (no mocks),
    lets the modules' own relative imports (``from .dataset import ...``)
    resolve, and stays collision-free across projects.
    """

    if _PKG_ALIAS in sys.modules:
        return sys.modules[_PKG_ALIAS]
    src_init = PROJECT_ROOT / "src" / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        _PKG_ALIAS,
        src_init,
        submodule_search_locations=[str(PROJECT_ROOT / "src")],
    )
    assert spec is not None and spec.loader is not None, f"cannot load {src_init}"
    package = importlib.util.module_from_spec(spec)
    sys.modules[_PKG_ALIAS] = package
    spec.loader.exec_module(package)
    return package


def _import_submodule(dotted: str) -> ModuleType:
    """Import ``<alias>.<dotted>`` (e.g. ``eda.cleaning``) via importlib."""

    _load_eda_package()
    return importlib.import_module(f"{_PKG_ALIAS}.{dotted}")


clean_dataset = _import_submodule("eda.cleaning").clean_dataset
_correlation = _import_submodule("eda.correlation")
correlation_matrix = _correlation.correlation_matrix
strongest_pairs = _correlation.strongest_pairs
load_dataset = _import_submodule("eda.dataset").load_dataset
histogram_data = _import_submodule("eda.figures").histogram_data


def _pin(pinned: dict[str, Any], key: str) -> dict[str, Any]:
    entry = pinned[key]
    assert isinstance(entry, dict), f"{key} must be an object"
    assert "value" in entry, f"{key} must include a pinned value"
    return entry


def _assert_pin_matches(entry: dict[str, Any], observed: float | int) -> None:
    tolerance = entry.get("abs_tolerance", 0)
    assert observed == pytest.approx(entry["value"], abs=tolerance)


@pytest.fixture(scope="module")
def eda_pipeline() -> dict[str, Any]:
    """Run the deterministic EDA pipeline once from the shipped fixture CSV."""

    raw = load_dataset()
    cleaned, report = clean_dataset(raw)
    matrix = correlation_matrix(cleaned)
    return {
        "raw": raw,
        "cleaned": cleaned,
        "report": report,
        "matrix": matrix,
        "pairs": strongest_pairs(matrix, top_n=3),
    }


def test_dataset_and_missingness_counts_rederive(
    load_pinned_values: Any,
    eda_pipeline: dict[str, Any],
) -> None:
    """Bind the '120 subject records' and 'four rows removed' claims to source."""

    pinned = load_pinned_values("template_eda_notebook")

    raw_rows = int(len(eda_pipeline["raw"]))
    dropped = int(eda_pipeline["report"].dropped)

    _assert_pin_matches(_pin(pinned, "dataset_subject_record_count"), raw_rows)
    _assert_pin_matches(_pin(pinned, "missingness_rows_dropped"), dropped)


def test_correlation_ranking_and_signs_rederive(
    load_pinned_values: Any,
    eda_pipeline: dict[str, Any],
) -> None:
    """Bind the height~weight and height~HR correlation claims to source.

    Checks the ranking (which pair is first vs second), the sign of each
    coefficient, and the numeric value against the committed pins.
    """

    pinned = load_pinned_values("template_eda_notebook")
    pairs = eda_pipeline["pairs"]

    top_entry = _pin(pinned, "strongest_pair_height_weight_value")
    second_entry = _pin(pinned, "second_pair_height_hr_value")

    # Ranking claim: the dominant pair is height ~ weight, then height ~ HR.
    top_pair = {pairs[0][0], pairs[0][1]}
    second_pair = {pairs[1][0], pairs[1][1]}
    assert top_pair == set(top_entry["verifier_args"]["expected_pair"])
    assert second_pair == set(second_entry["verifier_args"]["expected_pair"])

    # Sign claims: strong positive first, "slightly negative" second.
    assert pairs[0][2] > 0
    assert pairs[1][2] < 0

    # Numeric value claims to documented tolerance.
    _assert_pin_matches(top_entry, pairs[0][2])
    _assert_pin_matches(second_entry, pairs[1][2])


def test_height_histogram_counts_sum_to_complete_cases(
    load_pinned_values: Any,
    eda_pipeline: dict[str, Any],
) -> None:
    """Bind the figure-caption invariant: bin counts sum to complete-case rows."""

    pinned = load_pinned_values("template_eda_notebook")
    entry = _pin(pinned, "height_histogram_counts_sum")

    hist = histogram_data(eda_pipeline["cleaned"], "height_cm", bins=10)
    counts_sum = int(sum(hist.counts))

    # The invariant is that the pinned sum equals the complete-case row count.
    assert counts_sum == int(eda_pipeline["report"].rows_out)
    _assert_pin_matches(entry, counts_sum)


def test_pin_mutation_negative_control_fails(load_pinned_values: Any) -> None:
    """Changing a committed pin must fail the comparison predicate.

    This is the non-vacuity control: if it passed, the assertions above would
    prove nothing. Mutating the pinned value away from the observed value must
    break ``_assert_pin_matches``.
    """

    pinned = load_pinned_values("template_eda_notebook")
    entry = dict(_pin(pinned, "missingness_rows_dropped"))
    observed = entry["value"]
    entry["value"] = observed + 1

    with pytest.raises(AssertionError):
        _assert_pin_matches(entry, observed)
