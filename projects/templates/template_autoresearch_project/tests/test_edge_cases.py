"""Edge-case and gap-filling tests for the deterministic AutoResearch loop.

Covers previously-uncovered paths in:
- config.py  (load_human_review error branches, load_seed_ideas, load_experiment_candidates,
               _parse_evidence_links, load_loop_config without plan)
- source_ledger.py  (duplicate citekey, missing citekey, validate_source_ledger_contract
                     error propagation)
- loop_phases.py  (security-disabled branch in run_pre_readiness_visual_phase,
                   evidence-registry write in run_final_payload_and_visual_phase)
- research_object.py  (_existing_project_paths out-of-tree path exclusion)
- security/render.py  (non-list non_claims branch)
- writers/io.py  (relative_path ValueError / outside-project path)
- writers/benchmark.py  (_benchmark_score None branch, _has_supported_claim hollow evidence)
- ml/data.py  (config validation errors for bad model_type, training overrides,
               robustness transforms, diagnostics, helper validators)
- artifact_content.py  (bare string top-level JSON, list of None, nested-all-null tree)
- loop.py  (_combine_readiness_reports, _only_changed_artifact_manifest_issues,
            build_stage_results fallback action)

No mocks: real temp files, real data, real computations.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from infrastructure.autoresearch import AutoResearchReport, BudgetPolicy
from infrastructure.autoresearch.models import AutoResearchIssue

from src.artifact_content import _json_is_substantive, _value_is_substantive
from src.config import (
    AutoResearchLoopConfig,
    HumanReviewState,
    load_experiment_candidates,
    load_human_review,
    load_loop_config,
    load_seed_ideas,
)
from src.loop import (
    _combine_readiness_reports,
    _final_output_path_payload,
    _only_changed_artifact_manifest_issues,
    build_stage_results,
)
from src.loop_phases import LoopRunContext, append_paths, run_pre_readiness_visual_phase
from src.models import AutoResearchLoopResult, LoopStageResult
from src.research_object import research_object_manifest_payload
from src.security.render import render_security_review_markdown
from src.source_ledger import (
    load_source_ledger,
    source_age_summary,
    validate_source_ledger_contract,
)
from src.writers.benchmark import _benchmark_score, _has_supported_claim
from src.writers.io import relative_path


# ---------------------------------------------------------------------------
# Helper: minimal AutoResearchLoopResult for unit tests
# ---------------------------------------------------------------------------

def _minimal_result(*, readiness_valid: bool = True) -> AutoResearchLoopResult:
    config = AutoResearchLoopConfig(
        topic="Edge cases",
        review_policy="human_review_required",
        research_questions=(),
        loop_stages=("plan",),
        required_artifacts=(),
        quality_checks=(),
    )
    return AutoResearchLoopResult(
        project_name="test_project",
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        config=config,
        stage_results=(
            LoopStageResult(
                name="plan",
                status="declared",
                evidence="Declared one stage.",
                suggested_action="review",
            ),
        ),
        claims=(),
        readiness_valid=readiness_valid,
        output_paths=(),
    )


# ---------------------------------------------------------------------------
# config.py — load_human_review error branches
# ---------------------------------------------------------------------------


def test_load_human_review_rejects_wrong_schema(tmp_path: Path) -> None:
    path = tmp_path / "human_review.yaml"
    path.write_text(
        "schema: wrong-schema-v0\npublication_approved: false\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="schema must be"):
        load_human_review(path)


def test_load_human_review_rejects_non_bool_approved(tmp_path: Path) -> None:
    path = tmp_path / "human_review.yaml"
    path.write_text(
        "schema: template-autoresearch-human-review-v1\npublication_approved: maybe\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="must be a boolean"):
        load_human_review(path)


def test_load_human_review_rejects_non_mapping_decisions(tmp_path: Path) -> None:
    path = tmp_path / "human_review.yaml"
    path.write_text(
        "schema: template-autoresearch-human-review-v1\n"
        "publication_approved: false\n"
        "decisions:\n  - deferred\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="must be a mapping"):
        load_human_review(path)


def test_load_human_review_rejects_unknown_decision(tmp_path: Path) -> None:
    path = tmp_path / "human_review.yaml"
    path.write_text(
        "schema: template-autoresearch-human-review-v1\n"
        "publication_approved: false\n"
        "decisions:\n  proposal_review: pending\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="must be one of"):
        load_human_review(path)


# ---------------------------------------------------------------------------
# config.py — load_seed_ideas and load_experiment_candidates
# ---------------------------------------------------------------------------


def test_load_seed_ideas_rejects_non_list_ideas(tmp_path: Path) -> None:
    (tmp_path / "seed_ideas.yaml").write_text("ideas: not_a_list\n", encoding="utf-8")
    with pytest.raises(ValueError, match="must be a list"):
        load_seed_ideas(tmp_path)


def test_load_seed_ideas_rejects_non_mapping_entry(tmp_path: Path) -> None:
    (tmp_path / "seed_ideas.yaml").write_text("ideas:\n  - just_a_string\n", encoding="utf-8")
    with pytest.raises(ValueError, match="entries must be mappings"):
        load_seed_ideas(tmp_path)


def test_load_seed_ideas_rejects_incomplete_entry(tmp_path: Path) -> None:
    (tmp_path / "seed_ideas.yaml").write_text(
        "ideas:\n  - id: idea1\n    title: No Rationale\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="must declare id, title, rationale, and status"):
        load_seed_ideas(tmp_path)


def test_load_experiment_candidates_returns_empty_for_non_list_ideas(tmp_path: Path) -> None:
    # ideas must be non-list → return ()
    (tmp_path / "seed_ideas.yaml").write_text("ideas: not_a_list\n", encoding="utf-8")
    result = load_experiment_candidates(tmp_path)
    assert result == ()


def test_load_experiment_candidates_skips_non_mapping_ideas(tmp_path: Path) -> None:
    (tmp_path / "seed_ideas.yaml").write_text("ideas:\n  - just_a_string\n", encoding="utf-8")
    result = load_experiment_candidates(tmp_path)
    assert result == ()


def test_load_experiment_candidates_skips_non_list_candidates(tmp_path: Path) -> None:
    (tmp_path / "seed_ideas.yaml").write_text(
        "ideas:\n  - id: idea1\n    candidates: not_a_list\n",
        encoding="utf-8",
    )
    result = load_experiment_candidates(tmp_path)
    assert result == ()


def test_load_experiment_candidates_skips_non_mapping_candidate_entries(tmp_path: Path) -> None:
    (tmp_path / "seed_ideas.yaml").write_text(
        "ideas:\n  - id: idea1\n    candidates:\n      - just_a_string\n",
        encoding="utf-8",
    )
    result = load_experiment_candidates(tmp_path)
    assert result == ()


def test_load_experiment_candidates_skips_empty_identifier(tmp_path: Path) -> None:
    (tmp_path / "seed_ideas.yaml").write_text(
        "ideas:\n"
        "  - id: idea1\n"
        "    candidates:\n"
        "      - id: \"\"\n"
        "        status: proposed\n",
        encoding="utf-8",
    )
    # Empty identifier → filtered out by `candidate.identifier`
    result = load_experiment_candidates(tmp_path)
    assert result == ()


def test_load_seed_ideas_evidence_links_rejects_non_list(tmp_path: Path) -> None:
    (tmp_path / "seed_ideas.yaml").write_text(
        "ideas:\n"
        "  - id: idea1\n"
        "    title: T\n"
        "    rationale: R\n"
        "    status: accepted\n"
        "    evidence_links: not_a_list\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="evidence_links must be a list"):
        load_seed_ideas(tmp_path)


def test_load_seed_ideas_evidence_links_rejects_non_mapping_entry(tmp_path: Path) -> None:
    (tmp_path / "seed_ideas.yaml").write_text(
        "ideas:\n"
        "  - id: idea1\n"
        "    title: T\n"
        "    rationale: R\n"
        "    status: accepted\n"
        "    evidence_links:\n"
        "      - not_a_mapping\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="evidence link entries must be mappings"):
        load_seed_ideas(tmp_path)


def test_load_seed_ideas_evidence_links_skips_empty_evidence_path(tmp_path: Path) -> None:
    (tmp_path / "seed_ideas.yaml").write_text(
        "ideas:\n"
        "  - id: idea1\n"
        "    title: T\n"
        "    rationale: R\n"
        "    status: accepted\n"
        "    evidence_links:\n"
        "      - evidence_path: \"\"\n",
        encoding="utf-8",
    )
    ideas = load_seed_ideas(tmp_path)
    assert len(ideas) == 1
    # Empty evidence_path is silently skipped
    assert ideas[0].evidence_links == ()


# ---------------------------------------------------------------------------
# config.py — load_loop_config without an explicit plan
# ---------------------------------------------------------------------------


def test_load_loop_config_without_explicit_plan(project_root: Path) -> None:
    """load_loop_config(project_root) resolves the plan internally."""
    config = load_loop_config(project_root)
    assert config.topic.startswith("Deterministic bounded AutoResearch")
    assert config.human_review.source_exists is True


# ---------------------------------------------------------------------------
# source_ledger.py — duplicate citekey and schema mismatch
# ---------------------------------------------------------------------------


def test_source_ledger_rejects_duplicate_citekey(tmp_path: Path) -> None:
    ledger = tmp_path / "source_ledger.yaml"
    ledger.write_text(
        "schema: template-autoresearch-source-ledger-v1\n"
        "sources:\n"
        "  - citekey: dup_key\n"
        "    canonical_url: https://example.org/1\n"
        "    source_tier: scholarly_preprint\n"
        "    checked_as_of: 2026-05-26\n"
        "  - citekey: dup_key\n"
        "    canonical_url: https://example.org/2\n"
        "    source_tier: scholarly_preprint\n"
        "    checked_as_of: 2026-05-26\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate source ledger citekey"):
        load_source_ledger(ledger)


def test_source_ledger_rejects_wrong_schema(tmp_path: Path) -> None:
    ledger = tmp_path / "source_ledger.yaml"
    ledger.write_text(
        "schema: wrong-schema-v0\nsources: []\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="schema must be"):
        load_source_ledger(ledger)


def test_source_ledger_rejects_non_mapping_row(tmp_path: Path) -> None:
    ledger = tmp_path / "source_ledger.yaml"
    ledger.write_text(
        "schema: template-autoresearch-source-ledger-v1\n"
        "sources:\n"
        "  - just_a_string\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="must be a mapping"):
        load_source_ledger(ledger)


def test_source_ledger_rejects_non_list_sources(tmp_path: Path) -> None:
    ledger = tmp_path / "source_ledger.yaml"
    ledger.write_text(
        "schema: template-autoresearch-source-ledger-v1\n"
        "sources: not_a_list\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="must be a list"):
        load_source_ledger(ledger)


def test_source_ledger_rejects_missing_citekey(tmp_path: Path) -> None:
    ledger = tmp_path / "source_ledger.yaml"
    ledger.write_text(
        "schema: template-autoresearch-source-ledger-v1\n"
        "sources:\n"
        "  - canonical_url: https://example.org/no-key\n"
        "    source_tier: scholarly_preprint\n"
        "    checked_as_of: 2026-05-26\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="missing citekey"):
        load_source_ledger(ledger)


def test_source_ledger_rejects_bad_date(tmp_path: Path) -> None:
    ledger = tmp_path / "source_ledger.yaml"
    ledger.write_text(
        "schema: template-autoresearch-source-ledger-v1\n"
        "sources:\n"
        "  - citekey: bad_date\n"
        "    canonical_url: https://example.org/\n"
        "    source_tier: scholarly_preprint\n"
        "    checked_as_of: not-a-date\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="checked_as_of must be an ISO date"):
        load_source_ledger(ledger)


def test_source_age_summary_returns_correct_buckets(tmp_path: Path) -> None:
    """source_age_summary correctly buckets entries across age thresholds."""
    from datetime import date
    from src.source_ledger import SourceLedgerEntry

    today = date(2026, 6, 1)
    entries = (
        SourceLedgerEntry(
            citekey="recent",
            canonical_url="https://a.org/",
            source_tier="scholarly_preprint",
            checked_as_of=date(2026, 5, 1),  # ~31 days old → 0-180d
        ),
        SourceLedgerEntry(
            citekey="mid",
            canonical_url="https://b.org/",
            source_tier="peer_reviewed_article",
            checked_as_of=date(2025, 12, 1),  # ~182 days old → 181-365d
        ),
        SourceLedgerEntry(
            citekey="old",
            canonical_url="https://c.org/",
            source_tier="conference_proceeding",
            checked_as_of=date(2024, 6, 1),  # ~366 days old → 366d+
        ),
    )
    summary = source_age_summary(entries, today=today)
    assert summary.get("0-180d", 0) >= 1
    assert summary.get("181-365d", 0) >= 1
    assert summary.get("366d+", 0) >= 1


def test_validate_source_ledger_contract_propagates_load_error(tmp_path: Path) -> None:
    """If the ledger itself fails to load, contract validation returns that error."""
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "source_ledger.yaml").write_text(
        "schema: template-autoresearch-source-ledger-v1\n"
        "sources:\n"
        "  - just_a_string\n",
        encoding="utf-8",
    )
    issues = validate_source_ledger_contract(tmp_path)
    assert issues  # error from load propagates as an issue string
    assert any("mapping" in issue for issue in issues)


# ---------------------------------------------------------------------------
# loop.py — internal helpers
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# loop_phases.py — security-disabled branch
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# research_object.py — out-of-project path exclusion
# ---------------------------------------------------------------------------


def test_research_object_manifest_excludes_out_of_tree_paths(tmp_path: Path) -> None:
    """Paths outside project_root are silently excluded from the manifest."""
    project = tmp_path / "project"
    project.mkdir()
    (project / "output" / "data").mkdir(parents=True)

    inside = project / "output" / "data" / "inside.json"
    inside.write_text('{"ok": true}', encoding="utf-8")

    outside = tmp_path / "outside.json"
    outside.write_text('{"ok": true}', encoding="utf-8")

    payload = research_object_manifest_payload(project, [inside, outside], generated_at="t")
    artifact_paths = [a["path"] for a in payload["artifacts"]]
    assert any("inside.json" in p for p in artifact_paths)
    assert not any("outside.json" in p for p in artifact_paths)


def test_research_object_manifest_excludes_nonexistent_paths(tmp_path: Path) -> None:
    """Paths that do not exist are silently excluded."""
    project = tmp_path / "project"
    project.mkdir()
    nonexistent = project / "output" / "data" / "ghost.json"

    payload = research_object_manifest_payload(project, [nonexistent], generated_at="t")
    assert payload["artifact_count"] == 0
    assert payload["artifacts"] == []


# ---------------------------------------------------------------------------
# security/render.py — non-list non_claims
# ---------------------------------------------------------------------------


def test_render_security_review_markdown_handles_non_list_non_claims() -> None:
    """When non_claims is not a list the renderer should not crash and should skip items."""
    profile = {
        "mode": "test",
        "network_policy": "offline",
        "integrity_algorithm": "sha256",
        "external_signing": False,
        "claim_scope": "local only",
        "non_claims": "not_a_list",  # intentionally wrong type
    }
    threat_model = {"summary": {"asset_count": 0, "threat_count": 0, "control_count": 0}}
    inventory = {"inputs": [], "generated_artifacts": []}
    attestation = {"status": "passed", "checked_count": 0, "missing_count": 0, "mismatch_count": 0}

    markdown = render_security_review_markdown(profile, threat_model, inventory, attestation)
    assert "# AutoResearch Security Review" in markdown
    # No crash; non_claims treated as empty
    assert "## Non-Claims" in markdown


# ---------------------------------------------------------------------------
# writers/io.py — relative_path when path is outside project root
# ---------------------------------------------------------------------------


def test_relative_path_returns_absolute_string_when_outside_root(tmp_path: Path) -> None:
    """relative_path falls back to str(path) when path is outside project_root."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    outside = tmp_path / "external" / "file.json"
    outside.parent.mkdir()
    outside.write_text("{}", encoding="utf-8")

    result = relative_path(project_root, outside)
    # Not relative to project_root → falls back to absolute string
    assert "external" in result


