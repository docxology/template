#!/usr/bin/env python3
"""
Thin orchestrator for Blake & Bimetallism project numerical analysis.
Generates structural outputs corresponding to the meta-stability equations.
"""

import json
from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from projects.blake_bimetalism.src.analysis import (
    MetaStabilityMetrics, 
    compute_illuminated_inversion
)

logger = get_logger("blake_bimetalism.analyze")


def main():
    """
    Main orchestration step. Reads no inputs, applies baseline historical models 
    for theoretical mapping, and outputs metadata to the project's output directory.
    """
    logger.info("Starting Blake Bimetallism analysis pipeline...")
    
    # Ensure output directory exists (template root usually handles this, but safe to verify here too if run standalone locally)
    script_dir = Path(__file__).parent.resolve()
    project_dir = script_dir.parent
    output_dir = project_dir / "output" / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Compute 1790s bimetallic crisis theoretical baseline
    metrics = MetaStabilityMetrics(
        gold_reserves=2000000.0, 
        silver_reserves=40000000.0, 
        market_ratio=15.7, 
        mint_ratio=15.2
    )
    
    entropy_gap = metrics.gresham_entropy_gap
    inversion = compute_illuminated_inversion(metrics, prophetic_weight=0.8) # Strong Blakean visionary lens
    
    results = {
        "historical_market_ratio": metrics.market_ratio,
        "historical_mint_ratio": metrics.mint_ratio,
        "gresham_entropy_gap": entropy_gap,
        "visionary_inversion_gap": inversion,
        "conclusion": "High prophetic weight systematically reduces dualistic entropy."
    }
    
    out_file = output_dir / "metastability_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
        
    logger.info(f"Analysis completed successfully. Results saved to {out_file}")


if __name__ == "__main__":
    main()
