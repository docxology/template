"""Tests for infrastructure/core/pipeline/pipeline.yaml.

Verifies that the new Connector Search and Provenance Record stages
are correctly defined in the pipeline YAML.

No mocks. Uses yaml.safe_load on the real file.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
PIPELINE_YAML = REPO_ROOT / "infrastructure" / "core" / "pipeline" / "pipeline.yaml"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_pipeline() -> dict[str, Any]:
    """Load and return the pipeline.yaml as a dict."""
    yaml = pytest.importorskip("yaml", reason="PyYAML required to parse pipeline.yaml")
    with open(PIPELINE_YAML, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    assert isinstance(data, dict), "pipeline.yaml should parse to a dict"
    return data


def _get_stages(pipeline: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the list of stage dicts from the pipeline."""
    stages = pipeline.get("stages", [])
    assert isinstance(stages, list), "pipeline.yaml 'stages' should be a list"
    return stages


def _find_stage(stages: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    """Find a stage by name, or return None."""
    for stage in stages:
        if isinstance(stage, dict) and stage.get("name") == name:
            return stage
    return None


# ---------------------------------------------------------------------------
# Basic YAML validity
# ---------------------------------------------------------------------------


class TestPipelineYamlValid:
    def test_yaml_parses_correctly(self) -> None:
        """pipeline.yaml parses without errors via yaml.safe_load."""
        data = _load_pipeline()
        assert "stages" in data

    def test_pipeline_yaml_exists(self) -> None:
        """pipeline.yaml exists at the expected path."""
        assert PIPELINE_YAML.exists(), f"pipeline.yaml not found at {PIPELINE_YAML}"

    def test_stages_list_nonempty(self) -> None:
        """pipeline.yaml has at least one stage defined."""
        data = _load_pipeline()
        stages = _get_stages(data)
        assert len(stages) > 0


# ---------------------------------------------------------------------------
# Connector Search stage tests
# ---------------------------------------------------------------------------


class TestConnectorSearchStage:
    def test_connector_search_stage_present(self) -> None:
        """pipeline.yaml contains 'Connector Search' stage."""
        data = _load_pipeline()
        stages = _get_stages(data)
        stage = _find_stage(stages, "Connector Search")
        assert stage is not None, "Expected 'Connector Search' stage in pipeline.yaml"

    def test_connector_search_script(self) -> None:
        """Connector Search stage uses the correct script."""
        data = _load_pipeline()
        stage = _find_stage(_get_stages(data), "Connector Search")
        assert stage is not None
        assert stage.get("script") == "scripts/pipeline/stage_08_connector_search.py"

    def test_connector_search_depends_on_project_analysis(self) -> None:
        """Connector Search depends_on 'Project Analysis'."""
        data = _load_pipeline()
        stage = _find_stage(_get_stages(data), "Connector Search")
        assert stage is not None
        deps = stage.get("depends_on", [])
        assert "Project Analysis" in deps

    def test_connector_search_allow_skip(self) -> None:
        """Connector Search has allow_skip=true."""
        data = _load_pipeline()
        stage = _find_stage(_get_stages(data), "Connector Search")
        assert stage is not None
        assert stage.get("allow_skip") is True

    def test_connector_search_has_science_tag(self) -> None:
        """Connector Search has 'science' in its tags."""
        data = _load_pipeline()
        stage = _find_stage(_get_stages(data), "Connector Search")
        assert stage is not None
        tags = stage.get("tags", [])
        assert "science" in tags

    def test_connector_search_not_tagged_core(self) -> None:
        """Connector Search is NOT tagged 'core' (it's opt-in)."""
        data = _load_pipeline()
        stage = _find_stage(_get_stages(data), "Connector Search")
        assert stage is not None
        tags = stage.get("tags", [])
        assert "core" not in tags, "Connector Search should not be a core stage"

    def test_connector_search_has_contract(self) -> None:
        """Connector Search has a contract block."""
        data = _load_pipeline()
        stage = _find_stage(_get_stages(data), "Connector Search")
        assert stage is not None
        assert "contract" in stage, "Expected contract block in Connector Search stage"

    def test_connector_search_contract_has_failure_code(self) -> None:
        """Connector Search contract has failure_code."""
        data = _load_pipeline()
        stage = _find_stage(_get_stages(data), "Connector Search")
        assert stage is not None
        contract = stage.get("contract", {})
        assert contract.get("failure_code") == "CONNECTOR_SEARCH_FAILED"


# ---------------------------------------------------------------------------
# Provenance Record stage tests
# ---------------------------------------------------------------------------


class TestProvenanceRecordStage:
    def test_provenance_record_stage_present(self) -> None:
        """pipeline.yaml contains 'Provenance Record' stage."""
        data = _load_pipeline()
        stages = _get_stages(data)
        stage = _find_stage(stages, "Provenance Record")
        assert stage is not None, "Expected 'Provenance Record' stage in pipeline.yaml"

    def test_provenance_record_script(self) -> None:
        """Provenance Record stage uses the correct script."""
        data = _load_pipeline()
        stage = _find_stage(_get_stages(data), "Provenance Record")
        assert stage is not None
        assert stage.get("script") == "scripts/pipeline/stage_09_provenance_record.py"


def test_stage_keys_are_unique_and_scripts_are_canonical() -> None:
    """Machine keys are stable and scripts resolve from the repository root."""
    stages = _get_stages(_load_pipeline())
    keys = [stage.get("key") for stage in stages]
    assert all(isinstance(key, str) and key for key in keys)
    assert len(keys) == len(set(keys))
    for stage in stages:
        script = stage.get("script")
        if script is not None:
            assert script.startswith("scripts/")
            assert (REPO_ROOT / script).is_file()

    def test_provenance_record_depends_on_connector_search(self) -> None:
        """Provenance Record depends_on 'Connector Search'."""
        data = _load_pipeline()
        stage = _find_stage(_get_stages(data), "Provenance Record")
        assert stage is not None
        deps = stage.get("depends_on", [])
        assert "Connector Search" in deps

    def test_provenance_record_allow_skip(self) -> None:
        """Provenance Record has allow_skip=true."""
        data = _load_pipeline()
        stage = _find_stage(_get_stages(data), "Provenance Record")
        assert stage is not None
        assert stage.get("allow_skip") is True

    def test_provenance_record_has_provenance_tag(self) -> None:
        """Provenance Record has 'provenance' in its tags."""
        data = _load_pipeline()
        stage = _find_stage(_get_stages(data), "Provenance Record")
        assert stage is not None
        tags = stage.get("tags", [])
        assert "provenance" in tags

    def test_provenance_record_not_tagged_core(self) -> None:
        """Provenance Record is NOT tagged 'core' (it's opt-in)."""
        data = _load_pipeline()
        stage = _find_stage(_get_stages(data), "Provenance Record")
        assert stage is not None
        tags = stage.get("tags", [])
        assert "core" not in tags, "Provenance Record should not be a core stage"

    def test_provenance_record_has_args(self) -> None:
        """Provenance Record stage has args (--stage Connector Search)."""
        data = _load_pipeline()
        stage = _find_stage(_get_stages(data), "Provenance Record")
        assert stage is not None
        args = stage.get("args", [])
        assert "--stage" in args or "--stage" in str(args)

    def test_provenance_record_has_contract(self) -> None:
        """Provenance Record has a contract block."""
        data = _load_pipeline()
        stage = _find_stage(_get_stages(data), "Provenance Record")
        assert stage is not None
        assert "contract" in stage

    def test_provenance_record_contract_has_failure_code(self) -> None:
        """Provenance Record contract has failure_code."""
        data = _load_pipeline()
        stage = _find_stage(_get_stages(data), "Provenance Record")
        assert stage is not None
        contract = stage.get("contract", {})
        assert contract.get("failure_code") == "PROVENANCE_RECORD_FAILED"


# ---------------------------------------------------------------------------
# Combined / cross-stage tests
# ---------------------------------------------------------------------------


class TestNewStagesTags:
    def test_new_stages_have_correct_tags(self) -> None:
        """Both new stages have their expected tags."""
        data = _load_pipeline()
        stages = _get_stages(data)

        cs = _find_stage(stages, "Connector Search")
        pr = _find_stage(stages, "Provenance Record")

        assert cs is not None, "Connector Search stage missing"
        assert pr is not None, "Provenance Record stage missing"

        assert "science" in cs.get("tags", []), "Connector Search should have 'science' tag"
        assert "provenance" in pr.get("tags", []), "Provenance Record should have 'provenance' tag"

    def test_new_stages_both_allow_skip(self) -> None:
        """Both new stages have allow_skip=true."""
        data = _load_pipeline()
        stages = _get_stages(data)

        for name in ("Connector Search", "Provenance Record"):
            stage = _find_stage(stages, name)
            assert stage is not None, f"{name} stage missing"
            assert stage.get("allow_skip") is True, f"{name} should have allow_skip=true"

    def test_new_stages_are_after_project_analysis(self) -> None:
        """Both new stages appear after 'Project Analysis' in the stage list."""
        data = _load_pipeline()
        stages = _get_stages(data)

        names = [s.get("name") for s in stages if isinstance(s, dict)]
        pa_idx = names.index("Project Analysis")
        cs_idx = names.index("Connector Search")
        pr_idx = names.index("Provenance Record")

        assert cs_idx > pa_idx, "Connector Search should be after Project Analysis"
        assert pr_idx > pa_idx, "Provenance Record should be after Project Analysis"

    def test_new_stages_are_before_pdf_rendering(self) -> None:
        """Both new stages appear before 'PDF Rendering' in the stage list."""
        data = _load_pipeline()
        stages = _get_stages(data)

        names = [s.get("name") for s in stages if isinstance(s, dict)]
        pdf_idx = names.index("PDF Rendering")
        cs_idx = names.index("Connector Search")
        pr_idx = names.index("Provenance Record")

        assert cs_idx < pdf_idx, "Connector Search should be before PDF Rendering"
        assert pr_idx < pdf_idx, "Provenance Record should be before PDF Rendering"
