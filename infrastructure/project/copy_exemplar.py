"""Clean-copy public template exemplars into a fork workspace."""

from __future__ import annotations

import argparse
import fnmatch
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


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


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for exemplar fork copies."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Qualified source, e.g. templates/template_code_project")
    parser.add_argument("--dest", required=True, type=Path, help="Destination directory for the clean fork copy")
    parser.add_argument("--new-name", help="Optional project slug to substitute for the exemplar directory name")
    parser.add_argument("--dry-run", action="store_true", help="Print the planned files without writing")
    parser.add_argument("--repo-root", default=Path.cwd(), type=Path, help="Repository root. Defaults to cwd.")
    args = parser.parse_args(argv)

    result = plan_copy(args.repo_root, args.source, args.dest, new_name=args.new_name, dry_run=args.dry_run)
    action = "Would copy" if result.dry_run else "Copied"
    print(f"{action} {len(result.relative_files)} files from {result.source} to {result.destination}")
    for rel in result.relative_files:
        print(rel.as_posix())
    return 0


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
    return tuple(sorted(path for path in files if _is_clean_source_path(path)))


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
        raise ValueError(f"refusing to dereference symlink in exemplar copy: {source}")
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


__all__ = ["CopyResult", "copy_exemplar", "main", "plan_copy"]
