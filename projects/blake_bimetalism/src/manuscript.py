"""
Manuscript builder components for Blake & Bimetallism project.
Provides utilities for handling markdown serialization and assertions across the 
18-chapter structure, injecting mathematical parameters directly into LaTeX templates.
"""

from typing import Any

from projects.blake_bimetalism.src.analysis import MetaStabilityMetrics, compute_illuminated_inversion

class ManuscriptBuilder:
    """Class to compile dynamic values for manuscript template injection."""
    
    def __init__(self, metrics: MetaStabilityMetrics):
        self.metrics = metrics
        
    def generate_injection_data(self) -> dict[str, Any]:
        """Provides a dictionary of exact figures used dynamically in the manuscript."""
        return {
            "entropy_gap_value": round(self.metrics.gresham_entropy_gap, 2),
            "visionary_dampening_0_5": round(compute_illuminated_inversion(self.metrics, 0.5), 2),
            "visionary_dampening_1_0": round(compute_illuminated_inversion(self.metrics, 1.0), 2)
        }
