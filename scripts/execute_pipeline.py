#!/usr/bin/env python3
"""Compatibility wrapper for :mod:`scripts.runner.execute_pipeline`."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.runner.execute_pipeline import (  # noqa: E402
    PipelineArgs,
    execute_pipeline,
    execute_single_stage,
    handle_hitl_command,
    main,
)

__all__ = ["PipelineArgs", "handle_hitl_command", "execute_pipeline", "execute_single_stage", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
