"""Local research-object manifest helpers for generated AutoResearch runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from infrastructure.core.pipeline.artifacts import compute_sha256

RESEARCH_OBJECT_SCHEMA = "template-autoresearch-research-object-manifest-v1"


def research_object_manifest_payload(
    project_root: Path,
    paths: list[Path],
    *,
    generated_at: str,
) -> dict[str, object]:
    """Return a local research-object manifest without claiming an external standard."""
    review_decisions = _load_json_mapping(project_root / "output" / "data" / "review_decisions.json")
    artifacts = [_file_record(project_root, path) for path in _existing_project_paths(project_root, paths)]
    return {
        "schema": RESEARCH_OBJECT_SCHEMA,
        "generated_at": generated_at,
        "project_name": project_root.name,
        "artifact_count": len(artifacts),
        "empty_artifact_count": sum(1 for artifact in artifacts if artifact.get("empty")),
        "artifacts": artifacts,
        "manuscript_outputs": [
            _expected_file_record(project_root, "output/pdf/template_autoresearch_project_combined.pdf"),
            _expected_file_record(project_root, "output/web/index.html"),
            _expected_file_record(project_root, "output/manuscript/00_abstract.md"),
        ],
        "evidence_registry": _expected_file_record(project_root, "output/reports/evidence_registry.json"),
        "source_ledger": _expected_file_record(project_root, "manuscript/source_ledger.yaml"),
        "schema_manifest": _expected_file_record(project_root, "output/data/autoresearch_schema_manifest.json"),
        "approval_state": {
            "publication_approved": bool(review_decisions.get("publication_approved", False)),
            "decision_source": str(review_decisions.get("human_review_source", "human_review.yaml")),
            "decision_source_exists": bool(review_decisions.get("human_review_source_exists", False)),
        },
        "claim_boundary": (
            "Local research-object manifest for paths and checksums only; it does not claim RO-Crate, "
            "SLSA, external signing, or runtime monitoring compliance."
        ),
    }


def _existing_project_paths(project_root: Path, paths: list[Path]) -> tuple[Path, ...]:
    resolved_project = project_root.resolve()
    self_path = (project_root / "output" / "data" / "research_object_manifest.json").resolve()
    candidates: set[Path] = set()
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        resolved = path.resolve()
        if resolved == self_path:
            continue
        try:
            resolved.relative_to(resolved_project)
        except ValueError:
            continue
        candidates.add(resolved)
    return tuple(sorted(candidates))


def _file_record(project_root: Path, path: Path) -> dict[str, object]:
    rel_path = _relative_path(project_root, path)
    size_bytes = path.stat().st_size if path.exists() else 0
    return {
        "path": rel_path,
        "exists": path.exists(),
        "size_bytes": size_bytes,
        # Surface present-but-empty artifacts so the inventory binds to substance,
        # not just presence (consistent with the integrity gate that fails them).
        "empty": path.exists() and size_bytes == 0,
        "sha256": compute_sha256(path) if path.exists() else "",
    }


def _expected_file_record(project_root: Path, rel_path: str) -> dict[str, object]:
    return _file_record(project_root, project_root / rel_path)


def _relative_path(project_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _load_json_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}
