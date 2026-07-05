"""Temporal analysis variables."""

from __future__ import annotations

from manuscript.variables._logging import logger
from manuscript.variables.context import ExtractContext


def extract_temporal(ctx: ExtractContext) -> dict[str, str]:
    variables: dict[str, str] = {}
    temporal = ctx.load_json("temporal_analysis.json")
    if not temporal:
        logger.warning("temporal_analysis.json not found; temporal variables empty")
        return variables
    variables["YEAR_START"] = str(temporal.get("first_year", ""))
    variables["YEAR_END"] = str(temporal.get("last_year", ""))
    variables["YEAR_START_PUBS"] = str(temporal.get("year_counts", {}).get(str(temporal.get("first_year", "")), ""))
    variables["PEAK_YEAR"] = str(temporal.get("peak_year", ""))
    peak_year_val = str(temporal.get("year_counts", {}).get(str(temporal.get("peak_year", "")), ""))
    variables["PEAK_YEAR_COUNT"] = peak_year_val
    variables["PEAK_YEAR_PUBS"] = peak_year_val
    variables["CAGR_PCT"] = f"{temporal.get('cagr', 0) * 100:.2f}"
    variables["MEAN_YOY_GROWTH_PCT"] = f"{temporal.get('mean_growth_rate', 0) * 100:.1f}"
    doubling = temporal.get("doubling_time", 0)
    variables["DOUBLING_TIME"] = f"{doubling:.1f}" if doubling else ""
    year_counts = temporal.get("year_counts", {})
    variables["TEMPORAL_TOTAL_PAPERS"] = str(temporal.get("total_papers", ctx.corpus_size))
    variables["YEAR_SPAN"] = str(int(temporal.get("last_year", 0)) - int(temporal.get("first_year", 0)))
    if year_counts:
        sorted_years = sorted(year_counts.items(), key=lambda x: -x[1])[:10]
        rows = ["| Year | Publications |", "| --- | --- |"]
        for year, count in sorted(sorted_years, key=lambda x: x[0]):
            rows.append(f"| {year} | {count} |")
        variables["YEAR_COUNT_TABLE"] = "\n".join(rows)
    else:
        variables["YEAR_COUNT_TABLE"] = "| Year | Publications |\n| --- | --- |"
    return variables
