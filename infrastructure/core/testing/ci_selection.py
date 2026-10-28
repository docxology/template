"""Conservative PR functional selection; complete release gates are separate."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import shutil
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from infrastructure.project.public_package_dependencies import declared_local_dependencies
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES


_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def changed_git_paths(root: Path, base: str) -> tuple[tuple[str, ...], bool]:
    """Observe real NUL-delimited changes; ambiguity/rename/delete means full."""
    if re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", base) is None:
        return (), True
    git = shutil.which("git", path=os.defpath)
    if git is None:
        return (), True
    try:
        result = subprocess.run(
            [
                git,
                "--no-replace-objects",
                "--no-pager",
                "-c",
                "core.hooksPath=" + os.devnull,
                "-c",
                "core.fsmonitor=false",
                "diff",
                "--name-status",
                "-z",
                "--find-renames",
                base + "...HEAD",
                "--",
            ],
            cwd=root,
            capture_output=True,
            timeout=30,
            check=False,
            env={"PATH": os.defpath, "LC_ALL": "C", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull},
        )
    except (OSError, subprocess.TimeoutExpired):
        return (), True
    if result.returncode:
        return (), True
    return _parse_changed_paths(result.stdout)


def _parse_changed_paths(output: bytes) -> tuple[tuple[str, ...], bool]:
    if not output:
        return (), False
    if not output.endswith(b"\0"):
        return (), True
    try:
        fields = iter(output.decode("utf-8").split("\0")[:-1])
    except UnicodeError:
        return (), True
    paths: list[str] = []
    ambiguous = False
    for status in fields:
        if re.fullmatch(r"[AMDTUXB]|[RC][0-9]{1,3}", status) is None:
            return (), True
        count = 2 if status.startswith(("R", "C")) else 1
        if status not in {"A", "M"}:
            ambiguous = True
        for _ in range(count):
            path = next(fields, None)
            if not path or Path(path).is_absolute() or ".." in Path(path).parts or "\\" in path:
                return (), True
            paths.append(path)
    return tuple(sorted(set(paths))), ambiguous


def affected_projects(root: Path, paths: tuple[str, ...], *, full: bool = False) -> tuple[tuple[str, ...], str]:
    """Only exact project-owned A/M changes may reduce the functional roster."""
    all_projects = tuple(sorted(PUBLIC_PROJECT_NAMES))
    if full or not paths:
        return all_projects, "full event or unavailable/ambiguous change base"
    changed = set()
    for name in paths:
        parts = Path(name).parts
        if len(parts) < 4 or parts[:2] != ("projects", "templates"):
            return all_projects, "global, documentation, control or unknown changed path"
        scope = "/".join(parts[1:3])
        if scope not in PUBLIC_PROJECT_NAMES:
            return all_projects, "unknown public scope"
        changed.add(scope)
    try:
        dependencies = {scope: set(declared_local_dependencies(root, scope)) for scope in all_projects}
    except (ValueError, OSError, KeyError):
        return all_projects, "dependency declarations unavailable"
    while True:
        expanded = changed | {scope for scope, providers in dependencies.items() if providers & changed}
        if expanded == changed:
            break
        changed = expanded
    return tuple(sorted(changed)), "exact project changes plus transitive reverse dependencies"


def functional_selection(root: Path, event: str, base: str = "") -> dict[str, Any]:
    paths, ambiguous = changed_git_paths(root, base) if event in {"pull_request", "push"} else ((), True)
    projects, reason = affected_projects(root, paths, full=ambiguous or event != "pull_request")
    return {
        "schema_version": "template-functional-selection/v1",
        "projects": list(projects),
        "changed_paths": list(paths),
        "change_roster_available": not (ambiguous and not paths) if event in {"pull_request", "push"} else True,
        "full": len(projects) == len(PUBLIC_PROJECT_NAMES),
        "reason": reason,
    }


def _infra_matrix(shards: list[list[str]]) -> dict[str, Any]:
    """Prepare the real LaTeX provider for its selected routine consumers."""
    native_latex = {
        "tests/infra_tests/rendering/test_pdf_latex_pipeline.py",
        "tests/infra_tests/rendering/test_pdf_renderer_fixes.py",
    }
    return {"include": [{"shard": i, "tex": bool(native_latex.intersection(files))} for i, files in enumerate(shards)]}


def _contract_matrix(
    shards: list[list[str]],
    modules: list[str],
    durations: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    """Dispatch long observed contracts first without changing canonical shard IDs."""
    from infrastructure.core.testing.ci_contracts import contract_preparation
    from infrastructure.core.testing.ci_module_durations import load_module_durations

    # Committed measured seconds keyed by module. They affect dispatch order
    # only, never selected work, deadlines or acceptance.
    observed_seconds = load_module_durations(_REPOSITORY_ROOT) if durations is None else durations
    rows: list[dict[str, Any]] = [
        {"shard": len(shards) + i, "module": name, **contract_preparation(name)} for i, name in enumerate(modules)
    ]
    rows.sort(key=lambda row: (-observed_seconds.get(row["module"], 0), row["module"]))
    return {"include": rows or [{"shard": -1, "module": "none", **contract_preparation("none")}]}


def infrastructure_selection(root: Path, plan: dict[str, Any]) -> dict[str, Any]:
    """Attach the exact functional shards and contract roster to a selection plan.

    One assembly used by the CI selection CLI and local gates, so both derive
    their shard roster from the same source-owned functions.
    """
    from infrastructure.core.testing.ci_contracts import contract_files
    from infrastructure.core.testing.ci_infra import infrastructure_files, infrastructure_shards

    changed = tuple(plan["changed_paths"])
    plan["infra_shards"] = infrastructure_shards(root, changed)
    plan["contract_modules"] = list(contract_files(infrastructure_files(root, changed), infrastructure_files(root)))
    return plan


def main() -> int:
    from infrastructure.core.testing.ci_smoke import project_smoke_matrix

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path.cwd()
    project_smoke_matrix(root)  # Validate every public behavioral selection even for a reduced PR.
    plan = functional_selection(root, os.environ.get("CI_EVENT", ""), os.environ.get("CI_BASE", ""))
    if not plan["change_roster_available"]:
        raise ValueError("change roster unavailable or malformed; cannot safely route changed infrastructure tests")
    infrastructure_selection(root, plan)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, sort_keys=True, indent=2) + "\n")
    print("matrix=" + json.dumps(project_smoke_matrix(root, tuple(plan["projects"]))))
    print("infra=" + json.dumps(_infra_matrix(plan["infra_shards"])))
    print("contracts=" + json.dumps(_contract_matrix(plan["infra_shards"], plan["contract_modules"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["affected_projects", "changed_git_paths", "functional_selection", "infrastructure_selection"]
