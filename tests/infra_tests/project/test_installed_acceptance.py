"""Real installed-wheel, source-contamination and exact archive controls."""

from __future__ import annotations

import base64
import csv
import hashlib
import json
import shutil
import subprocess
import stat
import sys
import time
import zipfile
import uuid
from dataclasses import asdict
from io import BytesIO, StringIO
from pathlib import Path
from types import FrameType

import pytest

from infrastructure.core.testing.project_test_matrix import ProjectTestTask, run_project_test_matrix
from infrastructure.project.installed_acceptance import run_installed_acceptance
from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.project.installed_acceptance_artifacts import (
    INSTALLED_PROBE,
    admit_provider_wheel,
    freeze_wheel_bytes,
    inspect_wheel,
    prepare_export,
    write_binary,
)
from infrastructure.project.copy_exemplar import export_exemplar
from infrastructure.project.installed_acceptance_runtime import (
    declared_local_dependencies,
    freeze_locked_metadata,
    install_admitted_wheels,
    local_dependency_closure,
)
from infrastructure.project.installed_acceptance_worker import _environment, _run
from infrastructure.project.acceptance_payload import format_acceptance_payload_loader, write_acceptance_payload
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.publishing.root_release_contract import root_package_version
from infrastructure.reporting.release_readiness_profile import Requirement
from infrastructure.reporting.native_installed_preparation import native_runtime_export_command
from infrastructure.core.testing.pytest_profiles import TEST_RUNNER_BASE_DEPS
from tests.infra_tests.reporting.test_required_readiness import _root_policy_declaration


def _export_repository(tmp_path: Path) -> tuple[Path, Requirement, Path, Path]:
    root = tmp_path / "repository"
    project = root / "projects/templates/template_code_project"
    (project / "rendered").mkdir(parents=True)
    (project / "README.md").write_text("# Authored project\n")
    (project / "pyproject.toml").write_text("[project]\nname = 'template-code-project'\nversion = '1.0.0'\n")
    (project / "rendered/proof.pdf").write_bytes(b"retained deposited proof\x00\xff")
    (root / "pyproject.toml").write_text("[project]\nname = 'research-project-template'\nversion = '4.0.1'\n")
    for arguments in (
        ("init",),
        ("config", "user.email", "fixture@example.com"),
        ("config", "user.name", "Fixture"),
        ("add", "."),
        ("commit", "-m", "owned export fixture"),
    ):
        subprocess.run(["git", "-c", "core.fsmonitor=false", *arguments], cwd=root, check=True, capture_output=True)
    requirement = Requirement("code:export", "export", "templates/template_code_project", "1.0.0", "4.0.1", "a" * 64)
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    return root, requirement, scratch, root / "output/readiness/export"


def test_acceptance_export_retains_exact_proofs_without_changing_fork_copy(tmp_path: Path) -> None:
    root, requirement, scratch, directory = _export_repository(tmp_path)
    fork = tmp_path / "ordinary-fork"
    export_exemplar(root, requirement.scope, fork)
    assert not (fork / "rendered").exists()

    destination, details = prepare_export(root, requirement, scratch, directory)

    proof = (root / "projects" / requirement.scope / "rendered/proof.pdf").read_bytes()
    manifest = json.loads((root / details["manifest_artifact"]["path"]).read_bytes())
    with zipfile.ZipFile(root / details["bundle_artifact"]["path"]) as archive:
        embedded = json.loads(archive.read(".template-export.json"))
        assert archive.read("rendered/proof.pdf") == proof
        assert embedded["files"] == manifest["files"]
        assert embedded["files"]["rendered/proof.pdf"] == hashlib.sha256(proof).hexdigest()
    assert (destination / "rendered/proof.pdf").read_bytes() == proof


def test_acceptance_export_refuses_missing_bytes_outside_root_proofs(tmp_path: Path) -> None:
    root, requirement, scratch, directory = _export_repository(tmp_path)
    nested = root / "projects" / requirement.scope / "docs/rendered/authored.md"
    nested.parent.mkdir(parents=True)
    nested.write_text("Authored nested input, excluded by ordinary fork copying.\n")
    subprocess.run(["git", "add", str(nested)], cwd=root, check=True, capture_output=True)

    with pytest.raises(ValueError, match="differs outside retained publication proofs"):
        prepare_export(root, requirement, scratch, directory)
    assert not (directory / "source.zip").exists()


@pytest.mark.parametrize("changed_path", ["source-proof", "copied-readme"])
def test_acceptance_export_refuses_actual_byte_changes_during_copy(tmp_path: Path, changed_path: str) -> None:
    root, requirement, scratch, directory = _export_repository(tmp_path)
    observed = []

    def change_owned_file(frame: FrameType, event: str, argument: object) -> None:
        if event == "return" and frame.f_code is export_exemplar.__code__:
            target = (
                root / "projects" / requirement.scope / "rendered/proof.pdf"
                if changed_path == "source-proof"
                else scratch / "template_code_project/README.md"
            )
            target.write_bytes(b"changed after original export\n")
            observed.append(target)

    previous = sys.getprofile()
    try:
        sys.setprofile(change_owned_file)
        with pytest.raises(ValueError, match="canonical export differs"):
            prepare_export(root, requirement, scratch, directory)
    finally:
        sys.setprofile(previous)
    assert len(observed) == 1
    assert not (directory / "source.zip").exists()


