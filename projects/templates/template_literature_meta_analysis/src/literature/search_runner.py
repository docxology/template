"""Literature search pipeline (multi-source retrieval and corpus persistence)."""

from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path
from typing import Callable, TypedDict

from config_loader import load_search_config
from config_validation import require_valid_search_config
from literature.corpus import Corpus
from literature.models import Paper
from literature.engine_dispatch import dispatch_ordered
from literature.query_router import QueryRouter


class RetrievalObservation(TypedDict, total=False):
    """Deterministic per-source provenance for one retrieval attempt."""

    source: str
    status: str
    fetched: int
    new_records: int
    duplicates: int
    detail: str
    elapsed_seconds: float
    rate_limit_hits: int
    retries: int


def _record_skipped(observations: list[RetrievalObservation], source: str, detail: str) -> None:
    observations.append(
        {
            "source": source,
            "status": "skipped",
            "fetched": 0,
            "new_records": 0,
            "duplicates": 0,
            "detail": detail,
        }
    )


def _write_retrieval_report(
    path: Path,
    *,
    query: str,
    max_results: int,
    corpus_records: int,
    run_mode: str,
    observations: list[RetrievalObservation],
    route: dict[str, object] | None = None,
) -> Path:
    """Persist a timestamp-free retrieval report suitable for exact replay checks."""
    payload = {
        "schema_version": "template-literature-retrieval-report-v1",
        "query": query,
        "max_results_per_engine": max_results,
        "corpus_records": corpus_records,
        "run_mode": run_mode,
        "route": route or {},
        "engines": observations,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)
    return path


def search_source(
    source_name: str,
    search_fn: Callable[..., list[Paper]],
    query: str,
    max_results: int,
    corpus: Corpus,
    logger: logging.Logger,
    *,
    observations: list[RetrievalObservation] | None = None,
) -> str | None:
    """Search one API source and merge papers into *corpus*."""
    t0 = time.monotonic()
    try:
        logger.info("Searching %s for: %s (max %d)", source_name, query[:80], max_results)
        papers = search_fn(query, max_results=max_results)
        before_count = len(corpus)
        for paper in papers:
            corpus.add(paper)
        new_papers = len(corpus) - before_count
        duplicates = len(papers) - new_papers
        elapsed = time.monotonic() - t0
        logger.info(
            "  %s: %d fetched, %d new, %d duplicates (%.1fs)",
            source_name,
            len(papers),
            new_papers,
            duplicates,
            elapsed,
        )
        if observations is not None:
            observations.append(
                {
                    "source": source_name,
                    "status": "ok",
                    "fetched": len(papers),
                    "new_records": new_papers,
                    "duplicates": duplicates,
                    "detail": "",
                    "elapsed_seconds": round(elapsed, 2),
                }
            )
        return f"{source_name} ({len(papers)} papers, {new_papers} new)"
    except Exception as exc:  # noqa: BLE001 -- safety net: one engine failing must not abort multi-engine dispatch
        elapsed = time.monotonic() - t0
        logger.error("  %s search failed after %.1fs: %s", source_name, elapsed, exc)
        if observations is not None:
            observations.append(
                {
                    "source": source_name,
                    "status": "error",
                    "fetched": 0,
                    "new_records": 0,
                    "duplicates": 0,
                    "detail": type(exc).__name__,
                    "elapsed_seconds": round(elapsed, 2),
                }
            )
        return None


