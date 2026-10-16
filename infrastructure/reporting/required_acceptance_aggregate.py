"""Combine original required evidence; publish only independently passed candidates."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Sequence

from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.project.public_root_census_encoding import ENCODING_SCHEMAS, decode
from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.project.public_hosted_origin import HostedReadbackContext
from infrastructure.publishing.release_acceptance import RECEIPT_PATH, _checkout_revision
from infrastructure.reporting.readiness_receipts import SCHEMA_VERSION, source_fingerprint
from infrastructure.reporting.original_job_outcome import validate_auxiliary_receipt_closure
from infrastructure.reporting.release_readiness_profile import collect_profile, required_profile
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader
from infrastructure.reporting.native_format_joint_source import NativeReaderOperation
from infrastructure.reporting.required_candidate_transport import (
    RequiredCandidatePackingInputs,
    _pack_required_candidate_from_reader,
)

AUDIT_PATH = "output/readiness/aggregate-audit/receipt.json"
BUNDLE_PATH = "output/readiness/hosted-bundle"


def root_owned_projection(
    values: dict[tuple[str, str], dict[str, Any]], requirements: Sequence[Any]
) -> list[dict[str, Any]]:
    """Assign every literal cell once by source-owned host/minor, never status.

    Each input remains the original full audit, including blocked cells on other
    hosts. Policy and combined branch coverage have one fixed Linux 3.14 owner.
    Independent gate validators still require actual original native evidence.
    """
    targets = {(host, minor) for host in ("darwin", "linux") for minor in ("3.12", "3.13", "3.14")}
    if set(values) != targets:
        raise ValueError("Root aggregate requires all six exact owned targets")
    root_requirements = [item for item in requirements if item.kind == "root-case"]
    full = {item.id for item in root_requirements} | {"root:case-policy", "root:coverage"}
    projections = []
    observed: set[str] = set()
    for target in sorted(targets):
        value = values[target]
        if not isinstance(value.get("gates"), dict) or set(value["gates"]) != full:
            raise ValueError("Root original receipt omitted or invented required cells")
        owned = {item.id for item in root_requirements if (item.case_platform, item.python_version) == target}
        if target == ("linux", "3.14"):
            owned |= {"root:case-policy", "root:coverage"}
        if observed.intersection(owned):
            raise ValueError("Root owned cells overlap")
        observed |= owned
        projections.append({**value, "gates": {key: value["gates"][key] for key in sorted(owned)}})
    if observed != full:
        raise ValueError("Root owned cells are incomplete")
    return projections


def auxiliary_owned_projection(values: dict[str, dict[str, Any]], requirements: Sequence[Any]) -> list[dict[str, Any]]:
    """Fixed original Linux common/Darwin platform ownership, independent of status."""
    if set(values) != {"linux", "darwin"}:
        raise ValueError("auxiliary aggregate requires both fixed host owners")
    full = {
        item.id
        for item in requirements
        if item.kind in {"roster", "docs", "oracle", "platform", "transfer", "pipeline", "domain", "live"}
    }
    macos = {"root:macos:process", "root:macos:rendering"}
    if not macos.issubset(full) or "root:sandbox:transfer" not in full:
        raise ValueError("auxiliary source-owned profile lacks mandatory host/transfer obligations")
    if set(values["linux"].get("gates", {})) != full or set(values["darwin"].get("gates", {})) != macos:
        raise ValueError("auxiliary original owner omitted or invented source-owned gates")
    for value in values.values():
        validate_auxiliary_receipt_closure(value)
    return [
        {
            **values["linux"],
            "gates": {key: values["linux"]["gates"][key] for key in sorted(full - macos - {"root:sandbox:transfer"})},
        },
        {**values["darwin"], "gates": {key: values["darwin"]["gates"][key] for key in sorted(macos)}},
    ]


def _evidence_closure(reader: SnapshotReader, relative: str) -> dict[str, bytes]:
    """Follow exact public artifact bindings, excluding unrelated readiness outputs."""
    observed: dict[str, bytes] = {}

    def visit(path: str, expected: str | None = None) -> None:
        held = reader.read(path)
        if expected is not None and held.sha256 != expected:
            raise ValueError("bundle artifact differs from its original reference")
        if not Path(path).is_relative_to("output/readiness"):
            return  # Source remains in the exact checkout, never overwritten by transfer.
        if path in observed:
            return
        observed[path] = held.content
        if sum(len(content) for content in observed.values()) > 64 * 1024 * 1024:
            raise ValueError("complete acceptance exceeds the hosted archive byte ceiling")
        if path.endswith(".json"):
            payload = json.loads(held.content)
            if isinstance(payload, dict) and payload.get("schema_version") in ENCODING_SCHEMAS:
                payload = decode(payload)
            walk(payload)

    def walk(value: object) -> None:
        if isinstance(value, dict):
            if (
                set(value) in ({"path", "sha256"}, {"path", "sha256", "width_px", "height_px", "variance"})
                and isinstance(value.get("path"), str)
                and isinstance(value.get("sha256"), str)
            ):
                visit(value["path"], value["sha256"])
            if isinstance(value.get("artifact"), str) and isinstance(value.get("artifact_sha256"), str):
                visit(value["artifact"], value["artifact_sha256"])
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    visit(relative)
    return observed


def stage_passed_bundle(
    root: Path,
    *,
    revision: str,
    hosted_origin: HostedReadbackContext | None = None,
    native_operation: NativeReaderOperation | None = None,
) -> dict[str, Any]:
    """Stage only the source-bound, independently verified evidence closure."""
    root = root.resolve(strict=True)
    if not _exact_source(root, revision):
        raise ValueError("bundle requires clean exact-revision source")
    reader = SnapshotReader(root, hosted_origin=hosted_origin, native_operation=native_operation)
    receipt = reader.read(RECEIPT_PATH)
    if receipt.json_object().get("source_commit") != revision:
        raise ValueError("bundle receipt differs from its exact revision")
    evidence = collect_profile(root, root / RECEIPT_PATH, reader)
    if evidence.candidate_state != "pass":
        raise ValueError("incomplete candidate cannot be staged as required acceptance")
    return _stage_passed_bundle_from_reader(root, reader, receipt, revision=revision)


def _stage_passed_bundle_from_reader(
    root: Path, reader: SnapshotReader, receipt: ArtifactSnapshot, *, revision: str
) -> dict[str, Any]:
    """Stage bytes immediately within the caller's complete passing profile observation."""
    if (
        reader.root != root
        or receipt.relative != RECEIPT_PATH
        or reader.read(RECEIPT_PATH) is not receipt
        or receipt.json_object().get("source_commit") != revision
        or not reader.unchanged()
        or not _exact_source(root, revision)
    ):
        raise ValueError("bundle lost its exact source/receipt observation after full profile validation")
    operation = reader.native_operation
    if operation is not None:
        if not isinstance(operation, NativeReaderOperation):
            raise ValueError("bundle native context must be the genuinely held current reader")
        operation.verify(reader)
    content = _evidence_closure(reader, RECEIPT_PATH)
    destination = reader.public_path(BUNDLE_PATH)
    if destination.exists() or not reader.unchanged() or not _exact_source(root, revision):
        raise ValueError("bundle destination exists or original evidence changed")
    for relative, data in sorted(content.items()):
        atomic_write_bytes_confined(root, destination / relative, data)
    for relative, data in content.items():
        held = reader.read((Path(BUNDLE_PATH) / relative).as_posix())
        if held.sha256 != hashlib.sha256(data).hexdigest():
            raise ValueError("staged bundle readback differs from its original bytes")
    if not reader.unchanged() or not _exact_source(root, revision):
        raise ValueError("bundle source or evidence changed during readback")
    if operation is not None:
        operation.verify(reader)
    if not reader.unchanged():
        raise ValueError("bundle evidence changed during final native Source verification")
    return {"directory": BUNDLE_PATH, "receipt_sha256": receipt.sha256, "files": sorted(content)}


