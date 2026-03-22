# Conclusion

Finite-$Q$ rational proximity is a deliberately coarse lens: it rewards numbers that admit unusually accurate low-height approximants, not “randomness” in a probabilistic sense. Reporting **both** $\delta_Q$ and $\mu_Q$ (`03e_q_squared_quality.md`) separates raw closeness from denominator-weighted quality and catches cases—such as the golden ratio in the default run—where the two scales tell different stories at the same $Q$.

At $Q=120$ under the default pooled reference, $\pi$ occupies an extreme left tail for $\delta_Q$ while several algebraic irrationals and transcendentals fall closer to the bulk; `q_sensitivity` shows that such rankings are **not monotone** in $Q$ because enlarging the rational search set can unlock new approximants in a non-uniform way. Optional `compare_mod1: true` re-expresses constants on $[0,1)$ when the scientific question targets uniform-on-the-circle comparison.

The pipeline remains modular (`src/continued_fractions`, `rational_distance`, `diophantine_bounds`, `cf_distance`, `sampling`, `statistics_compare`), tested without mocks (`docs/testing_philosophy.md`), and parameterized from `manuscript/config.yaml`. Figures subsample for clarity; tables and JSON ranks reflect the **full** pooled Monte Carlo array.
