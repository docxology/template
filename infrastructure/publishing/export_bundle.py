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
import os
import secrets
import stat
import shutil
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO, Iterator
from infrastructure.core.project_paths import (
    resolve_source_manuscript_dir,
    validate_project_name,
)


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


@contextmanager
def _root_descriptor(root: Path, existing_fd: int | None = None) -> Iterator[int]:
    """Hold a directory reached without following symlinks in any component."""
    if existing_fd is not None:
        yield existing_fd
        return
    if not hasattr(os, "O_NOFOLLOW") or os.open not in os.supports_dir_fd:
        raise ValueError("confined export reads require no-follow directory descriptor support")
    absolute = root.absolute()
    if ".." in absolute.parts:
        raise ValueError(f"export root must not contain traversal: {root}")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    current = os.open(absolute.anchor, flags)
    try:
        for part in absolute.parts[1:]:
            child = os.open(part, flags, dir_fd=current)
            os.close(current)
            current = child
        yield current
    finally:
        os.close(current)


@contextmanager
def _source_reader(root: Path, source: Path, root_fd: int | None = None) -> Iterator[BinaryIO]:
    """Open a previously resolved artifact under a held root, refusing swaps."""
    relative = source.absolute().relative_to(root.absolute())
    if not relative.parts or ".." in relative.parts:
        raise ValueError(f"export source escapes selected root: {source}")
    with _root_descriptor(root, root_fd) as descriptor:
        current = os.dup(descriptor)
        try:
            for part in relative.parts[:-1]:
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=current)
                os.close(current)
                current = child
            flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
            source_fd = os.open(relative.name, flags, dir_fd=current)
            with os.fdopen(source_fd, "rb") as handle:
                if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                    raise ValueError(f"export source must be a regular file: {source}")
                yield handle
        finally:
            os.close(current)


def _collect_artifacts(output_root: Path, *, output_fd: int | None = None) -> dict[str, list[dict[str, Any]]]:
    """Collect nonempty PDF/ebook/metadata files contained in the output tree."""
    buckets: dict[str, tuple[str, tuple[str, ...]]] = {
        "pdf": ("pdf", (".pdf",)),
        "epub": ("ebook", (".epub", ".mobi")),
        "metadata": ("metadata", (".xml", ".json", ".opf")),
    }
    result: dict[str, list[dict[str, Any]]] = {}
    # Resolve before opening only for the standalone helper; production already
    # holds the selected output root across collection and copying.
    if output_fd is None:
        output_root = output_root.resolve()
    if not output_root.exists():
        return {key: [] for key in buckets}
    with _root_descriptor(output_root, output_fd) as descriptor:
        for key, (directory, extensions) in buckets.items():
            src_dir = _confined_path(output_root / directory, output_root)
            entries: list[dict[str, Any]] = []
            if src_dir.is_dir():
                for candidate in sorted(src_dir.iterdir()):
                    if not candidate.is_file() or candidate.suffix.lower() not in extensions:
                        continue
                    source = _confined_path(candidate, output_root)
                    with _source_reader(output_root, source, descriptor) as handle:
                        metadata = os.fstat(handle.fileno())
                        if metadata.st_size == 0:
                            continue
                        digest = hashlib.sha256()
                        for chunk in iter(lambda: handle.read(65536), b""):
                            digest.update(chunk)
                    entries.append(
                        {
                            "filename": candidate.name,
                            "source_path": str(source),
                            "sha256": digest.hexdigest(),
                            "size_bytes": metadata.st_size,
                        }
                    )
            result[key] = entries
    return result


