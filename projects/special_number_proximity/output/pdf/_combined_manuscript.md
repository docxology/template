# Abstract

We quantify how close fixed mathematical constants lie to rationals $p/q$ with bounded denominator $q \leq Q$, and contrast them against Monte Carlo draws from a **pooled reference** on $[0,1)$: uniform samples, fractional parts $\{\sqrt{k}\}$ for square-free $k$ from a fixed list, and (when configured) independent $\mathrm{Beta}(a,b)$ draws. The primary statistic is the elementary minimum absolute error
\[
\delta_Q(x) = \min_{p \in \mathbb{Z},\, 1 \leq q \leq Q} \left| x - \frac{p}{q} \right|,
\]
evaluated in IEEE-754 double precision with a deterministic pseudorandom seed. A companion scale
\[
\mu_Q(x) = \min_{1 \leq q \leq Q}\ \min_{p \in \mathbb{Z}} q^2 \left| x - \frac{p}{q} \right|
\]
records the same best hit weighted by $q^2$, in the spirit of Lagrange–Hurwitz quality measures.

Classical Diophantine theory explains asymptotic behaviour as $Q \to \infty$: Dirichlet's principle forces $\delta_Q(x) \lesssim 1/Q$ for irrationals, Khinchin-type results describe typical continued-fraction statistics, and badly approximable numbers (bounded partial quotients, including quadratic irrationals such as the golden ratio) resist unusually sharp low-height approximations [@khinchin1964continued; @cassels1957]. Here we **fix modest $Q$** and report where named constants sit in the empirical distribution of $\delta_Q(X)$ and $\mu_Q(X)$ relative to the synthetic baselines—together with optional **multi-$Q$ sensitivity** on the *same* pooled abscissa.

The contribution is pedagogical and computational: a transparent, test-backed pipeline (`projects/special_number_proximity/src/`, zero-mock tests) links limit theorems to observable finite-$Q$ variation. Figures and tabular summaries are produced by `scripts/proximity_monte_carlo.py` from `manuscript/config.yaml`.

**Keywords:** Diophantine approximation, continued fractions, Monte Carlo methods, reproducible computing



```{=latex}
\newpage
```


# Introduction

Rational numbers are dense in the reals, yet the **quality** of the best rational approximation at a fixed denominator ceiling varies sharply across individual $x$. Number theory classifies extremes: algebraic irrationals of degree two have bounded partial quotients in their continued fraction expansion and are *badly approximable* in the sense of [@cassels1957]; almost every $x \in \mathbb{R}$ satisfies Khinchin-type statistics for the growth of those quotients [@khinchin1964continued]. Transcendental constants carry no finite-degree algebraic constraint, but particular numbers such as $\pi$ or $e$ still admit **structured** rational approximations from series, integrals, or independent constructions—so their finite-$Q$ behaviour need not resemble a “generic” draw from a simple continuous law.

### Finite $Q$ as a deliberate lens

As $Q$ grows, $\delta_Q(x)$ tends to $0$ for every irrational $x$, and $\mu_Q(x)$ admits universal upper bounds tied to continued-fraction convergents [@hurwitz1891]. Those limits wash out differences on a logarithmic scale unless one studies **rates** or **exceptional sets**. By contrast, fixing $Q$ at a moderate value (for example $Q=120$ in the default configuration) asks a different question: *among all rationals with denominators up to $Q$, how small is the best error, and how does that single number compare to the same functional evaluated on random $X$?* The answer is a **scalar summary**—an empirical percentile relative to a chosen reference law—not a Diophantine *type* in the classical sense.

### Statistical comparison protocol

