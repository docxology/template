```{=latex}
\phantomsection
\addcontentsline{toc}{section}{Results}
\section*{Results}
```

# Mutual-information parameter sweep {#sec:results_mi_sweep}

<!-- sheaf-track:prose -->

We sweep coupling strength $\lambda$ on a grid of 21 points up to $\lambda_{\max} = 4$. Closed-form mutual information from [@eq:entangled_joint] is compared to Monte Carlo estimates from the analytical module ([@sec:methods_analytical]).

Measured invariant checks: 12 / 12 passed on the clean tree.

<!-- sheaf-track:formalism -->

The sweep reuses the entangled joint defined in [@eq:entangled_joint] ([@sec:methods_analytical]). Mutual information $I(\lambda)=\log 2 - H_b(\sigma(\lambda))$ is evaluated on the same $\lambda$ grid as the analytical oracle and Monte Carlo estimates.

<!-- sheaf-track:simulation -->

Empirical MI estimates use fixed seed 0 and share the same $\lambda$ grid as the closed-form sweep ([@sec:methods_analytical], [@fig:ising_mi_curve]).

<!-- sheaf-track:visualization -->

![Two-panel plot of mutual information versus coupling strength lambda for the symmetric Bernoulli-Ising toy. Left panel shows closed-form curve (solid dark line) and Monte Carlo estimates (dashed blue line) with lambda on the x-axis and mutual information in nats on the y-axis. Right panel shows Monte Carlo minus closed-form residuals versus lambda with a zero reference line.](../output/figures/ising_mi_curve.png){width=90%}

*Figure 2 (results). Closed-form and Monte Carlo mutual information I(λ) for the symmetric Bernoulli-Ising toy across 21 grid points up to λ_max = 4; grid maximum 0.6031 nats on the measured sweep.*
