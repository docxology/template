"""Hermetic reproduction bundle builder and verifier (REPRO-BUNDLE-1).

A *repro bundle* captures everything a third party needs to confirm that a
public exemplar reproduces byte-for-byte: the lockfile, the project's artifact
manifest, content hashes of declared output artifacts, a hash pointer to
``docs/_generated/COUNTS.md``, and the exact pipeline command used to
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
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any

from infrastructure.core.files.operations import calculate_file_hash
from infrastructure.core.logging.utils import get_logger
from infrastructure.core.pipeline.artifacts import output_inventory_mode_for_project, validate_artifact_manifest
from infrastructure.core.project_paths import resolve_project_root, validate_project_name
from infrastructure.project.public_scope import public_project_names
from infrastructure.validation.output.artifacts import read_artifact_manifest

logger = get_logger(__name__)

SCHEMA_VERSION = "1.0"
BUNDLE_MANIFEST_NAME = "repro_manifest.json"
COUNTS_RELPATH = "docs/_generated/COUNTS.md"

# Reproduction-input file kinds, in the order they are collected.
_KIND_LOCKFILE = "lockfile"
_KIND_PYPROJECT = "pyproject"
_KIND_ARTIFACT_MANIFEST = "artifact-manifest"
_KIND_CANONICAL_FACTS = "canonical-facts"
_KIND_OUTPUT_ARTIFACT = "output-artifact"

_PROJECT_COMPONENT_RE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9._-]*")
_TIMESTAMP_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})")
_ENTRY_REQUIRED_FIELDS = frozenset({"kind", "path", "present", "sha256", "size_bytes"})


@dataclass(frozen=True)
class BundleEntry:
    """A single hashed reproduction input, relative to the checkout root."""

    kind: str
    path: str
    sha256: str | None
    size_bytes: int
    present: bool

    def to_dict(self) -> dict[str, Any]:
        """Serialize this object to a plain dict for JSON output."""
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
        """Serialize this object to a plain dict for JSON output."""
        return {
            "ok": self.ok,
            "checked": self.checked,
            "mismatches": self.mismatches,
        }


def _hash_relpath(checkout_root: Path, relpath: str) -> tuple[str | None, int, bool]:
    """Return ``(sha256, size_bytes, present)`` for *relpath* under *checkout_root*."""
    target = checkout_root / relpath
    try:
        resolved = target.resolve()
        resolved.relative_to(checkout_root.resolve())
    except (OSError, ValueError):
        return None, 0, False
    prefix = checkout_root
    for part in PurePosixPath(relpath).parts:
        prefix /= part
        if prefix.is_symlink():
            return None, 0, False
    if not target.is_file():
        return None, 0, False
    digest = calculate_file_hash(target)
    size = target.stat().st_size
    return digest, size, digest is not None


def _make_entry(checkout_root: Path, kind: str, relpath: str) -> BundleEntry:
    digest, size, present = _hash_relpath(checkout_root, relpath)
    return BundleEntry(kind=kind, path=relpath, sha256=digest, size_bytes=size, present=present)


def _validate_repro_project_name(project_name: str) -> str:
    """Return a canonical command-safe project name or raise ``ValueError``."""
    normalized = validate_project_name(project_name)
    if any(_PROJECT_COMPONENT_RE.fullmatch(part) is None for part in normalized.split("/")):
        raise ValueError(
            "project name components must start with a letter, digit, or underscore "
            "and contain only letters, digits, dots, underscores, or hyphens"
        )
    return normalized


def _valid_generated_at(value: object) -> bool:
    """Return whether *value* is a timezone-aware ISO-8601/RFC3339 timestamp."""
    if not isinstance(value, str) or _TIMESTAMP_RE.fullmatch(value) is None:
        return False
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _resolve_repro_project(repo_root: Path, project_name: str) -> tuple[str, Path]:
    """Resolve a reproduction project and confine it to the public checkout."""
    repo_root = repo_root.resolve()
    normalized = _validate_repro_project_name(project_name)
    candidate = resolve_project_root(repo_root, normalized)
    try:
        project_dir = candidate.resolve(strict=True)
    except OSError as exc:
        raise ValueError(f"reproduction project does not exist: {normalized!r}") from exc
    if not project_dir.is_dir():
        raise ValueError(f"reproduction project is not a directory: {normalized!r}")
    try:
        project_dir.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError(f"reproduction project must resolve inside the repository: {normalized!r}") from exc
    return normalized, project_dir


def _declared_output_relpaths(repo_root: Path, project_dir: Path) -> list[str]:
    """Read declared output artifact paths from the project artifact manifest.

    The artifact manifest lives at ``output/reports/artifact_manifest.json``. Its
    ``path`` values are stored **relative to the project directory** (see
    ``infrastructure.core.pipeline.artifacts`` — ``path.relative_to(project_dir)``),
    e.g. ``output/data/result.json``. Every other entry in the bundle resolves
    against ``repo_root``, so these are rebased onto the repo root here
    (``projects/templates/<name>/output/data/result.json``); without the rebase
    the resolver looked for ``<repo_root>/output/data/...`` and reported every
    artifact absent, so ``verify`` always failed. Malformed, stale, unsafe, or
    non-shippable manifests fail closed: a public reproduction bundle cannot
    silently omit outputs after consuming an invalid attestation.
    """
    manifest_path = project_dir / "output" / "reports" / "artifact_manifest.json"
    if not manifest_path.is_file():
        return []
    try:
        manifest = read_artifact_manifest(manifest_path)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid artifact manifest at {manifest_path}: {exc}") from exc
    validation = validate_artifact_manifest(
        manifest,
        project_dir=project_dir,
        expected_inventory_mode=output_inventory_mode_for_project(repo_root, project_dir),
    )
    if validation.issues:
        raise ValueError(f"invalid artifact manifest at {manifest_path}: " + "; ".join(validation.issues))
    repo_root = repo_root.resolve()
    paths: list[str] = []
    for entry in manifest.entries:
        path = entry.path
        try:
            repo_relative = (project_dir / path).resolve().relative_to(repo_root)
        except (OSError, ValueError) as exc:
            raise ValueError(f"artifact manifest path escapes the repository: {path!r}") from exc
        paths.append(repo_relative.as_posix())
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
        f"uv run python scripts/runner/execute_pipeline.py --project {project_name} --core-only",
    ]


def _collect_entries_for_project(repo_root: Path, project_dir: Path) -> list[BundleEntry]:
    """Collect entries for a validated, checkout-confined project directory."""
    entries: list[BundleEntry] = [
        _make_entry(repo_root, _KIND_LOCKFILE, "uv.lock"),
        _make_entry(repo_root, _KIND_PYPROJECT, "pyproject.toml"),
        _make_entry(repo_root, _KIND_CANONICAL_FACTS, COUNTS_RELPATH),
    ]

    artifact_manifest_rel = _artifact_manifest_relpath(repo_root, project_dir)
    if artifact_manifest_rel is None:
        raise ValueError(f"artifact manifest is required for a reproduction bundle: {project_dir}")
    artifact_manifest_entry = _make_entry(repo_root, _KIND_ARTIFACT_MANIFEST, artifact_manifest_rel)
    if not artifact_manifest_entry.present:
        raise ValueError(f"artifact manifest must be a present regular file inside the repository: {project_dir}")
    entries.append(artifact_manifest_entry)

    declared_outputs = _declared_output_relpaths(repo_root, project_dir)
    if not declared_outputs:
        raise ValueError(f"artifact manifest must declare at least one output artifact: {project_dir}")
    output_entries = [_make_entry(repo_root, _KIND_OUTPUT_ARTIFACT, relpath) for relpath in declared_outputs]
    absent_outputs = [entry.path for entry in output_entries if not entry.present]
    if absent_outputs:
        raise ValueError(
            "artifact manifest declares output artifacts that are not present regular files "
            f"inside the repository: {', '.join(absent_outputs)}"
        )
    entries.extend(output_entries)

    # Deduplicate by path (stable) then sort for a deterministic manifest.
    seen: dict[str, BundleEntry] = {}
    for entry in entries:
        seen.setdefault(entry.path, entry)
    return sorted(seen.values(), key=lambda e: e.path)


def collect_entries(repo_root: Path, project_name: str) -> list[BundleEntry]:
    """Collect and hash all reproduction inputs for *project_name*.

    Entries are returned sorted by ``path`` for deterministic manifests.
    """
    repo_root = repo_root.resolve()
    _normalized, project_dir = _resolve_repro_project(repo_root, project_name)
    return _collect_entries_for_project(repo_root, project_dir)


def _build_manifest_for_project(
    repo_root: Path,
    project_name: str,
    project_dir: Path,
    *,
    generated_at: str,
) -> dict[str, Any]:
    """Build a manifest after project validation and path confinement."""
    if not _valid_generated_at(generated_at):
        raise ValueError("generated_at must be a timezone-aware ISO-8601/RFC3339 timestamp")
    entries = _collect_entries_for_project(repo_root, project_dir)
    return {
        "schema_version": SCHEMA_VERSION,
        "project": project_name,
        "generated_at": generated_at,
        "reproduce": _reproduce_commands(project_name),
        "entries": [entry.to_dict() for entry in entries],
    }


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
    repo_root = repo_root.resolve()
    normalized, project_dir = _resolve_repro_project(repo_root, project_name)
    return _build_manifest_for_project(
        repo_root,
        normalized,
        project_dir,
        generated_at=generated_at,
    )


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
    normalized, project_dir = _resolve_repro_project(repo_root, project_name)
    manifest = _build_manifest_for_project(
        repo_root,
        normalized,
        project_dir,
        generated_at=generated_at,
    )
    if out_dir is None:
        out_dir = repo_root / "output" / normalized / "repro_bundle"
        try:
            out_dir.resolve(strict=False).relative_to(repo_root)
        except (OSError, ValueError) as exc:
            raise ValueError(f"default output directory escapes the repository: {out_dir}") from exc
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / BUNDLE_MANIFEST_NAME).write_text(_serialize(manifest), encoding="utf-8")
    logger.info("Wrote %s with %d entries", BUNDLE_MANIFEST_NAME, len(manifest["entries"]))
    return out_dir


def build_public_repro_bundles(
    repo_root: Path,
    *,
    out_dir: Path | None = None,
    generated_at: str = "1970-01-01T00:00:00+00:00",
) -> dict[str, Path]:
    """Build a repro bundle for every public template exemplar in this checkout.

    The roster is resolved via :func:`infrastructure.project.public_scope.public_project_names`,
    so it stays in lockstep with the CI/publication scope rather than a hard-coded
    list. Each exemplar gets its own manifest; nothing is merged, so every bundle
    remains independently verifiable.

    Args:
        repo_root: Repository / checkout root.
        out_dir: Parent directory for the per-exemplar bundles. When given, each
            bundle is written to ``<out_dir>/<project_name>/repro_bundle/``. When
            ``None``, each bundle falls back to its default
            ``output/<project>/repro_bundle/`` location under *repo_root*.
        generated_at: Provenance timestamp baked into every manifest.

    Returns:
        Mapping of exemplar project name -> output directory containing its
        ``repro_manifest.json``.
    """
    repo_root = repo_root.resolve()
    names = public_project_names(repo_root)
    results: dict[str, Path] = {}
    for name in names:
        target = (out_dir / name / "repro_bundle") if out_dir is not None else None
        results[name] = build_repro_bundle(
            repo_root,
            name,
            out_dir=target,
            generated_at=generated_at,
        )
    logger.info("Built %d public exemplar repro bundle(s)", len(results))
    return results


def verify_repro_bundle(manifest_path: Path, *, checkout_root: Path) -> VerifyReport:
    """Verify a manifest against *checkout_root*, failing closed on any drift."""
    # Lazy import: ``_repro_bundle_verify`` loads helpers from this module.
    from infrastructure.publishing._repro_bundle_verify import verify_repro_bundle as _verify

    return _verify(manifest_path, checkout_root=checkout_root)


def _build_argv(parser: argparse.ArgumentParser) -> None:
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="Build a repro bundle for an exemplar.")
    build.add_argument(
        "project",
        nargs="?",
        default=None,
        help="Project name (or templates/<name>). Omit when using --all-public.",
    )
    build.add_argument(
        "--all-public",
        action="store_true",
        help="Build a bundle for every public template exemplar (roster from public_scope).",
    )
    build.add_argument("--repo-root", default=".", help="Repository root (default: cwd).")
    build.add_argument(
        "--out",
        default=None,
        help="Output directory. With --all-public this is the parent for per-exemplar bundles.",
    )
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
        if args.all_public and args.project is not None:
            parser.error("pass a project name OR --all-public, not both")
        if args.all_public:
            results = build_public_repro_bundles(
                Path(args.repo_root),
                out_dir=Path(args.out) if args.out else None,
                generated_at=args.generated_at,
            )
            if not results:
                logger.error("No public exemplars discovered under %s", args.repo_root)
                return 1
            for name in sorted(results):
                manifest_path = results[name] / BUNDLE_MANIFEST_NAME
                logger.info("Repro bundle written to %s", manifest_path)
                print(str(manifest_path))
            return 0

        if not args.project:
            parser.error("build requires a project name unless --all-public is given")
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
    "COUNTS_RELPATH",
    "SCHEMA_VERSION",
    "BundleEntry",
    "VerifyReport",
    "build_manifest_dict",
    "build_public_repro_bundles",
    "build_repro_bundle",
    "collect_entries",
    "main",
    "verify_repro_bundle",
]


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
