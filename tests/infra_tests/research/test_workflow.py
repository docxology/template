"""Tests for infrastructure.research workflow and config."""

from __future__ import annotations

import pytest

from infrastructure.research import (
    ResearchStage,
    ResearchWorkflow,
    StageStatus,
    ResearchWorkflowConfig,
    load_research_workflow_config,
)


# ---------------------------------------------------------------------------
# StageStatus
# ---------------------------------------------------------------------------

class TestStageStatus:
    def test_values(self):
        vals = {s.value for s in StageStatus}
        assert "pending" in vals
        assert "in_progress" in vals
        assert "complete" in vals
        assert "skipped" in vals
        assert "blocked" in vals


# ---------------------------------------------------------------------------
# ResearchStage
# ---------------------------------------------------------------------------

class TestResearchStage:
    def test_defaults(self):
        s = ResearchStage(name="test", label="Test", description="desc")
        assert s.inputs == ()
        assert s.outputs == ()
        assert s.gate == ""
        assert s.status == StageStatus.pending
        assert s.order == 0

    def test_to_dict(self):
        s = ResearchStage(
            name="scope",
            label="Scope",
            description="Define scope",
            inputs=("a.yaml",),
            outputs=("b.yaml",),
            gate="b.yaml exists",
            order=0,
        )
        d = s.to_dict()
        assert d["name"] == "scope"
        assert d["inputs"] == ["a.yaml"]
        assert d["outputs"] == ["b.yaml"]
        assert d["gate"] == "b.yaml exists"
        assert d["status"] == "pending"

    def test_frozen(self):
        s = ResearchStage(name="x", label="X", description="D")
        with pytest.raises((AttributeError, TypeError)):
            s.name = "y"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# ResearchWorkflow
# ---------------------------------------------------------------------------

class TestResearchWorkflow:
    def test_default_has_7_stages(self):
        wf = ResearchWorkflow()
        assert len(wf) == 7

    def test_stage_names(self):
        wf = ResearchWorkflow()
        names = {s.name for s in wf.all_stages()}
        assert names == {"scope", "survey", "hypothesise", "experiment", "validate", "review", "write"}

    def test_stage_by_name(self):
        wf = ResearchWorkflow()
        s = wf.stage("scope")
        assert s.name == "scope"
        assert s.order == 0

    def test_stages_ordered(self):
        wf = ResearchWorkflow()
        orders = [s.order for s in wf.all_stages()]
        assert orders == sorted(orders)

    def test_stage_missing_raises(self):
        wf = ResearchWorkflow()
        with pytest.raises(KeyError, match="bogus"):
            wf.stage("bogus")

    def test_all_stages_returns_list(self):
        wf = ResearchWorkflow()
        stages = wf.all_stages()
        assert isinstance(stages, list)
        assert len(stages) == 7

    def test_describe_includes_stage_names(self):
        wf = ResearchWorkflow()
        desc = wf.describe()
        # describe() uses label.upper(), e.g. "SCOPE" (scope)
        for name in ("SCOPE", "SURVEY", "EXPERIMENT", "WRITE"):
            assert name in desc

    def test_describe_includes_gate(self):
        wf = ResearchWorkflow()
        desc = wf.describe()
        assert "Gate" in desc

    def test_to_dict(self):
        wf = ResearchWorkflow()
        d = wf.to_dict()
        assert "stages" in d
        assert len(d["stages"]) == 7

    def test_each_stage_has_inputs_outputs(self):
        wf = ResearchWorkflow()
        # At least the middle stages should have inputs and outputs
        for name in ("survey", "experiment", "validate"):
            s = wf.stage(name)
            assert len(s.inputs) > 0 or len(s.outputs) > 0

    def test_write_stage_order_is_last(self):
        wf = ResearchWorkflow()
        write = wf.stage("write")
        assert write.order == max(s.order for s in wf.all_stages())

    def test_scope_stage_order_is_first(self):
        wf = ResearchWorkflow()
        scope = wf.stage("scope")
        assert scope.order == 0

    def test_custom_stages(self):
        custom = [
            ResearchStage(name="alpha", label="Alpha", description="First", order=0),
            ResearchStage(name="beta", label="Beta", description="Second", order=1),
        ]
        wf = ResearchWorkflow(stages=custom)
        assert len(wf) == 2
        assert wf.stage("alpha").label == "Alpha"

    def test_repr(self):
        wf = ResearchWorkflow()
        r = repr(wf)
        assert "ResearchWorkflow" in r


