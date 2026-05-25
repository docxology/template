"""Registered expectation heuristics for skill eval grading."""

from __future__ import annotations

from collections.abc import Callable

from skill_eval.grader.stages import (
    mentions_any_pipeline_stage,
    mentions_output_validation,
    mentions_project_analysis,
)
from skill_eval.grader.tokens import tokens

RuleFn = Callable[[str, str], bool]


def _recommends_code_development_primary(lower: str) -> bool:
    primary_markers = (
        "following the template-code-development",
        "open code-development",
        "use code-development",
        "start with code-development",
        "load code-development",
    )
    if any(m in lower for m in primary_markers):
        return True
    lines = [ln.strip() for ln in lower.splitlines() if ln.strip()]
    for line in lines[:12]:
        if line.startswith("following") and "code-development" in line:
            return True
        if line.startswith("## workflow") and "code-development" in line:
            return True
    return False


def check_negative_expectation(lower: str, el: str) -> bool:
    if "does not require 90% template coverage gates" in el:
        return not any(
            phrase in lower
            for phrase in (
                "90%",
                "cov-fail-under",
                "coverage gate",
                "coverage gates",
                "cov-fail",
            )
        )
    if "does not mention" in el or "does not require" in el:
        forbidden = el.split("does not mention", 1)[-1].split("does not require", 1)[-1].strip()
        found = any(t in lower for t in tokens(forbidden) if len(t) > 4)
        return not found
    return True


def _rule(substrings: tuple[str, ...], fn: RuleFn) -> tuple[tuple[str, ...], RuleFn]:
    return (substrings, fn)


def _match_any(substrings: tuple[str, ...], el: str) -> bool:
    return any(s in el for s in substrings)


