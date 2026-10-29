"""Locked dependency installation without editable/source provider substitution."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from packaging.requirements import Requirement as PackageRequirement

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.core.pipeline.fingerprints import tree_records
from infrastructure.project.installed_acceptance_artifacts import AdmittedWheel, admit_provider_wheel, write_binary
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.project.locked_dependency_export import normalize_locked_dependency_export
from infrastructure.project.public_package_dependencies import declared_local_dependencies, local_dependency_closure
from infrastructure.reporting.release_readiness_profile import Requirement
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


class MissingProviderWheel(RuntimeError):
    """A declared public dependency needs its actual admitted candidate wheel."""


@dataclass(frozen=True)
class LockedMetadata:
    """Private read-only metadata tree retaining the canonical resolver layout."""

    root: Path
    records: tuple[tuple[str, str, str], ...]

    def unchanged(self) -> bool:
        """Recheck the exact metadata consumed by each locked export."""
        return tree_records(self.root, source=True) == self.records


def freeze_locked_metadata(root: Path, scratch: Path) -> LockedMetadata:
    """Snapshot canonical metadata before child tools can consume mutable paths.

    Project path resolvers keep their original three-level layout, including
    sibling declarations. Source packages are never installed from this tree.
    """
    reader = SnapshotReader(root)
    destination = scratch / "locked-metadata"
    destination.mkdir()
    for base in (Path(), *(Path("projects") / scope for scope in PUBLIC_PROJECT_NAMES)):
        for filename in ("pyproject.toml", "uv.lock", ".python-version"):
            relative = (base / filename).as_posix()
            if not (root / relative).exists():
                continue
            snapshot = reader.read(relative)
            atomic_write_bytes_confined(destination, destination / relative, snapshot.content, mode=0o400)
    if not reader.unchanged():
        raise ValueError("locked metadata changed while its private snapshot was captured")
    for directory in sorted(
        (path for path in destination.rglob("*") if path.is_dir()), key=lambda path: len(path.parts), reverse=True
    ):
        directory.chmod(0o500)
    destination.chmod(0o500)
    return LockedMetadata(destination, tree_records(destination, source=True))


def install_admitted_wheels(
    scratch: Path,
    python: Path,
    uv: str,
    wheels: list[AdmittedWheel],
    run: Callable[[tuple[str, ...], str], Any],
) -> None:
    """Enforce original admitted hashes when uv consumes private wheel copies."""
    if not wheels:
        raise ValueError("installed execution requires at least one admitted wheel")
    requirements = scratch / "admitted-wheel-requirements.txt"
    lines = []
    for wheel in wheels:
        if not wheel.path.absolute().is_relative_to(scratch.absolute() / "admitted-wheels"):
            raise ValueError("installation wheel is outside private admitted custody")
        lines.append(f"{wheel.package} @ {wheel.path.absolute().as_uri()} --hash=sha256:{wheel.sha256}\n")
    atomic_write_bytes_confined(scratch, requirements, "".join(lines).encode(), mode=0o400)
    run(
        (
            uv,
            "pip",
            "install",
            "--offline",
            "--no-config",
            "--no-deps",
            "--no-build",
            "--require-hashes",
            "--python",
            str(python),
            "--requirements",
            str(requirements),
        ),
        "wheel-install",
    )


def install_runtime(
    root: Path,
    requirement: Requirement,
    scratch: Path,
    directory: Path,
    interpreter: Path,
    wheel: AdmittedWheel,
    uv: str,
    run: Callable[[tuple[str, ...], str], Any],
    *,
    provider_wheels: dict[str, tuple[dict[str, str], Requirement]],
    metadata: LockedMetadata,
) -> tuple[Path, dict[str, Any]]:
    """Use exact locked transitives, then install genuine wheels with no dependencies.

    The local root resolver in exemplar metadata is a checkout convenience.
    Exporting only dependency requirements from that canonical source retains
    its lock and transitive pins while excluding local source installations.
    Declared public dependencies are supplied by separately admitted wheels.
    """
    providers: list[dict[str, Any]] = []
    if not metadata.unchanged():
        raise ValueError("private locked metadata changed before dependency export")
    scopes = local_dependency_closure(metadata.root, requirement.scope)
    declarations: dict[str, list[PackageRequirement]] = {}
    for parent in (*scopes, requirement.scope):
        for provider_scope, declaration in declared_local_dependencies(metadata.root, parent).items():
            declarations.setdefault(provider_scope, []).append(declaration)
    wheels: list[AdmittedWheel] = []
    for scope in scopes:
        if scope not in provider_wheels:
            raise MissingProviderWheel(f"declared {scope} dependency needs its current admitted wheel")
        wheel_artifact, provider_requirement = provider_wheels[scope]
        if (
            any(
                provider_requirement.package.lower().replace("_", "-") != declaration.name.lower().replace("_", "-")
                or not declaration.specifier.contains(provider_requirement.version, prereleases=True)
                for declaration in declarations[scope]
            )
            or scope == "root"
            and provider_requirement.version != requirement.platform_version
        ):
            raise ValueError("installed provider wheel differs from its declared package/version")
        admitted = admit_provider_wheel(root, provider_requirement, wheel_artifact, scratch)
        providers.append(
            {
                "scope": scope,
                "wheel_artifact": dict(wheel_artifact),
                "targets": admitted.targets,
                "wheel_members": admitted.members,
                "package": provider_requirement.package,
                "version": provider_requirement.version,
            }
        )
        wheels.append(admitted)
    metadata_root = metadata.root if requirement.scope == "root" else metadata.root / "projects" / requirement.scope
    dependencies = scratch / "runtime-requirements.txt"
    run(
        (
            uv,
            "export",
            "--directory",
            str(metadata_root),
            "--locked",
            "--offline",
            "--no-default-groups",
            "--no-emit-project",
            "--no-emit-local",
            "--no-header",
            "--no-annotate",
            "--output-file",
            str(dependencies),
        ),
        "runtime-lock",
    )
    normalize_locked_dependency_export(metadata_root, dependencies, minor=requirement.python_version or None)
    if not metadata.unchanged():
        raise ValueError("private locked metadata changed during dependency export")
    write_binary(root, directory / dependencies.name, dependencies.read_bytes())
    environment = scratch / "installed-environment"
    run(
        (uv, "venv", "--no-project", "--no-python-downloads", "--python", str(interpreter), str(environment)),
        "runtime-venv",
    )
    python = environment / "bin/python"
    run(
        (
            uv,
            "pip",
            "sync",
            "--offline",
            "--no-config",
            "--no-build",
            "--require-hashes",
            "--allow-empty-requirements",
            "--python",
            str(python),
            str(dependencies),
        ),
        "runtime-dependencies",
    )
    wheels.append(wheel)
    install_admitted_wheels(scratch, python, uv, wheels, run)
    run((uv, "pip", "check", "--python", str(python)), "installed-dependency-check")
    return python, {"providers": providers}
