"""Artifact-only coordinated publication generation; never release acceptance."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
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
from infrastructure.publishing._publication_refresh_protocol import (
    COMMAND_STREAMS,
    command_receipt,
    gate_commands,
    generation_commands,
)
from infrastructure.publishing.publication_refresh_custody import (
    REFRESH_MODES,
    build_plan,
    check_footprint,
    commit_candidate,
    finish_review,
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


def run_logged(
    root: Path,
    directory: Path,
    label: str,
    argv: list[str],
    *,
    timeout: int = 5400,
    environment: Mapping[str, str] | None = None,
) -> int:
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
    child_environment = strip_secret_env({**os.environ, **(environment or {})})
    for name in ("SSH_AUTH_SOCK", "GPG_AGENT_INFO"):
        child_environment.pop(name, None)
    process = supervise(argv, root, cell, time.monotonic() + timeout, environment=child_environment)
    for stream in COMMAND_STREAMS:
        body = (root / process["streams"][stream]["path"]).read_bytes()
        with (diagnostics / f"{label}.{stream}").open("xb") as output:
            output.write(body)
    receipt = command_receipt(argv, process, git(root, "rev-parse", "HEAD").decode().strip())
    write_json(diagnostics / f"{label}.exit.json", receipt)
    code = receipt["returncode"]
    print(f"{label}: original exit {receipt['original_exit_code']}; supervised result {code}", flush=True)
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


def _generation_sequence(
    root: Path,
    directory: Path,
    commands: list[tuple[str, list[str]]],
    *,
    environment: Mapping[str, str] | None = None,
) -> int:
    """Keep a project's actual analysis/refresh commands sequential and terminal."""
    for label, argv in commands:
        code = run_logged(root, directory, label, argv, environment=environment)
        if code:
            return code
    return 0


def _run_generation_wave(
    root: Path,
    directory: Path,
    sequences: list[list[tuple[str, list[str]]]],
    environment: Mapping[str, str],
) -> bool:
    """Finish every admitted sequence and report the first execution error."""
    failed = False
    first_error: BaseException | None = None
    for commands in sequences:
        try:
            code = _generation_sequence(root, directory, commands, environment=environment)
        except BaseException as error:
            if first_error is None:
                first_error = error
        else:
            failed |= code != 0
    if first_error is not None:
        raise first_error
    return failed


def _require_single_worker(jobs: int) -> None:
    """Keep peer producers outside the shared execution-account census."""
    if type(jobs) is not int or jobs != 1:
        raise ValueError("publication refresh workers must be exactly one for the shared execution-account census")


def generate(root: Path, directory: Path, jobs: int) -> int:
    """Refresh tracked publication copies; revalidate the unchanged complement."""
    code, _ = _generate(root, directory, jobs)
    return code


def _generate(root: Path, directory: Path, jobs: int) -> tuple[int, dict[str, str]]:
    _require_single_worker(jobs)
    plan = _source_plan(root, directory)
    prepared = json.loads((directory / "prepared.json").read_bytes())
    if prepared != {
        "base_commit": plan["base_commit"],
        "platform_version": plan["platform_version"],
        "mode": plan["mode"],
    }:
        raise ValueError("current own runtime preparation is missing")
    epoch = git(root, "show", "-s", "--format=%ct", plan["base_commit"]).decode().strip()
    environment = {
        "SOURCE_DATE_EPOCH": epoch,
        "TEMPLATE_BUILD_EPOCH_SOURCE": "git:" + plan["base_commit"],
        "MPLBACKEND": "Agg",
        "ANALYSIS_SCRIPT_TIMEOUT_SEC": "1800",
    }
    waves = provider_waves(plan["providers"])
    for wave in waves:
        sequences = [generation_commands(root, plan, [scope]) for scope in wave if scope != "root"]
        if sequences:
            # The producer owns its child deadline even when the caller is interrupted.
            with ThreadPoolExecutor(max_workers=1) as pool:
                failed = pool.submit(_run_generation_wave, root, directory, sequences, environment).result()
            if failed:
                return 1, environment
        check_footprint(root, plan)
    write_json(
        directory / "generated.json",
        {
            "base_commit": plan["base_commit"],
            "mode": plan["mode"],
            "refresh": plan["refresh"],
            "dependent_analysis": sorted(plan["dependent_analysis"]),
            "rebind": plan["rebind"],
            "provider_waves": waves,
        },
    )
    return 0, environment


