# Analytical Bernoulli–Ising toy

<!-- sheaf-track:prose -->

We study a minimal **K=2 Bernoulli / Ising** coupling as the analytical companion to multi-track verification. Closed-form mutual information $I(\lambda)$ provides an oracle for empirical checks and GNN round-trips.

Measured sweep grid points: {{lambda_grid_points}}. Invariants passed: {{invariants_passed}} / {{invariants_total}}.

<!-- sheaf-track:formalism -->

The entangled joint over binary policies satisfies

$$q_\lambda(\pi) \propto E(\pi)\,\exp(\lambda J(\pi)),$$

with symmetric Ising coupling $J$ and deformation parameter $\lambda$. Mutual information is $I(\lambda)=\log 2 - H_b(\sigma(\lambda))$.

<!-- sheaf-track:simulation -->

The analytical track writes `output/data/parameter_sweep.csv` comparing closed-form and empirical mutual information across $\lambda \in [0, {{lambda_max}}]$.

<!-- sheaf-track:visualization -->

![Two-panel plot of mutual information versus coupling strength lambda for the symmetric Bernoulli-Ising toy. Left panel shows closed-form curve (solid dark line) and Monte Carlo estimates (dashed blue line) with lambda on the x-axis and mutual information in nats on the y-axis. Right panel shows Monte Carlo minus closed-form residuals versus lambda with a zero reference line.](../output/figures/ising_mi_curve.png)

*Figure 1 (methods). Closed-form and Monte Carlo mutual information I(λ) for the symmetric Bernoulli-Ising toy across {{param_sweep_grid_points}} grid points up to λ_max = {{lambda_max}}; grid maximum {{ising_mi_saturation}} nats on the measured sweep.*

<!-- sheaf-track:gnn -->

The Bernoulli toy is also declared in `gnn/bernoulli_toy.gnn.md` (GNN v1.1). Ontology annotations bind framework symbols to Active Inference Ontology terms.

<!-- sheaf-track:ontology -->

### Ontology bindings

- `J` → **CrossStreamCouplingPotential**
- `gamma` → **SophisticationWeight**
- `lam` → **EntanglementDeformationParameter**
- `pi1` → **Stream1PolicyVector**
- `pi2` → **Stream2PolicyVector**
- `q_joint` → **EntangledJointPosterior**

