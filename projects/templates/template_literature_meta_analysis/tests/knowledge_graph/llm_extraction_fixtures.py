"""Shared fixtures for LLM extraction tests (not collected by pytest)."""

from __future__ import annotations

from literature.models import Paper


def make_paper(**overrides) -> Paper:
    """Create a minimal Paper for testing."""
    defaults = dict(
        title="Active Inference and Free Energy",
        abstract="This paper explores the free energy principle as a universal account of self-organization.",
        authors=[],
        year=2023,
        doi="10.1234/test",
        arxiv_id=None,
        s2_id=None,
        openalex_id=None,
        citation_count=42,
        references=[],
    )
    defaults.update(overrides)
    return Paper(**defaults)


def valid_llm_response() -> list[dict]:
    """Generate a valid LLM response JSON array."""
    return [
        {
            "hypothesis_id": "PRIMARY_EFFICACY",
            "direction": "supports",
            "confidence": 0.85,
            "reasoning": "The paper provides formal proofs extending FEP to non-equilibrium systems.",
        },
        {
            "hypothesis_id": "OPTIMAL_PERFORMANCE",
            "direction": "irrelevant",
            "confidence": 0.0,
            "reasoning": "The paper does not address planning or decision-making.",
        },
        {
            "hypothesis_id": "PROCESS_MODEL",
            "direction": "contradicts",
            "confidence": 0.6,
            "reasoning": "The paper challenges standard predictive coding assumptions.",
        },
        {
            "hypothesis_id": "MECHANISTIC_BASIS",
            "direction": "neutral",
            "confidence": 0.5,
            "reasoning": "The paper mentions Markov blankets but does not take a stance.",
        },
        {
            "hypothesis_id": "SCALABILITY",
            "direction": "irrelevant",
            "confidence": 0.0,
            "reasoning": "Not relevant.",
        },
        {
            "hypothesis_id": "CLINICAL_UTILITY",
            "direction": "irrelevant",
            "confidence": 0.0,
            "reasoning": "Not relevant.",
        },
        {
            "hypothesis_id": "BIOLOGICAL_BASIS",
            "direction": "irrelevant",
            "confidence": 0.0,
            "reasoning": "Not relevant.",
        },
        {
            "hypothesis_id": "DOMAIN_GENERALIZATION",
            "direction": "irrelevant",
            "confidence": 0.0,
            "reasoning": "Not relevant.",
        },
    ]


def httpserver_base_url(httpserver) -> str:
    """Strip trailing slash from pytest-httpserver base URL."""
    return httpserver.url_for("")[:-1]
