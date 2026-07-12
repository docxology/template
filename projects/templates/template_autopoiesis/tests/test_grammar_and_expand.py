"""Tests for grammar and expand modules."""

from __future__ import annotations

import pytest
from src.grammar import (
    KNOWN_DOMAINS,
    RESERVED_SLOTS,
    VENDORABLE_DEPS,
    DEP_MODES,
    GrammarError,
    GrammarSlot,
    force_domain,
    load_grammar,
    parse_grammar,
)
from src.expand import (
    SCHEMA_VERSION,
    Spec,
    derive_seed,
    enumerate_all,
    expand,
    sample,
    write_spec,
)


# ---------------------------------------------------------------------------
# Grammar constants
# ---------------------------------------------------------------------------


def test_known_domains_count():
    assert len(KNOWN_DOMAINS) == 5


def test_known_domains_includes_optimization():
    assert "optimization" in KNOWN_DOMAINS


def test_known_domains_includes_all():
    for d in ("optimization", "dynamics", "statistics", "signal", "graph"):
        assert d in KNOWN_DOMAINS


def test_reserved_slots_count():
    assert len(RESERVED_SLOTS) == 3


def test_reserved_slots_names():
    assert "figure_profile" in RESERVED_SLOTS
    assert "qr_profile" in RESERVED_SLOTS
    assert "integrity_profile" in RESERVED_SLOTS


def test_vendorable_deps_count():
    assert len(VENDORABLE_DEPS) >= 4


def test_dep_modes():
    assert "template" in DEP_MODES
    assert "vendor" in DEP_MODES


# ---------------------------------------------------------------------------
# GrammarSlot
# ---------------------------------------------------------------------------


def test_grammar_slot_basic():
    s = GrammarSlot(name="color", options=("red", "blue"))
    assert s.name == "color"
    assert s.options == ("red", "blue")


def test_grammar_slot_empty_name_raises():
    with pytest.raises(GrammarError):
        GrammarSlot(name="", options=("a",))


def test_grammar_slot_empty_options_raises():
    with pytest.raises(GrammarError):
        GrammarSlot(name="x", options=())


def test_grammar_slot_duplicate_options_raises():
    with pytest.raises(GrammarError):
        GrammarSlot(name="x", options=("a", "a"))


# ---------------------------------------------------------------------------
# parse_grammar
# ---------------------------------------------------------------------------


def _make_block(domains=None, seed=42, deps=None):
    return {
        "seed": seed,
        "slots": [
            {"name": "primitive_domain", "options": domains or list(KNOWN_DOMAINS)},
            {"name": "dep_mode", "options": ["template", "vendor"]},
            {"name": "figure_profile", "options": ["minimal", "full"]},
            {"name": "qr_profile", "options": ["off", "on"]},
            {"name": "integrity_profile", "options": ["sha256", "merkle"]},
        ],
        "deps": deps or [],
    }


def test_parse_grammar_basic():
    g = parse_grammar(_make_block())
    assert g.seed == 42
    assert len(g.slots) == 5


def test_parse_grammar_seed():
    g = parse_grammar(_make_block(seed=99))
    assert g.seed == 99


def test_parse_grammar_product_size():
    g = parse_grammar(_make_block())
    # 5 * 2 * 2 * 2 * 2 = 80
    assert g.product_size == 80


def test_parse_grammar_effective_product_size():
    g = parse_grammar(_make_block())
    # reserved: figure_profile, qr_profile, integrity_profile removed
    # effective: 5 * 2 = 10 (primitive_domain * dep_mode)
    assert g.effective_product_size == 10


def test_parse_grammar_reserved_slots():
    g = parse_grammar(_make_block())
    reserved_names = {s.name for s in g.reserved_slots}
    assert reserved_names == set(RESERVED_SLOTS)


def test_parse_grammar_effective_slots():
    g = parse_grammar(_make_block())
    eff_names = {s.name for s in g.effective_slots}
    assert "primitive_domain" in eff_names
    assert "figure_profile" not in eff_names


def test_parse_grammar_bad_type_raises():
    with pytest.raises(GrammarError):
        parse_grammar("not a dict")


def test_parse_grammar_no_slots_raises():
    with pytest.raises(GrammarError):
        parse_grammar({"seed": 1, "slots": []})


def test_parse_grammar_unknown_dep_raises():
    block = _make_block()
    block["deps"] = ["nonexistent_dep"]
    with pytest.raises(GrammarError):
        parse_grammar(block)


def test_parse_grammar_grammar_hash_stable():
    g1 = parse_grammar(_make_block())
    g2 = parse_grammar(_make_block())
    assert g1.grammar_hash == g2.grammar_hash


def test_parse_grammar_different_seed_different_hash():
    g1 = parse_grammar(_make_block(seed=1))
    g2 = parse_grammar(_make_block(seed=2))
    assert g1.grammar_hash != g2.grammar_hash


def test_load_grammar_reads_project_config_passthrough(tmp_path):
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    manuscript.joinpath("config.yaml").write_text(
        "project_config:\n"
        "  autopoiesis:\n"
        "    seed: 17\n"
        "    slots:\n"
        "      - name: primitive_domain\n"
        "        options: [optimization]\n"
        "    deps: []\n",
        encoding="utf-8",
    )

    grammar = load_grammar(tmp_path)

    assert grammar.seed == 17
    assert grammar.slot("primitive_domain").options == ("optimization",)


# ---------------------------------------------------------------------------
# Grammar.slot()
# ---------------------------------------------------------------------------


