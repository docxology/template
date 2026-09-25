"""Project test configuration: put src/ on the path for pytest imports."""

import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