def _wheel(
    root: Path,
    *,
    scope: str = "templates/template_code_project",
    module: str = "installed_example",
    distribution: str = "installed-example",
    content: bytes | None = None,
) -> tuple[Requirement, Path, dict[str, str]]:
    package = root / "projects" / scope / "src" / module
    package.mkdir(parents=True)
    content = content or b"def measured_value():\n    return 17\n"
    (package / "__init__.py").write_bytes(content)
    requirement = Requirement(
        f"{scope}:installed", "installed", scope, "1.0.0", "4.0.1", "a" * 64, package=distribution
    )
    metadata = f"{module}-1.0.0.dist-info"
    members = {
        f"{module}/__init__.py": content,
        f"{metadata}/METADATA": f"Metadata-Version: 2.1\nName: {distribution}\nVersion: 1.0.0\n".encode(),
        f"{metadata}/WHEEL": (
            b"Wheel-Version: 1.0\nGenerator: independent-control\nRoot-Is-Purelib: true\nTag: py3-none-any\n"
        ),
    }
    record = f"{metadata}/RECORD"
    buffer = StringIO()
    writer = csv.writer(buffer)
    for name, data in members.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip("=")
        writer.writerow((name, "sha256=" + digest, str(len(data))))
    writer.writerow((record, "", ""))
    members[record] = buffer.getvalue().encode()
    wheel = root / f"{module}-1.0.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    return requirement, wheel, {f"{module}/__init__.py": hashlib.sha256(content).hexdigest()}


def test_exact_wheel_source_and_record_admission_rejects_old_implementation(tmp_path: Path) -> None:
    requirement, wheel, _ = _wheel(tmp_path)
    targets, members = inspect_wheel(tmp_path, requirement, wheel)
    assert targets == ("installed_example",)
    assert "installed_example/__init__.py" in members
    (tmp_path / "projects/templates/template_code_project/src/installed_example/__init__.py").write_text("VALUE=99\n")
    with pytest.raises(ValueError, match="current exact source"):
        inspect_wheel(tmp_path, requirement, wheel)


def _startup_marker_wheel(wheel: Path, marker: Path) -> bytes:
    """Build a valid owned negative wheel with executable invented startup bytes."""
    with zipfile.ZipFile(wheel) as archive:
        record = next(name for name in archive.namelist() if name.endswith(".dist-info/RECORD"))
        members = {name: archive.read(name) for name in archive.namelist() if name != record}
    members["invented_startup.pth"] = (
        f"import pathlib; pathlib.Path({str(marker)!r}).write_text('invented startup executed')\n".encode()
    )
    rows = StringIO()
    writer = csv.writer(rows)
    for name, content in members.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).decode().rstrip("=")
        writer.writerow((name, "sha256=" + digest, str(len(content))))
    writer.writerow((record, "", ""))
    members[record] = rows.getvalue().encode()
    result = BytesIO()
    with zipfile.ZipFile(result, "w") as archive:
        for name, content in members.items():
            archive.writestr(name, content)
    return result.getvalue()


@pytest.mark.parametrize("provider", [False, True])
def test_actual_install_consumes_admitted_bytes_after_origin_replacement(tmp_path: Path, provider: bool) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    requirement, wheel, _ = _wheel(root)
    scratch = tmp_path / "private scratch #fixture"
    scratch.mkdir(mode=0o700)
    if provider:
        binding = write_binary(root, root / "output/readiness/origin" / wheel.name, wheel.read_bytes())
        original = root / binding["path"]
        admitted = admit_provider_wheel(root, requirement, binding, scratch)
    else:
        original = scratch / "build" / wheel.name
        original.parent.mkdir()
        original.write_bytes(wheel.read_bytes())
        admitted = freeze_wheel_bytes(root, requirement, read_bytes_confined(scratch, original), scratch, original.name)
    assert stat.S_IMODE(admitted.path.stat().st_mode) == 0o400
    marker = tmp_path / "invented-startup.txt"
    original.write_bytes(_startup_marker_wheel(original, marker))
    assert hashlib.sha256(original.read_bytes()).hexdigest() != admitted.sha256
    uv = shutil.which("uv")
    assert uv is not None
    environment = _environment(Path(sys.executable), scratch)
    deadline = time.monotonic() + 120
    directory = root / "output/readiness/actual-replacement"

    def run(command: tuple[str, ...], label: str):
        return _run(command, scratch, environment, deadline, root, directory, label)

    # This real positive control proves the replacement wheel's startup code
    # executes if its mutable origin is installed without admission.
    unsafe = scratch / "unsafe-environment"
    run((uv, "venv", "--no-project", "--no-python-downloads", "--python", sys.executable, str(unsafe)), "unsafe-venv")
    run(
        (
            uv,
            "pip",
            "install",
            "--offline",
            "--no-config",
            "--no-deps",
            "--no-build",
            "--python",
            str(unsafe / "bin/python"),
            f"installed-example @ {original.as_uri()}",
        ),
        "unsafe-install",
    )
    run((str(unsafe / "bin/python"), "-I", "-c", "pass"), "unsafe-startup")
    assert marker.read_text() == "invented startup executed"
    marker.unlink()
    if provider:
        with pytest.raises(ValueError, match="changed after its original admission"):
            admit_provider_wheel(root, requirement, binding, scratch)
    installed = scratch / "verified-environment"
    run(
        (uv, "venv", "--no-project", "--no-python-downloads", "--python", sys.executable, str(installed)),
        "verified-venv",
    )
    install_admitted_wheels(scratch, installed / "bin/python", uv, [admitted], run)
    run(
        (
            str(installed / "bin/python"),
            "-I",
            "-c",
            "import installed_example; assert installed_example.measured_value() == 17",
        ),
        "verified-startup",
    )
    assert not marker.exists()
    requirements = (scratch / "admitted-wheel-requirements.txt").read_text()
    assert "%20" in requirements and "%23" in requirements
    assert admitted.sha256 in requirements and str(original) not in requirements


