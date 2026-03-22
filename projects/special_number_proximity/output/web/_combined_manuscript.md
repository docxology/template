# Abstract

We quantify how close fixed mathematical constants lie to rationals $p/q$ with bounded denominator $q \leq Q$, and contrast them against Monte Carlo draws from reference ensembles on $[0,1)$ and from fractional parts of square roots. The statistic is the elementary minimum absolute error $\min_{p \in \mathbb{Z},\,1 \leq q \leq Q} |x - p/q|$, evaluated in IEEE-754 double precision with deterministic seeds. Classical Diophantine theory (Dirichlet, Hurwitz, Khinchin) explains why almost every real admits arbitrarily sharp rational approximations as $Q \to \infty$; here we fix modest $Q$ and compare empirical tail placement of named constants (including a rational control) relative to synthetic baselines. All computation lives in `projects/special_number_proximity/src/` with a zero-mock test suite; figures and tables are produced by `scripts/proximity_monte_carlo.py`.

**Keywords:** Diophantine approximation, continued fractions, Monte Carlo methods, reproducible computing



---



# Introduction

Rational numbers are dense in the reals, yet the *quality* of the best approximation at a fixed denominator ceiling varies sharply across individual $x$. Number theory classifies extremes: algebraic irrationals of degree two have bounded partial quotients in their continued fraction expansion (hence are *badly approximable*), while almost every $x$ satisfies Khinchin-type statistics for the growth of those quotients [@khinchin1964continued]. Transcendental numbers carry no algebraic constraint of that form, but individual constants such as $\pi$ or $e$ still exhibit structured rational approximations arising from truncated series or independent constructions.

This note does not prove new bounds. It implements a transparent, test-backed pipeline that measures a single finite-$Q$ statistic for several standard constants and compares each value to the distribution induced by simple random constructions. The goal is pedagogical and methodological: link classical statements about limits as $Q\to\infty$ to observable finite-$Q$ variation, and document the measurement chain so others can change $Q$, the reference law, or the constant registry without touching infrastructure code.



---



# Problem statement

Fix an integer $Q \geq 1$. For a real $x$, define
\begin{equation}
\label{eq:delta}
\delta_Q(x) = \min_{p \in \mathbb{Z},\, 1 \leq q \leq Q} \left| x - \frac{p}{q} \right|.
\end{equation}

For analysis on the circle group $\mathbb{R}/\mathbb{Z}$ one often studies the fractional part $\{x\}$ and the same functional with $x$ replaced by $\{x\}$; the implementation exposes both the raw distance on $\mathbb{R}$ and the fractional variant used when comparing draws supported on $[0,1)$.

**Research question (statistical).** Conditional on a chosen reference law for $X$ (uniform on $[0,1)$, or fractional parts $\{\sqrt{k}\}$ with random square-free $k$), where do deterministic constants $x^\star$ sit in the empirical distribution of $\delta_Q(X)$? Equivalently: what empirical percentile does $\delta_Q(x^\star)$ attain relative to Monte Carlo samples at the same $Q$?

**Rational control.** Any $x \in \mathbb{Q}$ yields $\delta_Q(x)=0$ once $Q$ exceeds the reduced denominator of $x$, providing a structural sanity check on the implementation.



---



# Measure-theoretic context (qualitative)

## Almost every number is well approximable

Dirichlet's theorem guarantees that for every irrational $x$ and every $Q>1$ there exist integers $p,q$ with $1 \leq q \leq Q$ and $|qx - p| < 1/Q$, hence $|x - p/q| < 1/qQ \leq 1/Q$. Thus $\delta_Q(x) \leq 1/Q$ always for irrational $x$; the interesting variation is sub-leading in $Q$.

## Badly approximable numbers

An irrational $x$ is *badly approximable* if there exists $c>0$ such that $|x - p/q| > c/q^2$ for all rationals $p/q$. Equivalently, the partial quotients in the continued fraction expansion of $x$ are bounded. Quadratic irrationals, including the golden ratio $\varphi$, belong to this class [@cassels1957]. At fixed $Q$, such numbers tend to sit in less extreme left tails of $\delta_Q$ than typical draws from uniform $[0,1)$—they resist *especially* close low-denominator hits.

## What transcendence does not encode at fixed $Q$

Being transcendental rules out exact satisfaction of a nontrivial integer polynomial, but it does not by itself determine $\delta_Q(x)$ at moderate $Q$ in double precision. Empirical comparison against random baselines therefore remains informative for exposition even when classical transcendentality proofs are orthogonal to the statistic \eqref{eq:delta}.



---



# Continued fractions as an explanatory tool

