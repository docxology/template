"""Tests for template.metrics module."""

from __future__ import annotations

from pathlib import Path

from template.introspection import ModuleInfo
from template.metrics import (
    build_manuscript_metrics_dict,
    build_module_inventory_table,
    count_docs_markdown_files,
    count_docs_subdirs,
    count_test_functions,
    format_count,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


class TestCountTestFunctions:
    """Tests for count_test_functions()."""

    def test_returns_zero_for_missing_directory(self, tmp_path: Path) -> None:
        assert count_test_functions(tmp_path / "missing") == 0

    def test_counts_def_test_functions(self, tmp_path: Path) -> None:
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_one.py").write_text(
            "def test_a():\n    pass\n\ndef helper():\n    pass\n",
            encoding="utf-8",
        )
        (tests_dir / "test_two.py").write_text(
            "def test_b():\n    pass\n\ndef test_c():\n    pass\n",
            encoding="utf-8",
        )
        (tests_dir / "nontest.py").write_text("def test_ignored():\n    pass\n", encoding="utf-8")
        assert count_test_functions(tests_dir) == 3


class TestDocsCounters:
    """Tests for docs counters."""

    def test_count_docs_markdown_files(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        (docs / "a").mkdir(parents=True)
        (docs / "a" / "file.md").write_text("# x", encoding="utf-8")
        (docs / "b.md").write_text("# y", encoding="utf-8")
        (docs / "__pycache__").mkdir()
        (docs / "__pycache__" / "z.md").write_text("# z", encoding="utf-8")
        assert count_docs_markdown_files(tmp_path) == 2

    def test_count_docs_subdirs(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        (docs / "x").mkdir(parents=True)
        (docs / "y").mkdir()
        (docs / "file.md").write_text("# f", encoding="utf-8")
        assert count_docs_subdirs(tmp_path) == 2


class TestFormatCount:
    """Tests for format_count()."""

    def test_small_number_plain(self) -> None:
        assert format_count(42) == "42"

    def test_small_number_approx(self) -> None:
        assert format_count(42, approx=True) == "~42"

    def test_large_number_plain(self) -> None:
        assert format_count(2950) == "2,950"

    def test_large_number_approx(self) -> None:
        assert format_count(2950, approx=True) == "~3,000"


class TestBuildModuleInventoryTable:
    """Tests for build_module_inventory_table()."""

    def test_table_contains_header_and_rows(self) -> None:
        modules = [
            ModuleInfo(
                name="core",
                path=Path("/tmp/core"),
                python_file_count=10,
                has_init=True,
                has_agents_md=True,
                has_readme_md=True,
                public_symbols=[],
            ),
            ModuleInfo(
                name="validation",
                path=Path("/tmp/validation"),
                python_file_count=7,
                has_init=True,
                has_agents_md=False,
                has_readme_md=True,
                public_symbols=[],
            ),
        ]
        table = build_module_inventory_table(modules)
        assert "| Module | Python Files | Has AGENTS.md | Has README.md | Key Exports |" in table
        assert "| `core` | 10 | ✓ | ✓ | `get_logger`, `load_config`, `TemplateError` |" in table
        assert "| `validation` | 7 | — | ✓ | PDF validation, Markdown checking, CLI |" in table


class TestBuildManuscriptMetricsDict:
    """Integration-style tests for build_manuscript_metrics_dict()."""

    def test_returns_expected_keys_and_values(self) -> None:
        metrics = build_manuscript_metrics_dict(REPO_ROOT)
        assert "module_count" in metrics
        assert "infra_test_count" in metrics
        assert "module_inventory_table" in metrics
        assert "generated_at" in metrics
        assert "project_code_project_test_count" in metrics
        assert isinstance(metrics["module_count"], int)
        assert isinstance(metrics["infra_test_count"], int)
        assert isinstance(metrics["module_inventory_table"], str)
        assert len(metrics["module_inventory_table"].strip()) > 0
