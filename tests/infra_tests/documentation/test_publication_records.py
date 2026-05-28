"""Tests for generated public publication record docs."""

from __future__ import annotations

import json
import re
from pathlib import Path

from infrastructure.documentation.publication_records import (
    README_BLOCK_BEGIN,
    README_BLOCK_END,
    load_publication_records,
    render_github_readme_publication_block,
    render_publication_records_doc,
    replace_github_readme_publication_block,
)
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES


def _scaffold_publication_project(root: Path, name: str, version: str = "1.0.0") -> None:
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


def test_load_publication_records_follows_public_project_scope(tmp_path: Path) -> None:
    """Publication records come from public_scope, not arbitrary projects/ globs."""
    for name in PUBLIC_PROJECT_NAMES:
        _scaffold_publication_project(tmp_path, name)
    _scaffold_publication_project(tmp_path, "private_project")

    records = load_publication_records(tmp_path)

    assert [record.project_name for record in records] == sorted(PUBLIC_PROJECT_NAMES)
    assert {record.github_repository for record in records} == {
        f"docxology/{name}" for name in PUBLIC_PROJECT_NAMES
    }
    assert all(record.sidecar_status == "ok" for record in records)


def test_rendered_publication_docs_include_every_public_record(tmp_path: Path) -> None:
    """The generated markdown and GitHub block expose all public exemplar rows."""
    for name in PUBLIC_PROJECT_NAMES:
        _scaffold_publication_project(tmp_path, name)
    records = load_publication_records(tmp_path)

    generated = render_publication_records_doc(tmp_path, records)
    readme_block = render_github_readme_publication_block(records)

    for name in PUBLIC_PROJECT_NAMES:
        assert f"`{name}`" in generated
        assert f"../projects/{name}/" in readme_block
    assert "Do not edit by hand" in generated
    assert "scripts/generate_publication_records_doc.py --refresh-external" in generated


def test_replace_github_readme_publication_block() -> None:
    """Only the generated block is replaced."""
    replacement = "\n".join([README_BLOCK_BEGIN, "new table", README_BLOCK_END])
    source = "\n".join(["before", README_BLOCK_BEGIN, "old table", README_BLOCK_END, "after"])

    result = replace_github_readme_publication_block(source, replacement)

    assert result == "\n".join(["before", replacement, "after"])
    assert re.search(r"old table", result) is None
