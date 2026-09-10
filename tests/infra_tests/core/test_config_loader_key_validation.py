"""Tests for config-key validation — typo detection in ``load_config``."""

from infrastructure.core.config.loader import load_config, validate_config_keys


class TestConfigKeyValidation:
    """Test config key typo detection."""

    def test_unknown_key_logs_warning(self, tmp_path, caplog):
        """Test that unknown config keys produce a warning with typo suggestion."""
        import logging

        import yaml

        config = {
            "papr": {"title": "Typo Test"},  # Typo: should be 'paper'
            "authors": [{"name": "Test Author"}],
        }
        config_file = tmp_path / "typo_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config, f)

        with caplog.at_level(logging.WARNING, logger="infrastructure.core.config.loader"):
            result = load_config(config_file)

        assert result is not None
        # Should warn about 'papr' with suggestion 'paper'
        assert any("papr" in msg and "paper" in msg for msg in caplog.messages)

    def test_known_keys_no_warning(self, tmp_path, caplog):
        """Test that valid config keys produce no warnings."""
        import logging

        import yaml

        config = {
            "paper": {"title": "Valid Config"},
            "authors": [{"name": "Test Author"}],
            "publication": {"doi": "10.1234/test"},
            "keywords": ["optimization"],
            "metadata": {"license": "MIT"},
            "sheaf": {"manifest": "manuscript/sheaf/manifest.yaml"},
            "llm": {"reviews": {"enabled": True}},
            "testing": {"max_test_failures": 0},
            "render": {"formats": {"pdf": True, "html": True, "slides": False}},
            "analysis": {"scripts": ["run_analysis.py"]},
            "manuscript_dir": "manuscript",
            "prose": {"long_sentence_threshold": 35},
            "bibliography": {"references_path": "manuscript/references.bib"},
            "report": {"output_path": "output/review_report.md"},
            "book": {"edition": "1.0"},
            "layout": {"page_size": "letter"},
            "typography": {"body_font": "Latin Modern Roman"},
            "front_matter": {"files": []},
            "rendering": {"number_sections": True},
            "units": [{"id": "unit_1"}],
            "appendices": {"enabled": True},
            "accessibility": {"alt_text_required": True},
            "content_notes": {"audience": "graduate"},
            "chapter_metadata": {"unit_1": {"title": "Unit 1"}},
            "export": {"formats": ["pdf"]},
            "gold_refinement": {"seed": 431},
        }
        config_file = tmp_path / "valid_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config, f)

        with caplog.at_level(logging.WARNING, logger="infrastructure.core.config.loader"):
            result = load_config(config_file)

        assert result is not None
        # No warnings should be logged for valid keys
        config_warnings = [msg for msg in caplog.messages if "Unknown config key" in msg]
        assert config_warnings == []

    def test_validate_config_keys_direct(self):
        """Test validate_config_keys function directly."""
        # Known keys only → no warnings
        warnings = validate_config_keys({"paper": {}, "testing": {}})
        assert warnings == []

        # Unknown key with typo suggestion
        warnings = validate_config_keys({"papr": {}})
        assert len(warnings) == 1
        assert "papr" in warnings[0]
        assert "paper" in warnings[0]

        # Unknown key with no close match
        warnings = validate_config_keys({"zzz_nonsense": {}})
        assert len(warnings) == 1
        assert "zzz_nonsense" in warnings[0]

    def test_validate_config_keys_non_dict(self):
        """Test validate_config_keys handles non-dict input gracefully."""
        warnings = validate_config_keys("not a dict")  # type: ignore[arg-type]
        assert warnings == []
