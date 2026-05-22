"""Executable-bundle manifest generator.

Reads pinned numerical-claim values, git commit metadata, and the publishing
environment, and produces the ``manifest.json`` described in
``docs/maintenance/stage-10-executable-bundle.md``.

The manifest is the contract between this template and any future agentic
verifier. An agent in 2036 reading the manifest can:

1. Reconstitute the build environment from the bundled Dockerfile + lockfiles
2. Re-execute each claim's verifier function
3. Compare against the pinned value within tolerance
4. Report PASS/FAIL per claim
"""

from __future__ import annotations

import json
import platform
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Final

__all__ = [
    "ManifestClaim",
    "Manifest",
    "build_manifest",
    "SCHEMA_VERSION",
]


SCHEMA_VERSION: Final[str] = "1.0"


@dataclass(frozen=True)
class ManifestClaim:
    """A single quantitative claim asserted in the manuscript.

    Mirrors one entry in ``tests/regression/pinned_values/<project>.json``.
    """

    id: str
    manuscript_section: str
    claim_text: str
    value: float | int | str
    tolerance_abs: float | None
    tolerance_rel: float | None
    verifier_function: str
    verifier_args: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        out: dict[str, object] = {
            "id": self.id,
            "manuscript_section": self.manuscript_section,
            "claim_text": self.claim_text,
            "value": self.value,
            "verifier_function": self.verifier_function,
            "verifier_args": self.verifier_args,
        }
        if self.tolerance_abs is not None:
            out["abs_tolerance"] = self.tolerance_abs
        if self.tolerance_rel is not None:
            out["rel_tolerance"] = self.tolerance_rel
        return out


@dataclass(frozen=True)
class Manifest:
    """Full executable-bundle manifest."""

    schema_version: str
    project_name: str
    commit_hash: str
    rendered_at: str
    renderer: str
    python_version: str
    platform: str
    entry_points: dict[str, str]
    claims: tuple[ManifestClaim, ...]
    external_data: tuple[dict[str, object], ...] = field(default_factory=tuple)
    archival_receipts: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "project_name": self.project_name,
            "commit_hash": self.commit_hash,
            "rendered_at": self.rendered_at,
            "renderer": self.renderer,
            "python_version": self.python_version,
            "platform": self.platform,
            "entry_points": dict(self.entry_points),
            "claims": [c.to_dict() for c in self.claims],
            "external_data": [dict(d) for d in self.external_data],
            "archival_receipts": dict(self.archival_receipts),
        }

    def write_to(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def _git_commit_hash(repo_dir: Path) -> str:
    """Best-effort current commit hash; returns ``"unknown"`` outside a repo."""

    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return "unknown"
    return result.stdout.strip() or "unknown"


def _load_pinned_values(pinned_path: Path) -> dict[str, dict[str, object]]:
    if not pinned_path.exists():
        return {}
    raw = json.loads(pinned_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Pinned values file at {pinned_path} must contain a JSON object, got {type(raw).__name__}")
    out: dict[str, dict[str, object]] = {}
    for key, value in raw.items():
        if key.startswith("_"):
            continue  # _meta / _example_do_not_use
        if isinstance(value, dict):
            out[key] = value
    return out


def _claim_from_pinned(key: str, entry: dict[str, object]) -> ManifestClaim:
    value = entry.get("value", "")
    if not isinstance(value, (int, float, str)):
        raise ValueError(f"Pinned value for {key!r} must be int/float/str, got {type(value).__name__}")
    verifier_function = str(entry.get("verifier_function", ""))
    verifier_args_raw = entry.get("verifier_args", {})
    verifier_args = dict(verifier_args_raw) if isinstance(verifier_args_raw, dict) else {}

    abs_tol_raw = entry.get("abs_tolerance")
    rel_tol_raw = entry.get("rel_tolerance")
    abs_tol = float(abs_tol_raw) if isinstance(abs_tol_raw, (int, float)) else None
    rel_tol = float(rel_tol_raw) if isinstance(rel_tol_raw, (int, float)) else None

    return ManifestClaim(
        id=key,
        manuscript_section=str(entry.get("manuscript_section", "")),
        claim_text=str(entry.get("claim_text", "")),
        value=value,
        tolerance_abs=abs_tol,
        tolerance_rel=rel_tol,
        verifier_function=verifier_function,
        verifier_args=verifier_args,
    )


def build_manifest(
    *,
    project_name: str,
    repo_dir: Path,
    pinned_values_path: Path,
    renderer: str = "template/v1.0.0",
    entry_points: dict[str, str] | None = None,
    external_data: tuple[dict[str, object], ...] = (),
    archival_receipts: dict[str, str] | None = None,
) -> Manifest:
    """Build a Manifest for a single project's executable bundle.

    Parameters
    ----------
    project_name
        Name of the project under ``projects/<name>/``.
    repo_dir
        Path to the repository root (used for git commit hash lookup).
    pinned_values_path
        Path to ``tests/regression/pinned_values/<project>.json``.
    renderer
        Tool name + version stamped into the manifest.
    entry_points
        Dictionary of named entry points (e.g. ``{"reproduce_all": "docker compose run reproduce"}``).
        Defaults to a standard set.
    external_data
        Records of external data dependencies (URL + SHA-256 + size).
    archival_receipts
        Map of provider → identifier (DOI, CID, SWHID) for the published artifacts.
    """

    pinned = _load_pinned_values(pinned_values_path)
    claims = tuple(_claim_from_pinned(k, v) for k, v in pinned.items())

    default_entry_points = entry_points or {
        "reproduce_all": "docker compose run reproduce",
        "tests": "docker compose run tests",
        "render_pdf": "docker compose run render",
        "verify_claims": "docker compose run verify",
    }

    return Manifest(
        schema_version=SCHEMA_VERSION,
        project_name=project_name,
        commit_hash=_git_commit_hash(repo_dir),
        rendered_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        renderer=renderer,
        python_version=platform.python_version(),
        platform=f"{platform.system()}-{platform.machine()}",
        entry_points=default_entry_points,
        claims=claims,
        external_data=external_data,
        archival_receipts=archival_receipts or {},
    )
