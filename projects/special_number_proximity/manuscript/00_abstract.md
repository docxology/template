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
