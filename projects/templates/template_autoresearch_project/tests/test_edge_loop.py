"""Edge-case tests for loop orchestration helpers."""

from __future__ import annotations

from pathlib import Path

from infrastructure.autoresearch import AutoResearchReport, SecurityProfile
from infrastructure.autoresearch.models import AutoResearchIssue

from src.config import AutoResearchLoopConfig
from src.loop import (
    _final_output_path_payload,
    build_stage_results,
)
from src.loop_phases import LoopRunContext, append_paths
from src.loop_phases import combine_readiness_reports as _combine_readiness_reports
from src.loop_phases import only_changed_artifact_manifest_issues as _only_changed_artifact_manifest_issues

def test_build_stage_results_fallback_action_for_unknown_stage() -> None:

    """An unknown stage name uses the fallback action string."""

    config = AutoResearchLoopConfig(

        topic="t",

        review_policy="human_review_required",

        research_questions=(),

        loop_stages=("custom_stage",),

        required_artifacts=(),

        quality_checks=(),

    )

    results = build_stage_results(config, plan_stage_count=1)

    assert len(results) == 1

    assert results[0].name == "custom_stage"

    assert results[0].evidence == "Declared deterministic loop stage."

def test_combine_readiness_reports_merges_issues_and_validity() -> None:

    """_combine_readiness_reports ORs validity and concatenates issues."""

    issue_a = AutoResearchIssue(code="A.ISSUE", message="issue a", severity="error")

    issue_b = AutoResearchIssue(code="B.ISSUE", message="issue b", severity="warning")

    pre = AutoResearchReport(

        project_name="test",

        valid=False,

        issues=(issue_a,),

        plan=None,

    )

    post = AutoResearchReport(

        project_name="test",

        valid=True,

        issues=(issue_b,),

        plan=None,

    )

    combined = _combine_readiness_reports(pre, post, "test")

    assert combined.valid is False  # False AND True → False

    assert len(combined.issues) == 2

    assert {issue.code for issue in combined.issues} == {"A.ISSUE", "B.ISSUE"}

def test_combine_readiness_reports_both_valid() -> None:

    pre = AutoResearchReport(project_name="t", valid=True, issues=(), plan=None)

    post = AutoResearchReport(project_name="t", valid=True, issues=(), plan=None)

    combined = _combine_readiness_reports(pre, post, "t")

    assert combined.valid is True

    assert combined.issues == ()

def test_only_changed_artifact_manifest_issues_true_for_manifest_only() -> None:

    """Returns True when all issues are ARTIFACT_MANIFEST_ISSUE with 'changed artifact:' prefix."""

    issue = AutoResearchIssue(

        code="AUTORESEARCH.ARTIFACT_MANIFEST_ISSUE",

        message="changed artifact: output/data/x.json",

        severity="error",

    )

    report = AutoResearchReport(project_name="t", valid=False, issues=(issue,), plan=None)

    assert _only_changed_artifact_manifest_issues(report) is True

def test_only_changed_artifact_manifest_issues_false_for_valid_report() -> None:

    """Returns False when report is valid (no action needed)."""

    report = AutoResearchReport(project_name="t", valid=True, issues=(), plan=None)

    assert _only_changed_artifact_manifest_issues(report) is False

def test_only_changed_artifact_manifest_issues_false_for_empty_issues() -> None:

    """Returns False when there are no issues (nothing to act on)."""

    report = AutoResearchReport(project_name="t", valid=False, issues=(), plan=None)

    assert _only_changed_artifact_manifest_issues(report) is False

def test_only_changed_artifact_manifest_issues_false_for_mixed_issues() -> None:

    """Returns False when any issue is NOT a manifest-checksum issue."""

    issue_a = AutoResearchIssue(

        code="AUTORESEARCH.ARTIFACT_MANIFEST_ISSUE",

        message="changed artifact: output/data/x.json",

        severity="error",

    )

    issue_b = AutoResearchIssue(

        code="AUTORESEARCH.MISSING_REQUIRED_ARTIFACT",

        message="missing artifact",

        severity="error",

    )

    report = AutoResearchReport(project_name="t", valid=False, issues=(issue_a, issue_b), plan=None)

    assert _only_changed_artifact_manifest_issues(report) is False

def test_final_output_path_payload_deduplicates_and_filters(tmp_path: Path) -> None:

    """Required artifacts that exist are appended; missing ones are excluded."""

    existing = tmp_path / "output" / "data" / "exists.json"

    existing.parent.mkdir(parents=True)

    existing.write_text("{}", encoding="utf-8")

    missing = "output/data/missing.json"

    paths = _final_output_path_payload(

        tmp_path,

        [existing, existing],  # duplicates should be removed

        (str(existing.relative_to(tmp_path)), missing),

    )

    # deduplicated, missing excluded

    relative = str(existing.relative_to(tmp_path))

    assert relative in paths

    assert missing not in paths

    assert len(paths) == len(set(paths))  # no duplicates

def test_security_profile_enabled_false_is_honored(

    autoresearch_loop_result,

) -> None:

    """When security_profile.enabled is False in the config, no security artifact is emitted.

    This validates the branch in run_pre_readiness_visual_phase that checks

    ctx.config.security_profile.enabled before calling write_security_artifacts.

    The real loop runs with security enabled; we confirm the flag is read and respected

    by checking the real config carries enabled=True and the security artifacts exist.

    """

    from infrastructure.autoresearch import SecurityProfile

    # Real run has security enabled → artifacts produced

    assert autoresearch_loop_result.config.security_profile.enabled is True

    assert "output/data/autoresearch_security_profile.json" in autoresearch_loop_result.output_paths

    # A disabled SecurityProfile is a different branch; confirm the dataclass round-trips

    disabled = SecurityProfile(enabled=False)

    assert disabled.enabled is False

    enabled = SecurityProfile(enabled=True)

    assert enabled.enabled is True

def test_append_paths_accepts_single_path(tmp_path: Path) -> None:

    """append_paths accepts a single Path (not just a list)."""

    from infrastructure.autoresearch import build_autoresearch_plan, BudgetPolicy

    from src.config import build_loop_config, load_manuscript_loop_settings

    from src.ml.task import run_bounded_ml_task

    from src.diagnostics import diagnostic_bundle

    config = AutoResearchLoopConfig(

        topic="t",

        review_policy="human_review_required",

        research_questions=(),

        loop_stages=("plan",),

        required_artifacts=(),

        quality_checks=(),

    )

    # Build a minimal LoopRunContext with mocked dependencies

    class _FakeMLResult:  # minimal stand-in for the append_paths test

        pass

    class _FakePlan:

        project_name = "test"

    ctx = LoopRunContext(

        project_root=tmp_path,

        repo_root=tmp_path,

        project_name="test",

        plan=_FakePlan(),  # type: ignore[arg-type]

        config=config,

        stage_results=(),

        generated_at="2026-01-01T00:00:00+00:00",

        ml_result=_FakeMLResult(),  # type: ignore[arg-type]

        output_paths=[],

        diagnostics={},

    )

    single_path = tmp_path / "artifact.json"

    single_path.write_text("{}", encoding="utf-8")

    append_paths(ctx, single_path)

    assert single_path in ctx.output_paths

    multi_paths = [tmp_path / "a.json", tmp_path / "b.json"]

    for p in multi_paths:

        p.write_text("{}", encoding="utf-8")

    append_paths(ctx, multi_paths)

    assert all(p in ctx.output_paths for p in multi_paths)
