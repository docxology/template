"""Token extraction for fallback grader matching."""

from __future__ import annotations

import re


def tokens(phrase: str) -> list[str]:
    phrase = re.sub(r"[^\w\s/.-]", " ", phrase)
    parts = [p.strip() for p in phrase.split() if len(p.strip()) > 2]
    joined = " ".join(parts)
    out = list(parts)
    if "execute_pipeline" in joined:
        out.append("execute_pipeline")
    if "active_projects" in joined:
        out.append("active_projects")
    if "--resume" in phrase:
        out.append("--resume")
    if "--core-only" in phrase:
        out.append("--core-only")
    return out
