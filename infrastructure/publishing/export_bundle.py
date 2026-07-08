#!/usr/bin/env python3
"""Formal handoff from template/ to the docxology/publishing repo.

Bundles all generated artifacts from a project's output/ directory into a
timestamped import package that the publishing repo can consume.

USAGE (from the template/ repo root)::

    uv run python scripts/publish/export_for_publishing.py --project templates/my_book
    uv run python scripts/publish/export_for_publishing.py \\
        --project templates/my_book \\
        --output-dir ~/Documents/GitHub/publishing/workspace/imports/

Artifacts collected per project:
    - output/pdf/          → *.pdf
    - output/ebook/        → *.epub, *.mobi  (Stage 10 EPUB renderer output)
    - output/metadata/     → *.xml, *.json   (Stage 11 metadata package output)

A ``manifest.json`` is written into the bundle directory and a ``latest``
symlink at the output root points to the most-recent export.

Exit codes:
    0  success — bundle written, path printed to stdout
    1  project root not found or no artifacts collected
    2  config.yaml missing or unreadable
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# --- repo root ----------------------------------------------------------------

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

# --- defaults -----------------------------------------------------------------

DEFAULT_OUTPUT_DIR = Path.home() / "Documents" / "GitHub" / "publishing" / "workspace" / "imports"

# --- helpers ------------------------------------------------------------------


def _sha256(path: Path) -> str:
    """Return the hex SHA-256 digest of *path*."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _collect_artifacts(output_root: Path) -> dict[str, list[dict[str, Any]]]:
    """Scan output/ sub-directories and return a structured artifact map.

    Returns a dict with keys ``pdf``, ``epub``, and ``metadata``, each
    containing a list of ``{filename, source_path, sha256, size_bytes}`` dicts.
    Only existing, non-empty files are included.
    """
    buckets: dict[str, tuple[str, tuple[str, ...]]] = {
        "pdf": ("pdf", (".pdf",)),
        "epub": ("ebook", (".epub", ".mobi")),
        "metadata": ("metadata", (".xml", ".json", ".opf")),
    }
    result: dict[str, list[dict[str, Any]]] = {}

    for key, (directory, extensions) in buckets.items():
        src_dir = output_root / directory
        entries: list[dict[str, Any]] = []
        if src_dir.is_dir():
            for f in sorted(src_dir.iterdir()):
                if f.is_file() and f.suffix.lower() in extensions and f.stat().st_size > 0:
                    entries.append(
                        {
                            "filename": f.name,
                            "source_path": str(f),
                            "sha256": _sha256(f),
                            "size_bytes": f.stat().st_size,
                        }
                    )
        result[key] = entries

    return result


def _read_config(manuscript_dir: Path) -> dict[str, Any]:
    """Read manuscript/config.yaml and return a flat metadata dict.

    Returns an empty dict (with a warning) if the file is missing or unparseable.
    """
    config_path = manuscript_dir / "config.yaml"
    if not config_path.exists():
        print(f"WARNING: config.yaml not found at {config_path}", file=sys.stderr)
        return {}

    try:
        import yaml  # noqa: PLC0415

        raw: Any = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            print(f"WARNING: config.yaml did not parse to a dict: {config_path}", file=sys.stderr)
            return {}
        # Extract the fields relevant to publishing
        pub: dict[str, Any] = {}
        for key in (
            "title",
            "author",
            "authors",
            "isbn",
            "isbn13",
            "doi",
            "license",
            "publisher",
            "publication_date",
            "keywords",
            "abstract",
            "language",
            "version",
            "github_repo",
        ):
            if key in raw:
                pub[key] = raw[key]
        # publication sub-dict is common in template configs
        if "publication" in raw and isinstance(raw["publication"], dict):
            for k, v in raw["publication"].items():
                pub.setdefault(k, v)
        return pub
    except Exception as exc:  # noqa: BLE001
        print(f"WARNING: failed to parse config.yaml: {exc}", file=sys.stderr)
        return {}


def _resolve_project_root(project: str, repo_root: Path) -> Path:
    """Resolve a qualified project name like ``templates/my_book`` to a Path.

    Also accepts bare project names (no slash) and tries common prefixes.
    """
    # Qualified: templates/name, working/name, active/name, etc.
    candidate = repo_root / "projects" / project
    if candidate.is_dir():
        return candidate

    # Bare name — try common lifecycle prefixes
    for prefix in ("templates", "working", "active", "published"):
        candidate = repo_root / "projects" / prefix / project
        if candidate.is_dir():
            return candidate

    raise FileNotFoundError(
        f"Project not found: {project!r}\n"
        f"  Searched under {repo_root / 'projects'}.\n"
        f"  Use a qualified name like 'templates/my_book' or 'working/draft'."
    )


def _make_bundle_dir(output_dir: Path, project: str, timestamp: str) -> Path:
    """Create and return the timestamped bundle directory."""
    # Flatten project name: templates/my_book → templates_my_book
    safe_name = project.replace("/", "_").replace("\\", "_")
    bundle_name = f"{safe_name}-{timestamp}"
    bundle_dir = output_dir / bundle_name
    bundle_dir.mkdir(parents=True, exist_ok=True)
    return bundle_dir


