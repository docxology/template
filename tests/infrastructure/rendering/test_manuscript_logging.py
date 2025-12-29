"""Tests for manuscript logging."""
import pytest
from pathlib import Path
from infrastructure.rendering.manuscript_discovery import discover_manuscript_files
from infrastructure.core.logging_utils import get_logger


def test_all_filenames_logged(tmp_path, caplog):
    """Verify all discovered files are logged by name."""
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()

    # Create test files
    files = ["01_intro.md", "02_methods.md", "S01_supp.md", "99_refs.md"]
    for fname in files:
        (manuscript_dir / fname).write_text(f"# {fname}\n\nContent here.")

    result = discover_manuscript_files(manuscript_dir)

    # Verify each filename appears in logs
    log_text = caplog.text
    for fname in files:
        assert fname in log_text, f"File {fname} not in logs"

    # Verify bullet points used
    assert "•" in log_text, "Bullet points not used in output"


def test_no_hardcoded_warnings(tmp_path, caplog):
    """Verify no 'missing expected sections' warnings for minimal projects."""
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()

    # Create minimal project (just 2 files)
    (manuscript_dir / "01_intro.md").write_text("# Intro")
    (manuscript_dir / "02_conclusion.md").write_text("# Conclusion")

    discover_manuscript_files(manuscript_dir)

    log_text = caplog.text
    assert "Missing expected" not in log_text
    assert "⚠️" not in log_text or "Figures directory" in log_text  # Only figures warning allowed


def test_categorization_logged(tmp_path, caplog):
    """Verify main/supplemental/glossary/refs categories shown."""
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()

    files = {
        "01_intro.md": "Main",
        "S01_supp.md": "Supplemental",
        "98_glossary.md": "Glossary",
        "99_refs.md": "References"
    }

    for fname in files:
        (manuscript_dir / fname).write_text(f"# {fname}")

    discover_manuscript_files(manuscript_dir)

    log_text = caplog.text
    assert "Main sections (1)" in log_text
    assert "Supplemental (1)" in log_text
    assert "Glossary (1)" in log_text
    assert "References (1)" in log_text


def test_latex_files_logged(tmp_path, caplog):
    """Verify LaTeX files are logged separately."""
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()

    # Create markdown and LaTeX files
    (manuscript_dir / "01_intro.md").write_text("# Intro")
    (manuscript_dir / "preamble.tex").write_text("\\usepackage{amsmath}")

    discover_manuscript_files(manuscript_dir)

    log_text = caplog.text
    assert "LaTeX files (1)" in log_text
    assert "preamble.tex" in log_text


def test_other_files_categorized(tmp_path, caplog):
    """Verify uncategorized markdown files go in 'Other' category."""
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()

    # Create files with non-standard naming
    (manuscript_dir / "01_intro.md").write_text("# Intro")
    (manuscript_dir / "custom_section.md").write_text("# Custom")

    discover_manuscript_files(manuscript_dir)

    log_text = caplog.text
    assert "Main sections (1)" in log_text
    assert "Other (1)" in log_text
    assert "custom_section.md" in log_text


def test_empty_directory_handling(tmp_path, caplog):
    """Verify empty directory is handled gracefully."""
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()

    result = discover_manuscript_files(manuscript_dir)

    assert result == []
    log_text = caplog.text
    assert "Discovered 0 manuscript file(s)" in log_text


def test_mixed_file_types(tmp_path, caplog):
    """Test discovery with mixed markdown, LaTeX, and other files."""
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()

    # Create various file types
    files = [
        "01_abstract.md",
        "02_intro.md",
        "S01_supp.md",
        "98_glossary.md",
        "99_refs.md",
        "preamble.tex",
        "config.yaml"  # Should be excluded
    ]

    for fname in files:
        content = f"# {fname}" if fname.endswith('.md') else f"% {fname}"
        (manuscript_dir / fname).write_text(content)

    result = discover_manuscript_files(manuscript_dir)

    log_text = caplog.text
    # Should log markdown files but not config.yaml
    assert "config.yaml" not in log_text
    assert "Main sections (2)" in log_text  # 01_abstract, 02_intro
    assert "Supplemental (1)" in log_text
    assert "Glossary (1)" in log_text
    assert "References (1)" in log_text
    assert "LaTeX files (1)" in log_text

    # Verify correct count
    assert len(result) == 6  # 5 md + 1 tex, excluding config.yaml


def test_case_insensitive_md_detection(tmp_path, caplog):
    """Verify .MD files are detected case-insensitively."""
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()

    # Create files with different case extensions
    (manuscript_dir / "01_intro.md").write_text("# Intro")
    (manuscript_dir / "02_methods.MD").write_text("# Methods")

    discover_manuscript_files(manuscript_dir)

    log_text = caplog.text
    assert "01_intro.md" in log_text
    assert "02_methods.MD" in log_text
    assert "Main sections (2)" in log_text


def test_excluded_files_not_logged(tmp_path, caplog):
    """Verify excluded files (AGENTS.md, README.md, etc.) are not logged."""
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()

    # Create regular and excluded files
    (manuscript_dir / "01_intro.md").write_text("# Intro")
    (manuscript_dir / "AGENTS.md").write_text("# Agents")
    (manuscript_dir / "README.md").write_text("# Readme")
    (manuscript_dir / "preamble.md").write_text("# Preamble")

    discover_manuscript_files(manuscript_dir)

    log_text = caplog.text
    assert "01_intro.md" in log_text
    assert "AGENTS.md" not in log_text
    assert "README.md" not in log_text
    assert "preamble.md" not in log_text  # This should be excluded


def test_file_order_preserved(tmp_path):
    """Verify discovered files maintain proper ordering."""
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()

    # Create files in non-alphabetical order
    files = ["03_results.md", "01_abstract.md", "02_intro.md", "S01_supp.md"]
    for fname in files:
        (manuscript_dir / fname).write_text(f"# {fname}")

    result = discover_manuscript_files(manuscript_dir)

    # Should be ordered: main sections first, then supplemental
    assert len(result) == 4
    # Main sections should be sorted
    assert str(result[0]).endswith("01_abstract.md")
    assert str(result[1]).endswith("02_intro.md")
    assert str(result[2]).endswith("03_results.md")
    assert str(result[3]).endswith("S01_supp.md")