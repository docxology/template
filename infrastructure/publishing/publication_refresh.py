"""Artifact-only coordinated publication generation; never release acceptance."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import importlib.metadata
import json
import os
from pathlib import Path
import re
import shutil
import time
import tomllib
from typing import Any

from infrastructure.core.secrets import strip_secret_env
from infrastructure.project.public_acceptance_auxiliary_supervision import supervise
from infrastructure.publishing.publication_refresh_custody import (
    REFRESH_MODES,
    build_plan,
    check_footprint,
    commit_candidate,
    finish_review,
    gate_commands,
    git,
    load_plan,
    write_json,
)


def provider_waves(graph: dict[str, list[str]]) -> list[list[str]]:
    """Schedule the actual provider graph without concurrent dependent writers."""
    done: set[str] = set()
    waves = []
    while len(done) < len(graph):
        ready = sorted(scope for scope, parents in graph.items() if scope not in done and set(parents) <= done)
        if not ready:
            raise ValueError("provider graph has an unknown dependency or cycle")
        waves.append(ready)
        done.update(ready)
    return waves


def run_logged(root: Path, directory: Path, label: str, argv: list[str], *, timeout: int = 5400) -> int:
    """Retain original bytes/exit through the existing owned-process supervisor."""
    if re.fullmatch(r"[A-Za-z0-9_-]+", label) is None:
        raise ValueError("refresh command label must be one bounded path component")
    diagnostics = directory / "diagnostics"
    diagnostics.mkdir(exist_ok=True)
    executable = shutil.which(argv[0])
    if executable is None:
        raise ValueError("prepared refresh executable is unavailable")
    argv = [executable, *argv[1:]]
    cell = root / "output/readiness/publication-refresh" / label
    if cell.exists():
        raise ValueError("refresh process evidence must be fresh")
    environment = strip_secret_env(dict(os.environ))
    for name in ("SSH_AUTH_SOCK", "GPG_AGENT_INFO"):
        environment.pop(name, None)
    process = supervise(argv, root, cell, time.monotonic() + timeout, environment=environment)
    for stream in ("stdout", "stderr"):
        body = (root / process["streams"][stream]["path"]).read_bytes()
        with (diagnostics / f"{label}.{stream}").open("xb") as output:
            output.write(body)
    original = process["exit_code"]
    code = original if type(original) is int and original != 0 else 0 if process["accepted"] else 1
    if process["timed_out"]:
        code = 124
    receipt = {
        "argv": argv,
        "returncode": code,
        "original_exit_code": original,
        "process": process,
        "source_commit": git(root, "rev-parse", "HEAD").decode().strip(),
        **{stream + "_sha256": process["streams"][stream]["sha256"] for stream in ("stdout", "stderr")},
    }
    write_json(diagnostics / f"{label}.exit.json", receipt)
    print(f"{label}: original exit {original}; supervised result {code}", flush=True)
    return code


def _source_plan(root: Path, directory: Path) -> dict[str, Any]:
    plan = load_plan(directory)
    if plan != build_plan(root, plan["base_commit"], plan["platform_version"], mode=plan["mode"]):
        raise ValueError("publication refresh plan is stale or altered")
    return plan


def prepare_environments(root: Path, directory: Path) -> int:
    """Prepare each own lock in provider order before any expensive producer."""
    plan = _source_plan(root, directory)
    python = str(root / ".venv/bin/python")
    for wave in provider_waves(plan["providers"]):
        for scope in wave:
            if scope == "root":
                continue
            project = root / "projects" / scope
            metadata = tomllib.loads((project / "pyproject.toml").read_text())
            argv = ["uv", "sync", "--locked", "--project", str(project), "--python", python]
            for extra in ("dev", "formal-tools"):
                if extra in metadata.get("project", {}).get("optional-dependencies", {}):
                    argv.extend(["--extra", extra])
            if run_logged(root, directory, scope.replace("/", "__") + "-prepare", argv, timeout=900):
                return 1
    probe = (
        "import importlib.metadata as m,json,sys;from pathlib import Path;import infrastructure;"
        "expected=sys.argv[1];root=Path(sys.argv[2]).resolve();"
        "assert m.version('research-project-template')==infrastructure.__version__==expected;"
        "assert Path(infrastructure.__file__).resolve().is_relative_to(root/'infrastructure');"
        "print(json.dumps({'sdk_version':infrastructure.__version__,'sdk_origin':infrastructure.__file__,"
        "'python':sys.version,'prefix':sys.prefix}))"
    )
    for scope in ("root", *plan["public_roster"]):
        prefix = root if scope == "root" else root / "projects" / scope
        argv = [str(prefix / ".venv/bin/python"), "-I", "-B", "-c", probe, plan["platform_version"], str(root)]
        if run_logged(root, directory, scope.replace("/", "__") + "-runtime", argv, timeout=120):
            return 1
    _source_plan(root, directory)
    write_json(
        directory / "prepared.json",
        {"base_commit": plan["base_commit"], "platform_version": plan["platform_version"], "mode": plan["mode"]},
    )
    return 0


def generation_commands(root: Path, plan: dict[str, Any], wave: list[str]) -> list[tuple[str, list[str]]]:
    """Select only the frozen original refresh or unchanged-output rebind CLI."""
    commands = []
    for scope in wave:
        if scope == "root":
            continue
        if scope in plan["dependent_analysis"]:
            commands.append(
                (
                    scope.replace("/", "__") + "-analysis",
                    [str(root / ".venv/bin/python"), "scripts/pipeline/stage_02_analysis.py", "--project", scope],
                )
            )
        argv = [
            str(root / ".venv/bin/python"),
            "scripts/maintenance/refresh_rendered_provenance.py",
            "--project",
            scope,
        ]
        if scope in plan["rebind"]:
            argv.append("--rebind")
        commands.append((scope.replace("/", "__") + "-generate", argv))
    return commands


def _generation_sequence(root: Path, directory: Path, commands: list[tuple[str, list[str]]]) -> int:
    """Keep a project's actual analysis/refresh commands sequential and terminal."""
    for label, argv in commands:
        code = run_logged(root, directory, label, argv)
        if code:
            return code
    return 0


