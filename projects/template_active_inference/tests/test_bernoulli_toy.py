import numpy as np

from analytical.bernoulli_toy import (
    empirical_mutual_information,
    ising_mutual_information,
    lambda_sweep_values,
)


def test_ising_mi_zero_at_lambda_zero() -> None:
    assert abs(ising_mutual_information(0.0)) < 1e-9


def test_ising_mi_saturates() -> None:
    assert np.isclose(ising_mutual_information(100.0), np.log(2.0), atol=1e-3)


def test_empirical_matches_closed_form_on_grid() -> None:
    for lam in lambda_sweep_values(11):
        assert abs(ising_mutual_information(lam) - empirical_mutual_information(lam)) < 1e-9
