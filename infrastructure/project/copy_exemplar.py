"""Clean-copy public template exemplars into a fork workspace."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - Python 3.10
    import tomli as tomllib


_IGNORED_NAMES = frozenset(
    {
        ".DS_Store",
        ".cache",
        ".lake",
        ".mypy_cache",
        ".nox",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "htmlcov",
        "lake-packages",
        "output",
        "rendered",
        "venv",
    }
)
_IGNORED_PATTERNS = ("*.egg-info", "*.pyc", "*.pyo")
_PROJECT_SLUG_RE = re.compile(r"^[a-z][a-z0-9_-]*$")


@dataclass(frozen=True)
class CopyResult:
    """Summary of an exemplar copy operation."""

    source: Path
    destination: Path
    relative_files: tuple[Path, ...]
    dry_run: bool = False


@dataclass(frozen=True)
class ExportManifest:
    """Content-addressed provenance for one standalone exemplar export."""

    source_project: str
    exported_project: str
    source_commit: str
    infrastructure_version: str
    files: dict[str, str]
    resource_dependencies: tuple[str, ...] = ()
    schema_version: int = 2

    def to_json(self) -> str:
        """Return stable, human-readable JSON with a trailing newline."""
        payload = {
            "schema_version": self.schema_version,
            "source_project": self.source_project,
            "exported_project": self.exported_project,
            "source_commit": self.source_commit,
            "infrastructure_version": self.infrastructure_version,
            "resource_dependencies": list(self.resource_dependencies),
            "files": dict(sorted(self.files.items())),
        }
        return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def plan_copy(
    repo_root: Path | str,
    source: str,
    dest: Path | str,
    *,
    new_name: str | None = None,
    dry_run: bool = False,
) -> CopyResult:
    """Return the clean-copy plan and optionally create the destination tree."""
    root = Path(repo_root).resolve()
    destination = Path(dest).expanduser().resolve()
    source_root = _resolve_source(root, source)
    if new_name is not None:
        _validate_new_name(new_name)
    files = _source_files(root, source_root)
    if not files:
        raise ValueError(f"no source files found under {source_root}")

    if dry_run:
        return CopyResult(source=source_root, destination=destination, relative_files=files, dry_run=True)

    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError(f"destination exists and is not empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    old_name = source_root.name
    old_project_path = source_root.relative_to(root).as_posix()
    try:
        new_project_path = destination.relative_to(root).as_posix()
    except ValueError:
        new_project_path = new_name or old_name
    for rel in files:
        target_rel = _renamed_path(rel, old_name, new_name)
        target = _contained_destination(destination, target_rel)
        _copy_one(
            source_root / rel,
            target,
            old_name=old_name,
            new_name=new_name,
            old_project_path=old_project_path,
            new_project_path=new_project_path,
        )
    return CopyResult(source=source_root, destination=destination, relative_files=files, dry_run=False)


def copy_exemplar(
    repo_root: Path | str,
    source: str,
    dest: Path | str,
    *,
    new_name: str | None = None,
) -> CopyResult:
    """Clean-copy a public exemplar to ``dest``."""
    return plan_copy(repo_root, source, dest, new_name=new_name, dry_run=False)


def export_exemplar(
    repo_root: Path | str,
    source: str,
    dest: Path | str,
    *,
    new_name: str | None = None,
    project_only: bool = False,
) -> CopyResult:
    """Clean-copy an exemplar and write a deterministic provenance manifest."""
    root = Path(repo_root).resolve()
    result = copy_exemplar(root, source, dest, new_name=new_name)
    dependencies = () if project_only else _declared_resource_dependencies(result.source)
    for dependency in dependencies:
        _copy_resource_dependency(root, dependency, result.destination)
    manifest = _build_export_manifest(
        root,
        result.destination,
        source_project=source,
        exported_project=new_name or result.destination.name,
        resource_dependencies=dependencies,
    )
    (result.destination / ".template-export.json").write_text(manifest.to_json(), encoding="utf-8")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for exemplar fork copies."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Qualified source, e.g. templates/template_code_project")
    parser.add_argument("--dest", required=True, type=Path, help="Destination directory for the clean fork copy")
    parser.add_argument("--new-name", help="Optional project slug to substitute for the exemplar directory name")
    parser.add_argument("--dry-run", action="store_true", help="Print the planned files without writing")
    parser.add_argument(
        "--project-only",
        action="store_true",
        help="Exclude declared cross-root resources from a standalone export.",
    )
    parser.add_argument("--repo-root", default=Path.cwd(), type=Path, help="Repository root. Defaults to cwd.")
    args = parser.parse_args(argv)

    if args.dry_run:
        result = plan_copy(args.repo_root, args.source, args.dest, new_name=args.new_name, dry_run=True)
    else:
        result = export_exemplar(
            args.repo_root,
            args.source,
            args.dest,
            new_name=args.new_name,
            project_only=args.project_only,
        )
    action = "Would copy" if result.dry_run else "Copied"
    print(f"{action} {len(result.relative_files)} files from {result.source} to {result.destination}")
    for rel in result.relative_files:
        print(rel.as_posix())
    return 0


def _build_export_manifest(
    repo_root: Path,
    destination: Path,
    *,
    source_project: str,
    exported_project: str,
    resource_dependencies: tuple[str, ...] = (),
) -> ExportManifest:
    hashes: dict[str, str] = {}
    for path in sorted(candidate for candidate in destination.rglob("*") if candidate.is_file()):
        rel = path.relative_to(destination).as_posix()
        if rel == ".template-export.json":
            continue
        hashes[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return ExportManifest(
        source_project=source_project,
        exported_project=exported_project,
        source_commit=_git_head(repo_root),
        infrastructure_version=_infrastructure_version(repo_root),
        files=hashes,
        resource_dependencies=resource_dependencies,
    )


def _declared_resource_dependencies(source_root: Path) -> tuple[str, ...]:
    """Read validated cross-root resource declarations from ``export.toml``."""
    config_path = source_root / "export.toml"
    if not config_path.is_file():
        return ()
    payload = tomllib.loads(config_path.read_text(encoding="utf-8"))
    config = payload.get("template_export", {})
    if not isinstance(config, dict):
        raise ValueError(f"[template_export] must be a table: {config_path}")
    raw = config.get("cross_root_dependencies", [])
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise ValueError("template_export.cross_root_dependencies must be a list of strings")
    dependencies = tuple(raw)
    allowed = {"fonds/templates", "rules/templates", "tools/templates", "infrastructure"}
    invalid = sorted(set(dependencies) - allowed)
    if invalid:
        raise ValueError(f"unsupported cross-root resource dependencies: {', '.join(invalid)}")
    if len(dependencies) != len(set(dependencies)):
        raise ValueError("cross-root resource dependencies must be unique")
    return dependencies


def _copy_resource_dependency(repo_root: Path, dependency: str, destination: Path) -> None:
    """Bundle one declared public resource tree under ``_template_resources``."""
    source_root = (repo_root / dependency).resolve()
    if not source_root.is_dir():
        raise FileNotFoundError(f"declared resource dependency does not exist: {dependency}")
    target_root = destination / "_template_resources" / dependency
    files = _git_source_files(repo_root, source_root) or _walk_source_files(source_root)
    for rel in sorted(path for path in files if _is_clean_resource_path(path, dependency)):
        _copy_one(
            source_root / rel,
            _contained_destination(target_root, rel),
            old_name=source_root.name,
            new_name=None,
            old_project_path=dependency,
            new_project_path=dependency,
        )


def _is_clean_resource_path(path: Path, dependency: str) -> bool:
    """Apply artifact exclusions without hiding Layer-1 ``output`` source."""
    for part in path.parts:
        if part in _IGNORED_NAMES and not (dependency == "infrastructure" and part == "output"):
            return False
        if any(fnmatch.fnmatch(part, pattern) for pattern in _IGNORED_PATTERNS):
            return False
    return True


def _git_head(repo_root: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return proc.stdout.strip() or "unknown"


def _infrastructure_version(repo_root: Path) -> str:
    pyproject = repo_root / "pyproject.toml"
    if not pyproject.is_file():
        return "unknown"
    try:
        payload = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError):
        return "unknown"
    project = payload.get("project")
    if not isinstance(project, dict):
        return "unknown"
    version = project.get("version")
    return str(version) if version else "unknown"


def _resolve_source(repo_root: Path, source: str) -> Path:
    source_path = Path(source)
    if source_path.is_absolute() or source_path.parts[:1] != ("templates",):
        raise ValueError("source must be qualified as templates/<name>")
    if len(source_path.parts) != 2:
        raise ValueError("source must be qualified as templates/<name>")
    root = (repo_root / "projects" / source_path).resolve()
    expected_parent = (repo_root / "projects" / "templates").resolve()
    if root.parent != expected_parent:
        raise ValueError("source must resolve under projects/templates")
    if not root.is_dir():
        raise FileNotFoundError(f"source exemplar does not exist: {root}")
    return root


def _source_files(repo_root: Path, source_root: Path) -> tuple[Path, ...]:
    git_files = _git_source_files(repo_root, source_root)
    files = git_files or _walk_source_files(source_root)
    clean = tuple(path for path in files if _is_clean_source_path(path))
    return _expand_public_symlinks(repo_root, source_root, clean)


def _resolve_public_symlink(repo_root: Path, source: Path) -> Path:
    """Resolve a symlink only when its target belongs to a public exemplar.

    Public exemplars may share implementation snapshots with one another while
    the exported tree must remain standalone. Targets outside the declared
    public roster remain a hard error so clean-copy can never dereference a
    private sidecar or arbitrary host path.
    """
    try:
        target = source.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError(f"refusing to dereference invalid symlink in exemplar copy: {source}") from exc

    for project_name in PUBLIC_PROJECT_NAMES:
        public_root = (repo_root / "projects" / project_name).resolve()
        if target == public_root or target.is_relative_to(public_root):
            return target
    raise ValueError(f"refusing to dereference symlink outside public exemplars: {source}")


def _expand_public_symlinks(repo_root: Path, source_root: Path, files: tuple[Path, ...]) -> tuple[Path, ...]:
    """Expand tracked public directory symlinks into standalone file paths."""
    expanded: set[Path] = set()

    def visit(relative: Path, source: Path, ancestors: frozenset[Path]) -> None:
        if not source.is_symlink():
            expanded.add(relative)
            return
        target = _resolve_public_symlink(repo_root, source)
        if target.is_file():
            expanded.add(relative)
            return
        if not target.is_dir():
            raise ValueError(f"refusing to dereference non-file symlink in exemplar copy: {source}")
        if target in ancestors:
            raise ValueError(f"refusing cyclic public-exemplar symlink: {source}")
        children = _git_source_files(repo_root, target) or _walk_source_files(target)
        for child in children:
            combined = relative / child
            if _is_clean_source_path(combined):
                visit(combined, target / child, ancestors | {target})

    for relative in files:
        visit(relative, source_root / relative, frozenset())
    return tuple(sorted(expanded))


def _git_source_files(repo_root: Path, source_root: Path) -> tuple[Path, ...]:
    try:
        source_rel = source_root.relative_to(repo_root)
    except ValueError:
        return ()
    try:
        proc = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "--", source_rel.as_posix()],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return ()

    rels: list[Path] = []
    for line in proc.stdout.splitlines():
        if not line:
            continue
        path = repo_root / line
        if path.is_file() or path.is_symlink():
            rels.append(path.relative_to(source_root))
    return tuple(rels)


def _walk_source_files(source_root: Path) -> tuple[Path, ...]:
    files: list[Path] = []
    for path in source_root.rglob("*"):
        rel = path.relative_to(source_root)
        if path.is_dir():
            continue
        if _is_clean_source_path(rel):
            files.append(rel)
    return tuple(files)


def _is_clean_source_path(path: Path) -> bool:
    for part in path.parts:
        if part in _IGNORED_NAMES:
            return False
        if any(fnmatch.fnmatch(part, pattern) for pattern in _IGNORED_PATTERNS):
            return False
    return True


def _copy_one(
    source: Path,
    dest: Path,
    *,
    old_name: str,
    new_name: str | None,
    old_project_path: str,
    new_project_path: str,
) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if source.is_symlink():
        repo_root = _find_repo_root(source)
        source = _resolve_public_symlink(repo_root, source)
        if not source.is_file():
            raise ValueError(f"refusing to copy unresolved directory symlink: {source}")
    data = source.read_bytes()
    if new_name:
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            dest.write_bytes(data)
            return
        dest.write_text(
            _rename_text(
                text,
                old_name,
                new_name,
                old_project_path=old_project_path,
                new_project_path=new_project_path,
            ),
            encoding="utf-8",
        )
        shutil.copystat(source, dest)
        return
    dest.write_bytes(data)
    shutil.copystat(source, dest)


def _find_repo_root(source: Path) -> Path:
    """Return the ancestor containing the public project registry surface."""
    for parent in (source, *source.parents):
        if (parent / "infrastructure" / "project" / "public_scope.py").is_file():
            return parent
    raise ValueError(f"refusing to dereference symlink outside a template checkout: {source}")


def _renamed_path(path: Path, old_name: str, new_name: str | None) -> Path:
    if not new_name:
        return path
    return Path(*(_rename_text(part, old_name, new_name) for part in path.parts))


def _rename_text(
    text: str,
    old_name: str,
    new_name: str,
    *,
    old_project_path: str | None = None,
    new_project_path: str | None = None,
) -> str:
    """Replace project slug spellings without touching unrelated tokens."""
    old_hyphen = old_name.replace("_", "-")
    new_hyphen = new_name.replace("_", "-")
    if old_project_path and new_project_path:
        text = text.replace(old_project_path, new_project_path)
        renamed_old_path = old_project_path.replace(old_name, new_name)
        if renamed_old_path != old_project_path:
            text = text.replace(renamed_old_path, new_project_path)
    for old_token, new_token in (
        (f"projects/templates/{old_name}", f"projects/templates/{new_name}"),
        (f"projects/working/{old_name}", f"projects/working/{new_name}"),
        (f"projects/active/{old_name}", f"projects/active/{new_name}"),
        (f"templates/{old_name}", f"templates/{new_name}"),
        (f"working/{old_name}", f"working/{new_name}"),
        (f"active/{old_name}", f"active/{new_name}"),
    ):
        text = text.replace(old_token, new_token)
    text = _replace_keyed_slug(text, old_name, new_name)
    text = _replace_keyed_slug(text, old_hyphen, new_hyphen)
    text = re.sub(rf"\b{re.escape(old_name)}\b", new_name, text)
    text = re.sub(rf"\b{re.escape(old_hyphen)}\b", new_hyphen, text)
    return text


def _replace_keyed_slug(text: str, old_slug: str, new_slug: str) -> str:
    """Replace slug spellings only on known configuration keys and import paths."""
    if old_slug == new_slug:
        return text
    patterns = (
        rf"(?P<prefix>name\s*=\s*['\"]){re.escape(old_slug)}(?P<suffix>['\"])",
        rf"(?P<prefix>project\s*=\s*['\"]){re.escape(old_slug)}(?P<suffix>['\"])",
        rf"(?P<prefix>--project\s+){re.escape(old_slug)}(?P<suffix>\b)",
        rf"(?P<prefix>from\s+projects\.templates\.{re.escape(old_slug)}\.)",
        rf"(?P<prefix>import\s+projects\.templates\.{re.escape(old_slug)}\.)",
        rf"(?P<prefix>projects/templates/{re.escape(old_slug)}/)",
        rf"(?P<prefix>projects/working/{re.escape(old_slug)}/)",
        rf"(?P<prefix>projects/active/{re.escape(old_slug)}/)",
    )
    for pattern in patterns:
        if pattern.endswith("/)"):
            text = re.sub(pattern, lambda m: m.group("prefix").replace(old_slug, new_slug), text)
        elif "from" in pattern or "import" in pattern:
            text = re.sub(pattern, lambda m: m.group("prefix").replace(old_slug, new_slug), text)
        else:
            text = re.sub(pattern, rf"\g<prefix>{new_slug}\g<suffix>", text)
    return text


def _validate_new_name(new_name: str) -> None:
    if not _PROJECT_SLUG_RE.fullmatch(new_name):
        raise ValueError("--new-name must be a lowercase project slug using letters, numbers, '_' or '-'")


def _contained_destination(destination: Path, target_rel: Path) -> Path:
    target = (destination / target_rel).resolve()
    try:
        target.relative_to(destination)
    except ValueError as exc:
        raise ValueError(f"copy target would escape destination: {target_rel}") from exc
    return target


__all__ = ["CopyResult", "ExportManifest", "copy_exemplar", "export_exemplar", "main", "plan_copy"]
