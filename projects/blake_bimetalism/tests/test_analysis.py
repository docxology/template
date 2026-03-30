"""
Core mathematical tests for Blake Bimetallism.
Enforces a strict Zero-Mock policy against the `MetaStabilityMetrics` matrix,
verifying that 18th-century Bimetallic divergence ratios correctly output
an 'Entropy Gap' mimicking structural fragility.
"""

import pytest
from projects.blake_bimetalism.src.analysis import (
    MetaStabilityMetrics,
    compute_illuminated_inversion,
    bimetallic_discourse_terms
)


def test_metastability_entropy_gap():
    """Test the physical entropic gap computation of Gresham's dynamics."""
    # Market ratio of 15.5 vs mint ratio of 15 (historical drift example)
    metrics = MetaStabilityMetrics(100.0, 1500.0, 15.5, 15.0)
    assert metrics.gresham_entropy_gap == 0.5


def test_prophetic_inversion():
    """Test Blake's theoretical inversion of the dualistic divide."""
    metrics = MetaStabilityMetrics(100.0, 1500.0, 15.5, 15.0)
    # A 50% visionary integration weight halves the entropy gap from 0.5 to 0.25
    inversion = compute_illuminated_inversion(metrics, 0.5)
    assert inversion == 0.25
    
    # 100% prophetic weight completely collapses the gap (absolute nonduality)
    inversion_full = compute_illuminated_inversion(metrics, 1.0)
    assert inversion_full == 0.0


def test_prophetic_inversion_bounds():
    """Test boundaries of the prophetic weighting."""
    metrics = MetaStabilityMetrics(100.0, 1500.0, 15.5, 15.0)
    with pytest.raises(ValueError, match="within"):
        compute_illuminated_inversion(metrics, 1.5)


def test_discourse_terms():
    """Test basic fetching of theoretical anchors."""
    terms = bimetallic_discourse_terms()
    assert "Gresham's Law" in terms
    assert "nonduality" in terms
    assert len(terms) == 7