def apply_relevance_filter(
    corpus: Corpus,
    keywords: list[str],
    logger: logging.Logger,
) -> None:
    """Drop papers whose title+abstract lack any *keywords*.

    Keywords are matched case-insensitively: the paper text is lower-cased AND so
    are the keywords, so a configured keyword like ``"ADHD"`` or ``"Sleep
    Deprivation"`` matches rather than silently excluding every paper. An empty
    keyword list is treated as "no filter" (a guard against silently wiping the
    whole corpus, since ``any()`` over an empty list is ``False``).
    """
    norm_keywords = [kw.lower() for kw in keywords if kw and kw.strip()]
    if not norm_keywords:
        logger.warning(
            "Relevance filter: no usable keywords configured — skipping filter "
            "(all %d papers retained) to avoid silently emptying the corpus.",
            len(corpus),
        )
        return

    pre_filter = len(corpus)
    to_remove: list[str] = []
    for paper in corpus.papers:
        text = (paper.title + " " + paper.abstract).lower()
        if not any(kw in text for kw in norm_keywords):
            to_remove.append(paper.canonical_id)
    for cid in to_remove:
        corpus.remove(cid)
    if to_remove:
        logger.info(
            "Relevance filter: removed %d off-topic papers (%d → %d)",
            len(to_remove),
            pre_filter,
            len(corpus),
        )
    if pre_filter and len(corpus) == 0:
        logger.warning(
            "Relevance filter removed ALL %d papers — check that relevance_keywords "
            "(%s) actually occur in the retrieved corpus.",
            pre_filter,
            norm_keywords,
        )


def _fast_delay() -> Callable[[float], None]:
    return lambda _seconds: None


def _arxiv_search_fn(
    base_url: str | None,
    *,
    fast: bool,
) -> Callable[..., list[Paper]]:
    from literature.arxiv_client import ARXIV_API_URL, DEFAULT_RATE_LIMIT_SECONDS, search_arxiv

    url = base_url or ARXIV_API_URL
    delay = _fast_delay() if fast else None
    rate_limit = 0.0 if fast else DEFAULT_RATE_LIMIT_SECONDS

    def _search(query: str, max_results: int = 100) -> list[Paper]:
        return list(
            search_arxiv(
                query,
                max_results=max_results,
                base_url=url,
                rate_limit_seconds=rate_limit,
                delay_override=delay,
            )
        )

    return _search


def _semantic_scholar_search_fn(
    base_url: str | None,
    *,
    fast: bool,
) -> Callable[..., list[Paper]]:
    from literature.semantic_scholar import S2_API_URL, search_semantic_scholar

    url = base_url or S2_API_URL
    delay = _fast_delay() if fast else None

    def _search(query: str, max_results: int = 100) -> list[Paper]:
        return list(
            search_semantic_scholar(
                query,
                max_results=max_results,
                base_url=url,
                delay_override=delay,
            )
        )

    return _search


def _openalex_search_fn(
    base_url: str | None,
    *,
    fast: bool,
) -> Callable[..., list[Paper]]:
    from literature.openalex_client import OPENALEX_API_URL, search_openalex

    url = base_url or OPENALEX_API_URL
    delay = _fast_delay() if fast else None

    def _search(query: str, max_results: int = 100) -> list[Paper]:
        return list(
            search_openalex(
                query,
                max_results=max_results,
                base_url=url,
                delay_override=delay,
            )
        )

    return _search


def _crossref_search_fn(
    base_url: str | None,
    *,
    fast: bool,
) -> Callable[..., list[Paper]]:
    from literature.crossref_client import CROSSREF_API_URL, search_crossref

    url = base_url or CROSSREF_API_URL
    delay = 0.0 if fast else None

    def _search(query: str, max_results: int = 100) -> list[Paper]:
        return list(search_crossref(query, max_results=max_results, base_url=url, delay_override=delay))

    return _search


def _pubmed_search_fn(
    esearch_url: str | None,
    efetch_url: str | None,
    *,
    fast: bool,
) -> Callable[..., list[Paper]]:
    from literature.pubmed_client import PUBMED_EFETCH_URL, PUBMED_ESEARCH_URL, search_pubmed

    es = esearch_url or PUBMED_ESEARCH_URL
    ef = efetch_url or PUBMED_EFETCH_URL
    delay = 0.0 if fast else None

    def _search(query: str, max_results: int = 100) -> list[Paper]:
        return list(search_pubmed(query, max_results=max_results, esearch_url=es, efetch_url=ef, delay_override=delay))

    return _search


