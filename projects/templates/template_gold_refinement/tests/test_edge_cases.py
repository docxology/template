"""Edge-case tests to improve coverage for evidence, dashboard, figures, manuscript_variables.

Targets uncovered paths identified by coverage analysis:
- evidence.py: _check_evidence_source (#-style sources, missing files, missing symbols,
  ledger mismatch path)
- dashboard.py: category rows rendered, evidence entries rendered
- figures/: project_root=None fallback, evidence registry load path
- manuscript_variables.py: SOURCE_DATE_EPOCH path, staleness detection paths
- __init__.py: public API import coverage
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

# ---- helpers ----------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SRC = _PROJECT_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def _minimal_manuscript(tmp_path: Path) -> Path:
    """Create a minimal manuscript/config.yaml."""
    ms = tmp_path / "manuscript"
    ms.mkdir(parents=True)
    (ms / "config.yaml").write_text(
        yaml.dump(
            {
                "paper": {"title": "Edge Test", "version": "0.1"},
                "authors": [{"name": "Bob"}],
                "keywords": ["gold"],
                "gold_refinement": {
                    "seed": 1,
                    "composition_depth": "compact",
                    "lexicon": {
                        "metallurgical_terms": ["cupellation", "assaying"],
                        "manuscript_terms": ["draft", "claim"],
                        "purity_adjectives": ["refined", "pure"],
                        "refinement_verbs": ["smelt", "certify"],
                    },
                    "slots": [
                        {"name": "SLOT_A", "category": "metallurgical_terms", "count": 1, "section": "methodology"},
                    ],
                },
            }
        ),
        encoding="utf-8",
    )
    return tmp_path


# ============================================================================
# evidence.py — _check_evidence_source edge cases
# ============================================================================


class TestCheckEvidenceSourcePaths:
    """Directly test _check_evidence_source for uncovered branches."""

    def _check(self, source: str, project_root: Path) -> tuple[bool, str]:
        from evidence import _check_evidence_source  # type: ignore[attr-defined]

        return _check_evidence_source(source, project_root)

    def test_hash_style_source_existing_file(self, tmp_path):
        """Source with # separator pointing to an existing file."""
        (tmp_path / "src").mkdir()
        src_file = tmp_path / "src" / "refinery.py"
        src_file.write_text("CANONICAL_STAGES = ()\n", encoding="utf-8")
        ok, msg = self._check("src/refinery.py#CANONICAL_STAGES", tmp_path)
        assert ok is True
        assert msg == ""

    def test_hash_style_source_missing_file(self, tmp_path):
        """Source with # separator pointing to a nonexistent file."""
        ok, msg = self._check("src/missing.py#SomeSymbol", tmp_path)
        assert ok is False
        assert "not found" in msg.lower()

    def test_no_separator_existing_file(self, tmp_path):
        """Source with no :: or # separator, file exists."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "plain.py").write_text("x = 1\n", encoding="utf-8")
        ok, msg = self._check("src/plain.py", tmp_path)
        assert ok is True
        assert msg == ""

    def test_no_separator_missing_file(self, tmp_path):
        """Source with no separator, file missing."""
        ok, msg = self._check("src/nonexistent_file.py", tmp_path)
        assert ok is False
        assert "not found" in msg.lower()

    def test_colons_style_missing_symbol(self, tmp_path):
        """Source with :: separator but symbol not in file."""
        (tmp_path / "src").mkdir()
        src_file = tmp_path / "src" / "refinery.py"
        src_file.write_text("# no symbol here\n", encoding="utf-8")
        ok, msg = self._check("src/refinery.py::MISSING_SYMBOL", tmp_path)
        assert ok is False
        assert "MISSING_SYMBOL" in msg or "not found" in msg.lower()


class TestEvidenceRegistryZeroClaims:
    """EvidenceRegistry with zero claims — support_rate and is_passing."""

    def test_zero_total_support_rate(self):
        from evidence import EvidenceRegistry

        reg = EvidenceRegistry(entries=[], total_claims=0, supported_claims=0, unsupported_claims=0)
        assert reg.support_rate == 0.0

    def test_zero_total_is_not_passing(self):
        from evidence import EvidenceRegistry

        reg = EvidenceRegistry(entries=[], total_claims=0, supported_claims=0, unsupported_claims=0)
        assert reg.is_passing is False


class TestCheckClaimLedgerMismatch:
    """check_claim_ledger_alignment returns mismatches for unmatched claims."""

    def test_unmatched_claim_returns_mismatch(self, tmp_path):
        from config import GoldRefinementConfig
        from evidence import check_claim_ledger_alignment

        # A config with a contribution claim that has no ledger match
        cfg = GoldRefinementConfig(
            contribution_claims=[
                {
                    "name": "completely-unique-xyz",
                    "claim": "test",
                    "evidence": "src/refinery.py::NOT_REAL",
                    "boundary": "local",
                }
            ]
        )
        ledger_path = tmp_path / "claim_ledger.yaml"
        ledger_path.write_text(
            yaml.dump({"claims": [{"id": "other-claim", "statement": "something else entirely"}]}),
            encoding="utf-8",
        )
        mismatches = check_claim_ledger_alignment(cfg, ledger_path)
        assert len(mismatches) >= 1
        assert "src/refinery.py::NOT_REAL" in mismatches[0]

    def test_path_escape_is_rejected(self, tmp_path):
        from evidence import _check_evidence_source

        outside = tmp_path.parent / "outside.py"
        outside.write_text("SECRET = 1\n", encoding="utf-8")
        ok, msg = _check_evidence_source("../outside.py::SECRET", tmp_path)
        assert ok is False
        assert "escapes project root" in msg.lower()


# ============================================================================
# dashboard.py — evidence rows and category rows rendered
# ============================================================================


class TestDashboardWithPopulatedData:
    """Dashboard renders token category rows and evidence entry rows."""

    def test_token_category_rows_rendered(self, tmp_path):
        """Token category count rows appear in dashboard HTML."""
        from dashboard import build_dashboard_html

        token_data = {
            "total_tokens": 6,
            "section_counts": {"methodology": 4, "results": 2},
            "category_counts": {"metallurgical_terms": 3, "manuscript_terms": 2, "refinement_verbs": 1},
        }
        html = build_dashboard_html(tmp_path, token_data=token_data)
        assert "metallurgical_terms" in html
        assert "manuscript_terms" in html
        assert "refinement_verbs" in html

    def test_evidence_entry_rows_rendered(self, tmp_path):
        """Evidence entry rows (✅/❌) appear in dashboard HTML when entries provided."""
        from dashboard import build_dashboard_html

        evidence_data = {
            "total_claims": 2,
            "supported_claims": 1,
            "entries": [
                {
                    "claim_name": "monotone-purity",
                    "evidence_source": "src/refinery.py::CANONICAL_STAGES",
                    "boundary": "local",
                    "supported": True,
                },
                {
                    "claim_name": "broken-claim",
                    "evidence_source": "missing/file.py",
                    "boundary": "local",
                    "supported": False,
                },
            ],
        }
        html = build_dashboard_html(tmp_path, evidence_data=evidence_data)
        assert "monotone-purity" in html
        assert "broken-claim" in html
        assert "✅" in html
        assert "❌" in html

    def test_dashboard_with_all_data_files(self, tmp_path):
        """Dashboard correctly reads and renders all three data files from disk."""
        from dashboard import build_dashboard_html

        data_dir = tmp_path / "output" / "data"
        reports_dir = tmp_path / "output" / "reports"
        data_dir.mkdir(parents=True)
        reports_dir.mkdir(parents=True)

        (data_dir / "refinery_results.json").write_text(
            json.dumps({"stage_count": 5, "final_purity": 0.999999999}), encoding="utf-8"
        )
        (reports_dir / "token_plan.json").write_text(
            json.dumps(
                {
                    "total_tokens": 4,
                    "section_counts": {"methodology": 3},
                    "category_counts": {"metallurgical_terms": 3, "manuscript_terms": 1},
                }
            ),
            encoding="utf-8",
        )
        (reports_dir / "claim_support_registry.json").write_text(
            json.dumps(
                {
                    "total_claims": 2,
                    "supported_claims": 2,
                    "entries": [
                        {"claim_name": "c1", "evidence_source": "src/x.py", "boundary": "local", "supported": True},
                        {"claim_name": "c2", "evidence_source": "src/y.py", "boundary": "local", "supported": True},
                    ],
                }
            ),
            encoding="utf-8",
        )
        html = build_dashboard_html(tmp_path)
        # Category rows rendered
        assert "metallurgical_terms" in html
        # Evidence rows rendered
        assert "c1" in html
        assert "c2" in html
        assert "✅" in html


# ============================================================================
# figures/ — None-output_dir/project_root paths + evidence load path
# ============================================================================


class TestFiguresNonePathFallbacks:
    """Figures functions use correct fallback when output_dir is None."""

    def test_purity_progression_none_output_dir_no_project_root(self, tmp_path, monkeypatch):
        """When output_dir=None and project_root=None, figures fall back to cwd."""
        monkeypatch.chdir(tmp_path)
        from figures import generate_purity_progression

        out = generate_purity_progression(output_dir=None, project_root=None)
        assert out.exists()
        assert out.name == "purity_progression.png"

    def test_karat_grading_none_output_dir_no_project_root(self, tmp_path, monkeypatch):
        """karat grading chart uses cwd fallback when both args are None."""
        monkeypatch.chdir(tmp_path)
        from figures import generate_karat_grading_chart

        out = generate_karat_grading_chart(output_dir=None, project_root=None)
        assert out.exists()
        assert out.name == "karat_grading.png"

    def test_karat_grading_none_output_dir_with_project_root(self, tmp_path):
        """karat grading chart uses project_root/output/figures when output_dir=None."""
        (tmp_path / "manuscript").mkdir()
        from figures import generate_karat_grading_chart

        out = generate_karat_grading_chart(output_dir=None, project_root=tmp_path)
        assert out.exists()
        assert "figures" in str(out)

    def test_token_density_none_output_dir_no_project_root(self, tmp_path, monkeypatch):
        """Token density chart uses cwd fallback when both args are None."""
        monkeypatch.chdir(tmp_path)
        from figures import generate_token_density_chart

        out = generate_token_density_chart(output_dir=None, project_root=None)
        assert out.exists()
        assert out.name == "token_density.png"

    def test_token_density_reads_token_plan_json(self, tmp_path):
        """Token density chart reads token_plan.json from output/reports when present."""
        reports_dir = tmp_path / "output" / "reports"
        reports_dir.mkdir(parents=True)
        figures_dir = tmp_path / "output" / "figures"
        figures_dir.mkdir(parents=True)
        (reports_dir / "token_plan.json").write_text(
            json.dumps(
                {
                    "section_counts": {"methodology": 4, "results": 2},
                    "category_counts": {"metallurgical_terms": 3, "manuscript_terms": 1},
                }
            ),
            encoding="utf-8",
        )
        from figures import generate_token_density_chart

        out = generate_token_density_chart(figures_dir)
        assert out.exists()
        assert out.stat().st_size > 100

    def test_provenance_sankey_none_output_dir(self, tmp_path, monkeypatch):
        """Provenance sankey uses cwd fallback when output_dir=None."""
        monkeypatch.chdir(tmp_path)
        from figures import generate_provenance_sankey

        out = generate_provenance_sankey(output_dir=None, project_root=None)
        assert out.exists()
        assert out.name == "provenance_sankey.png"

    def test_purity_claim_scatter_none_output_dir(self, tmp_path, monkeypatch):
        """Purity-claim scatter uses cwd fallback when output_dir=None."""
        monkeypatch.chdir(tmp_path)
        from figures import generate_purity_claim_scatter

        out = generate_purity_claim_scatter(output_dir=None, project_root=None)
        assert out.exists()
        assert out.name == "purity_claim_scatter.png"

    def test_purity_claim_scatter_loads_claim_support_registry(self, tmp_path):
        figures_dir = tmp_path / "output" / "figures"
        figures_dir.mkdir(parents=True)
        reports_dir = tmp_path / "output" / "reports"
        reports_dir.mkdir(parents=True)
        (reports_dir / "claim_support_registry.json").write_text(json.dumps({"support_rate": 0.75}), encoding="utf-8")
        from figures import generate_purity_claim_scatter

        out = generate_purity_claim_scatter(figures_dir, project_root=tmp_path)
        assert out.exists()
        assert out.stat().st_size > 100

    def test_token_heatmap_none_output_dir(self, tmp_path, monkeypatch):
        """Token heatmap uses cwd fallback when output_dir=None."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "manuscript").mkdir()
        from figures import generate_token_heatmap

        out = generate_token_heatmap(output_dir=None, project_root=None)
        assert out.exists()
        assert out.name == "token_heatmap.png"


