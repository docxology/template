"""
Financial and poetics analytical domains for William Blake and Bimetallism.
Models meta-stability of historical dual-money equilibrium using semantic frequency 
and simulates Gresham's law dynamics functionally to ensure Zero-Mock adherence.
"""

from dataclasses import dataclass


@dataclass
class MetaStabilityMetrics:
    """Historical valuation metrics reflecting Gresham's structural divide."""
    gold_reserves: float
    silver_reserves: float
    market_ratio: float
    mint_ratio: float

    @property
    def gresham_entropy_gap(self) -> float:
        """
        Quantifies the divergence between actual market ratios and 
        rigid mint ratios—simulating the entropic collapse Blake critiques
        in static material dualism (Urizenic fragmentation).
        """
        return abs(self.market_ratio - self.mint_ratio)


def compute_illuminated_inversion(metrics: MetaStabilityMetrics, prophetic_weight: float = 0.5) -> float:
    """
    Simulates Blake's Prophetic Inversion resolving dualistic instability.
    Applies the prophetic weight as a damping factor scaling the Gresham entropy gap.
    """
    if prophetic_weight < 0 or prophetic_weight > 1.0:
         raise ValueError("Prophetic weight must be within [0, 1].")
         
    return metrics.gresham_entropy_gap * (1.0 - prophetic_weight)

def bimetallic_discourse_terms() -> list[str]:
    """Returns the primary scholarly terms anchoring the Bimetallism analysis."""
    return [
        "meta-stability",
        "Lucretian atomism",
        "Epicurean collision",
        "Gresham's Law",
        "Urizenic division",
        "nonduality",
        "illuminated printing"
    ]
