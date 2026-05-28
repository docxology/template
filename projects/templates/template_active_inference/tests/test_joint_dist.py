import numpy as np

from analytical.joint_dist import is_mean_field, is_pmf, m_projection, mean_field_to_joint, normalize
from analytical.coupling import entangled_posterior
from analytical.bernoulli_toy import ising_coupling, symmetric_mean_field_prior


def test_normalize_sums_to_one() -> None:
    q = normalize(np.array([1.0, 2.0, 3.0]))
    assert is_pmf(q)


def test_mean_field_product() -> None:
    mf = [np.array([0.5, 0.5]), np.array([0.5, 0.5])]
    q = mean_field_to_joint(mf)
    assert q.shape == (2, 2)
    assert is_mean_field(q)


def test_m_projection_idempotent_on_mean_field() -> None:
    mf = symmetric_mean_field_prior()
    q = mean_field_to_joint(mf)
    assert np.allclose(q, m_projection(q))


def test_entangled_posterior_at_lambda_zero_is_mean_field() -> None:
    mf = symmetric_mean_field_prior()
    g0 = [np.zeros(2), np.zeros(2)]
    q = entangled_posterior(mf, g0, ising_coupling(), np.zeros((2, 2)), gamma=0.0, lam=0.0)
    assert is_mean_field(q)
