"""Pipeline output snapshots and comparison reports."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from infrastructure.core.pipeline.artifacts import compute_sha256


@dataclass(frozen=True)
class PipelineSnapshot:
    """Metadata snapshot for one pipeline output state."""

    path: Path
    stage_num: int
    stage_name: str
    artifact_manifest_hash: str
    artifacts: dict[str, str]
    validation_summary: dict[str, Any]
    evidence_fact_count: int
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))

    def to_dict(self) -> dict[str, Any]:
        """Serialize snapshot metadata."""
        payload = asdict(self)
        payload["path"] = _release_safe_path(self.path)
        return payload


@dataclass(frozen=True)
class SnapshotComparison:
    """Comparison between two pipeline snapshots."""

    left: str
    right: str
    artifact_deltas: tuple[str, ...] = ()
    metric_deltas: tuple[str, ...] = ()
    evidence_delta: int = 0
    render_deltas: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize comparison payload."""
        return {
            "left": self.left,
            "right": self.right,
            "artifact_deltas": list(self.artifact_deltas),
            "metric_deltas": list(self.metric_deltas),
            "evidence_delta": self.evidence_delta,
            "render_deltas": list(self.render_deltas),
        }


def create_snapshot(output_dir: Path, *, stage_num: int, stage_name: str) -> PipelineSnapshot:
    """Create and persist a snapshot for an output directory."""
    reports_dir = output_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = reports_dir / "artifact_manifest.json"
    registry_path = reports_dir / "evidence_registry.json"
    validation_path = reports_dir / "validation_report.json"
    artifacts = _artifact_hashes(manifest_path)
    snapshot = PipelineSnapshot(
        path=_snapshot_path(output_dir, stage_num, stage_name),
        stage_num=stage_num,
        stage_name=stage_name,
        artifact_manifest_hash=compute_sha256(manifest_path) if manifest_path.exists() else "",
        artifacts=artifacts,
        validation_summary=_validation_summary(validation_path),
        evidence_fact_count=_evidence_fact_count(registry_path),
    )
    snapshot.path.parent.mkdir(parents=True, exist_ok=True)
    snapshot.path.write_text(json.dumps(snapshot.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return snapshot


def compare_snapshots(left: Path, right: Path) -> SnapshotComparison:
    """Compare two snapshot files or output directories."""
    left_payload = _load_snapshot_or_output(left)
    right_payload = _load_snapshot_or_output(right)
    left_artifacts = _string_dict(left_payload.get("artifacts", {}))
    right_artifacts = _string_dict(right_payload.get("artifacts", {}))
    artifact_deltas = []
    for artifact in sorted(set(left_artifacts) | set(right_artifacts)):
        if left_artifacts.get(artifact) != right_artifacts.get(artifact):
            artifact_deltas.append(artifact)
    render_deltas = [artifact for artifact in artifact_deltas if "/pdf/" in artifact or artifact.endswith(".pdf")]
    evidence_delta = int(right_payload.get("evidence_fact_count", 0) or 0) - int(
        left_payload.get("evidence_fact_count", 0) or 0
    )
    metric_deltas = _metric_deltas(
        left_payload.get("validation_summary", {}), right_payload.get("validation_summary", {})
    )
    return SnapshotComparison(
        left=_release_safe_path(left),
        right=_release_safe_path(right),
        artifact_deltas=tuple(artifact_deltas),
        metric_deltas=tuple(metric_deltas),
        evidence_delta=evidence_delta,
        render_deltas=tuple(render_deltas),
    )


def write_snapshot_comparison(comparison: SnapshotComparison, output_dir: Path) -> tuple[Path, Path]:
    """Write JSON and Markdown comparison reports."""
    report_dir = output_dir / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "snapshot_compare.json"
    md_path = report_dir / "snapshot_compare.md"
    json_path.write_text(json.dumps(comparison.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(snapshot_compare_to_markdown(comparison), encoding="utf-8")
    return json_path, md_path


def snapshot_compare_to_markdown(comparison: SnapshotComparison) -> str:
    """Render a snapshot comparison as Markdown."""
    lines = [
        "# Snapshot Comparison",
        "",
        f"- Left: `{comparison.left}`",
        f"- Right: `{comparison.right}`",
        f"- Evidence delta: `{comparison.evidence_delta}`",
        "",
        "## Artifact Deltas",
        "",
    ]
    lines.extend(f"- `{artifact}`" for artifact in comparison.artifact_deltas)
    if not comparison.artifact_deltas:
        lines.append("No artifact deltas.")
    lines.extend(["", "## Metric Deltas", ""])
    lines.extend(f"- `{metric}`" for metric in comparison.metric_deltas)
    if not comparison.metric_deltas:
        lines.append("No metric deltas.")
    lines.extend(["", "## Render Deltas", ""])
    lines.extend(f"- `{artifact}`" for artifact in comparison.render_deltas)
    if not comparison.render_deltas:
        lines.append("No render deltas.")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for snapshot comparison."""
    parser = argparse.ArgumentParser(description="Compare template pipeline snapshots")
    subparsers = parser.add_subparsers(dest="command", required=True)
    compare_parser = subparsers.add_parser("compare", help="Compare two snapshots or output directories")
    compare_parser.add_argument("left")
    compare_parser.add_argument("right")
    compare_parser.add_argument("--output-dir", help="Output directory for comparison reports")
    args = parser.parse_args(argv)
    comparison = compare_snapshots(Path(args.left), Path(args.right))
    if args.output_dir:
        write_snapshot_comparison(comparison, Path(args.output_dir))
    else:
        print(json.dumps(comparison.to_dict(), indent=2, sort_keys=True))
    return 0


def _snapshot_path(output_dir: Path, stage_num: int, stage_name: str) -> Path:
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in stage_name).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return output_dir / "reports" / "snapshots" / f"stage-{stage_num:02d}-{slug}.json"


def _release_safe_path(path: Path) -> str:
    """Serialize snapshot paths without machine-local checkout prefixes."""
    parts = path.parts
    if "output" in parts:
        index = parts.index("output")
        return str(Path(*parts[index:]))
    if "reports" in parts:
        index = parts.index("reports")
        return str(Path(*parts[index:]))
    return path.name


def _artifact_hashes(manifest_path: Path) -> dict[str, str]:
    payload = _read_json_object(manifest_path)
    artifacts: dict[str, str] = {}
    entries = payload.get("entries", [])
    if not isinstance(entries, list):
        return artifacts
    for row in entries:
        if isinstance(row, dict):
            artifacts[str(row.get("path", ""))] = str(row.get("sha256", ""))
    return artifacts


def _validation_summary(path: Path) -> dict[str, Any]:
    payload = _read_json_object(path)
    return {
        "checks": payload.get("checks", {}),
        "summary": payload.get("summary", {}),
    }


def _evidence_fact_count(path: Path) -> int:
    payload = _read_json_object(path)
    facts = payload.get("facts", [])
    return len(facts) if isinstance(facts, list) else 0


def _load_snapshot_or_output(path: Path) -> dict[str, Any]:
    if path.is_dir():
        snapshot = create_snapshot(path, stage_num=0, stage_name="ad-hoc")
        return snapshot.to_dict()
    return _read_json_object(path)


def _metric_deltas(left: object, right: object) -> tuple[str, ...]:
    if not isinstance(left, dict) or not isinstance(right, dict):
        return ()
    deltas: list[str] = []
    for key in sorted(set(left) | set(right)):
        if left.get(key) != right.get(key):
            deltas.append(str(key))
    return tuple(deltas)


def _string_dict(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {str(key): str(item) for key, item in value.items()}


def _read_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


if __name__ == "__main__":
    raise SystemExit(main())
