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
