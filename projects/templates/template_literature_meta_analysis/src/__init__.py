"""Literature Meta-Analysis source code.

Top-level subpackages are imported directly (the project's conftest/scripts put
``src/`` on ``sys.path``), e.g. ``from literature.models import Paper``.
"""

from __future__ import annotations

__all__ = [
    "analysis",
    "knowledge_graph",
    "literature",
    "manuscript",
    "visualization",
]
