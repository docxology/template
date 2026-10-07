"""Portable Root observations authenticated by the exact hosted artifact origin.

Legacy local readers retain physical filesystem/runtime checks. This versioned
contract retains actual producer observations and checks them against current
source and the independently verified same-run artifact byte inventory.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import re
import sys
import hashlib
import json

from infrastructure.core.implementation_custody import capture_implementation_custody, source_file_digest
from infrastructure.project.public_acceptance_evidence import bootstrap_command, runtime_identity
from infrastructure.project.public_root_case_contract import (
    _artifact,
    _json,
    _root_identity,
    _runtime_locations,
    _fresh_prefix,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.project.public_hosted_origin import HostedReadbackContext

SCHEMA = "template-root-portable-observation-v1"


def _providers(cases: list[dict[str, Any]], locations: dict[str, str]) -> dict[str, str]:
    origins: dict[str, str] = {}

    def walk(value: object) -> None:
        if isinstance(value, dict):
            if set(value) == {"scope", "path", "sha256"} and value["scope"] in {"runtime-site", "runtime-stdlib"}:
                scope, relative, expected = value["scope"], value["path"], value["sha256"]
                if (
                    not isinstance(relative, str)
                    or Path(relative).is_absolute()
                    or any(p in {"", ".", ".."} for p in relative.split("/"))
                ):
                    raise ValueError("portable provider path is not confined")
                choices = ("purelib", "platlib") if scope == "runtime-site" else ("stdlib",)
                observed = {
                    source_file_digest(Path(locations[key]) / relative)
                    for key in choices
                    if (Path(locations[key]) / relative).is_file()
                }
                if expected not in observed:
                    raise ValueError("original selected provider changed")
                identity = scope + ":" + relative
                if identity in origins and origins[identity] != expected:
                    raise ValueError("original provider has contradictory bytes")
                origins[identity] = expected
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(cases)
    return origins


def observe_origin(reader: SnapshotReader, census_spec: dict[str, Any], cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Observe actual producer bytes twice; never redistribute executable files."""
    import infrastructure

    implementation = capture_implementation_custody(fresh_pycache_prefix=_fresh_prefix())
    if implementation != census_spec["implementation"]:
        raise ValueError("original audited implementation changed before portable observation")
    return {
        "root": str(reader.root),
        "root_identity": _root_identity(reader.root),
        "platform": sys.platform,
        "runtime": runtime_identity(),
        "runtime_locations": _runtime_locations(),
        "implementation": implementation,
        "implementation_root": str(Path(infrastructure.__file__).absolute().parent),
        "provider_files": _providers(cases, _runtime_locations()),
    }


@dataclass(frozen=True)
class OriginContext:
    root: Path
    identity: list[int]
    platform: str
    runtime: dict[str, Any]
    locations: dict[str, str]
    implementation: dict[str, Any]
    implementation_root: Path
    providers: dict[str, str]

    def bootstrap(self, local_root: Path, module: str, *arguments: str) -> tuple[str, ...]:
        projected = tuple(
            str(self.root / Path(arg).relative_to(local_root))
            if Path(arg).is_absolute() and Path(arg).is_relative_to(local_root)
            else arg
            for arg in arguments
        )
        return bootstrap_command(
            Path(self.runtime["executable"]),
            local_root,
            module,
            *projected,
            command_root=self.root,
            implementation_root=self.implementation_root,
        )

    def provider(self, scope: str, relative: str, expected: str) -> None:
        if self.providers.get(scope + ":" + relative) != expected:
            raise ValueError("portable selected provider differs from original before/after observation")


def evidence_bindings(reader: SnapshotReader, roots: list[dict[str, str]]) -> list[dict[str, str]]:
    """Retain complete original closure; every byte must share one fixed owner."""
    found: dict[str, str] = {}

    def visit(binding: dict[str, str]) -> None:
        held = _artifact(reader, binding)
        if not held.relative.startswith("output/readiness/"):
            return
        if held.relative in found:
            if found[held.relative] != held.sha256:
                raise ValueError("portable closure has contradictory bytes")
            return
        found[held.relative] = held.sha256
        if held.relative.endswith(".json"):
            walk(_json(held))

    def walk(value: object) -> None:
        if isinstance(value, dict):
            if set(value) == {"path", "sha256"}:
                visit(value)
            if isinstance(value.get("artifact"), str) and isinstance(value.get("artifact_sha256"), str):
                visit({"path": value["artifact"], "sha256": value["artifact_sha256"]})
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    for binding in roots:
        visit(binding)
    return [{"path": path, "sha256": digest} for path, digest in sorted(found.items())]


