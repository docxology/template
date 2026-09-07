"""No-mock tests for publication record generation, drift checking, and writing.

These tests exercise real code paths in ``infrastructure.documentation.publication_records``
that are not covered by the existing ``test_publication_records.py`` and
``test_publication_records_additional.py`` suites — specifically:

* ``write_publication_records_doc`` end-to-end (writes the generated markdown,
  syncs the ``.github/README.md`` block, and updates ``STANDALONE.md`` identity blocks).
* ``check_publication_records_doc`` drift paths: missing generated doc, missing
  ``.github/README.md``, stale standalone blocks.
* Internal helpers: ``_markdown_table_rows``, ``_row_map_differences``,
  ``_publication_matrix_source_rows``, ``_github_readme_source_rows``,
  ``_local_source_path_rows``.
* ``render_publication_records_doc`` with ``refreshed_external=True`` and with
  an explicit ``generated_at`` timestamp.
* ``PublicationRecord`` computed-property edge cases (monorepo slug, non-github URLs,
  declared_location_count, sidecar_status, external_status).
* ``_relative_link`` for ``_generated`` directory and root-relative paths.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from infrastructure.documentation.publication_records import (
    PublicationRecord,
    README_BLOCK_BEGIN,
    README_BLOCK_END,
    _github_readme_source_rows,
    _local_source_path_rows,
    _markdown_table_rows,
    _publication_matrix_source_rows,
    _relative_link,
    _row_map_differences,
    check_publication_records_doc,
    load_publication_records,
    render_github_readme_publication_block,
    render_publication_records_doc,
    replace_github_readme_publication_block,
    write_publication_records_doc,
)
from infrastructure.documentation.publication_standalone import (
    STANDALONE_BLOCK_BEGIN,
    STANDALONE_BLOCK_END,
    render_standalone_publication_block,
    replace_standalone_publication_block,
)
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES


def _scaffold_publication_project(root: Path, name: str, version: str = "1.0.0") -> None:
    """Scaffold a minimum-valid publication project under ``root/projects/<name>``."""
    project_root = root / "projects" / name
    (project_root / "src").mkdir(parents=True)
    (project_root / "tests").mkdir()
    (project_root / "manuscript").mkdir()
    (project_root / "src" / "__init__.py").write_text("", encoding="utf-8")
    (project_root / "tests" / "__init__.py").write_text("", encoding="utf-8")
    concept_id = abs(hash(name)) % 100000 + 100000
    version_id = concept_id + 1
    concept_doi = f"10.5281/zenodo.{concept_id}"
    version_doi = f"10.5281/zenodo.{version_id}"
    (project_root / "manuscript" / "config.yaml").write_text(
        "\n".join(
            [
                "paper:",
                f"  title: {name}",
                f"  version: '{version}'",
                "authors:",
                "  - name: Daniel Ari Friedman",
                "publication:",
                f"  doi: '{concept_doi}'",
                f"  version_doi: '{version_doi}'",
                f"  version_record: 'https://zenodo.org/records/{version_id}'",
                f"  github_repository: 'docxology/{name}'",
                "  published_artifacts:",
                f"    github_pages: 'https://docxology.github.io/{name}/'",
                f"    osf: 'https://osf.io/{concept_id}/'",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (project_root / "CITATION.cff").write_text(
        f"cff-version: 1.2.0\ntitle: {name}\ndoi: {concept_doi}\nversion: '{version}'\n",
        encoding="utf-8",
    )
    (project_root / ".zenodo.json").write_text(
        json.dumps({"title": name, "version": version}),
        encoding="utf-8",
    )
    (project_root / "codemeta.json").write_text(
        json.dumps({"name": name, "version": version, "identifier": concept_doi}),
        encoding="utf-8",
    )
    (project_root / "STANDALONE.md").write_text(f"# {name} standalone contract\n", encoding="utf-8")


def _scaffold_all_public_projects(root: Path) -> None:
    for name in PUBLIC_PROJECT_NAMES:
        _scaffold_publication_project(root, name)


def _sync_standalone_blocks(records: list[PublicationRecord]) -> None:
    for record in records:
        standalone_path = record.standalone_path
        standalone_path.write_text(
            replace_standalone_publication_block(
                standalone_path.read_text(encoding="utf-8"),
                render_standalone_publication_block(record),
            ),
            encoding="utf-8",
        )


# ---------------------------------------------------------------------------
# write_publication_records_doc
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_write_writes_generated_markdown_without_readme(tmp_path: Path) -> None:
    """``write_publication_records_doc`` writes the generated publication matrix."""
    _scaffold_all_public_projects(tmp_path)
    records = load_publication_records(tmp_path)
    _sync_standalone_blocks(records)

    out_path, readme_path = write_publication_records_doc(tmp_path, update_github_readme=False)

    assert out_path == tmp_path / "docs" / "_generated" / "publication_records.md"
    assert out_path.is_file()
    content = out_path.read_text(encoding="utf-8")
    assert "# Publication Records" in content
    assert "Do not edit by hand" in content
    for name in PUBLIC_PROJECT_NAMES:
        assert f"`{name}`" in content
    assert readme_path is None


def test_write_updates_github_readme_block(tmp_path: Path) -> None:
    """``write_publication_records_doc`` syncs the ``.github/README.md`` block."""
    _scaffold_all_public_projects(tmp_path)
    records = load_publication_records(tmp_path)
    _sync_standalone_blocks(records)
    github_dir = tmp_path / ".github"
    github_dir.mkdir()
    readme_path = github_dir / "README.md"
    readme_path.write_text(
        "\n".join(["# Template", "", README_BLOCK_BEGIN, "old block", README_BLOCK_END, "", "footer"]),
        encoding="utf-8",
    )

    _out, returned_readme = write_publication_records_doc(tmp_path, update_github_readme=True)

    assert returned_readme == readme_path
    updated = readme_path.read_text(encoding="utf-8")
    assert README_BLOCK_BEGIN in updated
    assert README_BLOCK_END in updated
    assert "old block" not in updated
    for name in PUBLIC_PROJECT_NAMES:
        assert f"../projects/{name}/" in updated
    assert "footer" in updated


def test_write_syncs_standalone_identity_blocks(tmp_path: Path) -> None:
    """``write_publication_records_doc`` inserts publication identity blocks into STANDALONE.md."""
    _scaffold_all_public_projects(tmp_path)
    records = load_publication_records(tmp_path)
    _sync_standalone_blocks(records)

    write_publication_records_doc(tmp_path, update_github_readme=False)

    for record in records:
        content = record.standalone_path.read_text(encoding="utf-8")
        assert STANDALONE_BLOCK_BEGIN in content
        assert STANDALONE_BLOCK_END in content
        assert record.concept_doi in content
        assert record.github_display_url in content


def test_write_skips_missing_standalone(tmp_path: Path) -> None:
    """Projects without a STANDALONE.md are skipped during standalone sync."""
    _scaffold_all_public_projects(tmp_path)
    records = load_publication_records(tmp_path)
    _sync_standalone_blocks(records)
    first = records[0]
    first.standalone_path.unlink()

    out_path, _ = write_publication_records_doc(tmp_path, update_github_readme=False)

    assert out_path.is_file()
    for record in records[1:]:
        content = record.standalone_path.read_text(encoding="utf-8")
        assert STANDALONE_BLOCK_BEGIN in content


# ---------------------------------------------------------------------------
# check_publication_records_doc — drift paths
# ---------------------------------------------------------------------------


def test_check_returns_missing_doc_when_generated_absent(tmp_path: Path) -> None:
    """Missing ``docs/_generated/publication_records.md`` is reported as drift."""
    _scaffold_all_public_projects(tmp_path)
    records = load_publication_records(tmp_path)
    _sync_standalone_blocks(records)

    differences = check_publication_records_doc(tmp_path, update_github_readme=False)

    doc_path = tmp_path / "docs" / "_generated" / "publication_records.md"
    assert differences == [f"missing {doc_path.relative_to(tmp_path)}"]


def test_check_reports_missing_github_readme(tmp_path: Path) -> None:
    """Missing ``.github/README.md`` is reported when ``update_github_readme=True``."""
    _scaffold_all_public_projects(tmp_path)
    records = load_publication_records(tmp_path)
    _sync_standalone_blocks(records)
    (tmp_path / "docs" / "_generated").mkdir(parents=True)
    (tmp_path / "docs" / "_generated" / "publication_records.md").write_text(
        render_publication_records_doc(tmp_path, records),
        encoding="utf-8",
    )

    differences = check_publication_records_doc(tmp_path, update_github_readme=True)

    readme_rel = (tmp_path / ".github" / "README.md").relative_to(tmp_path)
    assert any(diff.endswith(f"missing {readme_rel}") for diff in differences)


def test_check_reports_stale_standalone_blocks(tmp_path: Path) -> None:
    """Standalone identity blocks that don't match the rendered block are reported."""
    _scaffold_all_public_projects(tmp_path)
    records = load_publication_records(tmp_path)
    (tmp_path / "docs" / "_generated").mkdir(parents=True)
    (tmp_path / "docs" / "_generated" / "publication_records.md").write_text(
        render_publication_records_doc(tmp_path, records),
        encoding="utf-8",
    )
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github" / "README.md").write_text(
        "\n".join(["before", render_github_readme_publication_block(records), "after"]),
        encoding="utf-8",
    )
    # Deliberately leave standalone blocks unsynced (just the H1).

    differences = check_publication_records_doc(tmp_path, update_github_readme=True)

    assert any("standalone publication identity blocks drifted" in d for d in differences)


