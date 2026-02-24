#!/usr/bin/env python3
"""Build a domain-appropriate entomological corpus for Ento-Linguistic analysis.

This script uses the PubMed eFetch API to download real abstracts focused on
entomological research — particularly social insects, ant behavior, caste systems,
and colony dynamics — and saves them as the canonical corpus for the project.

Usage:
    python build_ento_corpus.py [--max-results 200] [--output data/corpus/abstracts.json]
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from collections import Counter
from pathlib import Path

# Ensure project src is importable
PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))
sys.path.insert(0, str(PROJECT_DIR))

from data.literature_mining import PubMedMiner, create_entomology_query

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("build_ento_corpus")

# Domain-specific PubMed queries for targeted retrieval
# Using simple keyword queries (MeSH tags with brackets get double-encoded by urlencode)
ENTOMOLOGY_QUERIES = [
    # Core social insect terminology queries
    "Formicidae caste queen worker",
    "ant colony behavior social insect",
    "eusocial insect ant bee wasp",
    "division labor ant social insect Hymenoptera",
    "superorganism colony ant social insect",
    # Kin & Relatedness
    "kin selection social insect ant Hymenoptera",
    "inclusive fitness ant social insect",
    "haplodiploidy social sex determination",
    # Behavior & Identity
    "foraging behavior ant Formicidae",
    "task allocation ant social insect colony",
    # Power & Labor
    "reproductive conflict ant social insect",
    "social parasitism ant Hymenoptera",
]


def fetch_abstracts_for_query(
    miner: PubMedMiner, query: str, max_per_query: int = 50
) -> list[str]:
    """Fetch abstracts for a single PubMed query.

    Args:
        miner: PubMed miner instance
        query: PubMed query string
        max_per_query: Maximum results per query

    Returns:
        List of abstract text strings
    """
    logger.info(f"Query: {query}")
    pmids = miner.search(query, max_results=max_per_query)
    logger.info(f"  Found {len(pmids)} PMIDs")

    if not pmids:
        return []

    publications = miner.fetch_publications(pmids)
    abstracts = [
        pub.abstract
        for pub in publications
        if pub.abstract and len(pub.abstract) > 50  # Skip trivially short abstracts
    ]
    logger.info(f"  Retrieved {len(abstracts)} abstracts with text")
    return abstracts


def validate_corpus(abstracts: list[str]) -> dict:
    """Validate and report corpus quality metrics.

    Args:
        abstracts: List of abstract texts

    Returns:
        Dictionary with corpus statistics
    """
    # Domain seed terms to check for coverage
    domain_seeds = {
        "unit_of_individuality": ["colony", "superorganism", "individual", "nestmate", "organism"],
        "behavior_and_identity": ["foraging", "worker", "behavior", "task", "role", "caste"],
        "power_and_labor": ["caste", "queen", "worker", "hierarchy", "dominant", "subordinate"],
        "sex_and_reproduction": ["haplodiploidy", "reproduction", "mating", "sex", "queen"],
        "kin_and_relatedness": ["kin", "relatedness", "altruism", "inclusive fitness", "cooperation"],
        "economics": ["resource", "allocation", "cost", "benefit", "foraging efficiency"],
    }

    all_text = " ".join(abstracts).lower()
    words = all_text.split()

    domain_coverage = {}
    for domain, seeds in domain_seeds.items():
        found = [term for term in seeds if term in all_text]
        domain_coverage[domain] = {
            "terms_found": found,
            "coverage": len(found) / len(seeds) if seeds else 0,
        }

    word_counts = Counter(words)
    stats = {
        "total_abstracts": len(abstracts),
        "total_tokens": len(words),
        "unique_tokens": len(word_counts),
        "avg_abstract_length_tokens": len(words) / len(abstracts) if abstracts else 0,
        "domain_coverage": domain_coverage,
        "top_tokens": word_counts.most_common(30),
    }

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Build entomological corpus from PubMed abstracts"
    )
    parser.add_argument(
        "--max-per-query",
        type=int,
        default=50,
        help="Maximum results per query (default: 50)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (default: data/corpus/abstracts.json)",
    )
    parser.add_argument(
        "--stats-output",
        type=str,
        default=None,
        help="Stats output file path (default: output/data/corpus_statistics.json)",
    )
    args = parser.parse_args()

    # Resolve output paths
    output_path = Path(args.output) if args.output else PROJECT_DIR / "data" / "corpus" / "abstracts.json"
    stats_path = Path(args.stats_output) if args.stats_output else PROJECT_DIR / "output" / "data" / "corpus_statistics.json"

    logger.info("=" * 60)
    logger.info("Ento-Linguistics Corpus Builder")
    logger.info("=" * 60)
    logger.info(f"Max per query: {args.max_per_query}")
    logger.info(f"Queries: {len(ENTOMOLOGY_QUERIES)}")
    logger.info(f"Output: {output_path}")

    miner = PubMedMiner()
    all_abstracts = []
    seen = set()  # Deduplicate

    for i, query in enumerate(ENTOMOLOGY_QUERIES, 1):
        logger.info(f"\n--- Query {i}/{len(ENTOMOLOGY_QUERIES)} ---")
        abstracts = fetch_abstracts_for_query(miner, query, args.max_per_query)

        for abstract in abstracts:
            # Deduplicate by first 100 chars
            key = abstract[:100].lower()
            if key not in seen:
                seen.add(key)
                all_abstracts.append(abstract)

        # Rate limit between queries
        if i < len(ENTOMOLOGY_QUERIES):
            time.sleep(1.0)

    logger.info(f"\n{'=' * 60}")
    logger.info(f"Total unique abstracts collected: {len(all_abstracts)}")

    if len(all_abstracts) < 20:
        logger.warning(
            "Very few abstracts collected. The PubMed API may be rate-limiting. "
            "Try again in a few minutes or reduce --max-per-query."
        )

    # Validate corpus quality
    stats = validate_corpus(all_abstracts)
    logger.info(f"Total tokens: {stats['total_tokens']}")
    logger.info(f"Unique tokens: {stats['unique_tokens']}")
    logger.info(f"Avg abstract length: {stats['avg_abstract_length_tokens']:.0f} tokens")

    logger.info("\nDomain coverage:")
    for domain, info in stats["domain_coverage"].items():
        coverage_pct = info["coverage"] * 100
        found = ", ".join(info["terms_found"][:5])
        logger.info(f"  {domain}: {coverage_pct:.0f}% ({found})")

    # Save corpus
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_abstracts, f, indent=2, ensure_ascii=False)
    logger.info(f"\nCorpus saved to: {output_path}")

    # Save statistics
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    # Convert Counter most_common tuples to serializable format
    stats["top_tokens"] = [{"token": t, "count": c} for t, c in stats["top_tokens"]]
    for domain_info in stats["domain_coverage"].values():
        domain_info["coverage"] = round(domain_info["coverage"], 3)

    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    logger.info(f"Statistics saved to: {stats_path}")

    logger.info(f"\n{'=' * 60}")
    logger.info("Corpus build complete!")
    logger.info("=" * 60)

    return 0 if len(all_abstracts) >= 20 else 1


if __name__ == "__main__":
    sys.exit(main())
