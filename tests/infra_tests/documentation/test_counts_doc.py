"""Tests for ``infrastructure.documentation.counts_doc``.

Real I/O only (no mocks). The fast derivations (tracked-py count, package list)
run against the live repo tree; the renderer is exercised with a real
``CountsFacts`` value built in-test and against the on-disk ``COUNTS.md``.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import venv
from pathlib import Path

import pytest

from infrastructure.core.pipeline.stages import PIPELINE_STAGE_TIMEOUT_SECONDS
from infrastructure.documentation.counts_doc import (
    COVERAGE_PROVENANCE_RELATIVE_PATH,
    COVERAGE_PROVENANCE_SCHEMA_VERSION,
    COVERAGE_MEASUREMENT_TIMEOUT_SECONDS,
    DOC_RELATIVE_PATH,
    EXEMPLAR_SNAPSHOT,
    CountsFacts,
    _coverage_measurement_data_file,
    _exemplar_collected_count,
    exemplar_source_hash,
    infrastructure_packages,
    render_counts_doc,
    tracked_infra_python_count,
    validate_coverage_provenance,
    write_counts_doc,
)
from infrastructure.documentation.counts_coverage import (
    COVERAGE_MEASUREMENT_POLICY_OVERRIDES,
    COVERAGE_SOURCE_INVENTORY_MODE,
    COVERAGE_SUPPORT_IDENTITY_MODE,
    ExemplarSnapshot,
    _COVERAGE_COPY_SUPPORT_SPECS,
    _coverage_measurement_command,
    _coverage_measurement_environment,
    _coverage_measurement_process_policy,
    _coverage_measurement_workspace,
    _coverage_report_command,
    _coverage_support_identity,
    _coverage_total_from_report,
    _finalize_exemplar_coverage_result,
    _fresh_coverage_measurement_data_file,
    _nul_delimited_git_paths,
    _validated_coverage_report,
    build_coverage_provenance,
)
from infrastructure.project.public_scope import public_project_names
from infrastructure.reporting.project_verifier import DEFAULT_PROJECT_VERIFIER_TIMEOUT_SECONDS


# Several cases create temporary Git trees and exercise subprocess-backed
# provenance discovery. They are bounded, but can exceed the repository's
# 10-second default when the complete coverage suite is under load.
pytestmark = pytest.mark.timeout(30)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _initialize_test_git_repository(repo_root: Path) -> str:
    """Create one committed temporary repository and return its exact HEAD."""
    subprocess.run(["git", "init", "-q", str(repo_root)], check=True)
    subprocess.run(["git", "-C", str(repo_root), "config", "user.name", "Counts Test"], check=True)
    subprocess.run(
        ["git", "-C", str(repo_root), "config", "user.email", "counts@example.invalid"],
        check=True,
    )
    subprocess.run(["git", "-C", str(repo_root), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(repo_root), "-c", "commit.gpgsign=false", "commit", "-qm", "initial"],
        check=True,
    )
    return subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _write_test_coverage_support_closure(repo_root: Path) -> None:
    """Create real synthetic sources for every declared support-closure row."""
    for spec in _COVERAGE_COPY_SUPPORT_SPECS:
        path = repo_root / spec.relative_path
        if spec.kind == "directory":
            path.mkdir(parents=True, exist_ok=True)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {spec.relative_path.as_posix()}\n", encoding="utf-8")


def _regular_file_snapshot(root: Path) -> dict[str, tuple[bytes, int]]:
    """Capture regular-file bytes and mtimes without following symlinks."""
    return {
        path.relative_to(root).as_posix(): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }


def _coverage_support_file_snapshot(repo_root: Path) -> dict[str, tuple[bytes, int]]:
    """Capture the canonical support-file bytes and mtimes."""
    return {
        spec.relative_path.as_posix(): (
            (repo_root / spec.relative_path).read_bytes(),
            (repo_root / spec.relative_path).stat().st_mtime_ns,
        )
        for spec in _COVERAGE_COPY_SUPPORT_SPECS
        if spec.kind == "file"
    }


def test_tracked_infra_python_count_is_positive() -> None:
    """The tracked-py derivation returns the live git-tracked count."""
    count = tracked_infra_python_count(_repo_root())
    assert count > 100  # sanity floor; the tree has hundreds of modules


def test_infrastructure_packages_excludes_private_and_is_sorted() -> None:
    """Package discovery is sorted and skips dunder/underscore dirs."""
    pkgs = infrastructure_packages(_repo_root())
    assert pkgs == sorted(pkgs)
    assert "core" in pkgs
    assert all(not p.startswith("_") for p in pkgs)


def test_render_contains_parseable_markers() -> None:
    """The rendered doc carries the literals the consistency gates parse."""
    facts = CountsFacts(
        public_projects=["template_alpha", "template_beta"],
        packages=["core", "validation"],
        infra_py_count=553,
        project_tests=228,
        publishing_tests=395,
        exemplar_tests={"template_alpha": 7, "template_beta": 11},
    )
    doc = render_counts_doc(facts)

    count_match = re.search(r"Last refreshed count: \*\*(?P<count>\d+)\*\*", doc)
    assert count_match and int(count_match.group("count")) == 553

    collect_match = re.search(
        r"Result: \*\*(?P<project>\d+)\*\* project-scope infrastructure tests collected "
        r"and \*\*(?P<publishing>\d+)\*\* publishing tests collected",
        doc,
    )
    assert collect_match
    assert int(collect_match.group("project")) == 228
    assert int(collect_match.group("publishing")) == 395

    # Roster names round-trip into both roster blocks.
    assert "- `template_alpha`" in doc
    assert "- `template_beta`" in doc
    # Module count flows into the header and the mermaid diagram.
    assert "importable packages" in doc
    assert "(2)" in doc


def test_render_exemplar_table_one_row_per_snapshot() -> None:
    """Every measured snapshot row appears in the rendered table."""
    facts = CountsFacts(
        public_projects=[s.name for s in EXEMPLAR_SNAPSHOT],
        packages=["core"],
        infra_py_count=1,
        project_tests=1,
        publishing_tests=1,
        exemplar_tests={s.name: index for index, s in enumerate(EXEMPLAR_SNAPSHOT, 1)},
    )
    doc = render_counts_doc(facts)
    for index, snap in enumerate(EXEMPLAR_SNAPSHOT, 1):
        assert f"| `{snap.name}` | {index} | {snap.coverage_pct} |" in doc


def test_exemplar_snapshot_covers_public_scope() -> None:
    """The measured snapshot has exactly one row per public exemplar."""
    expected = {name.split("/")[-1] for name in public_project_names(_repo_root())}
    documented = {s.name for s in EXEMPLAR_SNAPSHOT}
    assert documented == expected


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


def test_active_coverage_support_closure_exactly_matches_outward_documentation_links() -> None:
    import runpy

    repo_root = _repo_root()
    project = repo_root / "projects" / "templates" / "template_active_inference"
    contract = runpy.run_path(str(project / "src" / "gates" / "documentation_contract.py"))
    iter_targets = contract["_iter_markdown_targets"]
    split_target = contract["_split_link_target"]
    skip_parts = contract["SKIP_PARTS"]
    outward_targets: list[str] = []
    for path in sorted(project.rglob("*.md")):
        if any(part in skip_parts for part in path.relative_to(project).parts):
            continue
        text = path.read_text(encoding="utf-8")
        for _, raw_target in iter_targets(text):
            target, _ = split_target(raw_target)
            if not target or re.match(r"^[a-z][a-z0-9+.-]*:", target):
                continue
            candidate = (path.parent / target).resolve()
            if candidate.is_relative_to(project):
                continue
            outward_targets.append(candidate.relative_to(repo_root).as_posix())

    expected_targets = [
        "AGENTS.md",
        "docs/RUN_GUIDE.md",
        "docs/_generated/COUNTS.md",
        "docs/_generated/COUNTS.md",
        "docs/guides/manuscript-semantics.md",
        "docs/guides/publishing-guide.md",
        "docs/guides/zenodo-doi-strategy.md",
        "docs/maintenance/archival-targets.md",
        "docs/maintenance/exemplar-backlog-history.md",
        "docs/rules/memory_and_decision_records.md",
        "infrastructure/publishing/README.md",
        "projects/AGENTS.md",
        "projects/AGENTS.md",
        "projects/templates/template_code_project",
    ]
    declared_targets = {spec.relative_path.as_posix() for spec in _COVERAGE_COPY_SUPPORT_SPECS}

    assert sorted(outward_targets) == sorted(expected_targets)
    assert set(outward_targets) == declared_targets


def test_active_coverage_support_identity_binds_contract_bytes_but_not_counts_content(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    project_source = repo_root / "projects" / "templates" / "template_active_inference" / "src" / "demo.py"
    project_source.parent.mkdir(parents=True)
    project_source.write_text("VALUE = 1\n", encoding="utf-8")
    _write_test_coverage_support_closure(repo_root)
    subprocess.run(["git", "init", "-q", str(repo_root)], check=True)

    before_identity = _coverage_support_identity(repo_root)
    before_source_hash = exemplar_source_hash(repo_root, "template_active_inference")
    counts = repo_root / "docs" / "_generated" / "COUNTS.md"
    counts.write_text("generated counts may refresh\n", encoding="utf-8")
    assert _coverage_support_identity(repo_root) == before_identity
    assert exemplar_source_hash(repo_root, "template_active_inference") == before_source_hash

    projects_agents = repo_root / "projects" / "AGENTS.md"
    projects_agents.write_text("# Changed anchor-bearing contract\n", encoding="utf-8")
    assert _coverage_support_identity(repo_root) != before_identity
    assert exemplar_source_hash(repo_root, "template_active_inference") != before_source_hash


def test_active_coverage_support_identity_rejects_missing_or_wrong_type(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _write_test_coverage_support_closure(repo_root)
    counts = repo_root / "docs" / "_generated" / "COUNTS.md"
    counts.unlink()
    with pytest.raises(RuntimeError, match="support path is unavailable"):
        _coverage_support_identity(repo_root)

    counts.write_text("restored\n", encoding="utf-8")
    code_project = repo_root / "projects" / "templates" / "template_code_project"
    code_project.rmdir()
    code_project.write_text("not a directory\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="not a real directory"):
        _coverage_support_identity(repo_root)


def test_active_coverage_workspace_rejects_symlinked_support_without_touching_target(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    project_source = repo_root / "projects" / "templates" / "template_active_inference" / "src" / "demo.py"
    project_source.parent.mkdir(parents=True)
    project_source.write_text("VALUE = 1\n", encoding="utf-8")
    _write_test_coverage_support_closure(repo_root)
    external = tmp_path / "external-agents.md"
    external.write_text("EXTERNAL\n", encoding="utf-8")
    projects_agents = repo_root / "projects" / "AGENTS.md"
    projects_agents.unlink()
    try:
        projects_agents.symlink_to(external)
    except OSError as exc:
        pytest.skip(f"symlink creation is unavailable: {exc}")

    with pytest.raises(RuntimeError, match="support path cannot contain a symlink"):
        with _coverage_measurement_workspace(repo_root, "template_active_inference"):
            pass

    assert external.read_text(encoding="utf-8") == "EXTERNAL\n"


def test_active_coverage_workspace_preserves_canonical_semantic_readiness(tmp_path: Path) -> None:
    from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy

    repo_root = _repo_root()
    canonical = repo_root / "projects" / "templates" / "template_active_inference"
    probe = (
        "import json; "
        "from gates.documentation_contract import check_documentation_contract; "
        "from manuscript.sheaf.semantic import semantic_gluing_issues; "
        "from roadmap_tracks.sheaf_track_validation import validate_sheaf_track_artifacts; "
        "from pathlib import Path; "
        "root=Path.cwd(); "
        "print(json.dumps({'documentation': [issue.format() for issue in check_documentation_contract(root)], "
        "'semantic': semantic_gluing_issues(root), "
        "'sheaf': validate_sheaf_track_artifacts(root)}, sort_keys=True))"
    )

    with _coverage_measurement_workspace(repo_root, "template_active_inference") as (_, disposable):
        result = run_with_policy(
            (
                "uv",
                "run",
                "--locked",
                "--project",
                str(canonical),
                "--directory",
                str(disposable),
                "--extra",
                "dev",
                "python",
                "-c",
                probe,
            ),
            cwd=repo_root,
            env=_coverage_measurement_environment(tmp_path / ".coverage.readiness-probe"),
            policy=SubprocessPolicy(
                policy_id="coverage-copy-readiness-probe",
                source_path="infrastructure/documentation/counts_coverage.py",
                timeout_seconds=30,
            ),
        )

    assert result.returncode == 0, result.stderr
    assert result.timed_out is False
    assert not result.command_error
    assert json.loads(result.stdout.splitlines()[-1]) == {
        "documentation": [],
        "semantic": [],
        "sheaf": [],
    }


def test_active_coverage_workspace_passes_documentation_and_inventory_nodes(tmp_path: Path) -> None:
    from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy

    repo_root = _repo_root()
    canonical = repo_root / "projects" / "templates" / "template_active_inference"
    nodes = (
        "tests/test_documentation_contracts.py::test_rendering_reproducibility_reference_is_signposted",
        "tests/test_documentation_contracts.py::test_documentation_contract_cli",
        "tests/test_method_inventory.py::test_method_inventory_check_command",
    )

    with _coverage_measurement_workspace(repo_root, "template_active_inference") as (_, disposable):
        result = run_with_policy(
            (
                "uv",
                "run",
                "--locked",
                "--project",
                str(canonical),
                "--directory",
                str(disposable),
                "--extra",
                "dev",
                "pytest",
                "-q",
                "--no-cov",
                *nodes,
            ),
            cwd=repo_root,
            env=_coverage_measurement_environment(tmp_path / ".coverage.documentation-probe"),
            policy=SubprocessPolicy(
                policy_id="coverage-copy-documentation-probe",
                source_path="infrastructure/documentation/counts_coverage.py",
                timeout_seconds=30,
            ),
        )

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.timed_out is False
    assert not result.command_error
    assert "3 passed" in result.stdout


def test_active_coverage_workspace_rejects_project_symlink_without_touching_target(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    project = repo_root / "projects" / "templates" / "template_active_inference"
    source = project / "src"
    source.mkdir(parents=True)
    external = tmp_path / "external.txt"
    external.write_bytes(b"EXTERNAL\n")
    try:
        (source / "external-link").symlink_to(external)
    except OSError as exc:
        pytest.skip(f"symlink creation is unavailable: {exc}")

    with pytest.raises(RuntimeError, match="copy refuses symlink"):
        with _coverage_measurement_workspace(repo_root, "template_active_inference"):
            pass

    assert external.read_bytes() == b"EXTERNAL\n"


@pytest.mark.parametrize("symlinked_component", ("projects", "templates", "template_active_inference"))
def test_active_coverage_workspace_rejects_symlinked_path_component_without_touching_target(
    tmp_path: Path,
    symlinked_component: str,
) -> None:
    repo_root = tmp_path / "repo"
    external = tmp_path / f"external-{symlinked_component}"
    project_name = "template_active_inference"
    if symlinked_component == "projects":
        repo_root.mkdir()
        external_project = external / "templates" / project_name
        link = repo_root / "projects"
    elif symlinked_component == "templates":
        (repo_root / "projects").mkdir(parents=True)
        external_project = external / project_name
        link = repo_root / "projects" / "templates"
    else:
        (repo_root / "projects" / "templates").mkdir(parents=True)
        external_project = external
        link = repo_root / "projects" / "templates" / project_name
    sentinel = external_project / "src" / "sentinel.py"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_bytes(b"EXTERNAL-SOURCE\n")
    try:
        link.symlink_to(external, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlink creation is unavailable: {exc}")

    with pytest.raises(RuntimeError, match="path component cannot be a symlink"):
        with _coverage_measurement_workspace(repo_root, project_name):
            pass

    assert sentinel.read_bytes() == b"EXTERNAL-SOURCE\n"


@pytest.mark.parametrize(
    "payload",
    (
        "no total row\n",
        "TOTAL 10 0 nan%\n",
        "TOTAL 10 0 inf%\n",
        "TOTAL 10 0 -0.01%\n",
        "TOTAL 10 0 100.01%\n",
        "TOTAL 10 0 92.63\n",
        "TOTAL 10 0 92.63%\nTOTAL 10 0 92.63%\n",
    ),
)
def test_coverage_total_parser_rejects_missing_or_nonfinite_percentages(payload: str) -> None:
    with pytest.raises(RuntimeError, match="invalid or missing TOTAL"):
        _coverage_total_from_report(payload, "demo")


def test_coverage_report_result_fails_closed_and_accepts_one_finite_total() -> None:
    from infrastructure.core.execution_boundary import BoundedSubprocessResult

    base = {"argv": ("coverage", "report"), "returncode": 0, "timed_out": False}
    assert (
        _validated_coverage_report(
            BoundedSubprocessResult(**base, stdout="Name Stmts Miss Cover\nTOTAL 10 1 92.63%\n"),
            "demo",
        )
        == "92.63 %"
    )
    with pytest.raises(RuntimeError, match="timed out"):
        _validated_coverage_report(BoundedSubprocessResult(**(base | {"timed_out": True})), "demo")
    with pytest.raises(RuntimeError, match="exit 4"):
        _validated_coverage_report(
            BoundedSubprocessResult(**(base | {"returncode": 4}), stderr="bad data"),
            "demo",
        )
    with pytest.raises(RuntimeError, match="cannot execute"):
        _validated_coverage_report(BoundedSubprocessResult(**base, command_error="cannot execute"), "demo")


def test_write_round_trips_supplied_facts(tmp_path: Path) -> None:
    """Writing supplied facts exercises real I/O without 23 subprocesses."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    facts = CountsFacts(
        public_projects=[s.name for s in EXEMPLAR_SNAPSHOT],
        packages=["core"],
        infra_py_count=1,
        project_tests=2,
        publishing_tests=3,
        exemplar_tests={s.name: 1 for s in EXEMPLAR_SNAPSHOT},
    )
    target = tmp_path / "COUNTS.md"
    write_counts_doc(repo_root, out_path=target, facts=facts)
    assert target.read_text(encoding="utf-8") == render_counts_doc(facts)


