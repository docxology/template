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
from simulation.pymdp_runtime import construct_agent_with_diagnostics
from simulation.si_belief import (
    belief_entropy,
    qs_marginal_state1,
    state_inference_action,
    state_inference_next_obs,
)
from simulation.si_policy import select_policy_action
from simulation.tmaze_model import build_tmaze_generative_model, spec_from_config


def pymdp_available() -> bool:
    """Process pymdp available."""
    try:
        import pymdp  # noqa: F401

        return True
    except ImportError:  # pragma: no cover
        return False


@dataclass(frozen=True)
class SIRunResult:
    """Data container for SIRunResult."""

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
    runtime_diagnostics: dict[str, Any] = field(default_factory=dict)


def _normalise_sampling_distribution(values: np.ndarray, *, label: str) -> np.ndarray:
    """Return a finite non-negative probability vector or fail closed."""
    probs = np.asarray(values, dtype=np.float64).reshape(-1)
    if probs.size == 0 or not np.all(np.isfinite(probs)):
        raise ValueError(f"{label} probabilities must be finite and non-empty")
    if np.any(probs < 0.0):
        raise ValueError(f"{label} probabilities must be non-negative")
    total = float(probs.sum())
    if total <= 0.0:
        raise ValueError(f"{label} probabilities must have positive mass")
    return probs / total


def sample_next_state(rng: np.random.Generator, b: np.ndarray, state: int, action: int) -> int:
    """Process sample next state."""
    transition = np.asarray(b, dtype=np.float64)
    if transition.ndim != 3:
        raise ValueError(f"transition model must be 3-dimensional, got shape {transition.shape}")
    if not 0 <= state < transition.shape[1] or not 0 <= action < transition.shape[2]:
        raise IndexError(f"state/action index out of range: state={state}, action={action}")
    probs = _normalise_sampling_distribution(transition[:, state, action], label="transition")
    return int(rng.choice(probs.size, p=probs))


def sample_observation(rng: np.random.Generator, a: np.ndarray, state: int) -> int:
    """Process sample observation."""
    likelihood = np.asarray(a, dtype=np.float64)
    if likelihood.ndim != 2:
        raise ValueError(f"observation model must be 2-dimensional, got shape {likelihood.shape}")
    if not 0 <= state < likelihood.shape[1]:
        raise IndexError(f"state index out of range: state={state}")
    probs = _normalise_sampling_distribution(likelihood[:, state], label="observation")
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

    cfg = config or load_pymdp_config(project_root)
    if steps is not None:
        cfg = apply_pymdp_overrides(cfg, steps=steps)
    rng = np.random.default_rng(cfg.random_seed)
    model = build_tmaze_generative_model(cfg)
    spec = spec_from_config(cfg)

    agent, runtime_diagnostics = construct_agent_with_diagnostics(
        project_root,
        config=cfg,
        model=model,
        policy_len=spec.policy_len,
        context=f"si_tmaze:{cfg.mode}:h{cfg.horizon}:s{cfg.random_seed}",
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
        policy_evidence: dict[str, Any] = {
            "posterior_available": False,
            "q_pi": [],
            "q_pi_sum": None,
            "q_pi_entropy": None,
            "q_pi_normalized": False,
            "expected_free_energy_available": False,
            "expected_free_energy_values": [],
            "selected_policy_expected_free_energy": None,
            "fallback_reason": "state_inference mode does not call infer_policies",
        }

        if cfg.mode == "policy_inference":
            action, policy_method, expected_free_energy, selected_policy, policy_evidence = select_policy_action(
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
            "policy_posterior_available": policy_evidence.get("posterior_available") is True,
            "policy_posterior_source": policy_evidence.get("posterior_source", policy_method),
            "q_pi": policy_evidence.get("q_pi", []),
            "q_pi_sum": policy_evidence.get("q_pi_sum"),
            "q_pi_entropy": policy_evidence.get("q_pi_entropy"),
            "q_pi_normalized": policy_evidence.get("q_pi_normalized") is True,
            "expected_free_energy_available": policy_evidence.get("expected_free_energy_available") is True,
            "expected_free_energy_values": policy_evidence.get("expected_free_energy_values", []),
            "selected_policy_expected_free_energy": policy_evidence.get("selected_policy_expected_free_energy"),
        }
        if policy_evidence.get("fallback_reason"):
            step_record["fallback_reason"] = policy_evidence["fallback_reason"]
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
            ctx["policy_posterior_available"] = policy_evidence.get("posterior_available") is True

    goal_reached = bool(observations and observations[-1] == goal_obs)
    fallback_reasons = sorted(
        {
            str(step["fallback_reason"])
            for step in trace_steps
            if step.get("fallback_reason") and step.get("policy_method") == "expected_utility_fallback"
        }
    )
    runtime_diagnostics = {
        **runtime_diagnostics,
        "inference_mode": cfg.mode,
        "inference_step_count": n_steps,
        "policy_fallback_count": sum(
            1 for step in trace_steps if step.get("policy_method") == "expected_utility_fallback"
        ),
        "policy_fallback_reasons": fallback_reasons,
        "policy_posterior_available_count": sum(
            1 for step in trace_steps if step.get("policy_posterior_available") is True
        ),
    }
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
        runtime_diagnostics=runtime_diagnostics,
    )