The implementation draws a pooled sample $X_1,\ldots,X_n$ on $[0,1)$, computes $\delta_Q(X_i)$ and $\mu_Q(X_i)$ for each draw, and records distribution summaries (quantiles, tail percentiles). For each registered constant $x^\star$ it stores $\delta_Q(x^\star)$, $\mu_Q(x^\star)$, and the **empirical rank** (proportion of reference samples strictly below the constant's value). Optional `experiment.q_sensitivity` repeats the constant table at additional $Q$ values **without resampling** $X$, so shifts in rank isolate the effect of enlarging the rational search set.

### Scope of this note

We do not prove new Diophantine bounds. The goal is **methodological**: connect classical statements about $Q\to\infty$ to concrete finite-$Q$ measurements, document the numerical chain (three-numerator scan, lattice cross-checks, convergent-only certificates), and parameterize the study from YAML so $Q$, sample sizes, reference components, and `compare_mod1` can change without editing infrastructure code.



```{=latex}
\newpage
```


# Problem statement

Fix an integer $Q \geq 1$. For a real $x$, define
\begin{equation}
\label{eq:delta}
\delta_Q(x) = \min_{p \in \mathbb{Z},\, 1 \leq q \leq Q} \left| x - \frac{p}{q} \right|.
\end{equation}

The minimum exists because for each $q$ the optimal numerator is one of three integers around $qx$ (convexity of $p \mapsto |x-p/q|$ along $\mathbb{Z}$), so the search over $p$ at fixed $q$ reduces to checking $p_0-1,p_0,p_0+1$ with $p_0=\mathrm{round}(qx)$. Enumerating $q=1,\ldots,Q$ yields an $O(Q)$ exact procedure in floating-point arithmetic at the stated grid.

### Circle formulation

For analysis on $\mathbb{R}/\mathbb{Z}$ one often studies the fractional part $\{x\}$ and replaces $x$ by $\{x\}$ in \eqref{eq:delta} when comparing to laws supported on $[0,1)$. The codebase exposes both the raw distance on $\mathbb{R}$ and the fractional variant when `experiment.compare_mod1` is true in `manuscript/config.yaml`.

### Statistical question

**Research question (statistical).** Conditional on a chosen reference law for $X$ (here: a mixture of $\mathrm{Unif}(0,1)$, fractional parts $\{\sqrt{k}\}$ with $k$ sampled from a fixed square-free list, and optionally $\mathrm{Beta}(a,b)$ with parameters from config), where do deterministic constants $x^\star$ sit in the empirical distribution of $\delta_Q(X)$? Equivalently: what empirical percentile does $\delta_Q(x^\star)$ attain relative to Monte Carlo samples at the same $Q$? The same question applies to $\mu_Q$ when reporting denominator-weighted quality (\eqref{eq:lagrange} in `03e_q_squared_quality.md`).

### Rational control

Any $x \in \mathbb{Q}$ yields $\delta_Q(x)=0$ once $Q$ is at least the reduced denominator of $x$, and $\mu_Q(x)=0$ simultaneously. The registry includes `one_sixth` as a **structural sanity check** on the implementation and on floating-point idempotence of the scan.

### Outputs

For each run, structured JSON records reference summaries, per-constant distances, ranks, and optional `q_sensitivity` blocks; CSV mirrors the primary constant table. Histograms (uniform subsample, pooled subsample, and $\mu_Q$ on the pooled subsample) are written under `../figures/` for visual comparison of tail placement.



```{=latex}
\newpage
```


# Measure-theoretic context (qualitative)

## Almost every number admits sharp approximations

Dirichlet's theorem (pigeonhole principle on fractional parts; see [@cassels1957]) implies that for every irrational $x$ and every $Q>1$ there exist integers $p,q$ with $1 \leq q \leq Q$ and $|qx-p|<1/Q$, hence
\[
\left|x-\frac{p}{q}\right| < \frac{1}{qQ} \leq \frac{1}{Q}.
\]
So $\delta_Q(x) \leq 1/Q$ always for irrational $x$; the **leading** scale is universal. The interesting structure at moderate $Q$ lies in **how much smaller** than $1/Q$ the minimum can be—left-tail behaviour of $\delta_Q(X)$ under a reference law—and in the **relative** placement of named constants inside that tail.

## Badly approximable numbers

An irrational $x$ is *badly approximable* if there exists $c>0$ such that $|x-p/q|>c/q^2$ for all rationals $p/q$. Equivalently, the partial quotients in the continued fraction expansion of $x$ are bounded. Quadratic irrationals, including the golden ratio $\varphi=(1+\sqrt{5})/2$, belong to this class. Heuristically, such numbers **avoid** exceptionally accurate low-height rationals: at fixed $Q$ they often sit closer to the **bulk** of $\delta_Q(X)$ than do numbers that admit a stellar approximant with $q\leq Q$ (e.g. $\pi$ near $355/113$ when $Q\ge 113$).

## Transcendence versus fixed-$Q$ floating-point measurement

Being transcendental excludes exact roots of nontrivial integer polynomials, but it does **not** determine $\delta_Q(x)$ at moderate $Q$ in double precision. Empirical comparison against synthetic baselines therefore remains a useful **expository** device: it shows how a single outstanding rational hit shifts percentiles even when classical transcendentality proofs are orthogonal to \eqref{eq:delta}.

## Relation to the pooled reference

The Monte Carlo pipeline does not sample from Haar measure on $\mathbb{R}/\mathbb{Z}$ in a measure-theoretic sense; it mixes simple laws on $[0,1)$ chosen for reproducibility and interpretability. Percentiles are **always conditional** on that mixture. Changing `experiment.n_uniform`, `n_quadratic`, `n_beta`, or `quadratic_candidates` shifts the empirical CDF; `compare_mod1: true` aligns constants with $[0,1)$ when comparing primarily to the uniform component.



```{=latex}
\newpage
```


# Continued fractions as an explanatory tool

The project module `src/continued_fractions.py` exposes partial quotients $[a_0; a_1, a_2, \ldots]$ for positive floats and exact Euclidean continued fractions for positive rationals $p/q$. Convergents $p_k/q_k$ satisfy the recurrence
\begin{align}
p_k &= a_k p_{k-1} + p_{k-2}, \\
q_k &= a_k q_{k-1} + q_{k-2},
\end{align}
initialized by $(p_{-1},q_{-1})=(1,0)$, $(p_0,q_0)=(a_0,1)$ in the indexing convention used in code.

For $\varphi = (1+\sqrt{5})/2$, exact arithmetic gives $a_i=1$ for all $i \geq 1$; in `float`, the expansion truncates once rounding breaks the fixed point of the Gauss map. That truncation is expected and is why continued-fraction output is treated as **diagnostic**, not as a proof instrument for large heights.

## Why $\delta_Q$ is not computed from convergents alone

The true finite-$Q$ optimum in \eqref{eq:delta} can be attained by a **semiconvergent**—a rational intermediate between two convergents—that beats every convergent with $q\leq Q$. The helper `cf_distance.min_distance_among_convergents` therefore returns a value **at least** $\delta_Q(x)$; tests document near-equality for well-behaved quadratics at Fibonacci denominators and strict inequality for $\pi$ at some $Q$.

## Implementation choice: three-$p$ scan per $q$

The statistic $\delta_Q(x)$ is computed by scanning denominators $1 \leq q \leq Q$ and three candidate numerators around $qx$. This $O(Q)$ method is exact for double-$x$ at the stated grid, is simpler to test exhaustively than full semiconvergent enumeration, and matches the vectorised batch path in `statistics_compare.py` bit-for-bit on regression suites.

## Reading continued fractions alongside histograms

When a constant's vertical marker on the $\log_{10}\delta_Q$ histogram sits far left of the pooled bulk, one practical explanation is a **small-$q$ excellent approximant** visible as a large partial quotient early in the expansion. Conversely, badly approximable profiles correlate with **bounded** quotients and less extreme left-tail $\delta_Q$ at moderate $Q$—always contingent on the actual rational with $q\leq Q$ that achieves the minimum.



```{=latex}
\newpage
```


# Monte Carlo design

## Reference samples (pooled abscissa)

The analysis script `proximity_monte_carlo.py` builds a single pooled array $X$ on $[0,1)$ from three independent components, all driven by one NumPy `Generator` seeded by `experiment.rng_seed` in `manuscript/config.yaml`:

1. **Uniform baseline:** $U_1,\ldots,U_{n_{\mathrm{u}}} \sim \mathrm{Unif}(0,1)$.
2. **Quadratic fractional baseline:** values $\{\sqrt{k}\}$ (fractional part after reduction mod $1$ in the sampling helper) for $k$ sampled with replacement from `experiment.quadratic_candidates` (default square-free integers up to $19$ excluding squares).
3. **Beta baseline:** when `experiment.n_beta > 0`, additional draws $B_i \sim \mathrm{Beta}(a,b)$ with parameters `beta_a`, `beta_b` from config. The repository default sets $n_{\mathrm{beta}}=1000$ with $a=b=1/2$ (arcsine-type law), which concentrates mass near $0$ and $1$ and **thickens the mixture tails** relative to uniform-only sampling.

Distances $\delta_Q(X_i)$ and $\mu_Q(X_i)$ are computed for **every** pooled draw. JSON output includes `reference_summary` and `reference_q_squared_summary` (count, mean, min/max, quartiles, `p05`, `p95`) for the full pooled sample, plus `reference_combined_n`.

## Constants registry

`src/constants.py` registers $\pi$, $e$, $\sqrt{2}$, $\sqrt{3}$, $\varphi$, $\ln 2$, and $1/6$ (rational control). `NumberClass` tags are **documentary**; the code does not certify transcendence or algebraicity.

## Multi-$Q$ sensitivity

When `experiment.q_sensitivity` lists integers (default `[30, 60, 120]` alongside `q_max=120`), the JSON gains a `q_sensitivity` object keyed by $Q$. For each key, reference summaries and constant tables are recomputed on the **same** pooled $X$; only the functional $\delta_Q$ (and $\mu_Q$) changes. This isolates the effect of enlarging the rational search set from resampling noise.

## Histograms versus tables

Tables and percentiles use the **full** pooled counts (`n_uniform + n_quadratic + n_beta`). Figures use a **visualisation subsample** capped by `histogram_uniform_cap`: uniform draws truncated to the cap, plus a quadratic stream sized relative to the cap (see script), **excluding** Beta draws from the histogram arrays for clarity. Captions in `04_results.md` state this distinction explicitly.

## Secondary validation artifact

`scripts/02_lattice_crosscheck.py` writes `output/data/lattice_crosscheck.json`, comparing brute-force $\delta_Q$ to the scaled-lattice formulation and recording Dirichlet residual checks on fixed test reals.



```{=latex}
\newpage
```


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

The classical box argument shows that for each $Q \geq 1$ there exists $q \in \{1,\ldots,Q\}$ with $\|qx\| \leq 1/(Q+1)$ [@cassels1957]. This controls the **numerator** $\|qx\|$ only; dividing by $q$ to compare with $\delta_Q(x)$ requires the separate minimisation over $q \leq Q$. In particular, a small $\|qx\|$ at a **large** $q$ need not beat a moderately small residual at a **smaller** $q$ once the $1/q$ factor is applied.

## Relation to continued fractions

Continued-fraction convergents supply excellent rational approximations but need not attain $\delta_Q(x)$ for a fixed $Q$ without semiconvergents; `cf_distance.py` documents the convergent-only lower envelope used for quick certificates. The three-$p$ scan closes that gap numerically at the chosen $Q$ ceiling.

## Computational takeaway

The lattice form is the preferred mental model for **why** scanning $q$ is natural: each $q$ places $qx$ near an integer grid on the circle; $\delta_Q$ is the best normalised residual $\|qx\|/q$ among heights $1,\ldots,Q$.



```{=latex}
\newpage
```


# $q^2$ error scale (Lagrange / Hurwitz viewpoint)

For integers $p,q$ with $q \geq 1$, define the **weighted** error
\begin{equation}
\label{eq:lagrange}
\mu_Q(x) = \min_{1 \leq q \leq Q}\ \min_{p \in \mathbb{Z}} q^2 \left| x - \frac{p}{q} \right|.
\end{equation}

For fixed $q$, the inner minimum is attained at $p = \mathrm{round}(qx)$, so the implementation checks the same three candidates per $q$ as for $\delta_Q(x)$ in `02_problem_statement.md`. The factor $q^2$ makes $\mu_Q$ dimensionless in the sense used in Hurwitz-type theorems: for infinitely many convergents one has $q^2|x - p/q| < 1$, and for every irrational $x$ there are infinitely many pairs with $q^2|x-p/q| < 1/\sqrt{5}$ [@hurwitz1891].

## Interpreting $\mu_Q$ at finite $Q$

At **finite** $Q$, $\mu_Q(x)$ answers: *how small is the best weighted error achievable with denominators up to $Q$?* A superb approximant with small $q$ can yield a **moderate** $\delta_Q$ but a **very small** $\mu_Q$ because $q^2$ penalises large denominators less aggressively than $1/q$ rewards them in $\delta_Q$. Conversely, a number may have a tiny $\delta_Q$ because some modest $q$ lands unusually close, while $\mu_Q$ need not be extreme if that hit is not outstanding on the $q^2$ scale.

The Monte Carlo pipeline records both $\delta_Q$ and $\mu_Q$ for named constants and for the pooled reference (`min_q_squared_error`, `empirical_percentile_rank_q_squared`, `reference_q_squared_summary` in `output/data/proximity_summary.json`). Figure \ref{fig:proximity_mu} shows the pooled reference distribution of $\log_{10}\mu_Q$ with the same constant markers as the $\delta_Q$ panels.

## Comparison to badly approximable heuristics

Badly approximable numbers satisfy $\liminf_q q^2|x-p/q|>0$, so $\mu_Q(x)$ is bounded away from $0$ as $Q\to\infty$ along worst-case subsequences. At fixed moderate $Q$, empirical ranks of $\mu_Q$ still fluctuate with the **best** hit available below the ceiling; reporting both statistics reduces the risk of over-interpreting a single scale.



```{=latex}
\newpage
```


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



```{=latex}
\newpage
```


# Results

Regenerate `output/data/proximity_summary.json`, CSV, and figures with:

```bash
uv run python projects/special_number_proximity/scripts/proximity_monte_carlo.py
```

(or the repository analysis stage via `./run.sh`). Unless noted, numbers below match the committed JSON from seed `20260322`, `q_{\max}=120`, pooled size $n=7000$ (`4000$ uniform + $2000$ quadratic mod $1$ + $1000$ $\mathrm{Beta}(1/2,1/2)$), `compare_mod1=false`.

## Pooled reference summaries

For $\delta_Q$ on the full pooled sample: median $\approx 5.68\times 10^{-5}$, mean $\approx 1.30\times 10^{-4}$, $5$th–$95$th empirical percentiles $\approx [8.25\times 10^{-6},\,3.74\times 10^{-4}]$. For $\mu_Q$: median $\approx 0.115$, mean $\approx 0.113$, $p_5$–$p_{95}$ $\approx [6.95\times 10^{-3},\,0.268]$. These blocks appear verbatim as `reference_summary` and `reference_q_squared_summary` in the JSON.

## Constant table at $Q=120$

Empirical rank is the proportion of pooled samples with **strictly smaller** $\delta_Q$ (respectively $\mu_Q$); multiply by $100$ for a percentage. Values below are read from `proximity_summary.json` (`constants` array).

| Constant | $\delta_{120}(x^\star)$ | rank ($\delta$) | $\mu_{120}(x^\star)$ | rank ($\mu$) |
|----------|-------------------------|-----------------|----------------------|--------------|
| `one_sixth` | $0$ | $0\%$ | $0$ | $0\%$ |
| `pi` | $2.67\times 10^{-7}$ | $\approx 0.17\%$ | $3.41\times 10^{-3}$ | $\approx 2.84\%$ |
| `e` | $2.80\times 10^{-5}$ | $\approx 19.2\%$ | $0.141$ | $\approx 68.9\%$ |
| `sqrt2` | $7.21\times 10^{-5}$ | $\approx 57.4\%$ | $0.343$ | $\approx 97.6\%$ |
| `sqrt3` | $9.20\times 10^{-5}$ | $\approx 71.8\%$ | $0.268$ | $\approx 94.6\%$ |
| `golden_ratio` | $5.65\times 10^{-5}$ | $\approx 49.8\%$ | $0.382$ | $\approx 100\%$ |
| `ln2` | $3.46\times 10^{-5}$ | $\approx 27.9\%$ | $0.142$ | $\approx 69.0\%$ |

At this $Q$, $\pi$ is a pronounced left-tail outlier on the $\delta_Q$ scale—consistent with an excellent low-height approximant—while $\varphi$ sits near the median for $\delta_Q$ but attains the **largest** observed $\mu_{120}$ among registry constants (rank $1$ on the pooled sample), illustrating the distinction between raw distance and $q^2$-weighted quality discussed in `03e_q_squared_quality.md`.

**Reproducibility note:** After any config change, replace the numeric cells from the latest `proximity_constants.csv` or JSON so the manuscript stays synchronized with artifacts.

## $Q$-sensitivity on the same draws

With `q_sensitivity: [30, 60, 120]`, the JSON includes recomputed constant rows at $Q\in\{30,60,120\}$ on the **identical** $7000$ draws. Illustrative pattern for $\pi$: empirical rank for $\delta_Q$ moves from $\approx 59.6\%$ at $Q=30$ to $\approx 0.17\%$ at $Q=120$—raising the ceiling exposes dramatically better rationals. $\sqrt{2}$ illustrates non-monotonicity: its empirical $\delta_Q$ rank **rises** from $\approx 19.1\%$ at $Q=30$ to $\approx 77.7\%$ at $Q=60$ as the minimiser over $q\le Q$ switches structure, before moving again at $Q=120$. Always consult `q_sensitivity` in the JSON for the exact numbers after reruns.

## Figures

Figure \ref{fig:proximity_hist} shows a **uniform-only** subsample (size capped by `histogram_uniform_cap` in config) with $60$ equal-width bins on $\log_{10}\delta_Q$. Vertical lines mark $\delta_{120}$ for six registry constants (`pi`, `e`, `golden_ratio`, `sqrt2`, `sqrt3`, `ln2`); rational `one_sixth` lies at $-\infty$ in log scale and is not drawn. The panel is intended for comparison to a pure uniform reference; it does **not** include Beta or quadratic draws.

Figure \ref{fig:proximity_pooled} uses the same $Q$ and seed but histograms a **mixed** subsample: uniform draws plus fractional parts $\{\sqrt{k}\}$ for random square-free $k$ from `quadratic_candidates` (Beta draws remain **out** of the histogram arrays by design—see `03c_monte_carlo_design.md`). Constant markers match Figure \ref{fig:proximity_hist} so the eye can compare tail placement when quadratic-mod-$1$ mass is folded in.

Figure \ref{fig:proximity_mu} displays $\log_{10}\mu_Q$ for the **same** pooled subsample as Figure \ref{fig:proximity_pooled}, with matching constant markers on the $\mu_{120}$ scale. Use it to see when large $\mu$ ranks (e.g. $\varphi$) accompany middling $\delta$ ranks.

![**Figure.** Histogram of $\log_{10}\delta_Q(x)$ for a uniform$(0,1)$ subsample at fixed $Q=120$ (seed `20260322`, bin count $60$). Each vertical line is $\log_{10}\delta_{120}(x^\star)$ for a named constant in the project registry (`pi`, `e`, `golden_ratio`, `sqrt2`, `sqrt3`, `ln2`). Leftward displacement indicates a smaller rational error than most uniform draws at this denominator ceiling; the bulk of the reference mass reflects typical $\delta_Q$ for generic $x$ under uniform sampling only.](../figures/proximity_histogram.png){#fig:proximity_hist}

![**Figure.** Same $Q$ and marker constants as Figure \ref{fig:proximity_hist}, but the reference histogram pools a **subsample** of uniform$(0,1)$ draws with fractional parts $\{\sqrt{k}\}$ for random square-free $k$ from the configured candidate list (Beta components of the full Monte Carlo sample are **not** included here). This panel contrasts how quadratic-mod-$1$ mass reshapes the $\delta_Q$ distribution relative to Figure \ref{fig:proximity_hist}; percentiles in the JSON still use the **full** pooled sample including Beta draws.](../figures/proximity_histogram_pooled.png){#fig:proximity_pooled}

![**Figure.** Histogram of $\log_{10}\mu_Q(x)$ on the **identical** subsample as Figure \ref{fig:proximity_pooled} ($Q=120$, same seed and bin count). Vertical lines mark $\mu_{120}(x^\star)$ for the same six constants. Interpreting this panel alongside Figures \ref{fig:proximity_hist}–\ref{fig:proximity_pooled} separates raw closeness $\delta_Q$ from denominator-weighted quality $\mu_Q$; a constant can sit near the $\delta_Q$ median while lying in an extreme $\mu_Q$ tail if its best admissible approximant is comparatively weak on the $q^2$ scale.](../figures/proximity_histogram_mu.png){#fig:proximity_mu}

## Related checks

Lattice versus brute-force agreement is recorded in `output/data/lattice_crosscheck.json` from `scripts/02_lattice_crosscheck.py`.



```{=latex}
\newpage
```


# Conclusion

Finite-$Q$ rational proximity is a deliberately coarse lens: it rewards numbers that admit unusually accurate low-height approximants, not “randomness” in a probabilistic sense. Reporting **both** $\delta_Q$ and $\mu_Q$ (`03e_q_squared_quality.md`) separates raw closeness from denominator-weighted quality and catches cases—such as the golden ratio in the default run—where the two scales tell different stories at the same $Q$.

At $Q=120$ under the default pooled reference, $\pi$ occupies an extreme left tail for $\delta_Q$ while several algebraic irrationals and transcendentals fall closer to the bulk; `q_sensitivity` shows that such rankings are **not monotone** in $Q$ because enlarging the rational search set can unlock new approximants in a non-uniform way. Optional `compare_mod1: true` re-expresses constants on $[0,1)$ when the scientific question targets uniform-on-the-circle comparison.

The pipeline remains modular (`src/continued_fractions`, `rational_distance`, `diophantine_bounds`, `cf_distance`, `sampling`, `statistics_compare`), tested without mocks (`docs/testing_philosophy.md`), and parameterized from `manuscript/config.yaml`. Figures subsample for clarity; tables and JSON ranks reflect the **full** pooled Monte Carlo array.



```{=latex}
\newpage
```


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

The script prints absolute paths to **five** outputs: JSON summary, CSV constant table, and three PNG figures (`proximity_histogram.png`, `proximity_histogram_pooled.png`, `proximity_histogram_mu.png`).

Edits to `manuscript/config.yaml` under `experiment:` change seeds, sample sizes, `q_max`, `quadratic_candidates`, `compare_mod1`, `q_sensitivity`, `histogram_uniform_cap`, and Beta parameters without editing Python.

## Data paths

| Artifact | Path |
|----------|------|
| Summary JSON | `projects/special_number_proximity/output/data/proximity_summary.json` |
| Table CSV | `projects/special_number_proximity/output/data/proximity_constants.csv` |
| Uniform $\delta_Q$ histogram | `projects/special_number_proximity/../figures/proximity_histogram.png` |
| Pooled $\delta_Q$ histogram | `projects/special_number_proximity/../figures/proximity_histogram_pooled.png` |
| Pooled $\mu_Q$ histogram | `projects/special_number_proximity/../figures/proximity_histogram_mu.png` |
| Lattice cross-check | `projects/special_number_proximity/output/data/lattice_crosscheck.json` |

Run `uv run python projects/special_number_proximity/scripts/02_lattice_crosscheck.py` to refresh the lattice JSON.

## Combined manuscript build

```bash
uv run python scripts/03_render_pdf.py --project special_number_proximity
python3 -m infrastructure.validation.cli markdown projects/special_number_proximity/manuscript/
```

Authoring conventions for Markdown and cross-refs: [`docs/manuscript_conventions.md`](../docs/manuscript_conventions.md).



```{=latex}
\newpage
```


# Limitations

- **Fixed $Q$:** The statistics $\delta_Q$ and $\mu_Q$ (\eqref{eq:delta}, \eqref{eq:lagrange}) are evaluated at a single ceiling in the headline table (or a short list via `experiment.q_sensitivity` in `config.yaml`). They do not classify a number’s Diophantine type as $Q \to \infty$.

- **Reference law:** Empirical percentiles depend on the mixture of Uniform$(0,1)$, quadratic-mod-$1$, and optional Beta draws. Changing `quadratic_candidates` or sample sizes shifts the pooled CDF; `compare_mod1: true` re-expresses constants on $[0,1)$ for fairer comparison when the uniform component dominates the scientific question.

- **Histograms vs tables:** Figures use a capped **visualisation subsample** that omits Beta draws even when the pooled Monte Carlo includes them (`histogram_uniform_cap`, see `03c_monte_carlo_design.md`). JSON/CVS percentiles always use the full pooled array.

- **Labels:** `NumberClass` tags in `constants.py` are documentary; the code does not certify transcendence or algebraicity.

- **Convergent-only helper:** `min_distance_among_convergents` can exceed $\delta_Q$ when a semiconvergent beats every convergent with $q \leq Q$.

- **Floating point:** Results are IEEE-754 doubles. Pathological $x$ with enormous partial quotients are not representative of the registry constants but illustrate that continued-fraction diagnostics can truncate early.



```{=latex}
\newpage
```


# Notation and symbols

| Symbol | Meaning |
|--------|---------|
| $Q$ | Fixed maximum denominator in \eqref{eq:delta}; integer $\geq 1$. |
| $\delta_Q(x)$ | $\min_{1\le q\le Q}\min_{p\in\mathbb{Z}} |x-p/q|$; primary proximity statistic. |
| $\mu_Q(x)$ | $\min_{1\le q\le Q}\min_{p\in\mathbb{Z}} q^2|x-p/q|$; Lagrange-type weighted error (\eqref{eq:lagrange}). |
| $\|y\|$ | Distance from real $y$ to the nearest integer. |
| $\{x\}$ | Fractional part $x-\lfloor x\rfloor$ (used when `compare_mod1` is enabled). |
| Pooled sample | Concatenation of configured uniform, quadratic-mod-$1$, and optional Beta draws on $[0,1)$ with one shared RNG seed. |
| Empirical rank | Proportion of pooled draws with $\delta_Q(X_i)$ (or $\mu_Q(X_i)$) **strictly less** than the constant’s value. |
| `q_sensitivity` | YAML-driven list of extra $Q$ values; recomputes tables on the **same** pooled abscissa. |

Module names refer to `projects/special_number_proximity/src/` unless a path is explicit.



```{=latex}
\newpage
```


# Reader’s guide to registered constants

Each entry below mirrors `src/constants.py`. Classification strings are **informative only**; no formal proof is recomputed in software.

**`pi` — transcendental (documentary).** Circle constant. Famous rational approximants at moderate height (e.g. $355/113$) can make $\delta_Q$ extremely small at finite $Q$ when those denominators enter the search range.

**`e` — transcendental (documentary).** Base of the natural logarithm. Continued-fraction coefficients are unbounded; finite-$Q$ behaviour is read from the JSON after each run.

**`sqrt2`, `sqrt3` — irrational algebraic degree $2$.** Quadratic irrationals are badly approximable in the classical sense; nonetheless $\delta_Q$ and $\mu_Q$ at fixed $Q$ depend on which rational with $q\le Q$ wins the minimum.

**`golden_ratio` — $\varphi=(1+\sqrt5)/2$, quadratic irrational.** All partial quotients equal $1$ in exact continued-fraction theory; expect bounded-quotient heuristics to interact with $\mu_Q$ ranks differently from $\delta_Q$ ranks at the same $Q$.

**`ln2` — transcendental (documentary).** Natural logarithm of $2$; included to show a transcendental on $(0,1)$ alongside uniform-style references.

**`one_sixth` — rational control.** Exact value $1/6$; $\delta_Q=\mu_Q=0$ for $Q\ge 6$ under exact arithmetic. Serves as a zero baseline for the scan and CSV export.
