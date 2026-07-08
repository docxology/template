"""Config-driven domain tokens."""

from __future__ import annotations

from manuscript.variables.context import ExtractContext
from manuscript.variables.formatters import humanize_list, latex_number


def extract_config_tokens(ctx: ExtractContext) -> dict[str, str]:
    """Process extract config tokens."""
    variables: dict[str, str] = {}
    search_cfg = ctx.cfg.get("project_config", {}).get("search", {})
    term = str(search_cfg.get("term") or "the target topic")
    variables["SEARCH_TERM"] = term
    variables["SEARCH_TERM_TITLE"] = term.title()
    keywords = ctx.cfg.get("keywords") or []
    variables["KEYWORDS_LIST"] = ", ".join(str(k) for k in keywords)
    rel_kw = search_cfg.get("relevance_keywords") or []
    variables["KEYWORDS_RELEVANCE"] = ", ".join(str(k) for k in rel_kw)
    engines_cfg = search_cfg.get("engines") or {}
    engine_labels = {
        "arxiv": "arXiv",
        "openalex": "OpenAlex",
        "semantic_scholar": "Semantic Scholar",
        "crossref": "Crossref",
        "pubmed": "PubMed",
        "sovietrxiv": "SovietRxiv",
        "chinarxiv": "ChinaRxiv",
    }
    enabled = [engine_labels.get(name, name) for name, on in engines_cfg.items() if on]
    if not enabled:
        enabled = list(engine_labels.values())
    variables["N_ENGINES"] = str(len(enabled))
    variables["ENGINE_LIST"] = humanize_list(enabled)
    variables["CORPUS_SIZE"] = str(ctx.corpus_size)
    variables["CORPUS_SIZE_LATEX"] = latex_number(ctx.corpus_size)
    return variables