def test_actual_install_refuses_private_copy_drift_before_startup(tmp_path: Path) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    requirement, wheel, _ = _wheel(root)
    scratch = tmp_path / "private-scratch"
    scratch.mkdir(mode=0o700)
    admitted = freeze_wheel_bytes(root, requirement, read_bytes_confined(root, wheel), scratch, wheel.name)
    marker = tmp_path / "invented-startup.txt"
    admitted.path.chmod(0o600)
    admitted.path.write_bytes(_startup_marker_wheel(admitted.path, marker))
    assert hashlib.sha256(admitted.path.read_bytes()).hexdigest() != admitted.sha256
    uv = shutil.which("uv")
    assert uv is not None
    environment = _environment(Path(sys.executable), scratch)
    deadline = time.monotonic() + 120
    directory = root / "output/readiness/private-copy-drift"

    def run(command: tuple[str, ...], label: str):
        return _run(command, scratch, environment, deadline, root, directory, label)

    installed = scratch / "verified-environment"
    run(
        (uv, "venv", "--no-project", "--no-python-downloads", "--python", sys.executable, str(installed)),
        "verified-venv",
    )
    with pytest.raises(ValueError, match="wheel-install child failed"):
        install_admitted_wheels(scratch, installed / "bin/python", uv, [admitted], run)
    run((str(installed / "bin/python"), "-I", "-c", "pass"), "verified-startup")
    assert not marker.exists()
    # Prove the refused copy is a genuinely executable wheel, rather than a
    # malformed-file control that cannot reach interpreter startup.
    unsafe = scratch / "unsafe-environment"
    run((uv, "venv", "--no-project", "--no-python-downloads", "--python", sys.executable, str(unsafe)), "unsafe-venv")
    run(
        (
            uv,
            "pip",
            "install",
            "--offline",
            "--no-config",
            "--no-deps",
            "--no-build",
            "--python",
            str(unsafe / "bin/python"),
            f"installed-example @ {admitted.path.as_uri()}",
        ),
        "unsafe-install",
    )
    run((str(unsafe / "bin/python"), "-I", "-c", "pass"), "unsafe-startup")
    assert marker.read_text() == "invented startup executed"


@pytest.fixture
def installed_environment(tmp_path: Path) -> tuple[Path, Requirement, Path, dict[str, str]]:
    root = tmp_path / "repository"
    root.mkdir()
    requirement, wheel, members = _wheel(root)
    environment = tmp_path / "environment"
    env = _environment(Path(sys.executable), tmp_path)
    env["UV_LINK_MODE"] = "copy"
    uv = shutil.which("uv")
    assert uv is not None
    commands = [
        (uv, "venv", "--no-project", "--no-python-downloads", "--python", sys.executable, str(environment)),
        (
            uv,
            "pip",
            "install",
            "--offline",
            "--no-config",
            "--no-deps",
            "--python",
            str(environment / "bin/python"),
            str(wheel),
        ),
    ]
    for index, command in enumerate(commands):
        observed = run_project_test_matrix([ProjectTestTask(index, "wheel-control", command, tmp_path, env, 30, True)])[
            0
        ]
        assert observed.returncode == 0 and not observed.timed_out, observed.output_tail
    return environment, requirement, root, members


def _probe(
    environment: Path,
    requirement: Requirement,
    root: Path,
    members: dict[str, str],
    outside: Path,
    providers: list[dict[str, object]] | None = None,
):
    outside.mkdir()
    spec = {
        "scope": requirement.scope,
        "package": requirement.package,
        "version": requirement.version,
        "targets": ["installed_example"],
        "wheel_members": members,
        "forbidden_roots": [str(root)],
        "dependency_providers": providers or [],
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "run_nonce": uuid.uuid4().hex,
    }
    observation = outside / "observation.json"
    bytecode = outside / "fresh-bytecode"
    bytecode.mkdir()
    from infrastructure.core.implementation_custody import bytecode_audit_bootstrap

    site = next((environment / "lib").glob("python*/site-packages"))
    admitted = dict(members)
    for provider in providers or []:
        admitted.update(provider["wheel_members"])
    from infrastructure.core import bytecode_audit

    hook = Path(bytecode_audit.__file__).read_bytes()
    (outside / "bytecode_audit.py").write_bytes(hook)
    canonical_hook = root / "infrastructure/core/bytecode_audit.py"
    canonical_hook.parent.mkdir(parents=True, exist_ok=True)
    canonical_hook.write_bytes(hook)
    namespace_targets = ["installed_example"]
    for provider in providers or []:
        namespace_targets.extend(provider["targets"])
    audit_roots = tuple(site / name for name in admitted if name.endswith(".py")) + tuple(
        site / target for target in namespace_targets if target + ".py" not in admitted
    )
    audit = bytecode_audit_bootstrap(audit_roots, bytecode, audit_path=outside / "bytecode_audit.py")
    spec["audit"] = {
        "roots": [str(path) for path in audit_roots],
        "path": str(outside / "bytecode_audit.py"),
        "prefix": str(bytecode),
        "sha256": hashlib.sha256(hook).hexdigest(),
    }
    spec["probe_payload"] = write_acceptance_payload(
        outside,
        outside / "installed-probe-payload.py",
        (audit + "\n" + INSTALLED_PROBE).encode(),
        forbidden_roots=(root,),
    )
    (outside / "spec.json").write_text(json.dumps(spec, sort_keys=True))
    command = (
        str(environment / "bin/python"),
        "-I",
        "-X",
        f"pycache_prefix={bytecode}",
        "-c",
        format_acceptance_payload_loader(spec["probe_payload"]),
        str(outside / "spec.json"),
        str(observation),
    )
    env = _environment(environment / "bin/python", outside)
    env["PRIVATE_API_TOKEN"] = "private environment sentinel"
    observed = run_project_test_matrix([ProjectTestTask(0, "installed-probe", command, outside, env, 30, True)])[0]
    (outside / "process.json").write_text(
        json.dumps({**asdict(observed), "command": list(command), "cwd": str(outside)})
    )
    return observed, observation


def test_real_installed_probe_runs_outside_checkout_without_source_paths(installed_environment, tmp_path: Path) -> None:
    environment, requirement, root, members = installed_environment
    observed, observation = _probe(environment, requirement, root, members, tmp_path / "outside")
    assert observed.returncode == 0 and not observed.timed_out, observed.output_tail
    payload = json.loads(observation.read_text())
    assert payload["isolated"] is True and payload["source_path_contamination"] is False
    assert payload["imported_modules"] == ["installed_example"]
    assert payload["interpreter"] == str(environment / "bin/python")
    assert all(Path(origin).is_relative_to(environment) for origin in payload["origins"]["installed_example"])
    assert "private environment sentinel" not in observation.read_text() + observed.output_tail


