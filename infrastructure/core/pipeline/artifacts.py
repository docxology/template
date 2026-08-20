"""Artifact manifests for advisory pipeline reproducibility controls."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from collections import Counter
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Literal

from infrastructure.core.files.portability import sanitize_machine_local_paths
from infrastructure.core.pipeline.types import StageContract

_IGNORED_OUTPUT_PARTS = frozenset(
    {
        ".checkpoints",
        ".history",
        ".pipeline",
        "logs",
        "hitl",
        "snapshots",
        "__pycache__",
        "fulltext",
        "llm",
        "translations",
    }
)
_IGNORED_OUTPUT_FILENAMES = frozenset(
    {
        "artifact_manifest.json",
        "autoresearch_readiness.json",
        "autoresearch_readiness.md",
        "diagnostics.json",
        "evidence_registry.json",
        "evidence_registry_full.json",
        "output_statistics.json",
        "output_statistics.txt",
        "rendered_provenance.json",
        "snapshot_compare.json",
        "snapshot_compare.md",
        "validation_report.json",
        "validation_report.md",
    }
)
OutputInventoryMode = Literal["stable-shippable-output-v1", "stable-local-output-v1"]
_IGNORED_OUTPUT_SUFFIXES = frozenset({".aux", ".log", ".nav", ".snm", ".toc", ".vrb"})
STABLE_OUTPUT_INVENTORY_MODE: OutputInventoryMode = "stable-shippable-output-v1"
STABLE_LOCAL_OUTPUT_INVENTORY_MODE: OutputInventoryMode = "stable-local-output-v1"


@dataclass(frozen=True)
class ArtifactManifestEntry:
    """One generated artifact recorded with deterministic provenance."""

    path: str
    size_bytes: int
    sha256: str
    stage_num: int
    stage_name: str
    contract_match: bool
    timestamp: str = field(default_factory=lambda: _artifact_timestamp())


@dataclass(frozen=True)
class ArtifactManifest:
    """Stage or aggregate artifact manifest."""

    entries: tuple[ArtifactManifestEntry, ...]
    issues: tuple[str, ...] = ()
    inventory_mode: OutputInventoryMode = STABLE_OUTPUT_INVENTORY_MODE

    def to_dict(self) -> dict[str, object]:
        """Serialize this object to a plain dict for JSON output."""
        return {
            "entries": [asdict(entry) for entry in self.entries],
            "inventory_mode": parse_output_inventory_mode(self.inventory_mode),
            "issues": list(self.issues),
        }


@dataclass(frozen=True)
class ArtifactValidationReport:
    """Validation result for an artifact manifest."""

    issues: tuple[str, ...] = ()

    @property
    def valid(self) -> bool:
        """Return True if the artifact is valid."""
        return not self.issues


@dataclass(frozen=True)
class StableOutputInventory:
    """Canonical stable files discovered below one output tree."""

    files: tuple[Path, ...]
    issues: tuple[str, ...] = ()
    mode: OutputInventoryMode = STABLE_OUTPUT_INVENTORY_MODE


@dataclass(frozen=True)
class _GitIgnoreEvaluation:
    """One batched Git-ignore query, including fail-closed error state."""

    matches: Mapping[Path, tuple[bytes, bytes, bytes]]
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


def parse_output_inventory_mode(value: object) -> OutputInventoryMode:
    """Parse a stable-output inventory mode without silently widening scope."""
    if value == STABLE_OUTPUT_INVENTORY_MODE:
        return STABLE_OUTPUT_INVENTORY_MODE
    if value == STABLE_LOCAL_OUTPUT_INVENTORY_MODE:
        return STABLE_LOCAL_OUTPUT_INVENTORY_MODE
    raise ValueError(f"unsupported stable output inventory mode: {value!r}")


def artifact_manifest_inventory_mode(payload: Mapping[str, object]) -> OutputInventoryMode:
    """Read a manifest mode, defaulting legacy payloads to strict shippable scope."""
    return parse_output_inventory_mode(payload.get("inventory_mode", STABLE_OUTPUT_INVENTORY_MODE))


def artifact_manifest_from_payload(payload: object) -> ArtifactManifest:
    """Parse the shared manifest schema without coercing untrusted JSON values."""
    if not isinstance(payload, dict):
        raise ValueError("artifact manifest must contain a mapping")
    raw_entries = payload.get("entries")
    raw_issues = payload.get("issues")
    if not isinstance(raw_entries, list):
        raise ValueError("artifact manifest entries must be a list")
    if not isinstance(raw_issues, list) or any(not isinstance(issue, str) for issue in raw_issues):
        raise ValueError("artifact manifest issues must be a list of strings")
    entries = tuple(artifact_manifest_entry_from_payload(row) for row in raw_entries)
    return ArtifactManifest(
        entries=entries,
        issues=tuple(raw_issues),
        inventory_mode=artifact_manifest_inventory_mode(payload),
    )


def artifact_manifest_entry_from_payload(payload: object) -> ArtifactManifestEntry:
    """Parse one manifest entry with exact, cross-platform-safe field types."""
    if not isinstance(payload, dict):
        raise ValueError("artifact manifest entry must contain a mapping")
    required = {
        "path",
        "size_bytes",
        "sha256",
        "stage_num",
        "stage_name",
        "contract_match",
        "timestamp",
    }
    missing = sorted(required - payload.keys())
    if missing:
        raise ValueError("artifact manifest entry missing fields: " + ", ".join(missing))

    raw_path = payload["path"]
    if not isinstance(raw_path, str) or not _is_canonical_manifest_path(raw_path):
        raise ValueError(f"artifact manifest entry path is not canonical: {raw_path!r}")
    size_bytes = payload["size_bytes"]
    stage_num = payload["stage_num"]
    if type(size_bytes) is not int or size_bytes < 0:
        raise ValueError("artifact manifest entry size_bytes must be a non-negative integer")
    if type(stage_num) is not int or stage_num < 0:
        raise ValueError("artifact manifest entry stage_num must be a non-negative integer")
    sha256 = payload["sha256"]
    if not isinstance(sha256, str) or len(sha256) != 64 or any(ch not in "0123456789abcdef" for ch in sha256):
        raise ValueError("artifact manifest entry sha256 must be 64 lowercase hexadecimal characters")
    stage_name = payload["stage_name"]
    if not isinstance(stage_name, str) or not stage_name.strip():
        raise ValueError("artifact manifest entry stage_name must be a nonempty string")
    contract_match = payload["contract_match"]
    if type(contract_match) is not bool:
        raise ValueError("artifact manifest entry contract_match must be a boolean")
    timestamp = payload["timestamp"]
    if not isinstance(timestamp, str):
        raise ValueError("artifact manifest entry timestamp must be a string")
    return ArtifactManifestEntry(
        path=raw_path,
        size_bytes=size_bytes,
        sha256=sha256,
        stage_num=stage_num,
        stage_name=stage_name,
        contract_match=contract_match,
        timestamp=timestamp,
    )


def _is_canonical_manifest_path(raw_path: str) -> bool:
    """Return whether *raw_path* is canonical POSIX project-output syntax."""
    if not raw_path.startswith("output/") or raw_path.endswith("/") or "\\" in raw_path or "\0" in raw_path:
        return False
    parts = raw_path.split("/")
    return (
        len(parts) > 1
        and all(part not in {"", ".", ".."} for part in parts)
        and not any(len(part) == 2 and part[0].isalpha() and part[1] == ":" for part in parts)
    )


def output_inventory_mode_for_project(repo_root: Path, project_dir: Path) -> OutputInventoryMode:
    """Authorize the stable inventory mode from the resolved project lifecycle.

    Only real project directories confined below the public
    ``projects/templates/`` tree receive Git-shippable mode. Resolved external
    sidecars and every other lifecycle location receive stable-local mode.
    Collector behavior never infers this authorization from Git ignore rules:
    an accidental blanket ignore in a public exemplar must still fail closed.
    """
    templates_root = (repo_root / "projects" / "templates").resolve()
    resolved_project = project_dir.resolve()
    try:
        resolved_project.relative_to(templates_root)
    except ValueError:
        return STABLE_LOCAL_OUTPUT_INVENTORY_MODE
    return STABLE_OUTPUT_INVENTORY_MODE


def compute_sha256(path: Path) -> str:
    """Compute a SHA256 digest for a file."""
    if path.is_symlink():
        raise ValueError(f"refusing to hash symlink artifact: {path}")
    if not path.is_file():
        raise ValueError(f"artifact is not a regular file: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_stage_artifact_manifest(
    *,
    repo_root: Path,
    project_dir: Path,
    stage_num: int,
    stage_name: str,
    contract: StageContract,
) -> ArtifactManifest:
    """Write a stage-specific artifact manifest and return it."""
    output_dir = project_dir / "output"
    declared_paths = _declared_output_paths(repo_root, project_dir, contract)
    entries: list[ArtifactManifestEntry] = []
    issues: list[str] = []
    inventory_mode = output_inventory_mode_for_project(repo_root, project_dir)

    if output_dir.is_symlink():
        raise ValueError(f"refusing to write a manifest through symlink output directory: {output_dir}")
    sanitize_machine_local_paths(output_dir)

    for declared in declared_paths:
        if not declared.exists():
            issues.append(f"missing declared output: {_display_path(repo_root, declared)}")

    if output_dir.exists():
        inventory = collect_stable_output_inventory(
            output_dir,
            inventory_mode=inventory_mode,
        )
        issues.extend(inventory.issues)
        for path in inventory.files:
            relative_path = path.relative_to(project_dir).as_posix()
            digest = compute_sha256(path)
            contract_match = not declared_paths or any(_is_relative_to(path, declared) for declared in declared_paths)
            entries.append(
                ArtifactManifestEntry(
                    path=relative_path,
                    size_bytes=path.stat().st_size,
                    sha256=digest,
                    stage_num=stage_num,
                    stage_name=stage_name,
                    contract_match=contract_match,
                )
            )

    manifest = ArtifactManifest(
        entries=tuple(entries),
        issues=tuple(issues),
        inventory_mode=inventory_mode,
    )
    manifest_path = _stage_manifest_path(output_dir, stage_num, stage_name)
    symlink_component = _first_symlink_component(output_dir, manifest_path)
    if symlink_component is not None:
        raise ValueError(f"refusing to write a manifest through symlink: {symlink_component}")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def aggregate_artifact_manifests(
    output_dir: Path,
    *,
    inventory_mode: OutputInventoryMode = STABLE_OUTPUT_INVENTORY_MODE,
) -> ArtifactManifest:
    """Aggregate all stage manifests into ``output/reports/artifact_manifest.json``."""
    inventory_mode = parse_output_inventory_mode(inventory_mode)
    if output_dir.is_symlink():
        raise ValueError(f"refusing to aggregate through symlink output directory: {output_dir}")
    stage_dir = output_dir / ".pipeline" / "artifacts"
    project_dir = output_dir.parent
    entries: list[ArtifactManifestEntry] = []
    issues: list[str] = []
    if output_dir.exists():
        for path in sorted(output_dir.rglob("*")):
            if path.is_symlink():
                issues.append(_symlink_issue(path, output_dir))

    stage_dir_is_safe = _first_symlink_component(output_dir, stage_dir) is None
    if stage_dir_is_safe and stage_dir.exists():
        for manifest_path in sorted(stage_dir.glob("stage-*.json")):
            if manifest_path.is_symlink():
                continue
            try:
                payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                issues.append(f"cannot read stage artifact manifest: {manifest_path.name}: {exc}")
                continue
            if not isinstance(payload, dict):
                issues.append(f"cannot read stage artifact manifest: {manifest_path.name}: expected a mapping")
                continue
            try:
                stage_manifest = artifact_manifest_from_payload(payload)
            except ValueError as exc:
                issues.append(f"cannot read stage artifact manifest: {manifest_path.name}: {exc}")
                continue
            if "inventory_mode" in payload:
                stage_inventory_mode = stage_manifest.inventory_mode
                if stage_inventory_mode != inventory_mode:
                    issues.append(
                        "stage artifact manifest inventory mode mismatch: "
                        f"{manifest_path.name}: expected {inventory_mode}, found {stage_inventory_mode}"
                    )
            entries.extend(entry for entry in stage_manifest.entries if not _is_ignored_manifest_path(entry.path))
            issues.extend(stage_manifest.issues)

    if not entries and output_dir.exists():
        inventory = collect_stable_output_inventory(output_dir, inventory_mode=inventory_mode)
        issues.extend(inventory.issues)
        for path in inventory.files:
            entries.append(
                ArtifactManifestEntry(
                    path=path.relative_to(project_dir).as_posix(),
                    size_bytes=path.stat().st_size,
                    sha256=compute_sha256(path),
                    stage_num=0,
                    stage_name="standalone-output-scan",
                    contract_match=True,
                )
            )

    aggregate = ArtifactManifest(
        entries=_coalesce_artifact_entries(entries),
        issues=tuple(dict.fromkeys(issues)),
        inventory_mode=inventory_mode,
    )
    report_path = output_dir / "reports" / "artifact_manifest.json"
    symlink_component = _first_symlink_component(output_dir, report_path)
    if symlink_component is not None:
        raise ValueError(f"refusing to write an aggregate manifest through symlink: {symlink_component}")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(aggregate.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return aggregate


def collect_stable_output_inventory(
    output_dir: Path,
    *,
    git_ignore_output_dir: Path | None = None,
    git_ignore_path_overrides: Mapping[Path, Path] | None = None,
    inventory_mode: OutputInventoryMode = STABLE_OUTPUT_INVENTORY_MODE,
) -> StableOutputInventory:
    """Collect stable output files using publication and local-output semantics.

    This is the single read-only inventory used by artifact manifests and by
    deterministic statistics. Runtime state, self-referential reports, build
    intermediates, and files below hidden paths are always excluded. Public
    exemplar outputs additionally honor Git ignores so every admitted artifact
    can ship in a fresh clone. An authorized standalone/private lifecycle caller
    may explicitly select ``stable-local-output-v1`` so valid local deliverables
    remain testable without being misrepresented as Git-shippable evidence.
    Shippable mode is always the default and is never relaxed by observing an
    ignored output path. Symlinks are reported as issues rather than silently
    followed. ``git_ignore_output_dir`` maps copied files back to the canonical
    project output tree for Git-ignore evaluation; ``git_ignore_path_overrides``
    records promotions such as Stage 5's copied root PDF whose canonical source
    lives under ``pdf/``.
    """
    output_dir = output_dir.absolute()
    if output_dir.is_symlink():
        raise ValueError(f"refusing to collect through symlink output directory: {output_dir}")
    ignore_output_dir = (git_ignore_output_dir or output_dir).absolute()
    if ignore_output_dir.is_symlink():
        raise ValueError(f"refusing to map Git ignores through symlink output directory: {ignore_output_dir}")
    project_dir = ignore_output_dir.parent
    inventory_mode = parse_output_inventory_mode(inventory_mode)
    files: list[Path] = []
    issues: list[str] = []
    if output_dir.exists():
        snapshot_paths = tuple(sorted(output_dir.rglob("*")))
        candidate_metadata: dict[Path, os.stat_result] = {}
        snapshot_symlinks: set[Path] = set()
        for path in snapshot_paths:
            try:
                metadata = path.lstat()
            except OSError:
                continue
            if stat.S_ISLNK(metadata.st_mode):
                snapshot_symlinks.add(path)
            elif stat.S_ISREG(metadata.st_mode):
                candidate_metadata[path] = metadata
        candidates = tuple(candidate_metadata)
        # Never record an artifact git will not ship — the manifest is committed
        # evidence, and a fresh clone would read the entry as drift. A copied
        # delivery mirror is itself normally ignored, so evaluate each copied
        # relative path at its canonical source-output location when supplied.
        overrides = dict(git_ignore_path_overrides or {})
        git_candidates: dict[Path, list[Path]] = {}
        for path in candidates:
            relative = path.relative_to(output_dir)
            source_relative = overrides.get(relative, relative)
            if source_relative.is_absolute() or ".." in source_relative.parts:
                raise ValueError(f"invalid Git-ignore path override: {relative} -> {source_relative}")
            git_candidates.setdefault(ignore_output_dir / source_relative, []).append(path)
        candidate_evaluation = _git_ignore_matches(tuple(git_candidates), project_dir)
        if not candidate_evaluation.ok and _git_worktree_marker(project_dir) is not None:
            issues.append(f"git ignore evaluation failed: {candidate_evaluation.error}")
            return StableOutputInventory(files=(), issues=tuple(issues), mode=inventory_mode)
        candidate_matches = candidate_evaluation.matches
        blanket_rules: set[tuple[bytes, bytes, bytes]] = set()
        if inventory_mode == STABLE_LOCAL_OUTPUT_INVENTORY_MODE:
            # Local mode bypasses only the caller-authorized packaging ignore
            # covering the complete output tree (including ``output/``,
            # ``output/*``, and ``output/**`` spellings). Project-specific
            # ignores remain authoritative whenever Git can distinguish them.
            probes = (
                ignore_output_dir / "__template_output_inventory_probe__.sentinel-a",
                ignore_output_dir / "__template_output_inventory_probe__" / "artifact.sentinel-b",
                ignore_output_dir / "__template_output_inventory_probe__" / "nested" / "leaf",
            )
            probe_evaluation = _git_ignore_matches(probes, project_dir)
            if not probe_evaluation.ok and _git_worktree_marker(project_dir) is not None:
                issues.append(f"git ignore evaluation failed: {probe_evaluation.error}")
                return StableOutputInventory(files=(), issues=tuple(issues), mode=inventory_mode)
            probe_matches = probe_evaluation.matches
            matched_rules = set(probe_matches.values())
            if len(probe_matches) == len(probes) and len(matched_rules) == 1:
                blanket_rules.update(matched_rules)
        ignored = {
            destination
            for path, rule in candidate_matches.items()
            if path in git_candidates and rule not in blanket_rules
            for destination in git_candidates[path]
        }
        if output_dir.is_symlink():
            raise ValueError(f"refusing to collect through symlink output directory: {output_dir}")
        if ignore_output_dir.is_symlink():
            raise ValueError(f"refusing to map Git ignores through symlink output directory: {ignore_output_dir}")
        symlinks = set(snapshot_symlinks)
        for path in snapshot_paths:
            symlink_component = _first_symlink_component(output_dir, path)
            if symlink_component is not None:
                symlinks.add(symlink_component)
        issues.extend(_symlink_issue(path, output_dir) for path in sorted(symlinks))
        for path in candidates:
            if _first_symlink_component(output_dir, path) is not None:
                continue
            try:
                current_metadata = path.lstat()
            except OSError:
                continue
            initial_metadata = candidate_metadata[path]
            if (
                not stat.S_ISREG(current_metadata.st_mode)
                or current_metadata.st_dev != initial_metadata.st_dev
                or current_metadata.st_ino != initial_metadata.st_ino
                or current_metadata.st_size != initial_metadata.st_size
                or current_metadata.st_mtime_ns != initial_metadata.st_mtime_ns
                or current_metadata.st_ctime_ns != initial_metadata.st_ctime_ns
            ):
                continue
            if _is_ignored_output(path, output_dir) or path in ignored:
                continue
            files.append(path)
    return StableOutputInventory(files=tuple(files), issues=tuple(dict.fromkeys(issues)), mode=inventory_mode)


def collect_current_artifact_manifest(
    output_dir: Path,
    *,
    inventory_mode: OutputInventoryMode = STABLE_OUTPUT_INVENTORY_MODE,
) -> ArtifactManifest:
    """Collect the complete stable output tree in the explicitly selected mode."""
    output_dir = output_dir.absolute()
    project_dir = output_dir.parent
    inventory = collect_stable_output_inventory(output_dir, inventory_mode=inventory_mode)
    entries: list[ArtifactManifestEntry] = []
    for path in inventory.files:
        entries.append(
            ArtifactManifestEntry(
                path=path.relative_to(project_dir).as_posix(),
                size_bytes=path.stat().st_size,
                sha256=compute_sha256(path),
                stage_num=0,
                stage_name="current-output-snapshot",
                contract_match=True,
            )
        )
    return ArtifactManifest(
        entries=tuple(entries),
        issues=inventory.issues,
        inventory_mode=inventory.mode,
    )


def snapshot_current_artifact_manifest(
    output_dir: Path,
    *,
    inventory_mode: OutputInventoryMode = STABLE_OUTPUT_INVENTORY_MODE,
) -> ArtifactManifest:
    """Write an integrity baseline for the output tree's current stable files.

    This explicit maintenance operation is useful after a targeted render and
    validation run that did not execute through :class:`PipelineExecutor`.
    Historical per-stage manifests remain untouched; the aggregate report is a
    clearly labelled current-output snapshot rather than invented stage
    provenance.
    """
    if output_dir.is_symlink():
        raise ValueError(f"refusing to snapshot through symlink output directory: {output_dir}")
    sanitize_machine_local_paths(output_dir)
    manifest = collect_current_artifact_manifest(output_dir, inventory_mode=inventory_mode)
    report_path = output_dir / "reports" / "artifact_manifest.json"
    symlink_component = _first_symlink_component(output_dir, report_path)
    if symlink_component is not None:
        raise ValueError(f"refusing to write an aggregate manifest through symlink: {symlink_component}")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def validate_artifact_manifest(
    manifest: ArtifactManifest,
    *,
    project_dir: Path | None = None,
    expected_inventory_mode: OutputInventoryMode | None = None,
) -> ArtifactValidationReport:
    """Validate manifest issues and optionally verify current file hashes."""
    issues = list(manifest.issues)
    expected_paths: set[str] | None = None
    try:
        manifest_inventory_mode = parse_output_inventory_mode(manifest.inventory_mode)
    except ValueError as exc:
        issues.append(str(exc))
        manifest_inventory_mode = None
    if expected_inventory_mode is not None:
        expected_inventory_mode = parse_output_inventory_mode(expected_inventory_mode)
        if manifest_inventory_mode is not None and manifest_inventory_mode != expected_inventory_mode:
            issues.append(
                f"artifact inventory mode mismatch: expected {expected_inventory_mode}, found {manifest_inventory_mode}"
            )
        if project_dir is not None:
            project_root = project_dir.absolute()
            inventory = collect_stable_output_inventory(
                project_root / "output",
                inventory_mode=expected_inventory_mode,
            )
            issues.extend(inventory.issues)
            expected_paths = {path.relative_to(project_root).as_posix() for path in inventory.files}
    if project_dir is not None:
        manifest_paths = {entry.path for entry in manifest.entries}
        if expected_paths is not None:
            issues.extend(f"unattested stable artifact: {path}" for path in sorted(expected_paths - manifest_paths))
        duplicate_paths = sorted(
            path for path, count in Counter(entry.path for entry in manifest.entries).items() if count > 1
        )
        issues.extend(f"duplicate artifact path: {path}" for path in duplicate_paths)
        for entry in _coalesce_artifact_entries(manifest.entries):
            path, path_issue = _validated_manifest_path(project_dir, entry.path)
            if path_issue is not None:
                issues.append(path_issue)
                continue
            if _is_ignored_manifest_path(entry.path):
                issues.append(f"non-stable artifact forbidden: {entry.path}")
                continue
            if expected_paths is not None and entry.path not in expected_paths:
                issues.append(f"artifact outside {expected_inventory_mode} inventory: {entry.path}")
                continue
            assert path is not None
            if not path.exists():
                issues.append(f"missing artifact: {entry.path}")
                continue
            try:
                size_bytes = path.stat().st_size
                digest = compute_sha256(path)
            except (OSError, ValueError) as exc:
                issues.append(f"cannot hash artifact: {entry.path}: {exc}")
                continue
            if size_bytes != entry.size_bytes:
                issues.append(f"changed artifact size: {entry.path}")
            if digest != entry.sha256:
                issues.append(f"changed artifact: {entry.path}")
            if not entry.contract_match:
                issues.append(f"undeclared artifact: {entry.path}")
    return ArtifactValidationReport(issues=tuple(issues))


def _artifact_timestamp() -> str:
    """Return a reproducible manifest timestamp when explicitly supplied."""
    raw = os.environ.get("SOURCE_DATE_EPOCH", "").strip()
    if not raw.isdigit():
        return ""
    return datetime.fromtimestamp(int(raw), tz=timezone.utc).isoformat(timespec="seconds")


def _symlink_issue(path: Path, output_dir: Path) -> str:
    try:
        displayed = path.relative_to(output_dir).as_posix()
    except ValueError:
        displayed = path.as_posix()
    return f"symlink artifact forbidden: {displayed}"


def _first_symlink_component(root: Path, target: Path) -> Path | None:
    current = root
    try:
        parts = target.relative_to(root).parts
    except ValueError:
        return target
    for part in parts:
        current = current / part
        if current.is_symlink():
            return current
    return None


def _validated_manifest_path(project_dir: Path, raw_path: str) -> tuple[Path | None, str | None]:
    relative = Path(raw_path)
    if not _is_canonical_manifest_path(raw_path) or relative.is_absolute():
        return None, f"unsafe artifact path: {raw_path}"

    candidate = project_dir / relative
    if _first_symlink_component(project_dir, candidate) is not None:
        return None, f"symlink artifact forbidden: {raw_path}"

    try:
        candidate.resolve(strict=False).relative_to(project_dir.resolve())
    except (OSError, ValueError):
        return None, f"artifact path escapes project: {raw_path}"
    return candidate, None


def _coalesce_artifact_entries(
    entries: tuple[ArtifactManifestEntry, ...] | list[ArtifactManifestEntry],
) -> tuple[ArtifactManifestEntry, ...]:
    """Keep the latest digest while preserving declaration ownership across stages."""
    latest_by_path: dict[str, ArtifactManifestEntry] = {}
    declared_by_path: dict[str, bool] = {}
    for entry in entries:
        latest_by_path[entry.path] = entry
        declared_by_path[entry.path] = declared_by_path.get(entry.path, False) or entry.contract_match
    return tuple(replace(entry, contract_match=declared_by_path[path]) for path, entry in latest_by_path.items())


def _declared_output_paths(repo_root: Path, project_dir: Path, contract: StageContract) -> tuple[Path, ...]:
    paths: list[Path] = []
    project_slug = _project_slug(repo_root, project_dir)
    for raw in contract.output_artifacts:
        rendered = raw.replace("{project}", project_slug).rstrip("/")
        rendered_path = Path(rendered)
        if rendered_path.is_absolute() or ".." in rendered_path.parts:
            raise ValueError(f"declared artifact path escapes confinement: {raw}")
        if rendered.startswith("projects/"):
            candidate = repo_root / rendered
        elif rendered == f"output/{project_slug}" or rendered.startswith(f"output/{project_slug}/"):
            candidate = repo_root / rendered
        elif rendered.startswith("output/"):
            candidate = project_dir / rendered
        else:
            candidate = project_dir / rendered
        if not _is_relative_to(candidate, repo_root) and not _is_relative_to(candidate, project_dir):
            raise ValueError(f"declared artifact path escapes confinement: {raw}")
        paths.append(candidate)
    return tuple(paths)


def _project_slug(repo_root: Path, project_dir: Path) -> str:
    projects_root = repo_root / "projects"
    for candidate in (project_dir, project_dir.absolute()):
        try:
            return candidate.relative_to(projects_root).as_posix()
        except ValueError:
            continue
    try:
        return project_dir.resolve().relative_to(projects_root.resolve()).as_posix()
    except ValueError:
        pass
    resolved_project = project_dir.resolve()
    for candidate in _project_slug_candidates(projects_root):
        try:
            if candidate.resolve() == resolved_project:
                return candidate.relative_to(projects_root).as_posix()
        except OSError:
            continue
    return project_dir.name


def _project_slug_candidates(projects_root: Path) -> tuple[Path, ...]:
    if not projects_root.exists():
        return ()
    candidates: list[Path] = []
    for child in projects_root.iterdir():
        if child.name.startswith("."):
            continue
        candidates.append(child)
        if child.is_dir() or child.is_symlink():
            try:
                candidates.extend(grandchild for grandchild in child.iterdir() if not grandchild.name.startswith("."))
            except OSError:
                continue
    return tuple(sorted(candidates, key=lambda path: path.as_posix()))


def _stage_manifest_path(output_dir: Path, stage_num: int, stage_name: str) -> Path:
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in stage_name).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return output_dir / ".pipeline" / "artifacts" / f"stage-{stage_num:02d}-{slug}.json"


def git_ignored_paths(paths: "Sequence[Path]", project_dir: Path) -> frozenset[Path]:
    """Return paths Git ignores, failing closed on worktree query errors.

    A committed artifact manifest is publication evidence, so it must only
    reference files that can actually ship. The static suffix list below cannot
    express path-scoped rules like ``output/slides/**/*.tex``, so it drifted from
    ``.gitignore`` and the committed manifest for ``template_code_project`` came
    to list 15 LaTeX intermediates (``.bbl``, ``.blg``, ``_combined_manuscript.tex``,
    ``references.bib``) that exist after a local render but are absent from any
    fresh clone. CI failed on all four Python versions and both platforms while
    the same tests passed locally, because locally those files were present.

    Asking git removes the second source of truth. One batched
    ``git check-ignore --stdin`` call covers the whole candidate set; when git is
    absent and the tree is genuinely not a repository (unit tests build trees
    under ``tmp_path``), this returns empty and the static lists still apply. A
    detected worktree with unavailable or malformed Git output returns every
    candidate, so callers cannot mislabel unevaluated files as shippable.
    """
    evaluation = _git_ignore_matches(paths, project_dir)
    if evaluation.ok:
        return frozenset(evaluation.matches)
    if _git_worktree_marker(project_dir) is not None:
        return frozenset(paths)
    return frozenset()


def _git_ignore_matches(
    paths: "Sequence[Path]",
    project_dir: Path,
    *,
    command: Sequence[str] = ("git",),
) -> _GitIgnoreEvaluation:
    """Return ignored paths with the exact Git rule that selected each path."""
    if not paths:
        return _GitIgnoreEvaluation(matches={})
    payload = b"\0".join(os.fsencode(path) for path in paths) + b"\0"
    try:
        proc = subprocess.run(  # noqa: S603 - fixed argv, no shell
            [*command, "-C", str(project_dir), "check-ignore", "-v", "-z", "--stdin"],
            input=payload,
            capture_output=True,
            check=False,
        )
    except OSError:
        return _GitIgnoreEvaluation(matches={}, error="git check-ignore unavailable")
    except ValueError:
        return _GitIgnoreEvaluation(matches={}, error="git check-ignore invocation invalid")
    # 0 = some paths ignored, 1 = none ignored; anything else means git could not
    # answer. The collector decides whether a genuine non-repository tree may
    # use static fallback or a detected worktree must fail closed.
    if proc.returncode not in {0, 1}:
        return _GitIgnoreEvaluation(
            matches={},
            error=f"git check-ignore exited with status {proc.returncode}",
        )
    fields = proc.stdout.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()
    if len(fields) % 4 != 0 or (proc.returncode == 0 and not fields) or (proc.returncode == 1 and fields):
        return _GitIgnoreEvaluation(matches={}, error="git check-ignore returned malformed output")
    matches: dict[Path, tuple[bytes, bytes, bytes]] = {}
    for index in range(0, len(fields), 4):
        source, line_number, pattern, raw_path = fields[index : index + 4]
        # Verbose check-ignore reports the final negation pattern for an
        # explicitly re-included path. Such a path is shippable and must not be
        # returned as ignored.
        if pattern.startswith(b"!"):
            continue
        matches[Path(os.fsdecode(raw_path))] = (source, line_number, pattern)
    return _GitIgnoreEvaluation(matches=matches)


def _git_worktree_marker(project_dir: Path) -> Path | None:
    """Return the nearest ancestor Git marker without invoking Git itself."""
    current = project_dir.absolute()
    for candidate in (current, *current.parents):
        marker = candidate / ".git"
        if marker.is_dir() or marker.is_file():
            return marker
    return None


def _is_ignored_output(path: Path, output_dir: Path) -> bool:
    return _is_ignored_output_relative(path.relative_to(output_dir))


def _is_ignored_output_relative(relative: Path) -> bool:
    """Return whether an output-relative path is outside stable evidence."""
    rel_parts = relative.parts
    # Hidden paths under output are local caches, atomic-write leftovers, or
    # workspace markers rather than publication evidence. Reject every hidden
    # component, not only a hidden leaf: ``data/.private-cache/token`` and
    # ``.git/config`` are just as non-public as ``.partial.png``.
    if any(part.startswith(".") for part in rel_parts):
        return True
    # These are renderer-owned build inputs/intermediates even when a private
    # project blanket-ignores output/ and therefore authorizes local mode.
    # Mirror the path-scoped public .gitignore rules without excluding authored
    # TeX or bibliography deliverables in unrelated output categories.
    category = rel_parts[0] if len(rel_parts) > 1 else "root"
    if category == "pdf" and (
        relative.name.startswith("_combined_manuscript.")
        or (relative.name.startswith("references") and relative.suffix == ".bib")
    ):
        return True
    if category == "slides" and relative.suffix in {
        ".aux",
        ".bbl",
        ".blg",
        ".log",
        ".nav",
        ".out",
        ".snm",
        ".tex",
        ".toc",
        ".vrb",
    }:
        return True
    if relative == Path("fulltext/fulltext_inventory.json"):
        return False
    return (
        any(part in _IGNORED_OUTPUT_PARTS for part in rel_parts)
        or relative.name in _IGNORED_OUTPUT_FILENAMES
        or relative.suffix in _IGNORED_OUTPUT_SUFFIXES
    )


def _is_ignored_manifest_path(raw_path: str) -> bool:
    path = Path(raw_path)
    parts = path.parts
    try:
        output_index = parts.index("output")
        relative = Path(*parts[output_index + 1 :])
    except ValueError:
        relative = path
    return _is_ignored_output_relative(relative)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        pass
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except (OSError, ValueError):
        return False


def _display_path(repo_root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)