def _copy_artifacts(artifacts: dict[str, list[dict[str, Any]]], bundle_dir: Path) -> dict[str, list[dict[str, Any]]]:
    """Copy artifacts into bundle_dir and return updated entries with bundle-relative paths."""
    updated: dict[str, list[dict[str, Any]]] = {}
    for bucket, entries in artifacts.items():
        bucket_dir = bundle_dir / bucket
        if entries:
            bucket_dir.mkdir(parents=True, exist_ok=True)
        new_entries: list[dict[str, Any]] = []
        for entry in entries:
            src = Path(entry["source_path"])
            dst = bucket_dir / entry["filename"]
            shutil.copy2(src, dst)
            new_entries.append(
                {
                    "filename": entry["filename"],
                    "path": str(dst.relative_to(bundle_dir)),
                    "sha256": entry["sha256"],
                    "size_bytes": entry["size_bytes"],
                }
            )
        updated[bucket] = new_entries
    return updated


def _write_manifest(
    bundle_dir: Path,
    project: str,
    source_root: Path,
    metadata: dict[str, Any],
    artifacts: dict[str, list[dict[str, Any]]],
    timestamp: str,
) -> Path:
    """Write manifest.json into bundle_dir and return its path."""
    manifest: dict[str, Any] = {
        "schema_version": "1.0",
        "exported_at": timestamp,
        "project": project,
        "source_root": str(source_root),
        "metadata": metadata,
        "artifacts": artifacts,
    }
    manifest_path = bundle_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


def _update_latest_symlink(output_dir: Path, bundle_dir: Path) -> None:
    """Point output_dir/latest to bundle_dir (creates or replaces the symlink)."""
    latest = output_dir / "latest"
    # Remove old symlink or stale file
    if latest.is_symlink() or latest.exists():
        latest.unlink()
    # Use a relative target so the symlink works when the directory is moved
    try:
        rel = bundle_dir.relative_to(output_dir)
        latest.symlink_to(rel)
    except ValueError:
        # Fall back to absolute path when bundle_dir is not under output_dir
        latest.symlink_to(bundle_dir)


# --- main ---------------------------------------------------------------------


def export_for_publishing(
    project: str,
    output_dir: Path | None = None,
    repo_root: Path | None = None,
) -> Path:
    """Bundle a project's output artifacts for import by the publishing repo.

    Parameters
    ----------
    project:
        Qualified project name, e.g. ``'templates/my_book'`` or ``'working/draft'``.
    output_dir:
        Root directory under which the timestamped bundle is created.
        Defaults to ``~/Documents/GitHub/publishing/workspace/imports/``.
    repo_root:
        Path to the template/ repository root.  Defaults to the repo root
        inferred from this script's location.

    Returns
    -------
    Path
        The bundle directory that was created.

    Raises
    ------
    FileNotFoundError
        If the project root cannot be resolved.
    SystemExit(1)
        If no artifacts were found in output/.
    """
    repo_root = repo_root or REPO
    output_dir = output_dir or DEFAULT_OUTPUT_DIR

    # Resolve project root
    project_root = _resolve_project_root(project, repo_root)

    # Gather metadata from manuscript/config.yaml
    metadata = _read_config(project_root / "manuscript")

    # Collect artifacts from output/
    output_root = project_root / "output"
    artifacts = _collect_artifacts(output_root)

    total_count = sum(len(v) for v in artifacts.values())
    if total_count == 0:
        print(
            f"ERROR: no artifacts found under {output_root}\n"
            f"  Run the pipeline first: ./run.sh --project {project} --pipeline --core-only",
            file=sys.stderr,
        )
        raise SystemExit(1)

    # Create timestamped bundle
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir.mkdir(parents=True, exist_ok=True)
    bundle_dir = _make_bundle_dir(output_dir, project, timestamp)

    # Copy artifacts into bundle
    bundle_artifacts = _copy_artifacts(artifacts, bundle_dir)

    # Write manifest
    _write_manifest(
        bundle_dir=bundle_dir,
        project=project,
        source_root=project_root,
        metadata=metadata,
        artifacts=bundle_artifacts,
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )

    # Update latest symlink
    _update_latest_symlink(output_dir, bundle_dir)

    return bundle_dir


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--project",
        required=True,
        help="Qualified project name (e.g. 'templates/my_book' or 'working/draft').",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=(f"Root directory for the export bundle. Defaults to {DEFAULT_OUTPUT_DIR}."),
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Override the template/ repo root (useful for testing).",
    )
    args = parser.parse_args(argv)

    try:
        bundle_dir = export_for_publishing(
            project=args.project,
            output_dir=args.output_dir,
            repo_root=args.repo_root,
        )
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except SystemExit as exc:
        return int(exc.code) if exc.code is not None else 1

    # Count artifacts for summary
    manifest_path = bundle_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    counts = {k: len(v) for k, v in manifest["artifacts"].items()}
    total = sum(counts.values())

    print(f"\n✅ Exported {total} artifact(s) to: {bundle_dir}")
    for bucket, count in counts.items():
        if count:
            print(f"   {bucket:12} {count} file(s)")
    print(f"\n   manifest: {manifest_path}")
    print(f"   latest  : {bundle_dir.parent / 'latest'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
