"""CLI for the provenance DAG — ``record-artifact``, ``list``, and ``review`` subcommands.

Usage::

    python -m infrastructure.provenance record-artifact fig1 --path output/figures/fig1.pdf
    python -m infrastructure.provenance list
    python -m infrastructure.provenance review
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
    return result if isinstance(result, int) else 0


__all__ = ["build_parser", "main"]
