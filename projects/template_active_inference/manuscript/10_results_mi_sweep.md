# Mutual information sweep

<!-- sheaf-track:prose -->

We sweep coupling strength $\lambda$ on a grid of {{param_sweep_grid_points}} points up to $\lambda_{\max} = {{lambda_max}}$. Closed-form mutual information $I(\lambda)$ is compared to Monte Carlo estimates from the analytical module.

Measured invariant checks: {{invariants_passed}} / {{invariants_total}} passed on the clean tree.

<!-- sheaf-track:formalism -->

The entangled joint over binary policies satisfies

$$q_\lambda(\pi) \propto E(\pi)\,\exp(\lambda J(\pi)),$$

with symmetric Ising coupling $J$ and deformation parameter $\lambda$. Mutual information is $I(\lambda)=\log 2 - H_b(\sigma(\lambda))$.

<!-- sheaf-track:simulation -->

Empirical MI estimates use fixed seed {{random_seed}} and share the same $\lambda$ grid as the closed-form sweep in `output/data/parameter_sweep.csv`.

<!-- sheaf-track:visualization -->

![Two-panel plot of mutual information versus coupling strength lambda for the symmetric Bernoulli-Ising toy. Left panel shows closed-form curve (solid dark line) and Monte Carlo estimates (dashed blue line) with lambda on the x-axis and mutual information in nats on the y-axis. Right panel shows Monte Carlo minus closed-form residuals versus lambda with a zero reference line.](../output/figures/ising_mi_curve.png)

*Figure 2 (results). Closed-form and Monte Carlo mutual information I(λ) for the symmetric Bernoulli-Ising toy across {{param_sweep_grid_points}} grid points up to λ_max = {{lambda_max}}; grid maximum {{ising_mi_saturation}} nats on the measured sweep.*