def _read_config(manuscript_dir: Path, *, project_root: Path | None = None) -> dict[str, Any]:
    """Read manuscript/config.yaml and return a flat metadata dict.

    Returns an empty dict (with a warning) if the file is missing or unparseable.
    """
    config_path = manuscript_dir / "config.yaml"
    if not config_path.exists():
        print(f"WARNING: config.yaml not found at {config_path}", file=sys.stderr)
        return {}

    try:
        import yaml  # noqa: PLC0415

        root = project_root if project_root is not None else manuscript_dir.resolve()
        source = _confined_path(config_path, root)
        with _source_reader(root, source) as handle:
            raw: Any = yaml.safe_load(handle.read().decode("utf-8"))
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
    project = validate_project_name(project)
    projects_root = (repo_root / "projects").resolve()
    # Preserve this export API's established flat/templates/working/active order.
    candidates = [projects_root / project]
    if "/" not in project:
        candidates.extend(projects_root / prefix / project for prefix in ("templates", "working", "active"))
    for candidate in candidates:
        _confined_path(candidate.parent, projects_root)
        # Managed leaf project links intentionally resolve into a local sidecar.
        resolved = candidate.resolve() if candidate.is_symlink() else _confined_path(candidate, projects_root)
        if resolved.is_dir():
            return resolved

    raise FileNotFoundError(
        f"Project not found: {project!r}\n"
        f"  Searched under {repo_root / 'projects'}.\n"
        f"  Use a qualified name like 'templates/my_book' or 'working/draft'."
    )


def _confined_path(path: Path, root: Path) -> Path:
    """Resolve a path and refuse project, bucket, or file symlink escapes."""
    resolved = path.resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError(f"export path escapes selected root: {path}")
    return resolved


def _make_bundle_dir(output_dir: Path, project: str, timestamp: str) -> Path:
    """Allocate a fresh bundle; same-second exports never share artifacts."""
    safe_name = validate_project_name(project).replace("/", "_")
    bundle_name = f"{safe_name}-{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    for suffix in range(10000):
        name = bundle_name if suffix == 0 else f"{bundle_name}-{suffix}"
        bundle_dir = output_dir / name
        try:
            bundle_dir.mkdir()
        except FileExistsError:
            continue
        return bundle_dir
    raise FileExistsError(f"Unable to allocate a fresh export bundle for {project!r}")


def _copy_artifacts(
    artifacts: dict[str, list[dict[str, Any]]],
    bundle_dir: Path,
    *,
    output_root: Path,
    output_fd: int | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Copy through confined descriptors and describe the actual bundled bytes."""
    updated: dict[str, list[dict[str, Any]]] = {}
    with _root_descriptor(output_root, output_fd) as descriptor:
        for bucket, entries in artifacts.items():
            bucket_dir = bundle_dir / bucket
            if entries:
                bucket_dir.mkdir(parents=True, exist_ok=True)
            new_entries: list[dict[str, Any]] = []
            for entry in entries:
                source = Path(entry["source_path"])
                destination = bucket_dir / entry["filename"]
                with _source_reader(output_root, source, descriptor) as handle:
                    metadata = os.fstat(handle.fileno())
                    with destination.open("xb") as target:
                        shutil.copyfileobj(handle, target)
                        os.fchmod(target.fileno(), stat.S_IMODE(metadata.st_mode))
                os.utime(destination, ns=(metadata.st_atime_ns, metadata.st_mtime_ns))
                new_entries.append(
                    {
                        "filename": entry["filename"],
                        "path": str(destination.relative_to(bundle_dir)),
                        "sha256": _sha256(destination),
                        "size_bytes": destination.stat().st_size,
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
    temporary = output_dir / f".latest-{secrets.token_hex(12)}"
    try:
        target = bundle_dir.relative_to(output_dir)
    except ValueError:
        target = bundle_dir.resolve()
    temporary.symlink_to(target)
    try:
        temporary.replace(latest)
    finally:
        temporary.unlink(missing_ok=True)


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
    manuscript_dir = _confined_path(resolve_source_manuscript_dir(project_root), project_root)
    _confined_path(manuscript_dir / "config.yaml", project_root)
    metadata = _read_config(manuscript_dir, project_root=project_root)

    # Collect artifacts only from the selected project's contained output tree.
    output_root = _confined_path(project_root / "output", project_root)
    if not output_root.is_dir():
        print(f"ERROR: no artifacts found under {output_root}", file=sys.stderr)
        raise SystemExit(1)
    with _root_descriptor(output_root) as output_fd:
        artifacts = _collect_artifacts(output_root, output_fd=output_fd)

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
        bundle_artifacts = _copy_artifacts(artifacts, bundle_dir, output_root=output_root, output_fd=output_fd)

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
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except SystemExit as exc:
        return int(exc.code) if exc.code is not None else 1

    # Count artifacts for summary
    manifest_path = bundle_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
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
