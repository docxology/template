"""Configured core producer order and explicit deep-output hydration controls."""

from __future__ import annotations

import json
from pathlib import Path

from infrastructure.core.script_discovery import discover_analysis_scripts
from template_search_project.pipeline.composition import compose_literature_review
from template_search_project.publish.bibliography import GENERATED_SUPPLEMENT_NAME
from template_search_project.publish.config import DeepSearchConfig, ProjectConfig, SearchConfig
from template_search_project.publish.manuscript_variables import compute_variables, write_resolved_manuscript_tree
from template_search_project.search.deep_search import run_deep_search

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_ORDER = [
    "run_search_pipeline.py",
    "y_generate_search_figures.py",
    "z_generate_manuscript_variables.py",
    "zz_generate_review_report.py",
    "zzz_build_dashboard.py",
]


def test_configured_core_order_excludes_disabled_deep_and_live_acceptance():
    selected = discover_analysis_scripts(PROJECT_ROOT.parents[2], project_dir=PROJECT_ROOT)
    assert [path.name for path in selected] == EXPECTED_ORDER
    assert "run_deep_search.py" not in EXPECTED_ORDER
    assert "s_compose_literature_review.py" not in EXPECTED_ORDER
    assert "_run_unpaid_acceptance.py" not in EXPECTED_ORDER


def _current_deep_project(tmp_path: Path) -> tuple[Path, ProjectConfig]:
    root = tmp_path / "project"
    (root / "manuscript").mkdir(parents=True)
    (root / "manuscript" / "config.yaml").write_text("paper:\n  title: Controlled\n")
    (root / "manuscript" / "01_main.md").write_text("# Main\n\nAuthored content.\n")
    (root / "manuscript" / "S01_literature_review.md").write_text("# Curated appendix\n")
    corpus = root / "corpus.json"
    corpus.write_text(json.dumps([{"id": "a", "title": "Convexity", "authors": ["Alice"], "year": 2020}]))
    config = ProjectConfig(
        title="Controlled",
        search=SearchConfig(query="convex"),
        deep_search=DeepSearchConfig(
            enabled=True,
            keywords=["convex"],
            sources=["local"],
            fetch_abstracts=False,
            fetch_fulltext=False,
            llm_per_paper=False,
        ),
    )
    run_deep_search(config.deep_search, project_root=root, corpus_path=corpus)
    return root, config


def _variables():
    return compute_variables(
        config_query="convex", config_max_results=1, config_sources=["local"], search_result_payload={"papers": []}
    )


def test_hydration_keeps_generated_supplement_and_authored_appendix(tmp_path: Path):
    root, config = _current_deep_project(tmp_path)
    before = {path.name: path.read_bytes() for path in (root / "manuscript").iterdir()}
    assert compose_literature_review(root, config) == 0
    generated = root / "output" / "manuscript" / GENERATED_SUPPLEMENT_NAME
    composed = generated.read_bytes()
    write_resolved_manuscript_tree(root, _variables(), config=config)
    assert generated.read_bytes() == composed
    assert {path.name: path.read_bytes() for path in (root / "manuscript").iterdir()} == before
    assert (root / "output" / "manuscript" / "S01_literature_review.md").read_bytes() == before[
        "S01_literature_review.md"
    ]


def test_composer_after_hydration_updates_only_generated_supplement(tmp_path: Path):
    root, config = _current_deep_project(tmp_path)
    write_resolved_manuscript_tree(root, _variables(), config=config)
    generated = root / "output" / "manuscript" / GENERATED_SUPPLEMENT_NAME
    generated.write_text("STALE generated output\n")
    assert compose_literature_review(root, config) == 0
    assert "STALE" not in generated.read_text()
    assert "Convexity" in generated.read_text()
    assert (root / "manuscript" / "S01_literature_review.md").read_text() == "# Curated appendix\n"


def test_historical_missing_receipt_and_changed_configuration_cannot_replay(tmp_path: Path):
    root, config = _current_deep_project(tmp_path)
    receipt = root / "output" / "deep_search" / "producer_receipt.json"
    recorded = receipt.read_bytes()
    receipt.unlink()
    assert compose_literature_review(root, config) == 1
    receipt.write_bytes(recorded)
    config.deep_search.enabled = False
    assert compose_literature_review(root, config) == 1
    assert not (root / "output" / "manuscript" / GENERATED_SUPPLEMENT_NAME).exists()