# ---------------------------------------------------------------------------
# config.py
# ---------------------------------------------------------------------------

class TestResearchWorkflowConfig:
    def test_defaults_when_no_file(self, tmp_path):
        cfg = load_research_workflow_config(tmp_path)
        assert cfg.enabled is True
        assert cfg.active_stage == ""
        assert cfg.skip_stages == ()
        assert cfg.strict is False
        assert cfg.source_path == ""

    def test_load_full_config(self, tmp_path):
        (tmp_path / "research_workflow.yaml").write_text(
            "enabled: true\n"
            "active_stage: survey\n"
            "skip_stages: [review]\n"
            "strict: true\n"
        )
        cfg = load_research_workflow_config(tmp_path)
        assert cfg.enabled is True
        assert cfg.active_stage == "survey"
        assert cfg.skip_stages == ("review",)
        assert cfg.strict is True
        assert "research_workflow.yaml" in cfg.source_path

    def test_unknown_key_raises(self, tmp_path):
        (tmp_path / "research_workflow.yaml").write_text("bogus_key: 123\n")
        with pytest.raises(ValueError, match="unknown research_workflow"):
            load_research_workflow_config(tmp_path)

    def test_invalid_active_stage_raises(self, tmp_path):
        (tmp_path / "research_workflow.yaml").write_text("active_stage: unknown_stage\n")
        with pytest.raises(ValueError, match="not a valid stage"):
            load_research_workflow_config(tmp_path)

    def test_invalid_skip_stage_raises(self, tmp_path):
        (tmp_path / "research_workflow.yaml").write_text("skip_stages: [not_a_real_stage]\n")
        with pytest.raises(ValueError, match="invalid stages"):
            load_research_workflow_config(tmp_path)

    def test_to_dict(self):
        cfg = ResearchWorkflowConfig(active_stage="scope", strict=True)
        d = cfg.to_dict()
        assert d["active_stage"] == "scope"
        assert d["strict"] is True

    def test_empty_active_stage_allowed(self, tmp_path):
        (tmp_path / "research_workflow.yaml").write_text("active_stage: ''\n")
        cfg = load_research_workflow_config(tmp_path)
        assert cfg.active_stage == ""

    def test_all_valid_stages_accepted(self, tmp_path):
        for stage in ("scope", "survey", "hypothesise", "experiment", "validate", "review", "write"):
            (tmp_path / "research_workflow.yaml").write_text(f"active_stage: {stage}\n")
            cfg = load_research_workflow_config(tmp_path)
            assert cfg.active_stage == stage


# ---------------------------------------------------------------------------
# Prompts directory
# ---------------------------------------------------------------------------

class TestResearchPrompts:
    def test_research_workflow_prompt_exists(self):
        from pathlib import Path
        prompt_path = Path(__file__).parent.parent.parent.parent / "infrastructure/research/prompts/research_workflow.md"
        assert prompt_path.exists(), f"Expected prompt at {prompt_path}"

    def test_literature_review_prompt_exists(self):
        from pathlib import Path
        prompt_path = Path(__file__).parent.parent.parent.parent / "infrastructure/research/prompts/literature_review.md"
        assert prompt_path.exists(), f"Expected prompt at {prompt_path}"

    def test_prompts_are_non_empty(self):
        from pathlib import Path
        base = Path(__file__).parent.parent.parent.parent / "infrastructure/research/prompts"
        for fname in ("research_workflow.md", "literature_review.md"):
            content = (base / fname).read_text(encoding="utf-8")
            assert len(content) > 200, f"{fname} too short"
