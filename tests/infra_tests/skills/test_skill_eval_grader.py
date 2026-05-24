"""Table-driven tests for skill eval keyword grader (no mocks)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "docs/prompts/_skill-eval/scripts"
sys.path.insert(0, str(_SCRIPTS_DIR))

from skill_eval.grader import grade_output  # noqa: E402


def _expectation_passed(text: str, expectation: str, *, negative: bool = False) -> bool:
    result = grade_output(text, [expectation], negative=negative)
    assert len(result["expectations"]) == 1
    return result["expectations"][0]["passed"]


CLAIM_VERIFICATION_EXCERPT = """
## Workflow
Pass 1: inventory numbered claims from manuscript.
Pass 2: recompute metrics from src/ and regenerated outputs.
Pass 3: reconcile prose against live artifacts.
Never hand-edit output/ — regenerate via pipeline.
Use validation CLI prerender before PDF.
"""

REGISTRY_CROSS_REFS_EXCERPT = """
Audit labels.yaml registry tokens like [[FIG:foo]].
Warn against hard-coded theorem numbers in prose.
Confirm registry/token vs pure Pandoc-crossref — do not mix styles.
Run infrastructure.validation.cli markdown on manuscript/.
"""

PIPELINE_DEBUG_EXCERPT = """
Use --core-only to skip LLM stages.
Resume with --resume after fixing validate failures.
Find the first real error, not the last line exit code.
Run infrastructure.validation.cli on manuscript.
"""

PROJECT_ANALYSIS_EXCERPT = """
Name the failing stage (Project Analysis).
Isolate via scripts/02_run_analysis.py --project template_code_project.
Reproduce the first real error from stderr.
"""

INFRA_MODULE_EXCERPT = """
## Workflow
1. **Layout** — `__init__.py` under `infrastructure/<package>/`.
2. **Tests** — `tests/infra_tests/<package>/`.
"""

FEATURE_ADDITION_EXCERPT = """
## Workflow
1. **Design** — logic in `src/` or `infrastructure/`; script coordinates only.
2. **Implement** — src modules first (TDD: tests alongside).
"""

OUT_OF_SCOPE_FIBONACCI = """
This request is outside template workflow skills.
Provide a simple Python fibonacci implementation for homework.
No execute_pipeline.py or active_projects.md roster needed.
Research project naming is unrelated.
"""

HUB_ROUTING_TABLE_SNIPPET = """
| Symptom | Skill |
| code-development | template-code-development |
| broken refs | manuscript-cross-references |
| validate pdf | validation-quality |
Ask whether the issue is pipeline vs prose before routing.
Route to cross-reference or validation workflow, not code-development first.
"""

HUB_CODE_DEV_PRIMARY = """
Following the template-code-development skill:
## Workflow
1. Open code-development and implement fixes in src/
"""


@pytest.mark.parametrize(
    ("text", "expectation", "negative", "expected"),
    [
        (
            CLAIM_VERIFICATION_EXCERPT,
            "Describes multiple distinct verification passes",
            False,
            True,
        ),
        (
            CLAIM_VERIFICATION_EXCERPT,
            "Says not to hand-edit output/ directory",
            False,
            True,
        ),
        (
            REGISTRY_CROSS_REFS_EXCERPT,
            "Warns against hard-coded theorem/section numbers in prose",
            False,
            True,
        ),
        (
            REGISTRY_CROSS_REFS_EXCERPT,
            "Does not prescribe raw LaTeX \\ref in new prose",
            False,
            True,
        ),
        (
            PIPELINE_DEBUG_EXCERPT,
            "Names validate stage or validation CLI",
            False,
            True,
        ),
        (
            PIPELINE_DEBUG_EXCERPT,
            "Quotes need for first real error not last line",
            False,
            True,
        ),
        (
            PROJECT_ANALYSIS_EXCERPT,
            "Identifies Project Analysis stage or analysis script entrypoint",
            False,
            True,
        ),
        (
            INFRA_MODULE_EXCERPT,
            "Places code under infrastructure/",
            False,
            True,
        ),
        (
            FEATURE_ADDITION_EXCERPT,
            "Logic in src not scripts",
            False,
            True,
        ),
        (
            OUT_OF_SCOPE_FIBONACCI,
            "Does not require 90% template coverage gates",
            True,
            True,
        ),
        (
            "Research Project Template requires 90% cov-fail-under on src/",
            "Does not require 90% template coverage gates",
            True,
            False,
        ),
        (
            HUB_ROUTING_TABLE_SNIPPET,
            "Does not jump straight to unrelated code development",
            False,
            True,
        ),
        (
            HUB_CODE_DEV_PRIMARY,
            "Does not jump straight to unrelated code development",
            False,
            False,
        ),
    ],
    ids=[
        "claim-passes",
        "claim-hand-edit",
        "registry-hard-coded",
        "registry-no-ref",
        "pipeline-validate",
        "pipeline-first-error",
        "project-analysis",
        "infra-module-path",
        "feature-src-not-scripts",
        "fibonacci-negative-pass",
        "fibonacci-negative-fail-coverage",
        "hub-table-not-primary",
        "hub-code-dev-primary-fail",
    ],
)
def test_grader_expectations(
    text: str, expectation: str, negative: bool, expected: bool
) -> None:
    assert _expectation_passed(text, expectation, negative=negative) is expected
