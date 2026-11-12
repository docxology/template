"""Real Git ownership, original child outcomes and artifact-only workflow controls."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
import sys

import pytest
import yaml

from infrastructure.project.exemplar_config_contract import validate_exemplar_configs
from infrastructure.core.testing.pytest_marker_exprs import repository_marker_expression
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.publishing.root_release_contract import root_package_version
from infrastructure.publishing.publication_refresh import (
    _generation_sequence,
    generate,
    main,
    provider_waves,
    run_coordinated,
    run_logged,
)
from infrastructure.validation.publication.rendered_refresh import rebind_project
from infrastructure.validation.publication.rendered_provenance import write_rendered_provenance_receipt
from infrastructure.core.pipeline.artifacts import snapshot_current_artifact_manifest
from tests.infra_tests.validation._rendered_provenance_helpers import (
    PROJECT,
    _green_project,
    _write_green_validation_report,
)
from infrastructure.publishing.publication_refresh_custody import (
    DEPENDENT_ANALYSIS_SCOPE,
    _DEPENDENT_INPUTS,
    _DEPENDENT_PRODUCERS,
    _inventory_plan,
    build_plan,
    check_footprint,
    commit_candidate,
    finish_review,
    git,
    write_json,
)
from infrastructure.publishing.release_provider_graph import current_provider_graph
from infrastructure.publishing._publication_refresh_protocol import successful_command_receipt

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
        names = sorted({part.removeprefix("not ") for part in repository_marker_expression().split(" and ")})
        metadata = metadata.replace(
            "[tool.uv.sources]\n",
            "[tool.pytest.ini_options]\nmarkers="
            + json.dumps([name + ": canonical profile" for name in names])
            + "\n[tool.uv.sources]\n",
            1,
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
    # Real current producer/input bytes are fixture Source, never a substitute
    # for executing the canonical analysis in a hosted publication run.
    for relative in (*_DEPENDENT_INPUTS, *_DEPENDENT_PRODUCERS):
        if not (root / relative).exists():
            _write(root, relative, (ROOT / relative).read_bytes())
    _commit(root)
    return root


def _plan(root: Path) -> dict:
    return build_plan(root, git(root, "rev-parse", "HEAD").decode().strip(), "5.1.0")


def test_provider_order_and_generated_ownership_preserve_authored_sources(repository: Path) -> None:
    plan = _plan(repository)
    waves = provider_waves(current_provider_graph(repository))
    assert next(i for i, row in enumerate(waves) if META in row) < next(
        i for i, row in enumerate(waves) if ADVANCED in row
    )
    assert f"projects/{ACTIVE}/manuscript/02_compiled.md" in plan["allowed"]
    assert f"projects/{ACTIVE}/manuscript/01_authored.md" not in plan["allowed"]
    assert all(row["mode"] == "100644" for row in plan["allowed"].values())


def test_refresh_does_not_treat_missing_publication_copy_as_unchanged_output(repository: Path) -> None:
    publication = f"projects/{ADVANCED}/output/web/index.html"
    _write(repository, publication, "<!doctype html><h1>Retained engineering publication</h1>\n")
    _commit(repository)
    assert not (repository / f"projects/{ADVANCED}/output/manuscript/config.yaml").exists()

    plan = _plan(repository)

    assert ADVANCED in plan["refresh"] and ADVANCED not in plan["rebind"]
    assert publication in plan["allowed"]


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


@pytest.mark.parametrize("mode", ["refresh", "rebind-only"])
def test_actual_manifested_asset_replacement_retains_exact_candidate_custody(
    repository: Path, tmp_path: Path, mode: str
) -> None:
    prefix = f"projects/{ACTIVE}/output/"
    old = prefix + "figures/retired.svg"
    new = prefix + "figures/current.svg"
    old_bytes = b'<svg xmlns="http://www.w3.org/2000/svg"><title>Retired result</title></svg>\n'
    new_bytes = b'<svg xmlns="http://www.w3.org/2000/svg"><title>Current result</title></svg>\n'
    _write(repository, old, old_bytes)
    snapshot_current_artifact_manifest(repository / prefix)
    base = _commit(repository)
    plan = build_plan(repository, base, "5.1.0", mode=mode)
    (repository / old).unlink()
    _write(repository, new, new_bytes)
    snapshot_current_artifact_manifest(repository / prefix)
    if mode == "rebind-only":
        with pytest.raises((ValueError, OSError)):
            check_footprint(repository, plan)
        assert git(repository, "rev-parse", "HEAD").decode().strip() == base
        assert git(repository, "diff", "--cached", "--name-only") == b""
        return
    manifest = prefix + "reports/artifact_manifest.json"
    assert set(check_footprint(repository, plan)) == {old, new, manifest}
    directory = tmp_path / "asset-operator"
    directory.mkdir()
    write_json(directory / "plan.json", plan)
    candidate = commit_candidate(repository, directory)
    assert git(repository, "rev-parse", "HEAD^").decode().strip() == base
    assert git(repository, "rev-parse", "HEAD^{tree}").decode().strip() == candidate["tree"]
    assert set(git(repository, "diff", "--no-renames", "--name-status", base, "HEAD").decode().splitlines()) == {
        "D\t" + old,
        "A\t" + new,
        "M\t" + manifest,
    }
    assert git(repository, "show", base + ":" + old) == old_bytes
    assert git(repository, "show", "HEAD:" + new) == new_bytes
    assert git(repository, "ls-tree", "HEAD", "--", old) == b""
    assert git(repository, "status", "--porcelain", "--untracked-files=all") == b""


@pytest.mark.parametrize("tamper", ["changed-bytes", "symlink", "executable"])
def test_actual_manifested_addition_refuses_changed_bytes_links_and_modes(
    repository: Path, tmp_path: Path, tamper: str
) -> None:
    prefix = f"projects/{ACTIVE}/output/"
    _write(repository, prefix + "figures/retained.svg", "<svg/>\n")
    snapshot_current_artifact_manifest(repository / prefix)
    base = _commit(repository)
    plan = build_plan(repository, base, "5.1.0")
    target = _write(repository, prefix + "figures/current.svg", "<svg><title>Current result</title></svg>\n")
    snapshot_current_artifact_manifest(repository / prefix)
    if tamper == "changed-bytes":
        target.write_text("<svg><title>Unattested result</title></svg>\n")
    elif tamper == "symlink":
        external = tmp_path / "external.svg"
        external.write_bytes(target.read_bytes())
        target.unlink()
        target.symlink_to(external)
    else:
        target.chmod(0o755)
    with pytest.raises((ValueError, OSError)):
        check_footprint(repository, plan)
    assert git(repository, "rev-parse", "HEAD").decode().strip() == base
    assert git(repository, "diff", "--cached", "--name-only") == b""


def _assert_observed_custody(receipt: dict, original: int) -> None:
    from infrastructure.project.public_acceptance_auxiliary_validation import _supervision_diagnostic

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
        assert process["accepted"] is True and cleanup["verified"] is True, _supervision_diagnostic(process)
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


@pytest.mark.parametrize("original_exit", [False, 0.0])
def test_stored_receipt_rejects_json_boolean_or_float_original_success(
    tmp_path: Path, original_exit: bool | float
) -> None:
    diagnostics = tmp_path / "diagnostics"
    diagnostics.mkdir()
    argv = ["publication-producer"]
    source = "1" * 40
    receipt = {
        "argv": argv,
        "source_commit": source,
        "returncode": 0,
        "original_exit_code": 0,
        "process": {"accepted": True},
    }
    for stream, body in {"stdout": b"retained\0original\xff", "stderr": b""}.items():
        (diagnostics / f"typed-exit.{stream}").write_bytes(body)
        receipt[stream + "_sha256"] = hashlib.sha256(body).hexdigest()
    target = diagnostics / "typed-exit.exit.json"
    write_json(target, receipt)
    assert successful_command_receipt(tmp_path, "typed-exit", argv, source)

    receipt["original_exit_code"] = original_exit
    target.write_text(json.dumps(receipt, sort_keys=True) + "\n", encoding="utf-8")

    assert not successful_command_receipt(tmp_path, "typed-exit", argv, source)


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
    with pytest.raises(ValueError):
        finish_review(repository, directory)
    assert not (directory / "review").exists()


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


def test_actual_source_inventory_excludes_authored_manuscripts() -> None:
    sha = git(ROOT, "rev-parse", "HEAD").decode().strip()
    plan = _inventory_plan(ROOT, sha, root_package_version(ROOT))
    assert f"projects/{ACTIVE}/manuscript/00_abstract.md" not in plan["allowed"]


def test_rebind_only_ownership_excludes_analysis_and_compiled_manuscripts(repository: Path) -> None:
    sha = git(repository, "rev-parse", "HEAD").decode().strip()
    plan = build_plan(repository, sha, "5.1.0", mode="rebind-only")
    assert plan["mode"] == "rebind-only"
    assert plan["refresh"] == [] and plan["rebind"] == list(PUBLIC_PROJECT_NAMES)
    assert plan["compiled_manuscripts"] == []
    assert plan["dependent_analysis"] == {}
    assert all(Path(path).parent.name == "reports" and Path(path).suffix == ".json" for path in plan["allowed"])


@pytest.mark.parametrize(
    "relative",
    [
        f"projects/{ACTIVE}/output/figures/result.svg",
        f"projects/{ACTIVE}/manuscript/02_compiled.md",
        f"projects/{ACTIVE}/output/reports/nested/report.json",
    ],
)
def test_rebind_only_refuses_actual_tracked_figure_compiled_or_nested_report_changes(
    repository: Path, relative: str
) -> None:
    target = repository / relative
    if not target.exists():
        _write(repository, relative, "original fixture DATA\n")
        _commit(repository)
    sha = git(repository, "rev-parse", "HEAD").decode().strip()
    plan = build_plan(repository, sha, "5.1.0", mode="rebind-only")
    target.write_bytes(target.read_bytes() + b"changed DATA\n")
    with pytest.raises(ValueError, match="outside declared generated ownership"):
        check_footprint(repository, plan)


def test_rebind_only_accepts_only_existing_flat_report_updates(repository: Path) -> None:
    sha = git(repository, "rev-parse", "HEAD").decode().strip()
    plan = build_plan(repository, sha, "5.1.0", mode="rebind-only")
    relative = f"projects/{ACTIVE}/output/reports/validation_report.json"
    _write(repository, relative, '{"fixture":"new validation"}\n')
    assert check_footprint(repository, plan) == [relative]


def test_rebind_only_mode_tamper_refuses_reconstruction_and_dispatched_phase(repository: Path, tmp_path: Path) -> None:
    sha = git(repository, "rev-parse", "HEAD").decode().strip()
    plan = build_plan(repository, sha, "5.1.0", mode="rebind-only")
    plan["mode"] = "refresh"
    with pytest.raises(ValueError, match="differs"):
        check_footprint(repository, plan)
    directory = tmp_path / "mode-operator"
    directory.mkdir()
    write_json(directory / "plan.json", build_plan(repository, sha, "5.1.0"))
    with pytest.raises(ValueError, match="dispatched mode"):
        main(["--repo-root", str(repository), "--directory", str(directory), "--mode", "rebind-only", "candidate"])
    assert git(repository, "rev-parse", "HEAD").decode().strip() == sha
    assert not (directory / "candidate.json").exists()


def test_actual_rebind_refuses_changed_output_fingerprint_without_restamping(tmp_path: Path) -> None:
    project = _green_project(tmp_path)
    write_rendered_provenance_receipt(tmp_path, PROJECT)
    receipt = project / "output/reports/rendered_provenance.json"
    before = receipt.read_bytes()
    (project / "output/data/result.json").write_text('{"count":8}\n')
    snapshot_current_artifact_manifest(project / "output")
    passed, message = rebind_project(PROJECT, tmp_path)
    assert passed is False and "rendered bytes changed" in message
    assert receipt.read_bytes() == before


@pytest.mark.parametrize("version", ["5.0.2", "5.1.0"])
def test_dependent_pitch_analysis_plan_is_exact_source_bound_at_either_root_version(
    repository: Path, version: str
) -> None:
    if version != "5.1.0":
        for relative in (
            "pyproject.toml",
            "infrastructure/__init__.py",
            *["projects/" + scope + "/pyproject.toml" for scope in PUBLIC_PROJECT_NAMES],
            *["projects/" + scope + "/manuscript/config.yaml" for scope in PUBLIC_PROJECT_NAMES],
        ):
            path = repository / relative
            path.write_text(path.read_text().replace("5.1.0", version))
        _commit(repository)
    base = git(repository, "rev-parse", "HEAD").decode().strip()
    plan = build_plan(repository, base, version)
    assert plan["platform_version"] == version
    assert set(plan["dependent_analysis"]) == {DEPENDENT_ANALYSIS_SCOPE}
    assert plan["publication_copies"] == [scope for scope in PUBLIC_PROJECT_NAMES if scope in (ACTIVE, META)]
    bound = plan["dependent_analysis"][DEPENDENT_ANALYSIS_SCOPE]
    for row in [*bound["inputs"], *bound["producers"], *bound["analysis_scripts"]]:
        import hashlib

        assert row["sha256"] == hashlib.sha256((repository / row["path"]).read_bytes()).hexdigest()
        assert row["bytes"] == (repository / row["path"]).stat().st_size
    (repository / _DEPENDENT_INPUTS[0]).write_bytes(b"changed actual counts DATA")
    with pytest.raises(ValueError, match="differs"):
        check_footprint(repository, plan)


@pytest.mark.parametrize("subject", ["private_subject", "../template_template", "root"])
def test_dependent_analysis_refuses_private_or_unknown_subjects(repository: Path, subject: str) -> None:
    config = repository / ("projects/" + DEPENDENT_ANALYSIS_SCOPE + "/manuscript/config.yaml")
    value = yaml.safe_load(config.read_text())
    value["project_config"] = {"deck": {"pitch_subject": subject}}
    config.write_text(yaml.safe_dump(value))
    _commit(repository)
    with pytest.raises(ValueError, match="canonical public"):
        _plan(repository)


@pytest.mark.parametrize("target", [_DEPENDENT_PRODUCERS[0], _DEPENDENT_PRODUCERS[1], _DEPENDENT_INPUTS[0]])
def test_dependent_analysis_refuses_missing_tracked_producer_or_input(repository: Path, target: str) -> None:
    git(repository, "rm", "--", target)
    _commit(repository)
    with pytest.raises(ValueError, match="tracked Source"):
        _plan(repository)


@pytest.mark.parametrize("first_exit", [0, 19])
def test_actual_per_project_sequence_preserves_order_and_stops_after_first_refusal(
    repository: Path, tmp_path: Path, first_exit: int
) -> None:
    directory = tmp_path / "sequence"
    directory.mkdir()
    trace = tmp_path / "actual-order.txt"
    first = [
        sys.executable,
        "-I",
        "-B",
        "-c",
        r"import sys;from pathlib import Path;p=Path(sys.argv[1]);p.write_text('analysis\n');raise SystemExit(int(sys.argv[2]))",
        str(trace),
        str(first_exit),
    ]
    second = [
        sys.executable,
        "-I",
        "-B",
        "-c",
        r"import sys;from pathlib import Path;p=Path(sys.argv[1]);assert p.read_text()=='analysis\n';p.write_text(p.read_text()+'refresh\n')",
        str(trace),
    ]
    code = _generation_sequence(repository, directory, [("observed-analysis", first), ("observed-refresh", second)])
    original = json.loads((directory / "diagnostics/observed-analysis.exit.json").read_text())
    _assert_observed_custody(original, first_exit)
    assert trace.read_text().startswith("analysis\n")
    if original["returncode"]:
        assert code == original["returncode"]
        assert trace.read_text() == "analysis\n"
        assert not (directory / "diagnostics/observed-refresh.exit.json").exists()
    else:
        assert code == 0 and trace.read_text() == "analysis\nrefresh\n"
        _assert_observed_custody(json.loads((directory / "diagnostics/observed-refresh.exit.json").read_text()), 0)


def test_actual_pitch_counts_reader_can_change_while_old_rendered_output_fingerprint_stays_unchanged(
    tmp_path: Path,
) -> None:
    # Exercise the actual pure Pitch reader and the actual framework rebind
    # predicate. This fixture grants no native/publication acceptance.
    import importlib.util
    from infrastructure.validation.rendered_snapshot import build_current_rendered_snapshot

    module_path = ROOT / "projects/templates/template_pitch_deck/src/template_pitch_deck/coverage_chart_data.py"
    specification = importlib.util.spec_from_file_location("actual_pitch_counts_reader", module_path)
    assert specification is not None and specification.loader is not None
    reader = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(reader)
    project = _green_project(tmp_path)
    # This is a real valid HTML-only fixture, so an actual Stage 4 rebind can
    # succeed without inventing native PDF/PPTX output or relaxing production.
    config = yaml.safe_load((project / "manuscript/config.yaml").read_text())
    config["render"] = {"formats": {"pdf": False, "html": True, "slides": False, "docx": False, "epub": False}}
    body = yaml.safe_dump(config)
    (project / "manuscript/config.yaml").write_text(body)
    (project / "output/manuscript/config.yaml").write_text(body)
    (project / "output/web/index.html").write_text(
        "<!doctype html><html><body><main>Current prose.</main></body></html>\n"
    )
    counts = _write(tmp_path, "docs/_generated/COUNTS.md", "| `template_template` | 10 | 71.00% |\n")
    rows = reader.read_all_exemplar_coverage(tmp_path)
    data = project / "output/data/chart_inputs.json"
    data.write_text(json.dumps({"exemplar_coverage": rows}))
    snapshot_current_artifact_manifest(project / "output")
    _write_green_validation_report(tmp_path, project)
    write_rendered_provenance_receipt(tmp_path, PROJECT)
    before = build_current_rendered_snapshot(tmp_path, PROJECT).output.sha256
    counts.write_text("| `template_template` | 11 | 92.00% |\n")
    assert reader.read_all_exemplar_coverage(tmp_path) != rows
    assert json.loads(data.read_text())["exemplar_coverage"] == [list(row) for row in rows]
    assert build_current_rendered_snapshot(tmp_path, PROJECT).output.sha256 == before
    passed, message = rebind_project(PROJECT, tmp_path)
    assert passed, message
    assert json.loads(data.read_text())["exemplar_coverage"] == [list(row) for row in rows]


@pytest.mark.parametrize(
    "selected", [["20_render_decks.py"], ["16_generate_charts.py"], ["20_render_decks.py", "16_generate_charts.py"]]
)
def test_dependent_analysis_refuses_omitted_or_reordered_canonical_consumers(
    repository: Path, selected: list[str]
) -> None:
    path = repository / ("projects/" + DEPENDENT_ANALYSIS_SCOPE + "/manuscript/config.yaml")
    config = yaml.safe_load(path.read_text())
    config["analysis"] = {"scripts": selected}
    path.write_text(yaml.safe_dump(config))
    _commit(repository)
    with pytest.raises(ValueError, match="charts before.*deck"):
        _plan(repository)


@pytest.mark.parametrize("entry", ["direct", "cli-default"])
@pytest.mark.parametrize("mode", ["refresh", "rebind-only"])
def test_coordinated_run_keeps_actual_prepare_failure_terminal(
    repository: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str, entry: str
) -> None:
    version = root_package_version(ROOT)
    for relative in (
        "pyproject.toml",
        *["projects/" + scope + "/pyproject.toml" for scope in PUBLIC_PROJECT_NAMES],
        *["projects/" + scope + "/manuscript/config.yaml" for scope in PUBLIC_PROJECT_NAMES],
    ):
        path = repository / relative
        path.write_text(path.read_text().replace("5.1.0", version))
    first = next(
        scope for wave in provider_waves(current_provider_graph(repository)) for scope in wave if scope != "root"
    )
    # This is an actual uv parse refusal, before network/build/runtime work.
    _write(repository, "projects/" + first + "/uv.lock", "[invalid-lock\n")
    source = _commit(repository)
    monkeypatch.setenv("UV_OFFLINE", "1")
    directory = tmp_path / ("coordinated-" + mode)
    if entry == "direct":
        result = run_coordinated(repository, directory, source, version, 1, mode=mode)
    else:
        result = main(
            [
                "--repo-root",
                str(repository),
                "--directory",
                str(directory),
                "--mode",
                mode,
                "run",
                "--source-sha",
                source,
                "--expected-version",
                version,
            ]
        )
    assert result != 0
    label = first.replace("/", "__") + "-prepare"
    original = json.loads((directory / "diagnostics" / (label + ".exit.json")).read_bytes())
    assert original["original_exit_code"] != 0 and original["returncode"] != 0
    assert original["process"]["command"][1:3] == ["sync", "--locked"]
    assert json.loads((directory / "plan.json").read_bytes())["mode"] == mode
    assert sorted(path.name for path in (directory / "diagnostics").iterdir()) == [
        label + ".exit.json",
        label + ".stderr",
        label + ".stdout",
    ]
    assert not any(
        (directory / name).exists() for name in ("prepared.json", "generated.json", "candidate.json", "review")
    )
    assert git(repository, "rev-parse", "HEAD").decode().strip() == source


@pytest.mark.parametrize("workers", [0, 2, 3, 4, 5, True])
def test_coordinated_run_refuses_bad_workers_before_creating_any_evidence(
    repository: Path, tmp_path: Path, workers: int
) -> None:
    directory = tmp_path / "bad-workers"
    source = git(repository, "rev-parse", "HEAD").decode().strip()
    with pytest.raises(ValueError, match="workers"):
        run_coordinated(repository, directory, source, root_package_version(ROOT), workers)
    assert not directory.exists()
    assert git(repository, "rev-parse", "HEAD").decode().strip() == source


@pytest.mark.parametrize("workers", [2, 3, 4])
@pytest.mark.parametrize("entry", ["generate", "generate-cli", "run-cli"])
def test_unsafe_shared_account_workers_refuse_before_any_plan_or_producer(
    repository: Path, tmp_path: Path, workers: int, entry: str
) -> None:
    directory = tmp_path / "unsafe-workers"
    source = git(repository, "rev-parse", "HEAD").decode().strip()
    with pytest.raises(ValueError, match="workers.*exactly one.*census"):
        if entry == "generate":
            generate(repository, directory, workers)
        else:
            phase = "generate" if entry == "generate-cli" else "run"
            argv = ["--repo-root", str(repository), "--directory", str(directory), phase, "--jobs", str(workers)]
            if phase == "run":
                argv.extend(["--source-sha", source, "--expected-version", root_package_version(ROOT)])
            main(argv)
    assert not directory.exists()
    assert not (repository / "output/readiness/publication-refresh").exists()
    assert not git(repository, "status", "--porcelain")
    assert git(repository, "rev-parse", "HEAD").decode().strip() == source


@pytest.mark.parametrize("worker_arguments", [[], ["--jobs", "1"]])
def test_generate_cli_default_matches_explicit_single_worker_before_missing_preparation(
    repository: Path, tmp_path: Path, worker_arguments: list[str]
) -> None:
    directory = tmp_path / "unprepared-single-worker"
    write_json(directory / "plan.json", _plan(repository))
    before = (directory / "plan.json").read_bytes()
    # An allowed single worker reaches the unchanged own-runtime preparation
    # requirement; no producer is substituted or admitted by this control.
    with pytest.raises(FileNotFoundError, match="prepared.json"):
        main(["--repo-root", str(repository), "--directory", str(directory), "generate", *worker_arguments])
    assert (directory / "plan.json").read_bytes() == before
    assert sorted(path.name for path in directory.iterdir()) == ["plan.json"]
    assert not (repository / "output/readiness/publication-refresh").exists()
    assert not git(repository, "status", "--porcelain")
