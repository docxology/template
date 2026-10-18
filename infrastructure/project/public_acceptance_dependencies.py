"""Actual installed public providers consumed by source-suite pytest children."""

from __future__ import annotations

import importlib
import sys
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path
from typing import Any, Mapping

from packaging.utils import canonicalize_name
from packaging.requirements import Requirement as PackageRequirement

from infrastructure.core.implementation_custody import (
    MissingSelectedDistributionMetadata,
    capture_dependency_custody,
    source_file_bytes,
)
from infrastructure.project.installed_acceptance_artifacts import inspect_wheel_bytes, write_binary
from infrastructure.project.public_package_dependencies import declared_local_dependencies, local_dependency_closure
from infrastructure.reporting.release_readiness_profile import Requirement
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


class MissingRuntimeProvider(RuntimeError):
    """A declared source-suite dependency lacks its admitted actual installed wheel."""


def admit_runtime_providers(
    root: Path, scope: str, wheels: Mapping[str, Path], requirements: Mapping[str, Requirement], reader: SnapshotReader
) -> dict[str, Any]:
    """Bind exact current non-root providers from canonical source declarations."""
    providers = tuple(item for item in local_dependency_closure(root, scope, reader=reader) if item != "root")
    declarations: dict[str, list[PackageRequirement]] = {}
    for parent in (*providers, scope):
        for provider, declaration in declared_local_dependencies(root, parent, reader=reader).items():
            declarations.setdefault(provider, []).append(declaration)
    result = {}
    for provider in providers:
        if provider not in wheels:
            raise MissingRuntimeProvider(f"{provider} needs its current admitted installed provider wheel")
        requirement = requirements[f"{provider}:installed"]
        if any(
            canonicalize_name(item.name) != canonicalize_name(requirement.package)
            or not item.specifier.contains(requirement.version, prereleases=True)
            for item in declarations[provider]
        ):
            raise ValueError("runtime provider differs from its source-owned dependency constraint")
        wheel_path = wheels[provider].absolute()
        snapshot = reader.read(wheel_path.relative_to(root).as_posix())
        targets, _ = inspect_wheel_bytes(root, requirement, snapshot.content, reader=reader)
        if len(targets) != 1:
            raise ValueError("runtime provider needs one genuine namespaced package")
        result[provider] = {
            "package": requirement.package,
            "version": requirement.version,
            "wheel_artifact": {"path": snapshot.relative, "sha256": snapshot.sha256},
        }
    return result


def capture_runtime_providers(
    root: Path, providers: dict[str, Any], directory: Path, *, retain_metadata: bool
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Observe actual imports/distribution records in this selected pytest child."""
    if not sys.pycache_prefix:
        raise ValueError("runtime provider requires the launcher's fresh prefix")
    reader = SnapshotReader(root)
    custody: dict[str, Any] = {}
    artifacts: dict[str, Any] = {}
    for scope, provider in providers.items():
        artifact = provider["wheel_artifact"]
        wheel = reader.read(artifact["path"])
        if wheel.sha256 != artifact["sha256"]:
            raise ValueError("runtime provider wheel changed after admission")
        requirement = Requirement(
            f"{scope}:installed", "installed", scope, provider["version"], "", "", package=provider["package"]
        )
        targets, members = inspect_wheel_bytes(root, requirement, wheel.content, reader=reader)
        if len(targets) != 1:
            raise ValueError("runtime provider must be one declared canonical package")
        try:
            distribution(provider["package"])
        except PackageNotFoundError as exc:
            raise MissingRuntimeProvider(f"{scope} is not installed in the selected runtime") from exc
        module = importlib.import_module(targets[0])
        filename = getattr(module, "__file__", None)
        if not isinstance(filename, str) or Path(filename).name != "__init__.py":
            raise ValueError("runtime provider did not import its actual package")
        source_root = Path(filename).absolute().parent
        if source_root.is_relative_to(root):
            raise ValueError("source-suite provider must be the admitted installed distribution")
        try:
            observed = capture_dependency_custody(
                provider["package"], source_root, fresh_pycache_prefix=Path(sys.pycache_prefix)
            )
        except MissingSelectedDistributionMetadata as exc:
            raise MissingRuntimeProvider(f"{scope} is not installed in the selected runtime") from exc
        selected = observed.get("distribution")
        if (
            observed.get("binding_kind") != "installed-distribution"
            or not isinstance(selected, dict)
            or selected.get("version") != provider["version"]
        ):
            raise ValueError("runtime provider is not the intended installed distribution")
        expected = {
            name.removeprefix(targets[0] + "/"): digest
            for name, digest in members.items()
            if name.startswith(targets[0] + "/") and name.endswith(".py")
        }
        if selected.get("public_python") != expected:
            raise ValueError("actual runtime provider bytes differ from its admitted wheel")
        actual_members = selected.get("file_sha256", {})
        if any(actual_members.get(name) != digest for name, digest in members.items()):
            raise ValueError("actual runtime provider implementation/data differ from the admitted wheel")
        custody[scope] = observed
        if retain_metadata:
            installed = distribution(provider["package"])
            records = [str(item) for item in installed.files or () if str(item).endswith(".dist-info/RECORD")]
            if len(records) != 1:
                raise ValueError("runtime provider requires its actual selected RECORD")
            record = records[0]
            metadata = str(Path(record).parent / "METADATA")
            raw_metadata = source_file_bytes(Path(str(installed.locate_file(metadata))))
            raw_record = source_file_bytes(Path(str(installed.locate_file(record))))
            artifacts[scope] = {
                "metadata": write_binary(root, directory / scope / "METADATA", raw_metadata),
                "record": write_binary(root, directory / scope / "RECORD", raw_record),
            }
            if (
                artifacts[scope]["metadata"]["sha256"] != selected["metadata_sha256"]
                or artifacts[scope]["record"]["sha256"] != selected["record_sha256"]
            ):
                raise ValueError("actual provider metadata changed while copied for evidence")
    if not reader.unchanged():
        raise ValueError("admitted provider source or wheel changed during observation")
    return custody, artifacts


def runtime_provider_roots(root: Path, providers: dict[str, Any], interpreter: Path) -> tuple[Path, ...]:
    """Choose actual admitted provider namespaces before the selected child's imports."""
    reader = SnapshotReader(root)
    environment = interpreter.absolute().parent.parent
    sites = tuple(environment.glob("lib/python*/site-packages")) + (environment / "Lib/site-packages",)
    roots: list[Path] = []
    for scope, provider in providers.items():
        artifact = provider["wheel_artifact"]
        wheel = reader.read(artifact["path"])
        if wheel.sha256 != artifact["sha256"]:
            raise ValueError("provider wheel changed before audited child launch")
        requirement = Requirement(
            f"{scope}:installed", "installed", scope, provider["version"], "", "", package=provider["package"]
        )
        targets, _ = inspect_wheel_bytes(root, requirement, wheel.content, reader=reader)
        if len(targets) != 1:
            raise ValueError("provider launch requires its admitted canonical namespace")
        roots.extend(site / targets[0] for site in sites)
    if not reader.unchanged():
        raise ValueError("provider source or wheel changed before audited launch")
    return tuple(roots)


__all__ = ["MissingRuntimeProvider", "admit_runtime_providers", "capture_runtime_providers", "runtime_provider_roots"]
