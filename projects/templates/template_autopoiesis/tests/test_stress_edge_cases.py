"""Tests for stress and edge cases."""

from __future__ import annotations

import sys

import pytest

from src.grammar import (
    KNOWN_DOMAINS,
    GrammarSlot,
    parse_grammar,
    GrammarError,
)
from src.expand import expand, derive_seed, sample
from src.integrity import sha256_text, merkle_root


# ---------------------------------------------------------------------------
# Single slot / single option
# ---------------------------------------------------------------------------


def test_single_slot_single_option():
    block = {"seed": 1, "slots": [{"name": "primitive_domain", "options": ["optimization"]}], "deps": []}
    g = parse_grammar(block)
    assert g.product_size == 1
    spec = expand(g)
    assert spec.primitive_domain == "optimization"


def test_single_slot_multiple_options():
    block = {"seed": 1, "slots": [{"name": "primitive_domain", "options": list(KNOWN_DOMAINS)}], "deps": []}
    g = parse_grammar(block)
    assert g.product_size == len(KNOWN_DOMAINS)


def test_zero_options_raises():
    with pytest.raises(GrammarError):
        GrammarSlot(name="x", options=())


def test_zero_slots_raises():
    with pytest.raises(GrammarError):
        parse_grammar({"seed": 1, "slots": [], "deps": []})


# ---------------------------------------------------------------------------
# All reserved slots
# ---------------------------------------------------------------------------


def test_all_reserved_slots_effective_product_one():
    from src.grammar import RESERVED_SLOTS

    block = {
        "seed": 1,
        "slots": [{"name": s, "options": ["a", "b"]} for s in RESERVED_SLOTS],
        "deps": [],
    }
    g = parse_grammar(block)
    assert g.effective_product_size == 1  # no non-reserved slots


# ---------------------------------------------------------------------------
# Boundary seeds
# ---------------------------------------------------------------------------


def test_seed_zero():
    block = {"seed": 0, "slots": [{"name": "primitive_domain", "options": list(KNOWN_DOMAINS)}], "deps": []}
    g = parse_grammar(block)
    spec = expand(g)
    assert spec.primitive_domain in KNOWN_DOMAINS


def test_seed_max_int():
    big = sys.maxsize
    block = {"seed": big, "slots": [{"name": "primitive_domain", "options": list(KNOWN_DOMAINS)}], "deps": []}
    g = parse_grammar(block)
    spec = expand(g)
    assert spec.primitive_domain in KNOWN_DOMAINS


def test_seed_negative_one():
    block = {"seed": -1, "slots": [{"name": "primitive_domain", "options": list(KNOWN_DOMAINS)}], "deps": []}
    g = parse_grammar(block)
    spec = expand(g)
    assert spec.primitive_domain in KNOWN_DOMAINS


# ---------------------------------------------------------------------------
# 1000-seed stress
# ---------------------------------------------------------------------------


def test_1000_seed_stress():
    block = {
        "seed": 42,
        "slots": [
            {"name": "primitive_domain", "options": list(KNOWN_DOMAINS)},
            {"name": "dep_mode", "options": ["template", "vendor"]},
        ],
        "deps": [],
    }
    g = parse_grammar(block)
    seen_hashes = set()
    for i in range(1000):
        seed = derive_seed(42, i)
        spec = expand(g, seed=seed)
        seen_hashes.add(spec.spec_hash)
    # With 1000 distinct seeds, we should see many distinct specs
    assert len(seen_hashes) > 10


# ---------------------------------------------------------------------------
# Merkle invariants
# ---------------------------------------------------------------------------


def test_merkle_empty_is_deterministic():
    h1 = merkle_root([])
    h2 = merkle_root([])
    assert h1 == h2


def test_merkle_order_matters():
    a = sha256_text("a")
    b = sha256_text("b")
    assert merkle_root([a, b]) != merkle_root([b, a])


def test_merkle_odd_leaves_deterministic():
    leaves = [sha256_text(str(i)) for i in range(3)]
    assert merkle_root(leaves) == merkle_root(leaves)


def test_merkle_large_power_of_two():
    leaves = [sha256_text(str(i)) for i in range(16)]
    result = merkle_root(leaves)
    assert len(result) == 64


def test_merkle_single_leaf_is_itself():
    leaf = sha256_text("only_leaf")
    assert merkle_root([leaf]) == leaf


# ---------------------------------------------------------------------------
# Sample boundaries
# ---------------------------------------------------------------------------


def test_sample_zero_count():
    block = {"seed": 42, "slots": [{"name": "primitive_domain", "options": list(KNOWN_DOMAINS)}], "deps": []}
    g = parse_grammar(block)
    specs = sample(g, 0)
    assert specs == []


def test_sample_one_count():
    block = {"seed": 42, "slots": [{"name": "primitive_domain", "options": list(KNOWN_DOMAINS)}], "deps": []}
    g = parse_grammar(block)
    specs = sample(g, 1)
    assert len(specs) == 1


# ---------------------------------------------------------------------------
# derive_seed
# ---------------------------------------------------------------------------


def test_derive_seed_non_negative():
    for i in range(100):
        assert derive_seed(42, i) >= 0


def test_derive_seed_all_distinct_first_100():
    seeds = [derive_seed(42, i) for i in range(100)]
    assert len(set(seeds)) == 100


def test_derive_seed_different_base():
    s1 = derive_seed(1, 0)
    s2 = derive_seed(2, 0)
    assert s1 != s2
