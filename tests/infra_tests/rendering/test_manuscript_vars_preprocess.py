"""Tests for manuscript_vars.yaml placeholder substitution in combined markdown preprocess."""

from __future__ import annotations

from pathlib import Path

from infrastructure.rendering._pdf_combined_renderer import (
    flatten_manuscript_vars,
    preprocess_combined_markdown,
    substitute_manuscript_var_placeholders,
)


class TestManuscriptVarsPreprocess:
    """Placeholder substitution from manuscript_vars.yaml during combined preprocess."""

    def test_flatten_nested_yaml(self):
        """Dotted keys map nested YAML to strings."""
        data = {
            "total_topics": 50,
            "maturity": {"real": 8, "partial": 35},
            "areas": {"FEP": {"count": 14}},
            "verify": {"compiles_true": 0, "compiles_false": 1},
        }
        flat = flatten_manuscript_vars(data)
        assert flat["total_topics"] == "50"
        assert flat["maturity.real"] == "8"
        assert flat["areas.FEP.count"] == "14"
        assert flat["verify.compiles_true"] == "0"

    def test_substitute_special_and_dotted_keys(self):
        """{{maturity.*}}, {{verify.*}}, and {{areas.FEP.count}} expand."""
        flat = flatten_manuscript_vars(
            {
                "total_topics": 3,
                "maturity": {"real": 1, "partial": 2, "aspirational": 0},
                "areas": {"FEP": {"count": 7}},
                "verify": {"x": 1},
            }
        )
        text = (
            "n={{total_topics}} fep={{areas.FEP.count}} "
            "m={{maturity.*}} v={{verify.*}} end"
        )
        out, n = substitute_manuscript_var_placeholders(text, flat)
        assert n >= 4
        assert "{{" not in out
        assert "3" in out
        assert "7" in out
        assert "1 real, 2 partial, 0 aspirational" in out
        assert "verify.x=1" in out

    def test_preprocess_applies_vars_from_manuscript_dir(self, tmp_path):
        """preprocess_combined_markdown replaces placeholders when YAML is present."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        (manuscript_dir / "manuscript_vars.yaml").write_text(
            "total_topics: 42\nmaturity:\n  real: 1\n  partial: 2\n  aspirational: 3\n",
            encoding="utf-8",
        )
        md = "Total {{total_topics}}; {{maturity.*}}."
        result = preprocess_combined_markdown(md, manuscript_dir=manuscript_dir)
        assert result.manuscript_vars_substitutions > 0
        assert "42" in result.content
        assert "1 real, 2 partial, 3 aspirational" in result.content
