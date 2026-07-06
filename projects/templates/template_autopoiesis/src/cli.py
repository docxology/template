"""CLI entry point for template_autopoiesis."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _get_project_root() -> Path:
    """Return the project root (parent of src/)."""
    return Path(__file__).parent.parent


def cmd_enumerate(args: argparse.Namespace) -> None:
    from .grammar import load_grammar
    from .expand import enumerate_all

    grammar = load_grammar(args.project_root or _get_project_root())
    cells = enumerate_all(grammar)
    print(json.dumps(cells, indent=2))


def cmd_expand(args: argparse.Namespace) -> None:
    from .grammar import load_grammar
    from .expand import expand, write_spec

    grammar = load_grammar(args.project_root or _get_project_root())
    seed = int(args.seed) if args.seed else None
    spec = expand(grammar, seed=seed)
    if args.output:
        path = write_spec(spec, args.output)
        print(f"Spec written to {path}")
    else:
        print(spec.to_json())


def cmd_sample(args: argparse.Namespace) -> None:
    from .grammar import load_grammar
    from .expand import sample

    grammar = load_grammar(args.project_root or _get_project_root())
    specs = sample(grammar, count=int(args.count))
    for s in specs:
        print(s.spec_hash, s.primitive_domain)


def cmd_materialize(args: argparse.Namespace) -> None:
    from .grammar import load_grammar
    from .expand import expand
    from .materialize import materialize

    project_root = Path(args.project_root or _get_project_root())
    grammar = load_grammar(project_root)
    seed = int(args.seed) if args.seed else None
    spec = expand(grammar, seed=seed)
    result = materialize(
        spec,
        out_root=args.out_root or (project_root / "output" / "children"),
        template_root=project_root,
        clean=args.clean,
    )
    print(f"Materialized: {result.root}")
    print(f"Tree hash: {result.tree_hash}")


def cmd_verify(args: argparse.Namespace) -> None:
    from .verify import verify_child_full

    report = verify_child_full(args.child_root)
    for check in report.checks:
        status = "PASS" if check.passed else "FAIL"
        print(f"  [{status}] {check.name}: {check.detail}")
    sys.exit(0 if report.all_passed else 1)


def cmd_honesty(args: argparse.Namespace) -> None:
    from .honesty import verify_honesty

    project_root = args.project_root or _get_project_root()
    manifest = verify_honesty(project_root)
    print(json.dumps(
        {
            "evidence": manifest.evidence,
            "missing_calls": manifest.missing_calls,
            "unsupported_claims": manifest.unsupported_claims,
            "all_passed": manifest.all_passed,
        },
        indent=2,
    ))
    sys.exit(0 if manifest.all_passed else 1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="autopoiesis",
        description="Autopoietic project generator CLI",
    )
    parser.add_argument("--project-root", default=None, help="Override project root path")
    sub = parser.add_subparsers(dest="command")

    # enumerate
    sub.add_parser("enumerate", help="List all grammar cells")

    # expand
    p_expand = sub.add_parser("expand", help="Expand grammar to a spec")
    p_expand.add_argument("--seed", default=None)
    p_expand.add_argument("--output", default=None, help="Write spec JSON to path")

    # sample
    p_sample = sub.add_parser("sample", help="Sample multiple specs")
    p_sample.add_argument("--count", default="5")

    # materialize
    p_mat = sub.add_parser("materialize", help="Materialize a child project")
    p_mat.add_argument("--seed", default=None)
    p_mat.add_argument("--out-root", default=None)
    p_mat.add_argument("--clean", action="store_true")

    # verify
    p_ver = sub.add_parser("verify", help="Verify a child project")
    p_ver.add_argument("child_root", help="Path to child project root")

    # honesty
    sub.add_parser("honesty", help="Run honesty manifest check")

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    dispatch = {
        "enumerate": cmd_enumerate,
        "expand": cmd_expand,
        "sample": cmd_sample,
        "materialize": cmd_materialize,
        "verify": cmd_verify,
        "honesty": cmd_honesty,
    }

    fn = dispatch.get(args.command)
    if fn is None:
        parser.print_help()
        sys.exit(1)
    fn(args)


if __name__ == "__main__":
    main()
