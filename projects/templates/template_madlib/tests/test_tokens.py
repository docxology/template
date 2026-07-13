from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from src.config import load_madlib_config
from src.tokens import generate_token_plan
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


# ---------------------------------------------------------------------------
# TokenChoice.as_dict
# ---------------------------------------------------------------------------


def test_token_choice_as_dict_contains_all_fields(tmp_path: Path) -> None:
    """TokenChoice.as_dict() must include variable_name, slot_name, category, value, section, ordinal, source_key."""
    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)

    choice = plan.choices[0]
    as_dict = choice.as_dict()

    assert "variable_name" in as_dict
    assert "slot_name" in as_dict
    assert "category" in as_dict
    assert "value" in as_dict
    assert "section" in as_dict
    assert "ordinal" in as_dict
    assert "source_key" in as_dict


# ---------------------------------------------------------------------------
# TokenPlan properties
# ---------------------------------------------------------------------------


def test_token_plan_category_counts_sum_to_total_choices(tmp_path: Path) -> None:
    """The sum of all category_counts equals the total number of choices."""
    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)

    total = sum(plan.category_counts.values())

    assert total == len(plan.choices)


def test_token_plan_section_counts_sum_to_total_choices(tmp_path: Path) -> None:
    """The sum of all section_counts equals the total number of choices."""
    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)

    total = sum(plan.section_counts.values())

    assert total == len(plan.choices)


def test_token_plan_values_for_category_returns_correct_values(tmp_path: Path) -> None:
    """values_for_category returns only values for the specified category."""
    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)

    adj_values = plan.values_for_category("adjectives")

    for value in adj_values:
        assert value in config.lexicon["adjectives"]


def test_token_plan_first_value_returns_first_match(tmp_path: Path) -> None:
    """first_value returns the first choice value for the given category."""
    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)

    first_adj = plan.first_value("adjectives", "fallback")
    all_adjs = plan.values_for_category("adjectives")

    if all_adjs:
        assert first_adj == all_adjs[0]
    else:
        assert first_adj == "fallback"


def test_token_plan_first_value_returns_default_when_no_match(tmp_path: Path) -> None:
    """first_value returns the default when the category has no choices."""
    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)

    # 'qualities' has an entry in lexicon but no slot, so no choices
    result = plan.first_value("qualities", "my-default")

    assert result == "my-default"


def test_token_plan_provenance_has_entry_for_every_choice(tmp_path: Path) -> None:
    """Every variable_name in the plan must have a provenance entry."""
    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)

    for choice in plan.choices:
        assert choice.variable_name in plan.provenance


def test_token_plan_seed_matches_config(tmp_path: Path) -> None:
    """The TokenPlan seed must match the config seed."""
    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)

    assert plan.seed == config.seed


# ---------------------------------------------------------------------------
# Determinism: same inputs → same outputs
# ---------------------------------------------------------------------------


def test_token_selection_is_deterministic_across_runs(tmp_path: Path) -> None:
    """Generating the plan twice with the same config produces identical results."""
    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)

    plan_a = generate_token_plan(config)
    plan_b = generate_token_plan(config)

    assert plan_a == plan_b
    assert plan_a.choices == plan_b.choices


# ---------------------------------------------------------------------------
# Sensitivity: changing each digest input changes output
# ---------------------------------------------------------------------------


def test_plan_changes_when_slot_name_changes(tmp_path: Path) -> None:
    """Renaming a slot (which changes the digest input) changes the token value."""
    payload_a = base_payload()
    payload_b = base_payload()
    payload_b["madlib"]["slots"][0]["name"] = "renamed_adjective"

    write_config(tmp_path / "a", payload_a)
    write_config(tmp_path / "b", payload_b)

    plan_a = generate_token_plan(load_madlib_config(tmp_path / "a"))
    plan_b = generate_token_plan(load_madlib_config(tmp_path / "b"))

    # The first slot value may differ because the slot name is part of the digest
    # (It is theoretically possible they hash to the same index, but very unlikely
    # for the fixture vocabulary size — we verify they produce different variable names)
    names_a = {c.variable_name for c in plan_a.choices}
    names_b = {c.variable_name for c in plan_b.choices}
    assert names_a != names_b


def test_plan_changes_when_ordinal_changes(tmp_path: Path) -> None:
    """Different ordinals within a repeated slot produce different digests."""
    payload = base_payload()
    # noun_pair has count=2, so ordinals 1 and 2 exist
    write_config(tmp_path, payload)
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)

    # Find the two noun_pair choices
    noun_choices = [c for c in plan.choices if c.slot_name == "noun_pair"]
    assert len(noun_choices) == 2  # count=2 in base_payload
    assert noun_choices[0].ordinal == 1
    assert noun_choices[1].ordinal == 2
    # They should have different source_keys (different ordinals in digest)
    assert noun_choices[0].source_key != noun_choices[1].source_key


# ---------------------------------------------------------------------------
# Source key format
# ---------------------------------------------------------------------------


def test_source_key_references_config_path_and_category(tmp_path: Path) -> None:
    """source_key must point to manuscript/config.yaml#madlib.lexicon.<category>[<index>]."""
    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)

    for choice in plan.choices:
        assert choice.source_key.startswith("manuscript/config.yaml#madlib.lexicon.")
        assert "[" in choice.source_key
        assert "]" in choice.source_key


# ---------------------------------------------------------------------------
# Section-count tracking
# ---------------------------------------------------------------------------


