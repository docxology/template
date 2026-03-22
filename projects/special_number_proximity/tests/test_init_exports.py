"""Load ``src/__init__.py`` explicitly for coverage of re-exports."""

import importlib.util
from pathlib import Path


def test_init_module_executes() -> None:
    path = Path(__file__).resolve().parent.parent / "src" / "__init__.py"
    spec = importlib.util.spec_from_file_location("_snp_init", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "compare_constant_table")
    assert hasattr(mod, "continued_fraction_exact_positive_rational")
    assert hasattr(mod, "min_rational_distance_via_scaled_lattice")
    assert hasattr(mod, "min_distance_among_convergents")
    assert hasattr(mod, "beta_unit_samples")
    assert hasattr(mod, "reference_distribution_summary")
    assert hasattr(mod, "batch_min_q_squared_errors")
    assert hasattr(mod, "reference_percentiles")
    assert hasattr(mod, "min_q_squared_error")