def verify(root: Path, directory: Path, *, environment: Mapping[str, str] | None = None) -> int:
    """Run both unchanged strict gates on the committed disposable candidate."""
    candidate = json.loads((directory / "candidate.json").read_bytes())
    if git(root, "rev-parse", "HEAD").decode().strip() != candidate["commit"]:
        raise ValueError("candidate moved before strict verification")
    codes = [
        run_logged(root, directory, label, argv, timeout=1800, environment=environment)
        for label, argv in gate_commands(root, directory).items()
    ]
    return 1 if any(codes) else 0


def _phase_paths(root: Path, directory: Path, *, mode: str | None = None) -> tuple[Path, Path]:
    root, directory = root.absolute(), directory.absolute()
    if directory.is_relative_to(root) or directory != directory.resolve():
        raise ValueError("refresh evidence needs a fresh real directory outside Source")
    if mode is not None:
        load_plan(directory, mode=mode)
    return root, directory


def _create_plan(root: Path, directory: Path, source_sha: str, expected_version: str, mode: str) -> None:
    if importlib.metadata.version("research-project-template") != expected_version:
        raise ValueError("prepared Root distribution does not match requested Source version")
    directory.mkdir()
    write_json(directory / "plan.json", build_plan(root, source_sha, expected_version, mode=mode))


def _capture_candidate(root: Path, directory: Path) -> None:
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


def run_coordinated(
    root: Path, directory: Path, source_sha: str, expected_version: str, jobs: int, *, mode: str = "refresh"
) -> int:
    """Run every existing phase in one execution-account payload; failure is terminal."""
    _require_single_worker(jobs)
    if mode not in REFRESH_MODES:
        _parse_args(["--mode", mode])
    # Public artifact DATA must remain readable by the original upload account.
    # This does not change atomic producer modes or any ownership predicate.
    previous_umask = os.umask(0o022)
    try:
        _create_plan(*_phase_paths(root, directory), source_sha, expected_version, mode)
        result = prepare_environments(*_phase_paths(root, directory, mode=mode))
        if result:
            return result
        phase_root, phase_directory = _phase_paths(root, directory, mode=mode)
        result, environment = _generate(phase_root, phase_directory, jobs)
        if result:
            return result
        _capture_candidate(*_phase_paths(root, directory, mode=mode))
        result = verify(*_phase_paths(root, directory, mode=mode), environment=environment)
        if result:
            return result
        finish_review(*_phase_paths(root, directory, mode=mode))
    finally:
        os.umask(previous_umask)
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
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
    coordinated.add_argument("--jobs", type=int, default=1)
    commands.add_parser("prepare")
    run = commands.add_parser("generate")
    run.add_argument("--jobs", type=int, default=1)
    for phase in ("candidate", "verify", "finish"):
        commands.add_parser(phase)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Expose only the finite phases used by the manual artifact workflow."""
    args = _parse_args(argv)
    if args.phase in ("run", "generate"):
        _require_single_worker(args.jobs)
    required_mode = None if args.phase in ("plan", "run") else args.mode
    root, directory = _phase_paths(args.repo_root, args.directory, mode=required_mode)
    if args.phase == "run":
        return run_coordinated(root, directory, args.source_sha, args.expected_version, args.jobs, mode=args.mode)
    if args.phase == "plan":
        _create_plan(root, directory, args.source_sha, args.expected_version, args.mode)
    elif args.phase == "prepare":
        return prepare_environments(root, directory)
    elif args.phase == "generate":
        return generate(root, directory, args.jobs)
    elif args.phase == "candidate":
        _capture_candidate(root, directory)
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
