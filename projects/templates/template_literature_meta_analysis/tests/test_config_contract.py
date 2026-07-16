"""Cross-file contracts for the live and example manuscript configuration."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest
import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATHS = (
    PROJECT_ROOT / "manuscript" / "config.yaml",
    PROJECT_ROOT / "manuscript" / "config.yaml.example",
)
DEFAULT_ANALYSIS_SCRIPTS = [
    "02_meta_analysis_pipeline.py",
    "04_generate_figures.py",
    "06_fulltext_assessment.py",
    "07_literature_evaluation.py",
    "08_deep_research_dispatch.py",
    "09_export_bibliography.py",
    "05_inject_variables.py",
]
ENGINE_KEYS = {
    "arxiv",
    "semantic_scholar",
    "openalex",
    "crossref",
    "pubmed",
    "sovietrxiv",
    "chinarxiv",
    "europepmc",
    "biorxiv",
    "medrxiv",
}


def _load(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _mapping_paths(value: Mapping[str, Any], prefix: tuple[str, ...] = ()) -> set[tuple[str, ...]]:
    paths: set[tuple[str, ...]] = set()
    for key, child in value.items():
        path = (*prefix, str(key))
        paths.add(path)
        if isinstance(child, Mapping):
            paths.update(_mapping_paths(child, path))
    return paths


def test_config_example_covers_every_nested_mapping_key() -> None:
    """The copyable example must not silently omit live nested features."""
    live = _load(CONFIG_PATHS[0])
    example = _load(CONFIG_PATHS[1])
    missing = _mapping_paths(live) - _mapping_paths(example)
    assert not missing, "config.yaml.example lacks nested keys: " + ", ".join(
        ".".join(path) for path in sorted(missing)
    )


@pytest.mark.parametrize("config_path", CONFIG_PATHS, ids=("live", "example"))
def test_default_analysis_allowlist_is_offline_and_variable_injection_is_last(
    config_path: Path,
) -> None:
    config = _load(config_path)
    assert config["analysis"]["scripts"] == DEFAULT_ANALYSIS_SCRIPTS


@pytest.mark.parametrize("config_path", CONFIG_PATHS, ids=("live", "example"))
def test_search_config_declares_all_ten_engine_toggles(config_path: Path) -> None:
    config = _load(config_path)
    engines = config["project_config"]["search"]["engines"]
    assert set(engines) == ENGINE_KEYS
    assert all(enabled is True for enabled in engines.values())


@pytest.mark.parametrize("config_path", CONFIG_PATHS, ids=("live", "example"))
def test_declared_stage_order_respects_fulltext_dependencies(config_path: Path) -> None:
    config = _load(config_path)
    stages = config["project_config"]["pipeline_stages"]
    scripts = [stage["script"] for stage in stages]

    assert scripts.index("11_fulltext_download.py") < scripts.index("10_reproducibility_assessment.py")
    assert scripts[-1] == "05_inject_variables.py"

    fulltext = next(stage for stage in stages if stage["script"] == "11_fulltext_download.py")
    reproducibility = next(stage for stage in stages if stage["script"] == "10_reproducibility_assessment.py")
    assert "output/fulltext/" in fulltext["outputs"]
    assert "output/fulltext/" in reproducibility["inputs"]