def test_actual_installed_cell_reader_requires_bound_process_and_complete_minor_selection(
    installed_environment, tmp_path: Path
) -> None:
    from infrastructure.project.installed_acceptance_validation import _cell, validate_installed_matrix
    from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

    environment, requirement, root, members = installed_environment
    outside = tmp_path / "outside"
    observed, observation = _probe(environment, requirement, root, members, outside)
    assert observed.returncode == 0 and not observed.timed_out, observed.output_tail
    raw = json.loads(observation.read_text())
    process = json.loads((outside / "process.json").read_text())

    def bound(filename: str, content: bytes) -> dict[str, str]:
        return write_binary(root, root / "output/readiness/reader" / filename, content)

    spec = json.loads((outside / "spec.json").read_text())
    details = {
        **raw,
        "wheel_artifact": bound("current.whl", next(root.glob("*.whl")).read_bytes()),
        "runtime_artifact": bound("probe.json", observation.read_bytes()),
        "process_artifact": bound("process.json", json.dumps(process).encode()),
        "probe_spec_artifact": bound("spec.json", json.dumps(spec).encode()),
        "probe_payload_artifact": bound(
            "installed-probe-payload.py", (outside / "installed-probe-payload.py").read_bytes()
        ),
        "selected_interpreter_sha256": raw["interpreter_sha256"],
        "command": process["command"],
    }
    cell = {"scope": requirement.scope, "python_version": raw["python_version"], "status": "pass", "details": details}
    _cell(requirement, cell, SnapshotReader(root))
    for change in ({"returncode": 2}, {"timed_out": True}, {"detail": "child launch refused"}):
        forged = bound("bad-process.json", json.dumps({**process, **change}).encode())
        with pytest.raises(ValueError, match="successful bound isolated child process"):
            _cell(requirement, {**cell, "details": {**details, "process_artifact": forged}}, SnapshotReader(root))
    payload_body = (outside / "installed-probe-payload.py").read_bytes()
    for filename, body, diagnostic in (
        ("installed-probe-payload.py", payload_body + b"\n# changed retained body\n", "regenerated Source body"),
        ("alternate-payload.py", payload_body, "fixed evidence path"),
    ):
        with pytest.raises(ValueError, match=diagnostic):
            _cell(
                requirement,
                {**cell, "details": {**details, "probe_payload_artifact": bound(filename, body)}},
                SnapshotReader(root),
            )
    # Restore the canonical retained artifact after the intentionally wrong body.
    bound("installed-probe-payload.py", payload_body)
    for change in ("path", "hash", "identity"):
        payload = {**spec["probe_payload"]}
        if change == "path":
            payload["path"] = str(outside / "foreign.py")
        elif change == "hash":
            payload["sha256"] = "0" * 64
        else:
            payload["identity"] = {**payload["identity"], "inode": payload["identity"]["inode"] + 1}
        wrong_spec = {**spec, "probe_payload": payload}
        wrong_spec_binding = bound("wrong-spec.json", json.dumps(wrong_spec).encode())
        wrong_raw = {**raw, "probe_spec_sha256": wrong_spec_binding["sha256"]}
        with pytest.raises(
            ValueError, match="Source body or fixed outside path|successful bound isolated child process"
        ):
            _cell(
                requirement,
                {
                    **cell,
                    "details": {
                        **details,
                        "probe_spec_artifact": wrong_spec_binding,
                        "runtime_artifact": bound("wrong-probe.json", json.dumps(wrong_raw).encode()),
                    },
                },
                SnapshotReader(root),
            )
    # This real different zero-exit child reaches no probe but retains the
    # earlier actual positive observation. A suffix match cannot bind it.
    early_command = list(process["command"])
    early_command[5] = "raise SystemExit(0)\n" + INSTALLED_PROBE
    early = run_project_test_matrix(
        [
            ProjectTestTask(
                0,
                "installed-probe",
                tuple(early_command),
                outside,
                _environment(environment / "bin/python", outside),
                30,
                True,
            )
        ]
    )[0]
    assert early.returncode == 0 and not early.timed_out, early.output_tail
    early_binding = bound(
        "early-process.json", json.dumps({**asdict(early), "command": early_command, "cwd": str(outside)}).encode()
    )
    with pytest.raises(ValueError, match="successful bound isolated child process"):
        _cell(
            requirement,
            {**cell, "details": {**details, "command": early_command, "process_artifact": early_binding}},
            SnapshotReader(root),
        )
    foreign = next(minor for minor in ("3.14", "3.15") if minor != raw["python_version"])
    relabeled_spec = {**spec, "python_version": foreign}
    relabeled_binding = bound("relabeled-spec.json", json.dumps(relabeled_spec).encode())
    relabeled = {**raw, "python_version": foreign, "probe_spec_sha256": relabeled_binding["sha256"]}
    with pytest.raises(ValueError, match="exact run/specification/runtime"):
        _cell(
            requirement,
            {
                **cell,
                "python_version": foreign,
                "details": {
                    **details,
                    **relabeled,
                    "runtime_artifact": bound("relabeled-probe.json", json.dumps(relabeled).encode()),
                    "probe_spec_artifact": relabeled_binding,
                },
            },
            SnapshotReader(root),
        )
    for cells in ([cell], [cell, cell, cell]):
        with pytest.raises(ValueError, match="all supported runtime observations"):
            validate_installed_matrix(
                requirement,
                {
                    "source_current": True,
                    "tested_python_versions": ["3.14", "3.15"],
                    "runtime_observations": cells,
                },
                SnapshotReader(root),
            )