def test_write_canonical_counts_requires_coverage_provenance(tmp_path: Path) -> None:
    """The canonical writer cannot bypass source-bound coverage provenance."""
    facts = CountsFacts(
        public_projects=[s.name for s in EXEMPLAR_SNAPSHOT],
        packages=["core"],
        infra_py_count=1,
        project_tests=2,
        publishing_tests=3,
        exemplar_tests={s.name: 1 for s in EXEMPLAR_SNAPSHOT},
    )

    with pytest.raises(RuntimeError, match="missing coverage provenance"):
        write_counts_doc(tmp_path, facts=facts)


def test_doc_relative_path_points_at_counts_md() -> None:
    """The generator targets COUNTS.md, not the retired COUNTS.md."""
    assert DOC_RELATIVE_PATH == Path("docs/_generated/COUNTS.md")
    assert COVERAGE_PROVENANCE_RELATIVE_PATH == Path("docs/_generated/coverage_snapshot.json")


def test_exemplar_source_hash_changes_with_source(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "templates" / "demo"
    (project / "src").mkdir(parents=True)
    (project / "tests").mkdir()
    source = project / "src" / "demo.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    before = exemplar_source_hash(tmp_path, "demo")
    source.write_text("VALUE = 2\n", encoding="utf-8")
    assert exemplar_source_hash(tmp_path, "demo") != before


def test_exemplar_source_hash_requires_git_inventory(tmp_path: Path) -> None:
    source = tmp_path / "projects" / "templates" / "demo" / "src" / "demo.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="requires successful Git tracked/nonignored queries"):
        exemplar_source_hash(tmp_path, "demo")


def test_coverage_provenance_ignores_ambient_git_repository_redirection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = tmp_path / "canonical"
    for row in EXEMPLAR_SNAPSHOT:
        source = repo_root / "projects" / "templates" / row.name / "src" / "sentinel.py"
        source.parent.mkdir(parents=True)
        source.write_text(f'PROJECT = "{row.name}"\n', encoding="utf-8")
    _write_test_coverage_support_closure(repo_root)

    shared = repo_root / "shared" / "linked"
    shared.mkdir(parents=True)
    shared_source = shared / "sentinel.py"
    shared_source.write_text("VALUE = 'canonical'\n", encoding="utf-8")
    linked_source = repo_root / "projects" / "templates" / "template_active_inference" / "src" / "shared"
    try:
        linked_source.symlink_to(shared, target_is_directory=True)
    except OSError:
        # Repository/commit redirection remains testable on platforms where
        # creating a directory symlink is not available to this process.
        pass

    canonical_head = _initialize_test_git_repository(repo_root)
    canonical_active_hash = exemplar_source_hash(repo_root, "template_active_inference")

    attacker = tmp_path / "attacker"
    attacker_source = attacker / "attacker.py"
    attacker_source.parent.mkdir(parents=True)
    attacker_source.write_text("VALUE = 'attacker'\n", encoding="utf-8")
    attacker_head = _initialize_test_git_repository(attacker)
    attacker_before = attacker_source.read_bytes()
    excludes = attacker / "ambient-excludes"
    excludes.write_text("projects/\n", encoding="utf-8")

    monkeypatch.setenv("GIT_DIR", str(attacker / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(attacker))
    monkeypatch.setenv("GIT_INDEX_FILE", str(attacker / ".git" / "index"))
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.excludesfile")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", str(excludes))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(attacker / "ambient.gitconfig"))

    payload = build_coverage_provenance(repo_root)

    assert payload["source_commit"] == canonical_head
    assert payload["projects"]["template_active_inference"]["source_hash"] == canonical_active_hash
    assert attacker_source.read_bytes() == attacker_before
    assert (
        subprocess.run(
            ["git", "-C", str(attacker), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            env={key: value for key, value in os.environ.items() if not key.startswith("GIT_")},
        ).stdout.strip()
        == attacker_head
    )


def test_coverage_provenance_fails_closed_when_git_cannot_start(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATH", "")

    with pytest.raises(RuntimeError, match="Git context failed while resolving the coverage provenance source commit"):
        build_coverage_provenance(tmp_path)


def test_exemplar_source_hash_tracks_newline_named_direct_inputs(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "templates" / "demo"
    direct_tracked = project / "src" / "tracked\nsource.py"
    direct_untracked = project / "tests" / "untracked\ntest.py"
    direct_tracked.parent.mkdir(parents=True)
    direct_untracked.parent.mkdir(parents=True)
    direct_tracked.write_text("VALUE = 1\n", encoding="utf-8")
    direct_untracked.write_text("VALUE = 1\n", encoding="utf-8")

    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "--", direct_tracked], cwd=tmp_path, check=True)

    for path in (direct_tracked, direct_untracked):
        before = exemplar_source_hash(tmp_path, "demo")
        path.write_text("VALUE = 2\n", encoding="utf-8")
        assert exemplar_source_hash(tmp_path, "demo") != before


def test_exemplar_source_hash_tracks_newline_named_linked_inputs(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "templates" / "demo"
    (project / "src").mkdir(parents=True)

    shared = tmp_path / "shared" / "source"
    shared.mkdir(parents=True)
    linked_tracked = shared / "tracked\nlinked.py"
    linked_untracked = shared / "untracked\nlinked.py"
    linked_tracked.write_text("VALUE = 1\n", encoding="utf-8")
    linked_untracked.write_text("VALUE = 1\n", encoding="utf-8")
    link = project / "src" / "shared"
    try:
        link.symlink_to(shared, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlink creation is unavailable: {exc}")

    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "add", "--", linked_tracked, link],
        cwd=tmp_path,
        check=True,
    )

    for path in (linked_tracked, linked_untracked):
        before = exemplar_source_hash(tmp_path, "demo")
        path.write_text("VALUE = 2\n", encoding="utf-8")
        assert exemplar_source_hash(tmp_path, "demo") != before


def test_nul_delimited_git_paths_preserve_newlines_and_fail_closed() -> None:
    assert _nul_delimited_git_paths("first\npath\0second path\0", inventory="test") == [
        "first\npath",
        "second path",
    ]
    assert _nul_delimited_git_paths("", inventory="test") == []
    with pytest.raises(RuntimeError, match="non-NUL-terminated"):
        _nul_delimited_git_paths("first\npath", inventory="test")
    with pytest.raises(RuntimeError, match="empty pathname"):
        _nul_delimited_git_paths("first\0\0", inventory="test")


def test_exemplar_source_hash_ignores_untracked_build_metadata(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "templates" / "demo"
    source = project / "src" / "demo.py"
    test_file = project / "tests" / "test_demo.py"
    source.parent.mkdir(parents=True)
    test_file.parent.mkdir()
    source.write_text("VALUE = 1\n", encoding="utf-8")
    test_file.write_text("def test_value():\n    assert True\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "--", source, test_file], cwd=tmp_path, check=True)

    before = exemplar_source_hash(tmp_path, "demo")
    metadata = project / "src" / "demo.egg-info" / "PKG-INFO"
    metadata.parent.mkdir()
    metadata.write_text("platform-specific generated metadata\n", encoding="utf-8")

    assert exemplar_source_hash(tmp_path, "demo") == before


def test_exemplar_source_hash_tracks_untracked_source_before_staging(tmp_path: Path) -> None:
    """A new source file changes provenance before it crosses the staging boundary."""
    project = tmp_path / "projects" / "templates" / "demo"
    source = project / "src" / "demo.py"
    test_file = project / "tests" / "test_demo.py"
    source.parent.mkdir(parents=True)
    test_file.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    test_file.write_text("def test_value():\n    assert True\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "--", source, test_file], cwd=tmp_path, check=True)

    before = exemplar_source_hash(tmp_path, "demo")
    new_source = project / "src" / "new_surface.py"
    new_source.write_text("VALUE = 2\n", encoding="utf-8")

    assert exemplar_source_hash(tmp_path, "demo") != before


@pytest.mark.parametrize(
    "relative_path",
    (
        "pyproject.toml",
        "uv.lock",
        ".coveragerc",
        "conftest.py",
        "scripts/run_full_verification.py",
        "config/settings.yaml",
        "data/fixture.json",
        "manuscript/config.yaml",
    ),
)
def test_exemplar_source_hash_tracks_project_coverage_inputs(tmp_path: Path, relative_path: str) -> None:
    project = tmp_path / "projects" / "templates" / "demo"
    path = project / relative_path
    path.parent.mkdir(parents=True)
    path.write_text("version = 1\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)

    before = exemplar_source_hash(tmp_path, "demo")
    path.write_text("version = 2\n", encoding="utf-8")

    assert exemplar_source_hash(tmp_path, "demo") != before


@pytest.mark.parametrize(
    "relative_path",
    (
        "output/data/result.json",
        "rendered/book.pdf",
        ".pytest_cache/v/cache/nodeids",
        ".coverage.measure_demo",
        ".env",
        ".direnv/python/runtime.py",
        ".pipeline/checkpoint.json",
        ".ipynb_checkpoints/notebook-checkpoint.ipynb",
        "build/generated.py",
        "env/lib/runtime.py",
        "venv/lib/runtime.py",
        "ENV/lib/runtime.py",
        "env.bak/lib/runtime.py",
        "venv.bak/lib/runtime.py",
    ),
)
def test_exemplar_source_hash_ignores_output_and_runtime_cache_changes(tmp_path: Path, relative_path: str) -> None:
    project = tmp_path / "projects" / "templates" / "demo"
    source = project / "src" / "demo.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    path = project / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("version = 1\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)

    before = exemplar_source_hash(tmp_path, "demo")
    path.write_text("version = 2\n", encoding="utf-8")

    assert exemplar_source_hash(tmp_path, "demo") == before


def test_exemplar_source_hash_ignores_untracked_gitignored_project_files(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "templates" / "demo"
    source = project / "src" / "demo.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    ignore = project / ".gitignore"
    ignore.write_text("scratch/\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "--", source, ignore], cwd=tmp_path, check=True)

    before = exemplar_source_hash(tmp_path, "demo")
    ignored = project / "scratch" / "runtime.txt"
    ignored.parent.mkdir()
    ignored.write_text("ephemeral\n", encoding="utf-8")

    assert exemplar_source_hash(tmp_path, "demo") == before


def test_exemplar_source_hash_tracks_linked_shared_source(tmp_path: Path) -> None:
    """Tracked project symlinks include their in-repository target content."""
    project = tmp_path / "projects" / "templates" / "demo"
    shared = tmp_path / "projects" / "templates" / "shared" / "src"
    tests = project / "tests"
    (project / "src").mkdir(parents=True)
    shared.mkdir(parents=True)
    tests.mkdir()
    shared_source = shared / "shared.py"
    shared_source.write_text("VALUE = 1\n", encoding="utf-8")
    shared_output = shared / "output" / "generated.json"
    shared_output.parent.mkdir()
    shared_output.write_text('{"value": 1}\n', encoding="utf-8")
    linked_source = project / "src" / "shared"
    linked_source.symlink_to(shared, target_is_directory=True)
    test_file = tests / "test_demo.py"
    test_file.write_text("def test_value():\n    assert True\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "add", "--", linked_source, shared_source, shared_output, test_file],
        cwd=tmp_path,
        check=True,
    )

    before = exemplar_source_hash(tmp_path, "demo")
    shared_output.write_text('{"value": 2}\n', encoding="utf-8")
    assert exemplar_source_hash(tmp_path, "demo") == before
    shared_source.write_text("VALUE = 2\n", encoding="utf-8")

    assert exemplar_source_hash(tmp_path, "demo") != before


def test_exemplar_source_hash_tracks_confined_file_symlink_target(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "templates" / "demo"
    shared = tmp_path / "projects" / "templates" / "shared" / "src" / "config_loader.py"
    link = project / "src" / "config_loader.py"
    shared.parent.mkdir(parents=True)
    link.parent.mkdir(parents=True)
    shared.write_text("VALUE = 1\n", encoding="utf-8")
    try:
        link.symlink_to(shared)
    except OSError as exc:
        pytest.skip(f"symlink creation is unavailable: {exc}")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "--", shared, link], cwd=tmp_path, check=True)

    before = exemplar_source_hash(tmp_path, "demo")
    shared.write_text("VALUE = 2\n", encoding="utf-8")

    assert exemplar_source_hash(tmp_path, "demo") != before


def test_exemplar_source_hash_rejects_file_symlink_to_internal_output(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "templates" / "demo"
    generated = tmp_path / "projects" / "templates" / "shared" / "output" / "result.json"
    link = project / "src" / "linked_result.json"
    generated.parent.mkdir(parents=True)
    link.parent.mkdir(parents=True)
    generated.write_bytes(b"GENERATED\n")
    try:
        link.symlink_to(generated)
    except OSError as exc:
        pytest.skip(f"symlink creation is unavailable: {exc}")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "--", generated, link], cwd=tmp_path, check=True)

    with pytest.raises(RuntimeError, match="targets an excluded runtime or output path"):
        exemplar_source_hash(tmp_path, "demo")

    assert generated.read_bytes() == b"GENERATED\n"


def test_exemplar_source_hash_rejects_file_symlink_outside_repository(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    project = repo_root / "projects" / "templates" / "demo"
    external = tmp_path / "external.txt"
    link = project / "src" / "external.txt"
    external.write_bytes(b"EXTERNAL\n")
    link.parent.mkdir(parents=True)
    try:
        link.symlink_to(external)
    except OSError as exc:
        pytest.skip(f"symlink creation is unavailable: {exc}")
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    subprocess.run(["git", "add", "--", link], cwd=repo_root, check=True)

    with pytest.raises(RuntimeError, match="escapes the repository"):
        exemplar_source_hash(repo_root, "demo")

    assert external.read_bytes() == b"EXTERNAL\n"


def test_coverage_provenance_rejects_legacy_hash_schema(tmp_path: Path) -> None:
    path = tmp_path / COVERAGE_PROVENANCE_RELATIVE_PATH
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"schema_version": 1, "projects": {}}), encoding="utf-8")

    with pytest.raises(RuntimeError, match="schema mismatch"):
        validate_coverage_provenance(tmp_path)

    assert COVERAGE_PROVENANCE_SCHEMA_VERSION == 5


def test_coverage_provenance_rejects_legacy_source_inventory_mode(tmp_path: Path) -> None:
    path = tmp_path / COVERAGE_PROVENANCE_RELATIVE_PATH
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": COVERAGE_PROVENANCE_SCHEMA_VERSION,
                "source_inventory_mode": "tracked-and-nonignored-working-tree",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="source inventory mode"):
        validate_coverage_provenance(tmp_path)

    assert COVERAGE_SOURCE_INVENTORY_MODE == "tracked-and-nonignored-coverage-inputs-v3"
    assert COVERAGE_SUPPORT_IDENTITY_MODE == "explicit-public-documentation-support-v1"


def test_coverage_provenance_requires_source_tree_identity(tmp_path: Path) -> None:
    path = tmp_path / COVERAGE_PROVENANCE_RELATIVE_PATH
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": COVERAGE_PROVENANCE_SCHEMA_VERSION,
                "source_inventory_mode": COVERAGE_SOURCE_INVENTORY_MODE,
                "projects": {},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="source-tree identity"):
        validate_coverage_provenance(tmp_path)


