"""Integration tests for script entry points.

Tests that the main() functions in each orchestrator script
can be called without error when given minimal valid input.
Uses real computation; ``sys.argv`` is swapped via ``contextlib`` (no unittest.mock).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest


# Scripts directory
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


@contextmanager
def _argv(replacement: list[str]):
    """Temporarily replace ``sys.argv`` for CLI-style tests."""
    saved = sys.argv
    sys.argv = list(replacement)
    try:
        yield
    finally:
        sys.argv = saved


def _load_script_module(name: str, script_path: Path):
    """Load a script file as a module (same pattern as prior tests)."""
    spec = importlib.util.spec_from_file_location(name, script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {script_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestLiteratureSearchScript:
    """Integration tests for 01_literature_search.py entry point."""

    def test_main_with_all_sources_skipped(self, tmp_output_dir):
        """Verify main() runs when all API sources are skipped."""
        sys.path.insert(0, str(SCRIPTS_DIR.parent / "src"))
        mod = _load_script_module("literature_search", SCRIPTS_DIR / "01_literature_search.py")
        with _argv(
            [
                "01_literature_search.py",
                "--skip-arxiv",
                "--skip-s2",
                "--skip-openalex",
                "--output-dir",
                tmp_output_dir,
            ]
        ):
            mod.main()

        corpus_path = Path(tmp_output_dir) / "data" / "corpus.jsonl"
        assert corpus_path.exists(), "Corpus file should be created even with no sources"

    def test_parse_args_defaults(self):
        """Verify default argument parsing."""
        mod = _load_script_module("literature_search", SCRIPTS_DIR / "01_literature_search.py")
        with _argv(["01_literature_search.py"]):
            args = mod.parse_args()
        assert args.query is None
        assert args.max_results == 1000
        assert args.resume is True

    def test_parse_args_no_resume(self):
        """Verify --no-resume disables loading an existing corpus."""
        mod = _load_script_module("literature_search", SCRIPTS_DIR / "01_literature_search.py")
        with _argv(["01_literature_search.py", "--no-resume"]):
            args = mod.parse_args()
        assert args.resume is False

    def test_parse_args_can_skip_biorxiv_and_medrxiv_independently(self):
        """The shared API has two independently selectable corpus engines."""
        mod = _load_script_module("literature_search", SCRIPTS_DIR / "01_literature_search.py")
        with _argv(["01_literature_search.py", "--skip-medrxiv"]):
            args = mod.parse_args()

        assert args.skip_medrxiv is True
        assert args.skip_biorxiv is False

    def test_resume_loads_existing_corpus(self, sample_papers, tmp_output_dir):
        """Verify --resume loads an existing corpus before searching."""
        from literature.corpus import Corpus

        corpus = Corpus()
        for paper in sample_papers:
            corpus.add(paper)
        corpus_path = Path(tmp_output_dir) / "data" / "corpus.jsonl"
        corpus_path.parent.mkdir(parents=True, exist_ok=True)
        corpus.save(corpus_path)
        initial_count = len(corpus)

        mod = _load_script_module("literature_search", SCRIPTS_DIR / "01_literature_search.py")
        with _argv(
            [
                "01_literature_search.py",
                "--resume",
                "--skip-arxiv",
                "--skip-s2",
                "--skip-openalex",
                "--output-dir",
                tmp_output_dir,
            ]
        ):
            mod.main()

        reloaded = Corpus.load(corpus_path)
        assert len(reloaded) == initial_count

    def test_log_level_flag_accepted(self):
        """Verify --log-level flag is accepted by the argument parser."""
        mod = _load_script_module("literature_search", SCRIPTS_DIR / "01_literature_search.py")
        with _argv(["01_literature_search.py", "--log-level", "DEBUG"]):
            args = mod.parse_args()
        assert args.log_level == "DEBUG"


class TestMetaAnalysisPipelineScript:
    """Integration tests for 02_meta_analysis_pipeline.py entry point."""

    def test_main_with_sample_corpus(self, sample_papers, tmp_output_dir):
        """Verify meta-analysis pipeline runs on sample corpus."""
        from literature.corpus import Corpus

        corpus = Corpus()
        for paper in sample_papers:
            corpus.add(paper)
        corpus_path = Path(tmp_output_dir) / "corpus.jsonl"
        corpus.save(corpus_path)

        mod = _load_script_module("meta_analysis_pipeline", SCRIPTS_DIR / "02_meta_analysis_pipeline.py")
        with _argv(
            [
                "02_meta_analysis_pipeline.py",
                "--corpus",
                str(corpus_path),
                "--output-dir",
                tmp_output_dir,
            ]
        ):
            mod.main()

        data_dir = Path(tmp_output_dir) / "data"
        assert (data_dir / "subfield_classification.json").exists()
        assert (data_dir / "temporal_analysis.json").exists()


class TestBuildKnowledgeGraphScript:
    """Integration tests for 03_build_knowledge_graph.py entry point."""

    def test_main_generates_llm_assertions(self, sample_papers, tmp_output_dir, httpserver):
        """Verify KG construction with LLM assertion extraction via local HTTP."""
        from literature.corpus import Corpus

        corpus = Corpus()
        for paper in sample_papers:
            corpus.add(paper)
        corpus_path = Path(tmp_output_dir) / "corpus.jsonl"
        corpus.save(corpus_path)

        ollama_response = json.dumps(
            {
                "response": json.dumps(
                    [
                        {
                            "hypothesis_id": "PRIMARY_EFFICACY",
                            "direction": "supports",
                            "confidence": 0.8,
                            "reasoning": "test evidence",
                        },
                    ]
                ),
                "eval_duration": 500000000,
                "eval_count": 50,
            }
        )
        httpserver.expect_request("/api/generate", method="POST").respond_with_data(
            ollama_response, content_type="application/json"
        )

        mod = _load_script_module("build_knowledge_graph", SCRIPTS_DIR / "03_build_knowledge_graph.py")
        with _argv(
            [
                "03_build_knowledge_graph.py",
                "--corpus",
                str(corpus_path),
                "--output-dir",
                tmp_output_dir,
                "--llm-url",
                httpserver.url_for(""),
                "--clear-assertions",
            ]
        ):
            mod.main()

        data_dir = Path(tmp_output_dir) / "data"
        assert (data_dir / "hypothesis_scores.json").exists()
        scores = json.loads((data_dir / "hypothesis_scores.json").read_text())
        assert isinstance(scores, dict)
        assert len(scores) > 0


class TestGenerateFiguresScript:
    """Integration tests for 04_generate_figures.py entry point."""

    def test_main_with_minimal_data(self, tmp_output_dir):
        """Verify figure generation runs with minimal JSON data."""
        input_dir = Path(tmp_output_dir) / "input"
        input_dir.mkdir()
        output_dir = Path(tmp_output_dir) / "figures"

        with open(input_dir / "subfield_classification.json", "w") as f:
            json.dump({"General Theory": 5, "Neuroscience": 3, "Robotics": 2}, f)

        with open(input_dir / "temporal_analysis.json", "w") as f:
            json.dump(
                {
                    "year_counts": {"2019": 3, "2020": 4, "2021": 3},
                    "cumulative": {"2019": 3, "2020": 7, "2021": 10},
                    "first_year": 2019,
                    "last_year": 2021,
                    "total_papers": 10,
                    "peak_year": 2020,
                },
                f,
            )

        with open(input_dir / "hypothesis_scores.json", "w") as f:
            json.dump(
                {
                    "PRIMARY_EFFICACY": 0.65,
                    "SCALABILITY": 0.3,
                    "MECHANISTIC_BASIS": -0.2,
                },
                f,
            )

        mod = _load_script_module("generate_figures", SCRIPTS_DIR / "04_generate_figures.py")
        with _argv(
            [
                "04_generate_figures.py",
                "--input-dir",
                str(input_dir),
                "--output-dir",
                str(output_dir),
            ]
        ):
            mod.main()

        assert output_dir.exists()
        png_files = list(output_dir.glob("*.png"))
        assert len(png_files) >= 2, f"Expected at least 2 figures, got {len(png_files)}"


class TestLiteratureEvaluationScript:
    """Integration tests for 07_literature_evaluation.py entry point.

    Regression guard for a real wiring bug: the CLI previously called
    ``validate_fixture_honesty(manuscript_dir, corpus_path)`` positionally
    (the real signature takes a keyword-only ``search_term``), and the error
    branch read ``v.reason``/``v.line`` instead of the real
    ``FixtureHonestyFinding`` fields ``message``/``line_number``. Both bugs
    made ``--fixture-honesty`` raise instead of running. These tests exercise
    both the clean-pass and violation-found branches through the real CLI
    entry point (not just the underlying validator) so a regression on
    either the call signature or the result-object fields fails loudly.
    """

    def test_fixture_honesty_passes_on_clean_manuscript(self, sample_papers, tmp_path):
        """--fixture-honesty runs to completion when the manuscript is clean."""
        from literature.corpus import Corpus

        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        (manuscript_dir / "section.md").write_text(
            "The {{SEARCH_TERM}} corpus uses a committed synthetic fixture for offline runs.\n",
            encoding="utf-8",
        )

        corpus = Corpus()
        for paper in sample_papers:
            corpus.add(paper)
        corpus_path = tmp_path / "corpus.jsonl"
        corpus.save(corpus_path)
        output_dir = tmp_path / "output"

        mod = _load_script_module("literature_evaluation_clean", SCRIPTS_DIR / "07_literature_evaluation.py")
        mod.PROJECT_ROOT = tmp_path
        with _argv(
            [
                "07_literature_evaluation.py",
                "--corpus",
                str(corpus_path),
                "--output-dir",
                str(output_dir),
                "--fixture-honesty",
            ]
        ):
            mod.main()  # must not raise TypeError/AttributeError

        assert (output_dir / "literature_evaluation.json").exists()

    def test_fixture_honesty_exits_nonzero_on_violation(self, sample_papers, tmp_path):
        """--fixture-honesty reports violations and exits 1 without raising."""
        from literature.corpus import Corpus

        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        (manuscript_dir / "bad.md").write_text("We found strong evidence in the synthetic run.\n", encoding="utf-8")

        corpus = Corpus()
        for paper in sample_papers:
            corpus.add(paper)
        corpus_path = tmp_path / "corpus.jsonl"
        corpus.save(corpus_path)
        output_dir = tmp_path / "output"

        mod = _load_script_module("literature_evaluation_violation", SCRIPTS_DIR / "07_literature_evaluation.py")
        mod.PROJECT_ROOT = tmp_path
        with _argv(
            [
                "07_literature_evaluation.py",
                "--corpus",
                str(corpus_path),
                "--output-dir",
                str(output_dir),
                "--fixture-honesty",
            ]
        ):
            with pytest.raises(SystemExit) as exc_info:
                mod.main()

        assert exc_info.value.code == 1


class TestBibliographyExportScript:
    """Integration tests for 09_export_bibliography.py."""

    def test_main_exports_complete_corpus(self, sample_corpus_path, tmp_path):
        output_dir = tmp_path / "bibliography"
        mod = _load_script_module("export_bibliography", SCRIPTS_DIR / "09_export_bibliography.py")

        with _argv(
            [
                "09_export_bibliography.py",
                "--corpus",
                sample_corpus_path,
                "--output-dir",
                str(output_dir),
            ]
        ):
            mod.main()

        bibliography = (output_dir / "bibliography.bib").read_text(encoding="utf-8")
        assert bibliography.count("@article{") == 3


class TestReproducibilityAssessmentScript:
    """Integration tests for 10_reproducibility_assessment.py."""

    def test_main_degrades_without_fulltext_and_writes_valid_outputs(self, sample_corpus_path, tmp_path):
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            """
project_config:
  fulltext:
    enabled: false
    download_dir: artifacts/fulltext
  sampling:
    fraction: 1.0
    seed: 42
