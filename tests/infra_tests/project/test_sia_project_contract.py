"""Contract tests for template_sia git guards."""

from __future__ import annotations

from pathlib import Path

from infrastructure.project.git_guards import ALLOWED_PROJECT_DIRS, ALLOWED_TRACKED_OUTPUT_PREFIXES
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES


def test_template_sia_is_tracked_exemplar():
    assert "projects/templates/template_sia/" in ALLOWED_PROJECT_DIRS


def test_template_sia_output_prefix_allowed():
    assert "output/templates/template_sia/" in ALLOWED_TRACKED_OUTPUT_PREFIXES


def test_template_sia_is_public_project():
    assert "templates/template_sia" in PUBLIC_PROJECT_NAMES


def test_gitignore_allows_template_sia_project_tree():
    text = (Path(__file__).resolve().parents[3] / ".gitignore").read_text(encoding="utf-8")
    assert "!projects/templates/template_sia/" in text
    assert "!/output/templates/template_sia/" in text
