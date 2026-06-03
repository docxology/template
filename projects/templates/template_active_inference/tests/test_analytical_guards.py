"""Guard-branch coverage for pure analytical helpers and the de-vacuumed graph-world
invariants. No mocks — every case drives a real error path or a real computation."""

from __future__ import annotations

import numpy as np
import pytest

from analytical.bernoulli_toy import ising_coupling, ising_mutual_information, lambda_sweep_values
from analytical.coupling import entangled_posterior, entangled_prior_unnormalised, expected_value
from analytical.joint_dist import joint_marginal, mean_field_to_joint, normalize


def test_ising_coupling_rejects_non_2x2() -> None:
    with pytest.raises(ValueError, match="only defined for shape"):
        ising_coupling((3, 3))


def test_ising_mutual_information_negative_lambda_branch() -> None:
    # Exercises the lam < 0 stabilized branch; MI is symmetric in |lam|.
    assert ising_mutual_information(-1.5) == pytest.approx(ising_mutual_information(1.5), abs=1e-12)
    assert ising_mutual_information(-0.5) > 0.0


def test_lambda_sweep_values_requires_two_points() -> None:
    with pytest.raises(ValueError, match="at least 2"):
        lambda_sweep_values(num_points=1)


def test_entangled_prior_rejects_shape_mismatch() -> None:
    mf = [np.array([0.5, 0.5]), np.array([0.5, 0.5])]  # joint shape (2, 2)
    with pytest.raises(ValueError, match="coupling shape"):
        entangled_prior_unnormalised(mf, np.zeros((3, 3)), lam=1.0)


def test_entangled_posterior_rejects_kc_shape_mismatch() -> None:
    mf = [np.array([0.5, 0.5]), np.array([0.5, 0.5])]
    with pytest.raises(ValueError, match="K_c shape"):
        entangled_posterior(mf, [np.zeros(2), np.zeros(2)], np.zeros((2, 2)), np.zeros((3, 3)), gamma=0.0, lam=1.0)


def test_expected_value_rejects_shape_mismatch() -> None:
    with pytest.raises(ValueError, match="shape mismatch"):
        expected_value(np.ones((2, 2)), np.ones(2))


def test_normalize_rejects_non_positive_mass() -> None:
    with pytest.raises(ValueError, match="non-positive mass"):
        normalize(np.zeros(4))


def test_mean_field_to_joint_requires_a_stream() -> None:
    with pytest.raises(ValueError, match="at least one stream"):
        mean_field_to_joint([])


def test_joint_marginal_rejects_out_of_range_axis() -> None:
    with pytest.raises(IndexError, match="out of range"):
        joint_marginal(np.ones((2, 2)), 5)


def test_graph_world_trace_invariants_are_non_vacuous() -> None:
    """The de-vacuumed invariant must report False on a malformed trace (Forge CRITICAL)."""
    from roadmap_tracks.toy_sweep import _graph_world_trace_invariants

    good = _graph_world_trace_invariants([{"node": "start"}, {"node": "a"}, {"node": "goal"}])
    assert good == {"reachability": True, "transition_determinism": True, "terminal_absorbing": True}

    not_reaching = _graph_world_trace_invariants([{"node": "start"}, {"node": "a"}])
    assert not_reaching["reachability"] is False
    assert not_reaching["terminal_absorbing"] is False  # goal never visited

    nondeterministic = _graph_world_trace_invariants(
        [{"node": "a"}, {"node": "b"}, {"node": "a"}, {"node": "c"}, {"node": "goal"}]
    )
    assert nondeterministic["transition_determinism"] is False

    leaves_goal = _graph_world_trace_invariants([{"node": "goal"}, {"node": "x"}, {"node": "goal"}])
    assert leaves_goal["terminal_absorbing"] is False


def test_figure_registry_yaml_missing_raises(tmp_path) -> None:
    from visualizations.figure_registry import load_figure_registry

    with pytest.raises(FileNotFoundError, match="missing figure registry"):
        load_figure_registry(tmp_path)


def test_figure_registry_skips_non_mapping_and_requires_entries(tmp_path) -> None:
    import yaml

    from visualizations.figure_registry import load_figure_registry

    (tmp_path / "figures.yaml").write_text(
        yaml.safe_dump({"figures": {"bad": "notamapping", "good": {"filename": "g.png", "alt": "a", "caption": "c"}}}),
        encoding="utf-8",
    )
    registry = load_figure_registry(tmp_path)
    assert "good" in registry and "bad" not in registry

    (tmp_path / "figures.yaml").write_text(yaml.safe_dump({"figures": {}}), encoding="utf-8")
    with pytest.raises(ValueError, match="at least one figure"):
        load_figure_registry(tmp_path)


def test_formal_interop_load_json_missing_returns_empty(tmp_path) -> None:
    from roadmap_tracks.formal_interop import _load_json

    assert _load_json(tmp_path / "nope.json") == {}
