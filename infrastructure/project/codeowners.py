"""Generate public-exemplar and sensitive-area CODEOWNERS rules."""

from __future__ import annotations

from pathlib import Path

import yaml

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

BEGIN = "# BEGIN GENERATED PUBLIC/SENSITIVE OWNERS"
END = "# END GENERATED PUBLIC/SENSITIVE OWNERS"


def render_generated_rules(repo_root: Path) -> str:
    """Render deterministic ownership rules from public scope and policy."""
    policy_path = repo_root / ".github/sensitive-ownership.yaml"
    payload = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    areas = payload.get("sensitive_areas") if isinstance(payload, dict) else None
    if not isinstance(areas, list):
        raise ValueError("sensitive-ownership.yaml must contain sensitive_areas")

    lines = [BEGIN, "# Public exemplars (derived from PUBLIC_PROJECT_NAMES)."]
    lines.extend(f"/projects/{name}/ @docxology" for name in PUBLIC_PROJECT_NAMES)
    lines.append("# Sensitive areas (derived from sensitive-ownership.yaml).")
    seen_paths: set[str] = set()
    for area in areas:
        if not isinstance(area, dict):
            raise ValueError("sensitive area entries must be mappings")
        path = area.get("path")
        owners = area.get("owners")
        exception = area.get("exception")
        if not isinstance(path, str) or not path.startswith("/"):
            raise ValueError("sensitive area paths must be absolute CODEOWNERS patterns")
        if path in seen_paths:
            raise ValueError(f"sensitive area paths must be unique: {path}")
        seen_paths.add(path)
        if (
            not isinstance(owners, list)
            or not owners
            or not all(isinstance(owner, str) and owner.startswith("@") for owner in owners)
        ):
            raise ValueError(f"sensitive area must declare owners: {path}")
        if len(set(owners)) != len(owners):
            raise ValueError(f"sensitive area owners must be unique: {path}")
        if exception not in (None, "") and not isinstance(exception, str):
            raise ValueError(f"sensitive area exception must be text or null: {path}")
        if len(owners) < 2 and not (isinstance(exception, str) and exception.strip()):
            raise ValueError(f"single-owner sensitive area must document a sole-owner exception: {path}")
        suffix = f"  # exception: {exception}" if exception else ""
        lines.append(f"{path} {' '.join(owners)}{suffix}")
    lines.append(END)
    return "\n".join(lines)


def codeowners_is_current(repo_root: Path) -> bool:
    """Return whether generated ownership policy is current and cannot be overridden.

    GitHub applies the last matching CODEOWNERS rule.  Merely finding a current
    generated block is therefore insufficient: a later hand-written rule could
    silently replace ownership for a public or sensitive path.  Keep the
    generated policy as the final rule-bearing block and permit only comments or
    blank lines after it.
    """
    path = repo_root / ".github/CODEOWNERS"
    text = path.read_text(encoding="utf-8")
    if text.count(BEGIN) != 1 or text.count(END) != 1:
        return False
    start = text.find(BEGIN)
    end = text.find(END)
    if start < 0 or end < start:
        return False
    actual = text[start : end + len(END)]
    trailing = text[end + len(END) :]
    has_trailing_rule = any(line.strip() and not line.lstrip().startswith("#") for line in trailing.splitlines())
    return actual == render_generated_rules(repo_root) and not has_trailing_rule


__all__ = ["codeowners_is_current", "render_generated_rules"]
