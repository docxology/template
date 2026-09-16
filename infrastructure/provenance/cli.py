"""CLI for the provenance DAG — ``record-artifact``, ``list``, ``review``, and experiment-tree subcommands.

Usage::

    python -m infrastructure.provenance record-artifact fig1 --path output/figures/fig1.pdf
    python -m infrastructure.provenance list
    python -m infrastructure.provenance review
    python -m infrastructure.provenance experiment-add baseline --run-command "uv run python run.py"
    python -m infrastructure.provenance experiment-validate
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from infrastructure.provenance.models import (
    ArtifactNode,
    NodeKind,
)
from infrastructure.provenance.review import review_provenance_store
from infrastructure.provenance.store import Provenance, ProvenanceStoreError
from infrastructure.provenance.tree import ExperimentStatus, ExperimentTree, validate_experiment_tree
from infrastructure.provenance.validation import validate_provenance_dag


def _get_store(args: argparse.Namespace) -> Provenance:
    dag_path = Path(args.dag_path) if args.dag_path else Path("output/provenance/dag.json")
    return Provenance(dag_path)


def _cmd_list(args: argparse.Namespace) -> int:
    store = _get_store(args)
    kind = NodeKind(args.kind) if args.kind else None
    nodes = store.list(kind=kind)
    if args.json:
        print(json.dumps([n.to_dict() for n in nodes], indent=2))
    else:
        for n in nodes:
            print(f"  [{n.kind.value}] {n.node_id[:12]}  {n.label}")
    return 0


def _cmd_record_artifact(args: argparse.Namespace) -> int:
    store = _get_store(args)
    node = ArtifactNode.create(label=args.label, path=args.path)
    store.record(node)
    print(f"recorded artifact: {node.node_id}")
    return 0


def _cmd_review(args: argparse.Namespace) -> int:
    store = _get_store(args)
    result = review_provenance_store(store)
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        for f in result.findings:
            print(f"  [{f.severity.value.upper()}] {f.code}: {f.message}")
        status = "PASS" if result.passed else "FAIL"
        print(f"\nReview: {status} ({len(result.findings)} findings)")
    return 0 if result.passed else 1


def _cmd_validate(args: argparse.Namespace) -> int:
    store = _get_store(args)
    report = validate_provenance_dag(store)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        for f in report.findings:
            print(f"  [{f.severity.upper()}] {f.code}: {f.message}")
        status = "PASS" if report.is_valid else "FAIL"
        print(
            f"\nDAG Validation: {status} (Nodes: {report.total_nodes}, "
            f"Edges: {report.total_edges}, Errors: {len(report.errors)}, Warnings: {len(report.warnings)})"
        )
    return 0 if report.is_valid else 1


def _parse_payload(raw: str) -> dict | None:
    """Parse an optional JSON payload string; empty means ``None``."""
    if not raw:
        return None
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("payload must be a JSON object")
    return parsed


def _cmd_experiment_add(args: argparse.Namespace) -> int:
    tree = ExperimentTree(_get_store(args))
    payload = _parse_payload(args.payload)
    if args.parent:
        node = tree.add_child(args.label, args.parent, args.run_command, payload=payload)
    else:
        node = tree.add_baseline(args.label, args.run_command, payload=payload)
    print(f"recorded experiment: {node.experiment_id} ({node.kind.value})")
    return 0


def _cmd_experiment_update(args: argparse.Namespace) -> int:
    tree = ExperimentTree(_get_store(args))
    status = ExperimentStatus(args.status) if args.status else None
    node = tree.update_node(args.experiment_id, status=status)
    print(f"updated experiment: {node.experiment_id} -> {node.status.value}")
    return 0


def _cmd_experiment_validate(args: argparse.Namespace) -> int:
    report = validate_experiment_tree(ExperimentTree(_get_store(args)))
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        for f in report.findings:
            print(f"  [{f.severity.upper()}] {f.code}: {f.message}")
        status = "PASS" if report.is_valid else "FAIL"
        print(f"\nExperiment Tree Validation: {status} (Nodes: {report.total_nodes}, Errors: {len(report.errors)})")
    return 0 if report.is_valid else 1


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argparse parser."""
    parser = argparse.ArgumentParser(
        prog="provenance",
        description="Provenance DAG CLI",
    )
    parser.add_argument("--dag-path", default="", help="Path to dag.json")
    sub = parser.add_subparsers(dest="command")

    # list
    p_list = sub.add_parser("list", help="List provenance nodes")
    p_list.add_argument("--kind", choices=[k.value for k in NodeKind], default="")
    p_list.add_argument("--json", action="store_true")
    p_list.set_defaults(func=_cmd_list)

    # record artifact
    p_rec = sub.add_parser("record-artifact", help="Record an artifact node")
    p_rec.add_argument("label")
    p_rec.add_argument("--path", default="")
    p_rec.set_defaults(func=_cmd_record_artifact)

    # review
    p_review = sub.add_parser("review", help="Review provenance DAG for issues")
    p_review.add_argument("--json", action="store_true")
    p_review.set_defaults(func=_cmd_review)

    # validate
    p_val = sub.add_parser("validate", help="Validate provenance DAG structure and acyclicity")
    p_val.add_argument("--json", action="store_true")
    p_val.set_defaults(func=_cmd_validate)

    # experiment-add
    p_exp_add = sub.add_parser("experiment-add", help="Add an experiment node (baseline, or child with --parent)")
    p_exp_add.add_argument("label")
    p_exp_add.add_argument("--run-command", required=True, help="Fixed run command for the whole tree")
    p_exp_add.add_argument("--parent", default="", help="Parent experiment id (omit for a baseline)")
    p_exp_add.add_argument("--payload", default="", help="Optional JSON object payload")
    p_exp_add.set_defaults(func=_cmd_experiment_add)

    # experiment-update
    p_exp_upd = sub.add_parser("experiment-update", help="Update an experiment node's status")
    p_exp_upd.add_argument("experiment_id")
    p_exp_upd.add_argument("--status", choices=[s.value for s in ExperimentStatus], required=True)
    p_exp_upd.set_defaults(func=_cmd_experiment_update)

    # experiment-validate
    p_exp_val = sub.add_parser("experiment-validate", help="Validate experiment-tree discipline")
    p_exp_val.add_argument("--json", action="store_true")
    p_exp_val.set_defaults(func=_cmd_experiment_validate)

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    try:
        result = args.func(args)
    except ProvenanceStoreError as exc:
        print(f"provenance store error: {exc}", file=sys.stderr)
        return 2
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"provenance error: {exc}", file=sys.stderr)
        return 2
    return result if isinstance(result, int) else 0


__all__ = ["build_parser", "main"]
