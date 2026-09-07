"""Tests for infrastructure.rendering.pipeline manuscript resolution.

Covers _resolve_manuscript_dir injection/fallback behavior, project-resolved
config ownership, and the unresolved-token guard that fails the render closed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.core.exceptions import ValidationError
from infrastructure.rendering.pipeline import (
    _has_generated_manuscript_ordering,
    _is_project_resolved,
    _resolve_manuscript_dir,
    _unresolved_config_tokens,
    _verify_config_tokens_resolved,
)


# ---------------------------------------------------------------------------
# _resolve_manuscript_dir
# ---------------------------------------------------------------------------


def test_resolve_manuscript_dir_uses_injected_when_present(tmp_path: Path) -> None:
    """Prefers output/manuscript/ when it exists and contains .md files."""
    injected = tmp_path / "output" / "manuscript"
    injected.mkdir(parents=True)
    (injected / "01_intro.md").write_text("# Intro")

    result = _resolve_manuscript_dir(tmp_path)

    assert result == injected


def test_resolve_manuscript_dir_refreshes_injected_auxiliary_files(tmp_path: Path) -> None:
    """Refreshes source config, preamble, and bibliography with injected Markdown."""
    source = tmp_path / "manuscript"
    injected = tmp_path / "output" / "manuscript"
    source.mkdir()
    injected.mkdir(parents=True)
    (injected / "01_intro.md").write_text("# Intro")
    (source / "config.yaml").write_text("book:\n  title: Fresh\n", encoding="utf-8")
    (injected / "config.yaml").write_text("book:\n  title: Stale\n", encoding="utf-8")
    (source / "preamble.md").write_text("```latex\n% Fresh preamble\n```\n", encoding="utf-8")
    (injected / "preamble.md").write_text("```latex\n% Stale preamble\n```\n", encoding="utf-8")
    (source / "references.bib").write_text("@book{fresh,title={Fresh}}\n", encoding="utf-8")
    (injected / "references.bib").write_text("@book{stale,title={Stale}}\n", encoding="utf-8")

    result = _resolve_manuscript_dir(tmp_path)

    assert result == injected
    assert "Fresh" in (injected / "config.yaml").read_text(encoding="utf-8")
    assert "Fresh preamble" in (injected / "preamble.md").read_text(encoding="utf-8")
    assert "Stale preamble" not in (injected / "preamble.md").read_text(encoding="utf-8")
    assert "fresh" in (injected / "references.bib").read_text(encoding="utf-8")


def test_resolve_manuscript_dir_falls_back_to_source(tmp_path: Path) -> None:
    """Falls back to manuscript/ when injected dir is absent."""
    result = _resolve_manuscript_dir(tmp_path)

    assert result == tmp_path / "manuscript"


def test_resolve_manuscript_dir_falls_back_to_docs_source(tmp_path: Path) -> None:
    """Uses docs/manuscript directly when it is the populated source tree."""
    source = tmp_path / "docs" / "manuscript"
    source.mkdir(parents=True)
    (source / "01_intro.md").write_text("# Intro\n", encoding="utf-8")

    result = _resolve_manuscript_dir(tmp_path)

    assert result == source


def test_resolve_manuscript_dir_refreshes_injected_config_from_docs_source(tmp_path: Path) -> None:
    """Injected Markdown retains the canonical docs/manuscript configuration."""
    source = tmp_path / "docs" / "manuscript"
    injected = tmp_path / "output" / "manuscript"
    source.mkdir(parents=True)
    injected.mkdir(parents=True)
    (source / "01_intro.md").write_text("# Source\n", encoding="utf-8")
    (source / "config.yaml").write_text("paper:\n  title: Fresh docs config\n", encoding="utf-8")
    (source / "references.bib").write_text("@article{fresh,title={Fresh}}\n", encoding="utf-8")
    (injected / "01_intro.md").write_text("# Injected\n", encoding="utf-8")
    (injected / "config.yaml").write_text("paper:\n  title: Stale\n", encoding="utf-8")

    result = _resolve_manuscript_dir(tmp_path)

    assert result == injected
    assert "Fresh docs config" in (injected / "config.yaml").read_text(encoding="utf-8")
    assert "fresh" in (injected / "references.bib").read_text(encoding="utf-8")


def test_resolve_manuscript_dir_returns_manuscript_path_when_absent(tmp_path: Path) -> None:
    """Returns manuscript/ even when neither injected nor source trees exist."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    result = _resolve_manuscript_dir(project_root)

    assert result == project_root / "manuscript"