def generate(root: Path, directory: Path, jobs: int) -> int:
    """Refresh tracked publication copies; revalidate the unchanged complement."""
    if type(jobs) is not int or not 1 <= jobs <= 4:
        raise ValueError("publication refresh workers must be between one and four")
    plan = _source_plan(root, directory)
    prepared = json.loads((directory / "prepared.json").read_bytes())
    if prepared != {
        "base_commit": plan["base_commit"],
        "platform_version": plan["platform_version"],
        "mode": plan["mode"],
    }:
        raise ValueError("current own runtime preparation is missing")
    epoch = git(root, "show", "-s", "--format=%ct", plan["base_commit"]).decode().strip()
    os.environ.update(
        SOURCE_DATE_EPOCH=epoch,
        TEMPLATE_BUILD_EPOCH_SOURCE="git:" + plan["base_commit"],
        MPLBACKEND="Agg",
        ANALYSIS_SCRIPT_TIMEOUT_SEC="1800",
    )
    for wave in provider_waves(plan["providers"]):
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            futures = [
                pool.submit(_generation_sequence, root, directory, generation_commands(root, plan, [scope]))
                for scope in wave
                if scope != "root"
            ]
            codes = [future.result() for future in futures]
        if any(codes):
            return 1
        check_footprint(root, plan)
    write_json(
        directory / "generated.json",
        {
            "base_commit": plan["base_commit"],
            "mode": plan["mode"],
            "refresh": plan["refresh"],
            "dependent_analysis": sorted(plan["dependent_analysis"]),
            "rebind": plan["rebind"],
            "provider_waves": provider_waves(plan["providers"]),
        },
    )
    return 0


