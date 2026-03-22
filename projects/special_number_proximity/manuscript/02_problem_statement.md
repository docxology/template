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

For each run, structured JSON records reference summaries, per-constant distances, ranks, and optional `q_sensitivity` blocks; CSV mirrors the primary constant table. Histograms (uniform subsample, pooled subsample, and $\mu_Q$ on the pooled subsample) are written under `output/figures/` for visual comparison of tail placement.
