"""Literature Meta-Analysis source code.

Every installed subpackage uses this canonical namespace, for example
``from template_literature_meta_analysis.literature.models import Paper``.
Source launchers register the same package explicitly; bare sibling aliases
are not part of the distribution contract.
"""

from __future__ import annotations

__all__ = [
    "analysis",
    "knowledge_graph",
    "literature",
    "manuscript",
    "visualization",
]