def test_check_accepts_in_sync_repo(tmp_path: Path) -> None:
    """A fully-synced repo produces zero differences."""
    _scaffold_all_public_projects(tmp_path)
    records = load_publication_records(tmp_path)
    _sync_standalone_blocks(records)
    (tmp_path / "docs" / "_generated").mkdir(parents=True)
    (tmp_path / "docs" / "_generated" / "publication_records.md").write_text(
        render_publication_records_doc(tmp_path, records),
        encoding="utf-8",
    )
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github" / "README.md").write_text(
        "\n".join(["before", render_github_readme_publication_block(records), "after"]),
        encoding="utf-8",
    )

    differences = check_publication_records_doc(tmp_path, update_github_readme=True)

    assert differences == []


# ---------------------------------------------------------------------------
# render_publication_records_doc — formatting edge cases
# ---------------------------------------------------------------------------


def test_render_with_explicit_generated_at(tmp_path: Path) -> None:
    """An explicit ``generated_at`` timestamp appears when ``refreshed_external=True``."""
    _scaffold_all_public_projects(tmp_path)
    records = load_publication_records(tmp_path)
    ts = datetime(2025, 1, 15, 12, 30, 0, tzinfo=timezone.utc)

    rendered = render_publication_records_doc(tmp_path, records, generated_at=ts, refreshed_external=True)

    assert "2025-01-15T12:30:00+00:00" in rendered