The source module `continued_fractions.py` exposes partial quotients $[a_0; a_1, a_2, \ldots]$ for positive floats and exact Euclidean continued fractions for positive rationals $p/q$. Convergents $p_k/q_k$ satisfy the recurrence
\begin{align}
p_k &= a_k p_{k-1} + p_{k-2}, \\
q_k &= a_k q_{k-1} + q_{k-2},
\end{align}
initialized by $(p_{-1},q_{-1})=(1,0)$, $(p_0,q_0)=(a_0,1)$ in the standard indexing shift used in code.

For $\varphi = (1+\sqrt{5})/2$, one expects $a_i=1$ for all $i \geq 1$ under exact arithmetic; floating expansion truncates once rounding breaks the fixed point of the Gauss map.

The statistic $\delta_Q(x)$ in \eqref{eq:delta} is computed independently by scanning denominators $1 \leq q \leq Q$ and three candidate numerators around $xq$; this $O(Q)$ method is exact for double-$x$ at the stated grid and is simpler to test than full semiconvergent enumeration while remaining adequate for the Monte Carlo scales used here.



---



# Monte Carlo design

## Reference samples

The analysis script `proximity_monte_carlo.py` draws:

1. **Uniform baseline:** $U_1,\ldots,U_n \sim \mathrm{Unif}(0,1)$.
2. **Quadratic fractional baseline:** values $\{\sqrt{k}\}$ for $k$ sampled with replacement from a fixed list of small square-free integers.
3. **Optional Beta baseline:** if `experiment.n_beta > 0`, additional draws $B_i \sim \mathrm{Beta}(a,b)$ on $(0,1)$ (parameters `beta_a`, `beta_b`, default $1/2$, $1/2$) are included to stress U-shaped or boundary-heavy laws.

All streams share one NumPy `Generator` seeded from `manuscript/config.yaml` (`experiment.rng_seed`). Distances $\delta_Q$ are concatenated into a pooled reference; JSON output includes `reference_summary` (count, mean, selected quantiles) for quick tables.

## Constants

`constants.py` registers $\pi$, $e$, $\sqrt{2}$, $\sqrt{3}$, $\varphi$, $\ln 2$, and $1/6$ (rational control). Labels such as `transcendental` versus `irrational_algebraic` are documentary; proofs are not recomputed in software.

## Outputs

Structured JSON and CSV land in `output/data/`; a log-scale histogram of the uniform baseline with vertical markers for selected constants is written to `output/figures/proximity_histogram.png`.

A second script, `02_lattice_crosscheck.py`, writes `output/data/lattice_crosscheck.json` comparing brute-force $\delta_Q$ to the scaled-lattice formulation and recording Dirichlet residual checks.

Parameters `q_max`, `n_uniform`, `n_quadratic`, `n_beta`, `beta_a`, and `beta_b` are YAML-configurable to respect the template’s reproducibility contract without code edits.



---



# Scaled lattice and Dirichlet residual

## Identity

For $q \in \mathbb{N}$ and $x \in \mathbb{R}$, write $\|y\| := \mathrm{dist}(y,\mathbb{Z})$. Choosing $p = \mathrm{round}(qx)$ minimises $|qx - p|$, hence

$$
\left|x - \frac{p}{q}\right| = \frac{\|qx\|}{q}.
$$

Therefore the bounded-denominator functional from `02_problem_statement.md` satisfies

$$
\delta_Q(x) = \min_{1 \leq q \leq Q} \frac{\|qx\|}{q}.
$$

The implementation `min_rational_distance_via_scaled_lattice` in `diophantine_bounds.py` evaluates this form; it agrees with the brute-force search in `rational_distance.py` for every tested pair $(x,Q)$ (see `output/data/lattice_crosscheck.json` from `02_lattice_crosscheck.py`).

## Pigeonhole bound on the integer residual

The classical box argument shows that for each $Q \geq 1$ there exists $q \in \{1,\ldots,Q\}$ with $\|qx\| \leq 1/(Q+1)$ [@cassels1957]. This controls the **numerator** $\|qx\|$ only; dividing by $q$ to compare with $\delta_Q(x)$ requires the separate optimisation above.

## Relation to continued fractions

Continued-fraction convergents supply excellent rational approximations but need not attain $\delta_Q(x)$ for a fixed $Q$ without semiconvergents; `cf_distance.py` documents the convergent-only lower envelope used for quick certificates.



---



# $q^2$ error scale (Lagrange / Hurwitz viewpoint)

For integers $p,q$ with $q \geq 1$, define the **weighted** error
\begin{equation}
\label{eq:lagrange}
\mu_Q(x) = \min_{1 \leq q \leq Q}\ \min_{p \in \mathbb{Z}}\ q^2 \left| x - \frac{p}{q} \right|.
\end{equation}

