"""Strict source-bound, explicitly partial workflow extraction for the live lane."""

from __future__ import annotations

from typing import Any

from template_literature_meta_analysis.reproducibility.models import (
    NodeType,
    WorkflowGraph,
    WorkflowNode,
    build_workflow_graph,
)


def workflow_schema() -> dict[str, Any]:
    """Request at most three named nodes; no arbitrary code or paths are accepted."""
    properties = {
        "node_id": {"type": "string", "enum": ["n0", "n1", "n2"]},
        "node_name": {"type": "string"},
        "node_type": {"type": "string", "enum": [kind.value for kind in NodeType]},
        "source_quote": {"type": "string"},
        "description": {"type": "string"},
        "reproducibility_rating": {"type": "integer", "minimum": 1, "maximum": 4},
        "depends_on": {"type": "array", "items": {"type": "string", "enum": ["n0", "n1", "n2"]}},
    }
    return {
        "type": "object",
        "properties": {
            "nodes": {
                "type": "array",
                "minItems": 1,
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "properties": properties,
                    "required": list(properties),
                    "additionalProperties": False,
                },
            }
        },
        "required": ["nodes"],
        "additionalProperties": False,
    }


def parse_workflow(value: Any, source: str, paper_id: str) -> WorkflowGraph:
    """Reject malformed or fabricated nodes instead of silently dropping them."""
    if not isinstance(value, dict) or set(value) != {"nodes"}:
        raise ValueError("workflow must be exactly a nodes object")
    rows = value["nodes"]
    if not isinstance(rows, list) or not 1 <= len(rows) <= 3:
        raise ValueError("workflow requires one to three actual extracted nodes")
    expected = {
        "node_id",
        "node_name",
        "node_type",
        "source_quote",
        "description",
        "reproducibility_rating",
        "depends_on",
    }
    nodes: list[WorkflowNode] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != expected:
            raise ValueError("workflow node has missing or extra fields")
        for key in ("node_id", "node_name", "node_type", "source_quote", "description"):
            if not isinstance(row[key], str) or not row[key].strip() or len(row[key]) > 1000:
                raise ValueError(f"workflow {key} must be a bounded nonempty string")
        if row["node_id"] not in {"n0", "n1", "n2"} or row["node_id"] in seen:
            raise ValueError("workflow node identity is invalid or duplicated")
        seen.add(row["node_id"])
        quote = row["source_quote"]
        if len(quote) < 20 or quote not in source:
            raise ValueError("workflow quote is not verbatim in the exact consumed full text")
        rating = row["reproducibility_rating"]
        if type(rating) is not int or not 1 <= rating <= 4:
            raise ValueError("workflow rating must be an exact integer in [1, 4]")
        dependencies = row["depends_on"]
        if (
            not isinstance(dependencies, list)
            or len(dependencies) > 3
            or any(not isinstance(item, str) or item not in {"n0", "n1", "n2"} for item in dependencies)
            or len(set(dependencies)) != len(dependencies)
        ):
            raise ValueError("workflow dependencies must be a unique list of declared node IDs")
        nodes.append(
            WorkflowNode(
                row["node_id"],
                row["node_name"],
                NodeType(row["node_type"]),
                quote,
                row["description"],
                rating,
                depends_on=dependencies,
                paper_id=paper_id,
            )
        )
    # Dangling references/cycles are domain signals retained by the established
    # scorer. This bounded extraction does not claim a complete paper workflow.
    return build_workflow_graph(paper_id, nodes)
