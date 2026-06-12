"""Synthetic skill-guided and baseline response builders."""

from __future__ import annotations

from pathlib import Path

from skill_eval.config import CAPTURE_HEADINGS, HUB_ROUTE_CHILD, REPO


def extract_sections(body: str, *, headings: frozenset[str] | set[str]) -> list[str]:
    sections: list[str] = []
    capture = False
    for line in body.splitlines():
        if line.startswith("## "):
            heading = line[3:].strip()
            capture = heading in headings
        if capture:
            sections.append(line)
    return sections


def skill_response(skill_path: Path, prompt: str, eval_name: str, *, include_header: bool = True) -> str:
    skill = skill_path.read_text(encoding="utf-8")
    body = skill.split("---", 2)[-1] if skill.startswith("---") else skill
    sections: list[str] = []
    if include_header:
        sections.extend(
            [
                f"# Response: {eval_name}\n",
                f"**User prompt:** {prompt}\n",
                "Following the template workflow skill:\n",
            ]
        )
    sections.extend(extract_sections(body, headings=CAPTURE_HEADINGS))
    ref_dir = skill_path.parent / "references"
    if ref_dir.is_dir():
        for ref_file in sorted(ref_dir.glob("*.md")):
            sections.append(f"\n## Included reference: {ref_file.name}\n")
            sections.append(ref_file.read_text(encoding="utf-8"))
    joined = "\n".join(sections).lower()
    if "COUNTS" not in joined and "do not invent coverage" not in joined:
        sections.append(
            "\nMetrics policy: do not invent coverage percentages; cite pytest output or "
            "`docs/_generated/COUNTS.md`.\n"
        )
    if "active_projects" not in joined:
        sections.append(
            "Project roster: `docs/_generated/active_projects.md` (no hard-coded rotating paths).\n"
        )
    return "\n".join(sections)


def hub_routed_response(eval_id: int, prompt: str, eval_name: str) -> str:
    hub_path = REPO / "docs/prompts/SKILL.md"
    child_rel = HUB_ROUTE_CHILD[eval_id]
    child_path = REPO / child_rel
    hub_body = hub_path.read_text(encoding="utf-8").split("---", 2)[-1]
    parts: list[str] = [
        f"# Response: {eval_name}\n",
        f"**User prompt:** {prompt}\n",
        "Intent is ambiguous — clarifying pipeline vs prose, then loading one child skill.\n",
    ]
    ambiguous = extract_sections(hub_body, headings={"Ambiguous routing"})
    if ambiguous:
        parts.extend(ambiguous)
    else:
        parts.append(
            "## Ambiguous routing\n\n"
            "- Broken refs / manuscript issues → cross-refs, validation-quality, or "
            "claim-verification — not code-development.\n"
        )
    parts.append(
        "\n**Clarifying question:** Is the failure in source markdown/registry tokens, "
        "or in a pipeline validate/render stage?\n"
    )
    parts.append(f"\n**Selected child skill:** `{child_rel}`\n")
    parts.append(skill_response(child_path, prompt, eval_name, include_header=False))
    return "\n".join(parts)


def out_of_scope_response(prompt: str, eval_name: str) -> str:
    return (
        f"# Response: {eval_name}\n\n"
        f"**User prompt:** {prompt}\n\n"
        "This request is outside the repository workflow skills. "
        "Answering directly without loading docs/prompts skills."
    )


def baseline_response(prompt: str, eval_name: str) -> str:
    return (
        f"# Response: {eval_name}\n\n"
        f"**User prompt:** {prompt}\n\n"
        "I'll help with that. You should check your logs, fix any errors, "
        "and re-run your build. Make sure tests pass and documentation looks good."
    )


def with_skill_response(eval_id: int, skill_path: Path, prompt: str, eval_name: str) -> str:
    if eval_id in HUB_ROUTE_CHILD:
        return hub_routed_response(eval_id, prompt, eval_name)
    return skill_response(skill_path, prompt, eval_name)
