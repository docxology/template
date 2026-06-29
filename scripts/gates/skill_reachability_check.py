#!/usr/bin/env python3
"""Skill-reachability gate — assert the agent front door reaches every skill.

Opt-in gate. NOT (yet) wired into the default ``./run.sh`` pipeline. It
enforces two reachability invariants so an agent that starts at the
documentation hub can always find every skill:

1. **Front-door links.** ``docs/AGENTS.md`` must contain a *resolving*
   Markdown link (the link target, resolved relative to ``docs/``, points at
   a file that exists on disk) to each of the THREE skill-discovery
   entrypoints:
       - ``docs/_generated/skills_index.md`` (the generated skill catalog)
       - ``docs/prompts/SKILL.md`` (the prompts hub)
       - ``docs/prompts/COMPOSITION.md`` (the composition guide)

2. **Index completeness.** Every ``SKILL.md`` discoverable under the default
   discovery roots (``infrastructure/``, ``projects/``, ``docs/prompts/``,
   ``.cursor/skills/``) must appear as a row in
   ``docs/_generated/skills_index.md`` — keyed on its POSIX path so the
   generated catalog can never silently fall behind a newly added skill.

The gate prints one actionable ``FAIL`` line per problem and exits ``1`` when
any invariant is unmet, ``0`` otherwise.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.skills import (  # noqa: E402
    DEFAULT_SKILL_SEARCH_ROOTS,
    discover_skills,
)

# The three discovery entrypoints AGENTS.md must reach, expressed as paths
# relative to the repository root.
ENTRYPOINTS: tuple[str, ...] = (
    "docs/_generated/skills_index.md",
    "docs/prompts/SKILL.md",
    "docs/prompts/COMPOSITION.md",
)

# Markdown inline link: [text](target). Capture the target only.
_MD_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def _resolved_link_targets(agents_md: Path, docs_dir: Path) -> set[Path]:
    """Return the set of resolved, on-disk targets linked from ``agents_md``.

    Each Markdown link target is resolved relative to ``docs/`` (the directory
    that holds ``AGENTS.md``); only targets whose resolved path exists are
    returned, so a dangling link never counts as reaching an entrypoint.
    """
    targets: set[Path] = set()
    text = agents_md.read_text(encoding="utf-8")
    for raw in _MD_LINK.findall(text):
        # Strip any in-page anchor or title suffix from the link target.
        target = raw.split("#", 1)[0].split(" ", 1)[0].strip()
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        resolved = (docs_dir / target).resolve()
        if resolved.exists():
            targets.add(resolved)
    return targets


def _check_front_door(repo_root: Path) -> list[str]:
    """Verify ``docs/AGENTS.md`` links to all three entrypoints. Return failures."""
    failures: list[str] = []
    docs_dir = repo_root / "docs"
    agents_md = docs_dir / "AGENTS.md"
    if not agents_md.is_file():
        failures.append(f"FAIL front-door: missing {agents_md.relative_to(repo_root)}")
        return failures

    linked = _resolved_link_targets(agents_md, docs_dir)
    for entrypoint in ENTRYPOINTS:
        target = (repo_root / entrypoint).resolve()
        if not target.exists():
            failures.append(f"FAIL front-door: entrypoint {entrypoint} does not exist on disk")
            continue
        if target not in linked:
            failures.append(f"FAIL front-door: docs/AGENTS.md has no resolving link to {entrypoint}")
    return failures


def _check_index_completeness(repo_root: Path) -> list[str]:
    """Verify every discovered SKILL.md appears in the skills index. Return failures."""
    failures: list[str] = []
    index_path = repo_root / "docs" / "_generated" / "skills_index.md"
    if not index_path.is_file():
        failures.append(
            "FAIL index: missing docs/_generated/skills_index.md "
            "(regenerate with `uv run python -m infrastructure.skills write` "
            "or the skills-index generator)"
        )
        return failures

    index_text = index_path.read_text(encoding="utf-8")
    skills = discover_skills(repo_root, search_roots=DEFAULT_SKILL_SEARCH_ROOTS)
    for skill in skills:
        if skill.path_posix not in index_text:
            failures.append(
                f"FAIL index: skill {skill.path_posix} discovered under "
                f"{', '.join(DEFAULT_SKILL_SEARCH_ROOTS)} but absent from "
                "docs/_generated/skills_index.md"
            )
    return failures


def main(argv: list[str] | None = None) -> int:
    """Run the skill-reachability gate against a repository root."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root (defaults to the template repo root).",
    )
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()

    failures: list[str] = []
    failures.extend(_check_front_door(repo_root))
    failures.extend(_check_index_completeness(repo_root))

    if failures:
        for line in failures:
            print(line)
        print(f"\nFAIL skill-reachability gate: {len(failures)} issue(s).")
        return 1

    print("OK skill-reachability gate: front-door links + index complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
