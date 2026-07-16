from literature.query_router import QueryRouter


def test_academic_query_prefers_crossref_first() -> None:
    router = QueryRouter()
    route = router.route(
        "peer-reviewed systematic review of active inference",
        ["arxiv", "semantic_scholar", "openalex", "crossref", "pubmed"],
    )

    assert route.query_type == "academic"
    assert route.source_order[0] == "crossref"
    assert route.prefer_preprints is False


def test_preprint_query_prefers_arxiv_first() -> None:
    router = QueryRouter()
    route = router.route(
        "arXiv preprint on active inference",
        ["arxiv", "semantic_scholar", "openalex", "crossref", "pubmed"],
    )

    assert route.query_type == "academic"
    assert route.source_order[0] == "arxiv"
    assert route.prefer_preprints is True


def test_industry_query_prefers_crossref_and_openalex() -> None:
    router = QueryRouter()
    route = router.route(
        "industry report on neurotechnology market",
        ["arxiv", "semantic_scholar", "openalex", "crossref", "pubmed"],
    )

    assert route.query_type == "industry"
    assert route.source_order[:2] == ("crossref", "openalex")


def test_all_ten_sources_are_ordered_without_silent_exclusion() -> None:
    router = QueryRouter()
    sources = [
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
    ]

    route = router.route("medRxiv preprint", sources)

    assert set(route.source_order) == set(sources)
    assert route.source_order.index("medrxiv") < route.source_order.index("sovietrxiv")
