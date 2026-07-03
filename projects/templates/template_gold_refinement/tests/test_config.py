"""Tests for src.config — mega-madlib config schema and validation."""

from __future__ import annotations

import pytest
import yaml
from pathlib import Path

from config import (
    COMPOSITION_DEPTHS,
    DEFAULT_SECTION_TITLES,
    GOLD_REFINEMENT_SCHEMA_FIELDS,
    GoldRefinementConfigError,
    PROJECT_SCHEMA_EXTENSION,
    REQUIRED_LEXICON_CATEGORIES,
    SECTION_KEYS,
    SlotSpec,
    load_gold_refinement_config,
)


class TestSlotSpec:
    def test_valid_slot(self):
        slot = SlotSpec(name="TEST", category="metallurgical_terms", count=2, section="methodology")
        assert slot.name == "TEST"
        assert slot.count == 2

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="name must not be empty"):
            SlotSpec(name="", category="metallurgical_terms")

    def test_empty_category_raises(self):
        with pytest.raises(ValueError, match="category must not be empty"):
            SlotSpec(name="TEST", category="")

    def test_zero_count_raises(self):
        with pytest.raises(ValueError, match="count must be >= 1"):
            SlotSpec(name="TEST", category="metallurgical_terms", count=0)

    def test_invalid_section_raises(self):
        with pytest.raises(ValueError, match="section must be one of"):
            SlotSpec(name="TEST", category="metallurgical_terms", section="invalid")

    def test_default_section(self):
        slot = SlotSpec(name="TEST", category="metallurgical_terms")
        assert slot.section == "methodology"
        assert slot.count == 1


