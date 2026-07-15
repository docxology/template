"""CLI for skill discovery and manifest generation."""

import argparse
import json
import sys
from pathlib import Path

from infrastructure.core.logging.utils import get_logger

from .check_all_exports import run_cli as run_all_exports_audit
from .contracts import check_skill_contracts
from .discovery import (
    DEFAULT_SKILL_SEARCH_ROOTS,
    build_skill_index_markdown,
    discover_skills,
    manifest_matches_discovery,
    skill_descriptors_as_json_serializable,
    write_skill_manifest,
)
from .operation_registry import (
    build_operations_payload,
    discover_operations,
    operations_manifest_matches_discovery,
    write_operations_manifest,
)
from .runtime_sync import install_runtime_skills, runtime_status

logger = get_logger(__name__)


def _repo_root_from_args(args: argparse.Namespace) -> Path:
    return Path(args.repo_root).resolve()


def cmd_list_json(args: argparse.Namespace) -> int:
    """Print all discovered SKILL.md files as JSON to stdout."""
    root = _repo_root_from_args(args)
    skills = discover_skills(root, search_roots=args.roots)
    payload = skill_descriptors_as_json_serializable(skills)
    sys.stdout.write(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    return 0


def cmd_write(args: argparse.Namespace) -> int:
    """Write a skill manifest JSON file for all discovered SKILL.md files."""
    root = _repo_root_from_args(args)
    out = Path(args.output) if args.output else None
    path = write_skill_manifest(root, output_path=out, search_roots=args.roots)
    logger.info("Wrote skill manifest: %s", path)
    return 0


def cmd_write_index(args: argparse.Namespace) -> int:
    """Write a human-readable Markdown index for discovered skills."""
    root = _repo_root_from_args(args)
    out = Path(args.output) if args.output else root / "docs" / "_generated" / "skills_index.md"
    if not out.is_absolute():
        out = (root / out).resolve()
    skills = discover_skills(root, search_roots=args.roots)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_skill_index_markdown(skills, search_roots=args.roots), encoding="utf-8")
    logger.info("Wrote skill index: %s", out)
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """Verify that the skill manifest matches live discovery results."""
    root = _repo_root_from_args(args)
    mpath = Path(args.manifest)
    if not mpath.is_absolute():
        mpath = (root / mpath).resolve()
    else:
        mpath = mpath.resolve()
    ok, msg = manifest_matches_discovery(root, mpath, search_roots=args.roots)
    if ok:
        logger.info("%s", msg)
        manifest_rc = 0
    else:
        logger.error("%s", msg)
        manifest_rc = 1

    if not getattr(args, "all_exports", False):
        return manifest_rc

    audit_root = (root / "infrastructure").resolve()
    audit_rc = run_all_exports_audit(audit_root)
    return manifest_rc or audit_rc


def cmd_check_all_exports(args: argparse.Namespace) -> int:
    """Run the ``__all__`` audit on a directory (default: ``infrastructure/``)."""
    root = _repo_root_from_args(args)
    audit_root = (root / args.audit_root).resolve() if args.audit_root else (root / "infrastructure").resolve()
    return run_all_exports_audit(audit_root)


def cmd_check_contracts(args: argparse.Namespace) -> int:
    """Verify docs/prompts SKILL.md metadata contracts."""
    root = _repo_root_from_args(args)
    issues = check_skill_contracts(root)
    if issues:
        for issue in issues:
            logger.error("%s", issue)
        logger.error("%d skill contract violation(s)", len(issues))
        return 1
    logger.info("skill contracts ok")
    return 0


def cmd_operations_list_json(args: argparse.Namespace) -> int:
    """Print the machine-readable catalog of agent-invocable CLI operations."""
    root = _repo_root_from_args(args)
    ops = discover_operations(root)
    sys.stdout.write(json.dumps(build_operations_payload(ops), indent=2, ensure_ascii=False) + "\n")
    return 0


def cmd_operations_write(args: argparse.Namespace) -> int:
    """Write the operations manifest JSON (default: .cursor/operations_manifest.json)."""
    root = _repo_root_from_args(args)
    out = Path(args.output) if args.output else None
    path = write_operations_manifest(root, output_path=out)
    logger.info("Wrote operations manifest: %s", path)
    return 0


def cmd_operations_check(args: argparse.Namespace) -> int:
    """Verify the operations manifest matches live discovery results."""
    root = _repo_root_from_args(args)
    mpath = Path(args.manifest)
    mpath = mpath.resolve() if mpath.is_absolute() else (root / mpath).resolve()
    ok, msg = operations_manifest_matches_discovery(root, mpath)
    if ok:
        logger.info("%s", msg)
        return 0
    logger.error("%s", msg)
    return 1