RULES: list[tuple[tuple[str, ...], RuleFn]] = [
    _rule(
        ("multiple distinct verification passes",),
        lambda lower, _el: (("pass 1" in lower and "pass 2" in lower) or "three-pass" in lower or "pass 3" in lower),
    ),
    _rule(
        ("hand-edit output",),
        lambda lower, _el: "hand-edit" in lower and "output" in lower,
    ),
    _rule(
        ("hard-coded theorem",),
        lambda lower, _el: "hard-coded" in lower and any(w in lower for w in ("number", "theorem", "section")),
    ),
    _rule(
        ("does not prescribe raw latex", "raw latex \\ref"),
        lambda lower, _el: (
            ("never" in lower and ("\\ref" in lower or "ref{}" in lower or "raw" in lower))
            or ("not" in lower and "\\ref" in lower)
            or ("pandoc-crossref" in lower and ("registry" in lower or "token" in lower))
        ),
    ),
    _rule(
        ("validate stage or validation cli",),
        mentions_output_validation,
    ),
    _rule(
        ("first real error not last line",),
        lambda lower, _el: "first" in lower and "real error" in lower and "last line" in lower,
    ),
    _rule(
        ("includes manuscript validation approach",),
        lambda lower, _el: "manuscript" in lower
        and any(w in lower for w in ("validation", "markdown", "prerender", "validate")),
    ),
    _rule(
        ("does not jump straight to unrelated code development",),
        lambda lower, _el: not _recommends_code_development_primary(lower),
    ),
    _rule(
        ("per-paper structured", "contribution/method/evidence"),
        lambda lower, _el: "contribution" in lower and "method" in lower and "evidence" in lower,
    ),
    _rule(
        ("thematic clusters",),
        lambda lower, _el: "thematic" in lower or "cluster" in lower,
    ),
    _rule(
        ("square-bracket citation", "citekey"),
        lambda lower, _el: "citation key" in lower or "citekey" in lower or "[{" in lower,
    ),
    _rule(
        ("temperature 0", "seed for replay"),
        lambda lower, _el: "seed=42" in lower or "temperature=0" in lower or "seed" in lower,
    ),
    _rule(
        ("research question framing",),
        lambda lower, _el: "question framing" in lower or ("research question" in lower and "scope" in lower),
    ),
    _rule(
        ("source verification",),
        lambda lower, _el: "source verification" in lower or ("doi" in lower and "metadata" in lower),
    ),
    _rule(
        ("literature-synthesis", "citekey synthesis"),
        lambda lower, _el: "literature-synthesis" in lower or ("citekey" in lower and "synthesis" in lower),
    ),
    _rule(
        ("generated variables", "material gaps"),
        lambda lower, _el: "generated variables" in lower or "material gap" in lower,
    ),
    _rule(
        ("prerender markdown citation validation",),
        lambda lower, _el: "prerender" in lower and "markdown" in lower and "citation" in lower,
    ),
    _rule(
        ("source-layer manuscript edits",),
        lambda lower, _el: "source-layer" in lower and "manuscript" in lower,
    ),
    _rule(
        ("claim verification",),
        lambda lower, _el: "claim verification" in lower or "manuscript-claim-verification" in lower,
    ),
    _rule(
        ("read-only review boundary",),
        lambda lower, _el: "read-only" in lower and "review" in lower,
    ),
    _rule(
        ("methodology-focus", "re-review"),
        lambda lower, _el: "methodology-focus" in lower or "re-review" in lower,
    ),
    _rule(
        ("traceability matrix",),
        lambda lower, _el: "traceability matrix" in lower,
    ),
    _rule(
        ("does not edit manuscript directly",),
        lambda lower, _el: (
            ("does not edit" in lower or "do not modify" in lower or "not modify" in lower) and "manuscript" in lower
        )
        or ("read-only" in lower and "route edits" in lower),
    ),
    _rule(
        ("stage map research to paper",),
        lambda lower, _el: "stage map" in lower and "research" in lower and "paper" in lower,
    ),
    _rule(
        ("material passport",),
        lambda lower, _el: "material passport" in lower,
    ),
    _rule(
        ("hitl", "human checkpoints"),
        lambda lower, _el: "hitl" in lower or "human checkpoint" in lower,
    ),
    _rule(
        ("evidence registry artifact manifests snapshots",),
        lambda lower, _el: "evidence registry" in lower and "artifact manifest" in lower and "snapshot" in lower,
    ),
    _rule(
        ("academic workflow choices",),
        lambda lower, _el: "academic" in lower
        and any(token in lower for token in ("research", "paper", "review", "pipeline")),
    ),
    _rule(
        ("deep-research", "academic-paper", "reviewer"),
        lambda lower, _el: any(token in lower for token in ("deep-research", "academic-paper", "reviewer")),
    ),
    _rule(
        ("academic-pipeline",),
        lambda lower, _el: "academic-pipeline" in lower,
    ),
    _rule(
        ("methods orchestration plan",),
        lambda lower, _el: "methods orchestration" in lower and "plan" in lower,
    ),
    _rule(
        ("infrastructure.methods plan",),
        lambda lower, _el: "infrastructure.methods" in lower and "plan" in lower,
    ),
    _rule(
        ("artifact manifest and evidence registry",),
        lambda lower, _el: "artifact manifest" in lower and "evidence registry" in lower,
    ),
    _rule(
        ("generated output as fix",),
        lambda lower, _el: ("do not edit" in lower or "generated output is evidence" in lower)
        and ("output/" in lower or "generated output" in lower),
    ),
    _rule(
        ("does not invent coverage",),
        lambda lower, _el: "canonical_facts" in lower or "do not invent coverage" in lower,
    ),
    _rule(
        ("names a pipeline stage",),
        mentions_any_pipeline_stage,
    ),
    _rule(
        ("project analysis stage or analysis script",),
        mentions_project_analysis,
    ),
    _rule(
        ("move logic to src",),
        lambda lower, _el: "move logic" in lower and "src" in lower,
    ),
    _rule(
        ("logic in src not scripts",),
        lambda lower, _el: ("src/" in lower or ("logic in" in lower and "src" in lower))
        and ("thin orchestrator" in lower or ("script" in lower and ("orchestrat" in lower or "coordinates" in lower))),
    ),
    _rule(
        ("thin orchestrator",),
        lambda lower, _el: "thin" in lower and "orchestrat" in lower,
    ),
    _rule(
        ("pytest baseline",),
        lambda lower, _el: "pytest" in lower and ("baseline" in lower or "run tests" in lower),
    ),
    _rule(
        ("scope creep", "no new feature"),
        lambda lower, _el: "preserve" in lower or "behavior" in lower or "breaking" in lower,
    ),
    _rule(
        ("places code in projects",),
        lambda lower, _el: "projects" in lower and "src" in lower,
    ),
    _rule(
        ("places code under infrastructure/",),
        lambda lower, _el: "infrastructure/" in lower
        and any(w in lower for w in ("package", "layout", "module", "under")),
    ),
    _rule(
        ("type hints and get_logger",),
        lambda lower, _el: "type hint" in lower and "get_logger" in lower,
    ),
    _rule(
        ("90% coverage", "project test command"),
        lambda lower, _el: ("90" in lower and "cov" in lower) or "01_run_tests" in lower,
    ),
    _rule(
        ("structured issue reporting",),
        lambda lower, _el: "diagnostic" in lower or "path" in lower or "report" in lower,
    ),
    _rule(
        ("does not suggest hand-editing",),
        lambda lower, _el: "manuscript" in lower or "markdown" in lower or "source" in lower,
    ),
    _rule(
        ("read live code", "not invent apis"),
        lambda lower, _el: ("read" in lower or "live" in lower)
        and ("invent" in lower or "ground" in lower or "signature" in lower),
    ),
    _rule(
        ("includes verification commands",),
        lambda lower, _el: "verification commands" in lower or "```bash" in lower,
    ),
    _rule(
        ("explicitly rejects",),
        lambda lower, _el: "mock" in lower and ("no mock" in lower or "forbid" in lower or "never" in lower),
    ),
    _rule(
        ("distinguishes",),
        lambda lower, _el: "agents.md" in lower and "readme" in lower,
    ),
    _rule(
        ("asks clarifying", "picks manuscript"),
        lambda lower, _el: "manuscript" in lower or "cross-ref" in lower or "validation" in lower or "claim" in lower,
    ),
]


def check_positive_expectation(lower: str, el: str, original: str) -> bool:
    for substrings, fn in RULES:
        if _match_any(substrings, el):
            return fn(lower, original)
    if "mentions" in el or "references" in el or "uses" in el or "covers" in el:
        return any(t in lower for t in tokens(el) if len(t) > 3)
    return el[:40] in lower