class TestLoadConfig:
    def test_load_from_project_config(self):
        project_root = Path(__file__).resolve().parent.parent
        cfg = load_gold_refinement_config(project_root)
        assert cfg.seed == 431
        assert cfg.composition_depth == "deep"
        assert "metallurgical_terms" in cfg.lexicon
        assert len(cfg.slots) > 0

    def test_project_configured_rows_survive_parsing(self):
        project_root = Path(__file__).resolve().parent.parent
        config_path = project_root / "manuscript" / "config.yaml"
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))["gold_refinement"]
        cfg = load_gold_refinement_config(project_root)
        for field in (
            "design_principles",
            "quality_probes",
            "failure_modes",
            "authoring_obligations",
            "contribution_claims",
            "pipeline_phases",
            "audit_rules",
            "security_assay",
        ):
            assert getattr(cfg, field) == raw[field]

    def test_infrastructure_loader_accepts_gold_refinement_extension(self, caplog):
        from infrastructure.core.config.loader import load_config
        from infrastructure.core.config.schema import register_project_schema_extension

        register_project_schema_extension("template_gold_refinement", PROJECT_SCHEMA_EXTENSION)
        project_root = Path(__file__).resolve().parent.parent
        config_path = project_root / "manuscript" / "config.yaml"
        with caplog.at_level("WARNING"):
            loaded = load_config(config_path)
        assert loaded is not None
        assert not any("Unknown config key 'gold_refinement'" in record.message for record in caplog.records)

    def test_src_config_does_not_import_infrastructure(self):
        source = (Path(__file__).resolve().parent.parent / "src" / "config.py").read_text(encoding="utf-8")
        assert "from infrastructure." not in source
        assert "import infrastructure." not in source
        assert PROJECT_SCHEMA_EXTENSION == {"gold_refinement": dict}

    def test_load_from_missing_file_returns_defaults(self, tmp_path):
        cfg = load_gold_refinement_config(tmp_path)
        assert cfg.seed == 431
        assert cfg.composition_depth == "deep"
        assert len(cfg.lexicon) > 0
        assert len(cfg.slots) > 0

    def test_load_from_empty_yaml_returns_defaults(self, tmp_path):
        config_dir = tmp_path / "manuscript"
        config_dir.mkdir()
        (config_dir / "config.yaml").write_text("paper:\n  title: Test\n", encoding="utf-8")
        cfg = load_gold_refinement_config(tmp_path)
        assert cfg.seed == 431
        assert len(cfg.lexicon) > 0

    def test_load_with_custom_config(self, tmp_path):
        config_dir = tmp_path / "manuscript"
        config_dir.mkdir()
        (config_dir / "config.yaml").write_text(
            yaml.dump(
                {
                    "gold_refinement": {
                        "seed": 999,
                        "composition_depth": "standard",
                        "lexicon": {
                            "metallurgical_terms": ["a", "b", "c"],
                            "manuscript_terms": ["d", "e"],
                            "purity_adjectives": ["f", "g"],
                            "refinement_verbs": ["h", "i"],
                        },
                        "slots": [
                            {"name": "TEST_SLOT", "category": "metallurgical_terms", "count": 1, "section": "results"},
                        ],
                    }
                }
            ),
            encoding="utf-8",
        )
        cfg = load_gold_refinement_config(tmp_path)
        assert cfg.seed == 999
        assert cfg.composition_depth == "standard"
        assert len(cfg.slots) == 1
        assert cfg.slots[0].name == "TEST_SLOT"

    def test_invalid_composition_depth_raises(self, tmp_path):
        config_dir = tmp_path / "manuscript"
        config_dir.mkdir()
        (config_dir / "config.yaml").write_text(
            yaml.dump(
                {
                    "gold_refinement": {
                        "composition_depth": "invalid",
                        "lexicon": {
                            "metallurgical_terms": ["a"],
                            "manuscript_terms": ["b"],
                            "purity_adjectives": ["c"],
                            "refinement_verbs": ["d"],
                        },
                    }
                }
            ),
            encoding="utf-8",
        )
        with pytest.raises(GoldRefinementConfigError, match="composition_depth"):
            load_gold_refinement_config(tmp_path)

    def test_missing_required_lexicon_raises(self, tmp_path):
        config_dir = tmp_path / "manuscript"
        config_dir.mkdir()
        (config_dir / "config.yaml").write_text(
            yaml.dump(
                {
                    "gold_refinement": {
                        "lexicon": {
                            "metallurgical_terms": ["a"],
                            # missing required categories
                        },
                    }
                }
            ),
            encoding="utf-8",
        )
        with pytest.raises(GoldRefinementConfigError, match="manuscript_terms"):
            load_gold_refinement_config(tmp_path)

    def test_empty_lexicon_category_raises(self, tmp_path):
        config_dir = tmp_path / "manuscript"
        config_dir.mkdir()
        (config_dir / "config.yaml").write_text(
            yaml.dump(
                {
                    "gold_refinement": {
                        "lexicon": {
                            "metallurgical_terms": [],
                            "manuscript_terms": ["b"],
                            "purity_adjectives": ["c"],
                            "refinement_verbs": ["d"],
                        },
                    }
                }
            ),
            encoding="utf-8",
        )
        with pytest.raises(GoldRefinementConfigError, match="metallurgical_terms"):
            load_gold_refinement_config(tmp_path)

    def test_slot_category_not_in_lexicon_raises(self, tmp_path):
        config_dir = tmp_path / "manuscript"
        config_dir.mkdir()
        (config_dir / "config.yaml").write_text(
            yaml.dump(
                {
                    "gold_refinement": {
                        "lexicon": {
                            "metallurgical_terms": ["a"],
                            "manuscript_terms": ["b"],
                            "purity_adjectives": ["c"],
                            "refinement_verbs": ["d"],
                        },
                        "slots": [
                            {"name": "S", "category": "nonexistent", "count": 1},
                        ],
                    }
                }
            ),
            encoding="utf-8",
        )
        with pytest.raises(GoldRefinementConfigError, match="nonexistent"):
            load_gold_refinement_config(tmp_path)

    def test_optional_lexicon_category_allowed(self, tmp_path):
        config_dir = tmp_path / "manuscript"
        config_dir.mkdir()
        (config_dir / "config.yaml").write_text(
            yaml.dump(
                {
                    "gold_refinement": {
                        "lexicon": {
                            "metallurgical_terms": ["a"],
                            "manuscript_terms": ["b"],
                            "purity_adjectives": ["c"],
                            "refinement_verbs": ["d"],
                            "custom_category": ["e", "f"],
                        },
                    }
                }
            ),
            encoding="utf-8",
        )
        cfg = load_gold_refinement_config(tmp_path)
        assert "custom_category" in cfg.lexicon
        assert cfg.lexicon["custom_category"] == ("e", "f")