def test_coverage_provenance_rejects_extra_source_identity_project(tmp_path: Path) -> None:
    path = tmp_path / COVERAGE_PROVENANCE_RELATIVE_PATH
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": COVERAGE_PROVENANCE_SCHEMA_VERSION,
                "source_inventory_mode": COVERAGE_SOURCE_INVENTORY_MODE,
                "source_tree_identity": {
                    "algorithm": "sha256",
                    "inventory_mode": COVERAGE_SOURCE_INVENTORY_MODE,
                    "projects": {"unexpected": "0" * 64},
                },
                "projects": {},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="source-tree identity project roster"):
        validate_coverage_provenance(tmp_path)


def test_coverage_provenance_rejects_missing_measurement_support_identity(tmp_path: Path) -> None:
    _write_test_coverage_support_closure(tmp_path)
    source_hashes = {row.name: "0" * 64 for row in EXEMPLAR_SNAPSHOT}
    projects = {
        row.name: {"coverage_pct": row.coverage_pct, "source_hash": source_hashes[row.name]}
        for row in EXEMPLAR_SNAPSHOT
    }
    path = tmp_path / COVERAGE_PROVENANCE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": COVERAGE_PROVENANCE_SCHEMA_VERSION,
                "source_inventory_mode": COVERAGE_SOURCE_INVENTORY_MODE,
                "source_tree_identity": {
                    "algorithm": "sha256",
                    "inventory_mode": COVERAGE_SOURCE_INVENTORY_MODE,
                    "measurement_support": {},
                    "projects": source_hashes,
                },
                "projects": projects,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="measurement-support identity"):
        validate_coverage_provenance(tmp_path)


