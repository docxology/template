"""Actual original Root observations remain verifiable after physical relocation."""

from __future__ import annotations

import copy
import shutil
import json
import uuid
import sys
from pathlib import Path

import pytest

from infrastructure.project.public_root_case_contract import _artifact, _json
from infrastructure.project.public_root_portable import OriginContext, read_portable_runtime, evidence_bindings
from infrastructure.project.public_root_runtime_readback import read_runtime_cohort
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from tests.infra_tests.project import test_root_runtime_v2 as controls

pytestmark = [pytest.mark.slow, pytest.mark.timeout(1200)]


@pytest.fixture(scope="module")
def genuine_portable(tmp_path_factory):
    root, produced, _ = controls.genuine_runtime.__wrapped__(tmp_path_factory)
    proof_binding = produced["portable_artifact"]
    proof = _json(_artifact(SnapshotReader(root), proof_binding))
    assert proof["before"] == proof["after"]
    raw = proof["before"]
    context = OriginContext(
        Path(raw["root"]),
        raw["root_identity"],
        raw["platform"],
        raw["runtime"],
        raw["runtime_locations"],
        raw["implementation"],
        Path(raw["implementation_root"]),
        raw["provider_files"],
    )
    destination = tmp_path_factory.mktemp("relocated-root-evidence") / "root"
    shutil.copytree(root, destination)
    saved = root.with_name(root.name + "-original-unavailable")
    root.rename(saved)
    try:
        assert not root.exists()
        with pytest.raises(ValueError, match="specification"):
            read_runtime_cohort(SnapshotReader(destination), produced["bundle"])
        actual = read_runtime_cohort(SnapshotReader(destination), produced["bundle"], origin=context)
        assert actual["passed_counts"] == {"core": 2}
        assert actual["runtime"] == raw["runtime"]
        assert actual["platform"] == raw["platform"]
        # Retain real original bytes for a storage audit; this is a controlled
        # core cohort, never a complete production Root candidate.
        from infrastructure.core.files.secure_write import atomic_write_bytes_confined

        owner = Path(__file__).parents[3]
        retained = (
            owner
            / "output/readiness/root-portable-controls"
            / f"{sys.version_info.major}.{sys.version_info.minor}"
            / uuid.uuid4().hex
        )
        reader = SnapshotReader(destination)
        inventory = []
        for binding in evidence_bindings(reader, [proof_binding, produced["bundle_artifact"]]):
            held = reader.read(binding["path"])
            atomic_write_bytes_confined(owner, retained / binding["path"], held.content)
            inventory.append({**binding, "bytes": len(held.content)})
        atomic_write_bytes_confined(
            owner,
            retained / "inventory.json",
            json.dumps(
                {
                    "role": "original-controlled-core-cohort-storage-audit",
                    "original_root": str(root),
                    "files": inventory,
                    "total_bytes": sum(item["bytes"] for item in inventory),
                },
                sort_keys=True,
                indent=2,
            ).encode(),
        )
        yield destination, produced, context, proof_binding
    finally:
        saved.rename(root)


def test_genuine_original_process_census_cases_and_coverage_survive_origin_path_unavailability(genuine_portable):
    root, produced, context, proof_binding = genuine_portable
    actual = read_runtime_cohort(SnapshotReader(root), produced["bundle"], origin=context)
    assert actual["passed_counts"] == {"core": 2}
    bindings = evidence_bindings(SnapshotReader(root), [proof_binding, produced["bundle_artifact"]])
    assert any(binding["path"].endswith("census.json") for binding in bindings)
    assert any(binding["path"].endswith("coverage-data.json") for binding in bindings)
    assert any(binding["path"].endswith("process.json") for binding in bindings)


def test_portable_public_admission_requires_authenticated_handoff_context(genuine_portable):
    root, produced, _, proof_binding = genuine_portable
    with pytest.raises(ValueError, match="authenticated external"):
        read_portable_runtime(SnapshotReader(root), proof_binding, produced["bundle_artifact"])


@pytest.mark.parametrize("field", ["identity", "platform", "runtime", "providers"])
def test_portable_origin_cannot_replace_original_physical_runtime_host_or_provider_bytes(genuine_portable, field):
    root, produced, context, _ = genuine_portable
    values = copy.deepcopy(context.__dict__)
    if field == "identity":
        values[field][1] += 1
    elif field == "platform":
        values[field] = "linux" if context.platform == "darwin" else "darwin"
    elif field == "runtime":
        values[field]["interpreter_sha256"] = "0" * 64
    else:
        assert values[field], "genuine fixture providers must retain actual runtime sources"
        key = next(iter(values[field]))
        values[field][key] = "0" * 64
    with pytest.raises(ValueError):
        read_runtime_cohort(SnapshotReader(root), produced["bundle"], origin=OriginContext(**values))


def test_changed_hosted_context_binding_bytes_and_fresh_reader_cannot_reuse_origin_cache(genuine_portable):
    from infrastructure.project.public_hosted_origin import HostedReadbackContext
    import hashlib

    root, produced, _, proof_binding = genuine_portable
    manifest = root / "output/readiness/untrusted-control-origin.json"
    original = b'{"schema_version":"explicit-invalid-offline-control"}'
    manifest.write_bytes(original)
    binding = {"path": str(manifest.relative_to(root)), "sha256": hashlib.sha256(original).hexdigest()}
    context = HostedReadbackContext(binding, "example/public-template", 1, "f" * 40)
    reader = SnapshotReader(root, hosted_origin=context)
    with pytest.raises(ValueError, match="context mismatch"):
        read_portable_runtime(reader, proof_binding, produced["bundle_artifact"])
    assert reader.hosted_origin_authorizations == {}
    assert reader.public_path(binding["path"]) in reader.snapshots
    reader.hosted_origin = HostedReadbackContext(binding, "example/public-template", 2, "e" * 40)
    with pytest.raises(ValueError, match="context mismatch"):
        read_portable_runtime(reader, proof_binding, produced["bundle_artifact"])
    manifest.write_bytes(original + b"\n")
    with pytest.raises(ValueError, match="changed before hosted authentication"):
        read_portable_runtime(reader, proof_binding, produced["bundle_artifact"])
    fresh = SnapshotReader(root, hosted_origin=context)
    assert fresh.hosted_origin_authorizations == {} and fresh.snapshots == {}
    with pytest.raises(ValueError, match="hash changed"):
        read_portable_runtime(fresh, proof_binding, produced["bundle_artifact"])
    assert fresh.hosted_origin_authorizations == {}
    manifest.unlink()
