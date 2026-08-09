"""Shared deterministic experiment fixtures for the colony test modules."""

from __future__ import annotations

import time

import pytest

from template_formal.colony.experiment import ColonyTrialConfig, run_colony_trial
from template_formal.colony.nullmodel import NullModelTrialConfig, run_null_model_trial
from template_formal.colony.sweep import run_parameter_sweep

_BASE_KWARGS: dict[str, object] = {
    "num_agents": 8,
    "locations": ("north", "south"),
    "num_ticks": 30,
    "preference_mean_range": (8.0, 12.0),
    "preference_variance": 1.0,
    "sensing_noise_std": 0.5,
    "deposit_amount": 1.0,
    "decay": 0.46,
}
_REAL_VS_NULL_N = 150
_REAL_VS_NULL_SEED_BASE = 0
_HETEROGENEITY_WIDTHS: dict[str, tuple[float, float]] = {
    "tight": (9.0, 11.0),
    "medium": (8.0, 12.0),
    "wide": (5.0, 15.0),
    "very_wide": (2.0, 18.0),
}
_HETEROGENEITY_N = 60
_SENSED_CONCENTRATION_CAP = 13.0


@pytest.fixture(scope="session")
def decay_sweep_points(tmp_path_factory):  # type: ignore[no-untyped-def]
    db_dir = tmp_path_factory.mktemp("decay_sweep")
    kwargs = {k: v for k, v in _BASE_KWARGS.items() if k != "decay"}
    start_wall = time.perf_counter()
    start_cpu = time.process_time()
    points = run_parameter_sweep(
        kwargs,
        param_name="decay",
        values=[0.1, 0.3, 0.46, 0.6, 0.8, 1.0],
        n_per_value=60,
        seed_base=0,
        db_dir=db_dir,
    )
    wall_elapsed = time.perf_counter() - start_wall
    cpu_elapsed = time.process_time() - start_cpu
    return points, wall_elapsed, cpu_elapsed


@pytest.fixture(scope="session")
def real_vs_null_results(tmp_path_factory):  # type: ignore[no-untyped-def]
    db_dir = tmp_path_factory.mktemp("real_vs_null")
    start_wall = time.perf_counter()
    start_cpu = time.process_time()
    real_outcomes = []
    for i in range(_REAL_VS_NULL_N):
        config = ColonyTrialConfig(seed=_REAL_VS_NULL_SEED_BASE + i, **_BASE_KWARGS)  # type: ignore[arg-type]
        result = run_colony_trial(config, db_dir)
        real_outcomes.append(result.converged)
    real_wall_elapsed = time.perf_counter() - start_wall
    real_cpu_elapsed = time.process_time() - start_cpu

    start_wall = time.perf_counter()
    start_cpu = time.process_time()
    null_outcomes = []
    for i in range(_REAL_VS_NULL_N):
        null_config = NullModelTrialConfig(
            num_agents=8, locations=("north", "south"), num_ticks=30, seed=_REAL_VS_NULL_SEED_BASE + i
        )
        null_result = run_null_model_trial(null_config)
        null_outcomes.append(null_result.converged)
    null_wall_elapsed = time.perf_counter() - start_wall
    null_cpu_elapsed = time.process_time() - start_cpu

    return (
        real_outcomes,
        null_outcomes,
        real_wall_elapsed + null_wall_elapsed,
        real_cpu_elapsed + null_cpu_elapsed,
    )


@pytest.fixture(scope="session")
def heterogeneity_sweep_results(tmp_path_factory):  # type: ignore[no-untyped-def]
    db_dir = tmp_path_factory.mktemp("heterogeneity_sweep")
    base_kwargs = {k: v for k, v in _BASE_KWARGS.items() if k != "preference_mean_range"}
    start_wall = time.perf_counter()
    start_cpu = time.process_time()
    outcomes_by_name: dict[str, list[bool]] = {}
    for name, mean_range in _HETEROGENEITY_WIDTHS.items():
        outcomes: list[bool] = []
        for i in range(_HETEROGENEITY_N):
            config = ColonyTrialConfig(seed=i, preference_mean_range=mean_range, **base_kwargs)  # type: ignore[arg-type]
            result = run_colony_trial(config, db_dir / name)
            outcomes.append(result.converged)
        outcomes_by_name[name] = outcomes
    wall_elapsed = time.perf_counter() - start_wall
    cpu_elapsed = time.process_time() - start_cpu
    return outcomes_by_name, wall_elapsed, cpu_elapsed


@pytest.fixture(scope="session")
def capped_low_decay_points(tmp_path_factory):  # type: ignore[no-untyped-def]
    db_dir = tmp_path_factory.mktemp("capped_low_decay")
    kwargs = {k: v for k, v in _BASE_KWARGS.items() if k != "decay"}
    kwargs["sensed_concentration_cap"] = _SENSED_CONCENTRATION_CAP
    start_wall = time.perf_counter()
    start_cpu = time.process_time()
    points = run_parameter_sweep(
        kwargs,
        param_name="decay",
        values=[0.1, 0.3],
        n_per_value=60,
        seed_base=0,
        db_dir=db_dir,
    )
    wall_elapsed = time.perf_counter() - start_wall
    cpu_elapsed = time.process_time() - start_cpu
    return points, wall_elapsed, cpu_elapsed


_HETEROGENEITY_REPLICATION_SEED_BASE = 7000


@pytest.fixture(scope="session")
def heterogeneity_sweep_results_seed7000(tmp_path_factory):  # type: ignore[no-untyped-def]
    db_dir = tmp_path_factory.mktemp("heterogeneity_sweep_seed7000")
    base_kwargs = {k: v for k, v in _BASE_KWARGS.items() if k != "preference_mean_range"}
    start_wall = time.perf_counter()
    start_cpu = time.process_time()
    outcomes_by_name: dict[str, list[bool]] = {}
    for name, mean_range in _HETEROGENEITY_WIDTHS.items():
        outcomes: list[bool] = []
        for i in range(_HETEROGENEITY_N):
            config = ColonyTrialConfig(  # type: ignore[arg-type]
                seed=_HETEROGENEITY_REPLICATION_SEED_BASE + i,
                preference_mean_range=mean_range,
                **base_kwargs,
            )
            result = run_colony_trial(config, db_dir / name)
            outcomes.append(result.converged)
        outcomes_by_name[name] = outcomes
    wall_elapsed = time.perf_counter() - start_wall
    cpu_elapsed = time.process_time() - start_cpu
    return outcomes_by_name, wall_elapsed, cpu_elapsed
