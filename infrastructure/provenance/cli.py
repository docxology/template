"""CLI for the provenance DAG — ``record``, ``list``, ``query``, and ``review`` subcommands.

Usage::

    python -m infrastructure.provenance record artifact fig1.pdf --path output/figures/fig1.pdf
    python -m infrastructure.provenance list
    python -m infrastructure.provenance review
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from infrastructure.provenance.models import (
    ArtifactNode,
    NodeKind,
)
from infrastructure.provenance.review import review_provenance_store
from infrastructure.provenance.store import Provenance


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


def build_parser() -> argparse.ArgumentParser:
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

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    result = args.func(args)
    return result if isinstance(result, int) else 0


__all__ = ["build_parser", "main"]