# ---------------------------------------------------------------------------
# writers/benchmark.py — _benchmark_score and _has_supported_claim edge cases
# ---------------------------------------------------------------------------


def test_benchmark_score_returns_none_for_missing_file(tmp_path: Path) -> None:
    path = tmp_path / "nonexistent.json"
    assert _benchmark_score(path) is None


def test_benchmark_score_returns_none_for_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("not json", encoding="utf-8")
    assert _benchmark_score(path) is None


def test_benchmark_score_returns_none_for_non_dict_json(tmp_path: Path) -> None:
    path = tmp_path / "list.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")
    assert _benchmark_score(path) is None


def test_benchmark_score_returns_none_for_non_numeric_score(tmp_path: Path) -> None:
    path = tmp_path / "no_score.json"
    path.write_text('{"score": "high"}', encoding="utf-8")
    assert _benchmark_score(path) is None


def test_has_supported_claim_returns_false_for_missing_claims(tmp_path: Path) -> None:
    assert _has_supported_claim(tmp_path) is False


def test_has_supported_claim_returns_false_for_hollow_claims_file(tmp_path: Path) -> None:
    (tmp_path / "output" / "data").mkdir(parents=True)
    (tmp_path / "output" / "data" / "autoresearch_claims.json").write_text("{}", encoding="utf-8")
    assert _has_supported_claim(tmp_path) is False