For fixed $q$, the inner minimum is attained at $p = \mathrm{round}(qx)$, so the implementation checks the same three candidates per $q$ as for $\delta_Q(x)$ in `02_problem_statement.md`. The factor $q^2$ makes $\mu_Q$ dimensionless in the sense used in Hurwitz-type theorems: for infinitely many convergents one has $q^2|x - p/q| < 1$, and for every irrational $x$ there are infinitely many pairs with $q^2|x-p/q| < 1/\sqrt{5}$ [@hurwitz1891].

At **finite** $Q$, $\mu_Q(x)$ ranks how small a single rational hit is relative to its denominator height. The Monte Carlo pipeline records both $\delta_Q$ and $\mu_Q$ for named constants and for the pooled reference sample (`min_q_squared_error` and `reference_q_squared_summary` in `output/data/proximity_summary.json`).



---



# Implementation validation

## Three-numerator lemma

Fix $q$ and real $x$. The function $p \mapsto |x - p/q|$ is convex along the integer line; its minimum over $\mathbb{Z}$ occurs at $p_0 = \mathrm{round}(qx)$, and only $p_0-1$, $p_0$, and $p_0+1$ can beat other integers. The same remark applies to $q^2|x-p/q|$ for fixed $q$. Hence the loops in `rational_distance.py` are exhaustive over $p$ at each $q \leq Q$.

## Brute-force regression tests

The suite `tests/test_rational_distance_exhaustive.py` compares the scan to a full enumeration of $p \in \{0,\ldots,q\}$ for random $x \in [0,1)$ and $Q \leq 30$. Agreement holds in IEEE-754 double arithmetic at the stated tolerances.

## Continued-fraction cross-check

`cf_distance.min_distance_among_convergents` minimises $|x-p/q|$ over **convergents only** (no semiconvergents). For fixed $Q$ this value is always at least the true $\delta_Q(x)$; tests in `tests/test_cf_distance.py` check near-equality for quadratic irrationals at Fibonacci denominators and global inequality for $\pi$.

## Scaled-lattice identity

`diophantine_bounds.min_rational_distance_via_scaled_lattice` recomputes $\delta_Q$ as $\min_q \|qx\|/q$. It matches `min_rational_distance` on a grid of $(x,Q)$ in tests; `scripts/02_lattice_crosscheck.py` exports a small JSON witness under `output/data/lattice_crosscheck.json`.

## Floating-point scope

All constants use `float` (typically C doubles). Extremely large partial quotients in a continued fraction can be truncated early; the convergent cross-check is therefore diagnostic, not a proof tactic for arbitrary $Q$.



---



# Results

Regenerate `output/data/proximity_summary.json` and figures with `uv run python projects/special_number_proximity/scripts/proximity_monte_carlo.py` (or `./run.sh` analysis stage). Defaults match `manuscript/config.yaml`: `q_max=120`, pooled uniform + quadratic + Beta samples, seed `20260322`.

## Distribution summaries

The JSON fields `reference_summary` and `reference_q_squared_summary` report count, mean, min/max, quartiles, and tail percentiles (`p05`, `p95`) for $\delta_Q$ and $\mu_Q$ on the **pooled** reference. Each row in `constants` includes:

- `min_distance`, `empirical_percentile_rank`
- `min_q_squared_error`, `empirical_percentile_rank_q_squared`
- `use_fractional_part` (mirrors `experiment.compare_mod1`)

When `q_sensitivity` is set, the block `q_sensitivity` repeats constant tables at additional $Q$ values on the **same** pooled abscissa (only the functional changes).

## Empirical percentiles of $\delta_{120}(x^\star)$ (illustrative)

| Constant | $\delta_{120}(x^\star)$ | pooled rank | $\mu_{120}(x^\star)$ |
|----------|-------------------------|-------------|----------------------|
| `one_sixth` | $0$ | $0$ | $0$ |
| `pi` | $\approx 2.67\times 10^{-7}$ | left tail | see JSON |
| `e` | $\approx 2.80\times 10^{-5}$ | mid | see JSON |
| `golden_ratio` | $\approx 5.65\times 10^{-5}$ | near median | see JSON |
| `sqrt2`, `sqrt3`, `ln2` | — | — | — |

Replace the middle columns with the latest CSV/JSON after each run; $\pi$ at $Q=120$ remains an extreme left-tail outlier for $\delta_Q$ because of excellent low-height approximants (e.g. $355/113$).

## Figures

