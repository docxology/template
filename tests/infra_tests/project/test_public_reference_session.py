"""Genuine source DATA session controls; not installed-wheel acceptance."""

from __future__ import annotations

import json
import math
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

import pytest

import infrastructure
from infrastructure.core.project_paths import find_repo_root, resolve_project_root
from infrastructure.project.public_reference_git import native_git
from infrastructure.project.public_reference_session import ReferenceSession
from tests.infra_tests.project.test_public_reference import complete_reference as _complete_reference

complete_reference = _complete_reference
pytestmark = pytest.mark.timeout(1800)


def _environment(fixture: tuple[Path, str, str]) -> dict[str, str]:
    root, commit, source = fixture
    return {
        "TEMPLATE_PUBLIC_REFERENCE_ROOT": str(root),
        "TEMPLATE_PUBLIC_REFERENCE_COMMIT": commit,
        "TEMPLATE_PUBLIC_REFERENCE_FINGERPRINT": source,
    }


def test_real_bound_session_reuses_original_reference_and_rechecks_before_success(
    complete_reference: tuple[Path, str, str], tmp_path: Path
) -> None:
    environment = _environment(complete_reference)
    before = tuple(sys.path), infrastructure.__file__
    session = ReferenceSession(environment, timeout_seconds=300)
    reference = session.current()
    assert reference is not None and reference.root == complete_reference[0]
    original_deadline = session.deadline
    assert session.current() is reference and session.deadline == original_deadline
    assert session.current(explicit_root=reference.root) is reference
    with pytest.raises(ValueError, match="conflicts"):
        session.current(explicit_root=tmp_path)
    session.verify()
    from infrastructure.project.public_acceptance_auxiliary_reference import nominate_pipeline_reference
    from infrastructure.project.public_reference import reference_binding

    assert session.deadline is not None
    nominated_environment: dict[str, str] = {}
    nominated = nominate_pipeline_reference(
        reference.root, "templates/template_pitch_deck", nominated_environment, session.deadline
    )
    # The nomination binds the same original DATA triple through the pipeline key
    # family; it must not republish the native-origin claim.
    assert nominated is not None
    assert reference_binding(nominated_environment) == reference_binding(environment)
    nominated.verify_unchanged(deadline=session.deadline)
    assert nominate_pipeline_reference(tmp_path, "templates/template_code_project", {}, session.deadline) is None
    with pytest.raises(ValueError, match="conflicts"):
        nominate_pipeline_reference(
            reference.root,
            "templates/template_pitch_deck",
            dict(environment, TEMPLATE_PUBLIC_REFERENCE_FINGERPRINT="0" * 64),
            session.deadline,
        )
    with pytest.raises(ValueError, match="conflicts"):
        nominate_pipeline_reference(
            reference.root,
            "templates/template_pitch_deck",
            dict(environment, TEMPLATE_PUBLIC_REFERENCE_COMMIT="0" * 40),
            session.deadline,
        )
    assert session.deadline == original_deadline
    assert (tuple(sys.path), infrastructure.__file__) == before
    target = reference.root / "README.md"
    original = target.read_bytes()
    try:
        target.write_bytes(original + b"\nOwned source DATA mutation.\n")
        assert reference.read("README.md") == original
        with pytest.raises(ValueError, match="changed"):
            session.verify()
        with pytest.raises(ValueError, match="changed"):
            nominated.verify_unchanged(deadline=session.deadline)
    finally:
        target.write_bytes(original)


@pytest.mark.parametrize("change", ["remove", "replace"])
def test_real_admitted_binding_cannot_be_removed_or_replaced(
    complete_reference: tuple[Path, str, str], change: str
) -> None:
    environment = _environment(complete_reference)
    session = ReferenceSession(environment, timeout_seconds=300)
    assert session.current() is not None
    if change == "remove":
        environment.clear()
    else:
        environment["TEMPLATE_PUBLIC_REFERENCE_COMMIT"] = "a" * len(complete_reference[1])
    with pytest.raises(ValueError, match="binding changed"):
        session.verify()


def test_real_expired_admission_cannot_restart_its_original_clock(
    complete_reference: tuple[Path, str, str],
) -> None:
    session = ReferenceSession(_environment(complete_reference), timeout_seconds=0.000001)
    with pytest.raises(TimeoutError):
        session.current()
    original_deadline = session.deadline
    assert original_deadline is not None
    with pytest.raises(TimeoutError):
        session.current()
    assert session.deadline == original_deadline


@pytest.mark.parametrize("budget", [False, True, 0, -1, math.nan, math.inf, 14401])
def test_invalid_original_budget_is_refused(budget: float) -> None:
    with pytest.raises(ValueError, match="positive finite"):
        ReferenceSession({}, timeout_seconds=budget)


def test_unbound_development_and_partial_configuration_are_distinct() -> None:
    session = ReferenceSession({})
    assert session.current() is None
    session.verify()
    assert session.binding is None and session.deadline is None and session.reference is None
    with pytest.raises(ValueError, match="together"):
        ReferenceSession({"TEMPLATE_PUBLIC_REFERENCE_ROOT": "/owned-unresolved"}).current()


