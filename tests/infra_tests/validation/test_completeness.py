"""Tests for infrastructure.validation.docs.completeness — comprehensive coverage."""


from infrastructure.validation.docs.completeness import (
    check_feature_documentation,
    check_script_documentation,
    check_config_documentation,
    check_troubleshooting,
    check_workflow_documentation,
    check_onboarding,
    check_cross_reference_completeness,
    group_gaps_by_category,
    group_gaps_by_severity,
    run_completeness_phase,
)
from infrastructure.validation.docs.models import CompletenessGap, DocumentationFile


def _make_doc(relative_path="docs/foo.md"):
    return DocumentationFile(
        path=f"/repo/{relative_path}",
        relative_path=relative_path,
        directory="docs",
        name=relative_path.split("/")[-1],
    )


# ---------------------------------------------------------------------------
# check_feature_documentation
# ---------------------------------------------------------------------------


class TestCheckFeatureDocumentation:
    def test_no_src_dir(self, tmp_path):
        gaps = check_feature_documentation(tmp_path, [])
        assert gaps == []

    def test_module_documented(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "analysis.py").write_text("x = 1")
        doc = _make_doc("docs/analysis.md")
        gaps = check_feature_documentation(tmp_path, [doc])
        assert gaps == []

    def test_module_not_documented(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "hidden.py").write_text("x = 1")
        gaps = check_feature_documentation(tmp_path, [])
        assert len(gaps) == 1
        assert gaps[0].item == "hidden"
        assert gaps[0].category == "features"

    def test_init_ignored(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "__init__.py").write_text("")
        gaps = check_feature_documentation(tmp_path, [])
        assert gaps == []

    def test_match_uses_module_stem_in_relative_path(self, tmp_path):
        """The check tests `module_name in doc_file.relative_path.lower()`.
        module_name is the file stem (case-preserved), so a mixed-case stem
        won't match a lowercased path unless the stem itself is lowercase."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "analysis.py").write_text("x = 1")
        doc = _make_doc("docs/analysis_guide.md")
        gaps = check_feature_documentation(tmp_path, [doc])
        assert gaps == []

    def test_mixed_case_module_not_matched_by_lowercase_path(self, tmp_path):
        """Module stem 'MyModule' is not in 'docs/mymodule_guide.md' (case mismatch)."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "MyModule.py").write_text("x = 1")
        doc = _make_doc("docs/mymodule_guide.md")
        gaps = check_feature_documentation(tmp_path, [doc])
        assert len(gaps) == 1


# ---------------------------------------------------------------------------
# check_script_documentation
# ---------------------------------------------------------------------------


class TestCheckScriptDocumentation:
    def test_no_scripts_dir(self, tmp_path):
        gaps = check_script_documentation(tmp_path)
        assert gaps == []

    def test_script_with_docstring(self, tmp_path):
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "run.py").write_text('"""This script runs."""\nprint("go")')
        gaps = check_script_documentation(tmp_path)
        assert gaps == []

    def test_script_without_docstring(self, tmp_path):
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "run.py").write_text("print('go')")
        gaps = check_script_documentation(tmp_path)
        assert len(gaps) == 1
        assert gaps[0].item == "run.py"
        assert gaps[0].category == "scripts"

    def test_private_script_skipped(self, tmp_path):
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "_helper.py").write_text("x = 1")
        gaps = check_script_documentation(tmp_path)
        assert gaps == []

    def test_repo_utilities_dir(self, tmp_path):
        utils = tmp_path / "repo_utilities"
        utils.mkdir()
        (utils / "tool.py").write_text("no docstring here")
        gaps = check_script_documentation(tmp_path)
        assert len(gaps) == 1
        assert gaps[0].item == "tool.py"


# ---------------------------------------------------------------------------
# check_config_documentation
# ---------------------------------------------------------------------------


class TestCheckConfigDocumentation:
    def test_empty_config(self):
        gaps = check_config_documentation({})
        assert gaps == []

    def test_with_config_example(self, tmp_path):
        gaps = check_config_documentation({"config.yaml.example": tmp_path / "config.yaml.example"})
        assert gaps == []


