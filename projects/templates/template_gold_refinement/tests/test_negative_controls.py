"""Negative-control tests: deliberately broken inputs must fail correctly."""

from __future__ import annotations

import pytest
import yaml
from pathlib import Path

from config import GoldRefinementConfigError, load_gold_refinement_config
from purity import karat_for_purity, assert_monotone_increase
from refinery import RefinementStage, run_refinery


class TestBrokenConfig:
    """Config with deliberately broken values must raise errors."""

    def _make_config(self, tmp_path: Path, gold_refinement: dict) -> Path:
        config_dir = tmp_path / "manuscript"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "config.yaml").write_text(
            yaml.dump({"gold_refinement": gold_refinement}),
            encoding="utf-8",
        )
        return tmp_path

    def test_non_monotone_purity_in_config_stages(self, tmp_path):
        """Config with non-monotone purity in refinery stages is not
        directly validated by config.py, but run_refinery must catch it."""
        # This tests that the refinery itself enforces monotonicity
        bad_stages = (
            RefinementStage("a", "op", "mop", 0.5, 0.3, 1),
        )
        with pytest.raises(ValueError, match="monotonically"):
            run_refinery(stages=bad_stages)

    def test_empty_seed_raises(self, tmp_path):
        """Seed must be an integer."""
        root = self._make_config(tmp_path, {
            "seed": "not_a_number",
            "lexicon": {
                "metallurgical_terms": ["a"],
                "manuscript_terms": ["b"],
                "purity_adjectives": ["c"],
                "refinement_verbs": ["d"],
            },
        })
        with pytest.raises((ValueError, TypeError)):
            load_gold_refinement_config(root)

    def test_non_dict_lexicon_raises(self, tmp_path):
        """Config with lexicon as a string (not dict) must raise."""
        root = self._make_config(tmp_path, {
            "lexicon": "not_a_dict",
        })
        with pytest.raises(GoldRefinementConfigError, match="lexicon must be a mapping"):
            load_gold_refinement_config(root)

    def test_slot_with_invalid_section(self, tmp_path):
        """Slot with an invalid section name must raise."""
        root = self._make_config(tmp_path, {
            "lexicon": {
                "metallurgical_terms": ["a", "b", "c"],
                "manuscript_terms": ["d", "e"],
                "purity_adjectives": ["f", "g"],
                "refinement_verbs": ["h", "i"],
            },
            "slots": [
                {"name": "S", "category": "metallurgical_terms", "count": 1, "section": "invalid_section"},
            ],
        })
        with pytest.raises(ValueError, match="section must be one of"):
            load_gold_refinement_config(root)

    def test_slot_count_zero(self, tmp_path):
        """Slot with count=0 must raise."""
        root = self._make_config(tmp_path, {
            "lexicon": {
                "metallurgical_terms": ["a"],
                "manuscript_terms": ["b"],
                "purity_adjectives": ["c"],
                "refinement_verbs": ["d"],
            },
            "slots": [
                {"name": "S", "category": "metallurgical_terms", "count": 0},
            ],
        })
        with pytest.raises(ValueError, match="count must be >= 1"):
            load_gold_refinement_config(root)


class TestBrokenPurity:
    """Purity utility must reject invalid values."""

    def test_negative_purity(self):
        with pytest.raises(ValueError, match="purity must be in"):
            karat_for_purity(-0.1)

    def test_purity_above_one(self):
        with pytest.raises(ValueError, match="purity must be in"):
            karat_for_purity(1.5)

    def test_equal_purity_not_monotone(self):
        with pytest.raises(ValueError, match="monotonically"):
            assert_monotone_increase([0.5, 0.5])

    def test_decreasing_purity(self):
        with pytest.raises(ValueError, match="monotonically"):
            assert_monotone_increase([0.9, 0.3])


class TestBrokenRefinery:
    """Refinery must reject malformed stage configurations."""

    def test_empty_pipeline(self):
        with pytest.raises(ValueError, match="at least one stage"):
            run_refinery(stages=())

    def test_wrong_order(self):
        bad = (
            RefinementStage("a", "op", "mop", 0.1, 0.5, 5),
        )
        with pytest.raises(ValueError, match="Stage order mismatch"):
            run_refinery(stages=bad)

    def test_non_monotone_pipeline(self):
        bad = (
            RefinementStage("a", "op", "mop", 0.5, 0.3, 1),
            RefinementStage("b", "op", "mop", 0.3, 0.9, 2),
        )
        with pytest.raises(ValueError, match="monotonically"):
            run_refinery(stages=bad)
