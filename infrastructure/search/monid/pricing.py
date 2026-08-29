"""Reference pricing for common web-search APIs (USD per 1,000 searches).

Monid itself is a gateway: each endpoint carries its own price (``PER_CALL`` or
``PER_RESULT``). Use :meth:`MonidClient.discover` / :meth:`MonidClient.inspect`
for live Monid endpoint quotes. This module holds **direct-provider** list
prices for comparison.

All figures are vendor list prices; verify against live pricing pages before
budgeting. Last reviewed: 2026-08-28.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SearchApiPrice:
    """One row in the search-API pricing comparison table."""

    provider: str
    product: str
    usd_per_1k_searches: float | None
    notes: str
    source_url: str

    @property
    def usd_per_search(self) -> float | None:
        """Per-search cost derived from the per-1k figure."""
        if self.usd_per_1k_searches is None:
            return None
        return self.usd_per_1k_searches / 1000.0


# Direct search APIs — normalized to USD per 1,000 search requests.
SEARCH_API_PRICES: tuple[SearchApiPrice, ...] = (
    SearchApiPrice(
        provider="Serper",
        product="Google SERP API (Ultimate tier)",
        usd_per_1k_searches=0.30,
        notes="Volume tier ~12.5M queries/mo; lower tiers $0.75–$1.00/1k.",
        source_url="https://serper.dev/pricing",
    ),
    SearchApiPrice(
        provider="Serper",
        product="Google SERP API (Starter tier)",
        usd_per_1k_searches=1.00,
        notes="50k queries/mo at $50/mo.",
        source_url="https://serper.dev/pricing",
    ),
    SearchApiPrice(
        provider="Brave",
        product="Search API (web / LLM context)",
        usd_per_1k_searches=5.00,
        notes="Independent index; $5/mo free credits on paid plans.",
        source_url="https://brave.com/search/api/",
    ),
    SearchApiPrice(
        provider="Exa",
        product="POST /search (up to 10 results)",
        usd_per_1k_searches=7.00,
        notes="Each result above 10 adds $1/1k; contents/summary extra.",
        source_url="https://exa.ai/pricing?tab=api",
    ),
    SearchApiPrice(
        provider="Tavily",
        product="Research search (pay-as-you-go credits)",
        usd_per_1k_searches=8.00,
        notes="1 credit ≈ 1 basic search; subscription tiers reduce effective rate.",
        source_url="https://tavily.com/#pricing",
    ),
    SearchApiPrice(
        provider="Exa",
        product="POST /answer",
        usd_per_1k_searches=5.00,
        notes="Grounded answer with citations, not raw SERP.",
        source_url="https://exa.ai/pricing?tab=api",
    ),
    SearchApiPrice(
        provider="SerpAPI",
        product="Google search (Developer plan)",
        usd_per_1k_searches=10.00,
        notes="$75/mo for 5k searches; higher tiers reduce per-query cost.",
        source_url="https://serpapi.com/pricing",
    ),
    SearchApiPrice(
        provider="Exa",
        product="POST /monitors",
        usd_per_1k_searches=15.00,
        notes="Scheduled tracking, not ad-hoc search.",
        source_url="https://exa.ai/pricing?tab=api",
    ),
    SearchApiPrice(
        provider="Monid",
        product="Gateway (varies by endpoint)",
        usd_per_1k_searches=None,
        notes=(
            "Per-endpoint PER_CALL or PER_RESULT pricing from discover/inspect/run. "
            "Example homepage call: ~$0.0013/call (~$1.30/1k) for one tool; Exa-backed "
            "routes inherit upstream cost plus gateway markup — inspect before running."
        ),
        source_url="https://monid.ai/docs/guide/pricing",
    ),
)


def sorted_by_cost() -> list[SearchApiPrice]:
    """Return rows with a numeric per-1k price, cheapest first."""
    priced = [row for row in SEARCH_API_PRICES if row.usd_per_1k_searches is not None]
    return sorted(priced, key=lambda row: row.usd_per_1k_searches or 0.0)


def format_pricing_table() -> str:
    """Render a Markdown table of direct search API list prices."""
    lines = [
        "| Provider | Product | USD / 1k searches | Notes |",
        "| --- | --- | ---: | --- |",
    ]
    for row in sorted_by_cost():
        cost = f"${row.usd_per_1k_searches:.2f}" if row.usd_per_1k_searches is not None else "—"
        lines.append(f"| {row.provider} | {row.product} | {cost} | {row.notes} |")
    gateway = next(row for row in SEARCH_API_PRICES if row.provider == "Monid")
    lines.append(f"| {gateway.provider} | {gateway.product} | — | {gateway.notes} |")
    return "\n".join(lines)


__all__ = ["SEARCH_API_PRICES", "SearchApiPrice", "format_pricing_table", "sorted_by_cost"]
