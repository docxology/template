"""Evidence-backed variables specific to the advanced literature review."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(data_dir: Path, name: str) -> dict[str, Any] | None:
    path = data_dir / name
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else None


def _pending(value: Any = None) -> str:
    """Represent an unmeasured value explicitly instead of inventing a claim."""
    return str(value) if value is not None else "pending"


def _corpus_records(data_dir: Path) -> list[dict[str, Any]]:
    path = data_dir / "corpus.jsonl"
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            value = json.loads(line)
            if isinstance(value, dict):
                records.append(value)
    return records


def extract_multi_phase_variables(data_dir: Path, config: dict[str, Any] | None = None) -> dict[str, str]:
    """Extract only values supported by recorded pipeline artifacts."""
    variables: dict[str, str] = {}
    phase_meta = _load_json(data_dir, "phase_metadata.json")
    if phase_meta:
        phases = phase_meta.get("phases", {})
        if isinstance(phases, dict):
            variables["TOTAL_PHASES"] = str(len(phases))
            variables["CORPUS_SIZE"] = str(phase_meta.get("total_unique_papers", 0))
            for index, (phase_id, phase_data) in enumerate(phases.items(), 1):
                if not isinstance(phase_data, dict):
                    continue
                variables[f"PHASE_{index}_NAME"] = str(phase_data.get("name", phase_id))
                variables[f"PHASE_{index}_PAPERS"] = str(phase_data.get("papers_final", 0))
                variables[f"PHASE_{index}_QUERIES"] = str(len(phase_data.get("queries_executed", [])))
        overlap = phase_meta.get("phase_overlap", {})
        jaccards = [
            float(pair.get("jaccard_similarity", 0))
            for values in overlap.values()
            if isinstance(values, dict)
            for pair in values.values()
            if isinstance(pair, dict)
        ]
        if jaccards:
            variables["CROSS_PHASE_OVERLAP_PCT"] = f"{sum(jaccards) / len(jaccards) * 100:.1f}"
        citation_values = phase_meta.get("citation_validation", {})
        rates = [float(value.get("citation_rate", 0)) for value in citation_values.values() if isinstance(value, dict)]
        if rates:
            variables["CROSS_PHASE_CITATION_RATE"] = f"{sum(rates) / len(rates) * 100:.1f}"

    cfg = config or {}
    search = cfg.get("project_config", {}).get("search", {})
    engines = search.get("engines", {})
    labels = {
        "arxiv": "arXiv",
        "openalex": "OpenAlex",
        "semantic_scholar": "Semantic Scholar",
        "crossref": "Crossref",
        "pubmed": "PubMed",
        "sovietrxiv": "SovietRxiv",
        "chinarxiv": "ChinaRxiv",
        "europepmc": "Europe PMC",
        "biorxiv": "bioRxiv/medRxiv",
    }
    enabled = [labels.get(name, name) for name, active in engines.items() if active]
    variables["N_ENGINES"] = str(len(enabled))
    variables["ENGINE_LIST"] = ", ".join(enabled) if enabled else "none configured"
    keywords = cfg.get("keywords", [])
    variables["KEYWORDS_LIST"] = ", ".join(str(keyword) for keyword in keywords)
    variables["SEARCH_TERM"] = str(search.get("term", "the configured topic"))
    variables["SEARCH_TERM_TITLE"] = variables["SEARCH_TERM"].title()

    records = _corpus_records(data_dir)
    years = [int(record["year"]) for record in records if record.get("year") is not None]
    if years:
        variables["YEAR_START"] = str(min(years))
        variables["YEAR_END"] = str(max(years))
        variables["YEAR_SPAN"] = str(max(years) - min(years))
    else:
        variables.update({"YEAR_START": "pending", "YEAR_END": "pending", "YEAR_SPAN": "pending"})

    total = len(records)
    abstract_count = sum(bool(record.get("abstract")) for record in records)
    doi_count = sum(bool(record.get("doi")) for record in records)
    pdf_count = sum(bool(record.get("open_access_pdf_url") or record.get("pdf_url")) for record in records)
    if total:
        variables.update(
            {
                "ABSTRACT_COUNT": str(abstract_count),
                "NO_ABSTRACT_COUNT": str(total - abstract_count),
                "ABSTRACT_COVERAGE_PCT": f"{abstract_count / total * 100:.1f}",
                "DOI_COUNT": str(doi_count),
                "OA_COUNT": str(sum(bool(record.get("is_open_access")) for record in records)),
                "OA_PCT": f"{sum(bool(record.get('is_open_access')) for record in records) / total * 100:.1f}",
                "PDF_AVAIL_COUNT": str(pdf_count),
                "PDF_AVAIL_PCT": f"{pdf_count / total * 100:.1f}",
                "PUBLISHER_PDF_COUNT": str(pdf_count),
                "NO_FULLTEXT_COUNT": str(total - pdf_count),
            }
        )

    for name, filename, keys in (
        ("CITATION_EDGES", "citation_network.json", ("num_edges",)),
        ("CITATION_NODES", "citation_network.json", ("num_nodes",)),
        ("TOTAL_ASSERTIONS", "assertion_summary.json", ("total_assertions",)),
        ("NUM_TOPICS", "topics.json", ("num_topics",)),
        ("REPRO_PAPERS_SCORED", "reproducibility_summary.json", ("n_papers_scored", "papers_scored")),
    ):
        source = _load_json(data_dir, filename)
        if source:
            for key in keys:
                if key in source:
                    variables[name] = str(source[key])
                    break
    repro = _load_json(data_dir, "reproducibility_summary.json")
    if repro:
        for key in ("mean_composite_score", "mean_composite"):
            if key in repro:
                variables["REPRO_MEAN_SCORE"] = f"{float(repro[key]):.3f}"
                break

    for name in (
        "FOUNDATION_PEAK_YEAR",
        "JWST_LAUNCH_YEAR",
        "JWST_GROWTH_RATE",
        "MOL_DETECTION_GROWTH_RATE",
        "LLM_FILTER_PRECISION",
        "LLM_FILTERED_OUT",
    ):
        variables[name] = _pending()
    return variables