# ---------------------------------------------------------------------------
# check_troubleshooting / workflow / onboarding
# ---------------------------------------------------------------------------


class TestCheckTroubleshooting:
    def test_has_troubleshooting(self):
        doc = _make_doc("docs/TROUBLESHOOTING.md")
        gaps = check_troubleshooting([doc])
        assert gaps == []

    def test_missing_troubleshooting(self):
        doc = _make_doc("docs/readme.md")
        gaps = check_troubleshooting([doc])
        assert len(gaps) == 1
        assert gaps[0].category == "troubleshooting"


class TestCheckWorkflowDocumentation:
    def test_has_workflow(self):
        doc = _make_doc("docs/WORKFLOW.md")
        gaps = check_workflow_documentation([doc])
        assert gaps == []

    def test_missing_workflow(self):
        gaps = check_workflow_documentation([_make_doc("docs/other.md")])
        assert len(gaps) == 1
        assert gaps[0].category == "workflows"


class TestCheckOnboarding:
    def test_has_getting_started(self):
        doc = _make_doc("docs/GETTING_STARTED.md")
        gaps = check_onboarding([doc])
        assert gaps == []

    def test_has_quick_start(self):
        doc = _make_doc("docs/QUICK_START.md")
        gaps = check_onboarding([doc])
        assert gaps == []

    def test_missing_onboarding(self):
        gaps = check_onboarding([_make_doc("docs/readme.md")])
        assert len(gaps) == 1
        assert gaps[0].category == "onboarding"


class TestCheckCrossReferenceCompleteness:
    def test_returns_empty(self):
        gaps = check_cross_reference_completeness()
        assert gaps == []


# ---------------------------------------------------------------------------
# Grouping helpers
# ---------------------------------------------------------------------------


class TestGroupGaps:
    def test_by_category(self):
        gaps = [
            CompletenessGap(category="features", item="a", description="x"),
            CompletenessGap(category="features", item="b", description="y"),
            CompletenessGap(category="scripts", item="c", description="z"),
        ]
        result = group_gaps_by_category(gaps)
        assert result == {"features": 2, "scripts": 1}

    def test_by_severity(self):
        gaps = [
            CompletenessGap(category="a", item="x", description="d", severity="warning"),
            CompletenessGap(category="b", item="y", description="d", severity="info"),
            CompletenessGap(category="c", item="z", description="d", severity="warning"),
        ]
        result = group_gaps_by_severity(gaps)
        assert result == {"warning": 2, "info": 1}

    def test_empty_gaps(self):
        assert group_gaps_by_category([]) == {}
        assert group_gaps_by_severity([]) == {}


# ---------------------------------------------------------------------------
# run_completeness_phase (orchestrator)
# ---------------------------------------------------------------------------


class TestRunCompletenessPhase:
    def test_basic_run(self, tmp_path):
        report, gaps = run_completeness_phase(tmp_path, [], {})
        assert "total_gaps" in report
        assert "by_category" in report
        assert "severity_breakdown" in report
        assert isinstance(gaps, list)

    def test_finds_gaps(self, tmp_path):
        # No troubleshooting, no workflow, no onboarding
        report, gaps = run_completeness_phase(tmp_path, [], {})
        assert report["total_gaps"] >= 3  # troubleshooting + workflow + onboarding

    def test_documented_reduces_gaps(self, tmp_path):
        docs = [
            _make_doc("docs/TROUBLESHOOTING.md"),
            _make_doc("docs/WORKFLOW.md"),
            _make_doc("docs/GETTING_STARTED.md"),
        ]
        report, gaps = run_completeness_phase(tmp_path, docs, {})
        # No troubleshooting/workflow/onboarding gaps
        categories = {g.category for g in gaps}
        assert "troubleshooting" not in categories
        assert "workflows" not in categories
        assert "onboarding" not in categories

    def test_with_undocumented_module(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "secret.py").write_text("x = 1")
        report, gaps = run_completeness_phase(tmp_path, [], {})
        feature_gaps = [g for g in gaps if g.category == "features"]
        assert len(feature_gaps) == 1
        assert feature_gaps[0].item == "secret"