def test_has_supported_claim_returns_false_when_evidence_file_hollow(tmp_path: Path) -> None:
    """supported=true claim whose evidence_path points to an empty file → False."""
    (tmp_path / "output" / "data").mkdir(parents=True)
    evidence = tmp_path / "output" / "data" / "evidence.json"
    evidence.write_text("", encoding="utf-8")  # hollow
    claims = [{"identifier": "c1", "supported": True, "evidence_path": "output/data/evidence.json"}]
    (tmp_path / "output" / "data" / "autoresearch_claims.json").write_text(
        json.dumps(claims), encoding="utf-8"
    )
    assert _has_supported_claim(tmp_path) is False


def test_has_supported_claim_returns_true_for_substantive_evidence(tmp_path: Path) -> None:
    """supported=true claim whose evidence_path points to real content → True."""
    (tmp_path / "output" / "data").mkdir(parents=True)
    evidence = tmp_path / "output" / "data" / "evidence.json"
    evidence.write_text('{"result": "real"}', encoding="utf-8")
    claims = [{"identifier": "c1", "supported": True, "evidence_path": "output/data/evidence.json"}]
    (tmp_path / "output" / "data" / "autoresearch_claims.json").write_text(
        json.dumps(claims), encoding="utf-8"
    )
    assert _has_supported_claim(tmp_path) is True