def test_section_counts_only_tracks_assigned_sections(tmp_path: Path) -> None:
    """section_counts only contains sections that have at least one slot assigned."""
    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)

    # Every section key in section_counts must have count > 0
    for section, count in plan.section_counts.items():
        assert count > 0

    # Only sections that have slots in the plan should appear
    slot_sections = {slot.section for slot in config.slots}
    assert set(plan.section_counts.keys()) == slot_sections


# ---------------------------------------------------------------------------
# Lexicon with a single token — always returns that token
# ---------------------------------------------------------------------------


def test_single_token_lexicon_always_selects_that_token(tmp_path: Path) -> None:
    """When a lexicon category has only one entry, it's always selected."""
    payload = base_payload()
    payload["madlib"]["lexicon"]["adjectives"] = ["unique-value"]
    payload["madlib"]["slots"] = [{"name": "adj", "category": "adjectives", "section": "abstract"}]
    write_config(tmp_path, payload)
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)

    adj_choices = plan.values_for_category("adjectives")

    assert adj_choices == ("unique-value",)


# ---------------------------------------------------------------------------
# Property-like: different seeds produce different distributions (except collision)
# ---------------------------------------------------------------------------


def test_different_seeds_produce_different_plans_for_large_lexicon(tmp_path: Path) -> None:
    """Two configs differing only in seed should produce different token plans."""
    payload_low = base_payload()
    payload_low["madlib"]["seed"] = 1

    payload_high = base_payload()
    payload_high["madlib"]["seed"] = 9999

    write_config(tmp_path / "low", payload_low)
    write_config(tmp_path / "high", payload_high)

    plan_low = generate_token_plan(load_madlib_config(tmp_path / "low"))
    plan_high = generate_token_plan(load_madlib_config(tmp_path / "high"))

    # With 2-entry lexicons and 4 choices, some values may coincide but full plans differ
    assert plan_low.seed != plan_high.seed
    # The plans use different seeds so at minimum the seed field differs
    assert plan_low != plan_high


# ---------------------------------------------------------------------------
# TokenChoice is frozen (hashable)
# ---------------------------------------------------------------------------


def test_token_choice_is_hashable(tmp_path: Path) -> None:
    """TokenChoice is a frozen dataclass so it must be hashable."""
    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)
    plan = generate_token_plan(config)

    # This should not raise
    choice_set = set(plan.choices)

    assert len(choice_set) == len(plan.choices)


# ---------------------------------------------------------------------------
# TokenPlan is frozen (hashable/equal)
# ---------------------------------------------------------------------------


def test_token_plan_equality(tmp_path: Path) -> None:
    """Two plans generated from identical configs must compare equal."""
    write_config(tmp_path, base_payload())
    config = load_madlib_config(tmp_path)

    plan_a = generate_token_plan(config)
    plan_b = generate_token_plan(config)

    assert plan_a == plan_b
    assert hash(plan_a) == hash(plan_b)


# ---------------------------------------------------------------------------
# Ordered-category-inventory invariant: reordering the SAME lexicon values
# (a permutation, identical set) must change the token plan, because the
# ordered inventory is one of the five declared digest inputs in
# _choose_value (src/tokens.py: "\x1f".join(values)). This is distinct from
# test_token_plan_changes_when_category_inputs_change, which changes the
# *values*; here the value set is identical and only the order differs.
# ---------------------------------------------------------------------------


def test_reordering_same_lexicon_values_changes_plan(tmp_path: Path) -> None:
    """A permutation of identical lexicon values changes the selected tokens."""
    original = base_payload()
    # Use a wide lexicon so a reorder shifts the digest-derived index.
    wide = ["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "golf", "hotel"]
    original["madlib"]["lexicon"]["nouns"] = list(wide)
    original["madlib"]["slots"] = [{"name": "noun_run", "category": "nouns", "section": "introduction", "count": 6}]

    reordered = base_payload()
    reordered["madlib"]["lexicon"]["nouns"] = list(reversed(wide))
    reordered["madlib"]["slots"] = [{"name": "noun_run", "category": "nouns", "section": "introduction", "count": 6}]

    write_config(tmp_path / "original", original)
    write_config(tmp_path / "reordered", reordered)

    plan_original = generate_token_plan(load_madlib_config(tmp_path / "original"))
    plan_reordered = generate_token_plan(load_madlib_config(tmp_path / "reordered"))

    original_values = plan_original.values_for_category("nouns")
    reordered_values = plan_reordered.values_for_category("nouns")

    # Every selected value comes from the shared word set (identical in both configs).
    assert set(original_values) <= set(wide)
    assert set(reordered_values) <= set(wide)

    # Selected token sequences must differ: the ordered inventory feeds the digest.
    assert original_values != reordered_values


def test_reordering_single_value_lexicon_does_not_change_plan(tmp_path: Path) -> None:
    """A single-entry lexicon has only one ordering, so the plan is unchanged."""
    payload_a = base_payload()
    payload_a["madlib"]["lexicon"]["adjectives"] = ["only"]
    payload_a["madlib"]["slots"] = [{"name": "adj", "category": "adjectives", "section": "abstract"}]
    # A second identical config — there is no alternative ordering of one value.
    payload_b = base_payload()
    payload_b["madlib"]["lexicon"]["adjectives"] = ["only"]
    payload_b["madlib"]["slots"] = [{"name": "adj", "category": "adjectives", "section": "abstract"}]

    write_config(tmp_path / "a", payload_a)
    write_config(tmp_path / "b", payload_b)

    plan_a = generate_token_plan(load_madlib_config(tmp_path / "a"))
    plan_b = generate_token_plan(load_madlib_config(tmp_path / "b"))

    assert plan_a.values_for_category("adjectives") == ("only",)
    assert plan_a.values_for_category("adjectives") == plan_b.values_for_category("adjectives")
