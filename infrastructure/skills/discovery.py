"""Discover and parse agent-oriented SKILL.md descriptors in the repository."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, Sequence

import yaml

# Roots (relative to repository root) searched recursively for **/SKILL.md
DEFAULT_SKILL_SEARCH_ROOTS: tuple[str, ...] = ("infrastructure",)

_MANIFEST_VERSION = 1


@dataclass(frozen=True, slots=True)
class SkillDescriptor:
    """One discovered skill file with parsed YAML frontmatter."""

    absolute_path: Path
    relative_path: Path
    name: str | None
    description: str | None
    frontmatter: dict[str, Any] = field(default_factory=dict)

    @property
    def path_posix(self) -> str:
        """Path relative to repo root, POSIX-style (for JSON and @-references)."""
        return self.relative_path.as_posix()

    @property
    def cursor_at(self) -> str:
        """Suggested Cursor context reference (same as path_posix)."""
        return self.path_posix


def split_yaml_frontmatter(source: str) -> tuple[dict[str, Any] | None, str]:
    """Split leading YAML frontmatter from markdown body.

    Expects optional opening ``---``, YAML block, closing ``---``, then body.
    Returns ``(parsed_dict_or_none, body)``.
    """
    if not source.startswith("---"):
        return None, source
    parts = source.split("---", 2)
    if len(parts) < 3:
        return None, source
    yaml_blob = parts[1].strip()
    body = parts[2]
    if not yaml_blob:
        return None, body
    loaded = yaml.safe_load(yaml_blob)
    if loaded is None:
        return {}, body
    if not isinstance(loaded, dict):
        return None, body
    return loaded, body


def load_skill_descriptor(skill_path: Path, repo_root: Path) -> SkillDescriptor:
    """Read a SKILL.md file and return a :class:`SkillDescriptor`."""
    resolved_skill = skill_path.resolve()
    resolved_root = repo_root.resolve()
    text = resolved_skill.read_text(encoding="utf-8")
    fm, _body = split_yaml_frontmatter(text)
    rel = resolved_skill.relative_to(resolved_root)
    name = fm.get("name") if fm else None
    desc = fm.get("description") if fm else None
    if name is not None and not isinstance(name, str):
        name = str(name)
    if desc is not None and not isinstance(desc, str):
        desc = str(desc)
    return SkillDescriptor(
        absolute_path=resolved_skill,
        relative_path=rel,
        name=name,
        description=desc,
        frontmatter=dict(fm) if fm else {},
    )


def iter_skill_paths(repo_root: Path, roots: Sequence[str]) -> Iterator[Path]:
    """Yield absolute paths to ``SKILL.md`` under each root relative to ``repo_root``."""
    root_resolved = repo_root.resolve()
    for rel in roots:
        base = (root_resolved / rel).resolve()
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("SKILL.md")):
            if p.is_file():
                yield p


def _ensure_unique_names(skills: Sequence[SkillDescriptor]) -> None:
    seen: dict[str, str] = {}
    for s in skills:
        if not s.name:
            continue
        prev = seen.get(s.name)
        if prev is not None:
            msg = f"Duplicate skill name {s.name!r}: {prev} and {s.path_posix}"
            raise ValueError(msg)
        seen[s.name] = s.path_posix


def discover_skills(
    repo_root: Path | str,
    *,
    search_roots: Sequence[str] | None = None,
) -> list[SkillDescriptor]:
    """Discover all ``SKILL.md`` files under configured roots and parse frontmatter.

    Args:
        repo_root: Repository root directory.
        search_roots: Relative directory names to scan (default: :data:`DEFAULT_SKILL_SEARCH_ROOTS`).

    Returns:
        Descriptors sorted by POSIX relative path.

    Raises:
        ValueError: If two skills declare the same ``name`` in frontmatter.
    """
    root = Path(repo_root).resolve()
    roots = tuple(search_roots) if search_roots is not None else DEFAULT_SKILL_SEARCH_ROOTS
    found: list[SkillDescriptor] = []
    for path in iter_skill_paths(root, roots):
        found.append(load_skill_descriptor(path, root))
    found.sort(key=lambda s: s.path_posix)
    _ensure_unique_names(found)
    return found


def build_manifest_payload(skills: Sequence[SkillDescriptor]) -> dict[str, Any]:
    """Build the canonical JSON-serializable manifest structure."""
    return {
        "version": _MANIFEST_VERSION,
        "skills": [
            {
                "name": s.name,
                "description": s.description,
                "path": s.path_posix,
                "cursor_at": s.cursor_at,
            }
            for s in skills
        ],
    }


def write_skill_manifest(
    repo_root: Path | str,
    output_path: Path | str | None = None,
    *,
    search_roots: Sequence[str] | None = None,
) -> Path:
    """Write skill manifest JSON for editors and agents.

    Default output: ``<repo_root>/.cursor/skill_manifest.json``.

    Returns:
        Path to the written file.
    """
    root = Path(repo_root).resolve()
    if output_path is None:
        out = root / ".cursor" / "skill_manifest.json"
    else:
        out = Path(output_path)
        if not out.is_absolute():
            out = (root / out).resolve()
        else:
            out = out.resolve()
    skills = discover_skills(root, search_roots=search_roots)
    payload = build_manifest_payload(skills)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def load_manifest(manifest_path: Path | str) -> dict[str, Any]:
    """Load a manifest JSON file."""
    path = Path(manifest_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("manifest root must be a JSON object")
    return data


def manifest_matches_discovery(
    repo_root: Path | str,
    manifest_path: Path | str,
    *,
    search_roots: Sequence[str] | None = None,
) -> tuple[bool, str]:
    """Return whether the manifest matches current :func:`discover_skills` output."""
    root = Path(repo_root).resolve()
    mpath = Path(manifest_path).resolve()
    live = discover_skills(root, search_roots=search_roots)
    expected = build_manifest_payload(live)
    try:
        on_disk = load_manifest(mpath)
    except FileNotFoundError:
        return False, f"manifest missing: {mpath}"
    except (json.JSONDecodeError, OSError, ValueError) as e:
        return False, f"manifest unreadable: {e}"
    if on_disk.get("version") != expected["version"]:
        return False, "manifest version mismatch"
    if on_disk.get("skills") != expected["skills"]:
        return False, "manifest skills list out of date (run: uv run python -m infrastructure.skills write)"
    return True, "ok"


def manifest_skill_dicts_for_prompt(skills: Sequence[SkillDescriptor]) -> list[dict[str, str]]:
    """Compact rows suitable for logging or prompt injection."""
    return [
        {
            "name": s.name or "",
            "path": s.path_posix,
            "description": (s.description or "")[:500],
        }
        for s in skills
    ]


def skill_descriptors_as_json_serializable(
    skills: Sequence[SkillDescriptor],
) -> list[dict[str, Any]]:
    """Convert descriptors to plain dicts (paths as strings) for JSON APIs."""
    return [
        {
            "path": s.path_posix,
            "name": s.name,
            "description": s.description,
            "frontmatter": s.frontmatter,
        }
        for s in skills
    ]


__all__ = [
    "DEFAULT_SKILL_SEARCH_ROOTS",
    "SkillDescriptor",
    "build_manifest_payload",
    "discover_skills",
    "iter_skill_paths",
    "load_manifest",
    "load_skill_descriptor",
    "manifest_matches_discovery",
    "manifest_skill_dicts_for_prompt",
    "skill_descriptors_as_json_serializable",
    "split_yaml_frontmatter",
    "write_skill_manifest",
]
