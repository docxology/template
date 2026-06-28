"""Tests for src.dashboard — interactive HTML dashboard."""

from __future__ import annotations

from dashboard import build_dashboard_html, write_dashboard


class TestBuildDashboardHtml:
    def test_returns_html_string(self, tmp_path):
        html = build_dashboard_html(tmp_path)
        assert isinstance(html, str)
        assert "<html" in html.lower()
        assert "Gold Refinement Dashboard" in html

    def test_contains_stage_table(self, tmp_path):
        html = build_dashboard_html(tmp_path)
        assert "Refinery Stages" in html
        assert "ore" in html.lower()

    def test_contains_metrics(self, tmp_path):
        html = build_dashboard_html(tmp_path)
        assert "Final Purity" in html
        assert "Generated Tokens" in html
        assert "Evidence Claims" in html

    def test_source_date_epoch_pins_generated_footer(self, tmp_path, monkeypatch):
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "0")
        html = build_dashboard_html(tmp_path)
        assert "Generated: 1970-01-01T00:00:00Z" in html

    def test_with_data_files(self, tmp_path):
        """Dashboard should load data files when available."""
        import json

        data_dir = tmp_path / "output" / "data"
        reports_dir = tmp_path / "output" / "reports"
        data_dir.mkdir(parents=True)
        reports_dir.mkdir(parents=True)

        (data_dir / "refinery_results.json").write_text(
            json.dumps({"stage_count": 5, "final_purity": 0.999999999}),
            encoding="utf-8",
        )
        (reports_dir / "token_plan.json").write_text(
            json.dumps({"total_tokens": 8, "section_counts": {"methodology": 5}}),
            encoding="utf-8",
        )
        (reports_dir / "claim_support_registry.json").write_text(
            json.dumps({"total_claims": 4, "supported_claims": 4, "entries": []}),
            encoding="utf-8",
        )

        html = build_dashboard_html(tmp_path)
        assert "Refinery Stages" in html


class TestWriteDashboard:
    def test_writes_html_file(self, tmp_path):
        out = write_dashboard(tmp_path)
        assert out.exists()
        assert out.suffix == ".html"
        content = out.read_text(encoding="utf-8")
        assert "Gold Refinement Dashboard" in content

    def test_custom_output_path(self, tmp_path):
        custom = tmp_path / "custom" / "dashboard.html"
        out = write_dashboard(tmp_path, output_path=custom)
        assert out == custom
        assert out.exists()


class TestDashboardPreloadedData:
    """Dashboard with all three data blobs pre-loaded (not loaded from disk)."""

    def test_preloaded_refinery_token_evidence(self, tmp_path):
        """When all three data args are provided, dashboard skips disk reads."""
        html = build_dashboard_html(
            tmp_path,
            refinery_data={
                "stage_count": 1,
                "final_purity": 0.42,
                "final_karat": "18K (custom)",
                "total_purity_gain": 0.32,
                "is_nine_nines_certified": False,
                "purity_sequence": [0.1, 0.42],
                "stages": [
                    {
                        "order": 1,
                        "name": "alchemy",
                        "input_purity": 0.1,
                        "output_purity": 0.42,
                        "karat": "18K (custom)",
                        "metallurgical_operation": "custom operation",
                        "manuscript_operation": "custom operation",
                    }
                ],
            },
            token_data={
                "total_tokens": 8,
                "section_counts": {"methodology": 5},
                "category_counts": {"metallurgical_terms": 3, "manuscript_terms": 2},
            },
            evidence_data={
                "total_claims": 3,
                "supported_claims": 3,
                "entries": [
                    {
                        "claim_name": "monotone-purity",
                        "evidence_source": "src/refinery.py",
                        "boundary": "local",
                        "supported": True,
                    },
                ],
            },
        )
        assert "Gold Refinement Dashboard" in html
        assert "alchemy" in html
        assert "42.0000%" in html
        assert "18K (custom)" in html
        assert "metallurgical_terms" in html
        assert "monotone-purity" in html
        assert "✅" in html