@pytest.mark.timeout(300)
def test_exemplar_collection_uses_declared_dev_dependencies() -> None:
    count = _exemplar_collected_count(_repo_root(), "template_literature_meta_analysis")
    assert count > 0


@pytest.mark.timeout(300)
def test_exemplar_collection_injects_runner_when_project_venv_lacks_pytest() -> None:
    count = _exemplar_collected_count(_repo_root(), "template_autoresearch_project")
    assert count > 0


def test_exemplar_collection_ignores_stale_relocated_pytest_wrapper(tmp_path: Path) -> None:
    """Collection uses the resolved interpreter, never an absolute console wrapper."""
    project = tmp_path / "projects" / "templates" / "moved_project"
    tests = project / "tests"
    tests.mkdir(parents=True)
    (tests / "test_moved.py").write_text("def test_moved():\n    assert True\n", encoding="utf-8")

    venv.EnvBuilder(with_pip=False, system_site_packages=True).create(project / ".venv")
    wrapper = project / ".venv" / "bin" / "pytest"
    stale_contents = b"#!/checkout/that/no/longer/exists/.venv/bin/python\n"
    wrapper.write_bytes(stale_contents)
    wrapper.chmod(0o755)

    assert _exemplar_collected_count(tmp_path, "moved_project") == 1
    assert wrapper.read_bytes() == stale_contents


