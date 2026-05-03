"""Shell-replacement orchestration package.

This package contains all orchestration logic that previously lived in
``run.sh`` and ``secure_run.sh``. The shell wrappers are now thin
dispatchers that bootstrap ``uv``/``.venv`` and invoke
``python -m infrastructure.orchestration``.

Public API
----------

- :func:`main` — CLI entry point used by ``python -m infrastructure.orchestration``
- :class:`PipelineRunner` — wraps the existing :class:`PipelineExecutor`
- :func:`select_project_interactive` — interactive project picker
- :func:`validate_project_slug` — slug safety check (rejects path traversal)
- :func:`render_menu` — deterministic interactive menu rendering
- :func:`setup_stage_log` — per-stage log file setup
- :func:`run_secure_pipeline` — steganography post-processing wrapper

Design
------

The package follows the repository's two-layer architecture:

- It coordinates the existing :mod:`infrastructure.core.pipeline`,
  :mod:`infrastructure.project`, and :mod:`infrastructure.steganography`
  modules. It does **not** re-implement any pipeline logic.
- All functions are unit-testable in isolation; no shell state assumed.
"""

from __future__ import annotations

from infrastructure.orchestration.cli import build_parser, main
from infrastructure.orchestration.discovery import (
    select_project_interactive,
    validate_project_slug,
)
from infrastructure.orchestration.menu import MENU_OPTIONS, render_menu
from infrastructure.orchestration.pipeline_runner import PipelineRunner
from infrastructure.orchestration.secure_run import run_secure_pipeline
from infrastructure.orchestration.stage_logger import setup_stage_log

__all__ = [
    "MENU_OPTIONS",
    "PipelineRunner",
    "build_parser",
    "main",
    "render_menu",
    "run_secure_pipeline",
    "select_project_interactive",
    "setup_stage_log",
    "validate_project_slug",
]
