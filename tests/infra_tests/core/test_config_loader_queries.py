"""Tests for ``infrastructure.core.config.queries`` — translation, review, and testing queries.

Covers ``get_translation_languages``, ``get_review_types`` defaults and
filtering, and ``get_testing_config`` resolution against real YAML configs.
"""

from infrastructure.core.config.loader import ResolvedTestingConfig
from infrastructure.core.config.queries import get_testing_config, get_translation_languages


class TestGetTranslationLanguages:
    """Test get_translation_languages function."""

    def test_returns_empty_when_no_config(self, tmp_path):
        """Test returns empty list when config file doesn't exist."""
        result = get_translation_languages(tmp_path)
        assert result == []

    def test_returns_empty_when_translations_disabled(self, tmp_path):
        """Test returns empty list when translations are disabled."""
        import yaml

        config = {"llm": {"translations": {"enabled": False, "languages": ["zh", "hi", "ru"]}}}
        config_file = tmp_path / "projects" / "project" / "manuscript" / "config.yaml"
        config_file.parent.mkdir(parents=True)
        with open(config_file, "w") as f:
            yaml.dump(config, f)

        result = get_translation_languages(tmp_path)
        assert result == []

    def test_returns_empty_when_no_llm_section(self, tmp_path):
        """Test returns empty list when no llm section in config."""
        import yaml

        config = {"paper": {"title": "Test"}}
        config_file = tmp_path / "projects" / "project" / "manuscript" / "config.yaml"
        config_file.parent.mkdir(parents=True)
        with open(config_file, "w") as f:
            yaml.dump(config, f)

        result = get_translation_languages(tmp_path)
        assert result == []

    def test_returns_languages_when_enabled(self, tmp_path):
        """Test returns language list when translations are enabled."""
        import yaml

        config = {"llm": {"translations": {"enabled": True, "languages": ["zh", "hi", "ru"]}}}
        config_file = tmp_path / "projects" / "project" / "manuscript" / "config.yaml"
        config_file.parent.mkdir(parents=True)
        with open(config_file, "w") as f:
            yaml.dump(config, f)

        result = get_translation_languages(tmp_path)
        assert result == ["zh", "hi", "ru"]

    def test_returns_single_language(self, tmp_path):
        """Test returns single language when only one configured."""
        import yaml

        config = {"llm": {"translations": {"enabled": True, "languages": ["zh"]}}}
        config_file = tmp_path / "projects" / "project" / "manuscript" / "config.yaml"
        config_file.parent.mkdir(parents=True)
        with open(config_file, "w") as f:
            yaml.dump(config, f)

        result = get_translation_languages(tmp_path)
        assert result == ["zh"]

    def test_returns_empty_for_invalid_languages_type(self, tmp_path):
        """Test returns empty list when languages is not a list."""
        import yaml

        config = {
            "llm": {
                "translations": {
                    "enabled": True,
                    "languages": "zh",  # String instead of list
                }
            }
        }
        config_file = tmp_path / "projects" / "project" / "manuscript" / "config.yaml"
        config_file.parent.mkdir(parents=True)
        with open(config_file, "w") as f:
            yaml.dump(config, f)

        result = get_translation_languages(tmp_path)
        assert result == []


