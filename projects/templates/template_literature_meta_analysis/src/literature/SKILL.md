---
name: Systematic Literature Retrieval
description: Operations for federated API querying across ten literature engines (arXiv, Semantic Scholar, OpenAlex, Crossref, PubMed, SovietRxiv, ChinaRxiv, Europe PMC, bioRxiv, medRxiv).
---

# Instructions

You are interacting with the `src/literature/` module. This coordinates multi-source API harvesting across ten independently toggled engines, canonical-identifier deduplication, full-text resolution/extraction, unified bibliography export, and keyword-based subfield classification logic.

## Agentic Interface (MCP Strategy)

1. **Federated Politeness**: Ensure rigorous rate-limiting across provider networks. If writing tests for this package, absolutely enforce the "Zero-Mock" policy by orchestrating local `pytest-httpserver` fixtures rather than blinding the agent via `mocker.patch`.
2. **Canonical Deduplication**: The ecosystem is messy; always prioritize cross-referencing DOIs, arXiv IDs, and fuzzy-hashed title matches.
3. **Taxonomy Enforcement**: Categorization logic into the A (Theory), B (Tools), C (Application) tiers relies heavily on specific mathematical token matching. Update the keyword heuristics with precision.