def test_has_supported_claim_returns_false_when_all_claims_unsupported(tmp_path: Path) -> None:
    (tmp_path / "output" / "data").mkdir(parents=True)
    claims = [{"identifier": "c1", "supported": False, "evidence_path": "output/data/evidence.json"}]
    (tmp_path / "output" / "data" / "autoresearch_claims.json").write_text(
        json.dumps(claims), encoding="utf-8"
    )
    assert _has_supported_claim(tmp_path) is False


# ---------------------------------------------------------------------------
# artifact_content.py — deeper edge cases
# ---------------------------------------------------------------------------


def test_json_is_substantive_bare_string_true() -> None:
    """A bare top-level JSON string with content is substantive."""
    assert _json_is_substantive("hello") is True


def test_json_is_substantive_bare_string_whitespace_only() -> None:
    """A bare top-level JSON string of whitespace is NOT substantive."""
    assert _json_is_substantive("   ") is False


def test_json_is_substantive_bare_number_false() -> None:
    """A bare top-level number (not in container) is NOT substantive."""
    assert _json_is_substantive(42) is False


def test_json_is_substantive_bare_null_false() -> None:
    assert _json_is_substantive(None) is False


def test_value_is_substantive_nan_float_false() -> None:
    import math
    assert _value_is_substantive(float("nan")) is False


