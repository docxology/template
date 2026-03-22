# src/ — API summary

## `continued_fractions`

- `continued_fraction_terms(x, max_terms=64, tol=1e-14) -> list[int]`
- `continued_fraction_exact_positive_rational(p, q) -> list[int]`
- `convergents(terms) -> Iterator[tuple[int,int]]`
- `value_from_convergent(p, q) -> float`

## `rational_distance`

- `rational_at_min_distance(x, q_max) -> tuple[float,int,int]`
- `min_rational_distance(x, q_max) -> float`
- `rational_at_min_q_squared_error(x, q_max) -> tuple[float,int,int]` — minimises $q^2|x-p/q|$
- `min_q_squared_error(x, q_max) -> float`
- `min_rational_distance_fractional(x, q_max) -> float`
- `min_rational_distance_mod1(x, q_max) -> float | None`

## `cf_distance`

- `min_distance_among_convergents(x, q_max, max_terms=96) -> tuple[float,int,int]` — convergents only; $\geq \delta_Q$

## `diophantine_bounds`

- `distance_to_nearest_integer(y) -> float`
- `min_rational_distance_via_scaled_lattice(x, q_max) -> float`
- `dirichlet_pigeonhole_upper_bound(q_max) -> float`
- `max_integer_residual_over_q(x, q_max) -> float`

## `constants`

- `NumberClass`, `NamedConstant`, `named_constants()`, `constant_lookup()`

## `sampling`

- `uniform_unit_samples`, `beta_unit_samples`, `quadratic_irrationals`, `random_quadratic_mod1`

## `statistics_compare`

- `batch_min_rational_distances(values, q_max, implementation="auto"|"vectorized"|"scalar")`
- `batch_min_q_squared_errors(values, q_max, implementation=...)`
- `reference_percentiles(distances, levels=...) -> dict`
- `reference_distribution_summary(reference) -> dict` (includes `p05`, `p95`, …)
- `empirical_percentile_rank`, `empirical_percentile_rank_midrank`
- `summarize_vs_reference(..., reference_q_squared=None, use_fractional_part=False)`
- `compare_constant_table(..., reference_q_squared=None, use_fractional_part=False)`