def test_editable_source_path_cannot_impersonate_installed_wheel(installed_environment, tmp_path: Path) -> None:
    environment, requirement, root, members = installed_environment
    site = next((environment / "lib").glob("python*/site-packages"))
    (site / "source-leak.pth").write_text(str(root / "projects/templates/template_code_project/src"))
    observed, observation = _probe(environment, requirement, root, members, tmp_path / "outside")
    assert observed.returncode != 0 and "source path contamination" in observed.output_tail
    assert not observation.exists()


def test_installed_byte_mutation_cannot_reuse_original_wheel_receipt(installed_environment, tmp_path: Path) -> None:
    environment, requirement, root, members = installed_environment
    site = next((environment / "lib").glob("python*/site-packages"))
    (site / "installed_example/__init__.py").write_text("def measured_value():\n    return 99\n")
    observed, observation = _probe(environment, requirement, root, members, tmp_path / "outside")
    assert observed.returncode != 0 and "installed bytes differ" in observed.output_tail
    assert not observation.exists()


def test_binary_evidence_cannot_escape_readiness_lane(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="canonical"):
        write_binary(tmp_path, tmp_path / "output/readiness/../../infrastructure/package.whl", b"unapproved")
    assert not (tmp_path / "infrastructure").exists()


def test_real_child_deadline_refuses_incomplete_installation_stage(tmp_path: Path) -> None:
    command = (sys.executable, "-I", "-B", "-c", "import time; time.sleep(3)")
    with pytest.raises(TimeoutError, match="total deadline"):
        _run(
            command,
            tmp_path,
            _environment(Path(sys.executable), tmp_path),
            time.monotonic() + 0.1,
            tmp_path,
            tmp_path / "output/readiness/control",
            "deadline",
        )
    observed = json.loads((tmp_path / "output/readiness/control/deadline-process.json").read_text())
    assert observed["timed_out"] is True and observed["returncode"] == 124


@pytest.mark.parametrize("workers,deadline", [(True, 1), (0, 1), (4, 1), (1, True), (1, 0)])
def test_invalid_matrix_budget_is_refused_before_source_or_environment_writes(
    tmp_path: Path, workers, deadline
) -> None:
    with pytest.raises(ValueError):
        run_installed_acceptance(tmp_path, {}, project_workers=workers, timeout_seconds=deadline)
    assert list(tmp_path.iterdir()) == []


