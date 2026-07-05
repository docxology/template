from __future__ import annotations
from pathlib import Path
from visualization import style
from visualization.style import VIZ_CONFIG

class TestVizConfig:
    def test_subfield_colors_covers_modafinil_domains(self)->None:
        for sf in ["clinical_sleep","cognition","pharmacology","psychiatry","safety","neuroscience"]:
            assert sf in VIZ_CONFIG["subfield_colors"]
    def test_load_viz_labels_from_config(self,tmp_path:Path)->None:
        manuscript=tmp_path/"manuscript"; manuscript.mkdir()
        (manuscript/"config.yaml").write_text("project_config:\n  subfield_keywords:\n    custom_field: [kw]\n  hypothesis_definitions:\n    H9:\n      name: Custom Hypothesis\n",encoding="utf-8")
        style.load_viz_labels_from_config(tmp_path)
        assert style.SUBFIELD_NAMES["custom_field"]=="Custom Field"
        assert style.HYPOTHESIS_NAMES["H9"]=="Custom Hypothesis"
