"""Runtime-guard tests for ``ColonyTrialConfig.__post_init__`` (ISC-80).

Mirrors the discipline already proven for ``storage/schema.py``'s
``Column``/``TableSchema`` (SQL-identifier validation at construction) and
``storage/transaction.py``'s isolation-level ``Literal`` -- an unvalidated
numeric field that silently accepts a nonsensical value (a negative
standard deviation, a decay outside ``[0.0, 1.0]``) is the same class of
gap, just on the remaining numeric config surface. Every rejection case
below is proven by actually constructing the frozen dataclass and
asserting the raise, not by inspecting a type annotation.
"""

from __future__ import annotations

import pytest

from template_formal.colony.experiment import ColonyTrialConfig

_BASE_KWARGS: dict[str, object] = {
    "num_agents": 3,
    "locations": ("north", "south"),
    "num_ticks": 5,
    "preference_mean_range": (8.0, 12.0),
    "preference_variance": 1.0,
    "sensing_noise_std": 0.5,
    "deposit_amount": 1.0,
    "decay": 0.46,
    "seed": 0,
}


def _make(**overrides: object) -> ColonyTrialConfig:
    kwargs = dict(_BASE_KWARGS)
    kwargs.update(overrides)
    return ColonyTrialConfig(**kwargs)  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# decay must be a fraction in [0.0, 1.0]
# --------------------------------------------------------------------------


def test_negative_decay_raises() -> None:
    with pytest.raises(ValueError, match="decay must be a fraction"):
        _make(decay=-0.1)


def test_decay_above_one_raises() -> None:
    with pytest.raises(ValueError, match="decay must be a fraction"):
        _make(decay=1.5)


def test_decay_at_zero_and_one_boundary_is_accepted() -> None:
    assert _make(decay=0.0).decay == 0.0
    assert _make(decay=1.0).decay == 1.0


# --------------------------------------------------------------------------
# sensing_noise_std must be non-negative
# --------------------------------------------------------------------------


def test_negative_sensing_noise_std_raises() -> None:
    with pytest.raises(ValueError, match="sensing_noise_std must be non-negative"):
        _make(sensing_noise_std=-1.0)


def test_zero_sensing_noise_std_is_accepted() -> None:
    assert _make(sensing_noise_std=0.0).sensing_noise_std == 0.0


# --------------------------------------------------------------------------
# preference_variance must be > 0.0 -- matches BeliefState's stricter bound
# (a cross-vendor audit caught this field's original ">= 0.0" guard
# accepting 0.0 while its sole consumer, BeliefState, rejects it, causing
# the same "fails downstream, not at config construction" defect the
# __post_init__ guards on this class exist to prevent).
# --------------------------------------------------------------------------


def test_negative_preference_variance_raises() -> None:
    with pytest.raises(ValueError, match=r"preference_variance must be > 0\.0"):
        _make(preference_variance=-2.0)


def test_zero_preference_variance_raises() -> None:
    with pytest.raises(ValueError, match=r"preference_variance must be > 0\.0"):
        _make(preference_variance=0.0)


# --------------------------------------------------------------------------
# The full valid range still works end-to-end (no false-positive rejection).
# --------------------------------------------------------------------------


def test_full_valid_range_config_constructs_without_error() -> None:
    config = _make(
        decay=0.46,
        sensing_noise_std=0.5,
        preference_variance=1.0,
    )
    assert config.decay == 0.46
    assert config.sensing_noise_std == 0.5
    assert config.preference_variance == 1.0


def test_multiple_valid_boundary_and_interior_values_all_construct() -> None:
    for decay in (0.0, 0.02, 0.46, 0.97, 1.0):
        for sensing_noise_std in (0.0, 0.5, 4.0):
            for preference_variance in (1e-9, 1.0, 3.0):
                config = _make(
                    decay=decay,
                    sensing_noise_std=sensing_noise_std,
                    preference_variance=preference_variance,
                )
                assert config.decay == decay
                assert config.sensing_noise_std == sensing_noise_std
                assert config.preference_variance == preference_variance


@pytest.mark.parametrize(
    "field,value,diagnostic",
    [
        ("num_agents", True, "num_agents must be an int"),
        ("num_ticks", "5", "num_ticks must be an int"),
        ("decay", True, "decay must be numeric"),
        ("locations", ("north", 2), "locations must be a sequence of strings"),
        ("preference_mean_range", (8.0,), "preference_mean_range must contain two numeric bounds"),
        ("preference_mean_range", (True, 12.0), "preference_mean_range must contain two numeric bounds"),
        ("sensed_concentration_cap", True, "sensed_concentration_cap must be numeric or None"),
    ],
)
def test_dynamic_trial_inputs_reject_ambiguous_types(field: str, value: object, diagnostic: str) -> None:
    values = {**_BASE_KWARGS, field: value}
    with pytest.raises(TypeError, match=diagnostic):
        ColonyTrialConfig.from_mapping(seed=0, values=values)


def test_dynamic_trial_inputs_normalize_to_the_same_typed_configuration() -> None:
    values = {**_BASE_KWARGS, "locations": ["north", "south"], "preference_mean_range": [8, 12]}
    assert ColonyTrialConfig.from_mapping(seed=17, values=values) == _make(seed=17)
