"""Tests for infrastructure.validation.output.pipeline — testable functions."""


from infrastructure.validation.output.pipeline import generate_validation_report


class TestGenerateValidationReport:
    def test_all_passed(self, tmp_path, monkeypatch):
        # Monkeypatch _REPO_ROOT so it doesn't use the real repo
        import infrastructure.validation.output.pipeline as mod
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)

        # Create the output dir
        out_dir = tmp_path / "projects" / "test" / "output" / "reports"
        out_dir.mkdir(parents=True)

        checks = [
            ("PDF validation", True),
            ("Markdown validation", True),
            ("Output structure", True),
        ]
        result = generate_validation_report(checks, [], {}, project_name="test")
        assert result["summary"]["all_passed"] is True
        assert result["summary"]["passed"] == 3
        assert result["summary"]["failed"] == 0
        assert result["recommendations"] == []

    def test_pdf_failed(self, tmp_path, monkeypatch):
        import infrastructure.validation.output.pipeline as mod
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)

        out_dir = tmp_path / "projects" / "test" / "output" / "reports"
        out_dir.mkdir(parents=True)

        checks = [
            ("PDF validation", False),
            ("Markdown validation", True),
        ]
        result = generate_validation_report(checks, [], {}, project_name="test")
        assert result["summary"]["failed"] == 1
        recs = result["recommendations"]
        assert any(r["priority"] == "high" and "PDF" in r["issue"] for r in recs)

    def test_markdown_failed(self, tmp_path, monkeypatch):
        import infrastructure.validation.output.pipeline as mod
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)

        out_dir = tmp_path / "projects" / "test" / "output" / "reports"
        out_dir.mkdir(parents=True)

        checks = [("Markdown validation", False)]
        result = generate_validation_report(checks, [], {}, project_name="test")
        recs = result["recommendations"]
        assert any(r["priority"] == "medium" for r in recs)

    def test_output_structure_failed(self, tmp_path, monkeypatch):
        import infrastructure.validation.output.pipeline as mod
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)

        out_dir = tmp_path / "projects" / "test" / "output" / "reports"
        out_dir.mkdir(parents=True)

        checks = [("Output structure", False)]
        result = generate_validation_report(checks, [], {}, project_name="test")
        recs = result["recommendations"]
        assert any(r["priority"] == "high" and "Missing" in r["issue"] for r in recs)

    def test_figure_issues(self, tmp_path, monkeypatch):
        import infrastructure.validation.output.pipeline as mod
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)

        out_dir = tmp_path / "projects" / "test" / "output" / "reports"
        out_dir.mkdir(parents=True)

        checks = [("PDF validation", True)]
        figure_issues = ["Missing figure: fig1.png", "Unregistered: fig2.png"]
        result = generate_validation_report(checks, figure_issues, {}, project_name="test")
        recs = result["recommendations"]
        assert any("figure" in r["issue"].lower() for r in recs)

    def test_fallback_json_save(self, tmp_path, monkeypatch):
        import infrastructure.validation.output.pipeline as mod
        monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)

        out_dir = tmp_path / "projects" / "test" / "output" / "reports"
        out_dir.mkdir(parents=True)

        checks = [("PDF validation", True)]
        result = generate_validation_report(checks, [], {}, project_name="test")
        # The function tries to import save_validation_report; if it fails, it falls back
        # Either way, check the result structure
        assert "timestamp" in result
        assert "checks" in result
        assert "summary" in result
