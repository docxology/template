"""Canonical markdown path resolution for validation modules."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

PathType = Literal["file", "directory", "unknown"]


@dataclass(frozen=True)
class ResolvedPath:
    """Result of resolving a markdown link or file reference."""

    exists: bool
    message: str
    path_type: PathType
    resolved: Path | None = None


def _is_external_target(target: str) -> bool:
    if target.startswith(("http://", "https://", "mailto:", "ftp://")):
        return True
    parsed = urlparse(target)
    return bool(parsed.scheme and parsed.scheme not in {"", "file"})


def _strip_anchor(target: str) -> str:
    if "#" in target:
        return target.split("#", 1)[0]
    return target


def _resolve_relative_path(target: str, source_file: Path) -> Path:
    if target.startswith("../"):
        target_path = source_file.parent
        for _ in range(target.count("../")):
            target_path = target_path.parent
        remainder = target
        while remainder.startswith("../"):
            remainder = remainder[3:]
        if remainder.startswith("./"):
            remainder = remainder[2:]
        return target_path / remainder
    if target.startswith("./"):
        return source_file.parent / target[2:]
    return source_file.parent / target


def resolve_markdown_target(
    target: str,
    source_file: Path,
    repo_root: Path,
    *,
    infer_md_suffix: bool = True,
) -> ResolvedPath:
    """Resolve a markdown link target relative to *source_file* within *repo_root*."""
    if not target or target.startswith("#"):
        return ResolvedPath(True, str(source_file), "file", source_file.resolve())

    if _is_external_target(target):
        return ResolvedPath(True, "external URL", "unknown", None)

    file_part = _strip_anchor(target)
    if not file_part:
        return ResolvedPath(True, str(source_file), "file", source_file.resolve())

    is_directory_ref = file_part.endswith("/")

    try:
        repo_root_resolved = repo_root.resolve()
        if file_part.startswith(("/", "\\")) or Path(file_part).is_absolute():
            target_path = Path(file_part).expanduser().resolve()
        elif file_part.startswith(("./", "../")):
            target_path = _resolve_relative_path(file_part, source_file).resolve()
        else:
            source_candidate = (source_file.parent / file_part).resolve()
            root_candidate = (repo_root / file_part).resolve()
            if source_candidate.exists():
                target_path = source_candidate
            elif root_candidate.exists():
                target_path = root_candidate
            else:
                target_path = source_candidate

        target_path.relative_to(repo_root_resolved)
    except ValueError as exc:
        if "outside repository" in str(exc) or "embedded null" in str(exc):
            return ResolvedPath(False, f"Error resolving path: {exc}", "unknown", None)
        return ResolvedPath(False, f"Path outside repository: {target_path}", "unknown", target_path)
    except (OSError, RuntimeError) as exc:
        return ResolvedPath(False, f"Error resolving path: {exc}", "unknown", None)

    if target_path.exists():
        if target_path.is_file():
            rel = str(target_path.relative_to(repo_root_resolved))
            return ResolvedPath(True, rel, "file", target_path)
        if target_path.is_dir():
            rel = str(target_path.relative_to(repo_root_resolved))
            return ResolvedPath(True, rel, "directory", target_path)
        return ResolvedPath(
            False,
            f"Path exists but is not a file or directory: {target_path}",
            "unknown",
            target_path,
        )

    if infer_md_suffix and not is_directory_ref:
        md_path = target_path.with_suffix(".md")
        if md_path.exists() and md_path.is_file():
            rel = str(md_path.relative_to(repo_root_resolved))
            return ResolvedPath(True, rel, "file", md_path)

    if is_directory_ref:
        return ResolvedPath(False, f"Directory does not exist: {target_path}", "directory", target_path)
    return ResolvedPath(False, f"File or directory does not exist: {target_path}", "file", target_path)