def test_exemplar_snapshot_rewrite_updates_only_named_rows(tmp_path: Path) -> None:
    """`--verify-coverage --write` must rewrite measured rows and leave others alone.

    The recorded percentages were unverifiable until 2026-07-27: provenance only
    checked that the source had not changed since a number was written, never that
    the number was right. Two exemplars were found ~1.4pp and ~0.6pp adrift. This
    guards the rewrite path that now refreshes them from a real measurement.
    """
    from infrastructure.documentation import counts_doc

    module_copy = tmp_path / "counts_doc_copy.py"
    module_copy.write_text(
        'ExemplarSnapshot("template_alpha", "10.00 %"),\n'
        'ExemplarSnapshot("template_beta", "20.00 %"),\n'
        'ExemplarSnapshot("template_gamma", "30.00 %"),\n',
        encoding="utf-8",
    )
    counts_doc._rewrite_exemplar_snapshot({"template_beta": "77.77 %"}, module_copy)

    rewritten = module_copy.read_text(encoding="utf-8")
    assert 'ExemplarSnapshot("template_beta", "77.77 %")' in rewritten
    assert 'ExemplarSnapshot("template_alpha", "10.00 %")' in rewritten
    assert 'ExemplarSnapshot("template_gamma", "30.00 %")' in rewritten


