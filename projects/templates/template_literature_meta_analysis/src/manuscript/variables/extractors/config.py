"""Config-driven domain tokens."""

from __future__ import annotations

from manuscript.variables.context import ExtractContext
from manuscript.variables.formatters import humanize_list, latex_number


def extract_config_tokens(ctx: ExtractContext) -> dict[str, str]:
    """Extract configuration-based template variables.

    Returns domain-agnostic configuration tokens including search terms,
    enabled engines, and corpus size. Handles missing configuration gracefully
    with sensible fallbacks.
    """
    variables: dict[str, str] = {}

    # Search configuration with fallbacks
    search_cfg = ctx.cfg.get("project_config", {}).get("search", {})
    term = str(search_cfg.get("term") or "the target topic")
    variables["SEARCH_TERM"] = term
    variables["SEARCH_TERM_TITLE"] = term.title()

    # Keywords and relevance terms
    keywords = ctx.cfg.get("keywords") or []
    variables["KEYWORDS_LIST"] = ", ".join(str(k) for k in keywords)
    rel_kw = search_cfg.get("relevance_keywords") or []
    variables["KEYWORDS_RELEVANCE"] = ", ".join(str(k) for k in rel_kw)

    # Engine configuration with pretty names
    engines_cfg = search_cfg.get("engines") or {}
    engine_labels = {
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

    # Only include enabled engines, fallback to all if none specified
    enabled = [engine_labels.get(name, name) for name, on in engines_cfg.items() if on]
    if not enabled:
        enabled = list(engine_labels.values())

    variables["N_ENGINES"] = str(len(enabled))
    variables["ENGINE_LIST"] = humanize_list(enabled)

    # Corpus size with error handling
    try:
        corpus_size = ctx.corpus_size
        variables["CORPUS_SIZE"] = str(corpus_size)
        variables["CORPUS_SIZE_LATEX"] = latex_number(corpus_size)
    except Exception:
        # Fallback for missing or corrupt corpus
        variables["CORPUS_SIZE"] = "0"
        variables["CORPUS_SIZE_LATEX"] = "0"
        # Note: ExtractContext should handle corpus loading errors upstream

    return variables
