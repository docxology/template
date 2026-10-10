"""Portable complete-suite labels use current Source and preserved origin roles."""

from pathlib import Path

import pytest

from infrastructure.project.public_acceptance_cases import pytest_command
from infrastructure.project.public_acceptance_evidence import bootstrap_command
from infrastructure.reporting.native_project_domain import observe_native_project_domain
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def _root(tmp_path: Path) -> Path:
    root = tmp_path / "current"
    (root / "projects/templates/template_code_project").mkdir(parents=True)
    return root


def test_portable_pytest_reconstructs_root_and_sdk_without_reopening_origin(tmp_path: Path) -> None:
    root = _root(tmp_path)
    origin = tmp_path / "removed-original-source"
    sdk = tmp_path / "removed-original-sdk/infrastructure"
    directory = root / "output/readiness/native-suite"
    command = pytest_command(
        Path("/removed-runtime/bin/python3.14"),
        root,
        directory,
        "held-native-run",
        "templates/template_code_project",
        directory / "collection.json",
        directory / "collection-spec.json",
        ["tests/test_domain.py"],
        spec_sha256="a" * 64,
        collect=True,
        test_timeout=120,
        command_root=origin,
        implementation_root=sdk,
    )
    assert not origin.exists() and not sdk.exists()
    assert command[command.index("--root") + 1] == str(origin)
    assert command[command.index("--project-root") + 1] == str(origin / "projects/templates/template_code_project")
    assert command[command.index("--receipt") + 1] == str(origin / "output/readiness/native-suite/collection.json")
    assert repr(str(sdk.parent)) in command[3]
    assert "tests/test_domain.py" in command
    assert "--collect-only" in command and "--no-cov" in command
    assert "python_files=test_*.py *_test.py" in command


def test_portable_installed_provider_names_are_labels_with_exact_actual_arity(tmp_path: Path) -> None:
    root = _root(tmp_path)
    current = tmp_path / "current-runtime/lib/python3.14/site-packages/provider"
    original = Path("/removed-runtime/lib/python3.14/site-packages/provider")
    origin = tmp_path / "removed-original-source"
    command = bootstrap_command(
        Path("/removed-runtime/bin/python3.14"),
        root,
        "infrastructure.project.public_acceptance_pytest",
        audit_roots=(current,),
        command_root=origin,
        command_audit_roots=(original,),
    )
    assert str(original) in command[3]
    assert str(current) not in command[3]
    with pytest.raises(ValueError, match="arity"):
        bootstrap_command(
            Path("/removed-runtime/bin/python3.14"),
            root,
            "infrastructure.project.public_acceptance_pytest",
            audit_roots=(current,),
            command_root=origin,
            command_audit_roots=(),
        )


def test_declared_suite_cannot_begin_from_a_serialized_source_record(tmp_path: Path) -> None:
    root = _root(tmp_path)
    with pytest.raises(ValueError, match="genuine already-active Source owner"):
        observe_native_project_domain(
            {"status": "pass"},
            "templates/template_code_project",  # type: ignore[arg-type]
            root / "output/readiness/forged-native-suite",
            SnapshotReader(root),
            deadline=1.0,
            provider_wheels={},
        )
    assert not (root / "output").exists()