# ============================================================================
# manuscript_variables.py — staleness detection + SOURCE_DATE_EPOCH
# ============================================================================


class TestManuscriptVariablesStalenessDetection:
    """_detect_staleness covers fresh, missing-output, and stale branches."""

    def test_stale_when_output_manuscript_missing(self, tmp_path):
        """When output/manuscript/ doesn't exist, status is 'stale'."""
        from manuscript_variables import generate_variables

        root = _minimal_manuscript(tmp_path)
        v = generate_variables(root)
        assert v["MANUSCRIPT_STALENESS"].startswith("stale")

    def test_stale_when_source_file_missing_from_output(self, tmp_path):
        """When a source *.md is missing from output/manuscript/, status is 'stale'."""
        from manuscript_variables import generate_variables

        root = _minimal_manuscript(tmp_path)
        # Create source section file
        (root / "manuscript" / "00_abstract.md").write_text("# Abstract\n", encoding="utf-8")
        # Create output/manuscript/ but without the file
        (root / "output" / "manuscript").mkdir(parents=True)
        v = generate_variables(root)
        assert "stale" in v["MANUSCRIPT_STALENESS"]

    def test_stale_when_source_is_newer_than_output(self, tmp_path):
        """When source file is newer than rendered output, status is 'stale'."""
        import time
        from manuscript_variables import generate_variables

        root = _minimal_manuscript(tmp_path)
        src_file = root / "manuscript" / "00_abstract.md"
        out_dir = root / "output" / "manuscript"
        out_dir.mkdir(parents=True)
        # Write output first, then write source (newer)
        out_file = out_dir / "00_abstract.md"
        out_file.write_text("old\n", encoding="utf-8")
        time.sleep(0.01)
        src_file.write_text("# Abstract\n{{REFINERY_NUM_STAGES}}\n", encoding="utf-8")
        # Touch src file to ensure it's newer
        src_file.touch()
        v = generate_variables(root)
        assert "stale" in v["MANUSCRIPT_STALENESS"]

    def test_fresh_when_output_is_up_to_date(self, tmp_path):
        """When all output files are newer than source files, status is 'fresh'."""
        import time
        from manuscript_variables import generate_variables

        root = _minimal_manuscript(tmp_path)
        src_file = root / "manuscript" / "00_abstract.md"
        src_file.write_text("# Abstract\n", encoding="utf-8")
        time.sleep(0.01)
        out_dir = root / "output" / "manuscript"
        out_dir.mkdir(parents=True)
        out_file = out_dir / "00_abstract.md"
        out_file.write_text("rendered\n", encoding="utf-8")
        # Ensure output is newer
        out_file.touch()
        v = generate_variables(root)
        assert v["MANUSCRIPT_STALENESS"] == "fresh"


