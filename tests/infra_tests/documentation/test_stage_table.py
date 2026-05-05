"""Tests for ``infrastructure.documentation.stage_table``.

Real I/O only (no mocks). Synthetic ``pipeline.yaml`` is written to ``tmp_path``
and the rendered table is asserted against the expected column structure.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.documentation.stage_table import (
    build_stage_table,
    inject_stage_table,
)


@pytest.fixture
def synthetic_yaml(tmp_path: Path) -> Path:
    """Write a small pipeline.yaml with three stages for table assertions."""
    yaml_path = tmp_path / "pipeline.yaml"
    yaml_path.write_text(
        """
stages:
  - name: Clean Output Directories
    method: _run_clean_outputs
    tags: [core, clean]
    failure_mode: soft fail

  - name: Environment Setup
    script: 00_setup_environment.py
    depends_on: [Clean Output Directories]
    tags: [core]
    failure_mode: hard fail

  - name: LLM Translations
    script: 06_llm_review.py
    args: [--translations-only]
    allow_skip: true
    tags: [llm]
    failure_mode: skipped if Ollama absent
""".strip(),
        encoding="utf-8",
    )
    return yaml_path


class TestBuildStageTable:
    """Verify column structure and stage indexing."""

    def test_table_has_four_columns(self, synthetic_yaml: Path) -> None:
        table = build_stage_table(synthetic_yaml)
        header_line = next(
            line for line in table.splitlines() if line.startswith("| Stage |")
        )
        # Four columns + two pipe terminators = 5 pipes.
        assert header_line.count("|") == 5
        assert "Script" in header_line
        assert "Tags" in header_line
        assert "Failure mode" in header_line

    def test_stages_are_zero_indexed(self, synthetic_yaml: Path) -> None:
        table = build_stage_table(synthetic_yaml)
        # First data row has stage **0** (Clean Output Directories).
        assert "| **0** Clean Output Directories" in table
        # Third data row has stage **2** (LLM Translations).
        assert "| **2** LLM Translations" in table

    def test_script_cell_uses_method_for_builtins(self, synthetic_yaml: Path) -> None:
        table = build_stage_table(synthetic_yaml)
        assert "built-in `_run_clean_outputs`" in table

    def test_script_cell_includes_args(self, synthetic_yaml: Path) -> None:
        table = build_stage_table(synthetic_yaml)
        assert "`06_llm_review.py --translations-only`" in table

    def test_failure_mode_passes_through(self, synthetic_yaml: Path) -> None:
        table = build_stage_table(synthetic_yaml)
        assert "skipped if Ollama absent" in table
        assert "hard fail" in table

    def test_default_failure_mode_when_missing(self, tmp_path: Path) -> None:
        """No failure_mode → falls back to a sensible default from tags."""
        yaml_path = tmp_path / "pipeline.yaml"
        yaml_path.write_text(
            "stages:\n"
            "  - name: Mystery Stage\n"
            "    script: foo.py\n"
            "    tags: [llm]\n",
            encoding="utf-8",
        )
        table = build_stage_table(yaml_path)
        # llm-tag default = "skipped if Ollama absent"
        assert "skipped if Ollama absent" in table

    def test_caption_warns_about_index_vs_filename(self, synthetic_yaml: Path) -> None:
        table = build_stage_table(synthetic_yaml)
        assert "0-based" in table
        assert "scripts/NN_*.py" in table

    def test_missing_yaml_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            build_stage_table(tmp_path / "does_not_exist.yaml")

    def test_malformed_yaml_raises(self, tmp_path: Path) -> None:
        yaml_path = tmp_path / "pipeline.yaml"
        yaml_path.write_text("not_stages: []\n", encoding="utf-8")
        with pytest.raises(ValueError):
            build_stage_table(yaml_path)


class TestInjectStageTable:
    """Verify marker round-trip and idempotence."""

    def test_round_trip_with_existing_markers(self, tmp_path: Path) -> None:
        target = tmp_path / "doc.md"
        target.write_text(
            "# Title\n\n"
            "Some prose.\n\n"
            "<!-- BEGIN:STAGE_TABLE -->\n"
            "OLD CONTENT\n"
            "<!-- END:STAGE_TABLE -->\n\n"
            "More prose.\n",
            encoding="utf-8",
        )
        changed = inject_stage_table(target, "NEW CONTENT")
        assert changed is True
        new_text = target.read_text(encoding="utf-8")
        assert "NEW CONTENT" in new_text
        assert "OLD CONTENT" not in new_text
        # Surrounding prose preserved.
        assert "Some prose." in new_text
        assert "More prose." in new_text

    def test_idempotent_second_run(self, tmp_path: Path) -> None:
        target = tmp_path / "doc.md"
        target.write_text(
            "<!-- BEGIN:STAGE_TABLE -->\n"
            "OLD\n"
            "<!-- END:STAGE_TABLE -->\n",
            encoding="utf-8",
        )
        first = inject_stage_table(target, "STABLE")
        second = inject_stage_table(target, "STABLE")
        assert first is True
        assert second is False  # No change on second run.

    def test_appends_when_markers_missing(self, tmp_path: Path) -> None:
        target = tmp_path / "doc.md"
        target.write_text("# Title\n\nNo markers here.\n", encoding="utf-8")
        changed = inject_stage_table(target, "NEW BLOCK")
        assert changed is True
        text = target.read_text(encoding="utf-8")
        assert "<!-- BEGIN:STAGE_TABLE -->" in text
        assert "<!-- END:STAGE_TABLE -->" in text
        assert "NEW BLOCK" in text

    def test_custom_marker_label(self, tmp_path: Path) -> None:
        target = tmp_path / "doc.md"
        target.write_text(
            "<!-- BEGIN:CUSTOM -->\nx\n<!-- END:CUSTOM -->\n",
            encoding="utf-8",
        )
        changed = inject_stage_table(target, "Y", marker="CUSTOM")
        assert changed is True
        assert "Y" in target.read_text(encoding="utf-8")

    def test_missing_target_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            inject_stage_table(tmp_path / "missing.md", "x")

    def test_full_roundtrip_with_real_yaml(self, synthetic_yaml: Path, tmp_path: Path) -> None:
        target = tmp_path / "doc.md"
        target.write_text(
            "# Pipeline\n\n<!-- BEGIN:STAGE_TABLE -->\n_old_\n<!-- END:STAGE_TABLE -->\n",
            encoding="utf-8",
        )
        table = build_stage_table(synthetic_yaml)
        assert inject_stage_table(target, table) is True
        text = target.read_text(encoding="utf-8")
        assert "Stage" in text and "Failure mode" in text
        # Idempotence: regenerating with no input change → no diff.
        assert inject_stage_table(target, table) is False
