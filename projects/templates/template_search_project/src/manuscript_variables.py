"""Hydrate manuscript variables from the run summary.

The manuscript abstract / introduction reference values like
``{{RESULT_NUM_PAPERS}}`` that must be replaced with the latest run's
numbers before PDF rendering. This module mirrors the pattern used by
``projects/templates/template_code_project/scripts/z_generate_manuscript_variables.py``.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping

from src.config import DeepSearchConfig


@dataclass(frozen=True)
class ManuscriptVariables:
    """Variables substituted into manuscript markdown."""

    config_query: str
    config_max_results: int
    config_sources: str
    result_num_papers: int
    result_num_sources: int
    result_per_source: str
    result_errors: str
    result_year_min: str
    result_year_max: str
    result_with_abstract: int
    result_with_doi: int
    # Deep-search block (config + optional aggregate.json)
    deep_max_results_per_keyword: int
    deep_keyword_count: int
    deep_keywords_joined: str
    deep_sources: str
    deep_unique_papers: str

    def as_dict(self) -> dict[str, object]:
        """Process as dict."""
        return asdict(self)

    def as_uppercase_keys(self) -> dict[str, str]:
        """Return ``{NAME: value_str}`` ready for in-place text substitution."""
        return {f"{{{{{k.upper()}}}}}": str(v) for k, v in asdict(self).items()}


def compute_variables(
    *,
    config_query: str,
    config_max_results: int,
    config_sources: list[str],
    search_result_payload: Mapping[str, object],
    deep_search: DeepSearchConfig | None = None,
    aggregate_payload: Mapping[str, object] | None = None,
) -> ManuscriptVariables:
    """Pure computation: no I/O. Tests construct the inputs directly."""
    raw_papers = search_result_payload.get("papers")
    papers = list(raw_papers) if isinstance(raw_papers, list) else []
    raw_per_source = search_result_payload.get("per_source_counts")
    per_source = dict(raw_per_source) if isinstance(raw_per_source, Mapping) else {}
    raw_errors = search_result_payload.get("errors")
    errors = dict(raw_errors) if isinstance(raw_errors, Mapping) else {}
    raw_query = search_result_payload.get("query")
    query = raw_query if isinstance(raw_query, Mapping) else {}

    if deep_search is not None:
        dmax = deep_search.max_results_per_keyword
        dkc = len(deep_search.keywords)
        dkw = "; ".join(deep_search.keywords)
        dsrc = ", ".join(deep_search.sources)
    else:
        dmax = 10
        dkc = 0
        dkw = ""
        dsrc = ""

    # When no deep-search aggregate exists yet, surface a discoverable
    # sentinel rather than a silent dash so reviewers can grep the
    # rendered manuscript for "<deep-search not run>" to spot missed
    # substitutions (see manuscript/SYNTAX.md).
    uniq = "<deep-search not run>"
    if aggregate_payload is not None:
        up = aggregate_payload.get("unique_papers")
        if isinstance(up, list):
            uniq = str(len(up))

    return ManuscriptVariables(
        config_query=config_query,
        config_max_results=config_max_results,
        config_sources=", ".join(config_sources),
        result_num_papers=len(papers),
        result_num_sources=len(per_source),
        result_per_source=", ".join(f"{k}={v}" for k, v in per_source.items()) or "(none)",
        result_errors=", ".join(f"{k}: {v}" for k, v in errors.items()) or "none",
        result_year_min=str(query.get("year_min") or "—"),
        result_year_max=str(query.get("year_max") or "—"),
        result_with_abstract=sum(1 for p in papers if p.get("abstract")),
        result_with_doi=sum(1 for p in papers if p.get("doi")),
        deep_max_results_per_keyword=dmax,
        deep_keyword_count=dkc,
        deep_keywords_joined=dkw,
        deep_sources=dsrc,
        deep_unique_papers=uniq,
    )


def load_search_result_payload(path: Path | str) -> dict[str, object]:
    """Read the diagnostic ``output/search/results.json`` produced by the script."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"search result payload must be an object: {path}")
    return raw


def load_aggregate_payload(path: Path | str) -> dict[str, object] | None:
    """Read ``output/deep_search/aggregate.json`` if present."""
    p = Path(path)
    if not p.is_file():
        return None
    raw = json.loads(p.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else None


def write_variables(variables: ManuscriptVariables, output_path: Path | str) -> Path:
    """Persist variables as JSON for downstream rendering / debugging."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(variables.as_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return out


def substitute_in_text(text: str, variables: ManuscriptVariables) -> str:
    """Replace ``{{KEY}}`` markers in *text* with the variable values."""
    out = text
    for marker, value in variables.as_uppercase_keys().items():
        out = out.replace(marker, value)
    return out


def write_resolved_manuscript_tree(
    project_root: Path | str,
    variables: ManuscriptVariables,
) -> Path:
    """Write ``manuscript/*.md`` with substitutions plus aux files into ``output/manuscript``.

    PDF rendering prefers ``output/manuscript`` when it contains markdown
    (see :func:`infrastructure.rendering.pipeline._resolve_manuscript_dir`).
    """
    root = Path(project_root)
    manuscript_dir = root / "manuscript"
    out_dir = root / "output" / "manuscript"
    out_dir.mkdir(parents=True, exist_ok=True)

    for md_file in sorted(manuscript_dir.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        out_dir.joinpath(md_file.name).write_text(
            substitute_in_text(text, variables),
            encoding="utf-8",
        )

    for aux in ["config.yaml"]:
        src = manuscript_dir / aux
        if src.is_file():
            shutil.copy2(src, out_dir / aux)

    for bib in sorted(manuscript_dir.glob("*.bib")):
        shutil.copy2(bib, out_dir / bib.name)

    return out_dir
