#!/usr/bin/env python3
"""Architecture visualization generator — Thin Orchestrator."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")


PROJECT_DIR = Path(os.environ.get("PROJECT_DIR", Path(__file__).resolve().parent.parent))
_BOOTSTRAP_SPEC = importlib.util.spec_from_file_location(
    "template_script_bootstrap", Path(__file__).resolve().parent / "_bootstrap.py"
)
if _BOOTSTRAP_SPEC is None or _BOOTSTRAP_SPEC.loader is None:
    raise ImportError("actual own project bootstrap is unavailable")
_bootstrap = importlib.util.module_from_spec(_BOOTSTRAP_SPEC)
_BOOTSTRAP_SPEC.loader.exec_module(_bootstrap)
_bootstrap.bootstrap_project(PROJECT_DIR)

from template_template.core.paths import data_repo_root, verify_reference_inputs  # noqa: E402 - selected SDK and own namespace precede imports

# Complete public SOURCE DATA is a separate input, never an SDK import path.
_explicit_repo_root = os.environ.get("TEMPLATE_REPO_ROOT", "").strip()
REPO_ROOT = data_repo_root(
    PROJECT_DIR, explicit_root=Path(_explicit_repo_root).absolute() if _explicit_repo_root else None
)

from infrastructure.core.logging.utils import get_logger  # noqa: E402
from template_template import generate_all_architecture_figures  # noqa: E402

logger = get_logger(__name__)


def main() -> None:
    """Generate all architecture figures via src/template_template module logic."""
    logger.info("Starting architecture visualization generation...")
    paths = generate_all_architecture_figures(REPO_ROOT, PROJECT_DIR)
    verify_reference_inputs()
    logger.info("Architecture visualization generation complete")
    for path in paths:
        logger.info("  • %s", path)


if __name__ == "__main__":
    main()
