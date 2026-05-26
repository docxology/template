"""Generated-artifact schema manifest helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_MANIFEST_SCHEMA = "template-autoresearch-schema-manifest-v1"

GENERIC_JSON_EXEMPTIONS: dict[str, str] = {
    "output/data/autoresearch_claims.json": "list of generated claim rows",
    "output/data/autoresearch_loop.json": "project loop payload serialized from the public result model",
    "output/data/autoresearch_plan.json": "infrastructure AutoResearch plan payload",
    "output/data/autoresearch_stage_matrix.csv": "CSV table, not JSON",
    "output/data/benchmark_scores.json": "benchmark task table",
    "output/data/idea_ledger.json": "idea and candidate table",
    "output/data/manuscript_figure_blocks.json": "token-to-Markdown figure block table",
    "output/data/manuscript_variables.json": "token-to-value table",
    "output/data/ml_candidate_ledger.json": "candidate ledger table",
    "output/data/ml_confusion_matrix.csv": "CSV table, not JSON",
    "output/data/ml_error_examples.json": "error-example row table",
    "output/data/ml_task_results.json": "ML task result payload serialized from the public result model",
    "output/data/ml_training_history.csv": "CSV table, not JSON",
    "output/data/mnist_task_config.json": "task configuration snapshot",
    "output/data/research_program.json": "human-authored program snapshot",
    "output/data/run_ledger.json": "run budget ledger table",
    "output/figures/figure_registry.json": "figure-label keyed registry",
    "output/reports/autoresearch_loop.json": "project loop payload serialized from the public result model",
    "output/reports/autoresearch_readiness.json": "infrastructure readiness report payload",
    "output/reports/artifact_manifest.json": "pipeline artifact manifest table",
    "output/reports/benchmark_readiness_smoke.json": "benchmark grading row",
    "output/reports/evidence_registry.json": "evidence fact registry table",
    "output/reports/ml_benchmark_score.json": "benchmark grading row",
}


def schema_manifest_payload(
    project_root: Path,
    paths: list[Path],
    *,
    generated_at: str,
) -> dict[str, object]:
    """Return a manifest of schema-versioned JSON artifacts and documented exemptions."""
    schema_rows: list[dict[str, str]] = []
    exemption_rows: list[dict[str, str]] = []
    missing_schema_rows: list[dict[str, str]] = []
    for path in _candidate_artifact_paths(project_root, paths):
        rel_path = _relative_path(project_root, path)
        if path.suffix != ".json":
            if rel_path in GENERIC_JSON_EXEMPTIONS:
                exemption_rows.append({"path": rel_path, "reason": GENERIC_JSON_EXEMPTIONS[rel_path]})
            continue
        payload = _load_json(path)
        schema = payload.get("schema") if isinstance(payload, dict) else None
        if isinstance(schema, str) and schema:
            schema_rows.append({"path": rel_path, "schema": schema})
        elif rel_path in GENERIC_JSON_EXEMPTIONS:
            exemption_rows.append({"path": rel_path, "reason": GENERIC_JSON_EXEMPTIONS[rel_path]})
        else:
            missing_schema_rows.append({"path": rel_path, "reason": "JSON artifact lacks top-level schema"})
    schema_rows.append(
        {
            "path": "output/data/autoresearch_schema_manifest.json",
            "schema": SCHEMA_MANIFEST_SCHEMA,
        }
    )
    return {
        "schema": SCHEMA_MANIFEST_SCHEMA,
        "generated_at": generated_at,
        "schema_artifacts": _dedupe_rows(schema_rows, key="path"),
        "generic_table_exemptions": _dedupe_rows(exemption_rows, key="path"),
        "missing_schema_artifacts": _dedupe_rows(missing_schema_rows, key="path"),
        "claim_boundary": "Schemas version generated governance payload shapes; exemptions are generic tables.",
    }


def _candidate_artifact_paths(project_root: Path, paths: list[Path]) -> tuple[Path, ...]:
    candidates = {path.resolve() for path in paths if path.exists()}
    return tuple(sorted(candidates))


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _relative_path(project_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _dedupe_rows(rows: list[dict[str, str]], *, key: str) -> list[dict[str, str]]:
    deduped: dict[str, dict[str, str]] = {}
    for row in rows:
        deduped[row[key]] = row
    return [deduped[path] for path in sorted(deduped)]
