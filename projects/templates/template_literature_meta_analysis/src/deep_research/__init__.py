"""Deep-research fixture-replay adapter for the literature meta-analysis exemplar.

This subpackage demonstrates how a project wires
``infrastructure.search.deep_research`` (a PAID, non-deterministic capability)
through a deterministic, offline recorded-report replay path — so the public
template exercises the real import surface without network access or API keys.
"""

from __future__ import annotations

__all__ = ["deep_research_adapter"]
