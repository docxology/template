#!/usr/bin/env python3
"""Tests for infrastructure.publishing.status_report.

No mocks: every test writes a real ``config.yaml`` / README into ``tmp_path``
and exercises the compile/render/update functions and the CLI on real files.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.publishing.registry import PLATFORM_REGISTRY
from infrastructure.publishing.status_report import (
    BLOCK_END,
    BLOCK_START,
    PublicationState,
    compile_publishing_status,
    main,
    render_status_block,
    render_status_markdown,
    status_report_is_current,
    update_readme_block,
)

CONFIG_YAML = """\
paper:
  title: "Refinement of Gold: A Metallurgical Analogy"
  version: "0.1.0"

authors:
  - name: "Daniel Ari Friedman"
    orcid: "0000-0001-6232-9096"

publication:
  doi: "10.5281/zenodo.20931955"
  version_doi: "10.5281/zenodo.20938523"
  version_record: "https://zenodo.org/records/20938523"
  github_repository: "docxology/template_gold_refinement"
  repository_url: "https://github.com/docxology/template_gold_refinement"

keywords:
  - "gold refining"
  - "assaying"

metadata:
  license: "MIT"
"""


def _project(tmp_path: Path, config_text: str = CONFIG_YAML) -> Path:
    root = tmp_path / "proj"
    (root / "manuscript").mkdir(parents=True)
    (root / "manuscript" / "config.yaml").write_text(config_text, encoding="utf-8")
    return root


def test_compile_lists_every_registry_platform(tmp_path: Path) -> None:
    report = compile_publishing_status(_project(tmp_path))
    assert len(report.platforms) == len(PLATFORM_REGISTRY)
    assert {p.name for p in report.platforms} == {p.name for p in PLATFORM_REGISTRY}


def test_compile_extracts_durable_metadata(tmp_path: Path) -> None:
    report = compile_publishing_status(_project(tmp_path))
    assert report.title == "Refinement of Gold: A Metallurgical Analogy"
    assert report.version == "0.1.0"
    assert report.authors == ("Daniel Ari Friedman",)
    assert report.license == "MIT"
    assert report.concept_doi == "10.5281/zenodo.20931955"
    assert report.version_doi == "10.5281/zenodo.20938523"
    assert report.version_record == "https://zenodo.org/records/20938523"
    assert report.github_repo == "docxology/template_gold_refinement"
    assert report.keywords == ("gold refining", "assaying")


def test_zenodo_and_github_are_published_rest_available(tmp_path: Path) -> None:
    report = compile_publishing_status(_project(tmp_path))
    by_name = {p.name: p for p in report.platforms}
    assert by_name["zenodo"].state is PublicationState.PUBLISHED
    assert by_name["zenodo"].reference == "https://doi.org/10.5281/zenodo.20931955"
    assert by_name["github"].state is PublicationState.PUBLISHED
    assert by_name["github"].reference == "https://github.com/docxology/template_gold_refinement"
    assert by_name["osf"].state is PublicationState.AVAILABLE
    assert by_name["huggingface_hub"].state is PublicationState.AVAILABLE
    assert report.published_count == 2


def test_published_override_upgrades_platform(tmp_path: Path) -> None:
    cid_url = "https://gateway.pinata.cloud/ipfs/bafyTEST"
    report = compile_publishing_status(_project(tmp_path), published={"ipfs_pinata": cid_url})
    by_name = {p.name: p for p in report.platforms}
    assert by_name["ipfs_pinata"].state is PublicationState.PUBLISHED
    assert by_name["ipfs_pinata"].reference == cid_url
    # Override raises published count from 2 (zenodo+github) to 3.
    assert report.published_count == 3


def test_config_published_artifacts_mark_platforms(tmp_path: Path) -> None:
    # Inject a published_artifacts map inside the publication block.
    cfg = CONFIG_YAML.replace(
        '  github_repository: "docxology/template_gold_refinement"\n',
        '  github_repository: "docxology/template_gold_refinement"\n'
        "  published_artifacts:\n"
        '    osf: "https://osf.io/u485p/"\n'
        '    ipfs_pinata: "https://gateway.pinata.cloud/ipfs/QmTEST"\n',
    )
    report = compile_publishing_status(_project(tmp_path, cfg))
    by_name = {p.name: p for p in report.platforms}
    assert by_name["osf"].state is PublicationState.PUBLISHED
    assert by_name["osf"].reference == "https://osf.io/u485p/"
    assert by_name["ipfs_pinata"].state is PublicationState.PUBLISHED
    # zenodo + github (from config) + osf + ipfs_pinata = 4 published.
    assert report.published_count == 4


def test_caller_published_overrides_config(tmp_path: Path) -> None:
    cfg = CONFIG_YAML.replace(
        '  github_repository: "docxology/template_gold_refinement"\n',
        '  github_repository: "docxology/template_gold_refinement"\n'
        "  published_artifacts:\n"
        '    osf: "https://osf.io/CONFIG/"\n',
    )
    report = compile_publishing_status(
        _project(tmp_path, cfg), published={"osf": "https://osf.io/CALLER/"}
    )
    by_name = {p.name: p for p in report.platforms}
    assert by_name["osf"].reference == "https://osf.io/CALLER/"


def test_version_record_backfills_from_doi(tmp_path: Path) -> None:
    cfg = CONFIG_YAML.replace('  version_record: "https://zenodo.org/records/20938523"\n', "")
    report = compile_publishing_status(_project(tmp_path, cfg))
    assert report.version_record == "https://zenodo.org/records/20938523"


def test_missing_config_falls_back_to_project_name(tmp_path: Path) -> None:
    root = tmp_path / "myproject"
    root.mkdir()
    report = compile_publishing_status(root)
    assert report.title == "myproject"
    assert report.concept_doi is None
    assert report.published_count == 0


def test_render_markdown_contains_metadata_and_table(tmp_path: Path) -> None:
    md = render_status_markdown(compile_publishing_status(_project(tmp_path)))
    assert "Refinement of Gold" in md
    assert "https://doi.org/10.5281/zenodo.20931955" in md
    assert "| Platform | Tier | Status | Reference | Credentials |" in md
    assert "✅ published" in md
    assert "⚪ available" in md
    assert "Status legend" in md
    # Every registry platform appears as a table row.
    for platform in PLATFORM_REGISTRY:
        assert f"| {platform.name} |" in md


def test_render_block_wraps_markers(tmp_path: Path) -> None:
    block = render_status_block(compile_publishing_status(_project(tmp_path)))
    assert block.startswith(BLOCK_START)
    assert block.endswith(BLOCK_END)


def test_update_readme_replaces_between_markers(tmp_path: Path) -> None:
    report = compile_publishing_status(_project(tmp_path))
    readme = f"# Title\n\n## Publishing\n\n{BLOCK_START}\nOLD CONTENT\n{BLOCK_END}\n\nAfter.\n"
    new_text, changed = update_readme_block(readme, report)
    assert changed
    assert "OLD CONTENT" not in new_text
    assert "Refinement of Gold" in new_text
    assert new_text.endswith("After.\n")
    assert status_report_is_current(new_text, report)


def test_update_readme_is_idempotent(tmp_path: Path) -> None:
    report = compile_publishing_status(_project(tmp_path))
    readme = f"{BLOCK_START}\nx\n{BLOCK_END}\n"
    once, _ = update_readme_block(readme, report)
    twice, changed = update_readme_block(once, report)
    assert not changed
    assert once == twice


def test_update_readme_inserts_after_heading(tmp_path: Path) -> None:
    report = compile_publishing_status(_project(tmp_path))
    readme = "# Title\n\n## Publication and rendering\n\nSome prose.\n"
    new_text, changed = update_readme_block(readme, report, init_after_heading="## Publication and rendering")
    assert changed
    assert BLOCK_START in new_text and BLOCK_END in new_text
    assert new_text.index("## Publication and rendering") < new_text.index(BLOCK_START)
    assert "Some prose." in new_text


def test_update_readme_raises_without_markers_or_heading(tmp_path: Path) -> None:
    report = compile_publishing_status(_project(tmp_path))
    with pytest.raises(ValueError):
        update_readme_block("# No markers here\n", report)


def test_update_readme_raises_when_heading_absent(tmp_path: Path) -> None:
    report = compile_publishing_status(_project(tmp_path))
    with pytest.raises(ValueError):
        update_readme_block("# Title\n", report, init_after_heading="## Missing")


def test_cli_print_mode(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = _project(tmp_path)
    rc = main(["--project", str(root)])
    assert rc == 0
    out = capsys.readouterr().out
    assert BLOCK_START in out and BLOCK_END in out


def test_cli_write_then_check(tmp_path: Path) -> None:
    root = _project(tmp_path)
    readme = root / "README.md"
    readme.write_text("# Gold\n\n## Publication and rendering\n\nprose\n", encoding="utf-8")

    # check before write -> stale -> exit 1
    assert main(["--project", str(root), "--check"]) == 1

    # write inserts the block after the heading
    assert main(["--project", str(root), "--write", "--init-after", "## Publication and rendering"]) == 0
    assert BLOCK_START in readme.read_text(encoding="utf-8")

    # check after write -> current -> exit 0
    assert main(["--project", str(root), "--check"]) == 0

    # second write is a no-op
    assert main(["--project", str(root), "--write"]) == 0


def test_cli_published_override_marks_platform(tmp_path: Path) -> None:
    root = _project(tmp_path)
    readme = root / "README.md"
    readme.write_text(f"# x\n\n{BLOCK_START}\n{BLOCK_END}\n", encoding="utf-8")
    rc = main(
        [
            "--project",
            str(root),
            "--write",
            "--published",
            "osf=https://osf.io/abcde/",
        ]
    )
    assert rc == 0
    text = readme.read_text(encoding="utf-8")
    assert "https://osf.io/abcde/" in text
