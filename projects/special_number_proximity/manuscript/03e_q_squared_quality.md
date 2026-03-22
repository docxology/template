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
