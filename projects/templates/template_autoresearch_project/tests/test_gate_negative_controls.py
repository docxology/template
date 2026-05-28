"""Negative-control tests: prove each validation gate FAILS on bad input.

The audit showed every gate passed on the happy path but had never been shown
to fail. These tests inject the fault (empty/garbage evidence, empty figure
source, a missing core artifact, an unevaluated neural candidate, a drifted
artifact list) and assert the gate flips red — converting "we read the code"
into "we watched it fail". Each fault has a paired positive control proving the
healthy case still passes. No mocks: real temp files and real computations.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from src.artifact_content import is_substantive_artifact
from src.config import (
    AutoResearchLoopConfig,
    ResearchQuestion,
    build_loop_config,
    load_manuscript_loop_settings,
)
from src.figure_quality import figure_quality_report_payload
from src.loop import _final_output_path_payload, build_claims
from src.ml_selection import run_bounded_ml_task
from src.models import AutoResearchLoopResult
from src.writers import _BENCHMARK_CORE_ARTIFACTS, _grade_absent_benchmark
from infrastructure.autoresearch import BenchmarkTask, build_autoresearch_plan


# --------------------------------------------------------------------------- #
# is_substantive_artifact — the shared substance predicate                    #
# --------------------------------------------------------------------------- #


def test_is_substantive_rejects_missing(tmp_path: Path) -> None:
    assert is_substantive_artifact(tmp_path / "nope.json") is False


@pytest.mark.parametrize(
    "name,content",
    [
        ("empty.json", ""),
        ("empty_obj.json", "{}"),
        ("empty_arr.json", "[]"),
        ("garbage.json", "NOT VALID JSON {{{"),
        ("blank.md", "   \n\t  \n"),
        ("header_only.csv", "a,b,c\n"),
        # parseable-but-hollow: shallow predicates passed these; deep one must not
        ("null_value.json", '{"x": null}'),
        ("empty_string_value.json", '{"x": ""}'),
        ("list_of_null.json", "[null]"),
        ("list_of_empty.json", '["", null]'),
        ("bare_zero.json", "0"),
        ("bare_false.json", "false"),
        ("bare_null.json", "null"),
        # JSON-by-content: hollow object at a non-.json path must not slip the text branch
        ("hollow_obj.txt", "{}"),
        ("hollow_arr.md", "[]"),
        # nested-null / NaN: the predicate must recurse and reject non-finite floats
        ("nested_null.json", '{"a": {"b": null}}'),
        ("deep_nested_null.json", '{"a": {"b": {"c": null}}}'),
        ("list_of_null_dict.json", '[{"k": null}]'),
        ("nan_value.json", '{"x": NaN}'),
        ("inf_value.json", '{"x": Infinity}'),
    ],
)
def test_is_substantive_rejects_hollow(tmp_path: Path, name: str, content: str) -> None:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    assert is_substantive_artifact(path) is False


@pytest.mark.parametrize(
    "name,content",
    [
        ("real.json", '{"value": 1}'),
        ("zero_value.json", '{"count": 0}'),  # a real 0 is data, not hollow
        ("nested.json", '{"a": {"b": 1}}'),
        ("list_of_real_dict.json", '[{"k": 1}]'),
        ("list.json", "[1, 2, 3]"),
        ("notes.md", "# Real findings\n\nThis says something."),
        ("data.csv", "a,b\n1,2\n"),
    ],
)
def test_is_substantive_accepts_real(tmp_path: Path, name: str, content: str) -> None:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    assert is_substantive_artifact(path) is True


# --------------------------------------------------------------------------- #
# Claim support — must require substantive evidence, not mere existence        #
# --------------------------------------------------------------------------- #


def _config_with_questions(project_root: Path, repo_root: Path) -> AutoResearchLoopConfig:
    plan = build_autoresearch_plan(repo_root, project_root.name)
    settings = load_manuscript_loop_settings(project_root)
    return build_loop_config(plan, settings)


def _single_question_config(base: AutoResearchLoopConfig, evidence: str) -> AutoResearchLoopConfig:
    question = ResearchQuestion(identifier="rqx", question="Does it hold?", expected_evidence=evidence)
    return dataclasses.replace(base, research_questions=(question,))


def test_claim_unsupported_when_evidence_empty(tmp_path: Path, project_root: Path, repo_root: Path) -> None:
    base = _config_with_questions(project_root, repo_root)
    (tmp_path / "evidence.json").write_text("", encoding="utf-8")  # 0-byte placeholder
    config = _single_question_config(base, "evidence.json")
    claims = build_claims(config, tmp_path)
    assert claims[0].supported is False


def test_claim_unsupported_when_evidence_garbage(tmp_path: Path, project_root: Path, repo_root: Path) -> None:
    base = _config_with_questions(project_root, repo_root)
    (tmp_path / "evidence.json").write_text("NOT EVIDENCE {{{", encoding="utf-8")
    config = _single_question_config(base, "evidence.json")
    claims = build_claims(config, tmp_path)
    assert claims[0].supported is False


def test_claim_supported_when_evidence_substantive(tmp_path: Path, project_root: Path, repo_root: Path) -> None:
    base = _config_with_questions(project_root, repo_root)
    (tmp_path / "evidence.json").write_text('{"result": 0.93}', encoding="utf-8")
    config = _single_question_config(base, "evidence.json")
    claims = build_claims(config, tmp_path)
    assert claims[0].supported is True


# --------------------------------------------------------------------------- #
# Figure quality — must require substantive SOURCE data, not just nonblank px  #
# --------------------------------------------------------------------------- #


def _png_with_content(path: Path) -> None:
    from matplotlib import pyplot as plt

    figure = plt.figure()
    plt.plot([0, 1, 2], [1, 3, 2])
    figure.savefig(path)
    plt.close(figure)


def _figure_registry(project_root: Path, source_rel: str) -> dict[str, dict[str, object]]:
    figures_dir = project_root / "output" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    _png_with_content(figures_dir / "probe.png")
    return {
        "fig:probe": {
            "filename": "probe.png",
            "metadata": {
                "source": source_rel,
                "alt_text": "A probe figure with a real line.",
                "claim_boundary": "local",
            },
        }
    }


def test_figure_invalid_when_source_empty(tmp_path: Path) -> None:
    (tmp_path / "output" / "data").mkdir(parents=True, exist_ok=True)
    (tmp_path / "output" / "data" / "src.json").write_text("{}", encoding="utf-8")  # hollow source
    registry = _figure_registry(tmp_path, "output/data/src.json")
    report = figure_quality_report_payload(tmp_path, registry, generated_at="t", require_all_registered=True)
    assert report["valid"] is False
    assert report["figures"][0]["nonblank"] is True  # the pixel gate still passes...
    assert report["figures"][0]["source_nontrivial"] is False  # ...but substance does not


def test_figure_valid_when_source_substantive(tmp_path: Path) -> None:
    (tmp_path / "output" / "data").mkdir(parents=True, exist_ok=True)
    (tmp_path / "output" / "data" / "src.json").write_text('{"series": [1, 2, 3]}', encoding="utf-8")
    registry = _figure_registry(tmp_path, "output/data/src.json")
    report = figure_quality_report_payload(tmp_path, registry, generated_at="t", require_all_registered=True)
    assert report["valid"] is True
    assert report["figures"][0]["source_nontrivial"] is True


# --------------------------------------------------------------------------- #
# Benchmark grading — must measure emitted evidence, not self-grade 1.0        #
# --------------------------------------------------------------------------- #


def _benchmark_task() -> BenchmarkTask:
    return BenchmarkTask(
        identifier="readiness-smoke",
        description="probe",
        grading_output="output/reports/benchmark_readiness_smoke.json",
    )


def _write_healthy_benchmark_evidence(project_root: Path) -> None:
    """Write core artifacts with REAL content: a supported claim + ML improvement."""
    for rel in _BENCHMARK_CORE_ARTIFACTS:
        path = project_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if rel.endswith("autoresearch_claims.json"):
            path.write_text(
                '[{"identifier": "rq1", "supported": true, "evidence_path": "output/data/ml_task_results.json"}]',
                encoding="utf-8",
            )
        elif rel.endswith("ml_task_results.json"):
            path.write_text('{"accuracy_delta": 0.05}', encoding="utf-8")
        elif path.suffix == ".csv":
            path.write_text("a,b\n1,2\n", encoding="utf-8")
        else:
            path.write_text('{"value": 1}', encoding="utf-8")


def test_benchmark_grade_perfect_when_all_evidence_real(tmp_path: Path) -> None:
    _write_healthy_benchmark_evidence(tmp_path)
    payload = _grade_absent_benchmark(tmp_path, _benchmark_task())
    assert payload["score"] == 1.0
    assert payload["status"] == "graded"


def test_benchmark_grade_drops_when_core_artifact_missing(tmp_path: Path) -> None:
    _write_healthy_benchmark_evidence(tmp_path)
    (tmp_path / _BENCHMARK_CORE_ARTIFACTS[0]).unlink()  # remove one core artifact
    payload = _grade_absent_benchmark(tmp_path, _benchmark_task())
    assert float(payload["score"]) < 1.0
    assert payload["status"] == "incomplete"


def test_benchmark_grade_drops_when_core_artifact_empty(tmp_path: Path) -> None:
    _write_healthy_benchmark_evidence(tmp_path)
    (tmp_path / _BENCHMARK_CORE_ARTIFACTS[0]).write_text("", encoding="utf-8")  # hollow it out
    payload = _grade_absent_benchmark(tmp_path, _benchmark_task())
    assert float(payload["score"]) < 1.0


def test_benchmark_grade_drops_when_all_claims_unsupported(tmp_path: Path) -> None:
    _write_healthy_benchmark_evidence(tmp_path)
    # A non-empty claims list whose every claim is unsupported must NOT grade as ready.
    (tmp_path / "output" / "data" / "autoresearch_claims.json").write_text(
        '[{"identifier": "rq1", "supported": false}]', encoding="utf-8"
    )
    payload = _grade_absent_benchmark(tmp_path, _benchmark_task())
    assert float(payload["score"]) < 1.0
    assert "at_least_one_supported_claim" in payload["failed_checks"]


def test_benchmark_grade_drops_when_ml_not_improved(tmp_path: Path) -> None:
    _write_healthy_benchmark_evidence(tmp_path)
    (tmp_path / "output" / "data" / "ml_task_results.json").write_text('{"accuracy_delta": 0.0}', encoding="utf-8")
    payload = _grade_absent_benchmark(tmp_path, _benchmark_task())
    assert float(payload["score"]) < 1.0
    assert "ml_accuracy_improved_over_baseline" in payload["failed_checks"]


def test_benchmark_grade_drops_when_supported_flag_lacks_real_evidence(tmp_path: Path) -> None:
    # A self-asserted supported:true whose evidence_path is missing must NOT count.
    _write_healthy_benchmark_evidence(tmp_path)
    (tmp_path / "output" / "data" / "autoresearch_claims.json").write_text(
        '[{"identifier": "rq1", "supported": true, "evidence_path": "output/data/does_not_exist.json"}]',
        encoding="utf-8",
    )
    payload = _grade_absent_benchmark(tmp_path, _benchmark_task())
    assert float(payload["score"]) < 1.0
    assert "at_least_one_supported_claim" in payload["failed_checks"]


def test_benchmark_grade_drops_when_ml_delta_is_epsilon(tmp_path: Path) -> None:
    # An epsilon improvement must not score the loop as a real result.
    _write_healthy_benchmark_evidence(tmp_path)
    (tmp_path / "output" / "data" / "ml_task_results.json").write_text('{"accuracy_delta": 0.0001}', encoding="utf-8")
    payload = _grade_absent_benchmark(tmp_path, _benchmark_task())
    assert float(payload["score"]) < 1.0
    assert "ml_accuracy_improved_over_baseline" in payload["failed_checks"]


def test_benchmark_grade_zero_when_nothing_emitted(tmp_path: Path) -> None:
    payload = _grade_absent_benchmark(tmp_path, _benchmark_task())
    assert payload["score"] == 0.0
    assert payload["status"] == "incomplete"


# --------------------------------------------------------------------------- #
# neural_score — must reward an EVALUATED neural candidate, not mere presence  #
# --------------------------------------------------------------------------- #


def test_neural_score_requires_evaluation_not_presence(project_root: Path, repo_root: Path) -> None:
    plan = build_autoresearch_plan(repo_root, project_root.name)
    result = run_bounded_ml_task(project_root, plan.config.budget_policy)
    # Positive control: the real run evaluated a transformer -> full benchmark score.
    assert result.transformer_evaluated is True
    assert result.benchmark_score == 1.0

    # Negative control: deferred-ize the transformer (no test accuracy). Mere
    # presence in the candidate set must no longer earn the neural point.
    deferred = tuple(
        dataclasses.replace(candidate, test_accuracy=None)
        if candidate.model_type == "tiny_patch_transformer"
        else candidate
        for candidate in result.candidates
    )
    degraded = dataclasses.replace(result, candidates=deferred)
    assert degraded.transformer_evaluated is False
    assert degraded.benchmark_score < 1.0


# --------------------------------------------------------------------------- #
# Output-path list — must equal the required_artifacts contract (no drift)     #
# --------------------------------------------------------------------------- #


def test_output_paths_omit_missing_required_artifact(tmp_path: Path) -> None:
    # Binding: a required artifact that was never written must NOT be claimed.
    (tmp_path / "output" / "data").mkdir(parents=True)
    (tmp_path / "output" / "data" / "present.json").write_text('{"v": 1}', encoding="utf-8")
    required = ("output/data/present.json", "output/data/never_written.json")
    payload = _final_output_path_payload(tmp_path, [], required)
    assert "output/data/present.json" in payload
    assert "output/data/never_written.json" not in payload


def test_output_paths_cover_contract_when_present(tmp_path: Path) -> None:
    (tmp_path / "output" / "data").mkdir(parents=True)
    for name in ("a.json", "b.json"):
        (tmp_path / "output" / "data" / name).write_text('{"v": 1}', encoding="utf-8")
    required = ("output/data/a.json", "output/data/b.json")
    payload = _final_output_path_payload(tmp_path, [], required)
    assert set(required) <= set(payload)


def test_real_run_output_paths_all_exist(project_root: Path, autoresearch_loop_result: AutoResearchLoopResult) -> None:
    # Binding against overclaim on the real pipeline: every self-reported path exists.
    missing = [path for path in autoresearch_loop_result.output_paths if not (project_root / path).exists()]
    assert missing == [], f"output_paths overclaim non-existent files: {missing[:10]}"


# --------------------------------------------------------------------------- #
# Benchmark-grade ownership — the auto-grade must not clobber a dedicated grade #
# --------------------------------------------------------------------------- #


def test_dedicated_ml_grade_not_clobbered_by_auto_grade(
    project_root: Path, autoresearch_loop_result: AutoResearchLoopResult
) -> None:
    import json

    ml = json.loads((project_root / "output" / "reports" / "ml_benchmark_score.json").read_text())
    readiness = json.loads((project_root / "output" / "reports" / "benchmark_readiness_smoke.json").read_text())
    # ml-loop-score is graded by the dedicated ML grader: it must NOT be the
    # readiness auto-grade (which carries "checks"/"failed_checks").
    assert "checks" not in ml and "failed_checks" not in ml
    assert "accepted_candidate_id" in json.dumps(ml)
    # readiness-smoke IS the auto-grade and must reflect measured readiness.
    assert "checks" in readiness and "failed_checks" in readiness
