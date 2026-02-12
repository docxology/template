"""Blake Active Inference source package."""

from pathlib import Path

__version__ = "1.0.0"
__author__ = "Daniel Ari Friedman"

# Package root directory
PACKAGE_ROOT = Path(__file__).parent
PROJECT_ROOT = PACKAGE_ROOT.parent
OUTPUT_DIR = PROJECT_ROOT / "output"


def get_output_dir() -> Path:
    """Get the output directory, creating if necessary."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def get_figures_dir() -> Path:
    """Get the figures output directory, creating if necessary."""
    figures_dir = OUTPUT_DIR / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    return figures_dir