class TestConfigProperties:
    def test_enabled_sections(self, tmp_path):
        cfg = load_gold_refinement_config(tmp_path)
        # All sections enabled by default
        assert "abstract" in cfg.enabled_sections
        assert len(cfg.enabled_sections) == len(SECTION_KEYS)

    def test_disabled_sections(self, tmp_path):
        config_dir = tmp_path / "manuscript"
        config_dir.mkdir()
        (config_dir / "config.yaml").write_text(
            yaml.dump(
                {
                    "gold_refinement": {
                        "section_conditions": {"abstract": False},
                        "lexicon": {
                            "metallurgical_terms": ["a"],
                            "manuscript_terms": ["b"],
                            "purity_adjectives": ["c"],
                            "refinement_verbs": ["d"],
                        },
                    }
                }
            ),
            encoding="utf-8",
        )
        cfg = load_gold_refinement_config(tmp_path)
        assert "abstract" in cfg.disabled_sections
        assert "abstract" not in cfg.enabled_sections

    def test_total_token_count(self, tmp_path):
        cfg = load_gold_refinement_config(tmp_path)
        expected = sum(s.count for s in cfg.slots)
        assert cfg.total_token_count == expected


class TestConstants:
    def test_required_lexicon_categories(self):
        assert "metallurgical_terms" in REQUIRED_LEXICON_CATEGORIES
        assert "manuscript_terms" in REQUIRED_LEXICON_CATEGORIES
        assert "purity_adjectives" in REQUIRED_LEXICON_CATEGORIES
        assert "refinement_verbs" in REQUIRED_LEXICON_CATEGORIES

    def test_section_keys(self):
        assert "abstract" in SECTION_KEYS
        assert "scope" in SECTION_KEYS

    def test_composition_depths(self):
        assert "deep" in COMPOSITION_DEPTHS
        assert "standard" in COMPOSITION_DEPTHS
        assert "compact" in COMPOSITION_DEPTHS

    def test_default_section_titles(self):
        assert DEFAULT_SECTION_TITLES["abstract"] == "Abstract"

    def test_schema_fields_include_security_assay(self):
        assert "security_assay" in GOLD_REFINEMENT_SCHEMA_FIELDS

    def test_project_lexicon_terms_are_unique(self):
        project_root = Path(__file__).resolve().parent.parent
        cfg = load_gold_refinement_config(project_root)
        for category, terms in cfg.lexicon.items():
            assert len(terms) == len(set(terms)), f"{category} contains duplicate terms: {terms}"


