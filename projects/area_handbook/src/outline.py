"""Fixed handbook outline template and builder."""

from __future__ import annotations

from .models import AreaCorpus, HandbookSection

# section_id, title, depth, theme_ids — themes route evidence into chapters
HANDBOOK_TEMPLATE: tuple[HandbookSection, ...] = (
    HandbookSection("04_landscape", "Landscape and setting", 1, ("landscape",)),
    HandbookSection("05_communities", "Communities and civic life", 1, ("communities",)),
    HandbookSection("06_economy", "Economy and livelihoods", 1, ("economy",)),
    HandbookSection("07_infrastructure", "Infrastructure and connectivity", 1, ("infrastructure",)),
    HandbookSection("08_environment", "Environment and stewardship", 1, ("environment",)),
    HandbookSection("09_governance", "Governance and services", 1, ("governance",)),
    HandbookSection("10_risks", "Cross-cutting risks", 2, ("risks",)),
    HandbookSection("11_recommendations", "Recommendations", 2, ("recommendations",)),
)


def build_handbook_outline(_corpus: AreaCorpus) -> tuple[HandbookSection, ...]:
    """Return the canonical handbook section list (corpus reserved for future tailoring)."""
    return HANDBOOK_TEMPLATE
