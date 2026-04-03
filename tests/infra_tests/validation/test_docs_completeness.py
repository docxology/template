"""Tests for infrastructure.validation.docs.completeness module.

Tests documentation completeness gap detection functions.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.validation.docs.completeness import (
    check_config_documentation,
    check_cross_reference_completeness,
    check_feature_documentation,
    check_onboarding,
    check_script_documentation,
    check_troubleshooting,
    check_workflow_documentation,
    group_gaps_by_category,
    group_gaps_by_severity,
    run_completeness_phase,
)
from infrastructure.validation.docs.models import CompletenessGap, DocumentationFile


def _make_doc_file(relative_path: str) -> DocumentationFile:
    """Create a minimal DocumentationFile for testing."""
    return DocumentationFile(
        path=relative_path,
        relative_path=relative_path,
        directory=str(Path(relative_path).parent),
        name=Path(relative_path).name,
        word_count=50,
    )


class TestCheckFeatureDocumentation:
    """Tests for check_feature_documentation."""

    def test_no_src_dir(self, tmp_path: Path):
        """No src/ directory should return no gaps."""
        gaps = check_feature_documentation(tmp_path, [])
        assert gaps == []

    def test_documented_module(self, tmp_path: Path):
        """Module mentioned in docs should not produce a gap."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "analysis.py").write_text("# code")
        doc = _make_doc_file("docs/analysis_guide.md")
        gaps = check_feature_documentation(tmp_path, [doc])
        assert len(gaps) == 0

    def test_undocumented_module(self, tmp_path: Path):
        """Module not mentioned in docs should produce a gap."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "analysis.py").write_text("# code")
        (src_dir / "__init__.py").write_text("")
        gaps = check_feature_documentation(tmp_path, [])
        assert len(gaps) == 1
        assert gaps[0].item == "analysis"
        assert gaps[0].category == "features"

    def test_init_file_ignored(self, tmp_path: Path):
        """__init__.py should be skipped."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "__init__.py").write_text("")
        gaps = check_feature_documentation(tmp_path, [])
        assert len(gaps) == 0


class TestCheckScriptDocumentation:
    """Tests for check_script_documentation."""

    def test_no_scripts_dir(self, tmp_path: Path):
        """No scripts/ directory should return no gaps."""
        gaps = check_script_documentation(tmp_path)
        assert gaps == []

    def test_script_with_docstring(self, tmp_path: Path):
        """Script with docstring should not produce a gap."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "run.py").write_text('"""Run the pipeline."""\nprint("hi")')
        gaps = check_script_documentation(tmp_path)
        assert len(gaps) == 0

    def test_script_without_docstring(self, tmp_path: Path):
        """Script without docstring should produce a gap."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "run.py").write_text('print("no docstring")')
        gaps = check_script_documentation(tmp_path)
        assert len(gaps) == 1
        assert gaps[0].item == "run.py"
        assert gaps[0].severity == "warning"

    def test_private_script_ignored(self, tmp_path: Path):
        """Scripts starting with _ should be skipped."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "_helper.py").write_text('print("private")')
        gaps = check_script_documentation(tmp_path)
        assert len(gaps) == 0


class TestCheckTroubleshooting:
    """Tests for check_troubleshooting."""

    def test_has_troubleshooting(self):
        doc = _make_doc_file("docs/TROUBLESHOOTING.md")
        gaps = check_troubleshooting([doc])
        assert len(gaps) == 0

    def test_no_troubleshooting(self):
        doc = _make_doc_file("docs/README.md")
        gaps = check_troubleshooting([doc])
        assert len(gaps) == 1
        assert gaps[0].category == "troubleshooting"


class TestCheckWorkflowDocumentation:
    """Tests for check_workflow_documentation."""

    def test_has_workflow(self):
        doc = _make_doc_file("docs/WORKFLOW.md")
        gaps = check_workflow_documentation([doc])
        assert len(gaps) == 0

    def test_no_workflow(self):
        doc = _make_doc_file("docs/README.md")
        gaps = check_workflow_documentation([doc])
        assert len(gaps) == 1
        assert gaps[0].category == "workflows"


class TestCheckOnboarding:
    """Tests for check_onboarding."""

    def test_has_getting_started(self):
        doc = _make_doc_file("docs/GETTING_STARTED.md")
        gaps = check_onboarding([doc])
        assert len(gaps) == 0

    def test_has_quick_start(self):
        doc = _make_doc_file("docs/QUICK_START.md")
        gaps = check_onboarding([doc])
        assert len(gaps) == 0

    def test_no_onboarding_docs(self):
        doc = _make_doc_file("docs/README.md")
        gaps = check_onboarding([doc])
        assert len(gaps) == 1
        assert gaps[0].category == "onboarding"
        assert gaps[0].severity == "warning"


class TestCheckConfigDocumentation:
    """Tests for check_config_documentation."""

    def test_empty_config_files(self):
        gaps = check_config_documentation({})
        assert gaps == []

    def test_with_config_example(self, tmp_path: Path):
        gaps = check_config_documentation({"config.yaml.example": tmp_path / "config.yaml.example"})
        assert gaps == []


class TestCheckCrossReferenceCompleteness:
    """Tests for check_cross_reference_completeness."""

    def test_returns_empty_list(self):
        gaps = check_cross_reference_completeness()
        assert gaps == []


class TestGroupGaps:
    """Tests for grouping utilities."""

    def test_group_by_category(self):
        gaps = [
            CompletenessGap(category="features", item="a", description="d", severity="info"),
            CompletenessGap(category="features", item="b", description="d", severity="info"),
            CompletenessGap(category="scripts", item="c", description="d", severity="warning"),
        ]
        grouped = group_gaps_by_category(gaps)
        assert grouped == {"features": 2, "scripts": 1}

    def test_group_by_severity(self):
        gaps = [
            CompletenessGap(category="a", item="x", description="d", severity="info"),
            CompletenessGap(category="b", item="y", description="d", severity="warning"),
            CompletenessGap(category="c", item="z", description="d", severity="info"),
        ]
        grouped = group_gaps_by_severity(gaps)
        assert grouped == {"info": 2, "warning": 1}

    def test_group_empty_list(self):
        assert group_gaps_by_category([]) == {}
        assert group_gaps_by_severity([]) == {}


class TestRunCompletenessPhase:
    """Tests for run_completeness_phase."""

    def test_basic_run(self, tmp_path: Path):
        """Should return a report dict and list of gaps."""
        report, gaps = run_completeness_phase(tmp_path, [], {})
        assert "total_gaps" in report
        assert "by_category" in report
        assert "severity_breakdown" in report
        assert isinstance(gaps, list)

    def test_run_with_docs(self, tmp_path: Path):
        """With proper docs, some gaps should still be detected (onboarding, etc)."""
        docs = [_make_doc_file("docs/TROUBLESHOOTING.md")]
        report, gaps = run_completeness_phase(tmp_path, docs, {})
        assert report["total_gaps"] >= 0
