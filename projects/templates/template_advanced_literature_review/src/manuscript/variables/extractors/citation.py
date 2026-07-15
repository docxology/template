"""Citation network variables."""

from __future__ import annotations

from manuscript.variables._logging import logger
from manuscript.variables.context import ExtractContext
from manuscript.variables.formatters import latex_number
from manuscript.variables.io import count_total_references


def _empty_advanced() -> dict[str, str]:
    return {
        "DEGREE_ASSORTATIVITY": "0.0000",
        "AVG_CLUSTERING": "0.0000",
        "TOP_BETWEENNESS_TABLE": "| Rank | DOI | Betweenness |\n| --- | --- | --- |",
    }


def extract_citation(ctx: ExtractContext) -> dict[str, str]:
    """Process extract citation."""
    citation = ctx.load_json("citation_network.json")
    if not citation:
        logger.warning("citation_network.json not found; citation variables empty")
        return _empty_advanced()

    variables: dict[str, str] = {}
    edges = citation.get("num_edges", 0)
    nodes = citation.get("num_nodes", ctx.corpus_size)
    variables["CITATION_EDGES"] = latex_number(edges)
    variables["CITATION_EDGES_RAW"] = str(edges)
    variables["CITATION_NODES"] = str(nodes)
    variables["CITATION_COMPONENTS"] = str(citation.get("connected_components", 0))
    density = citation.get("density", 0)
    density_pct = density * 100 if density < 1 else density
    variables["CITATION_DENSITY_PCT"] = f"{density_pct:.2f}"
    variables["MEAN_IN_DEGREE"] = f"{citation.get('avg_in_degree', 0):.1f}"
    total_refs = citation.get("total_references", 0)
    if total_refs > 0:
        variables["CITATION_TOTAL_REFS"] = latex_number(total_refs)
        variables["CITATION_TOTAL_REFS_RAW"] = str(total_refs)
        variables["CITATION_RESOLUTION_PCT"] = f"{(edges / total_refs) * 100:.1f}"
    else:
        ref_count = count_total_references(ctx.data_dir / "corpus.jsonl")
        if ref_count == 0:
            ref_count = count_total_references(ctx.output_dir / "corpus.jsonl")
        if ref_count > 0:
            variables["CITATION_TOTAL_REFS"] = latex_number(ref_count)
            variables["CITATION_TOTAL_REFS_RAW"] = str(ref_count)
            variables["CITATION_RESOLUTION_PCT"] = f"{(edges / ref_count) * 100:.1f}"
        else:
            variables["CITATION_TOTAL_REFS"] = "0"
            variables["CITATION_TOTAL_REFS_RAW"] = "0"
            variables["CITATION_RESOLUTION_PCT"] = "0.0"
    variables["CITATION_COMMUNITIES"] = str(citation.get("num_communities", ""))
    variables["CITATION_MAX_IN_DEGREE"] = str(citation.get("max_in_degree", 0))
    variables["CITATION_MAX_OUT_DEGREE"] = str(citation.get("max_out_degree", 0))
    avg_out = citation.get("avg_out_degree", citation.get("avg_in_degree", 0))
    variables["CITATION_AVG_OUT_DEGREE"] = f"{avg_out:.1f}"
    for key, table_key, header in (
        ("top_pagerank", "TOP_PAGERANK_TABLE", "| Rank | DOI | PageRank |"),
        ("top_authorities", "TOP_AUTHORITIES_TABLE", "| Rank | DOI | Authority |"),
        ("top_hubs", "TOP_HUBS_TABLE", "| Rank | DOI | Hub |"),
    ):
        top = citation.get(key, {})
        if isinstance(top, dict) and top:
            items = sorted(top.items(), key=lambda x: -x[1])[:5]
            rows = [header, "| --- | --- | --- |"]
            for i, (doi, score) in enumerate(items, 1):
                rows.append(f"| {i} | {doi.replace('doi:', '')} | {score:.6f} |")
            variables[table_key] = "\n".join(rows)
            if key == "top_pagerank":
                variables["TOP_PAGERANK_DOI"] = items[0][0].replace("doi:", "")
        else:
            variables[table_key] = f"{header}\n| --- | --- | --- |"
            if key == "top_pagerank":
                variables["TOP_PAGERANK_DOI"] = ""
    variables.update(_empty_advanced())
    variables["DEGREE_ASSORTATIVITY"] = f"{citation.get('degree_assortativity', 0):.4f}"
    variables["AVG_CLUSTERING"] = f"{citation.get('avg_clustering', 0):.4f}"
    top_betw = citation.get("top_betweenness", {})
    if isinstance(top_betw, dict) and top_betw:
        betw_items = sorted(top_betw.items(), key=lambda x: -x[1])[:5]
        betw_rows = ["| Rank | DOI | Betweenness |", "| --- | --- | --- |"]
        for i, (doi, score) in enumerate(betw_items, 1):
            betw_rows.append(f"| {i} | {doi.replace('doi:', '')[:40]} | {score:.6f} |")
        variables["TOP_BETWEENNESS_TABLE"] = "\n".join(betw_rows)
    return variables