""".strip(),
            encoding="utf-8",
        )
        output_dir = tmp_path / "reproducibility"
        mod = _load_script_module(
            "reproducibility_assessment",
            SCRIPTS_DIR / "10_reproducibility_assessment.py",
        )
        mod.PROJECT_ROOT = tmp_path

        with _argv(
            [
                "10_reproducibility_assessment.py",
                "--corpus",
                sample_corpus_path,
                "--output-dir",
                str(output_dir),
                "--config",
                str(config_path),
            ]
        ):
            mod.main()

        data_dir = output_dir / "data"
        assert (data_dir / "workflow_graphs.jsonl").read_text(encoding="utf-8") == ""
        assert json.loads((data_dir / "reproducibility_scores.json").read_text()) == {}
        summary = json.loads((data_dir / "reproducibility_summary.json").read_text())
        assert summary["fulltext_available"] is False
        assert summary["n_papers_scored"] == 0


class TestFulltextDownloadScript:
    """Integration tests for 11_fulltext_download.py."""

    def test_main_uses_configured_project_relative_download_directory(self, tmp_path):
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            """
project_config:
  fulltext:
    enabled: false
    unpaywall_email: ""
    download_dir: artifacts/custom-fulltext
""".strip(),
            encoding="utf-8",
        )
        mod = _load_script_module("fulltext_download", SCRIPTS_DIR / "11_fulltext_download.py")
        mod.PROJECT_ROOT = tmp_path

        with _argv(["11_fulltext_download.py", "--config", str(config_path)]):
            mod.main()

        assert (tmp_path / "artifacts" / "custom-fulltext").is_dir()
        assert not (tmp_path / "output" / "fulltext").exists()
