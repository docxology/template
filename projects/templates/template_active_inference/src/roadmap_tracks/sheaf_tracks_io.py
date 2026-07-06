"""Shared I/O and manuscript registry loaders for sheaf-track builders."""

from __future__ import annotations

import copy
import hashlib
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

# Re-exported for the sheaf-track builder modules that import ``_load_json`` /
# ``_write_json`` from this module; the canonical implementations live in
# ``json_io`` so read/write behaviour stays identical across the package.
from json_io import load_json as _load_json
from json_io import write_json as _write_json  # noqa: F401  (re-exported for sheaf_tracks_write)


@lru_cache(maxsize=256)
def _parse_yaml_cached(path_str: str, _mtime_ns: int, _size: int) -> dict[str, Any]:
    """Parse a YAML file, memoized on (path, mtime, size).

    The artifact builders read the same manifest/registry/config/ledger YAML files
    dozens of times per ``write_sheaf_track_artifacts`` call; parsing dominates
    (~579 parses / ~7.5s in a single call). The cache key includes mtime_ns AND size
    so any rewrite (e.g. negative-control tests mutating then restoring these files)
    invalidates the entry. Callers receive a deepcopy via ``_load_yaml`` so mutation
    of the returned dict can never corrupt the cached object.
    """
    data = yaml.safe_load(Path(path_str).read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    stat = path.stat()
    return copy.deepcopy(_parse_yaml_cached(str(path), stat.st_mtime_ns, stat.st_size))


def _load_structured(path: Path) -> dict[str, Any]:
    if path.suffix.lower() in {".yaml", ".yml"}:
        return _load_yaml(path)
    return _load_json(path)


def _bridge_reference_section_status(row: dict[str, Any]) -> tuple[bool, bool]:
    sections = [str(section) for section in row.get("figure_reference_sections") or []]
    bindings = row.get("reference_track_bindings") or {}
    sheaf_bound = bool(sections) and all(bool(bindings.get(section)) for section in sections)
    visualization_bound = sheaf_bound and all(
        "visualization" in set(bindings.get(section) or []) for section in sections
    )
    return sheaf_bound, visualization_bound


def _sha256(path: Path) -> str:
    if not path.is_file():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _analysis_scripts(root: Path) -> list[str]:
    cfg = _load_yaml(root / "manuscript" / "config.yaml")
    return [str(script) for script in ((cfg.get("analysis") or {}).get("scripts") or [])]


def _registry_tracks(root: Path) -> dict[str, dict[str, Any]]:
    registry = _load_yaml(root / "manuscript" / "sheaf" / "tracks.yaml")
    tracks = registry.get("tracks") or {}
    return tracks if isinstance(tracks, dict) else {}


def _manifest_sections(root: Path) -> list[dict[str, Any]]:
    manifest = _load_yaml(root / "manuscript" / "sheaf" / "manifest.yaml")
    sections = manifest.get("sections") or []
    return [section for section in sections if isinstance(section, dict)]


def _bound_tracks(root: Path) -> dict[str, list[str]]:
    bound: dict[str, list[str]] = {}
    for section in _manifest_sections(root):
        section_id = str(section.get("id") or "")
        tracks = section.get("tracks") or {}
        if not isinstance(tracks, dict):
            continue
        for track_id in tracks:
            bound.setdefault(str(track_id), []).append(section_id)
    return bound


def _pipeline_tracks(root: Path) -> list[dict[str, Any]]:
    tracks_yaml = _load_yaml(root / "tracks.yaml")
    tracks = tracks_yaml.get("tracks") or []
    return [track for track in tracks if isinstance(track, dict) and track.get("id")]


def _claim_records(root: Path) -> list[dict[str, Any]]:
    ledger = _load_yaml(root / "data" / "claim_ledger.yaml")
    claims = ledger.get("claims") or []
    return [claim for claim in claims if isinstance(claim, dict)]


def _claim_ids_by_path(root: Path) -> dict[str, list[str]]:
    by_path: dict[str, list[str]] = {}
    for claim in _claim_records(root):
        rel = claim.get("path")
        claim_id = claim.get("id")
        if rel and claim_id:
            by_path.setdefault(str(rel), []).append(str(claim_id))
    return by_path


def _claim_ids_by_track(root: Path) -> dict[str, list[str]]:
    by_track: dict[str, list[str]] = {}
    for claim in _claim_records(root):
        claim_id = str(claim.get("id") or "")
        for track in claim.get("tracks") or []:
            by_track.setdefault(str(track), []).append(claim_id)
    return by_track


def _artifact_maps() -> tuple[dict[str, str], dict[str, tuple[str, ...]], dict[str, tuple[str, ...]]]:
    from manuscript.sheaf.semantic import ARTIFACT_CONSUMERS, ARTIFACT_GATES, ARTIFACT_PRODUCERS

    return ARTIFACT_PRODUCERS, ARTIFACT_CONSUMERS, ARTIFACT_GATES


def _source_commit(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return "unknown"
    return result.stdout.strip() or "unknown"


def _deterministic_seed(root: Path) -> int:
    payload = _load_yaml(root / "pymdp.yaml")
    return int(payload.get("random_seed", payload.get("seed", 0)) or 0)


def _config_digest(root: Path) -> str:
    inputs = (
        "manuscript/config.yaml",
        "manuscript/sheaf/manifest.yaml",
        "manuscript/sheaf/tracks.yaml",
        "manuscript/sheaf/coverage.yaml",
        "tracks.yaml",
        "figures.yaml",
        "pymdp.yaml",
        "data/claim_ledger.yaml",
    )
    digest = hashlib.sha256()
    for rel in inputs:
        path = root / rel
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        if path.is_file():
            digest.update(_sha256(path).encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()
