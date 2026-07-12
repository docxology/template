"""Small benchmark harness for canonical template exemplars."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

from infrastructure.benchmark.rubrics import RubricSet
from infrastructure.core.pipeline.artifacts import validate_artifact_manifest
from infrastructure.project.domain_profile import load_domain_profile
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.validation.evidence_registry import (
    build_project_evidence_registry,
    validate_text_against_registry,
)
from infrastructure.validation.output.artifacts import read_artifact_manifest

_CANONICAL_PROJECTS = PUBLIC_PROJECT_NAMES
_DEFAULT_CHECKS = (
    "output_validity",
    "evidence_grounding",
    "reproducibility_bundle",
    "artifact_manifest",
    "render_success",
    "publication_readiness",
)
_SUPPORTED_CHECKS = frozenset(
    {
        *_DEFAULT_CHECKS,
        "cross_reference_integrity",
        "source_quality",
    }
)
_ISSUE_DETAIL_LIMIT = 25


@dataclass(frozen=True)
class BenchmarkManifest:
    """Declarative benchmark manifest."""

    name: str
    projects: tuple[str, ...]
    required_outputs: tuple[str, ...] = ()
    checks: tuple[str, ...] = ()
    rubric: RubricSet | None = None


@dataclass(frozen=True)
class BenchmarkScore:
    """Score for one project against a manifest."""

    project: str
    passed: bool
    score: float
    max_score: float
    issues: tuple[str, ...] = field(default_factory=tuple)
    check_results: tuple[BenchmarkCheckResult, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class BenchmarkCheckResult:
    """Result and weight for one named benchmark dimension."""

    name: str
    passed: bool
    weight: float
    issues: tuple[str, ...] = field(default_factory=tuple)


def load_benchmark_manifest(path: Path) -> BenchmarkManifest:
    """Load a benchmark manifest from JSON."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Benchmark manifest must be a JSON object: {path}")
    manifest = BenchmarkManifest(
        name=str(payload["name"]),
        projects=_tuple_of_strings(payload.get("projects", ())),
        required_outputs=_tuple_of_strings(payload.get("required_outputs", ())),
        checks=_tuple_of_strings(payload.get("checks", ())),
        rubric=RubricSet.from_dict(payload["rubric"]) if isinstance(payload.get("rubric"), dict) else None,
    )
    _validate_manifest(manifest)
    return manifest


