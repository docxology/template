"""Tests for src.composition — mega-madlib token selection and composition."""

from __future__ import annotations

import pytest

from composition import (
    TokenChoice,
    compose_all_sections,
    compose_section_body,
    generate_token_plan,
)
from config import GoldRefinementConfig, load_gold_refinement_config
from pathlib import Path


def _make_config(tmp_path: Path) -> GoldRefinementConfig:
    """Load the real project config for deterministic token tests."""
    project_root = Path(__file__).resolve().parent.parent
    return load_gold_refinement_config(project_root)


class TestGenerateTokenPlan:
    def test_plan_has_choices(self):
        cfg = load_gold_refinement_config(Path(__file__).resolve().parent.parent)
        plan = generate_token_plan(cfg)
        assert len(plan.choices) > 0

    def test_seed_matches_config(self):
        cfg = load_gold_refinement_config(Path(__file__).resolve().parent.parent)
        plan = generate_token_plan(cfg)
        assert plan.seed == cfg.seed

    def test_deterministic_same_seed(self):
        cfg = load_gold_refinement_config(Path(__file__).resolve().parent.parent)
        plan1 = generate_token_plan(cfg)
        plan2 = generate_token_plan(cfg)
        assert plan1.choices == plan2.choices

    def test_different_seed_different_choices(self):
        project_root = Path(__file__).resolve().parent.parent
        cfg1 = load_gold_refinement_config(project_root)
        plan1 = generate_token_plan(cfg1)
        # Modify seed
        cfg2 = GoldRefinementConfig(
            seed=999,
            composition_depth=cfg1.composition_depth,
            hypothesis=cfg1.hypothesis,
            section_conditions=cfg1.section_conditions,
            section_titles=cfg1.section_titles,
            narrative_moves=cfg1.narrative_moves,
            lexicon=cfg1.lexicon,
            slots=cfg1.slots,
        )
        plan2 = generate_token_plan(cfg2)
        # With different seeds, at least some choices should differ
        values1 = [c.value for c in plan1.choices]
        values2 = [c.value for c in plan2.choices]
        assert values1 != values2

    def test_category_counts(self):
        cfg = load_gold_refinement_config(Path(__file__).resolve().parent.parent)
        plan = generate_token_plan(cfg)
        assert "metallurgical_terms" in plan.category_counts
        assert "manuscript_terms" in plan.category_counts

    def test_section_counts(self):
        cfg = load_gold_refinement_config(Path(__file__).resolve().parent.parent)
        plan = generate_token_plan(cfg)
        assert "methodology" in plan.section_counts

    def test_provenance(self):
        cfg = load_gold_refinement_config(Path(__file__).resolve().parent.parent)
        plan = generate_token_plan(cfg)
        prov = plan.provenance
        assert len(prov) == len(plan.choices)
        for var_name, p in prov.items():
            assert "category" in p
            assert "value" in p
            assert "section" in p
            assert "source" in p
            assert "config.yaml" in p["source"]

    def test_values_for_category(self):
        cfg = load_gold_refinement_config(Path(__file__).resolve().parent.parent)
        plan = generate_token_plan(cfg)
        vals = plan.values_for_category("metallurgical_terms")
        assert len(vals) > 0
        # Each value must be from the lexicon
        for v in vals:
            assert v in cfg.lexicon["metallurgical_terms"]

    def test_values_for_section(self):
        cfg = load_gold_refinement_config(Path(__file__).resolve().parent.parent)
        plan = generate_token_plan(cfg)
        vals = plan.values_for_section("methodology")
        assert len(vals) > 0

    def test_first_value(self):
        cfg = load_gold_refinement_config(Path(__file__).resolve().parent.parent)
        plan = generate_token_plan(cfg)
        val = plan.first_value("metallurgical_terms", "default")
        assert val != "default"

    def test_first_value_missing_category(self):
        cfg = load_gold_refinement_config(Path(__file__).resolve().parent.parent)
        plan = generate_token_plan(cfg)
        val = plan.first_value("nonexistent", "fallback")
        assert val == "fallback"


class TestComposeSectionBody:
    def test_methodology_body(self):
        cfg = load_gold_refinement_config(Path(__file__).resolve().parent.parent)
        plan = generate_token_plan(cfg)
        body = compose_section_body("methodology", plan, cfg)
        assert len(body) > 0
        assert "-" in body  # bullet list format

    def test_results_body(self):
        cfg = load_gold_refinement_config(Path(__file__).resolve().parent.parent)
        plan = generate_token_plan(cfg)
        body = compose_section_body("results", plan, cfg)
        assert len(body) > 0

    def test_compose_all_sections(self):
        cfg = load_gold_refinement_config(Path(__file__).resolve().parent.parent)
        plan = generate_token_plan(cfg)
        bodies = compose_all_sections(plan, cfg)
        assert "methodology" in bodies
        assert "results" in bodies
        assert len(bodies) == len(cfg.enabled_sections)


class TestTokenChoice:
    def test_as_dict(self):
        choice = TokenChoice(
            variable_name="TEST",
            slot_name="SLOT",
            category="cat",
            value="val",
            section="sec",
            ordinal=1,
            source_key="src",
        )
        d = choice.as_dict()
        assert d["variable_name"] == "TEST"
        assert d["value"] == "val"


class TestChooseValueEmptyLexicon:
    """_choose_value raises ValueError when lexicon category is empty."""

    def test_empty_lexicon_category_raises(self):
        from composition import _choose_value  # type: ignore[attr-defined]
        from config import GoldRefinementConfig, SlotSpec
        cfg = GoldRefinementConfig(
            seed=1,
            lexicon={"metallurgical_terms": ()},
        )
        slot = SlotSpec(name="T", category="metallurgical_terms", count=1, section="methodology")
        with pytest.raises(ValueError, match="is empty"):
            _choose_value(cfg, slot, 1)
