# Limitations

- **Fixed $Q$:** The statistics $\delta_Q$ and $\mu_Q$ (\eqref{eq:delta}, \eqref{eq:lagrange}) are evaluated at a single ceiling in the headline table (or a short list via `experiment.q_sensitivity` in `config.yaml`). They do not classify a number’s Diophantine type as $Q \to \infty$.

- **Reference law:** Empirical percentiles depend on the mixture of Uniform$(0,1)$, quadratic-mod-$1$, and optional Beta draws. Changing `quadratic_candidates` or sample sizes shifts the pooled CDF; `compare_mod1: true` re-expresses constants on $[0,1)$ for fairer comparison when the uniform component dominates the scientific question.

- **Histograms vs tables:** Figures use a capped **visualisation subsample** that omits Beta draws even when the pooled Monte Carlo includes them (`histogram_uniform_cap`, see `03c_monte_carlo_design.md`). JSON/CVS percentiles always use the full pooled array.

- **Labels:** `NumberClass` tags in `constants.py` are documentary; the code does not certify transcendence or algebraicity.

- **Convergent-only helper:** `min_distance_among_convergents` can exceed $\delta_Q$ when a semiconvergent beats every convergent with $q \leq Q$.

- **Floating point:** Results are IEEE-754 doubles. Pathological $x$ with enormous partial quotients are not representative of the registry constants but illustrate that continued-fraction diagnostics can truncate early.