def _sovietrxiv_search_fn(
    base_url: str | None,
    *,
    fast: bool,
    api_email: str | None = None,
    source: str | None = None,
) -> Callable[..., list[Paper]]:
    from literature.sovietrxiv_client import SOVIETRXIV_API_URL, search_sovietrxiv

    url = base_url or SOVIETRXIV_API_URL
    delay = 0.0 if fast else None

    def _search(query: str, max_results: int = 100) -> list[Paper]:
        return list(
            search_sovietrxiv(
                query,
                max_results=max_results,
                base_url=url,
                api_email=api_email,
                source=source,
                delay_override=delay,
            )
        )

    return _search


def _europepmc_search_fn(
    base_url: str | None,
    *,
    fast: bool,
) -> Callable[..., list[Paper]]:
    from literature.europepmc_client import EUROPEPMC_API_URL, search_europepmc

    url = base_url or EUROPEPMC_API_URL
    delay = 0.0 if fast else None

    def _search(query: str, max_results: int = 100) -> list[Paper]:
        return list(search_europepmc(query, max_results=max_results, base_url=url, delay_override=delay))

    return _search


def _biorxiv_search_fn(
    base_url: str | None,
    *,
    fast: bool,
    server: str = "biorxiv",
) -> Callable[..., list[Paper]]:
    from literature.biorxiv_client import BIORXIV_API_URL, search_biorxiv

    url = base_url or BIORXIV_API_URL
    delay = 0.0 if fast else None

    def _search(query: str, max_results: int = 100) -> list[Paper]:
        return list(
            search_biorxiv(
                query,
                max_results=max_results,
                base_url=url,
                delay_override=delay,
                server=server,
            )
        )

    return _search


