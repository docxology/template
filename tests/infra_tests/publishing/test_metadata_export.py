"""Tests for metadata export helpers and CLI."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from infrastructure.publishing import metadata_export_cli
from infrastructure.publishing.metadata_export import (
    build_citation_cff,
    build_codemeta,
    build_codemeta_json,
    build_zenodo,
    build_zenodo_json,
    write_metadata_files,
    write_metadata_for_config_path,
)


def test_book_title_fallback_for_booklength_projects(tmp_path: Path) -> None:
    """Book-length exemplars declare the title under ``book:`` not ``paper:``.

    Regression for PUB-1: template_textbook published as 'Untitled Research'
    because the metadata builder only read ``paper.title``.
    """
    from infrastructure.publishing.metadata_from_config import publication_metadata_from_config_dict

    config = {"book": {"title": "The Template Textbook", "version": "1.0"}}
    md = publication_metadata_from_config_dict(config, config_path=tmp_path / "config.yaml", allow_draft_abstract=True)
    assert md.title == "The Template Textbook"


def test_build_metadata_with_full_config() -> None:
    config = {
        "paper": {
            "title": "Convergence Analysis of Gradient Descent Optimization",
            "version": "2.2",
            "date": "2026-05-27",
        },
        "authors": [
            {
                "name": "Research Template Author",
                "orcid": "0000-0000-0000-1234",
                "email": "author@example.org",
                "affiliation": "Research Template Institute",
                "corresponding": True,
            },
            {
                "name": "Grace Hopper",
                "orcid": "0000-0000-0000-5678",
                "email": "grace@example.org",
                "affiliation": "Department of Computational Mathematics",
                "corresponding": False,
            },
        ],
        "publication": {
            "doi": "https://doi.org/10.5281/zenodo.123456",
            "github_repository": "docxology/template_code_project",
            "year": "2026",
        },
        "keywords": ["optimization", "gradient descent"],
        "metadata": {"license": "MIT"},
    }

    citation = yaml.safe_load(build_citation_cff(config, released_date="2026-05-27"))
    assert citation["cff-version"] == "1.2.0"
    assert citation["title"] == config["paper"]["title"]
    assert citation["authors"][0]["given-names"] == "Research Template"
    assert citation["authors"][0]["family-names"] == "Author"
    assert citation["authors"][1]["given-names"] == "Grace"
    assert citation["authors"][1]["family-names"] == "Hopper"
    assert citation["doi"] == "10.5281/zenodo.123456"
    assert citation["repository-code"] == "https://github.com/docxology/template_code_project"
    assert citation["date-released"] == "2026-05-27"

    codemeta = build_codemeta(config, released_date="2026-05-27")
    assert codemeta["@type"] == "SoftwareSourceCode"
    assert codemeta["license"] == "https://spdx.org/licenses/MIT"
    assert codemeta["identifier"] == "10.5281/zenodo.123456"
    assert codemeta["author"][0]["@id"] == "https://orcid.org/0000-0000-0000-1234"
    assert codemeta["author"][0]["affiliation"]["name"] == "Research Template Institute"
    assert codemeta["dateModified"] == "2026-05-27"

    zenodo = build_zenodo(config)
    assert zenodo["upload_type"] == "software"
    assert zenodo["creators"][0]["name"] == "Author, Research Template"
    assert zenodo["creators"][1]["name"] == "Hopper, Grace"
    assert zenodo["related_identifiers"] == [
        {
            "relation": "isVersionOf",
            "identifier": "10.5281/zenodo.123456",
            "scheme": "doi",
        }
    ]


def test_empty_doi_is_omitted_everywhere() -> None:
    config = {
        "paper": {"title": "Example", "version": "1.0", "date": "2026-05-27"},
        "authors": [{"name": "Example Author"}],
        "publication": {"doi": "   "},
        "keywords": ["example"],
        "metadata": {"license": "MIT"},
    }

    citation = yaml.safe_load(build_citation_cff(config, released_date="2026-05-27"))
    codemeta = build_codemeta(config, released_date="2026-05-27")
    zenodo = build_zenodo(config)

    assert "doi" not in citation
    assert "identifier" not in codemeta
    assert "related_identifiers" not in zenodo


def test_mononym_author_omits_cff_given_names() -> None:
    config = {
        "paper": {"title": "Mononym Example", "version": "1.0", "date": "2026-05-27"},
        "authors": [{"name": "Plato"}],
        "publication": {"doi": ""},
        "keywords": [],
        "metadata": {"license": "MIT"},
    }

    citation = yaml.safe_load(build_citation_cff(config, released_date="2026-05-27"))
    zenodo = build_zenodo(config)

    assert citation["authors"][0]["family-names"] == "Plato"
    assert "given-names" not in citation["authors"][0]
    assert zenodo["creators"][0]["name"] == "Plato"


def test_missing_license_falls_back_to_cc_by() -> None:
    config = {
        "paper": {"title": "License Example", "version": "1.0", "date": "2026-05-27"},
        "authors": [{"name": "Example Author"}],
        "publication": {"doi": ""},
        "keywords": [],
    }

    citation = yaml.safe_load(build_citation_cff(config, released_date="2026-05-27"))
    codemeta = build_codemeta(config, released_date="2026-05-27")
    zenodo = build_zenodo(config)

    assert citation["license"] == "CC-BY-4.0"
    assert codemeta["license"] == "https://spdx.org/licenses/CC-BY-4.0"
    assert zenodo["license"] == "CC-BY-4.0"


def test_repository_url_takes_precedence_over_github_repository() -> None:
    config = {
        "paper": {"title": "Repo Example", "version": "1.0", "date": "2026-05-27"},
        "authors": [{"name": "Example Author"}],
        "publication": {
            "doi": "",
            "github_repository": "docxology/template",
            "repository_url": "https://example.org/custom/repo",
        },
        "keywords": [],
        "metadata": {"license": "MIT"},
    }

    citation = yaml.safe_load(build_citation_cff(config, released_date="2026-05-27"))
    codemeta = build_codemeta(config, released_date="2026-05-27")

    assert citation["repository-code"] == "https://example.org/custom/repo"
    assert codemeta["codeRepository"] == "https://example.org/custom/repo"


def test_metadata_output_is_deterministic() -> None:
    config = {
        "paper": {"title": "Deterministic Example", "version": "1.0", "date": ""},
        "authors": [{"name": "Ada Lovelace"}],
        "publication": {"doi": "doi:10.5281/zenodo.42", "github_repository": "docxology/template"},
        "keywords": ["deterministic", "metadata"],
        "metadata": {"license": "Apache-2.0"},
    }

    cff_one = build_citation_cff(config, released_date="2026-01-02")
    cff_two = build_citation_cff(config, released_date="2026-01-02")
    codemeta_one = build_codemeta_json(config, released_date="2026-01-02")
    codemeta_two = build_codemeta_json(config, released_date="2026-01-02")
    zenodo_one = build_zenodo_json(config)
    zenodo_two = build_zenodo_json(config)

    assert cff_one == cff_two
    assert codemeta_one == codemeta_two
    assert zenodo_one == zenodo_two


def test_write_metadata_files_writes_three_files(tmp_path: Path) -> None:
    config = {
        "paper": {"title": "Writer Example", "version": "1.0", "date": ""},
        "authors": [{"name": "Example Author"}],
        "publication": {"doi": "", "github_repository": "docxology/template"},
        "keywords": ["writer"],
        "metadata": {"license": "MIT"},
    }
    out_dir = tmp_path / "nested" / "exports"

    written = write_metadata_files(
        config,
        out_dir,
        released_date="2026-05-27",
    )

    assert [path.name for path in written] == [".zenodo.json", "CITATION.cff", "codemeta.json"]
    assert all(path.exists() for path in written)
    assert out_dir.is_dir()


def test_write_metadata_for_config_path_uses_load_config(tmp_path: Path) -> None:
    config_dir = tmp_path / "project" / "manuscript"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "config.yaml"
    config_path.write_text(
        "\n".join(
            [
                "paper:",
                "  title: Config Path Example",
                "  version: '1.0'",
                "  date: ''",
                "authors:",
                "  - name: Example Author",
                "publication:",
                "  doi: ''",
                "keywords:",
                "  - config",
                "metadata:",
                "  license: MIT",
                "",
            ]
        ),
        encoding="utf-8",
    )

    written = write_metadata_for_config_path(
        config_path,
        tmp_path / "exports",
        released_date="2026-05-27",
    )

    assert len(written) == 3
    assert all(path.exists() for path in written)


def test_cli_main_writes_files_with_repo_override(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "infrastructure").mkdir(parents=True)
    project_root = repo_root / "projects" / "active" / "demo"
    manuscript_dir = project_root / "manuscript"
    manuscript_dir.mkdir(parents=True)
    config_path = manuscript_dir / "config.yaml"
    config_path.write_text(
        "\n".join(
            [
                "paper:",
                "  title: Demo Project",
                "  version: '1.2'",
                "  date: '2026-04-05'",
                "authors:",
                "  - name: Demo Author",
                "    orcid: 0000-0000-0000-9999",
                "publication:",
                "  doi: ''",
                "  repository_url: https://example.org/demo",
                "keywords:",
                "  - demo",
                "metadata:",
                "  license: BSD-3-Clause",
                "",
            ]
        ),
        encoding="utf-8",
    )
    out_dir = tmp_path / "out"

    exit_code = metadata_export_cli.main(
        [
            "metadata-export",
            "--project",
            "demo",
            "--repo-root",
            str(repo_root),
            "--out",
            str(out_dir),
        ]
    )

    assert exit_code == 0
    assert (out_dir / "CITATION.cff").exists()
    assert (out_dir / "codemeta.json").exists()
    assert (out_dir / ".zenodo.json").exists()


def test_cli_main_returns_one_for_missing_config(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "infrastructure").mkdir(parents=True)
    (repo_root / "projects").mkdir(parents=True)

    exit_code = metadata_export_cli.main(
        [
            "metadata-export",
            "--project",
            "missing",
            "--repo-root",
            str(repo_root),
        ]
    )

    assert exit_code == 1


def test_serialized_json_helpers_include_trailing_newline() -> None:
    config = {
        "paper": {"title": "JSON Example", "version": "1.0", "date": "2026-05-27"},
        "authors": [{"name": "Example Author"}],
        "publication": {"doi": ""},
        "keywords": [],
        "metadata": {"license": "MIT"},
    }

    codemeta_json = build_codemeta_json(config, released_date="2026-05-27")
    zenodo_json = build_zenodo_json(config)

    assert codemeta_json.endswith("\n")
    assert zenodo_json.endswith("\n")
    assert json.loads(codemeta_json)["name"] == "JSON Example"
    assert json.loads(zenodo_json)["title"] == "JSON Example"