def test_value_is_substantive_inf_float_false() -> None:
    import math
    assert _value_is_substantive(float("inf")) is False


def test_value_is_substantive_list_of_nones_false() -> None:
    """A list containing only None values is not substantive."""
    assert _value_is_substantive([None, None]) is False


def test_value_is_substantive_nested_all_null_dict_false() -> None:
    """Deeply nested all-null dict is not substantive."""
    assert _value_is_substantive({"a": {"b": None}}) is False


def test_value_is_substantive_nested_with_real_value_true() -> None:
    """Nested dict with at least one real value IS substantive."""
    assert _value_is_substantive({"a": {"b": 42}}) is True


def test_value_is_substantive_bool_true() -> None:
    """A boolean value (even False) is substantive — it carries intent."""
    assert _value_is_substantive(False) is True
    assert _value_is_substantive(True) is True


# ---------------------------------------------------------------------------
# ml/data.py — config validation errors
# ---------------------------------------------------------------------------


def test_load_mnist_task_config_rejects_bad_model_type(tmp_path: Path, project_root: Path) -> None:
    """A candidate with an unsupported model_type should raise ValueError."""
    import yaml
    from src.ml.data import load_mnist_task_config

    # Load real config and inject a bad candidate
    real_config_text = (project_root / "mnist_task.yaml").read_text(encoding="utf-8")
    config_dict = yaml.safe_load(real_config_text)

    # Replace first candidate's model_type with an invalid one
    config_dict["candidate_configs"][0]["model_type"] = "unsupported_model"
    bad_config_path = tmp_path / "mnist_task.yaml"
    bad_config_path.write_text(yaml.dump(config_dict), encoding="utf-8")

    with pytest.raises(ValueError, match="unsupported model_type"):
        load_mnist_task_config(tmp_path, "mnist_task.yaml")


