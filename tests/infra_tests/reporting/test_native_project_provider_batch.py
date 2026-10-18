"""Real complete Git Source controls for preimport provider batching.

These controls use the production Source admission factory and the existing
owned complete-public-source fixture. They do not grant installed acceptance.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Iterator, Mapping
from pathlib import Path
from uuid import uuid4

import pytest

import infrastructure
from infrastructure.core.implementation_custody import capture_implementation_custody
from infrastructure.project.copy_exemplar import export_exemplar
from infrastructure.project.public_acceptance_dependencies import MissingRuntimeProvider
from infrastructure.project.public_package_dependencies import local_dependency_closure
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.native_project_provider_batch import admitted_native_provider_batch
from infrastructure.reporting.native_format_joint_source import admitted_native_providers
from infrastructure.reporting.native_source_external_admission import (
    NativeExternalSourceBindings,
    NativeSourceContext,
    admit_external_native_source,
    _anchored_directory_identity,
    _verify_source_directory_identities,
)
from tests.infra_tests.project.test_public_reference import (
    _clone_complete_reference,
    complete_reference as complete_reference,
)

pytestmark = pytest.mark.timeout(1800)


@pytest.mark.parametrize("control", ("search-only", "symlink", "replacement"))
def test_native_directory_identity_keeps_confined_search_only_witnesses(tmp_path: Path, control: str) -> None:
    directory = tmp_path.resolve() / "runner"
    directory.mkdir()
    deadline = time.monotonic() + 30
    expected = directory.stat().st_dev, directory.stat().st_ino
    assert _anchored_directory_identity(directory, deadline) == expected
    if control == "search-only":
        directory.chmod(0o111)
        try:
            if os.geteuid() != 0:
                with pytest.raises(PermissionError):
                    tuple(directory.iterdir())
            if hasattr(os, "O_PATH") or os.geteuid() == 0:
                assert _anchored_directory_identity(directory, deadline) == expected
                _verify_source_directory_identities(((directory, expected),), deadline)
            else:
                # Platforms without search-only descriptors retain the
                # existing readable-directory fallback and fail closed.
                with pytest.raises(ValueError):
                    _anchored_directory_identity(directory, deadline)
            assert directory.stat().st_mode & 0o777 == 0o111
        finally:
            directory.chmod(0o700)
    elif control == "symlink":
        alias = directory.with_name("runner-alias")
        alias.symlink_to(directory, target_is_directory=True)
        with pytest.raises(ValueError, match="aliased locator"):
            _anchored_directory_identity(alias, deadline)
    else:
        directory.rename(directory.with_name("runner-original"))
        directory.mkdir()
        with pytest.raises(ValueError, match="physically replaced"):
            _verify_source_directory_identities(((directory, expected),), deadline)


class _ABANominations(Mapping[str, Path]):
    """An external nomination input mutates owned DATA during enumeration.

    No application function is substituted. Iteration is deliberately hostile
    input behavior at the production Mapping boundary, after opening custody.
    """

    def __init__(self, target: Path, entries: Mapping[str, Path]) -> None:
        self.target = target
        self.entries = dict(entries)
        self.mutated = False

    def __iter__(self) -> Iterator[str]:
        if not self.mutated:
            original = self.target.read_bytes()
            try:
                self.target.write_bytes(original + b"\nOwned nomination ABA control.\n")
            finally:
                self.target.write_bytes(original)
            self.mutated = True
        return iter(self.entries)

    def __len__(self) -> int:
        return len(self.entries)

    def __getitem__(self, key: str) -> Path:
        return self.entries[key]


def test_genuine_batch_matches_single_factories_and_refuses_changed_source(
    complete_reference: tuple[Path, str, str], tmp_path: Path
) -> None:
    """One real admitted mirror covers selection, input refusal and mutation.

    Keep the final mutation in this same case: a restored file still invalidates
    held custody, so no later test may accidentally reuse this Source context.
    The two complete owned trees require roughly twice the public source size.
    """
    original, commit, fingerprint = complete_reference
    deadline = time.monotonic() + 1200
    mirror = _clone_complete_reference(complete_reference, tmp_path / "current-full-git-mirror", deadline=deadline)
    selected_sdk = Path(infrastructure.__file__).absolute().parent
    metadata = mirror.stat()

    def admit_context() -> NativeSourceContext:
        return admit_external_native_source(
            NativeExternalSourceBindings(
                original,
                commit,
                fingerprint,
                mirror,
                (metadata.st_dev, metadata.st_ino),
                selected_sdk,
                json.dumps(capture_implementation_custody(), sort_keys=True).encode(),
                uuid4().hex,
            ),
            deadline=deadline,
        )

    context = admit_context()
    interpreter = Path(sys.executable)
    reader = context.current_source_reader
    independent = tuple(
        scope
        for scope in PUBLIC_PROJECT_NAMES
        if not any(provider != "root" for provider in local_dependency_closure(mirror, scope, reader=reader))
    )
    assert independent, "The genuine public roster must contain an independent no-provider scope"
    consumer = "templates/template_advanced_literature_review"
    meta = "templates/template_literature_meta_analysis"
    scopes = independent[0], consumer
    scratch = tmp_path / "meta-build"
    scratch.mkdir()
    evidence = mirror / "output/readiness/provider-batch-control"
    source = scratch / "template_literature_meta_analysis"
    # The complete fixture can commit existing root egg-info's five runtime
    # records (PKG-INFO, SOURCES.txt, dependency_links.txt, requires.txt and
    # top_level.txt). The canonical copier omits installation metadata. This
    # test exercises provider wheel admission, not the full archive contract;
    # every wheel code/data byte still passes genuine Source inspection.
    export_exemplar(mirror, meta, source, deadline_monotonic=deadline)
    wheel_directory = evidence / "wheels"
    uv = shutil.which("uv")
    assert uv is not None
    built = subprocess.run(
        [
            uv,
            "build",
            "--wheel",
            "--offline",
            "--no-config",
            "--no-python-downloads",
            "--no-build-isolation",
            "--python",
            str(interpreter),
            "--out-dir",
            str(wheel_directory),
            str(source),
        ],
        cwd=scratch,
        capture_output=True,
        timeout=120,
        check=False,
    )
    assert built.returncode == 0, built.stderr.decode(errors="replace")
    actual_wheels = tuple(wheel_directory.glob("*.whl"))
    assert len(actual_wheels) == 1
    nominations = {meta: actual_wheels[0]}
    expected = {
        scope: admitted_native_providers(context, scope, nominations, interpreter, deadline=deadline)
        for scope in scopes
    }
    assert expected[independent[0]] == ({}, ())
    assert set(expected[consumer][0]) == {meta}
    assert expected[consumer][1] and all(
        path.name == "template_literature_meta_analysis" for path in expected[consumer][1]
    )
    assert admitted_native_provider_batch(context, scopes, nominations, interpreter, deadline=deadline) == expected
    # The first scope succeeds, but the later genuine dependency has no wheel.
    # No partial result may escape the batch when that later admission fails.
    with pytest.raises(MissingRuntimeProvider):
        admitted_native_provider_batch(context, scopes, {}, interpreter, deadline=deadline)

    for invalid in (
        (),
        (scopes[0], scopes[0]),
        ("root",),
        ("working/untrusted",),
        (PUBLIC_PROJECT_NAMES[0] + "-other",),
    ):
        with pytest.raises(ValueError, match="distinct public scopes"):
            admitted_native_provider_batch(context, invalid, {}, interpreter, deadline=deadline)
    with pytest.raises(ValueError, match="distinct public scopes"):
        admitted_native_provider_batch(context, list(scopes), {}, interpreter, deadline=deadline)  # type: ignore[arg-type]
    with pytest.raises(TimeoutError):
        admitted_native_provider_batch(context, scopes, {}, interpreter, deadline=time.monotonic() - 1)

    target = mirror / "README.md"
    original_bytes = target.read_bytes()
    try:
        target.write_bytes(original_bytes + b"\nOwned changed Source negative control.\n")
        assert not reader.unchanged()
        with pytest.raises(ValueError):
            admitted_native_provider_batch(context, scopes, {}, interpreter, deadline=deadline)
    finally:
        target.write_bytes(original_bytes)
    assert original.joinpath("README.md").read_bytes() == original_bytes
    # Restoring bytes cannot restore held inode/mtime/ctime custody. A fresh
    # production admission is needed before each separate mid-batch ABA.
    context = admit_context()
    wheel = actual_wheels[0]
    wheel_bytes = wheel.read_bytes()
    context.current_source_reader.read(wheel.relative_to(mirror).as_posix())
    hostile_wheel = _ABANominations(wheel, nominations)
    with pytest.raises(ValueError):
        admitted_native_provider_batch(context, scopes, hostile_wheel, interpreter, deadline=deadline)
    assert hostile_wheel.mutated and wheel.read_bytes() == wheel_bytes
    assert not context.current_source_reader.unchanged()

    context = admit_context()
    hostile = _ABANominations(target, nominations)
    with pytest.raises(ValueError):
        admitted_native_provider_batch(context, scopes, hostile, interpreter, deadline=deadline)
    assert hostile.mutated and target.read_bytes() == original_bytes
    assert not context.current_source_reader.unchanged()
    assert original.joinpath("README.md").read_bytes() == original_bytes


def test_provider_batch_refuses_context_free_inputs_without_source_authority(tmp_path: Path) -> None:
    """Invalid objects never become Source by satisfying a structural interface."""
    for invalid in (None, object()):
        with pytest.raises(ValueError, match="genuine Source"):
            admitted_native_provider_batch(
                invalid,  # type: ignore[arg-type]
                (PUBLIC_PROJECT_NAMES[0],),
                {},
                tmp_path / "python",
                deadline=time.monotonic() + 60,
            )
