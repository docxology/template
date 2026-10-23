from __future__ import annotations
from pathlib import Path
from template_literature_meta_analysis.visualization import style
from template_literature_meta_analysis.visualization.style import VIZ_CONFIG


class TestVizConfig:
    def test_subfield_colors_covers_modafinil_domains(self) -> None:
        for sf in ["clinical_sleep", "cognition", "pharmacology", "psychiatry", "safety", "neuroscience"]:
            assert sf in VIZ_CONFIG["subfield_colors"]

    def test_load_viz_labels_from_config(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "config.yaml").write_text(
            "project_config:\n  subfield_keywords:\n    custom_field: [kw]\n  hypothesis_definitions:\n    H9:\n      name: Custom Hypothesis\n",
            encoding="utf-8",
        )
        old_subfields = dict(style.SUBFIELD_NAMES)
        old_hypotheses = dict(style.HYPOTHESIS_NAMES)
        try:
            style.load_viz_labels_from_config(tmp_path)
            assert style.SUBFIELD_NAMES["custom_field"] == "Custom Field"
            assert style.HYPOTHESIS_NAMES["H9"] == "Custom Hypothesis"
            assert style.HYPOTHESIS_NAMES["CUSTOM_HYPOTHESIS"] == "Custom Hypothesis"
            (manuscript / "config.yaml").write_text(
                "project_config:\n  hypothesis_definitions:\n"
                "    H1:\n      name: Current Domain Claim\n"
                "    H2:\n      id: EXPLICIT_DOMAIN_ID\n      name: Explicit Domain Claim\n",
                encoding="utf-8",
            )
            style.load_viz_labels_from_config(tmp_path)
            assert style.HYPOTHESIS_NAMES["H1"] == "Current Domain Claim"
            assert style.HYPOTHESIS_NAMES["PRIMARY_EFFICACY"] == "Current Domain Claim"
            assert style.HYPOTHESIS_NAMES["H2"] == "Explicit Domain Claim"
            assert style.HYPOTHESIS_NAMES["EXPLICIT_DOMAIN_ID"] == "Explicit Domain Claim"
            from template_literature_meta_analysis.visualization.hypothesis_charts import _format_hypothesis_label

            assert _format_hypothesis_label("PRIMARY_EFFICACY") == "Current Domain Claim"
            assert _format_hypothesis_label("EXPLICIT_DOMAIN_ID") == "Explicit Domain Claim"
            assert _format_hypothesis_label("H1") == "H1: Current Domain Claim"
            assert _format_hypothesis_label("unconfigured_metric") == "Unconfigured Metric"
        finally:
            style.SUBFIELD_NAMES.clear()
            style.SUBFIELD_NAMES.update(old_subfields)
            style.HYPOTHESIS_NAMES.clear()
            style.HYPOTHESIS_NAMES.update(old_hypotheses)