def test_complete_missing_runtime_matrix_retains_all_blockers_and_exit75(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[3]
    platform_version = root_package_version(root)
    (tmp_path / "infrastructure").mkdir()
    (tmp_path / "infrastructure/_version.py").write_bytes((root / "infrastructure/_version.py").read_bytes())
    (tmp_path / "pyproject.toml").write_text(
        f'[project]\nname="research-project-template"\nversion="{platform_version}"\n'
    )
    (tmp_path / "CHANGELOG.md").write_text(f"## [{platform_version}] - Unreleased\n")
    (tmp_path / ".python-version").write_text("3.14\n")
    _root_policy_declaration(tmp_path)
    for scope in PUBLIC_PROJECT_NAMES:
        project = tmp_path / "projects" / scope
        (project / "src").mkdir(parents=True)
        (project / "manuscript").mkdir()
        (project / "src/model.py").write_text("VALUE=1\n")
        (project / "pyproject.toml").write_text(
            "[project]\nname=" + json.dumps(Path(scope).name) + '\nversion="1.0.0"\n'
            f'[tool.template]\nplatform_version="{platform_version}"\n'
            'tested_python_versions=["3.14","3.15"]\nrequired_unpaid_capabilities=[]\n'
        )
        (project / "manuscript/config.yaml").write_text(
            f'publication:\n  intended_version: "1.0.0"\n  platform_version: "{platform_version}"\n'
        )
    report = run_installed_acceptance(tmp_path, {}, project_workers=3)
    assert report["exit_code"] == 75
    assert report["installed_matrix"]["matrix_complete"] is True
    assert report["installed_matrix"]["observed_cells"] == report["installed_matrix"]["expected_cells"] == 52
    assert report["installed_matrix"]["counts"] == {"pass": 0, "fail": 0, "blocked": 52}
    assert len(report["gates"]) == 52
    assert all(gate["status"] == "blocked" for gate in report["gates"].values())
    assert all(cell["blockers"] for cell in report["installed_matrix"]["results"])


def test_real_locked_exports_consume_private_metadata_despite_checkout_aba(tmp_path: Path) -> None:
    source = Path(__file__).resolve().parents[3]
    repository = tmp_path / "repository"
    scope = "templates/template_search_project"
    for base in (Path(), Path("projects") / scope):
        for name in ("pyproject.toml", "uv.lock"):
            target = repository / base / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((source / base / name).read_bytes())
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    snapshot = freeze_locked_metadata(repository, scratch)
    observed_root = repository / "pyproject.toml"
    observed_project = repository / "projects" / scope / "pyproject.toml"
    original_root, original_project = observed_root.read_bytes(), observed_project.read_bytes()
    # An altered canonical checkout would fail TOML parsing if uv still consumed it.
    observed_root.write_text("invalid checkout metadata [\n")
    observed_project.write_text("invalid checkout metadata [\n")
    uv = shutil.which("uv")
    assert uv is not None
    commands = [
        (
            uv,
            "export",
            "--directory",
            str(snapshot.root),
            "--locked",
            "--offline",
            "--only-group",
            "installed-build",
            "--no-emit-project",
            "--no-header",
            "--no-annotate",
            "--output-file",
            str(scratch / "build.txt"),
        ),
        (
            uv,
            "export",
            "--directory",
            str(snapshot.root / "projects" / scope),
            "--locked",
            "--offline",
            "--no-default-groups",
            "--no-emit-project",
            "--no-emit-local",
            "--no-header",
            "--no-annotate",
            "--output-file",
            str(scratch / "runtime.txt"),
        ),
    ]
    try:
        for index, command in enumerate(commands):
            result = run_project_test_matrix(
                [
                    ProjectTestTask(
                        index,
                        "frozen-lock-export",
                        command,
                        scratch,
                        _environment(Path(sys.executable), scratch),
                        30,
                        True,
                    )
                ]
            )[0]
            assert result.returncode == 0 and not result.timed_out, result.output_tail
    finally:
        observed_root.write_bytes(original_root)
        observed_project.write_bytes(original_project)
    assert snapshot.unchanged()
    assert "hatchling==1.32.4" in (scratch / "build.txt").read_text()
    runtime = (scratch / "runtime.txt").read_text()
    assert "requests==" in runtime and "--hash=sha256:" in runtime
    assert str(repository) not in runtime and "-e " not in runtime


@pytest.mark.timeout(120)
def test_native_locked_export_retains_real_full_suite_execution_dependencies(tmp_path: Path) -> None:
    """Actual locked exports distinguish the execution profile from format-only inputs."""
    source = Path(__file__).resolve().parents[3]
    snapshot = freeze_locked_metadata(source, tmp_path)
    uv = shutil.which("uv")
    assert uv is not None
    names = []
    for index, format_only in enumerate((False, True)):
        requirements = tmp_path / f"runtime-{index}.txt"
        command = native_runtime_export_command(Path(uv), snapshot.root, requirements)
        if format_only:
            command += ("--no-default-groups",)
        result = run_project_test_matrix(
            [
                ProjectTestTask(
                    index,
                    "native-locked-export",
                    command,
                    tmp_path,
                    _environment(Path(sys.executable), tmp_path),
                    30,
                    True,
                )
            ]
        )[0]
        assert result.returncode == 0 and not result.timed_out, result.output_tail
        text = requirements.read_text()
        names.append(
            {
                line.split("==", 1)[0].strip().replace("_", "-").lower()
                for line in text.splitlines()
                if line and not line[0].isspace() and "==" in line
            }
        )
        assert "--hash=sha256:" in text and "-e " not in text and str(source) not in text
        assert "git+" not in text and "desloppify" not in text, "native runtime excludes its unused Git lint scanner"
    required = {*TEST_RUNNER_BASE_DEPS, "coverage", "mypy", "inferactively-pymdp", "discopy", "cryptography"}
    assert required <= names[0]
    assert "coverage" not in names[1] and "pytest" not in names[1]
    assert snapshot.unchanged()


def test_private_metadata_mutation_refuses_original_snapshot_identity(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "pyproject.toml").write_text('[project]\nname="original"\nversion="1.0.0"\n')
    (repository / "uv.lock").write_text("version = 1\n")
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    snapshot = freeze_locked_metadata(repository, scratch)
    selected = snapshot.root / "pyproject.toml"
    selected.chmod(0o600)
    selected.write_text('[project]\nname="different"\nversion="1.0.0"\n')
    assert not snapshot.unchanged()


def _provider_metadata(root: Path) -> tuple[str, str]:
    root.mkdir(exist_ok=True)
    (root / "pyproject.toml").write_text('[project]\nname="research-project-template"\nversion="4.0.1"\n')
    engine = "templates/template_literature_meta_analysis"
    consumer = "templates/template_advanced_literature_review"
    for scope, name, dependencies, sources in (
        (
            engine,
            "template-literature-meta-analysis",
            '["research-project-template==4.0.1"]',
            'research-project-template={path="../../..",editable=true}',
        ),
        (
            consumer,
            "template-advanced-literature-review",
            '["template-literature-meta-analysis==0.2.0"]',
            'template-literature-meta-analysis={path="../template_literature_meta_analysis",editable=true}',
        ),
    ):
        directory = root / "projects" / scope
        directory.mkdir(parents=True)
        (directory / "pyproject.toml").write_text(
            f'[project]\nname="{name}"\nversion="0.2.0"\ndependencies={dependencies}\n[tool.uv.sources]\n{sources}\n'
        )
    return engine, consumer


def test_source_owned_provider_closure_preserves_transitive_topological_order(tmp_path: Path) -> None:
    engine, consumer = _provider_metadata(tmp_path)
    assert tuple(declared_local_dependencies(tmp_path, consumer)) == (engine,)
    assert local_dependency_closure(tmp_path, consumer) == ("root", engine)


def test_local_provider_cycles_and_private_paths_are_refused(tmp_path: Path) -> None:
    engine, consumer = _provider_metadata(tmp_path)
    project = tmp_path / "projects" / engine / "pyproject.toml"
    project.write_text(
        '[project]\nname="template-literature-meta-analysis"\nversion="0.2.0"\n'
        'dependencies=["template-advanced-literature-review==0.2.0"]\n'
        "[tool.uv.sources]\n"
        'template-advanced-literature-review={path="../template_advanced_literature_review",editable=true}\n'
    )
    with pytest.raises(ValueError, match="cycle"):
        local_dependency_closure(tmp_path, consumer)
    project.write_text(
        project.read_text().replace("../template_advanced_literature_review", "../../working/private_fixture")
    )
    with pytest.raises(ValueError, match="outside canonical public scope"):
        local_dependency_closure(tmp_path, consumer)


@pytest.mark.parametrize("mutated", [False, True])
def test_actual_namespaced_engine_wheel_is_consumed_and_bound(tmp_path: Path, mutated: bool) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    requirement, wheel, members = _wheel(
        root, content=b"from installed_engine import measured_value\nCOMPUTED=measured_value()\n"
    )
    # This invented1.0.0 package proves generic provider byte custody.
    # Canonical Meta's authored resource/default replay belongs to its genuine
    # installed cell and the dedicated mandatory-resource reader controls.
    engine, engine_wheel, _ = _wheel(
        root,
        scope="templates/template_prose_project",
        module="installed_engine",
        distribution="installed-engine",
    )
    targets, engine_members = inspect_wheel(root, engine, engine_wheel)
    environment = tmp_path / "environment"
    uv = shutil.which("uv")
    assert uv is not None
    commands = [
        (uv, "venv", "--no-project", "--no-python-downloads", "--python", sys.executable, str(environment)),
        (
            uv,
            "pip",
            "install",
            "--offline",
            "--no-config",
            "--no-deps",
            "--python",
            str(environment / "bin/python"),
            str(engine_wheel),
            str(wheel),
        ),
    ]
    for index, command in enumerate(commands):
        result = run_project_test_matrix(
            [
                ProjectTestTask(
                    index,
                    "actual-engine-wheel",
                    command,
                    tmp_path,
                    _environment(Path(sys.executable), tmp_path),
                    30,
                    True,
                )
            ]
        )[0]
        assert result.returncode == 0 and not result.timed_out, result.output_tail
    if mutated:
        site = next((environment / "lib").glob("python*/site-packages"))
        (site / "installed_engine/__init__.py").write_text("def measured_value():\n    return 99\n")
    provider = {
        "scope": engine.scope,
        "package": engine.package,
        "version": engine.version,
        "targets": list(targets),
        "wheel_members": engine_members,
        "wheel_artifact": {"path": engine_wheel.name, "sha256": hashlib.sha256(engine_wheel.read_bytes()).hexdigest()},
    }
    observed, observation = _probe(environment, requirement, root, members, tmp_path / "outside", [provider])
    if mutated:
        assert observed.returncode != 0 and "installed bytes differ" in observed.output_tail
        assert not observation.exists()
    else:
        assert observed.returncode == 0 and not observed.timed_out, observed.output_tail
        payload = json.loads(observation.read_text())
        assert payload["dependency_providers"][0]["imported_modules"] == ["installed_engine"]
        measured = subprocess.run(
            [
                str(environment / "bin/python"),
                "-I",
                "-c",
                "import installed_example; print(installed_example.COMPUTED)",
            ],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert measured.returncode == 0 and measured.stdout == "17\n"
        # Exercise the production installer twice with one immutable original
        # provider artifact. These are two disposable consuming cells, not a
        # complete installed acceptance matrix or a synthetic passing receipt.
        from typing import Any

        from infrastructure.project.installed_acceptance_runtime import install_runtime
        from infrastructure.project.installed_acceptance_validation import _cell
        from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
        from infrastructure.reporting.required_candidate_transport import _graph_paths

        (root / "pyproject.toml").write_text(
            '[project]\nname="research-project-template"\nversion="4.0.1"\nrequires-python=">=3.12"\n'
        )
        (root / "projects" / engine.scope / "pyproject.toml").write_text(
            '[project]\nname="installed-engine"\nversion="1.0.0"\nrequires-python=">=3.12"\ndependencies=[]\n'
        )
        consumer = root / "projects" / requirement.scope
        (consumer / "pyproject.toml").write_text(
            '[project]\nname="installed-example"\nversion="1.0.0"\nrequires-python=">=3.12"\n'
            'dependencies=["installed-engine==1.0.0"]\n'
            '[tool.uv.sources]\ninstalled-engine={path="../template_prose_project"}\n'
        )
        deadline = time.monotonic() + 120
        lock_directory = root / "output/readiness/shared-provider-lock"
        _run(
            (
                uv,
                "lock",
                "--directory",
                str(consumer),
                "--offline",
                "--no-python-downloads",
                "--python",
                sys.executable,
            ),
            tmp_path,
            _environment(Path(sys.executable), tmp_path),
            deadline,
            root,
            lock_directory,
            "genuine-fixture-lock",
        )
        provider_binding = write_binary(
            root, root / "output/readiness/shared-provider-origin" / engine_wheel.name, engine_wheel.read_bytes()
        )
        original_binding = dict(provider_binding)
        original_provider = root / provider_binding["path"]
        provider_content = original_provider.read_bytes()
        cells = []
        private_providers = []
        returned_bindings = []
        observed_bindings = []
        cell_directories = []
        private_consumers = []
        python_prefixes = []
        raw_prefixes = []
        for label in ("consumer-one", "consumer-two"):
            scratch = tmp_path / label
            scratch.mkdir(mode=0o700)
            directory = root / "output/readiness/shared-provider-cells" / label
            metadata = freeze_locked_metadata(root, scratch)
            admitted_consumer = freeze_wheel_bytes(root, requirement, wheel.read_bytes(), scratch, wheel.name)
            assert admitted_consumer.path.is_relative_to(scratch / "admitted-wheels")
            assert admitted_consumer.path.read_bytes() == wheel.read_bytes()
            assert stat.S_IMODE(admitted_consumer.path.stat().st_mode) == 0o400
            assert admitted_consumer.path.stat().st_nlink == 1
            private_consumers.append(admitted_consumer.path)
            runtime_environment = _environment(Path(sys.executable), scratch)

            def run(command: tuple[str, ...], operation: str) -> dict[str, Any]:
                return _run(command, scratch, runtime_environment, deadline, root, directory, operation)

            python, details = install_runtime(
                root,
                requirement,
                scratch,
                directory,
                Path(sys.executable),
                admitted_consumer,
                uv,
                run,
                provider_wheels={engine.scope: (provider_binding, engine)},
                metadata=metadata,
            )
            assert provider_binding == original_binding
            assert len(details["providers"]) == 1
            returned_bindings.append(details["providers"][0]["wheel_artifact"])
            cell_directories.append(directory)
            private = list((scratch / "admitted-wheels").glob("*/" + engine_wheel.name))
            assert len(private) == 1
            private_provider = private[0]
            assert private_provider.read_bytes() == provider_content
            assert stat.S_IMODE(private_provider.stat().st_mode) == 0o400
            assert private_provider.stat().st_nlink == 1
            private_providers.append(private_provider)
            outside = tmp_path / (label + "-probe")
            actual, observation = _probe(
                python.parent.parent, requirement, root, members, outside, details["providers"]
            )
            assert actual.returncode == 0 and not actual.timed_out, actual.output_tail
            raw = json.loads(observation.read_bytes())
            python_prefix = python.parent.parent.resolve(strict=True)
            raw_prefix = Path(raw["prefix"])
            assert python_prefix.is_relative_to(scratch.resolve(strict=True))
            assert raw_prefix == python_prefix
            assert raw["interpreter"] == str(python)
            python_prefixes.append(python_prefix)
            raw_prefixes.append(raw_prefix)
            assert raw["dependency_providers"][0]["imported_modules"] == ["installed_engine"]
            observed_bindings.append(raw["dependency_providers"][0]["wheel_artifact"])
            run(
                (str(python), "-I", "-B", "-c", "import installed_example; assert installed_example.COMPUTED == 17"),
                "actual-provider-result",
            )

            def bound(filename: str, content: bytes) -> dict[str, str]:
                return write_binary(root, directory / filename, content)

            process = json.loads((outside / "process.json").read_bytes())
            cell = {
                "scope": requirement.scope,
                "python_version": raw["python_version"],
                "status": "pass",
                "details": {
                    **raw,
                    "wheel_artifact": bound(wheel.name, wheel.read_bytes()),
                    "runtime_artifact": bound("probe.json", observation.read_bytes()),
                    "process_artifact": bound("process.json", json.dumps(process).encode()),
                    "probe_spec_artifact": bound("spec.json", (outside / "spec.json").read_bytes()),
                    "probe_payload_artifact": bound(
                        "installed-probe-payload.py", (outside / "installed-probe-payload.py").read_bytes()
                    ),
                    "selected_interpreter_sha256": raw["interpreter_sha256"],
                    "command": process["command"],
                },
            }
            _cell(requirement, cell, SnapshotReader(root))
            cells.append(cell)
        # Keep both genuine install/probe/cell paths complete before checking
        # the new reuse contract, so the old implementation is a meaningful red.
        assert len({str(path) for path in private_consumers}) == 2
        assert len({(path.stat().st_dev, path.stat().st_ino) for path in private_consumers}) == 2
        assert len(set(python_prefixes)) == len(set(raw_prefixes)) == 2
        assert returned_bindings == [original_binding, original_binding]
        assert observed_bindings == [original_binding, original_binding]
        assert all(not (directory / engine_wheel.name).exists() for directory in cell_directories)
        assert len({str(path) for path in private_providers}) == 2
        assert len({(path.stat().st_dev, path.stat().st_ino) for path in private_providers}) == 2
        graph = write_binary(
            root,
            root / "output/readiness/shared-provider-diagnostic-graph.json",
            json.dumps(
                {"role": "diagnostic-fixture-only", "original_provider": original_binding, "cells": cells}
            ).encode(),
        )
        reader = SnapshotReader(root)
        paths = _graph_paths(root, graph["path"], reader, deadline=deadline)
        assert paths[original_binding["path"]] == original_binding["sha256"]
        assert sum(Path(path).name == engine_wheel.name for path in paths) == 1
        marker = tmp_path / "unexecuted-mutated-provider-startup"
        original_provider.write_bytes(_startup_marker_wheel(original_provider, marker))
        assert hashlib.sha256(original_provider.read_bytes()).hexdigest() != original_binding["sha256"]
        assert not reader.unchanged()
        refused = tmp_path / "third-admission"
        refused.mkdir(mode=0o700)
        with pytest.raises(ValueError, match="changed after its original admission"):
            admit_provider_wheel(root, engine, original_binding, refused)
        assert not (refused / "admitted-wheels").exists()
        with pytest.raises(ValueError, match="bytes differ from the verified binding"):
            _graph_paths(root, graph["path"], SnapshotReader(root), deadline=deadline)
        for cell in cells:
            with pytest.raises(ValueError, match="provider wheel differs from its bound bytes"):
                _cell(requirement, cell, SnapshotReader(root))
        assert all(path.read_bytes() == provider_content for path in private_providers)
        assert not marker.exists()


@pytest.mark.parametrize(
    "damage", ["none", "omitted-member", "changed-member", "changed-result", "outside-prefix", "changed-source"]
)
def test_meta_installed_replay_reader_binds_authored_fixture_and_normalized_result(tmp_path: Path, damage: str) -> None:
    from infrastructure.project.installed_acceptance_validation import _validate_meta_replay
    from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

    source = (
        Path(__file__).resolve().parents[3]
        / "projects/templates/template_literature_meta_analysis/src/deep_research/fixtures/recorded_report.json"
    )
    fixture = (
        tmp_path
        / "projects/templates/template_literature_meta_analysis/src/deep_research/fixtures/recorded_report.json"
    )
    fixture.parent.mkdir(parents=True)
    fixture.write_bytes(source.read_bytes())
    payload = json.loads(fixture.read_bytes())
    prefix = tmp_path / "installed"
    site = prefix / f"lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages"
    member = "template_literature_meta_analysis/deep_research/fixtures/recorded_report.json"
    digest = hashlib.sha256(fixture.read_bytes()).hexdigest()
    citations = [{"title": item.get("title"), "url": item.get("url")} for item in payload["citations"]]
    members = {member: digest}
    domain = {
        "fixture_path": str(site / member),
        "fixture_sha256": digest,
        "replay": {
            "provider": payload["provider"],
            "job_id": payload["job_id"],
            "status": payload["status"],
            "query": payload["request"]["query"],
            "output_text": payload["output_text"],
            "citations": citations,
            "citation_count": len(citations),
        },
    }
    if damage == "omitted-member":
        members.clear()
    elif damage == "changed-member":
        members[member] = "0" * 64
    elif damage == "changed-result":
        domain["replay"]["output_text"] = "unexecuted replacement report"
    elif damage == "outside-prefix":
        domain["fixture_path"] = str(tmp_path / member)
    elif damage == "changed-source":
        fixture.write_text(json.dumps({**payload, "output_text": "new authored report"}))
    if damage == "none":
        _validate_meta_replay(domain, prefix, site, members, SnapshotReader(tmp_path))
    else:
        with pytest.raises(ValueError, match="admitted authored fixture"):
            _validate_meta_replay(domain, prefix, site, members, SnapshotReader(tmp_path))
