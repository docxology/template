"""Manuscript variable generation tests (strict + negative controls)."""

import json

import pytest

from template_experiment_tree.manuscript_variables import (
    ManuscriptVariablesError,
    generate_variables,
    resolve_tokens,
)
from template_experiment_tree.store import save_tree
from template_experiment_tree.tree import ExperimentTree


def make_store(tmp_path):
    tree = ExperimentTree()
    tree.add_node("E001", "Baseline", "python scripts/run_baseline.py", round_number=1)
    tree.record_answer("E001", "converged", "win")
    store = tmp_path / "tree.json"
    save_tree(tree, store)
    return store


def test_generate_variables_writes_json(tmp_path):
    out = tmp_path / "vars" / "manuscript_variables.json"
    variables = generate_variables(make_store(tmp_path), out)
    assert out.is_file()
    on_disk = json.loads(out.read_text())
    assert on_disk["exp_wins"] == 1
    assert "results" in variables["exp_sections"]


def test_require_answered_fail_closed(tmp_path):
    tree = ExperimentTree()
    tree.add_node("P", "Planned", "cmd planned")
    store = save_tree(tree, tmp_path / "empty.json")
    with pytest.raises(ManuscriptVariablesError, match="no answered nodes"):
        generate_variables(store, tmp_path / "v.json", require_answered=True)


def test_missing_store_fails(tmp_path):
    with pytest.raises(ManuscriptVariablesError, match="not found"):
        generate_variables(tmp_path / "missing.json", tmp_path / "v.json")


def test_resolve_tokens_fail_closed():
    with pytest.raises(ManuscriptVariablesError, match="no tree-derived"):
        resolve_tokens({"x": "{{NOT_A_TOKEN}}"}, {"exp_wins": 1})
