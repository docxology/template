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
