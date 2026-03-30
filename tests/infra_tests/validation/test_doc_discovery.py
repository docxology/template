"""Tests for infrastructure/validation/doc_discovery.py.

Covers find_markdown_files, identify_cross_references, catalog_agents_readme,
find_config_files, create_hierarchy, and run_discovery_phase using real temp directories.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.validation.docs.discovery import (
    catalog_agents_readme,
    create_hierarchy,
    find_config_files,
    find_markdown_files,
    identify_cross_references,
    run_discovery_phase,
)


@pytest.fixture()
def doc_root(tmp_path: Path) -> Path:
    """Create a minimal documentation tree for testing."""
    # Root-level docs
    (tmp_path / "README.md").write_text("# Root\n[link](docs/guide.md)\n")
    (tmp_path / "AGENTS.md").write_text("# Agents\n")

    # docs/ subdirectory
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "guide.md").write_text("# Guide\n[back](../README.md)\n")
    (docs / "api.md").write_text("# API\n")

    # Config file
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")

    return tmp_path


class TestFindMarkdownFiles:
    def test_finds_all_md_files(self, doc_root: Path) -> None:
        files = find_markdown_files(doc_root)
        names = [f.name for f in files]
        assert "README.md" in names
        assert "AGENTS.md" in names
        assert "guide.md" in names
        assert "api.md" in names

    def test_excludes_output_directory(self, tmp_path: Path) -> None:
        (tmp_path / "README.md").write_text("# Root")
        output = tmp_path / "output"
        output.mkdir()
        (output / "generated.md").write_text("# Generated")

        files = find_markdown_files(tmp_path)
        names = [f.name for f in files]
        assert "README.md" in names
        assert "generated.md" not in names

    def test_returns_sorted_list(self, doc_root: Path) -> None:
        files = find_markdown_files(doc_root)
        assert files == sorted(files)

    def test_empty_directory_returns_empty(self, tmp_path: Path) -> None:
        files = find_markdown_files(tmp_path)
        assert files == []


class TestCatalogAgentsReadme:
    def test_finds_agents_and_readme(self, doc_root: Path) -> None:
        md_files = find_markdown_files(doc_root)
        result = catalog_agents_readme(md_files, doc_root)
        assert any("AGENTS.md" in r for r in result)
        assert any("README.md" in r for r in result)

    def test_excludes_other_docs(self, doc_root: Path) -> None:
        md_files = find_markdown_files(doc_root)
        result = catalog_agents_readme(md_files, doc_root)
        assert not any("guide.md" in r for r in result)
        assert not any("api.md" in r for r in result)

    def test_returns_relative_paths(self, doc_root: Path) -> None:
        md_files = find_markdown_files(doc_root)
        result = catalog_agents_readme(md_files, doc_root)
        for r in result:
            assert not Path(r).is_absolute()


class TestFindConfigFiles:
    def test_finds_toml(self, doc_root: Path) -> None:
        configs = find_config_files(doc_root)
        assert "pyproject.toml" in configs

    def test_finds_yaml(self, tmp_path: Path) -> None:
        (tmp_path / "config.yaml").write_text("key: value\n")
        configs = find_config_files(tmp_path)
        assert "config.yaml" in configs

    def test_excludes_venv_configs(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text("[project]\n")
        venv = tmp_path / ".venv"
        venv.mkdir()
        (venv / "config.yaml").write_text("key: value\n")
        configs = find_config_files(tmp_path)
        # The venv config should not be present
        for path in configs.values():
            assert ".venv" not in str(path)


class TestCreateHierarchy:
    def test_returns_dict_keyed_by_directory(self, doc_root: Path) -> None:
        md_files = find_markdown_files(doc_root)
        hierarchy = create_hierarchy(md_files, doc_root)
        assert isinstance(hierarchy, dict)
        assert "root" in hierarchy or "docs" in hierarchy

    def test_root_files_keyed_as_root(self, doc_root: Path) -> None:
        md_files = find_markdown_files(doc_root)
        hierarchy = create_hierarchy(md_files, doc_root)
        assert "root" in hierarchy
        root_files = hierarchy["root"]
        assert any("README.md" in f for f in root_files)

    def test_subdirectory_files_keyed_correctly(self, doc_root: Path) -> None:
        md_files = find_markdown_files(doc_root)
        hierarchy = create_hierarchy(md_files, doc_root)
        assert "docs" in hierarchy
        docs_files = hierarchy["docs"]
        assert any("guide.md" in f for f in docs_files)


class TestIdentifyCrossReferences:
    def test_finds_relative_links(self, doc_root: Path) -> None:
        md_files = find_markdown_files(doc_root)
        refs = identify_cross_references(md_files)
        assert isinstance(refs, set)
        assert len(refs) > 0

    def test_excludes_http_links(self, tmp_path: Path) -> None:
        (tmp_path / "doc.md").write_text("[external](https://example.com)\n")
        md_files = find_markdown_files(tmp_path)
        refs = identify_cross_references(md_files)
        assert not any("http" in r for r in refs)

    def test_excludes_anchor_links(self, tmp_path: Path) -> None:
        (tmp_path / "doc.md").write_text("[section](#heading)\n")
        md_files = find_markdown_files(tmp_path)
        refs = identify_cross_references(md_files)
        assert not any(r.startswith("#") for r in refs)

    def test_empty_directory_returns_empty_set(self, tmp_path: Path) -> None:
        refs = identify_cross_references([])
        assert refs == set()


class TestRunDiscoveryPhase:
    def test_returns_dict_with_expected_keys(self, doc_root: Path) -> None:
        result = run_discovery_phase(doc_root)
        assert isinstance(result, dict)
        expected_keys = [
            "markdown_files",
            "agents_readme_files",
            "config_files",
            "script_files",
            "hierarchy",
            "cross_references",
            "categories",
            "documentation_files",
        ]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"

    def test_markdown_count_matches_files(self, doc_root: Path) -> None:
        result = run_discovery_phase(doc_root)
        actual_files = find_markdown_files(doc_root)
        assert result["markdown_files"] == len(actual_files)

    def test_config_files_count_positive(self, doc_root: Path) -> None:
        result = run_discovery_phase(doc_root)
        assert result["config_files"] >= 1

    def test_documentation_files_list_populated(self, doc_root: Path) -> None:
        result = run_discovery_phase(doc_root)
        assert len(result["documentation_files"]) > 0