def run_literature_search(
    args: argparse.Namespace,
    *,
    project_root: Path,
    arxiv_base_url: str | None = None,
    semantic_scholar_base_url: str | None = None,
    openalex_base_url: str | None = None,
    crossref_base_url: str | None = None,
    pubmed_esearch_url: str | None = None,
    pubmed_efetch_url: str | None = None,
    sovietrxiv_base_url: str | None = None,
    chinarxiv_base_url: str | None = None,
    europepmc_base_url: str | None = None,
    biorxiv_base_url: str | None = None,
) -> Path:
    """Execute literature search; return path to saved corpus JSONL.

    Optional ``*_base_url`` kwargs wire pytest-httpserver endpoints into API
    clients without changing production defaults.
    """
    logger = logging.getLogger("literature_search")
    config_path = Path(args.config) if args.config else project_root / "manuscript" / "config.yaml"
    if args.config and not config_path.exists():
        raise FileNotFoundError(f"Configuration file does not exist: {config_path}")
    if config_path.exists():
        require_valid_search_config(
            config_path,
            query_override=getattr(args, "query", None),
        )
        cfg = load_search_config(config_path)
        if cfg.get("query"):
            args.query = cfg["query"]
        if cfg.get("max_results"):
            args.max_results = cfg["max_results"]
        if cfg.get("resume") is not None:
            args.resume = cfg["resume"]
        if cfg.get("clear_corpus") is not None:
            args.clear_corpus = cfg["clear_corpus"]
        if cfg.get("start_year") is not None and args.start_year is None:
            args.start_year = cfg["start_year"]
        arxiv_queries = cfg["arxiv_queries"]
        relevance_keywords = cfg["relevance_keywords"]
        engines = cfg.get("engines", {})
    else:
        from config import DEFAULT_ARXIV_QUERIES, DEFAULT_RELEVANCE_KEYWORDS

        arxiv_queries = list(DEFAULT_ARXIV_QUERIES)
        relevance_keywords = list(DEFAULT_RELEVANCE_KEYWORDS)
        engines = {}
        cfg = {}

    if getattr(args, "query", None) is None:
        q = cfg.get("query") if isinstance(cfg, dict) else None
        if not q and config_path.exists():
            import yaml

            raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            search_block = raw.get("project_config", {}).get("search", {})
            q = search_block.get("query") or search_block.get("term")
        if q:
            args.query = str(q)
        else:
            raise ValueError("Search query missing: pass --query or set project_config.search.query/term in config")

    # Term-driven fallback: when no explicit per-engine queries / keywords are
    # configured, derive them from the single search term. This keeps the
    # template fully domain-agnostic — no hardcoded default queries are needed.
    if not arxiv_queries and getattr(args, "query", None):
        arxiv_queries = [f'all:"{args.query}"']
    if not relevance_keywords and getattr(args, "query", None):
        relevance_keywords = [str(args.query).lower()]

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    corpus_path = data_dir / "corpus.jsonl"
    retrieval_report_path = data_dir / "retrieval_report.json"
    observations: list[RetrievalObservation] = []

    if args.clear_corpus and corpus_path.exists():
        corpus_path.unlink()
        logger.info("Cleared existing corpus: %s", corpus_path)

    if args.resume and corpus_path.exists():
        corpus = Corpus.load(corpus_path)
        logger.info("Resumed existing corpus with %d papers from %s", len(corpus), corpus_path)
        if len(corpus) > 0 and not args.clear_corpus:
            logger.info(
                "Corpus already populated (%d papers) — skipping network searches.",
                len(corpus),
            )
            corpus.save(corpus_path)
            if not retrieval_report_path.exists():
                _write_retrieval_report(
                    retrieval_report_path,
                    query=str(args.query),
                    max_results=int(args.max_results),
                    corpus_records=len(corpus),
                    run_mode="resume_without_prior_retrieval_report",
                    observations=observations,
                )
            print(str(corpus_path))
            return corpus_path
    else:
        corpus = Corpus()

    sources_searched: list[str] = []
    pipeline_start = time.monotonic()

    fast_api = any(
        url is not None
        for url in (
            arxiv_base_url,
            semantic_scholar_base_url,
            openalex_base_url,
            crossref_base_url,
            pubmed_esearch_url,
            sovietrxiv_base_url,
            chinarxiv_base_url,
            europepmc_base_url,
            biorxiv_base_url,
        )
    )

    route = QueryRouter().route(
        args.query,
        [
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
        ],
    )
    logger.info(
        "Routing query as %s (confidence %.2f, preprints=%s)",
        route.query_type,
        route.confidence,
        "preferred" if route.prefer_preprints else "deprioritized",
    )

    def run_arxiv() -> None:
        """Run arxiv."""
        if args.skip_arxiv or not engines.get("arxiv", True):
            _record_skipped(observations, "arXiv", "disabled")
            return
        arxiv_search = _arxiv_search_fn(arxiv_base_url, fast=fast_api)
        arxiv_total_before = len(corpus)
        for i, arxiv_query in enumerate(arxiv_queries, 1):
            logger.info("arXiv query %d/%d: %s", i, len(arxiv_queries), arxiv_query)
            result = search_source(
                f"arXiv[{i}]",
                arxiv_search,
                arxiv_query,
                args.max_results,
                corpus,
                logger,
                observations=observations,
            )
            if result:
                sources_searched.append(result)
        logger.info(
            "arXiv total: %d new unique papers from %d queries",
            len(corpus) - arxiv_total_before,
            len(arxiv_queries),
        )

    def run_semantic_scholar() -> None:
        """Run semantic scholar."""
        if args.skip_s2 or not engines.get("semantic_scholar", True):
            _record_skipped(observations, "Semantic Scholar", "disabled")
            return
        s2_search = _semantic_scholar_search_fn(semantic_scholar_base_url, fast=fast_api)
        result = search_source(
            "Semantic Scholar",
            s2_search,
            args.query,
            args.max_results,
            corpus,
            logger,
            observations=observations,
        )
        if result:
            sources_searched.append(result)

    def run_openalex() -> None:
        """Run openalex."""
        if args.skip_openalex or not engines.get("openalex", True):
            _record_skipped(observations, "OpenAlex", "disabled")
            return
        openalex_search = _openalex_search_fn(openalex_base_url, fast=fast_api)
        result = search_source(
            "OpenAlex",
            openalex_search,
            args.query,
            args.max_results,
            corpus,
            logger,
            observations=observations,
        )
        if result:
            sources_searched.append(result)

    def run_crossref() -> None:
        """Run crossref."""
        crossref_on = engines.get("crossref", True) and not getattr(args, "skip_crossref", False)
        if not crossref_on or (crossref_base_url is None and fast_api):
            _record_skipped(
                observations,
                "Crossref",
                "disabled" if not crossref_on else "not_injected_in_hermetic_run",
            )
            return
        crossref_search = _crossref_search_fn(crossref_base_url, fast=fast_api)
        result = search_source(
            "Crossref",
            crossref_search,
            args.query,
            args.max_results,
            corpus,
            logger,
            observations=observations,
        )
        if result:
            sources_searched.append(result)

    def run_pubmed() -> None:
        """Run pubmed."""
        pubmed_on = engines.get("pubmed", True) and not getattr(args, "skip_pubmed", False)
        if not pubmed_on or (pubmed_esearch_url is None and fast_api):
            _record_skipped(
                observations,
                "PubMed",
                "disabled" if not pubmed_on else "not_injected_in_hermetic_run",
            )
            return
        pubmed_search = _pubmed_search_fn(pubmed_esearch_url, pubmed_efetch_url, fast=fast_api)
        result = search_source(
            "PubMed",
            pubmed_search,
            args.query,
            args.max_results,
            corpus,
            logger,
            observations=observations,
        )
        if result:
            sources_searched.append(result)

    def run_sovietrxiv() -> None:
        """Run sovietrxiv."""
        sovietrxiv_cfg = cfg.get("sovietrxiv", {}) if isinstance(cfg, dict) else {}
        if not engines.get("sovietrxiv", True) or getattr(args, "skip_sovietrxiv", False):
            _record_skipped(observations, "SovietRxiv", "disabled")
            return
        if sovietrxiv_base_url is None and fast_api:
            _record_skipped(observations, "SovietRxiv", "not_injected_in_hermetic_run")
            return
        sovietrxiv_email = sovietrxiv_cfg.get("api_email") if isinstance(sovietrxiv_cfg, dict) else None
        sovietrxiv_source = sovietrxiv_cfg.get("source") if isinstance(sovietrxiv_cfg, dict) else None
        sovietrxiv_search = _sovietrxiv_search_fn(
            sovietrxiv_base_url,
            fast=fast_api,
            api_email=sovietrxiv_email,
            source=sovietrxiv_source,
        )
        result = search_source(
            "SovietRxiv",
            sovietrxiv_search,
            args.query,
            args.max_results,
            corpus,
            logger,
            observations=observations,
        )
        if result:
            sources_searched.append(result)

    def run_chinarxiv() -> None:
        """Run chinarxiv."""
        chinarxiv_cfg = cfg.get("chinarxiv", {}) if isinstance(cfg, dict) else {}
        if not engines.get("chinarxiv", True) or getattr(args, "skip_chinarxiv", False):
            _record_skipped(observations, "ChinaRxiv", "disabled")
            return
        if chinarxiv_base_url is None and fast_api:
            _record_skipped(observations, "ChinaRxiv", "not_injected_in_hermetic_run")
            return
        chinarxiv_email = chinarxiv_cfg.get("api_email") if isinstance(chinarxiv_cfg, dict) else None
        chinarxiv_search = _sovietrxiv_search_fn(
            chinarxiv_base_url,
            fast=fast_api,
            api_email=chinarxiv_email,
            source="chinaxiv",
        )
        result = search_source(
            "ChinaRxiv",
            chinarxiv_search,
            args.query,
            args.max_results,
            corpus,
            logger,
            observations=observations,
        )
        if result:
            sources_searched.append(result)

    def run_europepmc() -> None:
        """Run europepmc."""
        europepmc_on = engines.get("europepmc", True) and not getattr(args, "skip_europepmc", False)
        if not europepmc_on or (europepmc_base_url is None and fast_api):
            _record_skipped(
                observations,
                "Europe PMC",
                "disabled" if not europepmc_on else "not_injected_in_hermetic_run",
            )
            return
        europepmc_search = _europepmc_search_fn(europepmc_base_url, fast=fast_api)
        result = search_source(
            "Europe PMC",
            europepmc_search,
            args.query,
            args.max_results,
            corpus,
            logger,
            observations=observations,
        )
        if result:
            sources_searched.append(result)

    def run_biorxiv() -> None:
        """Run biorxiv."""
        biorxiv_on = engines.get("biorxiv", True) and not getattr(args, "skip_biorxiv", False)
        if not biorxiv_on or (biorxiv_base_url is None and fast_api):
            _record_skipped(
                observations,
                "bioRxiv",
                "disabled" if not biorxiv_on else "not_injected_in_hermetic_run",
            )
            return
        biorxiv_search = _biorxiv_search_fn(biorxiv_base_url, fast=fast_api)
        result = search_source(
            "bioRxiv",
            biorxiv_search,
            args.query,
            args.max_results,
            corpus,
            logger,
            observations=observations,
        )
        if result:
            sources_searched.append(result)

    def run_medrxiv() -> None:
        """Run medRxiv as a distinct provenance-bearing preprint source."""
        skip_medrxiv = getattr(args, "skip_medrxiv", getattr(args, "skip_biorxiv", False))
        medrxiv_on = engines.get("medrxiv", True) and not skip_medrxiv
        if not medrxiv_on or (biorxiv_base_url is None and fast_api):
            _record_skipped(
                observations,
                "medRxiv",
                "disabled" if not medrxiv_on else "not_injected_in_hermetic_run",
            )
            return
        medrxiv_search = _biorxiv_search_fn(
            biorxiv_base_url,
            fast=fast_api,
            server="medrxiv",
        )
        result = search_source(
            "medRxiv",
            medrxiv_search,
            args.query,
            args.max_results,
            corpus,
            logger,
            observations=observations,
        )
        if result:
            sources_searched.append(result)

    source_runners = {
        "arxiv": run_arxiv,
        "semantic_scholar": run_semantic_scholar,
        "openalex": run_openalex,
        "crossref": run_crossref,
        "pubmed": run_pubmed,
        "sovietrxiv": run_sovietrxiv,
        "chinarxiv": run_chinarxiv,
        "europepmc": run_europepmc,
        "biorxiv": run_biorxiv,
        "medrxiv": run_medrxiv,
    }

    dispatch_ordered(route.source_order, source_runners)

    apply_relevance_filter(corpus, relevance_keywords, logger)

    if args.start_year is not None:
        pre_year = len(corpus)
        corpus = corpus.filter_by_year(start=args.start_year)
        dropped = pre_year - len(corpus)
        if dropped:
            logger.info(
                "Year filter: removed %d papers published before %d (%d → %d)",
                dropped,
                args.start_year,
                pre_year,
                len(corpus),
            )

    deduped = corpus.deduplicate_by_metadata(prefer_preprints=route.prefer_preprints)
    if deduped:
        logger.info(
            "Metadata dedupe: removed %d versioned duplicate papers (%d total remaining)",
            deduped,
            len(corpus),
        )

    corpus.save(corpus_path)
    _write_retrieval_report(
        retrieval_report_path,
        query=str(args.query),
        max_results=int(args.max_results),
        corpus_records=len(corpus),
        run_mode="retrieval",
        observations=observations,
        route={
            "query_type": route.query_type,
            "confidence": route.confidence,
            "prefer_preprints": route.prefer_preprints,
            "source_order": route.source_order,
        },
    )
    total_elapsed = time.monotonic() - pipeline_start
    logger.info("--- Literature Search Summary ---")
    logger.info("Sources: %s", ", ".join(sources_searched) if sources_searched else "None")
    logger.info("Total unique papers: %d", len(corpus))
    logger.info("Corpus saved to: %s", corpus_path)
    logger.info("Total search time: %.1fs", total_elapsed)
    print(str(corpus_path))
    return corpus_path
