"""Contract checks for template workflow ``SKILL.md`` frontmatter."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from infrastructure.skills.discovery import split_yaml_frontmatter
from infrastructure.validation.docs.scan_scope import DEFAULT_EXCLUDE_PARTS, should_exclude_path

__all__ = [
    "ALLOWED_DATA_ACCESS_LEVELS",
    "ALLOWED_STATUSES",
    "ALLOWED_TASK_TYPES",
    "check_skill_contracts",
    "iter_contract_skill_paths",
    "validate_skill_contract_file",
]

ALLOWED_STATUSES = frozenset({"active", "experimental", "deprecated"})
ALLOWED_DATA_ACCESS_LEVELS = frozenset({"raw", "redacted", "verified_only"})
ALLOWED_TASK_TYPES = frozenset({"open-ended", "outcome-gradable"})

_REQUIRED_METADATA_FIELDS = (
    "version",
    "last_updated",
    "status",
    "data_access_level",
    "task_type",
    "modes",
    "related_skills",
)


def iter_contract_skill_paths(repo_root: Path | str) -> Iterable[Path]:
    """Yield workflow skill files whose metadata contract is enforced."""
    root = Path(repo_root).resolve()
    base = root / "docs" / "prompts"
    if not base.is_dir():
        return
    for path in sorted(base.rglob("SKILL.md")):
        rel = path.relative_to(root)
        if should_exclude_path(rel, DEFAULT_EXCLUDE_PARTS):
            continue
        yield path


def validate_skill_contract_file(skill_path: Path | str) -> list[str]:
    """Return contract issues for one workflow ``SKILL.md`` file."""
    path = Path(skill_path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"{path}: cannot read file: {exc}"]
    frontmatter, _body = split_yaml_frontmatter(text)
    if frontmatter is None:
        return [f"{path}: missing YAML frontmatter"]
    issues: list[str] = []
    _validate_required_string(frontmatter, "name", issues, path)
    _validate_required_string(frontmatter, "description", issues, path)
    metadata = frontmatter.get("metadata")
    if not isinstance(metadata, dict):
        issues.append(f"{path}: metadata must be a mapping")
        metadata = {}
    for field in _REQUIRED_METADATA_FIELDS:
        if field not in metadata:
            issues.append(f"{path}: metadata.{field} is missing")
    _validate_required_string(metadata, "version", issues, path, prefix="metadata.")
    _validate_required_string(metadata, "last_updated", issues, path, prefix="metadata.")
    _validate_enum(metadata, "status", ALLOWED_STATUSES, issues, path)
    _validate_enum(metadata, "data_access_level", ALLOWED_DATA_ACCESS_LEVELS, issues, path)
    _validate_enum(metadata, "task_type", ALLOWED_TASK_TYPES, issues, path)
    _validate_string_list(metadata, "modes", issues, path, allow_empty=False)
    _validate_string_list(metadata, "related_skills", issues, path, allow_empty=True)
    return issues


def check_skill_contracts(repo_root: Path | str) -> list[str]:
    """Return all docs/prompts skill contract issues for a repository."""
    root = Path(repo_root).resolve()
    issues: list[str] = []
    for skill_path in iter_contract_skill_paths(root):
        rel_path = skill_path.relative_to(root)
        for issue in validate_skill_contract_file(skill_path):
            issues.append(issue.replace(str(skill_path), rel_path.as_posix(), 1))
    return issues


def _validate_required_string(
    mapping: dict[str, Any],
    field: str,
    issues: list[str],
    path: Path,
    *,
    prefix: str = "",
) -> None:
    value = mapping.get(field)
    if not isinstance(value, str) or not value.strip():
        issues.append(f"{path}: {prefix}{field} must be a non-empty string")


def _validate_enum(
    metadata: dict[str, Any],
    field: str,
    allowed: frozenset[str],
    issues: list[str],
    path: Path,
) -> None:
    value = metadata.get(field)
    if value not in allowed:
        issues.append(f"{path}: metadata.{field} must be one of {sorted(allowed)}")


def _validate_string_list(
    metadata: dict[str, Any],
    field: str,
    issues: list[str],
    path: Path,
    *,
    allow_empty: bool,
) -> None:
    value = metadata.get(field)
    if not isinstance(value, list) or (not allow_empty and not value):
        requirement = "a list" if allow_empty else "a non-empty list"
        issues.append(f"{path}: metadata.{field} must be {requirement}")
        return
    for item in value:
        if not isinstance(item, str) or not item.strip():
            issues.append(f"{path}: metadata.{field} entries must be non-empty strings")
            return