def test_render_refreshed_external_text(tmp_path: Path) -> None:
    """``refreshed_external=True`` surfaces the refresh timestamp text."""
    _scaffold_all_public_projects(tmp_path)
    records = load_publication_records(tmp_path)

    rendered = render_publication_records_doc(tmp_path, records, refreshed_external=True)

    assert "refreshed at" in rendered
    assert "not refreshed in this run" not in rendered


def test_render_not_refreshed_external_text(tmp_path: Path) -> None:
    """``refreshed_external=False`` (default) surfaces the 'not refreshed' text."""
    _scaffold_all_public_projects(tmp_path)
    records = load_publication_records(tmp_path)

    rendered = render_publication_records_doc(tmp_path, records)

    assert "not refreshed in this run" in rendered


def test_render_local_source_paths_section(tmp_path: Path) -> None:
    """The Local Source Paths section includes per-project path links."""
    _scaffold_all_public_projects(tmp_path)
    records = load_publication_records(tmp_path)

    rendered = render_publication_records_doc(tmp_path, records)

    assert "## Local Source Paths" in rendered
    assert "manuscript/config.yaml" in rendered
    assert "CITATION.cff" in rendered
    assert ".zenodo.json" in rendered


def test_render_doi_roles_section(tmp_path: Path) -> None:
    """The DOI Roles section is present and documents each role."""
    _scaffold_all_public_projects(tmp_path)
    records = load_publication_records(tmp_path)

    rendered = render_publication_records_doc(tmp_path, records)

    assert "## DOI Roles" in rendered
    assert "publication.doi" in rendered
    assert "publication.version_doi" in rendered
    assert "publication.version_record" in rendered
    assert "publication.github_repository" in rendered
    assert "publication.published_artifacts" in rendered


