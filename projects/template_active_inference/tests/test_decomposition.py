import numpy as np

from analytical.bernoulli_toy import ising_coupling, ising_joint_posterior, symmetric_mean_field_prior
from analytical.decomposition import decomposition_identity_holds


def test_decomposition_identity_holds_for_sample_lambda() -> None:
    lam = 1.25
    q = ising_joint_posterior(lam)
    mf = symmetric_mean_field_prior()
    g0 = [np.zeros(2), np.zeros(2)]
    assert decomposition_identity_holds(
        q,
        mf,
        g0,
        ising_coupling(),
        np.zeros((2, 2)),
        gamma=1.0,
        lam=lam,
    )
