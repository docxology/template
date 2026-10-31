"""One local gate entry point mirrors the hosted CI commands."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from infrastructure.core.testing.local_gate import STAGE_ORDER, main, stage_commands, working_tree_changes  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]


def test_every_stage_builds_commands_with_the_offline_runner() -> None:
    for stage in STAGE_ORDER:
        commands = stage_commands(stage, None)
        assert commands, stage
        for command in commands:
            assert command[:4] == ["uv", "run", "--no-sync", "--offline"], command


def test_file_scoped_stages_follow_the_declared_ci_scope() -> None:
    ruff = stage_commands("format", None)[0]
    assert ruff[:5] == ["uv", "run", "--no-sync", "--offline", "ruff"]
    assert ruff[5] == "format" and ruff[6] == "--check"
    assert "infrastructure" in ruff and "tests" in ruff and "output" not in ruff

    types = stage_commands("types", None)[0]
    assert "scripts/gates/mypy_ratchet.py" in types
    # Type checking stays source-only: the tests tree owns its own import root.
    assert "infrastructure" in types and "tests" not in types


def test_infra_stage_runs_one_job_per_declared_shard_and_contract() -> None:
    working_directory = Path("<tmp>")
    commands = stage_commands("infra", None, working_directory)
    assert len(commands) >= 3
    assert [command[command.index("--shard") + 1] for command in commands] == [
        str(index) for index in range(len(commands))
    ]
    for command in commands:
        assert command[:8] == [
            "uv",
            "run",
            "--no-sync",
            "--offline",
            "python",
            "-m",
            "infrastructure.core.testing.ci_infra",
            "--plan",
        ]
        assert command[command.index("--plan") + 1] == str(working_directory / "functional-selection.json")


def test_changed_scope_runs_only_affected_modules_and_never_implies_full_coverage() -> None:
    changed = ("infrastructure/core/testing/ci_module_durations.py", ".github/workflows/ci.yml")
    assert stage_commands("format", changed) == [
        [
            "uv",
            "run",
            "--no-sync",
            "--offline",
            "ruff",
            "format",
            "--check",
            "infrastructure/core/testing/ci_module_durations.py",
        ]
    ]
    assert stage_commands("lint", changed)[0][-1] == "infrastructure/core/testing/ci_module_durations.py"
    assert stage_commands("types", changed)[0][-1] == "infrastructure/core/testing/ci_module_durations.py"
    # Whole-tree controls are skipped under --changed instead of faking coverage.
    assert [command[-1] for command in stage_commands("gates", changed)] == [
        "scripts/gates/ci_module_durations_check.py",
        "scripts/audit/check_exemplar_configs.py",
        "scripts/audit/check_release_versions.py",
    ]
    assert stage_commands("format", (".github/workflows/ci.yml",)) == []
    assert stage_commands("types", (".github/workflows/ci.yml",)) == []
    assert stage_commands("security", (".github/workflows/ci.yml",)) == []


def test_unit_stage_selects_only_changed_public_projects() -> None:
    changed = ("projects/templates/template_code_project/src/module.py",)
    assert stage_commands("unit", changed) == [
        [
            "uv",
            "run",
            "--no-sync",
            "--offline",
            "python",
            "scripts/pipeline/stage_01_test.py",
            "--project",
            "templates/template_code_project",
        ]
    ]
    assert len(stage_commands("unit", None)) == 1


def test_list_prints_the_plan_without_running(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--list", "format", "infra"]) == 0
    output = capsys.readouterr().out
    assert "# format" in output and "# infra" in output
    assert "ruff format --check" in output
    assert "infrastructure.core.testing.ci_infra" in output


def test_unknown_stage_is_refused(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["nonsense"])
    assert excinfo.value.code == 2
    assert "unknown stage" in capsys.readouterr().err


def test_working_tree_changes_observes_real_files() -> None:
    changed = working_tree_changes(ROOT)
    assert isinstance(changed, tuple)
    assert all((ROOT / name).exists() for name in changed)
    # This file is part of an edited working tree during development, but the
    # helper must never invent paths that do not exist on disk.
    assert all(not name.startswith("/") for name in changed)


def test_changed_guides_use_the_same_complete_documentation_roster_as_prs() -> None:
    from infrastructure.core.testing.ci_contracts import combined_groups
    from infrastructure.core.testing.ci_infra import infrastructure_files, validate_plan
    from infrastructure.core.testing.local_gate import _infra_plan

    plan = _infra_plan(("README.md",))
    assert plan["documentation_only"] is True and plan["full"] is False
    validate_plan(ROOT, plan)
    assert {name for group in combined_groups(plan) for name in group} == set(
        infrastructure_files(ROOT, documentation=True)
    )
    assert plan["contract_modules"]
    assert _infra_plan(None)["documentation_only"] is False