class TestGetReviewTypes:
    """Test get_review_types function."""

    def test_returns_default_when_no_config(self, tmp_path):
        """Test returns default review type when config file doesn't exist."""
        from infrastructure.core.config.queries import get_review_types

        result = get_review_types(tmp_path)
        assert result == ["executive_summary"]

    def test_returns_default_when_config_cant_load(self, tmp_path):
        """When YAML cannot be parsed, load_config returns None and defaults apply."""
        from infrastructure.core.config.queries import get_review_types

        config_file = tmp_path / "projects" / "project" / "manuscript" / "config.yaml"
        config_file.parent.mkdir(parents=True)
        config_file.write_text("invalid: yaml: [unclosed")

        result = get_review_types(tmp_path)
        assert result == ["executive_summary"]

    def test_returns_empty_when_reviews_disabled(self, tmp_path):
        """Test returns empty list when reviews are disabled."""
        import yaml

        from infrastructure.core.config.queries import get_review_types

        config = {
            "llm": {
                "reviews": {
                    "enabled": False,
                    "types": ["executive_summary", "quality_review"],
                }
            }
        }
        config_file = tmp_path / "projects" / "project" / "manuscript" / "config.yaml"
        config_file.parent.mkdir(parents=True)
        with open(config_file, "w") as f:
            yaml.dump(config, f)

        result = get_review_types(tmp_path)
        assert result == []

    def test_returns_default_when_no_llm_section(self, tmp_path):
        """Test returns default review type when no llm section in config."""
        import yaml

        from infrastructure.core.config.queries import get_review_types

        config = {"paper": {"title": "Test"}}
        config_file = tmp_path / "projects" / "project" / "manuscript" / "config.yaml"
        config_file.parent.mkdir(parents=True)
        with open(config_file, "w") as f:
            yaml.dump(config, f)

        result = get_review_types(tmp_path)
        assert result == ["executive_summary"]

    def test_returns_default_when_no_reviews_section(self, tmp_path):
        """Test returns default review type when no reviews section in config."""
        import yaml

        from infrastructure.core.config.queries import get_review_types

        config = {"llm": {"translations": {"enabled": True, "languages": ["zh"]}}}
        config_file = tmp_path / "projects" / "project" / "manuscript" / "config.yaml"
        config_file.parent.mkdir(parents=True)
        with open(config_file, "w") as f:
            yaml.dump(config, f)

        result = get_review_types(tmp_path)
        assert result == ["executive_summary"]

    def test_returns_review_types_when_enabled(self, tmp_path):
        """Test returns review type list when reviews are enabled."""
        import yaml

        from infrastructure.core.config.queries import get_review_types

        config = {
            "llm": {
                "reviews": {
                    "enabled": True,
                    "types": ["executive_summary", "quality_review"],
                }
            }
        }
        config_file = tmp_path / "projects" / "project" / "manuscript" / "config.yaml"
        config_file.parent.mkdir(parents=True)
        with open(config_file, "w") as f:
            yaml.dump(config, f)

        result = get_review_types(tmp_path)
        assert result == ["executive_summary", "quality_review"]

    def test_returns_single_review_type(self, tmp_path):
        """Test returns single review type when only one configured."""
        import yaml

        from infrastructure.core.config.queries import get_review_types

        config = {"llm": {"reviews": {"enabled": True, "types": ["executive_summary"]}}}
        config_file = tmp_path / "projects" / "project" / "manuscript" / "config.yaml"
        config_file.parent.mkdir(parents=True)
        with open(config_file, "w") as f:
            yaml.dump(config, f)

        result = get_review_types(tmp_path)
        assert result == ["executive_summary"]

    def test_returns_default_for_empty_types_list(self, tmp_path):
        """Test returns default review type when types list is empty."""
        import yaml

        from infrastructure.core.config.queries import get_review_types

        config = {"llm": {"reviews": {"enabled": True, "types": []}}}
        config_file = tmp_path / "projects" / "project" / "manuscript" / "config.yaml"
        config_file.parent.mkdir(parents=True)
        with open(config_file, "w") as f:
            yaml.dump(config, f)

        result = get_review_types(tmp_path)
        assert result == ["executive_summary"]

    def test_filters_invalid_review_types(self, tmp_path):
        """Test filters out invalid review types and returns valid ones."""
        import logging

        import yaml

        from infrastructure.core.config.queries import get_review_types

        # Capture warnings
        with tmp_path.joinpath("test.log").open("w") as log_file:
            handler = logging.StreamHandler(log_file)
            logger = logging.getLogger("infrastructure.core.config.loader")
            logger.addHandler(handler)
            logger.setLevel(logging.WARNING)

            config = {
                "llm": {
                    "reviews": {
                        "enabled": True,
                        "types": [
                            "executive_summary",
                            "invalid_type",
                            "quality_review",
                            "another_invalid",
                        ],
                    }
                }
            }
            config_file = tmp_path / "projects" / "project" / "manuscript" / "config.yaml"
            config_file.parent.mkdir(parents=True)
            with open(config_file, "w") as f:
                yaml.dump(config, f)

            result = get_review_types(tmp_path)
            assert result == ["executive_summary", "quality_review"]
            assert "invalid_type" not in result
            assert "another_invalid" not in result

    def test_returns_default_when_all_types_invalid(self, tmp_path):
        """Test returns default review type when all configured types are invalid."""
        import yaml

        from infrastructure.core.config.queries import get_review_types

        config = {
            "llm": {
                "reviews": {
                    "enabled": True,
                    "types": ["invalid_type1", "invalid_type2"],
                }
            }
        }
        config_file = tmp_path / "projects" / "project" / "manuscript" / "config.yaml"
        config_file.parent.mkdir(parents=True)
        with open(config_file, "w") as f:
            yaml.dump(config, f)

        result = get_review_types(tmp_path)
        assert result == ["executive_summary"]

    def test_returns_default_for_invalid_types_type(self, tmp_path):
        """Test returns default review type when types is not a list."""
        import yaml

        from infrastructure.core.config.queries import get_review_types

        config = {
            "llm": {
                "reviews": {
                    "enabled": True,
                    "types": "executive_summary",  # String instead of list
                }
            }
        }
        config_file = tmp_path / "projects" / "project" / "manuscript" / "config.yaml"
        config_file.parent.mkdir(parents=True)
        with open(config_file, "w") as f:
            yaml.dump(config, f)

        result = get_review_types(tmp_path)
        assert result == ["executive_summary"]

    def test_returns_all_valid_review_types(self, tmp_path):
        """Test returns all valid review types when all are configured."""
        import yaml

        from infrastructure.core.config.queries import get_review_types

        config = {
            "llm": {
                "reviews": {
                    "enabled": True,
                    "types": [
                        "executive_summary",
                        "quality_review",
                        "methodology_review",
                        "improvement_suggestions",
                    ],
                }
            }
        }
        config_file = tmp_path / "projects" / "project" / "manuscript" / "config.yaml"
        config_file.parent.mkdir(parents=True)
        with open(config_file, "w") as f:
            yaml.dump(config, f)

        result = get_review_types(tmp_path)
        assert len(result) == 4
        assert "executive_summary" in result
        assert "quality_review" in result
        assert "methodology_review" in result
        assert "improvement_suggestions" in result


class TestTestingConfig:
    """Test testing configuration functions."""

    def test_get_testing_config_no_config(self, tmp_path):
        """Test get_testing_config with no config file."""
        result = get_testing_config(tmp_path)
        assert result == ResolvedTestingConfig(infra_coverage_threshold=60, project_coverage_threshold=90)

    def test_get_testing_config_with_testing_section(self, tmp_path):
        """Test get_testing_config with testing section."""
        config_path = tmp_path / "projects" / "myproject" / "manuscript" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(
            """
testing:
  max_test_failures: 5
  max_infra_test_failures: 2
  max_project_test_failures: 1
"""
        )

        result = get_testing_config(tmp_path)
        expected = ResolvedTestingConfig(
            max_test_failures=5,
            max_infra_test_failures=2,
            max_project_test_failures=1,
            infra_coverage_threshold=60,
            project_coverage_threshold=90,
        )
        assert result == expected
