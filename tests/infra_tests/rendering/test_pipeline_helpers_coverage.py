"""Tests for infrastructure.rendering.pipeline — testable helper functions."""


from infrastructure.rendering.pipeline import (
    _resolve_manuscript_dir,
    _validate_latex_packages,
    _log_manuscript_composition,
)
from infrastructure.rendering.latex_validation import ValidationReport


class TestResolveManuscriptDir:
    def test_prefers_injected_dir(self, tmp_path):
        injected = tmp_path / "output" / "manuscript"
        injected.mkdir(parents=True)
        (injected / "01_intro.md").write_text("# Intro")
        source = tmp_path / "manuscript"
        source.mkdir()
        (source / "01_intro.md").write_text("# Source Intro")

        result = _resolve_manuscript_dir(tmp_path)
        assert result == injected

    def test_falls_back_to_source(self, tmp_path):
        source = tmp_path / "manuscript"
        source.mkdir()
        (source / "01_intro.md").write_text("# Intro")

        result = _resolve_manuscript_dir(tmp_path)
        assert result == source

    def test_empty_injected_dir(self, tmp_path):
        injected = tmp_path / "output" / "manuscript"
        injected.mkdir(parents=True)
        # No .md files in injected

        result = _resolve_manuscript_dir(tmp_path)
        assert result == tmp_path / "manuscript"

    def test_no_injected_dir(self, tmp_path):
        result = _resolve_manuscript_dir(tmp_path)
        assert result == tmp_path / "manuscript"


class TestValidateLatexPackages:
    def test_all_required_available(self):
        report = ValidationReport(
            all_required_available=True,
            missing_required=[],
            missing_optional=[],
            required_packages=[],
            optional_packages=[],
        )
        result = _validate_latex_packages(report=report)
        assert result == 0

    def test_missing_required(self):
        report = ValidationReport(
            all_required_available=False,
            missing_required=["multirow", "cleveref"],
            missing_optional=[],
            required_packages=[],
            optional_packages=[],
        )
        result = _validate_latex_packages(report=report)
        assert result == 1

    def test_missing_optional_only(self):
        report = ValidationReport(
            all_required_available=True,
            missing_required=[],
            missing_optional=["tcolorbox", "minted"],
            required_packages=[],
            optional_packages=[],
        )
        result = _validate_latex_packages(report=report)
        assert result == 0


class TestLogManuscriptComposition:
    def test_md_files(self, tmp_path):
        f1 = tmp_path / "01_intro.md"
        f1.write_text("# Introduction\nSome content here.\n")
        f2 = tmp_path / "02_methods.md"
        f2.write_text("# Methods\nOur methodology.\n")
        # Should not raise
        _log_manuscript_composition([f1, f2])

    def test_mixed_files(self, tmp_path):
        md = tmp_path / "paper.md"
        md.write_text("# Paper")
        tex = tmp_path / "extra.tex"
        tex.write_text("\\section{Extra}")
        _log_manuscript_composition([md, tex])

    def test_empty_list(self):
        _log_manuscript_composition([])


class TestValidateLatexPackagesEdgeCases:
    """Additional edge cases for _validate_latex_packages."""

    def test_validation_error_branch(self):
        """Test when validate_preamble_packages raises ValidationError."""
        from infrastructure.rendering.pipeline import _validate_latex_packages

        # Create a report that simulates missing required
        report = ValidationReport(
            all_required_available=False,
            missing_required=["amsmath"],
            missing_optional=["tcolorbox"],
            required_packages=[],
            optional_packages=[],
        )
        result = _validate_latex_packages(report=report)
        assert result == 1

    def test_all_available_no_optional_missing(self):
        report = ValidationReport(
            all_required_available=True,
            missing_required=[],
            missing_optional=[],
            required_packages=[],
            optional_packages=[],
        )
        result = _validate_latex_packages(report=report)
        assert result == 0


class TestRunOverrideScript:
    """Test _run_override_script with real subprocess."""

    def test_override_script_success(self, tmp_path):
        from infrastructure.rendering.pipeline import _run_override_script
        script = tmp_path / "override.py"
        script.write_text("import sys; sys.exit(0)")
        result = _run_override_script(tmp_path, script)
        assert result == 0

    def test_override_script_failure(self, tmp_path):
        from infrastructure.rendering.pipeline import _run_override_script
        script = tmp_path / "override.py"
        script.write_text("import sys; sys.exit(42)")
        result = _run_override_script(tmp_path, script)
        assert result == 42

    def test_override_script_not_found(self, tmp_path):
        from infrastructure.rendering.pipeline import _run_override_script
        script = tmp_path / "nonexistent.py"
        result = _run_override_script(tmp_path, script)
        assert result != 0