Figure \ref{fig:proximity_hist}: uniform reference subsample, markers at selected constants (fractional part when `compare_mod1` is true).

![Uniform reference log histogram.](../output/figures/proximity_histogram.png){#fig:proximity_hist}

Figure \ref{fig:proximity_pooled}: uniform plus quadratic-mod-$1$ subsample for contrast.

![Pooled reference log histogram (subsample).](../output/figures/proximity_histogram_pooled.png){#fig:proximity_pooled}

## Related checks

Lattice vs brute-force agreement is recorded in `output/data/lattice_crosscheck.json` from `scripts/02_lattice_crosscheck.py`.



---



# Conclusion

Finite-$Q$ rational proximity is a coarse lens: it rewards numbers that admit unusually accurate low-height approximations, not “randomness” in a probabilistic sense. Reporting both $\delta_Q$ and the scaled statistic $\mu_Q$ (`03e_q_squared_quality.md`) separates raw closeness from denominator-weighted quality. At $Q=120$, $\pi$ is a visible outlier in $\delta_Q$ relative to uniform draws, while the golden ratio often sits nearer the median of the pooled reference—consistent with a badly approximable, bounded-quotient profile at the level of heuristics. Optional `q_sensitivity` in `config.yaml` stress-tests the same reference draws at multiple ceilings. The pipeline is modular (`continued_fractions`, `rational_distance`, `diophantine_bounds`, `cf_distance`, `sampling`, `statistics_compare`), tested without mocks (`docs/testing_philosophy.md`), and parameterized from YAML.



---



# Reproducibility

## Software

- Python $\geq 3.10$, NumPy, Matplotlib, PyYAML (declared in `projects/special_number_proximity/pyproject.toml`; root `uv sync` supplies the environment).
- Tests: `uv run pytest projects/special_number_proximity/tests/ --cov=projects/special_number_proximity/src --cov-fail-under=90`.

## Regenerating artifacts

```bash
uv run python projects/special_number_proximity/scripts/proximity_monte_carlo.py
# Optional: alternate project root (e.g. temporary checkout)
uv run python projects/special_number_proximity/scripts/proximity_monte_carlo.py --project-dir /path/to/projects/special_number_proximity
```

Edits to `manuscript/config.yaml` under `experiment:` change seeds, sample sizes, `q_max`, `quadratic_candidates`, `compare_mod1`, `q_sensitivity`, and histogram caps without editing Python.

## Data paths

| Artifact | Path |
|----------|------|
| Summary JSON | `projects/special_number_proximity/output/data/proximity_summary.json` |
| Table CSV | `projects/special_number_proximity/output/data/proximity_constants.csv` |
| Uniform histogram | `projects/special_number_proximity/output/figures/proximity_histogram.png` |
| Pooled histogram | `projects/special_number_proximity/output/figures/proximity_histogram_pooled.png` |
| Lattice cross-check | `projects/special_number_proximity/output/data/lattice_crosscheck.json` |

Run `uv run python projects/special_number_proximity/scripts/02_lattice_crosscheck.py` to refresh the lattice JSON.



---



# Limitations

- **Fixed $Q$:** The statistic $\delta_Q$ and the scaled variant $\mu_Q$ (\eqref{eq:lagrange} in `03e_q_squared_quality.md`) are evaluated at a single ceiling (or a short list via `experiment.q_sensitivity` in `config.yaml`). They do not describe the full Diophantine type of a number as $Q \to \infty$.

- **Reference law:** Empirical percentiles depend on the mixture of Uniform$(0,1)$, quadratic-mod-$1$, and optional Beta draws. Changing `quadratic_candidates` or sample sizes shifts the pooled CDF; `compare_mod1: true` re-expresses constants on $[0,1)$ for a fairer comparison to uniform reference.

- **Labels:** `NumberClass` tags in `constants.py` are documentary; the code does not certify transcendence or algebraicity.

- **Convergent-only helper:** `min_distance_among_convergents` can exceed $\delta_Q$ when a semiconvergent beats every convergent with $q \leq Q$.

- **Outputs:** Figures subsample for speed (`histogram_uniform_cap`); tables in the JSON use the full pooled sample counts from `n_uniform`, `n_quadratic`, and `n_beta`.



---



# Manuscript syntax

- Citations: `[@khinchin1964continued]`; keys must exist in `references.bib`.
- Equations: use `\begin{equation}` / `\label{eq:...}`; reference with `\ref{eq:...}`.
- Figures: e.g. `![caption](../output/figures/proximity_histogram.png){#fig:label}` or `proximity_histogram_pooled.png`; then `\ref{fig:label}` in prose.

See `infrastructure/rendering` for Pandoc and crossref details.
