"""Derived-documentation generators — thin orchestrators that write docs/_generated/ files.

Each script reads live repository state and writes a deterministic output file.
All business logic is in infrastructure/ modules.
"""

from __future__ import annotations