def read_portable_runtime(reader: SnapshotReader, proof_binding: object, bundle_binding: object) -> dict[str, Any]:
    """Verify trusted hosted origin, then independently reconstruct original evidence."""
    from infrastructure.project.public_hosted_origin import authorize_root_evidence
    from infrastructure.project.public_root_runtime_readback import read_runtime_cohort

    proof = _json(_artifact(reader, proof_binding))
    bundle = _json(_artifact(reader, bundle_binding))
    if (
        set(proof) != {"schema_version", "spec_artifact", "before", "after"}
        or proof["schema_version"] != SCHEMA
        or proof["spec_artifact"] != bundle["spec_artifact"]
        or proof["before"] != proof["after"]
    ):
        raise ValueError("portable Root original before/after custody differs")
    if not isinstance(proof_binding, dict) or not isinstance(bundle_binding, dict):
        raise ValueError("portable Root requires exact original bound observations")
    bindings = evidence_bindings(reader, [proof_binding, bundle_binding])
    expected = reader.hosted_origin
    if not isinstance(expected, HostedReadbackContext):
        raise ValueError("portable Root needs authenticated external hosted handoff context")
    # Hold the manifest even on cache hits; a context cannot point at absent or changed bytes.
    _artifact(reader, expected.manifest_binding)
    if not reader.unchanged():
        raise ValueError("portable original closure changed before hosted authentication")
    authorization_key = hashlib.sha256(
        json.dumps(
            {
                "bindings": bindings,
                "manifest": expected.manifest_binding,
                "repository": expected.repository,
                "run_id": expected.run_id,
                "head_sha": expected.head_sha,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    origin = reader.hosted_origin_authorizations.get(authorization_key)
    if origin is None:
        origin = authorize_root_evidence(
            reader,
            bindings,
            manifest_binding=expected.manifest_binding,
            repository=expected.repository,
            run_id=expected.run_id,
            head_sha=expected.head_sha,
        )
        if not reader.unchanged():
            raise ValueError("portable hosted origin changed during original archive authentication")
        reader.hosted_origin_authorizations[authorization_key] = origin
    raw = proof["before"]
    names = {
        "root",
        "root_identity",
        "platform",
        "runtime",
        "runtime_locations",
        "implementation",
        "implementation_root",
        "provider_files",
    }
    if (
        not isinstance(raw, dict)
        or set(raw) != names
        or raw["platform"] != origin.platform
        or raw["runtime"]["python_version"] != origin.python_version
    ):
        raise ValueError("portable Root host/minor differs from fixed hosted owner")
    for path in (raw["root"], raw["implementation_root"], *raw["runtime_locations"].values()):
        if (
            not isinstance(path, str)
            or not Path(path).is_absolute()
            or ".." in Path(path).parts
            or "\\" in path
            or "\0" in path
        ):
            raise ValueError("portable origin locations must be exact absolute paths")
    if (
        not isinstance(raw["root_identity"], list)
        or len(raw["root_identity"]) != 2
        or any(type(item) is not int or item < 0 for item in raw["root_identity"])
    ):
        raise ValueError("portable physical origin observations are invalid")
    implementation = raw["implementation"]
    if (
        not isinstance(implementation, dict)
        or implementation.get("binding_kind") != "source-checkout"
        or implementation.get("bytecode_binding") != "fresh-owned-prefix"
        or not isinstance(implementation.get("files"), dict)
    ):
        raise ValueError("portable Root requires original audited checkout implementation")
    current_implementation = capture_implementation_custody()
    if implementation["files"] != current_implementation["files"]:
        raise ValueError("portable implementation inventory differs from current exact loaded SDK source")
    if not isinstance(raw["provider_files"], dict) or any(
        not isinstance(key, str) or not isinstance(value, str) or re.fullmatch("[0-9a-f]{64}", value) is None
        for key, value in raw["provider_files"].items()
    ):
        raise ValueError("portable provider observation inventory is invalid")
    context = OriginContext(
        Path(raw["root"]),
        raw["root_identity"],
        raw["platform"],
        raw["runtime"],
        raw["runtime_locations"],
        implementation,
        Path(raw["implementation_root"]),
        raw["provider_files"],
    )
    actual = read_runtime_cohort(reader, bundle, origin=context)
    if not reader.unchanged():
        raise ValueError("portable Root source or original bytes changed")
    return actual