class TestConfigBranchEdgeCases:
    """Cover remaining branch misses in _parse_config."""

    def _make_cfg_yaml(self, tmp_path: Path, extra: dict) -> Path:
        config_dir = tmp_path / "manuscript"
        config_dir.mkdir(parents=True, exist_ok=True)
        base = {
            "gold_refinement": {
                "lexicon": {
                    "metallurgical_terms": ["a"],
                    "manuscript_terms": ["b"],
                    "purity_adjectives": ["c"],
                    "refinement_verbs": ["d"],
                },
            }
        }
        base["gold_refinement"].update(extra)
        import yaml

        (config_dir / "config.yaml").write_text(yaml.dump(base), encoding="utf-8")
        return tmp_path

    def test_optional_lexicon_empty_list_ignored(self, tmp_path):
        """Optional lexicon category with empty list is silently ignored (branch 279→276)."""
        cfg_dir = tmp_path / "manuscript"
        cfg_dir.mkdir()
        import yaml

        (cfg_dir / "config.yaml").write_text(
            yaml.dump(
                {
                    "gold_refinement": {
                        "lexicon": {
                            "metallurgical_terms": ["a"],
                            "manuscript_terms": ["b"],
                            "purity_adjectives": ["c"],
                            "refinement_verbs": ["d"],
                            "empty_optional": [],
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        cfg = load_gold_refinement_config(tmp_path)
        # empty optional category should not be in lexicon
        assert "empty_optional" not in cfg.lexicon

    def test_slot_not_a_dict_raises(self, tmp_path):
        """Slot entry that is not a dict raises GoldRefinementConfigError (line 286)."""
        root = self._make_cfg_yaml(tmp_path, {"slots": ["not_a_dict"]})
        with pytest.raises(GoldRefinementConfigError, match="slot must be a mapping"):
            load_gold_refinement_config(root)

    def test_section_conditions_non_dict_ignored(self, tmp_path):
        """section_conditions as a non-dict is silently ignored (branch 304→309)."""
        root = self._make_cfg_yaml(tmp_path, {"section_conditions": "not_a_dict"})
        cfg = load_gold_refinement_config(root)
        # All sections remain enabled (default)
        assert len(cfg.enabled_sections) == len(SECTION_KEYS)

    def test_section_titles_non_dict_ignored(self, tmp_path):
        """section_titles as a non-dict is silently ignored (branch 311→316)."""
        root = self._make_cfg_yaml(tmp_path, {"section_titles": "not_a_dict"})
        cfg = load_gold_refinement_config(root)
        assert cfg.section_titles["abstract"] == "Abstract"

    def test_narrative_moves_non_dict_ignored(self, tmp_path):
        """narrative_moves as a non-dict is silently ignored (branch 318→323)."""
        root = self._make_cfg_yaml(tmp_path, {"narrative_moves": "not_a_dict"})
        cfg = load_gold_refinement_config(root)
        # Should fall back to defaults
        assert "abstract" in cfg.narrative_moves

    def test_section_conditions_unknown_key_ignored(self, tmp_path):
        """Unknown key in section_conditions is ignored (branch 306→305)."""
        root = self._make_cfg_yaml(tmp_path, {"section_conditions": {"unknown_section": False}})
        cfg = load_gold_refinement_config(root)
        # All known sections remain enabled
        assert len(cfg.enabled_sections) == len(SECTION_KEYS)

    def test_narrative_moves_non_list_value_ignored(self, tmp_path):
        """narrative_moves with non-list value is ignored (branch 320→319)."""
        root = self._make_cfg_yaml(tmp_path, {"narrative_moves": {"abstract": "not_a_list"}})
        cfg = load_gold_refinement_config(root)
        # Default moves retained for abstract
        assert len(cfg.narrative_moves["abstract"]) > 0

    def test_section_titles_unknown_key_ignored(self, tmp_path):
        """Unknown key in section_titles is ignored (branch 313→312)."""
        root = self._make_cfg_yaml(tmp_path, {"section_titles": {"unknown_section": "Title"}})
        cfg = load_gold_refinement_config(root)
        assert "abstract" in cfg.section_titles

    def test_incomplete_security_assay_row_raises(self, tmp_path):
        root = self._make_cfg_yaml(
            tmp_path,
            {
                "security_assay": [
                    {
                        "threat": "implicit trust",
                        "standard": "NIST SP 800-207",
                        "evidence_surface": "output/reports/evidence_registry.json",
                        "validator": "evidence gate",
                    }
                ]
            },
        )
        with pytest.raises(GoldRefinementConfigError, match="security_assay\\[1\\].*claim_boundary"):
            load_gold_refinement_config(root)

    def test_incomplete_existing_config_row_raises(self, tmp_path):
        root = self._make_cfg_yaml(
            tmp_path,
            {
                "quality_probes": [
                    {
                        "name": "probe",
                        "question": "question",
                        "passing_signal": "signal",
                    }
                ]
            },
        )
        with pytest.raises(GoldRefinementConfigError, match="quality_probes\\[1\\].*artifact"):
            load_gold_refinement_config(root)

    def test_config_row_must_be_mapping(self, tmp_path):
        root = self._make_cfg_yaml(tmp_path, {"audit_rules": ["not_a_mapping"]})
        with pytest.raises(GoldRefinementConfigError, match="audit_rules\\[1\\] must be a mapping"):
            load_gold_refinement_config(root)
