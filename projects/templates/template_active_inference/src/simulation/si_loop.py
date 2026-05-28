"""Core sophisticated-inference T-maze simulation loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from simulation.logging_utils import RunLogger
from simulation.pymdp_config import (
    PymdpConfig,
    apply_pymdp_overrides,
    config_hash,
    load_pymdp_config,
)
from simulation.si_belief import (
    belief_entropy,
    qs_marginal_state1,
    state_inference_action,
    state_inference_next_obs,
)
from simulation.si_policy import select_policy_action
from simulation.tmaze_model import build_tmaze_generative_model, spec_from_config


def pymdp_available() -> bool:
    try:
        import pymdp  # noqa: F401

        return True
    except ImportError:  # pragma: no cover
        return False


@dataclass(frozen=True)
class SIRunResult:
    steps: int
    policy_len: int
    num_policies: int
    mean_belief_entropy: float
    actions: list[int]
    observations: list[int]
    mode: str
    config_hash: str
    goal_reached: bool
    action_diversity: int
    trace_steps: list[dict[str, Any]] = field(default_factory=list)


def sample_next_state(rng: np.random.Generator, b: np.ndarray, state: int, action: int) -> int:
    probs = np.asarray(b[:, state, action], dtype=np.float64)
    probs = np.clip(probs, 0.0, None)
    if probs.sum() <= 0:
        return state
    probs /= probs.sum()
    return int(rng.choice(probs.size, p=probs))


def sample_observation(rng: np.random.Generator, a: np.ndarray, state: int) -> int:
    probs = np.asarray(a[:, state], dtype=np.float64)
    probs = np.clip(probs, 0.0, None)
    probs /= probs.sum()
    return int(rng.choice(probs.size, p=probs))


def run_si_tmaze(
    project_root: Path,
    *,
    config: PymdpConfig | None = None,
    steps: int | None = None,
    logger: RunLogger | None = None,
) -> SIRunResult:
    """Run state or policy inference on the minimal T-maze harness."""
    if not pymdp_available():  # pragma: no cover
        raise RuntimeError("inferactively-pymdp is not installed")

    from pymdp.agent import Agent

    cfg = config or load_pymdp_config(project_root)
    if steps is not None:
        cfg = apply_pymdp_overrides(cfg, steps=steps)
    rng = np.random.default_rng(cfg.random_seed)
    model = build_tmaze_generative_model(cfg)
    spec = spec_from_config(cfg)

    def _numpy_factors(factors: list) -> list[np.ndarray]:
        return [np.asarray(factor, dtype=np.float64) for factor in factors]

    agent = Agent(
        A=_numpy_factors(model["A"]),
        B=_numpy_factors(model["B"]),
        C=_numpy_factors(model["C"]),
        D=_numpy_factors(model["D"]),
        policy_len=spec.policy_len,
        inference_algo=cfg.agent.inference_algo,
        action_selection=cfg.agent.action_selection,
    )

    log = logger or RunLogger.from_project_root(
        project_root,
        relative_path=cfg.logging.path,
        enabled=cfg.logging.enabled,
    )
    log.emit_run_header(
        config_hash=config_hash(cfg),
        mode=cfg.mode,
        seed=cfg.random_seed,
        policy_len=spec.policy_len,
    )

    obs = 0
    hidden_state = 0
    goal_obs = spec.num_obs - 1
    actions: list[int] = []
    observations: list[int] = []
    entropies: list[float] = []
    trace_steps: list[dict[str, Any]] = []

    b_matrix = np.asarray(model["B"][0], dtype=np.float64)
    a_matrix = np.asarray(model["A"][0], dtype=np.float64)
    c_matrix = np.asarray(model["C"][0], dtype=np.float64)

    n_steps = cfg.steps
    for t in range(n_steps):
        qs = agent.infer_states([np.array([obs], dtype=np.int32)], agent.D)
        entropy = belief_entropy(qs)
        qs_state1 = qs_marginal_state1(qs)
        selected_policy: int | None = None
        expected_free_energy: float | None = None
        policy_method = cfg.mode

        if cfg.mode == "policy_inference":
            action, policy_method, expected_free_energy, selected_policy = select_policy_action(
                agent,
                qs,
                b=b_matrix,
                c=c_matrix,
                rng=rng,
            )
            hidden_state = sample_next_state(rng, b_matrix, hidden_state, action)
            obs = sample_observation(rng, a_matrix, hidden_state)
        else:
            action = state_inference_action(obs, goal_obs)
            obs = state_inference_next_obs(obs, action)

        actions.append(action)
        observations.append(obs)
        entropies.append(entropy)
        step_record = {
            "step": t,
            "obs": obs,
            "action": action,
            "belief_entropy": entropy,
            "qs_state1": qs_state1,
            "mode": cfg.mode,
            "policy_method": policy_method,
        }
        if selected_policy is not None:
            step_record["selected_policy"] = selected_policy
        if expected_free_energy is not None:
            step_record["expected_free_energy"] = expected_free_energy
        trace_steps.append(step_record)

        with log.timed(event="si_tmaze_step", step=t, obs=obs, action=action) as ctx:
            ctx["belief_entropy"] = entropy
            ctx["policy_len"] = spec.policy_len
            ctx["num_policies"] = int(agent.policies.num_policies)
            ctx["qs_state1"] = qs_state1
            ctx["mode"] = cfg.mode
            if selected_policy is not None:
                ctx["selected_policy"] = selected_policy
            if expected_free_energy is not None:
                ctx["expected_free_energy"] = expected_free_energy

    goal_reached = bool(observations and observations[-1] == goal_obs)
    return SIRunResult(
        steps=n_steps,
        policy_len=spec.policy_len,
        num_policies=int(agent.policies.num_policies),
        mean_belief_entropy=float(np.mean(entropies)) if entropies else 0.0,
        actions=actions,
        observations=observations,
        mode=cfg.mode,
        config_hash=config_hash(cfg),
        goal_reached=goal_reached,
        action_diversity=len(set(actions)),
        trace_steps=trace_steps,
    )
