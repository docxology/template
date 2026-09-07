"""Tests for the coverage measurement subprocess policy and workspace (split from test_counts_doc.py)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.core.pipeline.stages import PIPELINE_STAGE_TIMEOUT_SECONDS
from infrastructure.documentation.counts_doc import (
    COVERAGE_MEASUREMENT_TIMEOUT_SECONDS,
    EXEMPLAR_SNAPSHOT,
    _coverage_measurement_data_file,
)
from infrastructure.documentation.counts_coverage import (
    COVERAGE_MEASUREMENT_POLICY_OVERRIDES,
    _coverage_measurement_command,
    _coverage_measurement_environment,
    _coverage_measurement_process_policy,
    _coverage_measurement_workspace,
    _coverage_report_command,
    _coverage_support_identity,
    _fresh_coverage_measurement_data_file,
)
from infrastructure.reporting.project_verifier import DEFAULT_PROJECT_VERIFIER_TIMEOUT_SECONDS

from tests.infra_tests.documentation._counts_doc_helpers import (
    _coverage_support_file_snapshot,
    _initialize_test_git_repository,
    _regular_file_snapshot,
    _repo_root,
    _write_test_coverage_support_closure,
)


# Several cases create temporary Git trees and exercise subprocess-backed
# provenance discovery. They are bounded, but can exceed the repository's
# 10-second default when the complete coverage suite is under load.
pytestmark = pytest.mark.timeout(30)


def test_coverage_measurement_uses_bounded_release_profile() -> None:
    """Coverage receipts must use the shared release selection and timeout policy."""
    command = _coverage_measurement_command(Path("/tmp/project"))
    marker = command[command.index("-m") + 1]

    assert "not requires_ollama" in marker
    assert "not long_running" in marker
    assert "not bench" in marker
    assert "not private_project" in marker
    assert "not external_fixture" in marker
    assert COVERAGE_MEASUREMENT_TIMEOUT_SECONDS == 1800


def test_active_coverage_measurement_selects_only_the_chunked_verifier() -> None:
    canonical = Path("/repo/projects/templates/template_active_inference")
    disposable = Path("/tmp/coverage/template_active_inference")

    direct = _coverage_measurement_command(canonical)
    isolated = _coverage_measurement_command(disposable, environment_project_dir=canonical)

    expected_tail = [
        "--extra",
        "dev",
        "python",
        "scripts/run_full_verification.py",
        "--coverage-only",
        "--profile",
        "release",
    ]
    assert direct == ["uv", "run", "--locked", "--directory", str(canonical), *expected_tail]
    assert isolated == [
        "uv",
        "run",
        "--locked",
        "--project",
        str(canonical),
        "--directory",
        str(disposable),
        *expected_tail,
    ]

    assert _coverage_report_command(disposable, environment_project_dir=canonical) == [
        "uv",
        "run",
        "--locked",
        "--project",
        str(canonical),
        "--directory",
        str(disposable),
        "--extra",
        "dev",
        "coverage",
        "report",
        "--precision=2",
    ]


def test_coverage_measurement_default_policy_stays_bounded() -> None:
    policy = _coverage_measurement_process_policy("template_code_project")

    assert policy.policy_id == "coverage-measurement"
    assert policy.timeout_seconds == COVERAGE_MEASUREMENT_TIMEOUT_SECONDS == 1800


def test_active_inference_coverage_measurement_has_scoped_ceiling() -> None:
    policy = _coverage_measurement_process_policy("template_active_inference")
    override = COVERAGE_MEASUREMENT_POLICY_OVERRIDES["template_active_inference"]

    assert policy.policy_id == "coverage-measurement-active-inference"
    assert policy.timeout_seconds == override.timeout_seconds == DEFAULT_PROJECT_VERIFIER_TIMEOUT_SECONDS == 6900
    assert policy.timeout_seconds < PIPELINE_STAGE_TIMEOUT_SECONDS == 7200
    assert override.strategy_id == "state-isolated-chunked-coverage"
    assert override.uv_run_args[-2:] == ("--profile", "release")


def test_coverage_timeout_overrides_are_public_and_drive_a_real_subprocess(tmp_path: Path) -> None:
    from infrastructure.core.subprocess_policy import INTENTIONAL_SUBPROCESS_POLICIES, run_with_policy

    public_names = {snapshot.name for snapshot in EXEMPLAR_SNAPSHOT}
    assert set(COVERAGE_MEASUREMENT_POLICY_OVERRIDES) == {"template_active_inference"}
    assert set(COVERAGE_MEASUREMENT_POLICY_OVERRIDES).issubset(public_names)

    policy = _coverage_measurement_process_policy("template_active_inference")
    inventory = {row.policy_id: row for row in INTENTIONAL_SUBPROCESS_POLICIES}
    assert inventory[policy.policy_id] == policy
    result = run_with_policy(
        (sys.executable, "-c", "print('coverage-policy-ok')"),
        cwd=tmp_path,
        env={"PATH": os.environ.get("PATH", "")},
        policy=policy,
    )

    assert result.returncode == 0
    assert result.timed_out is False
    assert result.stdout.strip() == "coverage-policy-ok"


def test_coverage_measurement_data_file_is_absolute_for_relative_checkout() -> None:
    """Coverage cleanup must target the same path the subprocess writes."""
    checkout = Path("relative-checkout")

    data_file = _coverage_measurement_data_file(checkout, "demo")

    assert data_file == checkout.resolve() / "projects" / "templates" / "demo" / ".coverage.measure_demo"
    assert data_file.is_absolute()


def test_coverage_measurement_starts_with_a_fresh_data_file(tmp_path: Path) -> None:
    stale = tmp_path / ".coverage.measure_demo"
    stale.write_bytes(b"stale coverage database")

    data_file = _fresh_coverage_measurement_data_file(tmp_path, "demo")

    assert data_file == stale
    assert not data_file.exists()


def test_coverage_measurement_environment_strips_conflicting_child_opt_ins(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TEMPLATE_ACTIVE_INFERENCE_ALLOW_GATE_REBUILD", "1")
    monkeypatch.setenv("UV_FROZEN", "true")
    monkeypatch.setenv("UV_NO_SYNC", "true")
    monkeypatch.setenv("UV_LOCKED", "true")
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "external.git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(tmp_path / "external-worktree"))
    monkeypatch.setenv("GIT_INDEX_FILE", str(tmp_path / "external.index"))
    monkeypatch.setenv("GIT_OBJECT_DIRECTORY", str(tmp_path / "external-objects"))
    monkeypatch.setenv("GIT_ALTERNATE_OBJECT_DIRECTORIES", str(tmp_path / "external-alternates"))
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    monkeypatch.setenv("GIT_COMMON_DIR", str(tmp_path / "external-common"))
    monkeypatch.setenv("GIT_DISCOVERY_ACROSS_FILESYSTEM", "1")
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.hooksPath")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", str(tmp_path / "external-hooks"))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "external-global-config"))
    monkeypatch.setenv("GIT_TEMPLATE_DIR", str(tmp_path / "external-template"))
    data_file = tmp_path / ".coverage.measure_demo"

    environment = _coverage_measurement_environment(data_file)

    assert "TEMPLATE_ACTIVE_INFERENCE_ALLOW_GATE_REBUILD" not in environment
    assert "UV_FROZEN" not in environment
    assert "UV_NO_SYNC" not in environment
    assert "GIT_DIR" not in environment
    assert "GIT_WORK_TREE" not in environment
    assert "GIT_INDEX_FILE" not in environment
    assert "GIT_OBJECT_DIRECTORY" not in environment
    assert "GIT_ALTERNATE_OBJECT_DIRECTORIES" not in environment
    assert "GIT_CEILING_DIRECTORIES" not in environment
    assert "GIT_COMMON_DIR" not in environment
    assert "GIT_DISCOVERY_ACROSS_FILESYSTEM" not in environment
    assert "GIT_CONFIG_COUNT" not in environment
    assert "GIT_CONFIG_KEY_0" not in environment
    assert "GIT_CONFIG_VALUE_0" not in environment
    assert environment["GIT_CONFIG_GLOBAL"] == os.devnull
    assert environment["GIT_CONFIG_NOSYSTEM"] == "1"
    assert environment["GIT_CONFIG_SYSTEM"] == os.devnull
    assert "GIT_TEMPLATE_DIR" not in environment
    assert environment["UV_LOCKED"] == "true"
    assert environment["COVERAGE_FILE"] == str(data_file)


def test_active_locked_uv_measurement_and_report_probes_ignore_inherited_frozen_mode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy

    monkeypatch.setenv("UV_FROZEN", "true")
    monkeypatch.setenv("UV_NO_SYNC", "true")
    project = _repo_root() / "projects" / "templates" / "template_active_inference"
    environment = _coverage_measurement_environment(tmp_path / ".coverage.measure_probe")
    prefix = (
        "uv",
        "run",
        "--locked",
        "--project",
        str(project),
        "--directory",
        str(tmp_path),
        "--extra",
        "dev",
    )
    commands = (
        (*prefix, "python", "-c", "print('locked-measurement-ok')"),
        (*prefix, "coverage", "--version"),
    )

    results = [
        run_with_policy(
            command,
            cwd=_repo_root(),
            env=environment,
            policy=SubprocessPolicy(
                policy_id=f"coverage-locked-probe-{index}",
                source_path="infrastructure/documentation/counts_coverage.py",
                timeout_seconds=30,
            ),
        )
        for index, command in enumerate(commands)
    ]

    assert all(result.returncode == 0 for result in results)
    assert all(result.timed_out is False for result in results)
    assert all(not result.command_error for result in results)
    assert results[0].stdout.strip() == "locked-measurement-ok"
    assert "Coverage.py" in results[1].stdout


@pytest.mark.parametrize(
    "mode, exit_code, delay, timeout_seconds",
    (("success", 0, 0.0, 2.0), ("failure", 7, 0.0, 2.0), ("timeout", 0, 2.0, 0.5)),
)
def test_active_coverage_workspace_confines_mutation_and_cleans_after_subprocess(
    tmp_path: Path,
    mode: str,
    exit_code: int,
    delay: float,
    timeout_seconds: float,
) -> None:
    from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy

    repo_root = tmp_path / "repo"
    project = repo_root / "projects" / "templates" / "template_active_inference"
    source = project / "src" / "sentinel.py"
    output = project / "output" / "sentinel.json"
    coverage_config = project / ".coveragerc"
    stale_coverage_data = project / ".coverage.measure_stale"
    source.parent.mkdir(parents=True)
    output.parent.mkdir(parents=True)
    source.write_bytes(b"SOURCE-ORIGINAL\n")
    output.write_bytes(b"OUTPUT-ORIGINAL\n")
    coverage_config.write_bytes(b"[run]\nbranch = true\n")
    stale_coverage_data.write_bytes(b"STALE-COVERAGE\n")
    _write_test_coverage_support_closure(repo_root)
    _initialize_test_git_repository(repo_root)
    source_mtime = source.stat().st_mtime_ns
    output_mtime = output.stat().st_mtime_ns
    support_before = _coverage_support_file_snapshot(repo_root)
    worker = (
        "import pathlib,sys,time; "
        "root=pathlib.Path(sys.argv[1]); "
        "repo=root.parents[2]; "
        "(root/'src'/'sentinel.py').unlink(); "
        "(root/'output'/'sentinel.json').write_bytes(b'OUTPUT-MUTATED\\n'); "
        "(root/'output'/'created.json').write_bytes(b'CREATED\\n'); "
        "(repo/'projects'/'AGENTS.md').unlink(); "
        "(repo/'AGENTS.md').write_bytes(b'SUPPORT-MUTATED\\n'); "
        "(repo/'docs'/'RUN_GUIDE.md').write_bytes(b'SUPPORT-MUTATED\\n'); "
        "(repo/'docs'/'created-by-test.md').write_bytes(b'CREATED\\n'); "
        "time.sleep(float(sys.argv[2])); "
        "raise SystemExit(int(sys.argv[3]))"
    )

    with _coverage_measurement_workspace(repo_root, "template_active_inference") as (_, disposable):
        temporary_repository = disposable.parents[2]
        assert disposable.relative_to(temporary_repository) == Path("projects/templates/template_active_inference")
        assert (disposable / ".coveragerc").read_bytes() == b"[run]\nbranch = true\n"
        assert not (disposable / ".coverage.measure_stale").exists()
        result = run_with_policy(
            (sys.executable, "-c", worker, str(disposable), str(delay), str(exit_code)),
            cwd=disposable,
            env={"PATH": os.environ.get("PATH", "")},
            policy=SubprocessPolicy(
                policy_id=f"coverage-copy-{mode}",
                source_path="infrastructure/documentation/counts_coverage.py",
                timeout_seconds=timeout_seconds,
            ),
        )
        assert result.timed_out is (mode == "timeout")
        if mode == "failure":
            assert result.returncode == exit_code
        assert not (temporary_repository / "projects" / "AGENTS.md").exists()
        assert (temporary_repository / "AGENTS.md").read_bytes() == b"SUPPORT-MUTATED\n"
        assert (temporary_repository / "docs" / "created-by-test.md").is_file()
        assert source.read_bytes() == b"SOURCE-ORIGINAL\n"
        assert output.read_bytes() == b"OUTPUT-ORIGINAL\n"
        assert not (project / "output" / "created.json").exists()
        assert _coverage_support_file_snapshot(repo_root) == support_before
        assert not (repo_root / "docs" / "created-by-test.md").exists()

    assert not temporary_repository.exists()
    assert source.stat().st_mtime_ns == source_mtime
    assert output.stat().st_mtime_ns == output_mtime
    assert _coverage_support_file_snapshot(repo_root) == support_before


def test_active_coverage_workspace_has_exact_isolated_git_identity(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    project = repo_root / "projects" / "templates" / "template_active_inference"
    source = project / "src" / "sentinel.py"
    output = project / "output" / "sentinel.json"
    source.parent.mkdir(parents=True)
    output.parent.mkdir(parents=True)
    source.write_bytes(b"SOURCE\n")
    output.write_bytes(b"OUTPUT\n")
    _write_test_coverage_support_closure(repo_root)
    canonical_head = _initialize_test_git_repository(repo_root)
    canonical_git = repo_root / ".git"
    canonical_git_before = _regular_file_snapshot(canonical_git)

    with _coverage_measurement_workspace(repo_root, "template_active_inference") as (_, disposable):
        disposable_repository = disposable.parents[2]
        disposable_head = subprocess.run(
            ["git", "-C", str(disposable), "rev-parse", "--verify", "HEAD^{commit}"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        assert disposable_head == canonical_head
        assert disposable.relative_to(disposable_repository) == Path("projects/templates/template_active_inference")
        disposable_top_level = subprocess.run(
            ["git", "-C", str(disposable), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        assert Path(disposable_top_level).resolve() == disposable_repository.resolve()
        assert _coverage_support_identity(disposable_repository) == _coverage_support_identity(repo_root)
        assert not (disposable / ".git").exists()
        assert (disposable_repository / ".git").is_dir()
        assert (disposable_repository / ".git").resolve() != canonical_git.resolve()
        disposable_git = (disposable_repository / ".git").resolve()
        for git_path_args in (
            ("--git-dir",),
            ("--git-common-dir",),
            ("--git-path", "index"),
            ("--git-path", "index.lock"),
            ("--git-path", "HEAD.lock"),
            ("--git-path", "logs"),
            ("--git-path", "objects"),
            ("--git-path", "packed-refs.lock"),
            ("--git-path", "refs"),
        ):
            raw_path = subprocess.run(
                ["git", "-C", str(disposable), "rev-parse", *git_path_args],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            resolved_path = (disposable / raw_path).resolve(strict=False)
            assert resolved_path == disposable_git or resolved_path.is_relative_to(disposable_git)
        assert (disposable_git / "objects" / "info" / "alternates").read_text(encoding="utf-8").strip() == str(
            (canonical_git / "objects").resolve()
        )
        config = (disposable_git / "config").read_text(encoding="utf-8")
        assert "hooksPath" not in config
        assert "[remote " not in config

        subprocess.run(
            ["git", "-C", str(disposable), "update-ref", "refs/heads/disposable-only", "HEAD"],
            check=True,
        )
        canonical_ref = subprocess.run(
            ["git", "-C", str(repo_root), "show-ref", "--verify", "refs/heads/disposable-only"],
            capture_output=True,
            text=True,
        )
        assert canonical_ref.returncode != 0
        assert source.read_bytes() == b"SOURCE\n"
        assert output.read_bytes() == b"OUTPUT\n"

    assert _regular_file_snapshot(canonical_git) == canonical_git_before