def _exact_source(root: Path, revision: str) -> bool:
    observed = subprocess.run(
        [
            "git",
            "--no-replace-objects",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "core.untrackedCache=false",
            "-c",
            "core.hooksPath=/dev/null",
            "-C",
            str(root),
            "status",
            "--porcelain",
            "--untracked-files=all",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
        env={
            "PATH": "/usr/bin:/bin",
            "LC_ALL": "C",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_NO_LAZY_FETCH": "1",
            "GIT_TERMINAL_PROMPT": "0",
        },
    )
    return observed.returncode == 0 and not observed.stdout.strip() and _checkout_revision(root) == revision


def merge_receipts(
    values: Sequence[dict[str, Any]], *, revision: str, fingerprint: str, version: str, required: set[str]
) -> dict[str, Any]:
    """Admit exact source-bound inventories without selecting a winner for duplicates."""
    if re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        raise ValueError("aggregate needs the exact Git revision")
    gates: dict[str, Any] = {}
    for value in values:
        if "auxiliary_workers" in value or "deadline_exhausted" in value:
            validate_auxiliary_receipt_closure(value)
        if (
            value.get("schema_version") != SCHEMA_VERSION
            or value.get("platform_version") != version
            or value.get("source_fingerprint") != fingerprint
            or value.get("roster") != list(PUBLIC_PROJECT_NAMES)
            or value.get("source_commit", revision) != revision
            or not isinstance(value.get("gates"), dict)
        ):
            raise ValueError("aggregate input is unsupported, source-stale or from another revision")
        incoming = value["gates"]
        if set(incoming) - required or set(incoming).intersection(gates):
            raise ValueError("aggregate refuses foreign or duplicate required gates")
        gates.update(incoming)
    return {
        "schema_version": SCHEMA_VERSION,
        "platform_version": version,
        "source_fingerprint": fingerprint,
        "source_commit": revision,
        "roster": list(PUBLIC_PROJECT_NAMES),
        "gates": gates,
    }


def produce_aggregate(
    root: Path,
    receipts: Sequence[str],
    *,
    revision: str,
    root_receipts: dict[tuple[str, str], str] | None = None,
    auxiliary_receipts: dict[str, str] | None = None,
    hosted_origin: HostedReadbackContext | None = None,
    native_operation: NativeReaderOperation | None = None,
    candidate_packing: RequiredCandidatePackingInputs | None = None,
    stage_bundle: bool = False,
) -> dict[str, Any]:
    """Read every supplied original receipt, then apply the complete strict profile.

    A missing gate remains unknown. Invalid evidence fails. Neither state creates
    the canonical candidate receipt. Readers retain responsibility for original
    process/runtime/artifact custody; this function never manufactures gate proof.
    """
    root = root.resolve(strict=True)
    if not _exact_source(root, revision):
        raise ValueError("aggregate requires clean exact-revision source bytes")
    if type(stage_bundle) is not bool or (
        candidate_packing is not None
        and (
            not isinstance(candidate_packing, RequiredCandidatePackingInputs)
            or not isinstance(native_operation, NativeReaderOperation)
            or not isinstance(hosted_origin, HostedReadbackContext)
        )
    ):
        raise ValueError("aggregate packing/staging requires explicit typed nominations and the held native reader")
    if native_operation is not None:
        if not isinstance(native_operation, NativeReaderOperation):
            raise ValueError("aggregate native context must be independently held current reader custody")
        native_operation.verify(SnapshotReader(root))
    roots = root_receipts or {}
    auxiliary = auxiliary_receipts or {}
    paths = [*receipts, *roots.values(), *auxiliary.values()]
    if len(set(paths)) != len(paths) or not paths:
        raise ValueError("aggregate needs unique original receipt paths")
    reader = SnapshotReader(root, hosted_origin=hosted_origin, native_operation=native_operation)
    fingerprint = source_fingerprint(root)
    requirements, faults = required_profile(root, reader, fingerprint)
    if not requirements:
        raise ValueError("source-owned required profile is unavailable")
    values = []
    for relative in receipts:
        path = Path(relative)
        if not path.is_relative_to("output/readiness") or relative in {AUDIT_PATH, RECEIPT_PATH}:
            raise ValueError("aggregate input must be original public readiness evidence")
        values.append(reader.read(relative).json_object())
    original_roots = {}
    for target, relative in roots.items():
        if not Path(relative).is_relative_to("output/readiness") or relative in {AUDIT_PATH, RECEIPT_PATH}:
            raise ValueError("Root aggregate requires original public readiness receipt paths")
        original_roots[target] = reader.read(relative).json_object()
    if original_roots:
        values.extend(root_owned_projection(original_roots, requirements))
    original_auxiliary: dict[str, dict[str, Any]] = {}
    for host, relative in auxiliary.items():
        if not Path(relative).is_relative_to("output/readiness") or relative in {AUDIT_PATH, RECEIPT_PATH}:
            raise ValueError("auxiliary aggregate requires original public readiness receipt paths")
        original_auxiliary[host] = reader.read(relative).json_object()
    if original_auxiliary:
        values.extend(auxiliary_owned_projection(original_auxiliary, requirements))
    payload = merge_receipts(
        values,
        revision=revision,
        fingerprint=fingerprint,
        version=requirements[0].platform_version,
        required={item.id for item in requirements},
    )
    if hosted_origin is not None:
        if hosted_origin.head_sha != revision:
            raise ValueError("hosted aggregate context differs from exact source SHA")
        payload["hosted_origin_artifact"] = hosted_origin.manifest_binding
    payload["original_receipts"] = [
        {"path": relative, "sha256": reader.read(relative).sha256} for relative in sorted(paths)
    ]
    if not reader.unchanged() or source_fingerprint(root) != fingerprint or not _exact_source(root, revision):
        raise ValueError("aggregate source/input changed during admission")
    if (root / AUDIT_PATH).exists() or (root / RECEIPT_PATH).exists():
        raise ValueError("aggregate refuses to replace an earlier evidence observation")
    audit = write_json(root, root / AUDIT_PATH, payload)
    checked_reader = SnapshotReader(root, hosted_origin=hosted_origin, native_operation=native_operation)
    evidence = collect_profile(root, root / AUDIT_PATH, checked_reader)
    state = evidence.candidate_state
    if faults or not reader.unchanged() or not checked_reader.unchanged() or source_fingerprint(root) != fingerprint:
        state = "fail"
    canonical = None
    result: dict[str, Any] = {}
    if state == "pass":
        canonical = write_json(root, root / RECEIPT_PATH, payload)
        if native_operation is not None:
            native_operation.verify(checked_reader)
        held_audit = checked_reader.read(AUDIT_PATH)
        held_canonical = checked_reader.read(RECEIPT_PATH)
        independent = SnapshotReader(root, hosted_origin=hosted_origin, native_operation=native_operation)
        if (
            held_canonical.content != held_audit.content
            or held_canonical.sha256 != held_audit.sha256
            or held_canonical.sha256 != canonical["sha256"]
        ):
            raise ValueError("canonical aggregate bytes differ from its completely validated audit")
        for consumed_reader in (reader, checked_reader):
            for held in tuple(consumed_reader.snapshots.values()):
                observed = independent.read(held.relative, max_bytes=max(1, len(held.content)))
                if (
                    observed.content != held.content
                    or observed.sha256 != held.sha256
                    or observed.identity != held.identity
                ):
                    raise ValueError("canonical aggregate independent closure readback differs from validated bytes")
        if (
            not reader.unchanged()
            or not checked_reader.unchanged()
            or not independent.unchanged()
            or source_fingerprint(root) != fingerprint
            or not _exact_source(root, revision)
        ):
            raise ValueError("canonical aggregate independent Source/evidence readback refused")
        if native_operation is not None:
            native_operation.verify(checked_reader)
            native_operation.verify(independent)
        if candidate_packing is not None:
            if native_operation is None or hosted_origin is None:
                raise ValueError("candidate packing lost its independently held native/hosted nominations")
            result["candidate_transport"] = _pack_required_candidate_from_reader(
                native_operation,
                checked_reader,
                held_canonical,
                packing_inputs=candidate_packing,
                hosted_origin=hosted_origin,
            )
        if stage_bundle:
            result["bundle"] = _stage_passed_bundle_from_reader(root, checked_reader, held_canonical, revision=revision)
        if (
            not reader.unchanged()
            or not checked_reader.unchanged()
            or source_fingerprint(root) != fingerprint
            or not _exact_source(root, revision)
        ):
            raise ValueError("aggregate source or consumed evidence changed during immediate packing/staging")
        if native_operation is not None:
            native_operation.verify(checked_reader)
        if not reader.unchanged() or not checked_reader.unchanged():
            raise ValueError("aggregate consumed evidence changed during final native Source verification")
    result.update(
        {
            "candidate_state": state,
            "audit": audit,
            "receipt": canonical,
            "issues": list(evidence.issues),
            "exit_code": {"pass": 0, "fail": 1, "blocked": 75, "unknown": 2}[state],
        }
    )
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--revision", required=True)
    parser.add_argument("--receipt", action="append", default=[])
    parser.add_argument("--root-receipt", action="append", default=[], metavar="HOST/MINOR=PATH")
    parser.add_argument("--auxiliary-receipt", action="append", default=[], metavar="HOST=PATH")
    parser.add_argument("--stage-bundle", action="store_true")
    parser.add_argument("--hosted-origin-manifest")
    parser.add_argument("--repository")
    parser.add_argument("--run-id", type=int)
    args = parser.parse_args(argv)
    try:
        roots = {}
        for value in args.root_receipt:
            target, separator, path = value.partition("=")
            parts = target.split("/")
            if not separator or len(parts) != 2 or tuple(parts) in roots:
                raise ValueError("Root receipt must name one unique HOST/MINOR=PATH")
            roots[tuple(parts)] = path
        auxiliary = {}
        for value in args.auxiliary_receipt:
            target, separator, path = value.partition("=")
            if not separator or target in auxiliary:
                raise ValueError("auxiliary receipt must name one unique HOST=PATH")
            auxiliary[target] = path
        hosted_origin = None
        if any(value is not None for value in (args.hosted_origin_manifest, args.repository, args.run_id)):
            if not all(value is not None for value in (args.hosted_origin_manifest, args.repository, args.run_id)):
                raise ValueError("hosted aggregate needs exact manifest/repository/run context")
            held = SnapshotReader(args.repo_root).read(args.hosted_origin_manifest)
            hosted_origin = HostedReadbackContext(
                {"path": held.relative, "sha256": held.sha256}, args.repository, args.run_id, args.revision
            )
        result = produce_aggregate(
            args.repo_root,
            args.receipt,
            revision=args.revision,
            root_receipts=roots,
            auxiliary_receipts=auxiliary,
            hosted_origin=hosted_origin,
            stage_bundle=args.stage_bundle,
        )
        print("required candidate acceptance: " + result["candidate_state"])
        for issue in result["issues"]:
            print(issue)
        if result["exit_code"] == 0 and args.stage_bundle:
            bundle = result["bundle"]
            print("receipt_sha256=" + bundle["receipt_sha256"])
        return int(result["exit_code"])
    except (OSError, ValueError, TypeError, KeyError, RuntimeError) as error:
        print("required aggregate refused: " + str(error))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