def test_render_coverage_summary_counts(tmp_path: Path) -> None:
    """The coverage summary section reports correct counts."""
    _scaffold_all_public_projects(tmp_path)
    records = load_publication_records(tmp_path)

    rendered = render_publication_records_doc(tmp_path, records)

    assert f"Public exemplars indexed: **{len(records)}**" in rendered
    assert f"Standalone guides present: **{len(records)}/{len(records)}**" in rendered
    additional = sum(len(r.published_artifacts) for r in records)
    assert f"Additional publication locations declared: **{additional}**" in rendered


def test_render_missing_standalone_guide(tmp_path: Path) -> None:
    """A missing STANDALONE.md is rendered as 'missing' in the matrix."""
    _scaffold_all_public_projects(tmp_path)
    first = PUBLIC_PROJECT_NAMES[0]
    (tmp_path / "projects" / first / "STANDALONE.md").unlink()
    records = load_publication_records(tmp_path)

    rendered = render_publication_records_doc(tmp_path, records)

    assert "missing" in rendered


def test_render_missing_codemeta(tmp_path: Path) -> None:
    """A missing codemeta.json is rendered as 'missing' in local source paths."""
    _scaffold_all_public_projects(tmp_path)
    first = PUBLIC_PROJECT_NAMES[0]
    (tmp_path / "projects" / first / "codemeta.json").unlink()
    records = load_publication_records(tmp_path)

    rendered = render_publication_records_doc(tmp_path, records)

    assert "missing" in rendered


# ---------------------------------------------------------------------------
# render_github_readme_publication_block / replace_github_readme_publication_block
# ---------------------------------------------------------------------------


def test_render_github_readme_block_contains_markers(tmp_path: Path) -> None:
    """The GitHub README block is wrapped in BEGIN/END markers."""
    _scaffold_all_public_projects(tmp_path)
    records = load_publication_records(tmp_path)

    block = render_github_readme_publication_block(records)

    assert block.startswith(README_BLOCK_BEGIN)
    assert block.rstrip().endswith(README_BLOCK_END)
    assert "Full generated matrix" in block
    for name in PUBLIC_PROJECT_NAMES:
        assert f"../projects/{name}/" in block


def test_replace_github_readme_block_no_markers_raises() -> None:
    """``replace_github_readme_publication_block`` raises ValueError when markers absent."""
    with pytest.raises(ValueError, match="Missing publication records markers"):
        replace_github_readme_publication_block("no markers here", "new block")


def test_replace_github_readme_block_idempotent(tmp_path: Path) -> None:
    """Replacing the block twice produces identical output."""
    _scaffold_all_public_projects(tmp_path)
    records = load_publication_records(tmp_path)
    block = render_github_readme_publication_block(records)
    source = "\n".join(["before", block, "after"])

    once = replace_github_readme_publication_block(source, block)
    twice = replace_github_readme_publication_block(once, block)

    assert once == twice


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def test_markdown_table_rows_parses_pipe_rows() -> None:
    """``_markdown_table_rows`` extracts cell values from pipe-delimited rows."""
    text = "\n".join(
        [
            "| col1 | col2 |",
            "| --- | --- |",
            "| a | b |",
            "not a row",
            "| c | d |",
        ]
    )
    rows = _markdown_table_rows(text)
    assert rows == [["col1", "col2"], ["a", "b"], ["c", "d"]]


def test_markdown_table_rows_skips_separator() -> None:
    """Separator rows (all dashes) are skipped."""
    text = "| --- | --- | --- |"
    assert _markdown_table_rows(text) == []


def test_markdown_table_rows_empty() -> None:
    """Empty text returns no rows."""
    assert _markdown_table_rows("") == []


def test_row_map_differences_identical() -> None:
    """Identical row maps produce no differences."""
    current = {"a": ("1", "2"), "b": ("3", "4")}
    assert _row_map_differences("label", current, dict(current)) == []


def test_row_map_differences_missing() -> None:
    """Missing keys in current are reported."""
    expected = {"a": ("1",), "b": ("2",)}
    current = {"a": ("1",)}
    diffs = _row_map_differences("label", current, expected)
    assert len(diffs) == 1
    assert "missing=" in diffs[0]
    assert "b" in diffs[0]


def test_row_map_differences_extra() -> None:
    """Extra keys in current are reported."""
    expected = {"a": ("1",)}
    current = {"a": ("1",), "c": ("3",)}
    diffs = _row_map_differences("label", current, expected)
    assert len(diffs) == 1
    assert "extra=" in diffs[0]
    assert "c" in diffs[0]