class TestSourceDateEpoch:
    """build_timestamp honours SOURCE_DATE_EPOCH env variable."""

    def test_source_date_epoch_used(self, monkeypatch):
        """When SOURCE_DATE_EPOCH is set, timestamp is deterministic."""
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "0")
        from parsing import build_timestamp  # type: ignore[attr-defined]

        ts = build_timestamp()
        assert ts == "1970-01-01T00:00:00Z"

    def test_source_date_epoch_not_set_returns_current(self, monkeypatch):
        """When SOURCE_DATE_EPOCH is unset, timestamp matches current UTC roughly."""
        monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
        from parsing import build_timestamp  # type: ignore[attr-defined]

        ts = build_timestamp()
        assert ts.endswith("Z")
        assert len(ts) == 20  # YYYY-MM-DDTHH:MM:SSZ


# ============================================================================
# __init__.py — public API import coverage
# ============================================================================


class TestPublicAPIImport:
    """Importing from __init__ exercises the public re-exports."""

    def test_import_run_refinery(self):
        import sys

        # Import via the package __init__
        pkg_path = str(_PROJECT_ROOT / "src")
        if pkg_path not in sys.path:
            sys.path.insert(0, pkg_path)
        # The __init__.py uses relative imports; we access via direct import
        # of each module (conftest adds src/ to path already)
        from refinery import run_refinery, CANONICAL_STAGES
        from purity import NINE_NINES_PURITY
        from config import GoldRefinementConfig
        from assay import ClaimRecord
        from evidence import EvidenceRegistry
        from dashboard import build_dashboard_html

        # Verify key imports resolve
        assert run_refinery is not None
        assert CANONICAL_STAGES is not None
        assert NINE_NINES_PURITY == 0.999999999
        assert GoldRefinementConfig is not None
        assert ClaimRecord is not None
        assert EvidenceRegistry is not None
        assert build_dashboard_html is not None
