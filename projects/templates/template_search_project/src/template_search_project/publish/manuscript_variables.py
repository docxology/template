"""Hydrate manuscript variables from the run summary.

The manuscript abstract / introduction reference values like
``{{RESULT_NUM_PAPERS}}`` that must be replaced with the latest run's
numbers before PDF rendering. This module mirrors the pattern used by
``projects/templates/template_code_project/scripts/z_generate_manuscript_variables.py``.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping

from infrastructure.core.files.secure_write import (
    atomic_write_bytes_confined,
    atomic_write_text_confined,
    read_bytes_confined,
    unlink_confined,
)

from template_search_project.publish.bibliography import GENERATED_SUPPLEMENT_NAME, project_bibliographies
from template_search_project.publish.config import DeepSearchConfig, ProjectConfig
from template_search_project.publish.deep_custody import admit_composed_supplement, admit_deep_producer


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


def write_variables(
    variables: ManuscriptVariables,
    output_path: Path | str,
    *,
    project_root: Path | str | None = None,
) -> Path:
    """Persist variables as JSON for downstream rendering / debugging."""
    out = Path(output_path).absolute()
    root = Path(project_root).absolute() if project_root is not None else out.parent
    atomic_write_text_confined(
        root,
        out,
        json.dumps(variables.as_dict(), indent=2, ensure_ascii=False),
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
    *,
    config: ProjectConfig | None = None,
) -> Path:
    """Write ``manuscript/*.md`` with substitutions plus aux files into ``output/manuscript``.

    PDF rendering prefers ``output/manuscript`` when it contains markdown
    (see :func:`infrastructure.rendering.pipeline._resolve_manuscript_dir`).
    """
    root = Path(project_root).absolute()
    admitted = (
        admit_deep_producer(root, config.deep_search, (root / config.deep_search.output_dir).absolute())
        if config is not None and config.deep_search.enabled
        else None
    )
    manuscript_dir = root / "manuscript"
    out_dir = root / "output" / "manuscript"
    supplement = (
        admit_composed_supplement(root, config.deep_search, admitted)
        if config is not None and admitted is not None
        else None
    )
    if (manuscript_dir / GENERATED_SUPPLEMENT_NAME).exists() or (
        manuscript_dir / GENERATED_SUPPLEMENT_NAME
    ).is_symlink():
        raise ValueError("Authored manuscript uses the reserved generated supplement name")

    for md_file in sorted(manuscript_dir.glob("*.md")):
        text = read_bytes_confined(root, md_file).decode("utf-8")
        atomic_write_text_confined(
            root,
            out_dir / md_file.name,
            substitute_in_text(text, variables),
        )

    for aux in ["config.yaml"]:
        src = manuscript_dir / aux
        if src.is_file():
            atomic_write_bytes_confined(root, out_dir / aux, read_bytes_confined(root, src))

    for bib in sorted(manuscript_dir.glob("*.bib")):
        atomic_write_bytes_confined(root, out_dir / bib.name, read_bytes_confined(root, bib))

    generated_paths: tuple[str, ...]
    if config is None:
        generated_paths = ("output/bibliography/references.bib", "output/bibliography/references_deep.bib")
    elif config.deep_search.enabled:
        generated_paths = (config.references_path, config.deep_search.unified_bibtex_path)
    else:
        generated_paths = (config.references_path,)
        # This reserved file is generated active output, not an authored section
        # or historical published artifact. Disabled deep search cannot replay it.
    project_bibliographies(root, generated_paths, admitted_sources=admitted)
    if supplement is not None:
        atomic_write_bytes_confined(root, out_dir / GENERATED_SUPPLEMENT_NAME, supplement)
    if config is not None and not config.deep_search.enabled:
        unlink_confined(root, out_dir / GENERATED_SUPPLEMENT_NAME)

    return out_dir
