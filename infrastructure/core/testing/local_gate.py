"""One local entry point for the commands hosted CI runs, offline by default.

Stages map onto hosted work:

* ``format`` / ``lint`` / ``types`` / ``gates`` — the ``Lint & Type Check`` job
  (Ruff check/format, the strict mypy ratchet, the static hygiene gates).
* ``security`` — the Bandit MEDIUM+ scan of the public scope.
* ``unit`` — the canonical project test stage CI runs per matrix entry.
* ``infra`` — ``detect-projects`` plus ``Infrastructure Smoke``: the exact
  functional selection plan and every shard it declares.

Every command is reused from the owning script or module; this gate only orders
them. ``--changed`` narrows file-scoped stages to the working-tree changes and
narrows the functional roster through the same selection functions CI uses.
``scripts/gates/local_gate.py`` is the thin CLI for this module.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from infrastructure.project.public_scope import (
    PUBLIC_PROJECT_NAMES,
    public_ci_lint_paths,
    public_ci_source_paths,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
UV = ("uv", "run", "--no-sync", "--offline")
STAGE_ORDER = ("format", "lint", "types", "security", "gates", "unit", "infra")
DEFAULT_PROJECT = os.environ.get("TEMPLATE_CI_PROJECT", "templates/template_code_project")


def _posix(paths: list[Path]) -> list[str]:
    return [path.as_posix() for path in paths]


def _in_scope(changed: tuple[str, ...], scopes: list[str], *, suffix: str = "") -> list[str]:
    """Return existing changed files that belong to one of the declared scopes."""
    selected: set[str] = set()
    for name in changed:
        if not (REPO_ROOT / name).is_file():
            continue
        if suffix and not name.endswith(suffix):
            continue
        if any(name == scope or name.startswith(scope.rstrip("/") + "/") for scope in scopes):
            selected.add(name)
    return sorted(selected)


def working_tree_changes(root: Path = REPO_ROOT) -> tuple[str, ...]:
    """Return staged, unstaged and untracked paths without touching the index."""
    git = shutil.which("git", path=os.defpath)
    if git is None:
        raise ValueError("git is required for --changed; rerun without it")
    environment = {"PATH": os.defpath, "LC_ALL": "C", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}
    commands = (
        [
            git,
            "--no-pager",
            "-c",
            "core.hooksPath=" + os.devnull,
            "-c",
            "core.fsmonitor=false",
            "diff",
            "--name-only",
            "-z",
            "HEAD",
        ],
        [git, "--no-pager", "ls-files", "--others", "--exclude-standard", "-z"],
    )
    paths: set[str] = set()
    for command in commands:
        try:
            result = subprocess.run(command, cwd=root, capture_output=True, timeout=60, check=False, env=environment)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise ValueError(f"changed-path observation failed: {error}") from error
        if result.returncode:
            raise ValueError("git refused the changed-path query; refusing to guess affected work")
        for raw in result.stdout.split(b"\0"):
            if not raw:
                continue
            name = raw.decode("utf-8", "surrogateescape")
            if not (root / name).is_file() and not (root / name).is_dir():
                continue
            paths.add(name)
    return tuple(sorted(paths))


def _lint_targets(changed: tuple[str, ...] | None) -> list[str]:
    scopes = _posix(public_ci_lint_paths(REPO_ROOT))
    return scopes if changed is None else _in_scope(changed, scopes)


def _source_targets(changed: tuple[str, ...] | None) -> list[str]:
    scopes = _posix(public_ci_source_paths(REPO_ROOT))
    if changed is None:
        return scopes
    return _in_scope(changed, scopes, suffix=".py")


def _security_targets() -> list[str]:
    return ["infrastructure/", "scripts/", *[f"projects/{name}/" for name in PUBLIC_PROJECT_NAMES]]


def _unit_commands(changed: tuple[str, ...] | None) -> list[list[str]]:
    if changed is None:
        projects = [DEFAULT_PROJECT]
    else:
        projects = sorted(
            {"/".join(Path(name).parts[1:3]) for name in changed if Path(name).parts[:2] == ("projects", "templates")}
            & set(PUBLIC_PROJECT_NAMES)
        )
        projects = projects or [DEFAULT_PROJECT]
    return [[*UV, "python", "scripts/pipeline/stage_01_test.py", "--project", project] for project in projects]


def _cheap_gate_commands() -> list[list[str]]:
    """Cheap contract gates that stay meaningful for any change set."""
    return [
        [*UV, "python", "scripts/gates/ci_module_durations_check.py"],
        [*UV, "python", "scripts/audit/check_exemplar_configs.py"],
        [*UV, "python", "scripts/audit/check_release_versions.py"],
    ]


def _gate_commands(changed: tuple[str, ...] | None) -> list[list[str]]:
    commands = [
        [*UV, "python", "scripts/audit/check_tracked_generated_artifacts.py"],
        [*UV, "python", "scripts/audit/check_tracked_all.py"],
        [*UV, "python", "scripts/audit/check_mirror_symlinks.py"],
        [*UV, "python", "-m", "infrastructure.skills", "check-all-exports"],
        [*UV, "python", "-m", "infrastructure.skills", "operations-check"],
        *_cheap_gate_commands(),
    ]
    if changed is None:
        return commands
    # Whole-tree controls cannot describe a partial change set; keep the cheap
    # contract gates and skip the rest instead of implying partial coverage.
    return _cheap_gate_commands()


def _infra_plan(changed: tuple[str, ...] | None) -> dict:
    """Build the functional plan with the selection functions CI itself calls."""
    from infrastructure.core.testing.ci_selection import functional_selection, infrastructure_selection

    plan = functional_selection(REPO_ROOT, "", "")
    if changed is not None:
        plan["changed_paths"] = list(changed)
    return infrastructure_selection(REPO_ROOT, plan)


def _infra_commands(plan: dict, working_directory: Path) -> list[list[str]]:
    plan_path = working_directory / "functional-selection.json"
    shards = len(plan["infra_shards"]) + len(plan["contract_modules"])
    return [
        [
            *UV,
            "python",
            "-m",
            "infrastructure.core.testing.ci_infra",
            "--plan",
            str(plan_path),
            "--shard",
            str(shard),
            "--directory",
            str(working_directory / f"shard-{shard}"),
        ]
        for shard in range(shards)
    ]


def stage_commands(
    stage: str, changed: tuple[str, ...] | None, working_directory: Path = Path("<tmp>")
) -> list[list[str]]:
    """Return the exact argv list for one stage, in execution order."""
    if stage == "format":
        targets = _lint_targets(changed)
        return [[*UV, "ruff", "format", "--check", *targets]] if targets else []
    if stage == "lint":
        targets = _lint_targets(changed)
        if not targets:
            return []
        commands = [[*UV, "ruff", "check", *targets]]
        if changed is None:
            # File-scoped lint cannot bound a repository-wide ratchet; keep it in
            # the full run where the complete scan root is actually present.
            commands.append([*UV, "python", "scripts/gates/module_line_count_check.py"])
        return commands
    if stage == "types":
        targets = _source_targets(changed)
        return [[*UV, "python", "scripts/gates/mypy_ratchet.py", *targets]] if targets else []
    if stage == "security":
        if changed is not None and not _in_scope(changed, _security_targets(), suffix=".py"):
            return []
        return [[*UV, "python", "-m", "bandit", "-r", "-ll", "-c", "bandit.yaml", *_security_targets()]]
    if stage == "gates":
        return _gate_commands(changed)
    if stage == "unit":
        return _unit_commands(changed)
    if stage == "infra":
        return _infra_commands(_infra_plan(changed), working_directory)
    raise ValueError(f"unknown stage {stage!r}; choose from {', '.join(STAGE_ORDER)}")


def _write_plan(plan: dict, working_directory: Path) -> None:
    working_directory.mkdir(parents=True, exist_ok=True)
    (working_directory / "functional-selection.json").write_text(json.dumps(plan, sort_keys=True, indent=2) + "\n")


def _run(stage: str, changed: tuple[str, ...] | None) -> int:
    if stage != "infra":
        return _execute(stage, stage_commands(stage, changed))
    with tempfile.TemporaryDirectory(prefix="local-gate-") as directory:
        working_directory = Path(directory)
        plan = _infra_plan(changed)
        _write_plan(plan, working_directory)
        return _execute(stage, _infra_commands(plan, working_directory))


def _execute(stage: str, commands: list[list[str]]) -> int:
    if not commands:
        print(f"[local-gate] {stage}: no affected files; nothing to run")
        return 0
    environment = {key: value for key, value in os.environ.items() if key != "PYTEST_ADDOPTS"}
    for command in commands:
        print(f"[local-gate] {stage}: {' '.join(command)}", flush=True)
        result = subprocess.run(command, cwd=REPO_ROOT, check=False, env=environment)
        if result.returncode:
            print(f"[local-gate] {stage}: failed with exit {result.returncode}", file=sys.stderr)
            return result.returncode
    print(f"[local-gate] {stage}: passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run or describe the requested stages."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stages", nargs="*", metavar="stage", help=f"One or more of: {', '.join(STAGE_ORDER)}, all.")
    parser.add_argument("--changed", action="store_true", help="Restrict to affected working-tree modules.")
    parser.add_argument("--list", action="store_true", help="Print the plan without running it.")
    args = parser.parse_args(argv)

    unknown = sorted(set(args.stages) - {*STAGE_ORDER, "all"})
    if unknown:
        parser.error(f"unknown stage(s): {', '.join(unknown)}; choose from {', '.join(STAGE_ORDER)}, all")
    stages = list(args.stages) or ["all"]
    if "all" in stages:
        if len(stages) > 1:
            parser.error("'all' cannot be combined with other stages")
        stages = list(STAGE_ORDER)
    try:
        changed = working_tree_changes() if args.changed else None
    except ValueError as error:
        parser.error(str(error))
    if args.list:
        for stage in stages:
            print(f"# {stage}")
            if stage == "infra":
                plan = _infra_plan(changed)
                print(f"# selected files: {sum(len(shard) for shard in plan['infra_shards'])}")
                commands = _infra_commands(plan, Path("<tmp>"))
            else:
                commands = stage_commands(stage, changed)
            for command in commands or [["<nothing to run>"]]:
                print("  " + " ".join(command))
        return 0
    for stage in stages:
        code = _run(stage, changed)
        if code:
            return code
    print("[local-gate] all requested stages passed")
    return 0


__all__ = ["STAGE_ORDER", "main", "stage_commands", "working_tree_changes"]