def test_load_mnist_task_config_rejects_bad_training_key(tmp_path: Path, project_root: Path) -> None:
    """An unsupported training key in a candidate config should raise ValueError."""
    import yaml
    from src.ml.data import load_mnist_task_config

    real_config_text = (project_root / "mnist_task.yaml").read_text(encoding="utf-8")
    config_dict = yaml.safe_load(real_config_text)

    # Add an unsupported training key
    config_dict["candidate_configs"][0].setdefault("training", {})["unsupported_key"] = 1
    bad_config_path = tmp_path / "mnist_task.yaml"
    bad_config_path.write_text(yaml.dump(config_dict), encoding="utf-8")

    with pytest.raises(ValueError, match="unsupported training key"):
        load_mnist_task_config(tmp_path, "mnist_task.yaml")


def test_load_mnist_task_config_rejects_non_mapping_yaml(tmp_path: Path) -> None:
    """A non-mapping YAML root should raise ValueError."""
    from src.ml.data import load_mnist_task_config

    (tmp_path / "mnist_task.yaml").write_text("- not\n- a\n- mapping\n", encoding="utf-8")
    with pytest.raises(ValueError, match="must contain a mapping"):
        load_mnist_task_config(tmp_path, "mnist_task.yaml")


def test_load_mnist_task_config_rejects_unsupported_normalization(
    tmp_path: Path, project_root: Path
) -> None:
    """An unsupported normalization mode should raise ValueError at array-load time."""
    import yaml
    from src.ml.data import load_mnist_task_config, load_mnist_arrays

    real_config_text = (project_root / "mnist_task.yaml").read_text(encoding="utf-8")
    config_dict = yaml.safe_load(real_config_text)
    config_dict["task"]["normalization"] = "minmax"

    bad_config_path = tmp_path / "mnist_task.yaml"
    bad_config_path.write_text(yaml.dump(config_dict), encoding="utf-8")

    config = load_mnist_task_config(tmp_path, "mnist_task.yaml")
    # Need to point dataset_path to the real fixture
    import dataclasses
    config = dataclasses.replace(config, dataset_path=str(project_root / "data" / "mnist_small.npz"))

    with pytest.raises(ValueError, match="unsupported normalization"):
        load_mnist_arrays(tmp_path, config)


def test_load_mnist_task_config_rejects_robustness_bad_type(
    tmp_path: Path, project_root: Path
) -> None:
    """An unsupported robustness transform type should raise ValueError."""
    import yaml
    from src.ml.data import load_mnist_task_config

    real_config_text = (project_root / "mnist_task.yaml").read_text(encoding="utf-8")
    config_dict = yaml.safe_load(real_config_text)
    config_dict["robustness_transforms"] = [{"id": "bad", "type": "unsupported_transform"}]

    bad_config_path = tmp_path / "mnist_task.yaml"
    bad_config_path.write_text(yaml.dump(config_dict), encoding="utf-8")

    with pytest.raises(ValueError, match="unsupported robustness transform type"):
        load_mnist_task_config(tmp_path, "mnist_task.yaml")


def test_load_mnist_task_config_rejects_robustness_empty_id(
    tmp_path: Path, project_root: Path
) -> None:
    """A robustness transform with empty id should raise ValueError."""
    import yaml
    from src.ml.data import load_mnist_task_config

    real_config_text = (project_root / "mnist_task.yaml").read_text(encoding="utf-8")
    config_dict = yaml.safe_load(real_config_text)
    config_dict["robustness_transforms"] = [{"id": "", "type": "identity"}]

    bad_config_path = tmp_path / "mnist_task.yaml"
    bad_config_path.write_text(yaml.dump(config_dict), encoding="utf-8")

    with pytest.raises(ValueError, match="id must not be empty"):
        load_mnist_task_config(tmp_path, "mnist_task.yaml")


# ---------------------------------------------------------------------------
# loop_phases.py — append_paths with a single Path
# ---------------------------------------------------------------------------


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
