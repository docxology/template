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
