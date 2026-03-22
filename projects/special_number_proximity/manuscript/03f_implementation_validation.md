# Implementation validation

## Three-numerator lemma

Fix $q$ and real $x$. The function $p \mapsto |x - p/q|$ is convex along the integer line; its minimum over $\mathbb{Z}$ occurs at $p_0 = \mathrm{round}(qx)$, and only $p_0-1$, $p_0$, and $p_0+1$ can beat other integers. The same remark applies to $q^2|x-p/q|$ for fixed $q$. Hence the loops in `rational_distance.py` are exhaustive over $p$ at each $q \leq Q$.

## Brute-force regression tests

The suite `tests/test_rational_distance_exhaustive.py` compares the scan to a full enumeration of admissible $p$ for random $x \in [0,1)$ and $Q \leq 30$. Agreement holds in IEEE-754 double arithmetic at stated tolerances.

## Continued-fraction cross-check

`cf_distance.min_distance_among_convergents` minimises $|x-p/q|$ over **convergents only** (no semiconvergents). For fixed $Q$ this value is always at least the true $\delta_Q(x)$; tests in `tests/test_cf_distance.py` check near-equality for quadratic irrationals at Fibonacci denominators and global inequality for $\pi$.

## Scaled-lattice identity

`diophantine_bounds.min_rational_distance_via_scaled_lattice` recomputes $\delta_Q$ as $\min_q \|qx\|/q$. It matches `min_rational_distance` on a grid of $(x,Q)$ in unit tests; `scripts/02_lattice_crosscheck.py` exports a small JSON witness under `output/data/lattice_crosscheck.json`.

## Vectorised batch parity

`statistics_compare.batch_min_rational_distances` defaults to a vectorised three-$p$ inner loop; `tests/test_batch_implementation_parity.py` asserts bitwise agreement with the scalar path on random batches.

## Floating-point scope

All constants use C doubles. Extremely large partial quotients in a continued fraction can be truncated early; the convergent cross-check is therefore diagnostic, not a substitute for semiconvergent theory at arbitrary $Q$.