def test_exemplar_snapshot_rewrite_is_a_noop_without_measurements(tmp_path: Path) -> None:
    """An empty measurement map must not blank out the recorded values."""
    from infrastructure.documentation import counts_doc

    module_copy = tmp_path / "counts_doc_copy.py"
    original = 'ExemplarSnapshot("template_alpha", "10.00 %"),\n'
    module_copy.write_text(original, encoding="utf-8")
    counts_doc._rewrite_exemplar_snapshot({}, module_copy)
    assert module_copy.read_text(encoding="utf-8") == original


def test_coverage_refresh_does_not_publish_partial_measurements(tmp_path: Path) -> None:
    """One failed exemplar leaves the complete recorded snapshot untouched."""
    snapshot = (
        ExemplarSnapshot("template_alpha", "10.00 %"),
        ExemplarSnapshot("template_beta", "20.00 %"),
    )
    module_copy = tmp_path / "counts_coverage_copy.py"
    original = 'ExemplarSnapshot("template_alpha", "10.00 %"),\nExemplarSnapshot("template_beta", "20.00 %"),\n'
    module_copy.write_text(original, encoding="utf-8")

    result = _finalize_exemplar_coverage_result(
        {"template_alpha": "77.77 %"},
        ["template_beta: coverage process failed"],
        rewrite=True,
        snapshot=snapshot,
        source_path=module_copy,
    )

    assert not result.all_match
    assert not result.measurement_complete
    assert not result.snapshot_rewritten
    assert result.failed_count == 1
    assert result.measured_count == 1
    assert "EXEMPLAR_SNAPSHOT not rewritten" in result.report
    assert module_copy.read_text(encoding="utf-8") == original


