"""Version-controlled experiment tree for a living research record.

Every experiment is a node in a durable tree. Nodes are either
``provisional`` (planned), ``frozen`` (preregistered, immutable), or
``answered`` (terminal, carrying an outcome). The tree is the single
source of truth for the manuscript: answered nodes form the results
table, frozen nodes the in-progress register, and dead ends the
discussion of negative results.
"""

from template_experiment_tree.manuscript_variables import (
    ManuscriptVariablesError,
    generate_variables,
    resolve_tokens,
    validate_tree,
)
from template_experiment_tree.report import (
    flatten_sections,
    render_markdown,
    render_variables,
    summarize,
)
from template_experiment_tree.store import (
    ExperimentStoreError,
    default_store_path,
    load_tree,
    save_tree,
    tree_from_payload,
    tree_to_payload,
)
from template_experiment_tree.tree import (
    ExperimentNode,
    ExperimentTree,
    ExperimentTreeError,
    NodeStatus,
)

__all__ = [
    "ExperimentNode",
    "ExperimentStoreError",
    "ExperimentTree",
    "ExperimentTreeError",
    "ManuscriptVariablesError",
    "NodeStatus",
    "default_store_path",
    "flatten_sections",
    "generate_variables",
    "load_tree",
    "render_markdown",
    "render_variables",
    "resolve_tokens",
    "save_tree",
    "summarize",
    "tree_from_payload",
    "tree_to_payload",
    "validate_tree",
]
