"""Tests for :func:`infrastructure.project.discovery.resolve_project_root`."""

from __future__ import annotations

from pathlib import Path

from infrastructure.project.discovery import resolve_project_root


def test_resolve_project_root_prefers_active_over_working(tmp_path: Path) -> None:
    """Hot-seat ``projects/active/<name>`` wins when both it and a WIP tree exist."""
    active_demo = tmp_path / "projects" / "active" / "demo"
    (active_demo / "src").mkdir(parents=True)
    (active_demo / "tests").mkdir()
    (active_demo / "src" / "__init__.py").write_text("")
    (active_demo / "tests" / "__init__.py").write_text("")
    wip_demo = tmp_path / "projects" / "working" / "demo"
    wip_demo.mkdir(parents=True)
    (wip_demo / "marker.txt").write_text("wip")

    resolved = resolve_project_root(tmp_path, "demo")
    assert resolved == active_demo.resolve()
    assert not (resolved / "marker.txt").exists()


def test_resolve_project_root_falls_back_to_working(tmp_path: Path) -> None:
    """When not under ``projects/active/``, use ``projects/working/<name>``."""
    wip = tmp_path / "projects" / "working" / "staged"
    (wip / "manuscript").mkdir(parents=True)
    (wip / "manuscript" / "config.yaml").write_text("paper:\n  title: T\n")

    resolved = resolve_project_root(tmp_path, "staged")
    assert resolved == wip.resolve()


def test_resolve_project_root_ignores_output_only_projects_shadow(tmp_path: Path) -> None:
    """A generated output stub under projects/active/ must not hide a WIP source tree."""
    (tmp_path / "projects" / "active" / "staged" / "output" / "reports").mkdir(parents=True)
    wip = tmp_path / "projects" / "working" / "staged"
    (wip / "manuscript").mkdir(parents=True)
    (wip / "manuscript" / "config.yaml").write_text("paper:\n  title: T\n")

    resolved = resolve_project_root(tmp_path, "staged")
    assert resolved == wip.resolve()


def test_resolve_project_root_finds_templates_exemplar_by_bare_name(tmp_path: Path) -> None:
    """A public exemplar under projects/templates/<name> resolves by bare name."""
    exemplar = tmp_path / "projects" / "templates" / "template_demo"
    (exemplar / "src").mkdir(parents=True)
    (exemplar / "tests").mkdir()
    (exemplar / "manuscript").mkdir()
    (tmp_path / "projects" / "active" / "template_demo" / "output").mkdir(parents=True)

    resolved = resolve_project_root(tmp_path, "template_demo")
    assert resolved == exemplar.resolve()


def test_resolve_project_root_promoted_active_beats_templates(tmp_path: Path) -> None:
    """A genuinely promoted hot-seat tree still wins over a templates exemplar."""
    active = tmp_path / "projects" / "active" / "template_demo"
    (active / "src").mkdir(parents=True)
    (active / "tests").mkdir()
    templated = tmp_path / "projects" / "templates" / "template_demo"
    (templated / "src").mkdir(parents=True)
    (templated / "manuscript").mkdir()

    resolved = resolve_project_root(tmp_path, "template_demo")
    assert resolved == active.resolve()


def test_resolve_project_root_qualified_templates_prefix(tmp_path: Path) -> None:
    """``templates/<name>`` qualified prefix takes the fast path directly under projects/."""
    exemplar = tmp_path / "projects" / "templates" / "template_demo"
    (exemplar / "src").mkdir(parents=True)
    (exemplar / "src" / "__init__.py").write_text("")

    resolved = resolve_project_root(tmp_path, "templates/template_demo")
    assert resolved == exemplar.resolve()


def test_resolve_project_root_templates_stub_without_markers_does_not_win(tmp_path: Path) -> None:
    """An empty templates stub (no src/tests/scripts/manuscript) must not shadow an active tree."""
    stub = tmp_path / "projects" / "templates" / "template_stub"
    stub.mkdir(parents=True)
    active_shadow = tmp_path / "projects" / "active" / "template_stub" / "output"
    active_shadow.mkdir(parents=True)
    wip = tmp_path / "projects" / "working" / "template_stub"
    (wip / "manuscript").mkdir(parents=True)
    (wip / "manuscript" / "config.yaml").write_text("paper:\n  title: Stub WIP\n")

    resolved = resolve_project_root(tmp_path, "template_stub")
    assert resolved != stub.resolve()
    assert resolved == wip.resolve()


def test_resolve_project_root_output_only_flat_shadow_does_not_hide_exemplar(
    tmp_path: Path,
) -> None:
    """An output-only flat ``projects/<name>/`` skeleton must not shadow the exemplar."""
    (tmp_path / "projects" / "template_demo" / "output").mkdir(parents=True)
    exemplar = tmp_path / "projects" / "templates" / "template_demo"
    (exemplar / "src").mkdir(parents=True)
    (exemplar / "manuscript").mkdir()

    resolved = resolve_project_root(tmp_path, "template_demo")
    assert resolved == exemplar.resolve()


def test_resolve_project_root_flat_tree_with_markers_still_wins(tmp_path: Path) -> None:
    """A real flat standalone tree (with source markers) keeps beating templates/."""
    flat = tmp_path / "projects" / "template_demo"
    (flat / "src").mkdir(parents=True)
    (flat / "tests").mkdir()
    templated = tmp_path / "projects" / "templates" / "template_demo"
    (templated / "src").mkdir(parents=True)

    resolved = resolve_project_root(tmp_path, "template_demo")
    assert resolved == flat.resolve()


def test_resolve_project_root_markerless_flat_without_exemplar_falls_back(
    tmp_path: Path,
) -> None:
    """With no exemplar counterpart, a marker-less flat dir is still returned."""
    flat = tmp_path / "projects" / "bespoke_layout"
    (flat / "data").mkdir(parents=True)

    resolved = resolve_project_root(tmp_path, "bespoke_layout")
    assert resolved == flat.resolve()


def test_resolve_project_root_templates_stub_without_markers_falls_through(tmp_path: Path) -> None:
    """A templates/ dir that exists but lacks project markers must NOT shadow active/."""
    (tmp_path / "projects" / "templates" / "template_stub" / "output").mkdir(parents=True)
    active = tmp_path / "projects" / "active" / "template_stub"
    (active / "src").mkdir(parents=True)
    (active / "tests").mkdir()
    (active / "src" / "__init__.py").write_text("")

    resolved = resolve_project_root(tmp_path, "template_stub")
    assert resolved == active.resolve()
