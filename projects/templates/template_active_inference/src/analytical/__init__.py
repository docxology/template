"""Closed-form Bernoulli / Ising analytical companion."""

from .bernoulli_toy import (
    empirical_mutual_information,
    ising_coupling,
    ising_joint_posterior,
    ising_mutual_information,
    lambda_sweep_values,
    symmetric_mean_field_prior,
)
from .decomposition import DecompositionTerms, decomposition_identity_holds, entanglement_decomposition_rhs
from .hyperparameters import Hyperparameters, load_hyperparameters
from .invariants import CORE_INVARIANTS, InvariantFn, all_invariants_pass, run_invariants

__all__ = [
    "CORE_INVARIANTS",
    "DecompositionTerms",
    "Hyperparameters",
    "InvariantFn",
    "all_invariants_pass",
    "decomposition_identity_holds",
    "empirical_mutual_information",
    "entanglement_decomposition_rhs",
    "ising_coupling",
    "ising_joint_posterior",
    "ising_mutual_information",
    "lambda_sweep_values",
    "load_hyperparameters",
    "run_invariants",
    "symmetric_mean_field_prior",
]
