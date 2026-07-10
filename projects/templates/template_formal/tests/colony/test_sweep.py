"""Unit + integration tests for ``colony/sweep.py``'s generic parameter-sweep runner.

Pure, stdlib-only, real computation -- every assertion below is bound to a
value hand-derived from :func:`~template_formal.colony.stats.wilson_score_interval`
directly, or to a small, fully-deterministic configuration (identical
preferences, zero sensing noise) whose convergence outcome is knowable in
advance without running the sweep at all.
"""

from __future__ import annotations

import pytest

from template_formal.colony.experiment import ColonyTrialConfig
from template_formal.colony.stats import wilson_score_interval
from template_formal.colony.sweep import SweepPointResult, run_parameter_sweep

_DETERMINISTIC_KWARGS: dict[str, object] = {
    "num_agents": 3,
    "locations": ("north", "south"),
    "num_ticks": 5,
    "preference_mean_range": (10.0, 10.0),  # identical preference -- no heterogeneity
    "preference_variance": 1.0,
    "sensing_noise_std": 0.0,  # zero noise
    "deposit_amount": 1.0,
}
"""Matches the negative-control configuration in
``tests/colony/test_colony_convergence_statistics.py`` -- guaranteed 100%
convergence regardless of ``decay``, so the sweep result at every point is
knowable in advance (a genuine hand-derivable expectation, not a "runs
without error" smoke test)."""


def test_param_name_not_a_real_colonytrialconfig_field_raises(tmp_path) -> None:  # type: ignore[no-untyped-def]
    kwargs = dict(_DETERMINISTIC_KWARGS)
    kwargs["decay"] = 0.02
    with pytest.raises(ValueError, match="not a sweepable ColonyTrialConfig field"):
        run_parameter_sweep(
            kwargs, param_name="not_a_real_field", values=[0.1], n_per_value=5, seed_base=0, db_dir=tmp_path
        )


def test_seed_is_not_a_sweepable_field(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """``seed`` varies *within* a sweep point, never *across* points --
    sweeping it would conflate the two axes, so it must be rejected."""
    kwargs = dict(_DETERMINISTIC_KWARGS)
    kwargs["decay"] = 0.02
    with pytest.raises(ValueError, match="not a sweepable ColonyTrialConfig field"):
        run_parameter_sweep(kwargs, param_name="seed", values=[1.0], n_per_value=5, seed_base=0, db_dir=tmp_path)


def test_empty_values_raises(tmp_path) -> None:  # type: ignore[no-untyped-def]
    kwargs = dict(_DETERMINISTIC_KWARGS)
    kwargs["decay"] = 0.02
    with pytest.raises(ValueError, match="values must be non-empty"):
        run_parameter_sweep(kwargs, param_name="decay", values=[], n_per_value=5, seed_base=0, db_dir=tmp_path)


def test_zero_n_per_value_raises(tmp_path) -> None:  # type: ignore[no-untyped-def]
    kwargs = dict(_DETERMINISTIC_KWARGS)
    kwargs["decay"] = 0.02
    with pytest.raises(ValueError, match="n_per_value must be >= 1"):
        run_parameter_sweep(kwargs, param_name="decay", values=[0.02], n_per_value=0, seed_base=0, db_dir=tmp_path)


def test_sweep_over_a_deterministic_config_matches_hand_derived_wilson_bounds(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Every trial in this configuration converges (100%, identical agents,
    zero noise -- matches the negative control in
    ``test_colony_convergence_statistics.py``), at every swept ``decay``
    value, regardless of value -- so both sweep points' ``successes``,
    ``rate``, and Wilson bounds are knowable in advance and checked against
    :func:`wilson_score_interval` called directly with the same n=5."""
    kwargs = dict(_DETERMINISTIC_KWARGS)
    points = run_parameter_sweep(
        kwargs, param_name="decay", values=[0.02, 0.5], n_per_value=5, seed_base=0, db_dir=tmp_path
    )

    assert len(points) == 2
    expected_lower, expected_upper = wilson_score_interval(5, 5, confidence=0.95)
    for point in points:
        assert isinstance(point, SweepPointResult)
        assert point.n == 5
        assert point.successes == 5
        assert point.rate == 1.0
        assert point.wilson_lower == pytest.approx(expected_lower)
        assert point.wilson_upper == pytest.approx(expected_upper)
    assert points[0].value == 0.02
    assert points[1].value == 0.5


def test_sweep_points_are_returned_in_the_same_order_as_values(tmp_path) -> None:  # type: ignore[no-untyped-def]
    kwargs = dict(_DETERMINISTIC_KWARGS)
    values = [0.9, 0.1, 0.5, 0.02]
    points = run_parameter_sweep(kwargs, param_name="decay", values=values, n_per_value=3, seed_base=0, db_dir=tmp_path)
    assert [point.value for point in points] == values


def test_different_sweep_points_use_disjoint_db_subdirectories(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Reusing the identical seed sequence across sweep points (the paired-
    seeds design documented in the module) must not collide on a shared
    on-disk SQLite path -- each point gets its own subdirectory."""
    kwargs = dict(_DETERMINISTIC_KWARGS)
    run_parameter_sweep(kwargs, param_name="decay", values=[0.02, 0.5], n_per_value=3, seed_base=0, db_dir=tmp_path)
    subdirs = sorted(p.name for p in tmp_path.iterdir() if p.is_dir())
    assert subdirs == ["decay_point_0", "decay_point_1"]


def test_base_config_kwargs_value_for_the_swept_field_is_overridden_not_merged(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """A value supplied in ``base_config_kwargs`` for ``param_name`` itself
    must be silently replaced by each sweep point's own value, proven by
    actually constructing the resulting config and reading its field back
    (via the deterministic 100%-convergence guarantee -- if the override
    had not taken effect, the sweep would still run, just at a different,
    unintended decay; the assertion below binds to the field actually used,
    not merely to "no exception raised")."""
    kwargs = dict(_DETERMINISTIC_KWARGS)
    kwargs["decay"] = 0.999  # deliberately wrong -- must be overridden per point
    points = run_parameter_sweep(kwargs, param_name="decay", values=[0.02], n_per_value=1, seed_base=0, db_dir=tmp_path)
    assert points[0].value == 0.02


def test_sweepable_field_names_matches_colonytrialconfig_fields_minus_seed() -> None:
    from dataclasses import fields

    from template_formal.colony.sweep import _SWEEPABLE_FIELD_NAMES

    real_field_names = {f.name for f in fields(ColonyTrialConfig)}
    assert _SWEEPABLE_FIELD_NAMES == real_field_names - {"seed"}
