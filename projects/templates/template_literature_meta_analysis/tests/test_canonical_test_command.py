"""Bind the primary documentation surfaces to the isolated project test gate."""

from __future__ import annotations

import shlex
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parents[2]
CANONICAL_TEST_COMMAND = (
    "uv run python scripts/pipeline/stage_01_test.py "
    "--project templates/template_literature_meta_analysis --project-only"
)
PRIMARY_DOCS = (
    PROJECT_ROOT / "README.md",
    PROJECT_ROOT / "AGENTS.md",
    PROJECT_ROOT / ".agents" / "skills" / "template-literature-meta-analysis" / "SKILL.md",
)


@pytest.mark.parametrize("document", PRIMARY_DOCS, ids=lambda path: path.name)
def test_primary_docs_use_canonical_isolated_test_command(document: Path) -> None:
    """Fresh-clone instructions must not drift back to root-environment pytest."""
    assert CANONICAL_TEST_COMMAND in document.read_text(encoding="utf-8")


def test_canonical_test_command_targets_real_stage_and_qualified_project() -> None:
    """The documented command must resolve to the Stage-01 project-only gate."""
    assert shlex.split(CANONICAL_TEST_COMMAND) == [
        "uv",
        "run",
        "python",
        "scripts/pipeline/stage_01_test.py",
        "--project",
        "templates/template_literature_meta_analysis",
        "--project-only",
    ]
    assert (REPO_ROOT / "scripts" / "pipeline" / "stage_01_test.py").is_file()