def test_row_map_differences_changed() -> None:
    """Changed values are reported."""
    expected = {"a": ("1",)}
    current = {"a": ("2",)}
    diffs = _row_map_differences("label", current, expected)
    assert len(diffs) == 1
    assert "changed=" in diffs[0]
    assert "a" in diffs[0]


def test_publication_matrix_source_rows_extracts_template_projects(tmp_path: Path) -> None:
    """``_publication_matrix_source_rows`` extracts rows for ``templates/*`` projects."""
    _scaffold_all_public_projects(tmp_path)
    records = load_publication_records(tmp_path)
    rendered = render_publication_records_doc(tmp_path, records)

    rows = _publication_matrix_source_rows(rendered)

    assert len(rows) == len(PUBLIC_PROJECT_NAMES)
    for name in PUBLIC_PROJECT_NAMES:
        assert name in rows
        assert len(rows[name]) == 6


def test_publication_matrix_source_rows_skips_non_template_rows() -> None:
    """Rows that don't start with ``templates/`` are excluded."""
    text = "\n".join(
        [
            "| `templates/foo` | 1.0 | guide | repo | tag | doi | vdoi | loc | zver | status |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
            "| `other/bar` | 2.0 | guide | repo | tag | doi | vdoi | loc | zver | status |",
        ]
    )
    rows = _publication_matrix_source_rows(text)
    assert "templates/foo" in rows
    assert "other/bar" not in rows


def test_local_source_path_rows_extracts_template_projects(tmp_path: Path) -> None:
    """``_local_source_path_rows`` extracts source-path rows for ``templates/*``."""
    _scaffold_all_public_projects(tmp_path)
    records = load_publication_records(tmp_path)
    rendered = render_publication_records_doc(tmp_path, records)

    rows = _local_source_path_rows(rendered)

    assert len(rows) == len(PUBLIC_PROJECT_NAMES)
    for name in PUBLIC_PROJECT_NAMES:
        assert name in rows
        assert len(rows[name]) == 5


def test_github_readme_source_rows_extracts_template_projects(tmp_path: Path) -> None:
    """``_github_readme_source_rows`` extracts rows from the README block."""
    _scaffold_all_public_projects(tmp_path)
    records = load_publication_records(tmp_path)
    block = render_github_readme_publication_block(records)
    readme_text = "\n".join(["# README", "", block, "", "footer"])

    rows = _github_readme_source_rows(readme_text)

    assert len(rows) == len(PUBLIC_PROJECT_NAMES)
    for name in PUBLIC_PROJECT_NAMES:
        assert name in rows
        assert len(rows[name]) == 6


def test_github_readme_source_rows_no_block() -> None:
    """When markers are absent, ``_github_readme_source_rows`` returns empty."""
    assert _github_readme_source_rows("no markers here") == {}


# ---------------------------------------------------------------------------
# PublicationRecord computed properties — additional edge cases
# ---------------------------------------------------------------------------


def _make_record(**overrides: object) -> PublicationRecord:
    defaults: dict[str, object] = dict(
        project_name="test_project",
        title="Test",
        paper_version="1.0.0",
        authors=("Author",),
        concept_doi="",
        version_doi="",
        version_record="",
        github_repository="",
        repository_url="",
        published_artifacts=(),
        standalone_path=Path("/tmp/STANDALONE.md"),
        config_path=Path("/tmp/config.yaml"),
        citation_path=Path("/tmp/CITATION.cff"),
        zenodo_json_path=Path("/tmp/.zenodo.json"),
        codemeta_path=Path("/tmp/codemeta.json"),
    )
    defaults.update(overrides)
    return PublicationRecord(**defaults)  # type: ignore[arg-type]


def test_github_repo_slug_from_monorepo_url_is_empty() -> None:
    """A monorepo ``/tree/`` URL does not produce a standalone repo slug."""
    record = _make_record(
        repository_url="https://github.com/docxology/template/tree/main/projects/templates/template_madlib"
    )
    assert record.github_repo_slug == ""
    assert record.is_monorepo_publication_path is True
    assert record.monorepo_slug == "docxology/template"


def test_github_url_path_from_non_github_url() -> None:
    """A non-GitHub URL returns an empty ``github_url_path``."""
    record = _make_record(repository_url="https://osf.io/12345/")
    assert record.github_url_path == ""
    assert record.github_display_label == ""
    assert record.github_display_url == ""


