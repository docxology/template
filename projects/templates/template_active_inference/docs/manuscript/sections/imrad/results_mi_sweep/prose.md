We sweep coupling strength $\lambda$ on a grid of {{param_sweep_grid_points}} points up to $\lambda_{\max} = {{lambda_max}}$. Closed-form mutual information from [@eq:entangled_joint] is cross-checked against an independent exact recomputation via total correlation from the analytical module ([@sec:methods_analytical]); both are deterministic (no sampling) and agree to {{sweep_max_residual}} nats.

Measured invariant checks: {{invariants_passed}} / {{invariants_total}} passed on the clean tree.
