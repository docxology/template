"""
Thin orchestrator for Blake & Bimetallism project programmatic figure generation.
Acts as the CLI entrypoint invoking the 7 topological rendering methods from `src/viz/`
(e.g., Timeline, Fourfold Mapping, 3D Gresham Topological Fracture, Contemporary GSR).
Adheres strictly to the Thin Orchestrator Pattern.
"""
from pathlib import Path
from infrastructure.core.logging_utils import get_logger
from projects.blake_bimetalism.src.figures import (
    render_timeline,
    render_fourfold_mapping,
    render_alchemical_bimetallism,
    render_topological_fracture,
    render_historic_ratio,
    render_historic_reserves,
    render_gsr_contemporary
)

logger = get_logger("blake_bimetalism.figures")


def main():
    """
    Main orchestration step. Calculates timelines and theoretical mappings.
    """
    logger.info("Starting Blake Bimetallism figure generation pipeline...")

    script_dir = Path(__file__).parent.resolve()
    project_dir = script_dir.parent
    figures_dir = project_dir / "output" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    output_png_1 = figures_dir / "timeline.png"
    output_png_2 = figures_dir / "fourfold_mapping.png"
    output_png_3 = figures_dir / "alchemical_bimetallism.png"
    output_png_4 = figures_dir / "topological_fracture.png"
    output_png_5 = figures_dir / "historic_ratio.png"
    output_png_6 = figures_dir / "historic_reserves.png"
    output_png_7 = figures_dir / "gsr_contemporary.png"

    render_timeline(output_png_1)
    logger.info(f"Timeline generated at {output_png_1}")

    render_fourfold_mapping(output_png_2)
    logger.info(f"Fourfold theoretical mapping generated at {output_png_2}")

    render_alchemical_bimetallism(output_png_3)
    logger.info(f"Esoteric Bimetallism mapping generated at {output_png_3}")

    render_topological_fracture(output_png_4)
    logger.info(f"Topological Fracture 3D visual generated at {output_png_4}")

    render_historic_ratio(output_png_5)
    logger.info(f"Historic divergence ratio graph generated at {output_png_5}")

    render_historic_reserves(output_png_6)
    logger.info(f"Historic Bank restriction reserves graph generated at {output_png_6}")

    render_gsr_contemporary(output_png_7)
    logger.info(f"Contemporary GSR 2010-2026 figure generated at {output_png_7}")

    logger.info("All figure generations completed successfully.")


if __name__ == "__main__":
    main()
