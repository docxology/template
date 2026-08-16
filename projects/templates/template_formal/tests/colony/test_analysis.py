"""Real artifact integration test for the source-owned analysis service."""

from __future__ import annotations

import json
import re
from pathlib import Path

from template_formal.colony.analysis import (
    SWEEP_NUM_TRIALS,
    describe_demo_figure,
    describe_sweep_figure,
    run_publication_analysis,
)
from template_formal.colony.demo import DemoSummary

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_publication_analysis_writes_complete_real_artifact_set(tmp_path: Path) -> None:
    project_root = tmp_path / "formal"
    artifacts = run_publication_analysis(project_root)

    assert all(path.is_file() and path.stat().st_size > 0 for path in artifacts.paths)
    assert len(artifacts.demo_databases) == 3

    sweep = json.loads(artifacts.sweep_summary.read_text(encoding="utf-8"))
    assert sweep["num_trials"] == SWEEP_NUM_TRIALS
    assert sweep["successes"] == 37
    assert len(sweep["consensus_ticks"]) == SWEEP_NUM_TRIALS

    registry = json.loads(artifacts.figure_registry.read_text(encoding="utf-8"))
    assert set(registry) == {"fig:demo-convergence", "fig:convergence-tick-distribution"}
    assert {entry["filename"] for entry in registry.values()} == {
        artifacts.demo_figure.name,
        artifacts.sweep_figure.name,
    }
    references: set[str] = set()
    for path in (PROJECT_ROOT / "manuscript").glob("*.md"):
        if path.name in {"AGENTS.md", "README.md"}:
            continue
        references.update(re.findall(r"\{#(fig:[A-Za-z0-9_:-]+)\}", path.read_text(encoding="utf-8")))
    assert references == set(registry)
    assert all(registry[label]["metadata"]["alt_text"].strip() for label in references)


def test_figure_alt_text_is_derived_from_alternate_analysis_data() -> None:
    alternate_demo: DemoSummary = {
        "num_agents": 2,
        "num_ticks": 2,
        "choice_history": [["south", "south"], ["south", "south"]],
        "concentration_history": [
            {"north": 0.5, "south": 1.0},
            {"north": 0.25, "south": 2.0},
        ],
        "observation_counts": {"agent-a": 2, "agent-b": 2},
        "agent_db_paths": ["agent-a.sqlite3", "agent-b.sqlite3"],
    }

    demo_alt = describe_demo_figure(alternate_demo)
    sweep_alt = describe_sweep_figure([2, None, 7, 2])

    assert "north changes from 0.50 to 0.25" in demo_alt
    assert "south changes from 1.00 to 2.00" in demo_alt
    assert "14.12" not in demo_alt
    assert "3 of 4 converged trials" in sweep_alt
    assert "tick 2 to tick 7" in sweep_alt
    assert "37 of 40" not in sweep_alt


def test_figure_alt_text_handles_empty_or_nonconverged_data() -> None:
    assert "no concentration history" in describe_demo_figure(
        {
            "num_agents": 0,
            "num_ticks": 0,
            "choice_history": [],
            "concentration_history": [],
            "observation_counts": {},
            "agent_db_paths": [],
        }
    )
    assert "no trials" in describe_sweep_figure([])
    assert "none of the 2 trials reached consensus" in describe_sweep_figure([None, None])
