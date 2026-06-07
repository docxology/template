"""Hermetic reproduction bundle builder and verifier (REPRO-BUNDLE-1).

A *repro bundle* captures everything a third party needs to confirm that a
public exemplar reproduces byte-for-byte: the lockfile, the project's artifact
manifest, content hashes of declared output artifacts, a hash pointer to
``docs/_generated/canonical_facts.md``, and the exact pipeline command used to
regenerate the outputs.

Two entry points:

* :func:`build_repro_bundle` — collect inputs for one exemplar into an output
  directory and emit a deterministic (sorted, byte-stable) ``repro_manifest.json``.
* :func:`verify_repro_bundle` — recompute hashes against a checkout and report
  match/mismatch per entry. **Fails closed**: any missing or changed file is a
  mismatch, never a silent pass.

Hashing reuses :func:`infrastructure.core.files.operations.calculate_file_hash`
so this module shares the repo's canonical SHA-256 implementation.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from infrastructure.core.files.operations import calculate_file_hash
from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

SCHEMA_VERSION = "1.0"
BUNDLE_MANIFEST_NAME = "repro_manifest.json"
CANONICAL_FACTS_RELPATH = "docs/_generated/canonical_facts.md"

# Reproduction-input file kinds, in the order they are collected.
_KIND_LOCKFILE = "lockfile"
_KIND_PYPROJECT = "pyproject"
_KIND_ARTIFACT_MANIFEST = "artifact-manifest"
_KIND_CANONICAL_FACTS = "canonical-facts"
_KIND_OUTPUT_ARTIFACT = "output-artifact"


@dataclass(frozen=True)
class BundleEntry:
    """A single hashed reproduction input, relative to the checkout root."""

    kind: str
    path: str
    sha256: str | None
    size_bytes: int
    present: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "path": self.path,
            "present": self.present,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
        }


@dataclass
class VerifyReport:
    """Outcome of verifying a manifest against a checkout."""

    ok: bool
    checked: int
    mismatches: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "checked": self.checked,
            "mismatches": self.mismatches,
        }


def _hash_relpath(checkout_root: Path, relpath: str) -> tuple[str | None, int, bool]:
    """Return ``(sha256, size_bytes, present)`` for *relpath* under *checkout_root*."""
    target = checkout_root / relpath
    if not target.is_file():
        return None, 0, False
    digest = calculate_file_hash(target)
    size = target.stat().st_size
    return digest, size, digest is not None


def _make_entry(checkout_root: Path, kind: str, relpath: str) -> BundleEntry:
    digest, size, present = _hash_relpath(checkout_root, relpath)
    return BundleEntry(kind=kind, path=relpath, sha256=digest, size_bytes=size, present=present)


def _declared_output_relpaths(project_dir: Path) -> list[str]:
    """Read declared output artifact paths from the project artifact manifest.

    The artifact manifest lives at ``output/reports/artifact_manifest.json`` and
    stores entries whose ``path`` values are relative to the repository root.
    Missing or malformed manifests yield an empty list (the lockfile and
    canonical-facts pointer still anchor the bundle).
    """
    manifest_path = project_dir / "output" / "reports" / "artifact_manifest.json"
    if not manifest_path.is_file():
        return []
    try:
        raw: Any = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.warning("Unreadable artifact manifest at %s — skipping output artifacts.", manifest_path)
        return []
    if not isinstance(raw, dict):
        return []
    entries = raw.get("entries")
    if not isinstance(entries, list):
        return []
    paths: list[str] = []
    for entry in entries:
        if isinstance(entry, dict):
            path = entry.get("path")
            if isinstance(path, str) and path:
                paths.append(path)
    return sorted(set(paths))


def _artifact_manifest_relpath(repo_root: Path, project_dir: Path) -> str | None:
    """Return the repo-relative path to the project artifact manifest, if present."""
    manifest_path = project_dir / "output" / "reports" / "artifact_manifest.json"
    if not manifest_path.is_file():
        return None
    return manifest_path.relative_to(repo_root).as_posix()


def _reproduce_commands(project_name: str) -> list[str]:
    """Exact, deterministic reproduction commands for *project_name*."""
    return [
        f"uv run python scripts/execute_pipeline.py --project {project_name} --core-only",
    ]


def collect_entries(repo_root: Path, project_name: str) -> list[BundleEntry]:
    """Collect and hash all reproduction inputs for *project_name*.

    Entries are returned sorted by ``path`` for deterministic manifests.
    """
    repo_root = repo_root.resolve()
    project_dir = repo_root / "projects" / project_name
    if not project_dir.is_dir():
        # Public exemplars live under projects/templates/<name>.
        nested = repo_root / "projects" / "templates" / project_name
        if nested.is_dir():
            project_dir = nested

    entries: list[BundleEntry] = [
        _make_entry(repo_root, _KIND_LOCKFILE, "uv.lock"),
        _make_entry(repo_root, _KIND_PYPROJECT, "pyproject.toml"),
        _make_entry(repo_root, _KIND_CANONICAL_FACTS, CANONICAL_FACTS_RELPATH),
    ]

    artifact_manifest_rel = _artifact_manifest_relpath(repo_root, project_dir)
    if artifact_manifest_rel is not None:
        entries.append(_make_entry(repo_root, _KIND_ARTIFACT_MANIFEST, artifact_manifest_rel))

    for relpath in _declared_output_relpaths(project_dir):
        entries.append(_make_entry(repo_root, _KIND_OUTPUT_ARTIFACT, relpath))

    # Deduplicate by path (stable) then sort for a deterministic manifest.
    seen: dict[str, BundleEntry] = {}
    for entry in entries:
        seen.setdefault(entry.path, entry)
    return sorted(seen.values(), key=lambda e: e.path)


def build_manifest_dict(
    repo_root: Path,
    project_name: str,
    *,
    generated_at: str,
) -> dict[str, Any]:
    """Build the deterministic manifest mapping for *project_name*.

    Args:
        repo_root: Repository / checkout root.
        project_name: Exemplar project name.
        generated_at: Caller-supplied timestamp (never read from the clock, so
            the manifest stays byte-stable across runs).
    """
    entries = collect_entries(repo_root, project_name)
    return {
        "schema_version": SCHEMA_VERSION,
        "project": project_name,
        "generated_at": generated_at,
        "reproduce": _reproduce_commands(project_name),
        "entries": [entry.to_dict() for entry in entries],
    }


def _serialize(manifest: dict[str, Any]) -> str:
    """Byte-stable JSON: sorted keys, trailing newline."""
    return json.dumps(manifest, indent=2, sort_keys=True) + "\n"


def build_repro_bundle(
    repo_root: Path,
    project_name: str,
    *,
    out_dir: Path | None = None,
    generated_at: str = "1970-01-01T00:00:00+00:00",
) -> Path:
    """Build a repro bundle for *project_name* and write ``repro_manifest.json``.

    Args:
        repo_root: Repository / checkout root.
        project_name: Exemplar project name.
        out_dir: Output directory. Defaults to
            ``output/<project>/repro_bundle/`` under *repo_root*.
        generated_at: Caller-supplied timestamp parameter (default is the epoch
            so unattended builds remain byte-stable). Pass an explicit value to
            record provenance.

    Returns:
        The output directory containing ``repro_manifest.json``.
    """
    repo_root = repo_root.resolve()
    if out_dir is None:
        out_dir = repo_root / "output" / project_name / "repro_bundle"
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = build_manifest_dict(repo_root, project_name, generated_at=generated_at)
    (out_dir / BUNDLE_MANIFEST_NAME).write_text(_serialize(manifest), encoding="utf-8")
    logger.info("Wrote %s with %d entries", BUNDLE_MANIFEST_NAME, len(manifest["entries"]))
    return out_dir


def verify_repro_bundle(manifest_path: Path, *, checkout_root: Path) -> VerifyReport:
    """Verify a manifest against *checkout_root*, failing closed on any drift.

    Each manifest entry is recomputed; an entry is a mismatch when the file is
    missing or its SHA-256 differs from the recorded value. Entries recorded as
    absent at build time (``present=False``) must remain absent.

    Args:
        manifest_path: Path to a ``repro_manifest.json`` emitted by the builder.
        checkout_root: Root of the checkout to verify against.

    Returns:
        A :class:`VerifyReport` whose ``ok`` is ``True`` only when every entry
        matches.
    """
    checkout_root = checkout_root.resolve()
    raw: Any = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    entries = raw.get("entries", []) if isinstance(raw, dict) else []

    mismatches: list[dict[str, Any]] = []
    checked = 0
    for entry in entries:
        if not isinstance(entry, dict):
            mismatches.append({"path": "<malformed>", "reason": "malformed-entry"})
            continue
        path = str(entry.get("path", ""))
        expected = entry.get("sha256")
        expected_present = bool(entry.get("present", expected is not None))
        checked += 1

        actual, _size, present = _hash_relpath(checkout_root, path)

        if not expected_present:
            # Recorded as absent at build time; it must stay absent.
            if present:
                mismatches.append({"path": path, "reason": "unexpected-present"})
            continue
        if not present:
            mismatches.append({"path": path, "reason": "missing"})
            continue
        if actual != expected:
            mismatches.append(
                {
                    "path": path,
                    "reason": "hash-changed",
                    "expected": expected,
                    "actual": actual,
                }
            )

    return VerifyReport(ok=not mismatches, checked=checked, mismatches=mismatches)


def _build_argv(parser: argparse.ArgumentParser) -> None:
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="Build a repro bundle for an exemplar.")
    build.add_argument("project", help="Project name (or templates/<name>).")
    build.add_argument("--repo-root", default=".", help="Repository root (default: cwd).")
    build.add_argument("--out", default=None, help="Output directory for the bundle.")
    build.add_argument(
        "--generated-at",
        default="1970-01-01T00:00:00+00:00",
        help="Provenance timestamp baked into the manifest (not read from the clock).",
    )

    verify = sub.add_parser("verify", help="Verify a manifest against a checkout.")
    verify.add_argument("manifest", help="Path to repro_manifest.json.")
    verify.add_argument("--checkout-root", default=".", help="Checkout root to verify (default: cwd).")


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns ``0`` on success, ``1`` on verification failure."""
    parser = argparse.ArgumentParser(
        prog="python -m infrastructure.publishing.repro_bundle",
        description="Build and verify hermetic reproduction bundles for exemplars.",
    )
    _build_argv(parser)
    args = parser.parse_args(argv)

    if args.command == "build":
        out_dir = build_repro_bundle(
            Path(args.repo_root),
            args.project,
            out_dir=Path(args.out) if args.out else None,
            generated_at=args.generated_at,
        )
        manifest_path = out_dir / BUNDLE_MANIFEST_NAME
        logger.info("Repro bundle written to %s", manifest_path)
        print(str(manifest_path))
        return 0

    # verify
    report = verify_repro_bundle(Path(args.manifest), checkout_root=Path(args.checkout_root))
    print(_serialize(report.to_dict()), end="")
    if not report.ok:
        logger.error("Repro verification FAILED: %d mismatch(es)", len(report.mismatches))
        return 1
    logger.info("Repro verification OK: %d entries matched", report.checked)
    return 0


__all__ = [
    "BUNDLE_MANIFEST_NAME",
    "CANONICAL_FACTS_RELPATH",
    "SCHEMA_VERSION",
    "BundleEntry",
    "VerifyReport",
    "build_manifest_dict",
    "build_repro_bundle",
    "collect_entries",
    "main",
    "verify_repro_bundle",
]


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
