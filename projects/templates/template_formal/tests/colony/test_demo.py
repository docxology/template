"""Behavioral tests for template_formal.colony.demo (moved out of scripts/
per the thin-orchestrator rule -- this is real business logic now living in
src/, so it needs real test coverage like everything else in src/)."""

from __future__ import annotations

from pathlib import Path

from template_formal.colony.demo import (
    DEMO_DECAY,
    DEMO_DEPOSIT_AMOUNT,
    DEMO_NUM_AGENTS,
    DEMO_NUM_TICKS,
    LOCATIONS,
    run_demo_colony,
    run_statistics_sweep,
)


def test_run_demo_colony_produces_real_per_agent_sqlite_files(tmp_path: Path) -> None:
    summary = run_demo_colony(tmp_path)

    assert summary["num_agents"] == DEMO_NUM_AGENTS
    assert summary["num_ticks"] == DEMO_NUM_TICKS
    agent_db_paths = summary["agent_db_paths"]
    assert isinstance(agent_db_paths, list)
    assert len(agent_db_paths) == DEMO_NUM_AGENTS
    for db_path in agent_db_paths:
        assert Path(db_path).is_file()
        assert Path(db_path).stat().st_size > 0


def test_run_demo_colony_choice_and_concentration_history_shapes(tmp_path: Path) -> None:
    summary = run_demo_colony(tmp_path)

    choice_history = summary["choice_history"]
    concentration_history = summary["concentration_history"]
    assert isinstance(choice_history, list)
    assert isinstance(concentration_history, list)
    assert len(choice_history) == DEMO_NUM_TICKS
    assert len(concentration_history) == DEMO_NUM_TICKS
    for tick_choices in choice_history:
        assert len(tick_choices) == DEMO_NUM_AGENTS
        assert all(choice in LOCATIONS for choice in tick_choices)
    for tick_concentrations in concentration_history:
        assert set(tick_concentrations) == set(LOCATIONS)


def test_run_demo_colony_is_deterministic_across_runs(tmp_path: Path) -> None:
    """All agents share the same fixed preference and a deterministic
    tie-break (see agent.decide) -- two independent runs must reach the
    identical choice_history, since nothing here is seeded/randomized."""
    run_a_dir = tmp_path / "run_a"
    run_b_dir = tmp_path / "run_b"
    run_a_dir.mkdir()
    run_b_dir.mkdir()
    first = run_demo_colony(run_a_dir)
    second = run_demo_colony(run_b_dir)
    assert first["choice_history"] == second["choice_history"]


def test_run_demo_colony_winner_share_reaches_one(tmp_path: Path) -> None:
    summary = run_demo_colony(tmp_path)
    concentration_history = summary["concentration_history"]
    assert isinstance(concentration_history, list)
    final = concentration_history[-1]
    total = sum(final.values())
    assert total > 0.0
    winner_share = max(final.values()) / total
    assert winner_share == 1.0


def test_run_statistics_sweep_runs_n_real_seeded_trials(tmp_path: Path) -> None:
    config_kwargs: dict[str, object] = {
        "num_agents": 3,
        "locations": LOCATIONS,
        "num_ticks": 5,
        "preference_mean_range": (8.0, 12.0),
        "preference_variance": 1.0,
        "sensing_noise_std": 1.0,
        "deposit_amount": DEMO_DEPOSIT_AMOUNT,
        "decay": DEMO_DECAY,
    }
    results = run_statistics_sweep(tmp_path, num_trials=6, seed_base=100, config_kwargs=config_kwargs)

    assert len(results) == 6
    assert [result.seed for result in results] == list(range(100, 106))
    # Different seeds draw different preferences -- the sweep is not a
    # no-op re-run of the same trial six times.
    assert len({tuple(result.preference_means) for result in results}) > 1


def test_run_statistics_sweep_same_seed_is_reproducible(tmp_path: Path) -> None:
    config_kwargs: dict[str, object] = {
        "num_agents": 3,
        "locations": LOCATIONS,
        "num_ticks": 5,
        "preference_mean_range": (8.0, 12.0),
        "preference_variance": 1.0,
        "sensing_noise_std": 1.0,
        "deposit_amount": DEMO_DEPOSIT_AMOUNT,
        "decay": DEMO_DECAY,
    }
    first = run_statistics_sweep(tmp_path / "a", num_trials=1, seed_base=42, config_kwargs=config_kwargs)
    second = run_statistics_sweep(tmp_path / "b", num_trials=1, seed_base=42, config_kwargs=config_kwargs)

    assert first[0].preference_means == second[0].preference_means
    assert first[0].choice_history == second[0].choice_history
    assert first[0].converged == second[0].converged
