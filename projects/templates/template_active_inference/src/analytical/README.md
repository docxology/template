# Analytical (closed-form) track

Closed-form Active Inference mathematics, kept separate from the numerical and
pymdp tracks so the formalism can be checked independently.

- `free_energy.py` — free energies plus the supporting information-theoretic quantities (Shannon entropy, KL divergence, total correlation), all in nats.
- `bernoulli_toy.py` — the Bernoulli coupling toy model.
- `coupling.py` — coupling between latent factors.
- `decomposition.py` — free-energy / belief decompositions.
- `joint_dist.py` — joint-distribution construction and marginalization.
- `hyperparameters.py` — declared, validated hyperparameter sets.