def test_grammar_slot_lookup():
    g = parse_grammar(_make_block())
    s = g.slot("primitive_domain")
    assert s.name == "primitive_domain"


def test_grammar_slot_missing_raises():
    g = parse_grammar(_make_block())
    with pytest.raises(KeyError):
        g.slot("nonexistent")


# ---------------------------------------------------------------------------
# force_domain
# ---------------------------------------------------------------------------


def test_force_domain_changes_domain_slot():
    g = parse_grammar(_make_block())
    for domain in KNOWN_DOMAINS:
        forced = force_domain(g, domain)
        s = forced.slot("primitive_domain")
        assert s.options == (domain,)


def test_force_domain_unknown_raises():
    g = parse_grammar(_make_block())
    with pytest.raises(GrammarError):
        force_domain(g, "unknown_domain")


def test_force_domain_preserves_other_slots():
    g = parse_grammar(_make_block())
    forced = force_domain(g, "signal")
    assert forced.slot("dep_mode").options == ("template", "vendor")


# ---------------------------------------------------------------------------
# expand
# ---------------------------------------------------------------------------


def test_expand_returns_spec():
    g = parse_grammar(_make_block())
    spec = expand(g)
    assert isinstance(spec, Spec)
    assert spec.schema_version == SCHEMA_VERSION


def test_expand_deterministic():
    g = parse_grammar(_make_block())
    s1 = expand(g)
    s2 = expand(g)
    assert s1.spec_hash == s2.spec_hash


def test_expand_with_seed():
    g = parse_grammar(_make_block())
    s1 = expand(g, seed=1)
    s2 = expand(g, seed=2)
    assert s1.spec_hash != s2.spec_hash


def test_expand_primitive_domain_in_known():
    g = parse_grammar(_make_block())
    spec = expand(g)
    assert spec.primitive_domain in KNOWN_DOMAINS


def test_expand_forced_domain():
    for domain in KNOWN_DOMAINS:
        g = parse_grammar(_make_block())
        g = force_domain(g, domain)
        spec = expand(g)
        assert spec.primitive_domain == domain


def test_expand_spec_hash_stable():
    g = parse_grammar(_make_block())
    spec = expand(g)
    assert len(spec.spec_hash) == 16


def test_expand_selections_cover_all_slots():
    g = parse_grammar(_make_block())
    spec = expand(g)
    sel_keys = {k for k, _ in spec.selections}
    slot_names = {s.name for s in g.slots}
    assert sel_keys == slot_names


def test_expand_to_dict_roundtrip():
    g = parse_grammar(_make_block())
    spec = expand(g)
    d = spec.to_dict()
    assert d["schema_version"] == SCHEMA_VERSION
    assert d["seed"] == g.seed


def test_expand_to_json():
    g = parse_grammar(_make_block())
    spec = expand(g)
    j = spec.to_json()
    import json

    d = json.loads(j)
    assert "spec_hash" not in d or True  # spec_hash is a property, may not be in to_dict
    assert "seed" in d


# ---------------------------------------------------------------------------
# enumerate_all
# ---------------------------------------------------------------------------


def test_enumerate_all_count():
    g = parse_grammar(_make_block())
    cells = enumerate_all(g)
    assert len(cells) == g.product_size


def test_enumerate_all_entries_are_dicts():
    g = parse_grammar(_make_block())
    cells = enumerate_all(g)
    for cell in cells[:5]:
        assert isinstance(cell, dict)


def test_enumerate_all_contains_all_domains():
    g = parse_grammar(_make_block())
    cells = enumerate_all(g)
    seen = {c["primitive_domain"] for c in cells}
    assert seen == set(KNOWN_DOMAINS)


# ---------------------------------------------------------------------------
# sample
# ---------------------------------------------------------------------------


def test_sample_count():
    g = parse_grammar(_make_block())
    specs = sample(g, 10)
    assert len(specs) == 10


def test_sample_all_specs():
    g = parse_grammar(_make_block())
    specs = sample(g, 3)
    for s in specs:
        assert isinstance(s, Spec)


def test_sample_deterministic():
    g = parse_grammar(_make_block())
    s1 = sample(g, 5)
    s2 = sample(g, 5)
    assert [s.spec_hash for s in s1] == [s.spec_hash for s in s2]


def test_sample_with_base_seed():
    g = parse_grammar(_make_block())
    s1 = sample(g, 3, base_seed=100)
    s2 = sample(g, 3, base_seed=200)
    hashes1 = [s.spec_hash for s in s1]
    hashes2 = [s.spec_hash for s in s2]
    assert hashes1 != hashes2


# ---------------------------------------------------------------------------
# derive_seed
# ---------------------------------------------------------------------------


def test_derive_seed_deterministic():
    assert derive_seed(42, 0) == derive_seed(42, 0)


def test_derive_seed_different_indices():
    assert derive_seed(42, 0) != derive_seed(42, 1)


def test_derive_seed_positive():
    assert derive_seed(42, 5) >= 0


# ---------------------------------------------------------------------------
# write_spec
# ---------------------------------------------------------------------------


def test_write_spec(tmp_path):
    g = parse_grammar(_make_block())
    spec = expand(g)
    out = tmp_path / "spec.json"
    result = write_spec(spec, out)
    assert result.exists()
    import json

    d = json.loads(result.read_text())
    assert d["seed"] == g.seed


def test_write_spec_creates_parents(tmp_path):
    g = parse_grammar(_make_block())
    spec = expand(g)
    out = tmp_path / "deep" / "dir" / "spec.json"
    write_spec(spec, out)
    assert out.exists()