def test_resolve_manuscript_dir_preserves_generated_config_ordering(tmp_path: Path) -> None:
    """Keeps injected config.yaml when it carries generated ordering marker."""
    source = tmp_path / "manuscript"
    injected = tmp_path / "output" / "manuscript"
    source.mkdir()
    injected.mkdir(parents=True)
    (injected / "01_intro.md").write_text("# Intro")
    (source / "config.yaml").write_text("book:\n  title: Source\n", encoding="utf-8")
    (injected / "config.yaml").write_text(
        "# Generated manuscript ordering\nbook:\n  title: Generated\n",
        encoding="utf-8",
    )

    result = _resolve_manuscript_dir(tmp_path)

    assert result == injected
    assert "Generated" in (injected / "config.yaml").read_text(encoding="utf-8")
    assert "Source" not in (injected / "config.yaml").read_text(encoding="utf-8")


def test_resolve_manuscript_dir_falls_back_when_injected_empty(tmp_path: Path) -> None:
    """Falls back to source when injected dir exists but has no .md files."""
    injected = tmp_path / "output" / "manuscript"
    injected.mkdir(parents=True)
    # directory exists but no .md files

    result = _resolve_manuscript_dir(tmp_path)

    assert result == tmp_path / "manuscript"


def test_resolve_manuscript_dir_ignores_non_md_files_in_injected(tmp_path: Path) -> None:
    """Falls back to source when injected dir has only non-.md files."""
    injected = tmp_path / "output" / "manuscript"
    injected.mkdir(parents=True)
    (injected / "notes.txt").write_text("just a note")

    result = _resolve_manuscript_dir(tmp_path)

    assert result == tmp_path / "manuscript"


# ---------------------------------------------------------------------------
# Project-resolved config.yaml is authoritative (never clobbered by the source)
# ---------------------------------------------------------------------------


def test_resolve_manuscript_dir_preserves_project_resolved_config(tmp_path: Path) -> None:
    """A generator that substituted {{TOKEN}}s into the injected config keeps its work.

    Regression pin: the source config is a token template, so copying it over
    the injected copy would silently discard the project's substitution and
    print ``{{PAPER_TITLE}}`` verbatim on the PDF title page.
    """
    source = tmp_path / "manuscript"
    injected = tmp_path / "output" / "manuscript"
    source.mkdir()
    injected.mkdir(parents=True)
    (injected / "01_intro.md").write_text("# Intro", encoding="utf-8")
    (source / "config.yaml").write_text('paper:\n  title: "{{PAPER_TITLE}}"\n', encoding="utf-8")
    (injected / "config.yaml").write_text('paper:\n  title: "Resolved Title"\n', encoding="utf-8")

    result = _resolve_manuscript_dir(tmp_path)

    assert result == injected
    rendered_config = (injected / "config.yaml").read_text(encoding="utf-8")
    assert "Resolved Title" in rendered_config
    assert "{{PAPER_TITLE}}" not in rendered_config


def test_resolve_manuscript_dir_preserves_config_with_explicit_project_marker(tmp_path: Path) -> None:
    """The explicit project-resolved marker claims ownership without any token diff."""
    source = tmp_path / "manuscript"
    injected = tmp_path / "output" / "manuscript"
    source.mkdir()
    injected.mkdir(parents=True)
    (injected / "01_intro.md").write_text("# Intro", encoding="utf-8")
    (source / "config.yaml").write_text("paper:\n  title: Source\n", encoding="utf-8")
    (injected / "config.yaml").write_text(
        "# Project-resolved config\npaper:\n  title: Project Owned\n",
        encoding="utf-8",
    )

    result = _resolve_manuscript_dir(tmp_path)

    assert result == injected
    assert "Project Owned" in (injected / "config.yaml").read_text(encoding="utf-8")


