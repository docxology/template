"""Root-owned integration for Meta's documented Stage-01 project selection."""

from __future__ import annotations

import os
import shlex
import sys
from pathlib import Path

import pytest

from infrastructure.core.execution_boundary import build_bounded_env, run_bounded_subprocess
from infrastructure.core.project_paths import find_repo_root, resolve_project_root
from infrastructure.orchestration.stage_policy import (
    build_stage_01_parser,
    resolve_default_project,
    resolve_test_stage_options,
)


PROJECT_NAME = "templates/template_literature_meta_analysis"
MONOREPO_TEST_COMMAND = (
    "uv run python scripts/pipeline/stage_01_test.py "
    "--project templates/template_literature_meta_analysis --project-only"
)


def test_meta_stage_command_selects_real_qualified_project_without_fallback() -> None:
    """Canonical Root resolvers admit the actual documented project-only policy."""
    root = find_repo_root()
    project = resolve_project_root(root, PROJECT_NAME)
    assert project == (root / "projects" / PROJECT_NAME).resolve()
    assert (project / "src").is_dir() and (project / "tests").is_dir()
    assert (root / "scripts" / "pipeline" / "stage_01_test.py").is_file()
    assert MONOREPO_TEST_COMMAND in (project / "README.md").read_text(encoding="utf-8")
    command = shlex.split(MONOREPO_TEST_COMMAND)
    assert command[:4] == ["uv", "run", "python", "scripts/pipeline/stage_01_test.py"]
    args = build_stage_01_parser().parse_args(command[4:])
    options = resolve_test_stage_options(
        profile=args.profile,
        include_slow=args.include_slow,
        include_long_running=args.include_long_running,
        include_ollama_tests=args.include_ollama_tests,
        include_bench=args.include_bench,
        infra_only=args.infra_only,
        project_only=args.project_only,
        all_projects=args.all_projects,
        public_projects=args.public_projects,
        infra_scope=args.infra_scope,
        quiet=args.quiet,
        strict=not args.non_strict,
        project_workers=args.project_workers,
        parallel=args.parallel,
        receipt_path=args.receipt,
    )
    resolution = resolve_default_project(root, args.project)
    assert resolution.project == PROJECT_NAME
    assert not resolution.fallback_applied and resolution.discovery_error is None
    assert options.project_only and not options.infra_only and not options.all_projects
    assert options.strict


@pytest.mark.timeout(120)
@pytest.mark.parametrize("invocation", ("help", "conflicting-scopes"))
def test_actual_stage_cli_exposes_project_only_and_rejects_conflict(tmp_path: Path, invocation: str) -> None:
    """The real thin entry point parses flags without provisioning or test execution."""
    root = find_repo_root()
    stage = root / "scripts" / "pipeline" / "stage_01_test.py"
    arguments = ["--help"] if invocation == "help" else ["--project", PROJECT_NAME, "--project-only", "--infra-only"]
    env = build_bounded_env(dict(os.environ))
    for name in ("PYTHONPATH", "PYTEST_ADDOPTS", "PYTEST_PLUGINS"):
        env.pop(name, None)
    result = run_bounded_subprocess(
        [sys.executable, "-I", str(stage), *arguments],
        cwd=tmp_path,
        env=env,
        timeout=90,
    )
    diagnostic = result.command_error + result.stdout + result.stderr
    assert not result.timed_out, diagnostic
    assert not result.custody_refused, diagnostic
    expected_exit = 0 if invocation == "help" else 2
    assert result.returncode == result.original_returncode == expected_exit, diagnostic
    if invocation == "help":
        assert "--project-only" in result.stdout and "--all-projects" in result.stdout
    else:
        assert "--infra-only and --project-only cannot be used together" in result.stderr
    assert not (tmp_path / ".venv").exists()
    assert not (tmp_path / "output").exists()
