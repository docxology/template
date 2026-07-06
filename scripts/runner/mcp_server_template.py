#!/usr/bin/env python3
"""Thin launcher for the template's stdio MCP server.

Exposes the package's agent surface (operation catalog, pipeline contract,
skills, and a scoped invoke_cli) over the Model Context Protocol on stdio.

Usage::

    uv run python scripts/mcp_server_template.py

Equivalent to ``uv run python -m infrastructure.mcp_server``. This is an opt-in
agent-facing surface and is intentionally NOT part of the default pipeline/CI.
See docs/architecture/capability-surfaces.md.
"""

from __future__ import annotations

from infrastructure.mcp_server import main

if __name__ == "__main__":
    raise SystemExit(main())