def test_github_display_label_monorepo_path() -> None:
    """Monorepo path display label includes 'path' suffix."""
    record = _make_record(
        repository_url="https://github.com/docxology/template/tree/main/projects/templates/template_madlib"
    )
    assert "docxology/template path" in record.github_display_label
    assert record.github_display_url == record.repository_url


def test_declared_location_count_no_locations() -> None:
    """A record with no GitHub URL, no DOI, and no artifacts has zero locations."""
    record = _make_record()
    assert record.declared_location_count == 0


def test_sidecar_status_with_multiple_findings() -> None:
    """Multiple sidecar findings are joined with semicolons."""
    record = _make_record(sidecar_findings=("missing STANDALONE.md", "missing CITATION.cff"))
    assert "missing STANDALONE.md" in record.sidecar_status
    assert "missing CITATION.cff" in record.sidecar_status
    assert "; " in record.sidecar_status


def test_external_status_includes_all_three_status_lines() -> None:
    """``external_status`` includes GitHub repo, release, and Zenodo statuses."""
    record = _make_record(github_repository="docxology/test")
    record.github_repo_status = "200"
    record.github_release_status = "200"
    record.zenodo_status = "not published separately"

    status = record.external_status
    assert "GitHub repo 200" in status
    assert "GitHub release 200" in status
    assert "Zenodo not published separately" in status


# ---------------------------------------------------------------------------
# _relative_link
# ---------------------------------------------------------------------------


def test_relative_link_from_generated_dir(tmp_path: Path) -> None:
    """``_relative_link`` prepends ``../../`` when emitting from ``_generated`` dir."""
    repo_root = tmp_path
    from_dir = repo_root / "docs" / "_generated"
    from_dir.mkdir(parents=True)
    target = repo_root / "projects" / "templates" / "template_test" / "STANDALONE.md"
    target.parent.mkdir(parents=True)
    target.write_text("x", encoding="utf-8")

    rel = _relative_link(target, repo_root, from_dir)

    assert rel.startswith("../../")
    assert "projects/templates/template_test/STANDALONE.md" in rel


def test_relative_link_from_root(tmp_path: Path) -> None:
    """``_relative_link`` returns a plain relative path when not from ``_generated``."""
    repo_root = tmp_path
    from_dir = repo_root / "docs"
    from_dir.mkdir(parents=True)
    target = repo_root / "projects" / "foo" / "config.yaml"
    target.parent.mkdir(parents=True)
    target.write_text("x", encoding="utf-8")

    rel = _relative_link(target, repo_root, from_dir)

    assert rel == "projects/foo/config.yaml"


# ---------------------------------------------------------------------------
# write + check round-trip
# ---------------------------------------------------------------------------


def test_write_then_check_is_in_sync(tmp_path: Path) -> None:
    """Writing then checking produces zero differences (round-trip)."""
    _scaffold_all_public_projects(tmp_path)
    github_dir = tmp_path / ".github"
    github_dir.mkdir()
    (github_dir / "README.md").write_text(
        "\n".join(["# Template", "", README_BLOCK_BEGIN, "stale", README_BLOCK_END, ""]),
        encoding="utf-8",
    )

    write_publication_records_doc(tmp_path, update_github_readme=True)

    differences = check_publication_records_doc(tmp_path, update_github_readme=True)
    assert differences == []


def test_write_then_check_with_refreshed_external(tmp_path: Path) -> None:
    """Writing with ``refreshed_external=True`` then checking with the same flag is in sync."""
    _scaffold_all_public_projects(tmp_path)
    records = load_publication_records(tmp_path)
    _sync_standalone_blocks(records)
    for record in records:
        record.github_repo_status = "monorepo path"
        record.github_release_status = "covered by root release"
        record.zenodo_status = "not published separately"
    github_dir = tmp_path / ".github"
    github_dir.mkdir()
    (github_dir / "README.md").write_text(
        "\n".join(["# Template", "", render_github_readme_publication_block(records), ""]),
        encoding="utf-8",
    )
    (tmp_path / "docs" / "_generated").mkdir(parents=True)
    (tmp_path / "docs" / "_generated" / "publication_records.md").write_text(
        render_publication_records_doc(tmp_path, records, refreshed_external=True),
        encoding="utf-8",
    )

    differences = check_publication_records_doc(tmp_path, refresh_external=False, update_github_readme=True)
    assert differences == []
