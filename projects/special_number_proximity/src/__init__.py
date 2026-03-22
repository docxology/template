"""Proximity of special real numbers to rationals with bounded denominator."""

from cf_distance import min_distance_among_convergents
from constants import NamedConstant, NumberClass, constant_lookup, named_constants
from continued_fractions import (
    continued_fraction_exact_positive_rational,
    continued_fraction_terms,
    convergents,
    value_from_convergent,
)
from diophantine_bounds import (
    dirichlet_pigeonhole_upper_bound,
    distance_to_nearest_integer,
    max_integer_residual_over_q,
    min_rational_distance_via_scaled_lattice,
)
from rational_distance import (
    min_q_squared_error,
    min_rational_distance,
    min_rational_distance_fractional,
    min_rational_distance_mod1,
    rational_at_min_distance,
    rational_at_min_q_squared_error,
)
from sampling import (
    beta_unit_samples,
    quadratic_irrationals,
    random_quadratic_mod1,
    uniform_unit_samples,
)
from statistics_compare import (
    batch_min_q_squared_errors,
    batch_min_rational_distances,
    compare_constant_table,
    empirical_percentile_rank,
    empirical_percentile_rank_midrank,
    reference_distribution_summary,
    reference_percentiles,
    summarize_vs_reference,
)

__all__ = [
    "NamedConstant",
    "NumberClass",
    "batch_min_q_squared_errors",
    "batch_min_rational_distances",
    "beta_unit_samples",
    "compare_constant_table",
    "constant_lookup",
    "continued_fraction_exact_positive_rational",
    "continued_fraction_terms",
    "convergents",
    "dirichlet_pigeonhole_upper_bound",
    "distance_to_nearest_integer",
    "empirical_percentile_rank",
    "empirical_percentile_rank_midrank",
    "max_integer_residual_over_q",
    "min_distance_among_convergents",
    "min_q_squared_error",
    "min_rational_distance",
    "min_rational_distance_fractional",
    "min_rational_distance_mod1",
    "min_rational_distance_via_scaled_lattice",
    "named_constants",
    "quadratic_irrationals",
    "random_quadratic_mod1",
    "rational_at_min_distance",
    "rational_at_min_q_squared_error",
    "reference_distribution_summary",
    "reference_percentiles",
    "summarize_vs_reference",
    "uniform_unit_samples",
    "value_from_convergent",
]