def test_is_project_resolved_preserves_generated_ordering_branch(tmp_path: Path) -> None:
    """The original marker test survives as one branch of the generalized test."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text("# Generated manuscript ordering\npaper:\n  title: X\n", encoding="utf-8")

    assert _is_project_resolved(cfg) is True
    assert _has_generated_manuscript_ordering(cfg) is True


def test_is_project_resolved_false_for_plain_injected_config(tmp_path: Path) -> None:
    """A tokenless source still refreshes a tokenless injected config, as before."""
    source_cfg = tmp_path / "source_config.yaml"
    injected_cfg = tmp_path / "config.yaml"
    source_cfg.write_text("paper:\n  title: Source\n", encoding="utf-8")
    injected_cfg.write_text("paper:\n  title: Stale\n", encoding="utf-8")

    assert _is_project_resolved(injected_cfg, source_cfg) is False


def test_is_project_resolved_false_when_injected_still_holds_the_token(tmp_path: Path) -> None:
    """An injected copy that resolved nothing has no ownership claim."""
    source_cfg = tmp_path / "source_config.yaml"
    injected_cfg = tmp_path / "config.yaml"
    source_cfg.write_text('paper:\n  title: "{{PAPER_TITLE}}"\n', encoding="utf-8")
    injected_cfg.write_text('paper:\n  title: "{{PAPER_TITLE}}"\n', encoding="utf-8")

    assert _is_project_resolved(injected_cfg, source_cfg) is False


# ---------------------------------------------------------------------------
# Unresolved {{TOKEN}} in the final config.yaml fails the render closed
# ---------------------------------------------------------------------------


def test_resolve_manuscript_dir_rejects_unresolved_token_in_injected_config(tmp_path: Path) -> None:
    """A token surviving into the injected config aborts before anything renders."""
    source = tmp_path / "manuscript"
    injected = tmp_path / "output" / "manuscript"
    source.mkdir()
    injected.mkdir(parents=True)
    (injected / "01_intro.md").write_text("# Intro", encoding="utf-8")
    (source / "config.yaml").write_text('paper:\n  title: "{{PAPER_TITLE}}"\n', encoding="utf-8")
    (injected / "config.yaml").write_text('paper:\n  title: "{{PAPER_TITLE}}"\n', encoding="utf-8")

    with pytest.raises(ValidationError) as excinfo:
        _resolve_manuscript_dir(tmp_path)

    assert "PAPER_TITLE" in str(excinfo.value)


def test_resolve_manuscript_dir_rejects_unresolved_token_in_source_config(tmp_path: Path) -> None:
    """The same guarantee covers the non-injected fallback path."""
    source = tmp_path / "manuscript"
    source.mkdir()
    (source / "01_intro.md").write_text("# Intro", encoding="utf-8")
    (source / "config.yaml").write_text('paper:\n  title: "{{PAPER_TITLE}}"\n', encoding="utf-8")

    with pytest.raises(ValidationError) as excinfo:
        _resolve_manuscript_dir(tmp_path)

    assert "PAPER_TITLE" in str(excinfo.value)


def test_unresolved_config_tokens_ignores_documented_token_in_code_span(tmp_path: Path) -> None:
    """A config documenting the token syntax in backticks is not an unresolved token.

    ``projects/templates/template_gold_refinement/manuscript/config.yaml``
    contains ``transformation: "Resolve `{{TOKEN}}` placeholders ..."`` — prose
    about the contract, which must never fail that project's render.
    """
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        'provenance:\n  transformation: "Resolve `{{TOKEN}}` placeholders into output/manuscript/"\n',
        encoding="utf-8",
    )

    assert _unresolved_config_tokens(cfg) == []
    _verify_config_tokens_resolved(cfg)


def test_unresolved_config_tokens_reports_sorted_unique_tokens(tmp_path: Path) -> None:
    """Every distinct live token is reported once, sorted."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        'paper:\n  title: "{{PAPER_TITLE}}"\n  subtitle: "{{PAPER_TITLE}} / {{ABSTRACT}}"\n',
        encoding="utf-8",
    )

    assert _unresolved_config_tokens(cfg) == ["ABSTRACT", "PAPER_TITLE"]


def test_unresolved_config_tokens_missing_file(tmp_path: Path) -> None:
    """An absent config has no tokens and never fails the render."""
    assert _unresolved_config_tokens(tmp_path / "missing.yaml") == []
    _verify_config_tokens_resolved(tmp_path / "missing.yaml")
