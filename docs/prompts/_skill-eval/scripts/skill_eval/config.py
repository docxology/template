"""Paths and eval configuration."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
EVAL_ROOT = REPO / "docs/prompts/_skill-eval"
EVAL_JSON = EVAL_ROOT / "evals/evals.json"
DEFAULT_RUN_DIR = EVAL_ROOT / "latest"
BASELINE_DIR = EVAL_ROOT / "baseline"
REVIEW_TEMPLATE = EVAL_ROOT / "review-template.html"

EVAL_SKILL_MAP: dict[int, str] = {
    1: "docs/prompts/pipeline-debugging/SKILL.md",
    2: "docs/prompts/comprehensive-assessment/SKILL.md",
    3: "docs/prompts/manuscript-claim-verification/SKILL.md",
    4: "docs/prompts/reproducibility-audit/SKILL.md",
    5: "docs/prompts/manuscript-cross-references/SKILL.md",
    6: "docs/prompts/manuscript-creation/SKILL.md",
    7: "docs/prompts/test-creation/SKILL.md",
    8: "docs/prompts/infrastructure-module/SKILL.md",
    9: "docs/prompts/validation-quality/SKILL.md",
    10: "docs/prompts/feature-addition/SKILL.md",
    11: "docs/prompts/literature-synthesis/SKILL.md",
    12: "docs/prompts/documentation-creation/SKILL.md",
    13: "docs/prompts/refactoring/SKILL.md",
    14: "docs/prompts/code-development/SKILL.md",
    15: "docs/prompts/SKILL.md",
    16: "docs/prompts/SKILL.md",
    17: "docs/prompts/SKILL.md",
    18: "docs/prompts/SKILL.md",
    19: "docs/prompts/pipeline-debugging/SKILL.md",
    20: "docs/prompts/pipeline-debugging/SKILL.md",
    21: "docs/prompts/deep-research/SKILL.md",
    22: "docs/prompts/academic-paper/SKILL.md",
    23: "docs/prompts/academic-paper-reviewer/SKILL.md",
    24: "docs/prompts/academic-pipeline/SKILL.md",
    25: "docs/prompts/SKILL.md",
    26: "docs/prompts/SKILL.md",
    27: "docs/prompts/methods-orchestration/SKILL.md",
    28: "docs/prompts/agentic-use/SKILL.md",
    29: "docs/prompts/agentic-use/SKILL.md",
}

HUB_ROUTE_CHILD: dict[int, str] = {
    18: "docs/prompts/manuscript-cross-references/SKILL.md",
    26: "docs/prompts/academic-pipeline/SKILL.md",
}

CAPTURE_HEADINGS = frozenset(
    {
        "Natural invoke",
        "Inputs to confirm",
        "Workflow",
        "Workflows",
        "Deliverables",
        "Verification commands",
        "Routing table",
        "Ambiguous routing",
        "Style",
        "References",
    }
)
