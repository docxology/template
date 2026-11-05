"""Real Git ownership, original child outcomes and artifact-only workflow controls."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
import sys

import pytest
import yaml

from infrastructure.project.exemplar_config_contract import validate_exemplar_configs
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.publishing.root_release_contract import root_package_version
from infrastructure.publishing.publication_refresh import provider_waves, run_logged
from infrastructure.publishing.publication_refresh_custody import (
    _inventory_plan,
    build_plan,
    check_footprint,
    commit_candidate,
    finish_review,
    git,
    gate_commands,
    write_json,
)
from infrastructure.publishing.release_provider_graph import current_provider_graph

ROOT = Path(__file__).resolve().parents[3]
ACTIVE = "templates/template_active_inference"
META = "templates/template_literature_meta_analysis"
ADVANCED = "templates/template_advanced_literature_review"


def _write(root: Path, path: str, body: str | bytes) -> Path:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(body.encode() if isinstance(body, str) else body)
    return target


def _commit(root: Path) -> str:
    git(root, "add", ".")
    git(
        root,
        "-c",
        "user.name=Publication Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "-qm",
        "Explicit fixture Source DATA",
    )
    return git(root, "rev-parse", "HEAD").decode().strip()


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    root = tmp_path / "owned"
    root.mkdir()
    git(root, "init", "-q")
    git(root, "config", "core.filemode", "true")
    _write(root, ".gitignore", "/output/\n")
    _write(root, "README.md", "Authored numbered sections remain Source.\n")
    _write(root, "pyproject.toml", '[project]\nname="research-project-template"\nversion="5.1.0"\n')
    for scope in PUBLIC_PROJECT_NAMES:
        prefix = f"projects/{scope}/"
        package = Path(scope).name.replace("_", "-")
        metadata = (
            f'[project]\nname="{package}"\nversion="0.2.0"\n'
            'dependencies=["research-project-template==5.1.0"]\n'
            '[tool.template]\nplatform_version="5.1.0"\n'
            '[tool.uv.sources]\nresearch-project-template={path="../../..",editable=true}\n'
        )
        if scope == ADVANCED:
            metadata += (
                'template-literature-meta-analysis={path="../template_literature_meta_analysis",editable=true}\n'
            )
        _write(root, prefix + "pyproject.toml", metadata)
        _write(root, prefix + "manuscript/config.yaml", 'publication:\n  platform_version: "5.1.0"\n')
        _write(root, prefix + "manuscript/01_authored.md", "# Authored\n")
        _write(root, prefix + "output/reports/validation_report.json", '{"fixture":true}\n')
        if scope in (ACTIVE, META):
            _write(root, prefix + "output/manuscript/config.yaml", 'publication:\n  platform_version: "5.0.2"\n')
    prefix = f"projects/{ACTIVE}/"
    for source in ("src/manuscript/sheaf/compose.py", "src/manuscript/compilation_io.py"):
        _write(root, prefix + source, (ROOT / prefix / source).read_bytes())
    _write(root, prefix + "manuscript/sections/fragment.md", "# Authored fragment\n")
    _write(root, prefix + "manuscript/02_compiled.md", "# Derived\n")
    _write(
        root,
        prefix + "manuscript/sheaf/manifest.yaml",
        "schema_version: 2\nsections:\n- id: compiled\n  output_name: 02_compiled.md\n"
        "  tracks:\n    prose: manuscript/sections/fragment.md\n",
    )
    _commit(root)
    return root


def _plan(root: Path) -> dict:
    return build_plan(root, git(root, "rev-parse", "HEAD").decode().strip(), "5.1.0")


def test_current_provider_graph_and_publication_copies_derive_from_source(repository: Path) -> None:
    plan = _plan(repository)
    assert plan["refresh"] == [scope for scope in PUBLIC_PROJECT_NAMES if scope in (ACTIVE, META)]
    assert set(plan["rebind"]) == set(PUBLIC_PROJECT_NAMES) - {ACTIVE, META}
    waves = provider_waves(current_provider_graph(repository))
    assert next(i for i, row in enumerate(waves) if META in row) < next(
        i for i, row in enumerate(waves) if ADVANCED in row
    )
    assert f"projects/{ACTIVE}/manuscript/02_compiled.md" in plan["allowed"]
    assert f"projects/{ACTIVE}/manuscript/01_authored.md" not in plan["allowed"]
    assert all(row["mode"] == "100644" for row in plan["allowed"].values())


@pytest.mark.parametrize("change", ["authored", "config", "untracked", "removed", "symlink", "mode", "forged-plan"])
def test_actual_unowned_or_incomplete_footprints_refuse(repository: Path, tmp_path: Path, change: str) -> None:
    plan = _plan(repository)
    output = repository / f"projects/{ACTIVE}/output/reports/validation_report.json"
    if change == "authored":
        (repository / f"projects/{ACTIVE}/manuscript/01_authored.md").write_text("# Changed authored\n")
    elif change == "config":
        (repository / f"projects/{ACTIVE}/manuscript/config.yaml").write_text(
            'publication:\n  platform_version: "5.1.0"\n# Edit\n'
        )
    elif change == "untracked":
        _write(repository, f"projects/{ACTIVE}/output/new-untracked.txt", "not retained")
    elif change == "removed":
        output.unlink()
    elif change == "symlink":
        external = tmp_path / "external.txt"
        external.write_text("outside")
        output.unlink()
        output.symlink_to(external)
    elif change == "mode":
        output.chmod(0o755)
    else:
        plan["allowed"]["README.md"] = {"mode": "100644", "kind": "blob", "blob": "0" * 40}
        (repository / "README.md").write_text("Cannot grant this path by editing operator DATA.\n")
    with pytest.raises((ValueError, OSError)):
        check_footprint(repository, plan)


def test_refuses_stale_sha_or_version_before_generation(repository: Path) -> None:
    sha = git(repository, "rev-parse", "HEAD").decode().strip()
    with pytest.raises(ValueError, match="exact"):
        build_plan(repository, "0" * 40, "5.1.0")
    with pytest.raises(ValueError, match="version"):
        build_plan(repository, sha, "5.2.0")


def test_manifest_requires_tracked_real_compiler_and_fragments(repository: Path) -> None:
    target = repository / f"projects/{ACTIVE}/src/manuscript/compilation_io.py"
    git(repository, "rm", "--", str(target))
    _commit(repository)
    with pytest.raises(ValueError, match="producer"):
        _plan(repository)


def test_declared_provider_escape_and_cycle_refuse(repository: Path) -> None:
    target = repository / f"projects/{ADVANCED}/pyproject.toml"
    original = target.read_text()
    target.write_text(original.replace("../template_literature_meta_analysis", "../../../../outside"))
    with pytest.raises(ValueError, match="outside"):
        current_provider_graph(repository)
    target.write_text(original)
    target = repository / f"projects/{META}/pyproject.toml"
    target.write_text(
        target.read_text() + 'template-advanced-literature-review={path="../template_advanced_literature_review"}\n'
    )
    with pytest.raises(ValueError, match="cycle"):
        current_provider_graph(repository)


def test_actual_candidate_commit_preserves_base_and_only_declared_generated_paths(
    repository: Path, tmp_path: Path
) -> None:
    directory = tmp_path / "operator"
    directory.mkdir()
    plan = _plan(repository)
    write_json(directory / "plan.json", plan)
    output = f"projects/{ACTIVE}/output/reports/validation_report.json"
    compiled = f"projects/{ACTIVE}/manuscript/02_compiled.md"
    _write(repository, output, b"\0genuine new binary fixture bytes")
    _write(repository, compiled, "# Updated compiled DATA\n")
    result = commit_candidate(repository, directory)
    assert git(repository, "rev-parse", "HEAD^").decode().strip() == plan["base_commit"]
    assert git(repository, "rev-parse", plan["base_commit"]).decode().strip() == plan["base_commit"]
    assert set(git(repository, "diff", "--name-only", plan["base_commit"], "HEAD").decode().splitlines()) == {
        output,
        compiled,
    }
    assert git(repository, "rev-parse", "HEAD^{tree}").decode().strip() == result["tree"]
    assert b"GIT binary patch" in git(repository, "diff", "--binary", plan["base_commit"], "HEAD")
    with pytest.raises(FileNotFoundError):
        finish_review(repository, directory)
    assert not (directory / "review").exists()


def _assert_observed_custody(receipt: dict, original: int) -> None:
    assert receipt["original_exit_code"] == original
    process = receipt["process"]
    cleanup = process["cleanup"]
    error = cleanup.get("final_census_error")
    actual_restriction = (
        sys.platform == "darwin"
        and isinstance(error, dict)
        and error.get("type") == "PermissionError"
        and error.get("errno") == 1
        and cleanup.get("final_census_succeeded") is False
        and any(
            "/bin/ps" in str(row) and "Operation not permitted" in str(row) for row in cleanup.get("diagnostics", [])
        )
    )
    assert cleanup["root_reaped"] is True and cleanup["guardian_finished"] is True
    if actual_restriction:
        assert process["accepted"] is False and cleanup["verified"] is False
        assert receipt["returncode"] == (original if original else 1)
        assert receipt["returncode"] != 0
    else:
        assert process["accepted"] is True and cleanup["verified"] is True
        assert receipt["returncode"] == original


@pytest.mark.parametrize("code", [0, 19])
def test_original_binary_streams_and_child_exit_are_preserved(repository: Path, tmp_path: Path, code: int) -> None:
    directory = tmp_path / "operator"
    directory.mkdir()
    argv = [
        sys.executable,
        "-I",
        "-B",
        "-c",
        f"import os;os.write(1,b'original\\x00\\xff');os.write(2,b'error\\xfe');raise SystemExit({code})",
    ]
    result = run_logged(repository, directory, "actual-child", argv, timeout=30)
    receipt = json.loads((directory / "diagnostics/actual-child.exit.json").read_bytes())
    assert result == receipt["returncode"]
    _assert_observed_custody(receipt, code)
    assert (directory / "diagnostics/actual-child.stdout").read_bytes() == b"original\0\xff"
    assert (directory / "diagnostics/actual-child.stderr").read_bytes() == b"error\xfe"


def test_arbitrary_real_zero_exits_cannot_replace_the_two_publication_gates(repository: Path, tmp_path: Path) -> None:
    directory = tmp_path / "operator"
    directory.mkdir()
    write_json(directory / "plan.json", _plan(repository))
    commit_candidate(repository, directory)
    for label in ("exemplar-config", "publication-gate", "rendered-audit"):
        result = run_logged(
            repository, directory, label, [sys.executable, "-I", "-B", "-c", "raise SystemExit(0)"], timeout=30
        )
        receipt = json.loads((directory / "diagnostics" / f"{label}.exit.json").read_bytes())
        assert result == receipt["returncode"]
        _assert_observed_custody(receipt, 0)
    with pytest.raises(ValueError, match="both original gates"):
        finish_review(repository, directory)
    assert not (directory / "review").exists()


def test_manual_workflow_has_no_write_credential_and_requires_both_original_gates() -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/publication-refresh.yml").read_text())
    trigger = workflow.get("on", workflow.get(True))
    assert set(trigger) == {"workflow_dispatch"}
    assert workflow["permissions"] == {"contents": "read"}
    job = workflow["jobs"]["refresh"]
    assert job["permissions"] == {"contents": "read"}
    steps = job["steps"]
    checkout = next(row for row in steps if row.get("uses", "").startswith("actions/checkout@"))
    assert checkout["with"]["persist-credentials"] is False
    assert any(row.get("uses") == "./.github/actions/setup-native-installed-readiness" for row in steps)
    upload = next(row for row in steps if row.get("name", "").startswith("Retain the verified patch"))
    assert "steps.verify.outcome == 'success'" in upload["if"] and "steps.capture.outcome == 'success'" in upload["if"]
    assert not any("push" in row.get("run", "") for row in steps)


def test_real_atomic_0600_publication_output_retains_git_100644(repository: Path) -> None:
    plan = _plan(repository)
    relative = f"projects/{ACTIVE}/output/reports/validation_report.json"
    target = repository / relative
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
        stream.write(b'{"fixture":true,"updated":true}\\n')
        temporary = Path(stream.name)
    assert temporary.stat().st_mode & 0o777 == 0o600
    os.replace(temporary, target)
    assert git(repository, "ls-files", "-s", "--", relative).split(b" ", 1)[0] == b"100644"
    assert check_footprint(repository, plan) == [relative]


def test_real_config_validator_refuses_stale_copy_then_accepts_exact_source_copy(repository: Path) -> None:
    before = validate_exemplar_configs(repository, projects=(ACTIVE,))
    assert not before.passed
    assert any("output/manuscript/config.yaml" in finding.detail for finding in before.findings)
    base = repository / "projects" / ACTIVE
    (base / "output/manuscript/config.yaml").write_bytes((base / "manuscript/config.yaml").read_bytes())
    assert validate_exemplar_configs(repository, projects=(ACTIVE,)).passed


def test_real_source_inventory_and_mandatory_config_guard(tmp_path: Path) -> None:
    sha = git(ROOT, "rev-parse", "HEAD").decode().strip()
    plan = _inventory_plan(ROOT, sha, root_package_version(ROOT))
    expected = [
        scope for scope in PUBLIC_PROJECT_NAMES if f"projects/{scope}/output/manuscript/config.yaml" in plan["allowed"]
    ]
    assert plan["refresh"] == expected
    assert set(plan["rebind"]) == set(PUBLIC_PROJECT_NAMES) - set(expected)
    assert f"projects/{ACTIVE}/manuscript/00_abstract.md" not in plan["allowed"]
    commands = gate_commands(ROOT, tmp_path)
    assert set(commands) == {"exemplar-config", "publication-gate", "rendered-audit"}
    assert commands["exemplar-config"][1:] == ["scripts/audit/check_exemplar_configs.py"]