def test_admitted_tracked_paths_match_original_root_index_without_expanding_gitlink(
    complete_reference: tuple[Path, str, str],
) -> None:
    session = ReferenceSession(_environment(complete_reference), timeout_seconds=300)
    reference = session.current()
    assert reference is not None
    paths = session.tracked_paths(explicit_root=reference.root)
    assert paths is not None
    raw = native_git(reference.root, time.monotonic() + 30, "ls-files", "--stage", "-z")
    actual = tuple(sorted(row.split(b"\t", 1)[1].decode() for row in raw.split(b"\0") if row))
    assert paths == actual
    assert paths.count("infrastructure/steganography/kmyth") == 1
    assert not any(path.startswith("infrastructure/steganography/kmyth/") for path in paths)
    session.verify()
    assert ReferenceSession({}).tracked_paths() is None


def test_real_path_git_forgery_executes_but_bound_pitch_uses_original_admitted_counts(
    complete_reference: tuple[Path, str, str], tmp_path: Path
) -> None:
    """A real external shadow command cannot supply bound numerical facts."""
    root, _, _ = complete_reference
    binary = tmp_path / "bin"
    binary.mkdir()
    marker = tmp_path / "owned-git-was-executed"
    producer = tmp_path / "owned_git.py"
    producer.write_text(
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('actual owned Git command executed')\n"
        "print('infrastructure/core/invented_untested_count.py')\n",
        encoding="utf-8",
    )
    fake = binary / "git"
    fake.write_text(
        "#!/bin/sh\nexec " + shlex.quote(sys.executable) + " -I " + shlex.quote(str(producer)) + "\n",
        encoding="utf-8",
    )
    fake.chmod(0o700)
    environment = {**os.environ, **_environment(complete_reference), "PATH": str(binary) + os.pathsep + os.defpath}
    positive = subprocess.run(
        ["git", "ls-files", "infrastructure"],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert positive.returncode == 0 and positive.stdout.strip() == "infrastructure/core/invented_untested_count.py"
    assert marker.read_text() == "actual owned Git command executed"
    marker.unlink()
    # Use the selected SDK and actual own Source package; DATA never enters sys.path.
    project = resolve_project_root(find_repo_root(), "templates/template_pitch_deck")
    selected_sdk = Path(infrastructure.__file__).resolve(strict=True)
    program = (
        "import importlib.util,json,sys;from pathlib import Path;"
        f"sys.path.insert(0,{str(selected_sdk.parent.parent)!r});import infrastructure;"
        f"assert Path(infrastructure.__file__).resolve()==Path({str(selected_sdk)!r});"
        f"project=Path({str(project)!r});"
        "spec=importlib.util.spec_from_file_location('own_deck_bootstrap',project/'scripts/_bootstrap.py');"
        "assert spec is not None and spec.loader is not None;"
        "bootstrap=importlib.util.module_from_spec(spec);spec.loader.exec_module(bootstrap);"
        "bootstrap.bootstrap_project(project);"
        "from template_pitch_deck.infra_facts import build_infra_tokens,infra_subpackage_python_counts;"
        "from template_pitch_deck.paths import data_repo_root,reference_tracked_paths,verify_reference_inputs;"
        "root=data_repo_root(project);"
        f"assert root==Path({str(root)!r});"
        "tokens=build_infra_tokens(root);rows=infra_subpackage_python_counts(root);"
        "tracked=reference_tracked_paths(root);assert tracked is not None;"
        "assert not any(Path(entry).resolve().is_relative_to(root) for entry in sys.path);"
        "verify_reference_inputs();print(json.dumps({'tokens':tokens,'rows':rows,'tracked':tracked}));"
    )
    actual = subprocess.run(
        [sys.executable, "-I", "-c", program],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    assert actual.returncode == 0, actual.stderr or actual.stdout
    assert not marker.exists()
    observations = [json.loads(line) for line in actual.stdout.splitlines() if line.startswith("{")]
    assert len(observations) == 1
    observed = observations[0]
    raw = native_git(root, time.monotonic() + 30, "ls-files", "--stage", "-z")
    paths = tuple(sorted(row.split(b"\t", 1)[1].decode() for row in raw.split(b"\0") if row))
    assert tuple(observed["tracked"]) == paths
    expected_total = sum(path.startswith("infrastructure/") and path.endswith(".py") for path in paths)
    assert int(observed["tokens"]["INFRA_PYTHON_FILE_COUNT"]) == expected_total
    for package, count in observed["rows"]:
        expected = sum(path.startswith(f"infrastructure/{package}/") and path.endswith(".py") for path in paths)
        assert count == expected and count > 0
    assert (
        sum(count for _, count in observed["rows"]) + int(observed["tokens"]["INFRA_UNATTRIBUTED_FILE_COUNT"])
        == expected_total
    )
