"""Compute template variables from pipeline output data.

Reads pipeline output JSON/JSONL files and computes a dictionary of
template variables that can be injected into manuscript markdown files.
All values are pre-formatted strings ready for LaTeX insertion.

Usage:
    from src.manuscript.variables import compute_variables, inject_variables

    variables = compute_variables(Path("output"))
    rendered = inject_variables(template_content, variables)
"""

from __future__ import annotations

import json
import re
from pathlib import Path

try:
    from infrastructure.core.logging.utils import get_logger
except ImportError:
    import logging as _logging

    def get_logger(name: str):  # type: ignore[misc]
        """Fallback logger factory used when the infrastructure package is unavailable."""
        return _logging.getLogger(name)


logger = get_logger(__name__)


def _latex_number(n: int) -> str:
    """Format an integer with comma thousand separators.

    Uses plain commas which render correctly in both LaTeX math mode
    and plain text contexts (tables, inline prose).

    Examples:
        775 -> "775"
        1834 -> "1,834"
        28073 -> "28,073"
    """
    s = str(n)
    if len(s) <= 3:
        return s
    # Insert comma separators from right
    parts = []
    while len(s) > 3:
        parts.append(s[-3:])
        s = s[:-3]
    parts.append(s)
    return ",".join(reversed(parts))


def _count_jsonl_lines(path: Path) -> int:
    """Count non-empty lines in a JSONL file."""
    if not path.exists():
        return 0
    count = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                count += 1
    return count


