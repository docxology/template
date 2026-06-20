from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from config import load_madlib_config
from tokens import generate_token_plan
from .helpers import base_payload, write_config


def test_token_plan_is_stable_for_fixed_config(tmp_path: Path) -> None:
    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)

    first = generate_token_plan(config)
    second = generate_token_plan(config)

    assert first == second
    assert [choice.variable_name for choice in first.choices] == [
        "FIRST_ADJECTIVE",
        "NOUN_PAIR_1",
        "NOUN_PAIR_2",
        "METHOD",
    ]


def test_token_plan_changes_when_seed_changes(tmp_path: Path) -> None:
    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)

    original = generate_token_plan(config)
    changed = generate_token_plan(replace(config, seed=config.seed + 1))

    assert [choice.value for choice in original.choices] != [choice.value for choice in changed.choices]


def test_token_plan_changes_when_category_inputs_change(tmp_path: Path) -> None:
    payload = base_payload()
    write_config(tmp_path / "first", payload)
    changed_payload = base_payload()
    changed_payload["madlib"]["lexicon"]["nouns"] = ["section", "pipeline"]
    write_config(tmp_path / "second", changed_payload)

    first = generate_token_plan(load_madlib_config(tmp_path / "first"))
    second = generate_token_plan(load_madlib_config(tmp_path / "second"))

    assert first.values_for_category("nouns") != second.values_for_category("nouns")


def test_provenance_records_category_source_and_section(tmp_path: Path) -> None:
    write_config(tmp_path, base_payload())
    plan = generate_token_plan(load_madlib_config(tmp_path))

    provenance = plan.provenance["FIRST_ADJECTIVE"]

    assert provenance["category"] == "adjectives"
    assert provenance["section"] == "abstract"
    assert str(provenance["source"]).startswith("manuscript/config.yaml#madlib.lexicon.adjectives")
    assert plan.category_counts["nouns"] == 2
    assert plan.section_counts["introduction"] == 2
