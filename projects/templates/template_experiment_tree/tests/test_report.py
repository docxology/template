"""Report/summarize/token-resolution tests with negative controls."""

import pytest

from template_experiment_tree.report import (
    flatten_sections,
    render_markdown,
    render_variables,
    resolve_token_map,
    summarize,
)
from template_experiment_tree.tree import ExperimentTree


def make_tree() -> ExperimentTree:
    tree = ExperimentTree()
    tree.add_node("E001", "Baseline", "python scripts/run_baseline.py", round_number=1)
    tree.add_node("E002", "Child", "python scripts/run_child.py --scale 0.5", parent_id="E001")
    tree.record_answer("E001", "converged", "win")
    tree.record_answer("E002", "halving made it worse", "dead_end")
    return tree


def test_summarize_counts():
    summary = summarize(make_tree())
    assert summary["total_nodes"] == 2
    assert summary["answered"] == 2
    assert summary["wins"] == 1
    assert summary["dead_ends"] == 1
    assert summary["max_depth"] == 1
    assert summary["winners_per_round"] == {"1": ["E001"]}


def test_render_markdown_sections():
    text = render_markdown(make_tree())
    assert "## Results (answered nodes)" in text
    assert "## Dead ends (negative-result registry)" in text
    assert "converged" in text
    assert "halving made it worse" in text


def test_render_markdown_empty_tree():
    tree = ExperimentTree()
    tree.add_node("P", "Planned only", "cmd planned")
    text = render_markdown(tree)
    assert "No answered experiments yet" in text
    assert "cmd planned" in text


def test_render_variables_and_flatten_sections():
    variables = render_variables(make_tree())
    assert variables["exp_wins"] == 1
    assert variables["exp_dead_ends"] == 1
    sections = flatten_sections(make_tree())
    assert "E001" in sections["results"]
    assert "No frozen experiments." in sections["in_progress"]
    assert "E002" in sections["dead_ends"]


def test_resolve_token_map_happy_and_fail_closed():
    variables = render_variables(make_tree())
    resolved = resolve_token_map({"wins": "Total wins: {{EXP_WINS}}"}, variables)
    assert resolved["wins"] == "Total wins: 1"
    with pytest.raises(KeyError, match="no tree-derived variable backing"):
        resolve_token_map({"bogus": "{{NO_SUCH_TOKEN}}"}, variables)
