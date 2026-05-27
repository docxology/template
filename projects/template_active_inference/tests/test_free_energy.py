import numpy as np

from analytical.free_energy import kl_divergence, shannon_entropy, total_correlation, total_correlation_via_kl
from analytical.hyperparameters import lambda_grid, load_hyperparameters


def test_shannon_entropy_uniform_binary() -> None:
    p = np.array([0.5, 0.5])
    assert np.isclose(shannon_entropy(p), np.log(2.0))


def test_total_correlation_independent_is_zero() -> None:
    q = np.array([[0.25, 0.25], [0.25, 0.25]])
    assert abs(total_correlation(q)) < 1e-9
    assert abs(total_correlation_via_kl(q)) < 1e-9


def test_kl_divergence_identical_is_zero() -> None:
    p = np.array([0.3, 0.7])
    assert abs(kl_divergence(p, p)) < 1e-12


def test_lambda_grid_length() -> None:
    hp = load_hyperparameters()
    grid = lambda_grid(hp)
    assert len(grid) == hp.lambda_grid_points
