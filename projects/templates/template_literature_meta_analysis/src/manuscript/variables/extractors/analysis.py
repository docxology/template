"""Analysis artifact variables."""

from __future__ import annotations

from manuscript.variables._logging import logger
from manuscript.variables.context import ExtractContext
from manuscript.variables.formatters import latex_number


def extract_analysis(ctx: ExtractContext) -> dict[str, str]:
    variables: dict[str, str] = {}
    figures_dir = ctx.output_dir / "figures"
    variables["NUM_FIGURES"] = str(len(list(figures_dir.glob("*.png")))) if figures_dir.exists() else "pending"
    if not figures_dir.exists():
        logger.warning("Figures directory not found at %s; NUM_FIGURES=pending", figures_dir)

    topics_raw = ctx.load_json_raw("topics.json")
    if isinstance(topics_raw, list) and topics_raw:
        variables["NUM_TOPICS"] = str(len(topics_raw))
        topic_rows = ["| Topic | Top terms |", "| --- | --- |"]
        for topic in topics_raw:
            if isinstance(topic, dict):
                words = topic.get("top_words", [])
                topic_rows.append(f"| {topic.get('topic_id', '')} | {', '.join(str(w) for w in words[:8])} |")
        variables["TOPIC_TABLE"] = "\n".join(topic_rows)
    else:
        variables["TOPIC_TABLE"] = "| Topic | Top terms |\n| --- | --- |"

    tfidf = ctx.load_json("tfidf_data.json")
    if tfidf:
        feature_names = tfidf.get("feature_names", [])
        variables["NUM_VOCAB_FEATURES"] = str(len(feature_names))
        variables["NUM_VOCAB_FEATURES_LATEX"] = latex_number(len(feature_names))
        variables["TOP_VOCAB_TERMS"] = ", ".join(str(t) for t in feature_names[:20])
    else:
        variables["NUM_VOCAB_FEATURES"] = "pending"
        variables["NUM_VOCAB_FEATURES_LATEX"] = "pending"
        variables["TOP_VOCAB_TERMS"] = ""

    fulltext = ctx.load_json("fulltext_assessment.json")
    if fulltext:
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

    desc = ctx.load_json("descriptive_stats.json")
    if desc:
        ds = desc.get("descriptive_stats", {})
        if isinstance(ds, dict):
            variables["UNIQUE_AUTHORS"] = str(ds.get("unique_authors", 0))
            variables["CITATION_MEAN"] = f"{ds.get('citation_count_mean', 0):.1f}"
            variables["CITATION_MEDIAN"] = f"{ds.get('citation_count_median', 0):.1f}"
            variables["CITATION_MAX"] = str(ds.get("citation_count_max", 0))
            variables["CITATION_TOTAL"] = latex_number(ds.get("citation_count_total", 0))
            variables["PAPERS_PER_AUTHOR_MEAN"] = f"{ds.get('papers_per_author_mean', 0):.2f}"
            variables["PCT_WITH_DOI"] = f"{ds.get('pct_with_doi', 0):.1f}"
            venues = ds.get("counts_by_venue", {})
            if isinstance(venues, dict) and venues:
                rows = ["| Venue | Papers |", "| --- | --- |"]
                for venue, count in sorted(venues.items(), key=lambda x: -x[1])[:10]:
                    rows.append(f"| {venue[:50]} | {count} |")
                variables["TOP_VENUES_TABLE"] = "\n".join(rows)
            else:
                variables["TOP_VENUES_TABLE"] = "| Venue | Papers |\n| --- | --- |"
        cd = desc.get("citation_distribution", {})
        if isinstance(cd, dict):
            variables["GINI_COEFFICIENT"] = f"{cd.get('gini', 0):.3f}"
            variables["CITATION_DIST_N"] = str(cd.get("n", 0))
            hist = cd.get("histogram", {})
            if isinstance(hist, dict) and hist:
                rows = ["| Citations | Papers |", "| --- | --- |"]
                for label, count in hist.items():
                    rows.append(f"| {label} | {count} |")
                variables["CITATION_DIST_TABLE"] = "\n".join(rows)
            else:
                variables["CITATION_DIST_TABLE"] = "| Citations | Papers |\n| --- | --- |"
        authors = desc.get("author_productivity", [])
        if isinstance(authors, list) and authors:
            rows = ["| Rank | Author | Papers |", "| --- | --- | --- |"]
            for i, entry in enumerate(authors[:10], 1):
                if isinstance(entry, list) and len(entry) >= 2:
                    rows.append(f"| {i} | {entry[0][:40]} | {entry[1]} |")
            variables["TOP_AUTHORS_TABLE"] = "\n".join(rows)
        else:
            variables["TOP_AUTHORS_TABLE"] = "| Rank | Author | Papers |\n| --- | --- | --- |"

    entities = ctx.load_json("entities.json")
    if isinstance(entities, dict) and entities:
        rows = ["| Entity | Frequency |", "| --- | --- |"]
        for name, count in sorted(entities.items(), key=lambda x: -x[1])[:15]:
            rows.append(f"| {name[:40]} | {count} |")
        variables["TOP_ENTITIES_TABLE"] = "\n".join(rows)
        variables["NUM_ENTITIES"] = str(len(entities))
    else:
        variables["TOP_ENTITIES_TABLE"] = "| Entity | Frequency |\n| --- | --- |"
        variables["NUM_ENTITIES"] = "0"

    keyphrases = ctx.load_json("keyphrases.json")
    kp_list = keyphrases.get("top_keyphrases", []) if isinstance(keyphrases, dict) else []
    if kp_list:
        rows = ["| Keyphrase | Score |", "| --- | --- |"]
        for entry in kp_list[:15]:
            if isinstance(entry, dict):
                rows.append(f"| {entry.get('phrase', '')[:40]} | {entry.get('score', 0):.4f} |")
        variables["TOP_KEYPHRASES_TABLE"] = "\n".join(rows)
        variables["NUM_KEYPHRASES"] = str(len(kp_list))
    else:
        variables["TOP_KEYPHRASES_TABLE"] = "| Keyphrase | Score |\n| --- | --- |"
        variables["NUM_KEYPHRASES"] = "0"

    emb = ctx.load_json("embedding_analysis.json")
    if emb:
        variables["NUM_EMBEDDING_CLUSTERS"] = str(emb.get("num_clusters", 0))
        pairs = emb.get("top_similar_pairs", [])
        if isinstance(pairs, list) and pairs:
            rows = ["| Paper A | Paper B | Similarity |", "| --- | --- | --- |"]
            for pair in pairs[:10]:
                if isinstance(pair, dict):
                    rows.append(
                        f"| {pair.get('paper_a', '')[:30]} | {pair.get('paper_b', '')[:30]} | {pair.get('similarity', 0):.4f} |"
                    )
            variables["TOP_SIMILAR_PAIRS_TABLE"] = "\n".join(rows)
        else:
            variables["TOP_SIMILAR_PAIRS_TABLE"] = "| Paper A | Paper B | Similarity |\n| --- | --- | --- |"
    else:
        variables["NUM_EMBEDDING_CLUSTERS"] = "0"
        variables["TOP_SIMILAR_PAIRS_TABLE"] = "| Paper A | Paper B | Similarity |\n| --- | --- | --- |"
    return variables