def _load_json(path: Path) -> dict:
    """Load a JSON file, returning error sentinel if missing."""
    if not path.exists():
        logger.warning("Variable source file not found: %s", path)
        return {"_error": f"file_not_found: {path}"}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _count_total_references(corpus_path: Path) -> int:
    """Count total references across all papers in a corpus JSONL.

    Sums the length of 'references' or 'referenced_works' lists from each paper.
    """
    if not corpus_path.exists():
        return 0
    total = 0
    with open(corpus_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                paper = json.loads(line)
                refs = paper.get("references", paper.get("referenced_works", []))
                if isinstance(refs, list):
                    total += len(refs)
            except json.JSONDecodeError:
                continue
    return total


def _load_config(project_root: Path) -> dict:
    """Load manuscript/config.yaml; return {} if missing or yaml unavailable."""
    config_path = project_root / "manuscript" / "config.yaml"
    if not config_path.exists():
        logger.warning("config.yaml not found at %s; domain tokens use fallbacks", config_path)
        return {}
    try:
        import yaml
    except ImportError:  # pragma: no cover - yaml is a hard dependency
        return {}
    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data if isinstance(data, dict) else {}


def _humanize_list(items: list[str]) -> str:
    """Join names as an English list: [a] -> 'a'; [a,b] -> 'a and b'; [a,b,c] -> 'a, b, and c'."""
    items = [str(i) for i in items]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def _humanize_key(key: str) -> str:
    """Turn a config key like 'clinical_sleep' into a label 'Clinical Sleep'."""
    return key.replace("_", " ").title()


def compute_variables(output_dir: Path) -> dict[str, str]:
    """Read all pipeline output JSONs and compute template variables.

    Args:
        output_dir: Path to the project's output/ directory containing
                    corpus.jsonl, temporal_analysis.json, citation_network.json,
                    subfield_classification.json, assertion_summary.json, etc.

    Returns:
        Dictionary mapping variable names (e.g., "CORPUS_SIZE") to
        pre-formatted string values ready for manuscript injection.
        All LaTeX-specific formatting (thousand separators, escaping)
        is applied here.
    """
    variables: dict[str, str] = {}
    data_dir = output_dir / "data"
    project_root = output_dir.parent

    # ── Configuration-driven domain tokens ───────────────────────────
    # Everything domain-specific in the manuscript (the search term, keyword
    # list, retrieval engines, subfield taxonomy, and hypotheses explored) is
    # sourced from manuscript/config.yaml so that re-targeting the config
    # re-targets the entire paper. These tokens carry the DEFINITIONS; the
    # measured counts/scores below are merged in from the analysis outputs.
    cfg = _load_config(project_root)
    search_cfg = cfg.get("project_config", {}).get("search", {})
    term = str(search_cfg.get("term") or "the target topic")
    variables["SEARCH_TERM"] = term
    variables["SEARCH_TERM_TITLE"] = term.title()
    keywords = cfg.get("keywords") or []
    variables["KEYWORDS_LIST"] = ", ".join(str(k) for k in keywords)
    rel_kw = search_cfg.get("relevance_keywords") or []
    variables["KEYWORDS_RELEVANCE"] = ", ".join(str(k) for k in rel_kw)

    engines_cfg = search_cfg.get("engines") or {}
    _engine_labels = {
        "arxiv": "arXiv",
        "openalex": "OpenAlex",
        "semantic_scholar": "Semantic Scholar",
        "crossref": "Crossref",
        "pubmed": "PubMed",
        "sovietrxiv": "SovietRxiv",
        "chinarxiv": "ChinaRxiv",
    }
    enabled_engines = [_engine_labels.get(name, name) for name, on in engines_cfg.items() if on]
    if not enabled_engines:
        enabled_engines = ["arXiv", "OpenAlex", "Semantic Scholar", "Crossref", "PubMed", "SovietRxiv", "ChinaRxiv"]
    variables["N_ENGINES"] = str(len(enabled_engines))
    variables["ENGINE_LIST"] = _humanize_list(enabled_engines)

    # ── Corpus size ──────────────────────────────────────────────────
    corpus_path = data_dir / "corpus.jsonl"
    if not corpus_path.exists():
        # Fall back to output root for legacy layout
        corpus_path = output_dir / "corpus.jsonl"
    corpus_size = _count_jsonl_lines(corpus_path)
    variables["CORPUS_SIZE"] = str(corpus_size)
    variables["CORPUS_SIZE_LATEX"] = _latex_number(corpus_size)
    logger.info("CORPUS_SIZE = %d", corpus_size)

    # ── Temporal analysis ────────────────────────────────────────────
    temporal = _load_json(data_dir / "temporal_analysis.json")
    if temporal.get("_error") is not None:
        temporal = _load_json(output_dir / "temporal_analysis.json")
    if temporal and "_error" not in temporal:
        variables["YEAR_START"] = str(temporal.get("first_year", ""))
        variables["YEAR_END"] = str(temporal.get("last_year", ""))
        variables["YEAR_START_PUBS"] = str(temporal.get("year_counts", {}).get(str(temporal.get("first_year", "")), ""))
        variables["PEAK_YEAR"] = str(temporal.get("peak_year", ""))

        peak_year_val = str(temporal.get("year_counts", {}).get(str(temporal.get("peak_year", "")), ""))
        variables["PEAK_YEAR_COUNT"] = peak_year_val
        variables["PEAK_YEAR_PUBS"] = peak_year_val

        cagr = temporal.get("cagr", 0)
        variables["CAGR_PCT"] = f"{cagr * 100:.2f}"

        mean_growth = temporal.get("mean_growth_rate", 0)
        variables["MEAN_YOY_GROWTH_PCT"] = f"{mean_growth * 100:.1f}"

        doubling = temporal.get("doubling_time", 0)
        variables["DOUBLING_TIME"] = f"{doubling:.1f}" if doubling else ""

        # Additional temporal metrics
        year_counts = temporal.get("year_counts", {})
        total_papers_temporal = temporal.get("total_papers", corpus_size)
        variables["TEMPORAL_TOTAL_PAPERS"] = str(total_papers_temporal)
        variables["YEAR_SPAN"] = str(int(temporal.get("last_year", 0)) - int(temporal.get("first_year", 0)))

        # Build year-count table (top 10 years by count)
        if year_counts:
            sorted_years = sorted(year_counts.items(), key=lambda x: -x[1])[:10]
            yc_rows = ["| Year | Publications |", "| --- | --- |"]
            for year, count in sorted(sorted_years, key=lambda x: x[0]):
                yc_rows.append(f"| {year} | {count} |")
            variables["YEAR_COUNT_TABLE"] = "\n".join(yc_rows)
        else:
            variables["YEAR_COUNT_TABLE"] = "| Year | Publications |\n| --- | --- |"
    else:
        logger.warning("temporal_analysis.json not found; temporal variables empty")

    # ── Citation network ─────────────────────────────────────────────
    citation = _load_json(data_dir / "citation_network.json")
    if citation.get("_error") is not None:
        citation = _load_json(output_dir / "citation_network.json")
    if citation and "_error" not in citation:
        edges = citation.get("num_edges", 0)
        nodes = citation.get("num_nodes", corpus_size)
        components = citation.get("connected_components", 0)
        density = citation.get("density", 0)
        avg_in = citation.get("avg_in_degree", 0)

        variables["CITATION_EDGES"] = _latex_number(edges)
        variables["CITATION_EDGES_RAW"] = str(edges)
        variables["CITATION_NODES"] = str(nodes)
        variables["CITATION_COMPONENTS"] = str(components)

        # Density as percentage
        density_pct = density * 100 if density < 1 else density
        variables["CITATION_DENSITY_PCT"] = f"{density_pct:.2f}"

        # Mean in-degree (use pipeline value directly)
        variables["MEAN_IN_DEGREE"] = f"{avg_in:.1f}"

        # Total references and resolution rate
        # These may need to be computed from corpus data
        total_refs = citation.get("total_references", 0)
        if total_refs > 0:
            variables["CITATION_TOTAL_REFS"] = _latex_number(total_refs)
            variables["CITATION_TOTAL_REFS_RAW"] = str(total_refs)
            resolution = (edges / total_refs) * 100
            variables["CITATION_RESOLUTION_PCT"] = f"{resolution:.1f}"
        else:
            # Compute from corpus JSONL if not in citation JSON
            ref_count = _count_total_references(data_dir / "corpus.jsonl")
            if ref_count == 0:
                ref_count = _count_total_references(output_dir / "corpus.jsonl")
            if ref_count > 0:
                variables["CITATION_TOTAL_REFS"] = _latex_number(ref_count)
                variables["CITATION_TOTAL_REFS_RAW"] = str(ref_count)
                resolution = (edges / ref_count) * 100
                variables["CITATION_RESOLUTION_PCT"] = f"{resolution:.1f}"
            else:
                variables["CITATION_TOTAL_REFS"] = "0"
                variables["CITATION_TOTAL_REFS_RAW"] = "0"
                variables["CITATION_RESOLUTION_PCT"] = "0.0"

        # Communities
        communities = citation.get("num_communities", "")
        variables["CITATION_COMMUNITIES"] = str(communities)

        # Additional citation network metrics
        max_in = citation.get("max_in_degree", 0)
        max_out = citation.get("max_out_degree", 0)
        avg_out = citation.get("avg_out_degree", avg_in)
        variables["CITATION_MAX_IN_DEGREE"] = str(max_in)
        variables["CITATION_MAX_OUT_DEGREE"] = str(max_out)
        variables["CITATION_AVG_OUT_DEGREE"] = f"{avg_out:.1f}"

        # Top-cited papers by PageRank
        top_pr = citation.get("top_pagerank", {})
        if isinstance(top_pr, dict) and top_pr:
            pr_items = sorted(top_pr.items(), key=lambda x: -x[1])[:5]
            pr_rows = ["| Rank | DOI | PageRank |", "| --- | --- | --- |"]
            for i, (doi, score) in enumerate(pr_items, 1):
                clean_doi = doi.replace("doi:", "")
                pr_rows.append(f"| {i} | {clean_doi} | {score:.6f} |")
            variables["TOP_PAGERANK_TABLE"] = "\n".join(pr_rows)
            variables["TOP_PAGERANK_DOI"] = pr_items[0][0].replace("doi:", "")
        else:
            variables["TOP_PAGERANK_TABLE"] = "| Rank | DOI | PageRank |\n| --- | --- | --- |"
            variables["TOP_PAGERANK_DOI"] = ""

        # Top authority papers
        top_auth = citation.get("top_authorities", {})
        if isinstance(top_auth, dict) and top_auth:
            auth_items = sorted(top_auth.items(), key=lambda x: -x[1])[:5]
            auth_rows = ["| Rank | DOI | Authority |", "| --- | --- | --- |"]
            for i, (doi, score) in enumerate(auth_items, 1):
                clean_doi = doi.replace("doi:", "")
                auth_rows.append(f"| {i} | {clean_doi} | {score:.6f} |")
            variables["TOP_AUTHORITIES_TABLE"] = "\n".join(auth_rows)
        else:
            variables["TOP_AUTHORITIES_TABLE"] = "| Rank | DOI | Authority |\n| --- | --- | --- |"

        # Top hub papers
        top_hubs = citation.get("top_hubs", {})
        if isinstance(top_hubs, dict) and top_hubs:
            hub_items = sorted(top_hubs.items(), key=lambda x: -x[1])[:5]
            hub_rows = ["| Rank | DOI | Hub |", "| --- | --- | --- |"]
            for i, (doi, score) in enumerate(hub_items, 1):
                clean_doi = doi.replace("doi:", "")
                hub_rows.append(f"| {i} | {clean_doi} | {score:.6f} |")
            variables["TOP_HUBS_TABLE"] = "\n".join(hub_rows)
        else:
            variables["TOP_HUBS_TABLE"] = "| Rank | DOI | Hub |\n| --- | --- | --- |"
    else:
        logger.warning("citation_network.json not found; citation variables empty")

    # ── Subfield classification (config-driven, arbitrary taxonomy) ──
    # The subfield taxonomy is whatever `project_config.subfield_keywords`
    # declares — any number of named buckets. We render a Markdown table whose
    # rows are the CONFIGURED subfields, with measured counts merged from
    # subfield_classification.json (0 / "—" when the analysis has not run).
    subfield_cfg = cfg.get("project_config", {}).get("subfield_keywords", {}) or {}
    subfield_names = list(subfield_cfg.keys())
    variables["N_SUBFIELDS"] = str(len(subfield_names))
    variables["SUBFIELD_LIST"] = _humanize_list([_humanize_key(k) for k in subfield_names])

    subfield = _load_json(data_dir / "subfield_classification.json")
    if subfield.get("_error") is not None:
        subfield = _load_json(output_dir / "subfield_classification.json")
    counts = subfield if (subfield and "_error" not in subfield) else {}
    total = sum(v for v in counts.values() if isinstance(v, int)) if counts else 0

    table_rows = ["| Subfield | Papers | Share |", "| --- | --- | --- |"]
    if not subfield_names:
        # No configured taxonomy — fall back to whatever the classifier emitted.
        subfield_names = [k for k in counts if not str(k).startswith("_")]
    for name in subfield_names:
        count = counts.get(name, 0)
        if counts:
            pct = (count / total * 100) if total > 0 else 0.0
            table_rows.append(f"| {_humanize_key(name)} | {count} | {pct:.1f}% |")
        else:
            table_rows.append(f"| {_humanize_key(name)} | — | — |")
    variables["SUBFIELD_TABLE"] = "\n".join(table_rows)
    if counts and total > 0:
        top_name = max(subfield_names, key=lambda n: counts.get(n, 0))
        variables["TOP_SUBFIELD"] = _humanize_key(top_name)
        variables["TOP_SUBFIELD_PCT"] = f"{counts.get(top_name, 0) / total * 100:.1f}"
    else:
        variables["TOP_SUBFIELD"] = _humanize_key(subfield_names[0]) if subfield_names else "—"
        variables["TOP_SUBFIELD_PCT"] = "—"

    # ── Assertion summary (if available) ─────────────────────────────
    assertion = _load_json(data_dir / "assertion_summary.json")
    if assertion.get("_error") is not None:
        assertion = _load_json(output_dir / "assertion_summary.json")
    if assertion and "_error" not in assertion:
        total_assertions = assertion.get("total_assertions", 0)
        variables["TOTAL_ASSERTIONS"] = _latex_number(total_assertions)
        variables["TOTAL_ASSERTIONS_RAW"] = str(total_assertions)

        # Per-hypothesis counts — JSON uses "per_hypothesis" key
        hyp_counts = assertion.get("per_hypothesis", assertion.get("hypothesis_counts", {}))
        for hid, hdata in hyp_counts.items():
            if isinstance(hdata, dict):
                sup = hdata.get("supports", 0)
                con = hdata.get("contradicts", 0)
                neu = hdata.get("neutral", 0)
                total = sup + con + neu
                variables[f"{hid}_SUPPORT"] = str(sup)
                variables[f"{hid}_CONTRADICT"] = str(con)
                variables[f"{hid}_NEUTRAL"] = str(neu)
                variables[f"{hid}_TOTAL"] = str(total)

        # Overall assertion direction percentages
        type_counts = assertion.get("type_counts", {})
        total_sup = type_counts.get("supports", 0)
        total_con = type_counts.get("contradicts", 0)
        total_sc = total_sup + total_con
        if total_sc > 0:
            variables["ASSERTION_SUPPORT_PCT"] = f"{(total_sup / total_sc * 100):.1f}"
            variables["ASSERTION_CONTRADICT_PCT"] = f"{(total_con / total_sc * 100):.1f}"
        else:
            variables["ASSERTION_SUPPORT_PCT"] = "0.0"
            variables["ASSERTION_CONTRADICT_PCT"] = "0.0"
    else:
        logger.info("assertion_summary.json not found; assertion variables skipped")

    # ── Hypothesis scores (if available) ─────────────────────────────
    scores = _load_json(data_dir / "hypothesis_scores.json")
    if scores.get("_error") is not None:
        scores = _load_json(output_dir / "hypothesis_scores.json")
    if scores and "_error" not in scores:
        for hid, score_val in scores.items():
            if isinstance(score_val, (int, float)):
                variables[f"{hid}_SCORE"] = f"{score_val:+.2f}"
            elif isinstance(score_val, dict):
                s = score_val.get("score", 0)
                variables[f"{hid}_SCORE"] = f"{s:+.2f}"
    else:
        logger.info("hypothesis_scores.json not found; score variables skipped")

    # ── Hypotheses explored (config-driven, arbitrary set) ───────────
    # The hypotheses are whatever `project_config.hypothesis_definitions`
    # declares. We render their names/scope from config and merge an evidence
    # score from hypothesis_scores.json when the (optional, LLM-gated)
    # knowledge-graph stage has run — otherwise the score reads "pending".
    hyp_defs = cfg.get("project_config", {}).get("hypothesis_definitions", {}) or {}
    variables["N_HYPOTHESES"] = str(len(hyp_defs))
    score_lookup: dict[str, float] = {}
    if scores and "_error" not in scores:
        for hid, sv in scores.items():
            if isinstance(sv, (int, float)):
                score_lookup[hid] = float(sv)
            elif isinstance(sv, dict) and isinstance(sv.get("score"), (int, float)):
                score_lookup[hid] = float(sv["score"])

    # Bridge the config-key → internal-hypothesis-id mapping the KG scorer uses
    # (H1 → PRIMARY_EFFICACY, …). Without it, hypothesis_scores.json (keyed by the
    # internal id) can't be looked up from the config key and every row reads
    # "pending" even after the knowledge-graph stage scored every hypothesis.
    try:
        from knowledge_graph.hypothesis import config_key_to_hypothesis_id
    except ImportError:  # pragma: no cover - KG package always present in template

        def config_key_to_hypothesis_id(key: str, name: str = "") -> str:  # type: ignore[misc]
            return key

    def _score_for(hid: str, hname: str) -> str:
        mapped = config_key_to_hypothesis_id(hid, hname)
        for key in (hid, mapped, hname, hname.upper().replace(" ", "_")):
            if key in score_lookup:
                return f"{score_lookup[key]:+.2f}"
        return "pending"

    hyp_list_parts: list[str] = []
    hyp_table = ["| ID | Hypothesis | Scope | Evidence score |", "| --- | --- | --- | --- |"]
    for hid, hdef in hyp_defs.items():
        hname = str((hdef or {}).get("name", hid)) if isinstance(hdef, dict) else str(hdef)
        hscope = str((hdef or {}).get("scope", "")) if isinstance(hdef, dict) else ""
        hyp_list_parts.append(f"{hid} {hname}")
        hyp_table.append(f"| {hid} | {hname} | {hscope} | {_score_for(hid, hname)} |")
    variables["HYPOTHESIS_LIST"] = "; ".join(hyp_list_parts)
    variables["HYPOTHESIS_TABLE"] = "\n".join(hyp_table)

    # ── Figure count ─────────────────────────────────────────────────
    figures_dir = output_dir / "figures"
    if figures_dir.exists():
        fig_count = len(list(figures_dir.glob("*.png")))
        variables["NUM_FIGURES"] = str(fig_count)
    else:
        variables["NUM_FIGURES"] = "16"
        logger.warning(
            "Figures directory not found at %s; defaulting NUM_FIGURES to 16 (canonical count)",
            figures_dir,
        )

    # ── NMF topics (if available) ────────────────────────────────────
    topics = _load_json(data_dir / "topics.json")
    if isinstance(topics, dict) and topics.get("_error") is not None:
        topics = _load_json(output_dir / "topics.json")
    if topics and "_error" not in topics:
        topic_list = topics if isinstance(topics, list) else topics.get("topics", [])
        variables["NUM_TOPICS"] = str(len(topic_list))

        # Build topic table
        topic_rows = ["| Topic | Top terms |", "| --- | --- |"]
        for t in topic_list:
            if isinstance(t, dict):
                tid = t.get("topic_id", "")
                words = t.get("top_words", [])
                top_words = ", ".join(str(w) for w in words[:8])
                topic_rows.append(f"| {tid} | {top_words} |")
        variables["TOPIC_TABLE"] = "\n".join(topic_rows)
    else:
        variables["TOPIC_TABLE"] = "| Topic | Top terms |\n| --- | --- |"

    # ── TF-IDF vocabulary size ────────────────────────────────────────
    tfidf = _load_json(data_dir / "tfidf_data.json")
    if tfidf.get("_error") is not None:
        tfidf = _load_json(output_dir / "tfidf_data.json")
    if tfidf and "_error" not in tfidf:
        feature_names = tfidf.get("feature_names", [])
        num_vocab = len(feature_names)
        variables["NUM_VOCAB_FEATURES"] = str(num_vocab)
        variables["NUM_VOCAB_FEATURES_LATEX"] = _latex_number(num_vocab)
        logger.info("NUM_VOCAB_FEATURES = %d", num_vocab)

        # Top TF-IDF terms
        if feature_names:
            variables["TOP_VOCAB_TERMS"] = ", ".join(str(t) for t in feature_names[:20])
    else:
        variables["NUM_VOCAB_FEATURES"] = "500"  # Canonical default from pipeline
        variables["NUM_VOCAB_FEATURES_LATEX"] = "500"
        variables["TOP_VOCAB_TERMS"] = ""
        logger.warning("tfidf_data.json not found; defaulting NUM_VOCAB_FEATURES to 500")

    # ── Fulltext assessment ───────────────────────────────────────────
    fulltext = _load_json(data_dir / "fulltext_assessment.json")
    if fulltext.get("_error") is not None:
        fulltext = _load_json(output_dir / "fulltext_assessment.json")
    if fulltext and "_error" not in fulltext:
        abstract_cov = fulltext.get("abstract_coverage", {})
        variables["ABSTRACT_COVERAGE_PCT"] = f"{abstract_cov.get('percent_with_abstract', 0):.1f}"
        variables["ABSTRACT_COUNT"] = str(abstract_cov.get("has_abstract", 0))
        variables["NO_ABSTRACT_COUNT"] = str(abstract_cov.get("no_abstract", 0))

        oa = fulltext.get("open_access", {})
        variables["OA_COUNT"] = str(oa.get("is_oa", 0))
        variables["OA_PCT"] = f"{oa.get('percent_oa', 0):.1f}"

        pdf_avail = fulltext.get("pdf_availability", {})
        variables["PDF_AVAIL_COUNT"] = str(pdf_avail.get("has_pdf_url", 0))
        variables["PDF_AVAIL_PCT"] = f"{pdf_avail.get('percent_with_pdf', 0):.1f}"

        id_cov = fulltext.get("identifier_coverage", {})
        variables["DOI_COUNT"] = str(id_cov.get("doi", 0))
        variables["ARXIV_ID_COUNT"] = str(id_cov.get("arxiv_id", 0))
        variables["OPENALEX_ID_COUNT"] = str(id_cov.get("openalex_id", 0))

        ft_format = fulltext.get("fulltext_format", {})
        variables["PUBLISHER_PDF_COUNT"] = str(ft_format.get("publisher_pdf_only", 0))
        variables["NO_FULLTEXT_COUNT"] = str(ft_format.get("no_fulltext_available", 0))
    else:
        logger.info("fulltext_assessment.json not found; fulltext variables skipped")

    # ── Descriptive statistics ────────────────────────────────────────
    desc = _load_json(data_dir / "descriptive_stats.json")
    if desc.get("_error") is not None:
        desc = _load_json(output_dir / "descriptive_stats.json")
    if desc and "_error" not in desc:
        ds = desc.get("descriptive_stats", {})
        if isinstance(ds, dict):
            variables["UNIQUE_AUTHORS"] = str(ds.get("unique_authors", 0))
            variables["CITATION_MEAN"] = f"{ds.get('citation_count_mean', 0):.1f}"
            variables["CITATION_MEDIAN"] = f"{ds.get('citation_count_median', 0):.1f}"
            variables["CITATION_MAX"] = str(ds.get("citation_count_max", 0))
            variables["CITATION_TOTAL"] = _latex_number(ds.get("citation_count_total", 0))
            variables["PAPERS_PER_AUTHOR_MEAN"] = f"{ds.get('papers_per_author_mean', 0):.2f}"
            variables["PCT_WITH_DOI"] = f"{ds.get('pct_with_doi', 0):.1f}"

            # Top venues table
            venues = ds.get("counts_by_venue", {})
            if isinstance(venues, dict) and venues:
                sorted_venues = sorted(venues.items(), key=lambda x: -x[1])[:10]
                v_rows = ["| Venue | Papers |", "| --- | --- |"]
                for venue, count in sorted_venues:
                    v_rows.append(f"| {venue[:50]} | {count} |")
                variables["TOP_VENUES_TABLE"] = "\n".join(v_rows)
            else:
                variables["TOP_VENUES_TABLE"] = "| Venue | Papers |\n| --- | --- |"

        # Citation distribution (Gini)
        cd = desc.get("citation_distribution", {})
        if isinstance(cd, dict):
            variables["GINI_COEFFICIENT"] = f"{cd.get('gini', 0):.3f}"
            variables["CITATION_DIST_N"] = str(cd.get("n", 0))

            # Build histogram table
            hist = cd.get("histogram", {})
            if isinstance(hist, dict) and hist:
                h_rows = ["| Citations | Papers |", "| --- | --- |"]
                for label, count in hist.items():
                    h_rows.append(f"| {label} | {count} |")
                variables["CITATION_DIST_TABLE"] = "\n".join(h_rows)
            else:
                variables["CITATION_DIST_TABLE"] = "| Citations | Papers |\n| --- | --- |"

        # Author productivity table
        authors = desc.get("author_productivity", [])
        if isinstance(authors, list) and authors:
            a_rows = ["| Rank | Author | Papers |", "| --- | --- | --- |"]
            for i, entry in enumerate(authors[:10], 1):
                if isinstance(entry, list) and len(entry) >= 2:
                    a_rows.append(f"| {i} | {entry[0][:40]} | {entry[1]} |")
            variables["TOP_AUTHORS_TABLE"] = "\n".join(a_rows)
        else:
            variables["TOP_AUTHORS_TABLE"] = "| Rank | Author | Papers |\n| --- | --- | --- |"
    else:
        logger.info("descriptive_stats.json not found; descriptive variables skipped")

    # ── Entity and keyphrase analysis ─────────────────────────────────
    entities = _load_json(data_dir / "entities.json")
    if entities and "_error" not in entities:
        if isinstance(entities, dict):
            sorted_ent = sorted(entities.items(), key=lambda x: -x[1])[:15]
            e_rows = ["| Entity | Frequency |", "| --- | --- |"]
            for name, count in sorted_ent:
                e_rows.append(f"| {name[:40]} | {count} |")
            variables["TOP_ENTITIES_TABLE"] = "\n".join(e_rows)
            variables["NUM_ENTITIES"] = str(len(entities))
        else:
            variables["TOP_ENTITIES_TABLE"] = "| Entity | Frequency |\n| --- | --- |"
            variables["NUM_ENTITIES"] = "0"
    else:
        variables["TOP_ENTITIES_TABLE"] = "| Entity | Frequency |\n| --- | --- |"
        variables["NUM_ENTITIES"] = "0"

    keyphrases = _load_json(data_dir / "keyphrases.json")
    if keyphrases and "_error" not in keyphrases:
        kp_list = keyphrases.get("top_keyphrases", []) if isinstance(keyphrases, dict) else []
        if kp_list:
            k_rows = ["| Keyphrase | Score |", "| --- | --- |"]
            for entry in kp_list[:15]:
                if isinstance(entry, dict):
                    k_rows.append(f"| {entry.get('phrase', '')[:40]} | {entry.get('score', 0):.4f} |")
            variables["TOP_KEYPHRASES_TABLE"] = "\n".join(k_rows)
            variables["NUM_KEYPHRASES"] = str(len(kp_list))
        else:
            variables["TOP_KEYPHRASES_TABLE"] = "| Keyphrase | Score |\n| --- | --- |"
            variables["NUM_KEYPHRASES"] = "0"
    else:
        variables["TOP_KEYPHRASES_TABLE"] = "| Keyphrase | Score |\n| --- | --- |"
        variables["NUM_KEYPHRASES"] = "0"

    # ── Embedding analysis ────────────────────────────────────────────
    emb = _load_json(data_dir / "embedding_analysis.json")
    if emb and "_error" not in emb:
        variables["NUM_EMBEDDING_CLUSTERS"] = str(emb.get("num_clusters", 0))
        pairs = emb.get("top_similar_pairs", [])
        if isinstance(pairs, list) and pairs:
            p_rows = ["| Paper A | Paper B | Similarity |", "| --- | --- | --- |"]
            for p in pairs[:10]:
                if isinstance(p, dict):
                    p_rows.append(
                        f"| {p.get('paper_a', '')[:30]} | {p.get('paper_b', '')[:30]} | {p.get('similarity', 0):.4f} |"
                    )
            variables["TOP_SIMILAR_PAIRS_TABLE"] = "\n".join(p_rows)
        else:
            variables["TOP_SIMILAR_PAIRS_TABLE"] = "| Paper A | Paper B | Similarity |\n| --- | --- | --- |"
    else:
        variables["NUM_EMBEDDING_CLUSTERS"] = "0"
        variables["TOP_SIMILAR_PAIRS_TABLE"] = "| Paper A | Paper B | Similarity |\n| --- | --- | --- |"

    # ── Advanced citation network metrics ─────────────────────────────
    # These are added to the citation_network.json by the pipeline
    if citation and "_error" not in citation:
        variables["DEGREE_ASSORTATIVITY"] = f"{citation.get('degree_assortativity', 0):.4f}"
        variables["AVG_CLUSTERING"] = f"{citation.get('avg_clustering', 0):.4f}"

        top_betw = citation.get("top_betweenness", {})
        if isinstance(top_betw, dict) and top_betw:
            betw_items = sorted(top_betw.items(), key=lambda x: -x[1])[:5]
            betw_rows = ["| Rank | DOI | Betweenness |", "| --- | --- | --- |"]
            for i, (doi, score) in enumerate(betw_items, 1):
                betw_rows.append(f"| {i} | {doi.replace('doi:', '')[:40]} | {score:.6f} |")
            variables["TOP_BETWEENNESS_TABLE"] = "\n".join(betw_rows)
        else:
            variables["TOP_BETWEENNESS_TABLE"] = "| Rank | DOI | Betweenness |\n| --- | --- | --- |"
    else:
        variables["DEGREE_ASSORTATIVITY"] = "0.0000"
        variables["AVG_CLUSTERING"] = "0.0000"
        variables["TOP_BETWEENNESS_TABLE"] = "| Rank | DOI | Betweenness |\n| --- | --- | --- |"

    logger.info("Computed %d template variables from pipeline output", len(variables))
    return variables


def inject_variables(
    content: str,
    variables: dict[str, str],
    filename: str = "<unknown>",
    lenient: bool = False,
) -> str:
    """Replace {{VAR_NAME}} placeholders in content with variable values.

    Args:
        content: Manuscript markdown content with {{VAR}} placeholders.
        variables: Dictionary of variable name -> formatted value.
        filename: Source filename for logging.
        lenient: If True, warn and leave unresolved placeholders as-is.
                If False (default), raise RuntimeError on any unresolved variable.

    Returns:
        Content with all recognized placeholders replaced.

    Raises:
        RuntimeError: If lenient=False and unresolved variables remain.
    """
    replaced_count = 0
    missing_vars = []

    def replacer(match: re.Match) -> str:
        """Replace a matched placeholder with its corresponding variable value."""
        nonlocal replaced_count
        var_name = match.group(1)
        if var_name in variables:
            replaced_count += 1
            return variables[var_name]
        else:
            missing_vars.append(var_name)
            return match.group(0)  # Leave unresolved

    result = re.sub(r"\{\{(\w+)\}\}", replacer, content)

    if replaced_count > 0:
        logger.info("Injected %d variables into %s", replaced_count, filename)

    if missing_vars:
        unique_missing = sorted(set(missing_vars))
        if lenient:
            logger.warning(
                "Unresolved variables in %s: %s",
                filename,
                ", ".join(unique_missing),
            )
        else:
            raise RuntimeError(f"Unresolved variables in {filename}: {', '.join(unique_missing)}")

    return result
