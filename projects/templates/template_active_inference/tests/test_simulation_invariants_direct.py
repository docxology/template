"""Direct leg-deterministic tests for ``simulation.invariants``.

Each simulation invariant is a boolean gate over the pymdp T-maze summary and
trace artifacts. On the tracked snapshot the invariants pass, so their FAILURE
branches (and the missing-artifact fallbacks in ``_load_summary`` /
``_load_trace``) only ran when a gate happened to rebuild the tree. These tests
build a minimal ``output/data`` skeleton under ``tmp_path`` -- the invariants'
only inputs -- write a valid summary/trace, then mutate one field at a time to
force each specific invariant False. Nothing touches the git-tracked tree.

Every invariant that this file asserts truthy in the valid baseline also has a
paired negative control that forces it falsy. Direct invariant calls are checked
for truthiness rather than identity because ``inv_belief_entropy_finite`` returns
a ``numpy.bool_`` on non-finite input, not a Python ``bool``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from simulation.invariants import (
    SIMULATION_INVARIANTS,
    build_merged_invariants_payload,
    inv_actions_length_matches_steps,
    inv_belief_entropy_finite,
    inv_goal_reached,
    inv_observations_in_obs_space,
    inv_policy_len_matches_config,
    inv_trace_step_count_matches_summary,
    merge_simulation_into_invariants_report,
    run_simulation_invariants,
    write_simulation_invariants,
)


def _valid_summary() -> dict[str, Any]:
    """A summary for which every simulation invariant holds."""
    return {
        "mean_belief_entropy": 0.5,
        "steps": 2,
        "actions": [0, 1],
        "observations": [0, 1],
        "policy_len": 2,
        "goal_reached": True,
        "mode": "state_inference",
        "config": {"tmaze": {"num_obs": 2}, "policy_len": 2},
    }


def _write(root: Path, summary: dict[str, Any] | None, trace_steps: int | None = 2) -> Path:
    """Write summary/trace artifacts under ``root/output/data`` and return root."""
    data_dir = root / "output" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    if summary is not None:
        (data_dir / "si_tmaze_summary.json").write_text(json.dumps(summary), encoding="utf-8")
    if trace_steps is not None:
        trace = {"steps": [{"t": i} for i in range(trace_steps)]}
        (data_dir / "si_tmaze_trace.json").write_text(json.dumps(trace), encoding="utf-8")
    return root


# ---------------------------------------------------------------------------
# Positive baseline: valid artifacts -> all invariants True
# ---------------------------------------------------------------------------


def test_all_invariants_pass_on_valid_artifacts(tmp_path: Path) -> None:
    root = _write(tmp_path, _valid_summary(), trace_steps=2)
    results = run_simulation_invariants(root)
    assert set(results) == set(SIMULATION_INVARIANTS)
    assert all(results.values()), results


# ---------------------------------------------------------------------------
# Per-invariant negative controls (each forces exactly one invariant falsy)
# ---------------------------------------------------------------------------


def test_belief_entropy_false_when_negative(tmp_path: Path) -> None:
    summary = _valid_summary()
    summary["mean_belief_entropy"] = -1.0
    assert not inv_belief_entropy_finite(_write(tmp_path, summary))


def test_belief_entropy_false_when_summary_missing(tmp_path: Path) -> None:
    """No summary file -> default -1.0 -> invariant falsy (_load_summary miss)."""
    root = _write(tmp_path, summary=None, trace_steps=None)
    assert not inv_belief_entropy_finite(root)


def test_belief_entropy_false_on_non_finite(tmp_path: Path) -> None:
    summary = _valid_summary()
    summary["mean_belief_entropy"] = float("inf")
    assert not inv_belief_entropy_finite(_write(tmp_path, summary))


def test_actions_length_false_when_mismatched(tmp_path: Path) -> None:
    summary = _valid_summary()
    summary["actions"] = [0]  # len 1 != steps 2
    assert not inv_actions_length_matches_steps(_write(tmp_path, summary))


def test_actions_length_false_when_zero_steps(tmp_path: Path) -> None:
    summary = _valid_summary()
    summary["steps"] = 0
    summary["actions"] = []
    assert not inv_actions_length_matches_steps(_write(tmp_path, summary))


def test_observations_false_when_out_of_space(tmp_path: Path) -> None:
    summary = _valid_summary()
    summary["observations"] = [0, 5]  # 5 >= num_obs (2)
    assert not inv_observations_in_obs_space(_write(tmp_path, summary))


def test_policy_len_false_when_disagrees_with_config(tmp_path: Path) -> None:
    summary = _valid_summary()
    summary["policy_len"] = 3  # config policy_len is 2
    assert not inv_policy_len_matches_config(_write(tmp_path, summary))


def test_goal_reached_false_when_flag_false(tmp_path: Path) -> None:
    summary = _valid_summary()
    summary["goal_reached"] = False
    assert not inv_goal_reached(_write(tmp_path, summary))


def test_goal_reached_via_observations_when_flag_absent(tmp_path: Path) -> None:
    """Without the flag, the last observation must equal the goal state."""
    hit = _valid_summary()
    del hit["goal_reached"]
    hit["observations"] = [0, 1]  # last == num_obs-1 == 1
    assert inv_goal_reached(_write(tmp_path / "hit", hit))

    miss = _valid_summary()
    del miss["goal_reached"]
    miss["observations"] = [0, 0]  # last 0 != goal state 1
    assert not inv_goal_reached(_write(tmp_path / "miss", miss))


def test_goal_reached_false_when_no_observations(tmp_path: Path) -> None:
    summary = _valid_summary()
    del summary["goal_reached"]
    summary["observations"] = []
    assert not inv_goal_reached(_write(tmp_path, summary))


def test_trace_step_count_false_when_mismatched(tmp_path: Path) -> None:
    root = _write(tmp_path, _valid_summary(), trace_steps=1)  # trace 1 != steps 2
    assert not inv_trace_step_count_matches_summary(root)


def test_trace_step_count_false_when_trace_missing(tmp_path: Path) -> None:
    """No trace file -> [] -> length mismatch (_load_trace miss)."""
    root = _write(tmp_path, _valid_summary(), trace_steps=None)
    assert not inv_trace_step_count_matches_summary(root)


# ---------------------------------------------------------------------------
# build_merged_invariants_payload -- all three branch arms
# ---------------------------------------------------------------------------


def test_merged_payload_uses_live_simulation_when_summary_present(tmp_path: Path) -> None:
    """Summary present -> simulation recomputed and folded into all_pass."""
    root = _write(tmp_path, _valid_summary(), trace_steps=2)
    payload = build_merged_invariants_payload(root, analytical_results={"an": True})
    assert payload["simulation"] and all(payload["simulation"].values())
    assert payload["all_pass"] is True


def test_merged_payload_false_when_analytical_fails(tmp_path: Path) -> None:
    """A failing analytical invariant sinks all_pass even if sim passes."""
    root = _write(tmp_path, _valid_summary(), trace_steps=2)
    payload = build_merged_invariants_payload(root, analytical_results={"an": False})
    assert payload["all_pass"] is False


def test_merged_payload_reuses_existing_simulation_when_no_summary(tmp_path: Path) -> None:
    """No summary but invariants.json carries a simulation block (elif arm)."""
    reports = tmp_path / "output" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "invariants.json").write_text(json.dumps({"simulation": {"prior": True}}), encoding="utf-8")
    payload = build_merged_invariants_payload(tmp_path, analytical_results={"an": True})
    assert payload["simulation"] == {"prior": True}
    assert payload["all_pass"] is True


def test_merged_payload_existing_simulation_can_force_false(tmp_path: Path) -> None:
    """Negative control for the elif arm: a stored failing sim sinks all_pass."""
    reports = tmp_path / "output" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "invariants.json").write_text(json.dumps({"simulation": {"prior": False}}), encoding="utf-8")
    payload = build_merged_invariants_payload(tmp_path, analytical_results={"an": True})
    assert payload["all_pass"] is False


def test_merged_payload_analytical_only_when_no_simulation(tmp_path: Path) -> None:
    """Neither summary nor stored simulation -> analytical-only (else arm)."""
    payload = build_merged_invariants_payload(tmp_path, analytical_results={"an": True})
    assert "simulation" not in payload
    assert payload["all_pass"] is True


# ---------------------------------------------------------------------------
# write_simulation_invariants + merge_simulation_into_invariants_report
# ---------------------------------------------------------------------------


def test_write_simulation_invariants_reports_all_pass(tmp_path: Path) -> None:
    root = _write(tmp_path, _valid_summary(), trace_steps=2)
    out = write_simulation_invariants(root)
    assert out.is_file()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["all_pass"] is True
    assert set(payload["invariants"]) == set(SIMULATION_INVARIANTS)


def test_write_simulation_invariants_records_failure(tmp_path: Path) -> None:
    summary = _valid_summary()
    summary["mean_belief_entropy"] = -1.0  # Python-bool False path (JSON-serializable)
    root = _write(tmp_path, summary, trace_steps=2)
    out = write_simulation_invariants(root)
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["all_pass"] is False
    assert payload["invariants"]["belief_entropy_finite"] is False


def test_merge_simulation_into_invariants_report_folds_simulation(tmp_path: Path) -> None:
    reports = tmp_path / "output" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "invariants.json").write_text(json.dumps({"invariants": {"an": True}}), encoding="utf-8")
    _write(tmp_path, _valid_summary(), trace_steps=2)
    out = merge_simulation_into_invariants_report(tmp_path)
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["simulation"] and all(payload["simulation"].values())
    assert payload["all_pass"] is True


def test_merge_simulation_report_false_when_summary_defective(tmp_path: Path) -> None:
    reports = tmp_path / "output" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "invariants.json").write_text(json.dumps({"invariants": {"an": True}}), encoding="utf-8")
    summary = _valid_summary()
    summary["observations"] = [0, 9]  # out of obs space -> Python-bool False path
    _write(tmp_path, summary, trace_steps=2)
    out = merge_simulation_into_invariants_report(tmp_path)
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["all_pass"] is False
    assert payload["simulation"]["observations_in_obs_space"] is False
