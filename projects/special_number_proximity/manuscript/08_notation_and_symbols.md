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
