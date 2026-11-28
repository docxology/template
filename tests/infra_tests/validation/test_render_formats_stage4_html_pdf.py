"""Real-filesystem regressions for combined HTML and Stage 4 format gates."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from infrastructure.core.pipeline.artifacts import collect_stable_output_inventory, output_inventory_mode_for_project
from infrastructure.project.discovery import resolve_project_root
from infrastructure.rendering._pipeline_summary import verify_render_outputs
from infrastructure.validation.output.pipeline import (
    build_core_checks,
    execute_validation_pipeline,
    verify_outputs_exist,
)
from infrastructure.validation.output.render_formats import validate_enabled_render_outputs
from tests.infra_tests.validation._render_formats_helpers import _minimal_pdf, _html_only_project

_BIBLIOGRAPHY = '<div id="refs" class="references csl-bib-body" role="list">{}</div>'
_ENTRY = '<div id="ref-demo" class="csl-entry" role="listitem"><em>Example work.</em></div>'


@pytest.mark.parametrize("stage", ["stage03", "stage04"])
@pytest.mark.parametrize(
    ("href", "destination", "valid"),
    [
        pytest.param("#ref-demo", _BIBLIOGRAPHY.format(_ENTRY), True, id="visible-entry"),
        pytest.param(
            "#ref-d%C3%A9mo%26co",
            _BIBLIOGRAPHY.format(_ENTRY.replace("ref-demo", "ref-d&eacute;mo&amp;co")),
            True,
            id="decoded-identifier",
        ),
        pytest.param("#ref-demo", _BIBLIOGRAPHY.format(""), False, id="missing-entry"),
        pytest.param("#ref-fig%3Ademo", "", True, id="reserved-cross-reference"),
        pytest.param("#ref-figure:demo", "", False, id="ordinary-key-with-colon"),
        pytest.param("#ref-demo", _BIBLIOGRAPHY.format(_ENTRY * 2), False, id="duplicate-entries"),
        pytest.param(
            "#ref-demo",
            _BIBLIOGRAPHY.format(_ENTRY) + '<h2 id="ref-demo">Duplicate ID elsewhere</h2>',
            False,
            id="duplicate-id-outside-bibliography",
        ),
        pytest.param(
            "#ref-demo",
            _BIBLIOGRAPHY.format('<h2 id="ref-demo">Unrelated content</h2>'),
            False,
            id="unrelated-id",
        ),
        pytest.param("#ref-demo", _ENTRY, False, id="entry-outside-bibliography"),
        pytest.param(
            "#ref-demo",
            _BIBLIOGRAPHY.format(_ENTRY.replace("<em>Example work.</em>", "&nbsp;<br><em> </em>")),
            False,
            id="empty-entry",
        ),
        pytest.param("#ref-demo", _BIBLIOGRAPHY.format(f"<!--{_ENTRY}-->"), False, id="commented-entry"),
        pytest.param("#ref-demo", _BIBLIOGRAPHY.format(f"<template>{_ENTRY}</template>"), False, id="inert-entry"),
        pytest.param("#ref-demo", _BIBLIOGRAPHY.format(f"<div hidden>{_ENTRY}</div>"), False, id="hidden-entry"),
        pytest.param(
            "#ref-demo",
            _BIBLIOGRAPHY.format(_ENTRY.replace("<em>", "<em hidden>")),
            False,
            id="hidden-entry-text",
        ),
        pytest.param("#REF-demo", _BIBLIOGRAPHY.format(_ENTRY), False, id="case-sensitive-identifier"),
    ],
)
def test_native_html_gates_require_linked_bibliography_entries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    stage: str,
    href: str,
    destination: str,
    valid: bool,
) -> None:
    for name in ("ENABLE_PDF", "ENABLE_HTML", "ENABLE_SLIDES", "ENABLE_DOCX", "ENABLE_EPUB"):
        monkeypatch.delenv(name, raising=False)
    project_root = _html_only_project(tmp_path)
    (project_root / "output" / "web" / "index.html").write_text(
        "<!doctype html><html><body>"
        f'<p><span class="citation" data-cites="demo"><a href="{href}" role="doc-biblioref">Demo</a></span></p>'
        '<p><a href="#ref-authored-fragment">Ordinary link</a></p>'
        f"{destination}</body></html>",
        encoding="utf-8",
    )

    if stage == "stage03":
        result = verify_render_outputs("demo", repo_root=tmp_path)
    else:
        checks = {check.name: check.run for check in build_core_checks("demo", repo_root=tmp_path)}
        result = checks["Enabled render outputs"]()

    assert result is valid
    if not valid:
        assert "Combined HTML citation validation failed" in caplog.text
        assert href in caplog.text


@pytest.mark.parametrize(
    ("before", "after"),
    [
        pytest.param("<p hidden>Reader-mode note<p>", "</p>", id="paragraph"),
        pytest.param("<p hidden>Reader-mode note<dialog open>", "</dialog>", id="paragraph-before-dialog"),
        pytest.param("<ul><li hidden>Reader-mode note<li>", "</li></ul>", id="list-item"),
        pytest.param("<ul><li hidden><p>Reader-mode note<li>", "</li></ul>", id="paragraph-in-list-item"),
        pytest.param("<dl><dt hidden>Reader-mode note<dd>", "</dd></dl>", id="definition-item"),
        pytest.param(
            "<table><tbody><tr><td hidden>Reader-mode note<td>",
            "</td></tr></tbody></table>",
            id="table-cell",
        ),
        pytest.param(
            "<table><tbody><tr hidden><td><p>Reader-mode note<tr><td>",
            "</td></tr></tbody></table>",
            id="table-row",
        ),
        pytest.param(
            "<table><thead hidden><tr><th>Reader-mode note<tbody><tr><td>",
            "</td></tr></tbody></table>",
            id="table-section",
        ),
        pytest.param(
            "<table><colgroup hidden><col><tbody><tr><td>",
            "</td></tr></tbody></table>",
            id="column-group-before-body",
        ),
        pytest.param(
            "<table><colgroup hidden><col><tr><td>",
            "</td></tr></table>",
            id="column-group-before-row",
        ),
        pytest.param(
            "<table><colgroup hidden><col><colgroup><col></colgroup><thead><tr><th>",
            "</th></tr></thead></table>",
            id="column-group-before-next-group",
        ),
        pytest.param(
            "<table><caption hidden>Reader-mode note<tbody><tr><td>",
            "</td></tr></tbody></table>",
            id="table-caption",
        ),
        pytest.param(
            "<p><ruby>Term<rp hidden>(<rt>",
            "</rt><rp>)</ruby></p>",
            id="ruby-parenthesis",
        ),
        pytest.param(
            "<p><ruby>Term<rt hidden>Reader-mode note<rt>",
            "</rt></ruby></p>",
            id="ruby-annotation",
        ),
    ],
)
@pytest.mark.parametrize("has_entry", [True, False], ids=["valid-entry", "missing-entry"])
def test_native_html_gates_check_citations_after_optional_end_tags(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    before: str,
    after: str,
    has_entry: bool,
) -> None:
    for name in ("ENABLE_PDF", "ENABLE_HTML", "ENABLE_SLIDES", "ENABLE_DOCX", "ENABLE_EPUB"):
        monkeypatch.delenv(name, raising=False)
    project_root = _html_only_project(tmp_path)
    withheld = '<a href="#ref-withheld" role="doc-biblioref">Withheld</a>'
    (project_root / "output" / "web" / "index.html").write_text(
        "<!doctype html><html><body>"
        f"<div hidden><p>Hidden note<p>{withheld}</p></div>"
        f"<ul><li hidden><ul><li>{withheld}</li></ul></li></ul>"
        f"<table><tr><td hidden><table><tr><td>{withheld}</td></tr></table></td></tr></table>"
        f"<table hidden><colgroup><col><tbody><tr><td>{withheld}</td></tr></tbody></table>"
        f"<p><ruby hidden>Term<rp hidden>(<rt>{withheld}</rt><rp>)</ruby></p>"
        f"<template><p hidden>Inert note<p>{withheld}</p></template>"
        f"<textarea><p hidden>Literal note<p>{withheld}</textarea>"
        f'{before}<a href="#ref-demo" role="doc-biblioref">Demo</a>{after}'
        f"{_BIBLIOGRAPHY.format(_ENTRY if has_entry else '')}</body></html>",
        encoding="utf-8",
    )

    stage03 = verify_render_outputs("demo", repo_root=tmp_path)
    checks = {check.name: check.run for check in build_core_checks("demo", repo_root=tmp_path)}
    stage04 = checks["Enabled render outputs"]()
    assert (stage03, stage04) == (has_entry, has_entry)
    assert "#ref-withheld" not in caplog.text
    if not has_entry:
        assert "Bibliography link '#ref-demo'" in caplog.text


def test_stage4_html_only_accepts_clean_tree(tmp_path) -> None:
    _html_only_project(tmp_path)

    checks = {check.name: check.run for check in build_core_checks("demo", repo_root=tmp_path)}

    assert "PDF validation" not in checks
    assert "Transmission bookends" not in checks
    assert checks["Enabled render outputs"]() is True


def test_stage4_html_only_full_stage_succeeds_without_pdf(tmp_path) -> None:
    _html_only_project(tmp_path)
    recorded_checks = {}

    def report_writer(check_results, *_args, **_kwargs):
        recorded_checks.update(check_results)
        return {"timestamp": "1970-01-01T00:00:00Z"}

    assert execute_validation_pipeline("demo", repo_root=tmp_path, report_writer=report_writer) == 0
    assert recorded_checks["Output structure"] is True


def test_stage4_html_only_detailed_structure_does_not_invent_pdf(tmp_path) -> None:
    _html_only_project(tmp_path)

    valid, details = verify_outputs_exist("demo", repo_root=tmp_path, enabled_formats={"html"})

    assert valid is True
    assert details["structure"]["missing_files"] == []
    assert details["structure"]["directory_structure"]["combined_pdf"]["required"] is False
    assert details["structure"]["directory_structure"]["slides"]["required"] is False
    assert details["structure"]["directory_structure"]["docx"]["required"] is False
    assert details["structure"]["directory_structure"]["epub"]["required"] is False
    assert not any(
        name in message
        for message in details["issues_by_severity"]["info"]
        for name in ("pdf/", "slides/", "docx/", "epub/")
    )


def test_stage4_html_only_rejects_stale_disabled_pdf(tmp_path) -> None:
    project_root = _html_only_project(tmp_path)
    stale_pdf = project_root / "output" / "pdf" / "old_section.pdf"
    stale_pdf.parent.mkdir(parents=True)
    stale_pdf.write_bytes(_minimal_pdf())

    checks = {check.name: check.run for check in build_core_checks("demo", repo_root=tmp_path)}

    assert checks["Enabled render outputs"]() is False


def test_stage4_pdf_requires_canonical_combined_pdf(tmp_path) -> None:
    project_root = tmp_path / "projects" / "active" / "demo"
    manuscript_dir = project_root / "manuscript"
    manuscript_dir.mkdir(parents=True)
    (manuscript_dir / "01_intro.md").write_text("# Intro\n", encoding="utf-8")
    (manuscript_dir / "config.yaml").write_text(
        "render:\n  formats:\n    pdf: true\n    html: false\n    slides: false\n",
        encoding="utf-8",
    )
    pdf_dir = project_root / "output" / "pdf"
    pdf_dir.mkdir(parents=True)
    (pdf_dir / "other_valid.pdf").write_bytes(_minimal_pdf())

    checks = {check.name: check.run for check in build_core_checks("demo", repo_root=tmp_path)}

    assert checks["PDF validation"]() is True
    assert checks["Enabled render outputs"]() is False


def test_enabled_pdf_cannot_be_gitignored_publication_evidence(tmp_path) -> None:
    """Structural validity cannot substitute for a shippable PDF."""
    output_dir = tmp_path / "output"
    pdf = output_dir / "pdf" / "demo_combined.pdf"
    pdf.parent.mkdir(parents=True)
    pdf.write_bytes(_minimal_pdf())
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / ".gitignore").write_text("output/pdf/*.pdf\n", encoding="utf-8")

    assert (
        validate_enabled_render_outputs(
            output_dir,
            "demo",
            {"pdf"},
            pdf_validator=lambda: True,
        )
        is False
    )


def test_managed_external_project_accepts_valid_ignored_local_pdf(tmp_path) -> None:
    """A lifecycle sidecar's blanket output ignore is local scope, not absence."""
    repo_root = tmp_path / "template"
    external_project = tmp_path / "private" / "demo"
    manuscript = external_project / "manuscript"
    manuscript.mkdir(parents=True)
    (manuscript / "01_intro.md").write_text("# Intro\n", encoding="utf-8")
    (manuscript / "config.yaml").write_text(
        "render:\n  formats:\n    pdf: true\n    html: false\n    slides: false\n    docx: false\n    epub: false\n",
        encoding="utf-8",
    )
    pdf = external_project / "output" / "pdf" / "demo_combined.pdf"
    pdf.parent.mkdir(parents=True)
    pdf.write_bytes(_minimal_pdf())
    subprocess.run(["git", "init", "-q"], cwd=external_project, check=True, capture_output=True)
    (external_project / ".gitignore").write_text("output/\n", encoding="utf-8")
    managed_link = repo_root / "projects" / "working" / "demo"
    managed_link.parent.mkdir(parents=True)
    managed_link.symlink_to(external_project, target_is_directory=True)

    resolved = resolve_project_root(repo_root, "working/demo")
    inventory = collect_stable_output_inventory(
        resolved / "output",
        inventory_mode=output_inventory_mode_for_project(repo_root, resolved),
    )

    assert resolved == external_project.resolve()
    assert inventory.mode == "stable-local-output-v1"
    assert pdf.absolute() in inventory.files
    checks = {check.name: check.run for check in build_core_checks("working/demo", repo_root=repo_root)}
    assert checks["Enabled render outputs"]() is True
    assert (
        validate_enabled_render_outputs(
            resolved / "output",
            "working/demo",
            {"pdf"},
            pdf_validator=lambda: True,
            inventory=inventory,
        )
        is True
    )


def test_public_template_blanket_ignore_cannot_downgrade_shippable_gate(tmp_path) -> None:
    """A public ignore-policy regression must expose an empty release inventory."""
    repo_root = tmp_path / "template"
    project = repo_root / "projects" / "templates" / "demo"
    pdf = project / "output" / "pdf" / "demo_combined.pdf"
    pdf.parent.mkdir(parents=True)
    pdf.write_bytes(_minimal_pdf())
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True, capture_output=True)
    (repo_root / ".gitignore").write_text("projects/templates/demo/output/\n", encoding="utf-8")

    inventory = collect_stable_output_inventory(
        project / "output",
        inventory_mode=output_inventory_mode_for_project(repo_root, project),
    )

    assert inventory.mode == "stable-shippable-output-v1"
    assert inventory.files == ()
    assert (
        validate_enabled_render_outputs(
            project / "output",
            "templates/demo",
            {"pdf"},
            pdf_validator=lambda: True,
            inventory=inventory,
        )
        is False
    )
