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
    for area in areas:
        if not isinstance(area, dict):
            raise ValueError("sensitive area entries must be mappings")
        path = area.get("path")
        owners = area.get("owners")
        exception = area.get("exception")
        if not isinstance(path, str) or not path.startswith("/"):
            raise ValueError("sensitive area paths must be absolute CODEOWNERS patterns")
        if (
            not isinstance(owners, list)
            or not owners
            or not all(isinstance(owner, str) and owner.startswith("@") for owner in owners)
        ):
            raise ValueError(f"sensitive area must declare owners: {path}")
        if exception not in (None, "") and not isinstance(exception, str):
            raise ValueError(f"sensitive area exception must be text or null: {path}")
        suffix = f"  # exception: {exception}" if exception else ""
        lines.append(f"{path} {' '.join(owners)}{suffix}")
    lines.append(END)
    return "\n".join(lines)


def codeowners_is_current(repo_root: Path) -> bool:
    """Return whether the generated CODEOWNERS block matches policy."""
    path = repo_root / ".github/CODEOWNERS"
    text = path.read_text(encoding="utf-8")
    start = text.find(BEGIN)
    end = text.find(END)
    if start < 0 or end < start:
        return False
    actual = text[start : end + len(END)]
    return actual == render_generated_rules(repo_root)


__all__ = ["codeowners_is_current", "render_generated_rules"]