def write_default_manifest(*, repo_root: Path, output_path: Path) -> BenchmarkManifest:
    """Write a fail-closed default manifest for every canonical public exemplar."""
    projects = _CANONICAL_PROJECTS
    checks = _DEFAULT_CHECKS
    rubric_payload = _profile_rubric_payload(repo_root, projects, checks) or _default_rubric_payload()
    manifest = BenchmarkManifest(
        name="template-smoke",
        projects=projects,
        required_outputs=("output/pdf", "output/reports/validation_report.json"),
        checks=checks,
        rubric=RubricSet.from_dict(rubric_payload),
    )
    _validate_manifest(manifest)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(_manifest_to_dict(manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def score_project_against_manifest(
    project_root: Path,
    manifest: BenchmarkManifest,
) -> BenchmarkScore:
    """Score one project against fixed benchmark checks."""
    issues: list[str] = []
    score = 0.0
    weights = _check_weights(manifest)
    max_score = sum(weights.values())
    if not project_root.is_dir():
        missing_issue = f"missing project directory: {_display_project_path(project_root)}"
        return BenchmarkScore(
            project=project_root.name,
            passed=False,
            score=score,
            max_score=max_score,
            issues=(missing_issue,),
            check_results=tuple(
                BenchmarkCheckResult(name=check, passed=False, weight=weights[check], issues=(missing_issue,))
                for check in manifest.checks
            ),
        )
    checkers = {
        "output_validity": lambda: [
            *_check_required_outputs(project_root, manifest.required_outputs),
            *_check_validation_report(project_root),
        ],
        "evidence_grounding": lambda: _check_evidence_grounding(project_root),
        "reproducibility_bundle": lambda: _check_reproducibility_bundle(project_root),
        "artifact_manifest": lambda: _check_artifact_manifest(project_root),
        "render_success": lambda: _check_render_success(project_root),
        "cross_reference_integrity": lambda: _check_cross_reference_integrity(project_root),
        "source_quality": lambda: _check_source_quality(project_root),
        "publication_readiness": lambda: _check_publication_readiness(project_root),
    }

    check_results: list[BenchmarkCheckResult] = []
    for check in manifest.checks:
        checker = checkers.get(check)
        if checker is None:  # Defensive: manifest validation rejects this earlier.
            check_issues = [f"unknown benchmark check: {check}"]
        else:
            check_issues = checker()
        if check_issues:
            issues.extend(check_issues)
        else:
            score += weights[check]
        check_results.append(
            BenchmarkCheckResult(
                name=check,
                passed=not check_issues,
                weight=weights[check],
                issues=tuple(check_issues),
            )
        )

    deduplicated_issues = tuple(dict.fromkeys(issues))

    return BenchmarkScore(
        project=project_root.name,
        passed=all(result.passed for result in check_results),
        score=score,
        max_score=max_score,
        issues=deduplicated_issues,
        check_results=tuple(check_results),
    )


def run_benchmark_manifest(repo_root: Path, manifest: BenchmarkManifest) -> tuple[BenchmarkScore, ...]:
    """Run a manifest against all listed projects under ``repo_root/projects``."""
    return tuple(
        score_project_against_manifest(repo_root / "projects" / project_name, manifest)
        for project_name in manifest.projects
    )


def scores_to_dict(scores: tuple[BenchmarkScore, ...]) -> dict[str, Any]:
    """Convert benchmark scores into a JSON-safe payload."""
    return {
        "passed": all(score.passed for score in scores),
        "projects": [
            {
                "project": score.project,
                "passed": score.passed,
                "score": score.score,
                "max_score": score.max_score,
                "issues": list(score.issues),
                "checks": {
                    result.name: {
                        "passed": result.passed,
                        "score": result.weight if result.passed else 0.0,
                        "max_score": result.weight,
                        "issues": list(result.issues),
                    }
                    for result in score.check_results
                },
            }
            for score in scores
        ],
    }


def scores_to_markdown(scores: list[BenchmarkScore] | tuple[BenchmarkScore, ...]) -> str:
    """Render benchmark scores as a small Markdown table."""
    lines = [
        "| Project | Passed | Score | Failed checks | Issues |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for score in scores:
        issues = _markdown_cell("; ".join(score.issues)) if score.issues else ""
        failed_checks = ", ".join(result.name for result in score.check_results if not result.passed)
        lines.append(
            f"| {score.project} | {'yes' if score.passed else 'no'} | "
            f"{_format_score(score.score)}/{_format_score(score.max_score)} | {failed_checks} | {issues} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for the template benchmark harness."""
    parser = argparse.ArgumentParser(description="Run template benchmark manifests")
    parser.add_argument(
        "manifest",
        nargs="?",
        default=str(Path(__file__).with_name("template_smoke_manifest.json")),
        help="Benchmark manifest JSON path",
    )
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--output-json", help="Write score payload to a JSON file")
    parser.add_argument("--output-markdown", help="Write score payload to a Markdown file")
    parser.add_argument(
        "--write-default-manifest",
        nargs="?",
        const="infrastructure/benchmark/template_smoke_manifest.json",
        help="Write a profile-aware default manifest and exit",
    )
    args = parser.parse_args(argv)

    if args.write_default_manifest:
        manifest = write_default_manifest(repo_root=Path(args.repo_root), output_path=Path(args.write_default_manifest))
        print(json.dumps(_manifest_to_dict(manifest), indent=2, sort_keys=True))
        return 0

    manifest = load_benchmark_manifest(Path(args.manifest))
    scores = run_benchmark_manifest(Path(args.repo_root), manifest)
    payload = scores_to_dict(scores)
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.output_json:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    if args.output_markdown:
        markdown_path = Path(args.output_markdown)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(scores_to_markdown(scores), encoding="utf-8")
    return 0 if payload["passed"] else 1


def _check_required_outputs(project_root: Path, required_outputs: tuple[str, ...]) -> list[str]:
    issues: list[str] = []
    for required in required_outputs:
        if not (project_root / required).exists():
            issues.append(f"missing required output: {required}")
    return issues


def _check_validation_report(project_root: Path) -> list[str]:
    report_path = project_root / "output" / "reports" / "validation_report.json"
    if not report_path.exists():
        return ["missing validation report: output/reports/validation_report.json"]
    try:
        payload: Any = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return [f"invalid validation report JSON: {_relative(project_root, report_path)}"]
    if not isinstance(payload, dict):
        return ["validation report must be a JSON object"]
    status = str(payload.get("overall_status", "")).lower()
    if status and status not in {"pass", "passed", "ok", "success"}:
        return [f"validation report did not pass: {status}"]
    summary = payload.get("summary", {})
    if isinstance(summary, dict) and summary.get("all_passed") is False:
        return ["validation summary did not pass all checks"]
    return []


def _read_validation_report(project_root: Path) -> dict[str, Any]:
    report_path = project_root / "output" / "reports" / "validation_report.json"
    if not report_path.exists():
        return {}
    try:
        payload: Any = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _check_evidence_grounding(project_root: Path) -> list[str]:
    registry = build_project_evidence_registry(project_root)
    text = "\n".join(_read_manuscript_markdown(project_root))
    if not text.strip():
        return ["no manuscript markdown found for evidence grounding"]
    report = validate_text_against_registry(text, registry)
    issues: list[str] = []
    numbers = [issue.value for issue in report.errors if issue.kind == "number"]
    citations = [issue.value for issue in report.errors if issue.kind == "citation"]
    if numbers:
        issues.append(f"unsupported numbers: {', '.join(numbers)}")
    if citations:
        issues.append(f"unsupported citations: {', '.join(citations)}")
    return issues


def _check_reproducibility_bundle(project_root: Path) -> list[str]:
    try:
        profile = load_domain_profile(project_root)
    except ValueError as exc:
        return [f"invalid domain profile: {exc}"]
    declared = [
        value
        for value in profile.artifact_expectations
        if "/" in value and ": " not in value and _is_safe_relative_path(value)
    ]
    if declared:
        missing = [value for value in declared if not (project_root / value).is_file()]
        return [f"missing declared reproducibility artifact: {value}" for value in missing]
    expected = project_root / "output" / "data" / "manuscript_variables.json"
    if expected.is_file():
        return []
    return ["missing reproducibility evidence: no declared artifacts or manuscript variables exist"]


def _check_artifact_manifest(project_root: Path) -> list[str]:
    manifest_path = project_root / "output" / "reports" / "artifact_manifest.json"
    if not manifest_path.exists():
        return ["missing artifact manifest: output/reports/artifact_manifest.json"]
    try:
        manifest = read_artifact_manifest(manifest_path)
    except (OSError, json.JSONDecodeError, ValueError):
        return ["invalid artifact manifest JSON: output/reports/artifact_manifest.json"]
    if not manifest.entries:
        return ["artifact manifest has no entries"]
    report = validate_artifact_manifest(manifest, project_dir=project_root)
    return _bounded_prefixed_issues("artifact manifest issue", report.issues)


def _check_render_success(project_root: Path) -> list[str]:
    pdf_dir = project_root / "output" / "pdf"
    pdf_files = list(pdf_dir.glob("*.pdf")) if pdf_dir.exists() else []
    if not pdf_files:
        return ["missing rendered PDF artifact"]
    if any(path.stat().st_size == 0 for path in pdf_files):
        return ["empty rendered PDF artifact"]
    report = _read_validation_report(project_root)
    checks = report.get("checks", {})
    if isinstance(checks, dict) and checks.get("PDF validation") is False:
        return ["PDF validation check failed"]
    return []


def _check_cross_reference_integrity(project_root: Path) -> list[str]:
    report = _read_validation_report(project_root)
    if not report:
        return []
    figure_issues = report.get("figure_issues", [])
    if isinstance(figure_issues, list) and figure_issues:
        return [f"figure reference issue: {issue}" for issue in figure_issues]
    summary = report.get("summary", {})
    if isinstance(summary, dict) and int(summary.get("figure_issues_count", 0) or 0) > 0:
        return ["figure reference issues reported"]
    return []


def _check_source_quality(project_root: Path) -> list[str]:
    report = _read_validation_report(project_root)
    stats = report.get("output_statistics", {}) if report else {}
    if isinstance(stats, dict):
        evidence_issues = stats.get("evidence_issues", [])
        if isinstance(evidence_issues, list):
            citation_issues = [str(issue) for issue in evidence_issues if "citation" in str(issue).lower()]
            if citation_issues:
                return citation_issues
    return []


def _check_publication_readiness(project_root: Path) -> list[str]:
    report = _read_validation_report(project_root)
    if not report:
        return ["missing validation report for publication readiness"]
    summary = report.get("summary", {})
    if isinstance(summary, dict) and summary.get("all_passed") is False:
        return ["validation summary did not pass all checks"]
    return []


def _profile_rubric_payload(
    repo_root: Path,
    projects: tuple[str, ...],
    checks: tuple[str, ...],
) -> dict[str, Any] | None:
    compatible: list[dict[str, Any]] = []
    for project in projects:
        try:
            profile = load_domain_profile(repo_root / "projects" / project)
        except ValueError:
            return None
        if not profile.benchmark_rubric:
            return None
        try:
            rubric = RubricSet.from_dict(profile.benchmark_rubric)
        except ValueError:
            return None
        if {dimension.name for dimension in rubric.dimensions} != set(checks):
            return None
        compatible.append(profile.benchmark_rubric)
    if not compatible:
        return None
    canonical = {json.dumps(payload, sort_keys=True) for payload in compatible}
    return compatible[0] if len(canonical) == 1 else None


def _default_rubric_payload() -> dict[str, Any]:
    return {
        "name": "template-publication-readiness",
        "dimensions": [
            {"name": "output_validity", "weight": 1.0},
            {"name": "evidence_grounding", "weight": 2.0},
            {"name": "reproducibility_bundle", "weight": 1.0},
            {"name": "artifact_manifest", "weight": 1.0},
            {"name": "render_success", "weight": 1.0},
            {"name": "publication_readiness", "weight": 1.0},
        ],
    }


def _manifest_to_dict(manifest: BenchmarkManifest) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "name": manifest.name,
        "projects": list(manifest.projects),
        "required_outputs": list(manifest.required_outputs),
        "checks": list(manifest.checks),
    }
    if manifest.rubric is not None:
        payload["rubric"] = {
            "name": manifest.rubric.name,
            "dimensions": [
                {"name": dimension.name, "weight": dimension.weight} for dimension in manifest.rubric.dimensions
            ],
        }
    return payload


def _read_manuscript_markdown(project_root: Path) -> list[str]:
    manuscript_dir = project_root / "manuscript"
    if not manuscript_dir.exists():
        return []
    texts: list[str] = []
    for markdown_path in sorted(manuscript_dir.rglob("*.md")):
        try:
            texts.append(markdown_path.read_text(encoding="utf-8"))
        except OSError:
            continue
    return texts


def _tuple_of_strings(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list | tuple):
        if not all(isinstance(item, str) for item in value):
            raise ValueError("Benchmark manifest sequence values must be strings")
        return tuple(value)
    raise ValueError("Benchmark manifest sequence values must be strings or lists of strings")


def _validate_manifest(manifest: BenchmarkManifest) -> None:
    if not manifest.name.strip():
        raise ValueError("benchmark manifest name must not be empty")
    if not manifest.projects:
        raise ValueError("benchmark manifest must list at least one project")
    if not manifest.checks:
        raise ValueError("benchmark manifest must list at least one check")
    if len(set(manifest.projects)) != len(manifest.projects):
        raise ValueError("benchmark manifest projects must be unique")
    if len(set(manifest.checks)) != len(manifest.checks):
        raise ValueError("benchmark manifest checks must be unique")
    unknown_checks = set(manifest.checks) - _SUPPORTED_CHECKS
    if unknown_checks:
        raise ValueError(f"unsupported benchmark checks: {', '.join(sorted(unknown_checks))}")
    _validate_relative_paths(manifest.projects, label="project")
    _validate_relative_paths(manifest.required_outputs, label="required output")
    if manifest.rubric is not None:
        dimensions = {dimension.name for dimension in manifest.rubric.dimensions}
        checks = set(manifest.checks)
        if dimensions != checks:
            missing = checks - dimensions
            extra = dimensions - checks
            details = []
            if missing:
                details.append(f"missing dimensions: {', '.join(sorted(missing))}")
            if extra:
                details.append(f"unknown dimensions: {', '.join(sorted(extra))}")
            raise ValueError(f"rubric dimensions must exactly match benchmark checks ({'; '.join(details)})")


def _check_weights(manifest: BenchmarkManifest) -> dict[str, float]:
    configured = (
        {dimension.name: dimension.weight for dimension in manifest.rubric.dimensions}
        if manifest.rubric is not None
        else {}
    )
    return {check: configured.get(check, 1.0) for check in manifest.checks}


def _display_project_path(project_root: Path) -> str:
    parts = project_root.parts
    if "projects" in parts:
        return Path(*parts[parts.index("projects") :]).as_posix()
    return project_root.as_posix()


def _format_score(value: float) -> str:
    return str(int(value)) if value.is_integer() else f"{value:g}"


def _markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _is_safe_relative_path(value: str) -> bool:
    normalized = value.replace("\\", "/")
    path = PurePosixPath(normalized)
    return bool(normalized.strip()) and not path.is_absolute() and ".." not in path.parts


def _validate_relative_paths(values: tuple[str, ...], *, label: str) -> None:
    unsafe = [value for value in values if not _is_safe_relative_path(value)]
    if unsafe:
        raise ValueError(f"benchmark {label} paths must be non-traversing relative paths: {', '.join(unsafe)}")


def _bounded_prefixed_issues(prefix: str, issues: tuple[str, ...], *, limit: int = _ISSUE_DETAIL_LIMIT) -> list[str]:
    rendered = [f"{prefix}: {issue}" for issue in issues[:limit]]
    omitted = len(issues) - len(rendered)
    if omitted:
        rendered.append(f"{prefix}: {omitted} additional issue(s) omitted")
    return rendered


def _relative(project_root: Path, path: Path) -> Path:
    try:
        return path.relative_to(project_root)
    except ValueError:
        return path


if __name__ == "__main__":
    raise SystemExit(main())
