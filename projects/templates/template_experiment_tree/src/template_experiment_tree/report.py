"""Query and report functions over the experiment tree.

Pure functions over a tree: no I/O, deterministic output. The manuscript
render discipline consumes ``render_markdown`` and ``render_variables``
so the paper is always a projection of the tree state.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from template_experiment_tree.tree import ExperimentNode, ExperimentTree, NodeStatus


def summarize(tree: ExperimentTree) -> dict[str, Any]:
    """Counts by status and outcome, plus per-round winners."""
    answered = tree.by_status(NodeStatus.ANSWERED)
    return {
        "total_nodes": len(tree.nodes()),
        "provisional": len(tree.by_status(NodeStatus.PROVISIONAL)),
        "frozen": len(tree.by_status(NodeStatus.FROZEN)),
        "answered": len(answered),
        "wins": len(tree.winners()),
        "losses": sum(1 for node in answered if node.outcome == "loss"),
        "dead_ends": len(tree.dead_ends()),
        "max_depth": max((tree.depth(node.node_id) for node in tree.nodes()), default=0),
        "winners_per_round": {
            str(round_number): [node.node_id for node in nodes]
            for round_number, nodes in tree.winners_per_round().items()
        },
    }


def _table_row(node: ExperimentNode) -> str:
    answer = (node.answer or "").replace("|", "\\|")
    command = node.run_command.replace("|", "\\|")
    return f"| {node.node_id} | {node.title} | {node.outcome} | R{node.round_number} | `{command}` | {answer} |"


def render_markdown(tree: ExperimentTree) -> str:
    """Full living-record markdown: results, in-progress, dead ends."""
    lines: list[str] = ["# Experiment Tree Record", ""]
    summary = summarize(tree)
    lines.append(
        f"{summary['total_nodes']} experiments: {summary['answered']} answered "
        f"({summary['wins']} wins, {summary['losses']} losses, {summary['dead_ends']} dead ends), "
        f"{summary['frozen']} frozen, {summary['provisional']} provisional."
    )
    lines.append("")

    lines.append("## Results (answered nodes)")
    lines.append("")
    lines.append("| Node | Title | Outcome | Round | Run command | Answer |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    answered = tree.by_status(NodeStatus.ANSWERED)
    if answered:
        lines.extend(_table_row(node) for node in answered)
    else:
        lines.append("| - | No answered experiments yet | | | | |")
    lines.append("")

    lines.append("## In progress (frozen, preregistered)")
    lines.append("")
    frozen = tree.by_status(NodeStatus.FROZEN)
    if frozen:
        lines.extend(f"- **{node.node_id}** — {node.title} (`{node.run_command}`)" for node in frozen)
    else:
        lines.append("- No frozen experiments.")
    lines.append("")

    lines.append("## Dead ends (negative-result registry)")
    lines.append("")
    dead = tree.dead_ends()
    if dead:
        lines.extend(f"- **{node.node_id}** — {node.title}: {node.answer}" for node in dead)
    else:
        lines.append("- No dead ends recorded.")
    lines.append("")

    lines.append("## Planned (provisional)")
    lines.append("")
    provisional = tree.by_status(NodeStatus.PROVISIONAL)
    if provisional:
        lines.extend(f"- {node.node_id}: {node.title} (`{node.run_command}`)" for node in provisional)
    else:
        lines.append("- No planned experiments.")
    lines.append("")
    return "\n".join(lines)


def render_variables(tree: ExperimentTree) -> dict[str, Any]:
    """Tree-derived manuscript variables (never hand-typed)."""
    summary = summarize(tree)
    return {
        "experiment_tree": summary,
        "exp_total": summary["total_nodes"],
        "exp_answered": summary["answered"],
        "exp_frozen": summary["frozen"],
        "exp_provisional": summary["provisional"],
        "exp_wins": summary["wins"],
        "exp_losses": summary["losses"],
        "exp_dead_ends": summary["dead_ends"],
        "exp_max_depth": summary["max_depth"],
        "exp_winners_per_round": summary["winners_per_round"],
    }


def flatten_sections(tree: ExperimentTree) -> dict[str, str]:
    """Map manuscript section slugs to generated markdown bodies."""
    summary = summarize(tree)
    return {
        "results": _section_results(tree),
        "in_progress": _section_in_progress(tree),
        "dead_ends": _section_dead_ends(tree),
        "overview": (
            f"This living record tracks {summary['total_nodes']} experiments across a "
            f"version-controlled tree of depth {summary['max_depth']}."
        ),
    }


def _section_results(tree: ExperimentTree) -> str:
    answered = tree.by_status(NodeStatus.ANSWERED)
    if not answered:
        return "No answered experiments yet."
    rows = ["| Node | Outcome | Answer |", "| --- | --- | --- |"]
    rows.extend(
        "| {} | {} | {} |".format(node.node_id, node.outcome, (node.answer or "").replace("|", "\\|"))
        for node in answered
    )
    return "\n".join(rows)


def _section_in_progress(tree: ExperimentTree) -> str:
    frozen = tree.by_status(NodeStatus.FROZEN)
    if not frozen:
        return "No frozen experiments."
    return "\n".join(f"- {node.node_id}: {node.title}" for node in frozen)


def _section_dead_ends(tree: ExperimentTree) -> str:
    dead = tree.dead_ends()
    if not dead:
        return "No dead ends recorded."
    return "\n".join(f"- {node.node_id}: {node.answer}" for node in dead)


def resolve_token_map(tokens: Mapping[str, Any], variables: Mapping[str, Any]) -> dict[str, Any]:
    """Resolve ``{{TOKEN}}`` placeholders in mapping values from tree variables.

    Raises:
        KeyError: If a token has no tree-derived backing (fail closed).
    """
    resolved: dict[str, Any] = {}
    for key, value in tokens.items():
        if isinstance(value, str):
            out = value
            for token, replacement in variables.items():
                out = out.replace("{{" + token.upper() + "}}", str(replacement))
            if "{{" in out:
                unknown = out[out.index("{{") : out.index("}}", out.index("{{")) + 2]
                raise KeyError(f"manuscript token {unknown} has no tree-derived variable backing")
            resolved[key] = out
        else:
            resolved[key] = value
    return resolved
