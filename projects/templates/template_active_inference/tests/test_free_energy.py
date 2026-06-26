import numpy as np
import pytest

from analytical.free_energy import (
    free_energy,
    kl_divergence,
    marginal_free_energy,
    shannon_entropy,
    total_correlation,
    total_correlation_via_kl,
)
from analytical.hyperparameters import lambda_grid, load_hyperparameters


def test_shannon_entropy_uniform_binary() -> None:
    p = np.array([0.5, 0.5])
    assert np.isclose(shannon_entropy(p), np.log(2.0))


def test_shannon_entropy_one_hot_is_zero() -> None:
    # 0 log 0 == 0; a one-hot distribution has zero entropy.
    assert shannon_entropy(np.array([1.0, 0.0, 0.0])) == 0.0


def test_shannon_entropy_all_zero_is_zero() -> None:
    # All-zeros is not a valid distribution but the safe convention is H=0.
    assert shannon_entropy(np.zeros(3)) == 0.0


def test_total_correlation_independent_is_zero() -> None:
    q = np.array([[0.25, 0.25], [0.25, 0.25]])
    assert abs(total_correlation(q)) < 1e-9
    assert abs(total_correlation_via_kl(q)) < 1e-9


def test_kl_divergence_identical_is_zero() -> None:
    p = np.array([0.3, 0.7])
    assert abs(kl_divergence(p, p)) < 1e-12


def test_kl_divergence_shape_mismatch_raises() -> None:
    """kl_divergence must raise ValueError when q and p have different shapes."""
    with pytest.raises(ValueError, match="shape mismatch"):
        kl_divergence(np.array([0.5, 0.5]), np.array([0.3, 0.3, 0.4]))


def test_kl_divergence_returns_inf_when_p_has_zero_in_support_of_q() -> None:
    """KL is unbounded when q places mass where p is zero."""
    q = np.array([0.5, 0.5])
    p = np.array([1.0, 0.0])  # p has no support at index 1
    assert kl_divergence(q, p) == float("inf")


def test_kl_divergence_finite_when_q_is_zero() -> None:
    """Zero q entries are skipped (0 log 0 = 0); result stays finite."""
    q = np.array([0.0, 1.0])
    p = np.array([0.5, 0.5])
    assert kl_divergence(q, p) < float("inf")


def test_free_energy_shape_mismatch_raises() -> None:
    """free_energy must raise ValueError when q, prior, G don't share a shape."""
    q = np.array([0.5, 0.5])
    prior = np.array([0.5, 0.5])
    g_wrong = np.array([1.0, 2.0, 3.0])  # mismatched shape
    with pytest.raises(ValueError, match="common shape"):
        free_energy(q, prior, g_wrong, gamma=1.0)


def test_free_energy_uniform_zero_prior() -> None:
    """free_energy returns a finite value for a uniform belief/prior.

    With uniform q=[0.5,0.5], uniform prior=[0.5,0.5], g=zeros, gamma=1:
    F = gamma*E[G] - E[log prior] - H(q) = 0 - (-log 2) - log 2 = 0.
    """
    q = np.array([0.5, 0.5])
    prior = np.array([0.5, 0.5])
    g = np.zeros(2)
    fe = free_energy(q, prior, g, gamma=1.0)
    assert abs(fe) < 1e-9


def test_marginal_free_energy_single_stream() -> None:
    """marginal_free_energy on a 1-D joint evaluates the only stream.

    Same identity as test_free_energy_uniform_zero_prior: F = 0 for a
    uniform belief against a uniform prior with no energy term.
    """
    q = np.array([0.5, 0.5])
    mf_prior = [np.array([0.5, 0.5])]
    per_stream_g = [np.zeros(2)]
    fe = marginal_free_energy(q, mf_prior, per_stream_g, gamma=1.0, k=0)
    assert abs(fe) < 1e-9


def test_total_correlation_via_kl_agrees_with_direct() -> None:
    """The KL form and the entropy-sum form agree to float precision."""
    q = np.array([[0.4, 0.1], [0.1, 0.4]])  # correlated joint
    tc_direct = total_correlation(q)
    tc_kl = total_correlation_via_kl(q)
    assert abs(tc_direct - tc_kl) < 1e-9


def test_lambda_grid_length() -> None:
    hp = load_hyperparameters()
    grid = lambda_grid(hp)
    assert len(grid) == hp.lambda_grid_points
