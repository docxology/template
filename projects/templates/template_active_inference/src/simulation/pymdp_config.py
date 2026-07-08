"""YAML-backed configuration for pymdp T-maze simulations."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Literal

import yaml

SimulationMode = Literal["state_inference", "policy_inference"]


@dataclass(frozen=True)
class TMazeConfig:
    """Data container for TMazeConfig."""

    num_states: int = 2
    num_obs: int = 2
    num_actions: int = 2
    likelihood_diag: float = 0.9
    preference_goal: float = 2.0


@dataclass(frozen=True)
class AgentConfig:
    """Data container for AgentConfig."""

    inference_algo: str = "fpi"
    action_selection: str = "deterministic"


@dataclass(frozen=True)
class LoggingConfig:
    """Data container for LoggingConfig."""

    enabled: bool = True
    path: str = "output/logs/pymdp_runs.jsonl"


@dataclass(frozen=True)
class ComparisonConfig:
    """Data container for ComparisonConfig."""

    horizons: tuple[int, ...] = (2, 3)
    seeds: tuple[int, ...] = (0,)
    modes: tuple[SimulationMode, ...] = ("state_inference", "policy_inference")


@dataclass(frozen=True)
class PymdpConfig:
    """Data container for PymdpConfig."""

    horizon: int = 2
    steps: int = 2
    random_seed: int = 0
    mode: SimulationMode = "state_inference"
    tmaze: TMazeConfig = TMazeConfig()
    agent: AgentConfig = AgentConfig()
    logging: LoggingConfig = LoggingConfig()
    comparison: ComparisonConfig = ComparisonConfig()

    @property
    def policy_len(self) -> int:
        """Process policy len."""
        return self.horizon


def _coerce_mode(value: Any) -> SimulationMode:
    mode = str(value or "state_inference")
    if mode not in {"state_inference", "policy_inference"}:
        raise ValueError(f"unsupported pymdp mode: {mode!r}")
    return mode  # type: ignore[return-value]


def _parse_raw(raw: dict[str, Any]) -> PymdpConfig:
    tmaze_raw = raw.get("tmaze") or {}
    agent_raw = raw.get("agent") or {}
    logging_raw = raw.get("logging") or {}
    comparison_raw = raw.get("comparison") or {}
    horizon = int(raw.get("horizon", 2))
    comparison_horizons = tuple(int(value) for value in comparison_raw.get("horizons", (horizon, horizon + 1)))
    comparison_seeds = tuple(int(value) for value in comparison_raw.get("seeds", (int(raw.get("random_seed", 0)),)))
    comparison_modes = tuple(
        _coerce_mode(value) for value in comparison_raw.get("modes", ("state_inference", "policy_inference"))
    )
    return PymdpConfig(
        horizon=horizon,
        steps=int(raw.get("steps", raw.get("horizon", 2))),
        random_seed=int(raw.get("random_seed", 0)),
        mode=_coerce_mode(raw.get("mode")),
        tmaze=TMazeConfig(
            num_states=int(tmaze_raw.get("num_states", 2)),
            num_obs=int(tmaze_raw.get("num_obs", 2)),
            num_actions=int(tmaze_raw.get("num_actions", 2)),
            likelihood_diag=float(tmaze_raw.get("likelihood_diag", 0.9)),
            preference_goal=float(tmaze_raw.get("preference_goal", 2.0)),
        ),
        agent=AgentConfig(
            inference_algo=str(agent_raw.get("inference_algo", "fpi")),
            action_selection=str(agent_raw.get("action_selection", "deterministic")),
        ),
        logging=LoggingConfig(
            enabled=bool(logging_raw.get("enabled", True)),
            path=str(logging_raw.get("path", "output/logs/pymdp_runs.jsonl")),
        ),
        comparison=ComparisonConfig(
            horizons=comparison_horizons,
            seeds=comparison_seeds,
            modes=comparison_modes,
        ),
    )


def default_pymdp_config() -> PymdpConfig:
    """Process default pymdp config."""
    return PymdpConfig()


def pymdp_config_path(project_root: Path) -> Path:
    """Process pymdp config path."""
    return project_root.resolve() / "pymdp.yaml"


def load_pymdp_config(
    project_root: Path,
    *,
    config_path: Path | None = None,
) -> PymdpConfig:
    """Load pymdp config from a file."""
    path = config_path or pymdp_config_path(project_root)
    if not path.is_file():
        return default_pymdp_config()
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return _parse_raw(raw)


def apply_pymdp_overrides(
    config: PymdpConfig,
    *,
    steps: int | None = None,
    horizon: int | None = None,
    seed: int | None = None,
    mode: SimulationMode | None = None,
    logging_enabled: bool | None = None,
) -> PymdpConfig:
    """Process apply pymdp overrides."""
    updated = config
    if horizon is not None:
        updated = replace(updated, horizon=horizon)
    if steps is not None:
        updated = replace(updated, steps=steps)
    if seed is not None:
        updated = replace(updated, random_seed=seed)
    if mode is not None:
        updated = replace(updated, mode=mode)
    if logging_enabled is not None:
        updated = replace(updated, logging=replace(updated.logging, enabled=logging_enabled))
    return updated


def config_snapshot(config: PymdpConfig) -> dict[str, Any]:
    """Process config snapshot."""
    return {
        "horizon": config.horizon,
        "steps": config.steps,
        "random_seed": config.random_seed,
        "mode": config.mode,
        "policy_len": config.policy_len,
        "tmaze": {
            "num_states": config.tmaze.num_states,
            "num_obs": config.tmaze.num_obs,
            "num_actions": config.tmaze.num_actions,
            "likelihood_diag": config.tmaze.likelihood_diag,
            "preference_goal": config.tmaze.preference_goal,
        },
        "agent": {
            "inference_algo": config.agent.inference_algo,
            "action_selection": config.agent.action_selection,
        },
        "logging": {
            "enabled": config.logging.enabled,
            "path": config.logging.path,
        },
        "comparison": {
            "horizons": list(config.comparison.horizons),
            "seeds": list(config.comparison.seeds),
            "modes": list(config.comparison.modes),
        },
    }


def config_hash(config: PymdpConfig) -> str:
    """Process config hash."""
    payload = json.dumps(config_snapshot(config), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
