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

![**Figure.** Histogram of $\log_{10}\delta_Q(x)$ for a uniform$(0,1)$ subsample at fixed $Q=120$ (seed `20260322`, bin count $60$). Each vertical line is $\log_{10}\delta_{120}(x^\star)$ for a named constant in the project registry (`pi`, `e`, `golden_ratio`, `sqrt2`, `sqrt3`, `ln2`). Leftward displacement indicates a smaller rational error than most uniform draws at this denominator ceiling; the bulk of the reference mass reflects typical $\delta_Q$ for generic $x$ under uniform sampling only.](../output/figures/proximity_histogram.png){#fig:proximity_hist}

![**Figure.** Same $Q$ and marker constants as Figure \ref{fig:proximity_hist}, but the reference histogram pools a **subsample** of uniform$(0,1)$ draws with fractional parts $\{\sqrt{k}\}$ for random square-free $k$ from the configured candidate list (Beta components of the full Monte Carlo sample are **not** included here). This panel contrasts how quadratic-mod-$1$ mass reshapes the $\delta_Q$ distribution relative to Figure \ref{fig:proximity_hist}; percentiles in the JSON still use the **full** pooled sample including Beta draws.](../output/figures/proximity_histogram_pooled.png){#fig:proximity_pooled}

![**Figure.** Histogram of $\log_{10}\mu_Q(x)$ on the **identical** subsample as Figure \ref{fig:proximity_pooled} ($Q=120$, same seed and bin count). Vertical lines mark $\mu_{120}(x^\star)$ for the same six constants. Interpreting this panel alongside Figures \ref{fig:proximity_hist}–\ref{fig:proximity_pooled} separates raw closeness $\delta_Q$ from denominator-weighted quality $\mu_Q$; a constant can sit near the $\delta_Q$ median while lying in an extreme $\mu_Q$ tail if its best admissible approximant is comparatively weak on the $q^2$ scale.](../output/figures/proximity_histogram_mu.png){#fig:proximity_mu}

## Related checks

Lattice versus brute-force agreement is recorded in `output/data/lattice_crosscheck.json` from `scripts/02_lattice_crosscheck.py`.