def verify(root: Path, directory: Path) -> int:
    """Run both unchanged strict gates on the committed disposable candidate."""
    candidate = json.loads((directory / "candidate.json").read_bytes())
    if git(root, "rev-parse", "HEAD").decode().strip() != candidate["commit"]:
        raise ValueError("candidate moved before strict verification")
    codes = [
        run_logged(root, directory, label, argv, timeout=1800) for label, argv in gate_commands(root, directory).items()
    ]
    return 1 if any(codes) else 0


def run_coordinated(
    root: Path, directory: Path, source_sha: str, expected_version: str, jobs: int, *, mode: str = "refresh"
) -> int:
    """Run every existing phase in one execution-account payload; failure is terminal."""
    if type(jobs) is not int or not 1 <= jobs <= 4:
        raise ValueError("publication refresh workers must be between one and four")
    common = ["--repo-root", str(root), "--directory", str(directory), "--mode", mode]
    phases = (
        ["plan", "--source-sha", source_sha, "--expected-version", expected_version],
        ["prepare"],
        ["generate", "--jobs", str(jobs)],
        ["candidate"],
        ["verify"],
        ["finish"],
    )
    # Public artifact DATA must remain readable by the original upload account.
    # This does not change atomic producer modes or any ownership predicate.
    previous_umask = os.umask(0o022)
    try:
        for phase in phases:
            result = main([*common, *phase])
            if result:
                return result
    finally:
        os.umask(previous_umask)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Expose only the finite phases used by the manual artifact workflow."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--mode", choices=REFRESH_MODES, default="refresh")
    commands = parser.add_subparsers(dest="phase", required=True)
    plan_parser = commands.add_parser("plan")
    plan_parser.add_argument("--source-sha", required=True)
    plan_parser.add_argument("--expected-version", required=True)
    coordinated = commands.add_parser("run")
    coordinated.add_argument("--source-sha", required=True)
    coordinated.add_argument("--expected-version", required=True)
    coordinated.add_argument("--jobs", type=int, default=2)
    commands.add_parser("prepare")
    run = commands.add_parser("generate")
    run.add_argument("--jobs", type=int, default=2)
    for phase in ("candidate", "verify", "finish"):
        commands.add_parser(phase)
    args = parser.parse_args(argv)
    root, directory = args.repo_root.absolute(), args.directory.absolute()
    if directory.is_relative_to(root) or directory != directory.resolve():
        raise ValueError("refresh evidence needs a fresh real directory outside Source")
    if args.phase == "run":
        return run_coordinated(root, directory, args.source_sha, args.expected_version, args.jobs, mode=args.mode)
    if args.phase != "plan":
        load_plan(directory, mode=args.mode)
    if args.phase == "plan":
        if importlib.metadata.version("research-project-template") != args.expected_version:
            raise ValueError("prepared Root distribution does not match requested Source version")
        directory.mkdir()
        write_json(directory / "plan.json", build_plan(root, args.source_sha, args.expected_version, mode=args.mode))
    elif args.phase == "prepare":
        return prepare_environments(root, directory)
    elif args.phase == "generate":
        return generate(root, directory, args.jobs)
    elif args.phase == "candidate":
        generated = json.loads((directory / "generated.json").read_bytes())
        plan = load_plan(directory)
        if (
            generated.get("base_commit") != plan["base_commit"]
            or generated.get("mode") != plan["mode"]
            or generated.get("refresh") != plan["refresh"]
            or generated.get("dependent_analysis") != sorted(plan["dependent_analysis"])
            or generated.get("rebind") != plan["rebind"]
        ):
            raise ValueError("complete producer result is missing")
        commit_candidate(root, directory)
    elif args.phase == "verify":
        return verify(root, directory)
    else:
        finish_review(root, directory)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "generate",
    "generation_commands",
    "main",
    "prepare_environments",
    "provider_waves",
    "run_coordinated",
    "run_logged",
    "verify",
]