def cmd_runtime_status(args: argparse.Namespace) -> int:
    """Audit the pinned source and Codex/Claude/Hermes user-runtime parity."""
    payload = runtime_status(_repo_root_from_args(args), Path(args.home))
    sys.stdout.write(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    return 0 if payload["ok"] else 1


def cmd_runtime_install(args: argparse.Namespace) -> int:
    """Install reversible links for the pinned skills, then verify parity."""
    root = _repo_root_from_args(args)
    home = Path(args.home)
    install = install_runtime_skills(root, home)
    status = runtime_status(root, home)
    sys.stdout.write(json.dumps({"install": install, "status": status}, indent=2, ensure_ascii=False) + "\n")
    return 0 if status["ok"] else 1


def _add_shared_cli_args(p: argparse.ArgumentParser) -> None:
    """Options shared by all subcommands (must live on subparsers so flags can follow the verb)."""
    p.add_argument(
        "--repo-root",
        default=".",
        help="Repository root (default: current directory)",
    )
    p.add_argument(
        "--roots",
        nargs="*",
        default=None,
        metavar="DIR",
        help=(
            "Override search roots relative to repo root "
            f"(default: {DEFAULT_SKILL_SEARCH_ROOTS}). "
            "Example: write --roots infrastructure docs"
        ),
    )


def build_parser() -> argparse.ArgumentParser:
    """Create the argparse parser for the skill CLI."""
    parser = argparse.ArgumentParser(
        description="Discover SKILL.md files and maintain .cursor/skill_manifest.json",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list-json", help="Print skills as JSON to stdout")
    _add_shared_cli_args(p_list)
    p_list.set_defaults(func=cmd_list_json)

    p_write = sub.add_parser("write", help="Write skill manifest JSON")
    _add_shared_cli_args(p_write)
    p_write.add_argument(
        "--output",
        default=None,
        help="Output file (default: .cursor/skill_manifest.json under repo root)",
    )
    p_write.set_defaults(func=cmd_write)

    p_write_index = sub.add_parser("write-index", help="Write generated Markdown skills index")
    _add_shared_cli_args(p_write_index)
    p_write_index.add_argument(
        "--output",
        default=None,
        help="Output file (default: docs/_generated/skills_index.md under repo root)",
    )
    p_write_index.set_defaults(func=cmd_write_index)

    p_check = sub.add_parser("check", help="Verify manifest matches discovery")
    _add_shared_cli_args(p_check)
    p_check.add_argument(
        "--manifest",
        default=".cursor/skill_manifest.json",
        help="Manifest path relative to repo root unless absolute",
    )
    p_check.add_argument(
        "--all-exports",
        action="store_true",
        help=("Also run the __all__ audit on infrastructure/ (modules that re-export symbols must declare __all__)."),
    )
    p_check.set_defaults(func=cmd_check)

    p_audit = sub.add_parser(
        "check-all-exports",
        help="Audit every public Python module under <audit-root> for missing __all__",
    )
    _add_shared_cli_args(p_audit)
    p_audit.add_argument(
        "--audit-root",
        default="infrastructure",
        help="Directory under repo root to audit (default: infrastructure)",
    )
    p_audit.set_defaults(func=cmd_check_all_exports)

    p_contracts = sub.add_parser(
        "check-contracts",
        help="Validate docs/prompts SKILL.md workflow metadata contracts",
    )
    _add_shared_cli_args(p_contracts)
    p_contracts.set_defaults(func=cmd_check_contracts)

    p_ops_list = sub.add_parser(
        "operations-list-json",
        help="Print the machine-readable catalog of agent-invocable CLI operations",
    )
    p_ops_list.add_argument("--repo-root", default=".", help="Repository root (default: current directory)")
    p_ops_list.set_defaults(func=cmd_operations_list_json)

    p_ops_write = sub.add_parser(
        "operations-write",
        help="Write the operations manifest JSON (machine-readable CLI catalog)",
    )
    p_ops_write.add_argument("--repo-root", default=".", help="Repository root (default: current directory)")
    p_ops_write.add_argument(
        "--output",
        default=None,
        help="Output file (default: .cursor/operations_manifest.json under repo root)",
    )
    p_ops_write.set_defaults(func=cmd_operations_write)

    p_ops_check = sub.add_parser(
        "operations-check",
        help="Verify the operations manifest matches live discovery",
    )
    p_ops_check.add_argument("--repo-root", default=".", help="Repository root (default: current directory)")
    p_ops_check.add_argument(
        "--manifest",
        default=".cursor/operations_manifest.json",
        help="Manifest path relative to repo root unless absolute",
    )
    p_ops_check.set_defaults(func=cmd_operations_check)

    p_runtime_status = sub.add_parser(
        "runtime-status",
        help="Audit pinned Agent Skills across Codex, Claude Code, and Hermes",
    )
    _add_shared_cli_args(p_runtime_status)
    p_runtime_status.add_argument("--home", default=str(Path.home()), help="User home to audit")
    p_runtime_status.set_defaults(func=cmd_runtime_status)

    p_runtime_install = sub.add_parser(
        "runtime-install",
        help="Reversibly install pinned Agent Skills across all three runtimes",
    )
    _add_shared_cli_args(p_runtime_install)
    p_runtime_install.add_argument("--home", default=str(Path.home()), help="User home to update")
    p_runtime_install.set_defaults(func=cmd_runtime_install)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the skill CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    roots = getattr(args, "roots", None)
    if roots is not None and len(roots) == 0:
        parser.error("--roots, if passed, must list at least one directory")
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