def test_coverage_refresh_publishes_complete_measurement_set(tmp_path: Path) -> None:
    """A complete measurement may replace every drifted recorded value."""
    snapshot = (
        ExemplarSnapshot("template_alpha", "10.00 %"),
        ExemplarSnapshot("template_beta", "20.00 %"),
    )
    module_copy = tmp_path / "counts_coverage_copy.py"
    module_copy.write_text(
        'ExemplarSnapshot("template_alpha", "10.00 %"),\nExemplarSnapshot("template_beta", "20.00 %"),\n',
        encoding="utf-8",
    )

    result = _finalize_exemplar_coverage_result(
        {"template_alpha": "77.77 %", "template_beta": "88.88 %"},
        [],
        rewrite=True,
        snapshot=snapshot,
        source_path=module_copy,
    )

    assert not result.all_match
    assert result.measurement_complete
    assert result.snapshot_rewritten
    assert result.failed_count == 0
    assert result.drifted_count == 2
    rewritten = module_copy.read_text(encoding="utf-8")
    assert 'ExemplarSnapshot("template_alpha", "77.77 %")' in rewritten
    assert 'ExemplarSnapshot("template_beta", "88.88 %")' in rewritten


def test_counts_cli_fails_when_coverage_measurements_are_missing(tmp_path: Path) -> None:
    """The real CLI exits nonzero and writes nothing for an incomplete checkout."""
    repo_root = _repo_root()
    source_script = repo_root / "scripts" / "docgen" / "counts.py"
    copied_script = tmp_path / "scripts" / "docgen" / "counts.py"
    copied_script.parent.mkdir(parents=True)
    copied_script.write_bytes(source_script.read_bytes())
    before = copied_script.read_bytes()
    environment = dict(os.environ)
    existing_pythonpath = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        f"{repo_root}{os.pathsep}{existing_pythonpath}" if existing_pythonpath else str(repo_root)
    )

    run = subprocess.run(
        [sys.executable, str(copied_script), "--verify-coverage", "--write"],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert run.returncode == 1, run.stdout + run.stderr
    assert f"{len(EXEMPLAR_SNAPSHOT)} failed, 0 measured" in run.stdout
    assert "coverage snapshot not refreshed" in run.stdout
    assert not (tmp_path / "docs").exists()
    assert copied_script.read_bytes() == before
