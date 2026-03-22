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
