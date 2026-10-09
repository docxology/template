"""Admit hosted, source-bound required acceptance before root 4+ publication.

The caller retrieves only fixed GitHub API endpoints after input admission.
Downloaded evidence stays under the ignored public readiness directory. A
successful upload/run establishes custody; the existing readiness validators
still decide whether every required candidate case is supported.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any, Sequence

from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined
from infrastructure.publishing.root_release_contract import root_package_version
from infrastructure.project.public_hosted_origin import HostedReadbackContext, WORKFLOW
from infrastructure.reporting.release_readiness_artifacts import bounded_members
from infrastructure.reporting.release_readiness_profile import collect_profile
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader, json_object_from_bytes

ARTIFACT_NAME = "platform-required-acceptance"
RECEIPT_PATH = "output/readiness/release-candidate/receipt.json"
_POSITIVE_ID = re.compile(r"[1-9][0-9]{0,18}")
_REVISION = re.compile(r"[0-9a-f]{40}")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")


class MissingAcceptanceHandoff(ValueError):
    """The breaking platform release has no explicit accepted-evidence handoff."""


def positive_id(value: str) -> int:
    """Admit a canonical finite positive GitHub identifier, never endpoint text."""
    if not isinstance(value, str) or _POSITIVE_ID.fullmatch(value) is None or int(value) > 2**63 - 1:
        raise ValueError("acceptance IDs must be canonical positive integers")
    return int(value)


def validate_handoff_inputs(root: Path, run_id: str, artifact_id: str, receipt_sha256: str) -> bool:
    """Require an explicit evidence handoff for root platform major versions 4+."""
    version = root_package_version(root)
    match = re.fullmatch(r"(0|[1-9][0-9]*)\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?", version)
    if match is None:
        raise ValueError("root release version must have an unambiguous semantic major")
    if int(match.group(1)) < 4:
        return False
    if not all((run_id, artifact_id, receipt_sha256)):
        raise MissingAcceptanceHandoff("root 4+ release requires a run, artifact, and exact receipt SHA256")
    positive_id(run_id)
    positive_id(artifact_id)
    if _SHA256.fullmatch(receipt_sha256) is None:
        raise ValueError("acceptance receipt SHA256 must be 64 lowercase hexadecimal characters")
    return True


def validate_hosted_handoff(
    run: dict[str, Any],
    artifact: dict[str, Any],
    *,
    repository: str,
    revision: str,
    run_id: str,
    artifact_id: str,
) -> None:
    """Require a successful exact-revision run and one unexpired public artifact.

    Fork-run evidence cannot authorize this repository's publication. Numeric
    endpoint admission is independent of these untrusted API response fields.
    """
    selected_run, selected_artifact = positive_id(run_id), positive_id(artifact_id)
    if _REPOSITORY.fullmatch(repository) is None or _REVISION.fullmatch(revision) is None:
        raise ValueError("acceptance repository/revision is invalid")
    identity = run.get("repository", {})
    head = run.get("head_repository", {})
    origin = artifact.get("workflow_run", {})
    if not all(isinstance(value, dict) for value in (identity, head, origin)):
        raise ValueError("hosted acceptance provenance is malformed")
    repository_id = identity.get("id")
    if (
        type(run.get("id")) is not int
        or run["id"] != selected_run
        or run.get("status") != "completed"
        or run.get("conclusion") != "success"
        or run.get("head_sha") != revision
        or run.get("path") != WORKFLOW
        or identity.get("full_name") != repository
        or type(repository_id) is not int
        or repository_id <= 0
        or type(head.get("id")) is not int
        or head.get("id") != repository_id
        or head.get("full_name") != repository
        or type(artifact.get("id")) is not int
        or artifact["id"] != selected_artifact
        or artifact.get("name") != ARTIFACT_NAME
        or artifact.get("expired") is not False
        or type(artifact.get("size_in_bytes")) is not int
        or not 0 < artifact["size_in_bytes"] <= 64 * 1024 * 1024
        or not isinstance(artifact.get("digest"), str)
        or re.fullmatch(r"sha256:[0-9a-f]{64}", artifact["digest"]) is None
        or any(type(origin.get(field)) is not int for field in ("id", "repository_id", "head_repository_id"))
        or origin.get("id") != selected_run
        or origin.get("head_sha") != revision
        or origin.get("repository_id") != repository_id
        or origin.get("head_repository_id") != repository_id
    ):
        raise ValueError("acceptance artifact is not from the successful tagged-revision repository run")


def admit_acceptance_archive(root: Path, archive_path: Path, *, artifact_metadata: dict[str, Any]) -> None:
    """Reuse bounded native-archive checks and refuse source/control overwrites."""
    root = root.resolve()
    reader = SnapshotReader(root)
    content = read_bytes_confined(archive_path.absolute().parent, archive_path.absolute(), max_bytes=64 * 1024 * 1024)
    if (
        type(artifact_metadata.get("size_in_bytes")) is not int
        or artifact_metadata["size_in_bytes"] != len(content)
        or artifact_metadata.get("digest") != "sha256:" + hashlib.sha256(content).hexdigest()
    ):
        raise ValueError("acceptance archive digest/size differs from hosted API observation")
    with zipfile.ZipFile(BytesIO(content)) as archive:
        names = bounded_members(archive)
        if RECEIPT_PATH not in names:
            raise ValueError("acceptance archive lacks the canonical aggregate receipt")
        admitted = []
        for name in sorted(names):
            if (
                name != Path(name).as_posix()
                or len(Path(name).parts) < 4
                or not Path(name).is_relative_to(Path("output/readiness"))
            ):
                raise ValueError("acceptance archive may contain only canonical public readiness evidence")
            destination = reader.public_path(name)
            if destination.exists():
                raise ValueError("acceptance archive cannot replace an existing evidence observation")
            admitted.append((destination, archive.read(name)))
        # All names and bytes are admitted before the first confined write.
        for destination, content in admitted:
            atomic_write_bytes_confined(root, destination, content)


def _checkout_revision(root: Path) -> str:
    """Observe the actual local Git revision with a finite, credential-free query."""
    actual = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
        env={"PATH": "/usr/bin:/bin", "LC_ALL": "C", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null"},
    )
    if actual.returncode or _REVISION.fullmatch(actual.stdout.strip()) is None:
        raise ValueError("candidate checkout has no admitted Git revision")
    return actual.stdout.strip()


def validate_candidate_handoff(
    root: Path,
    *,
    revision: str,
    receipt_sha256: str,
    repository: str = "",
    run_id: str = "",
    artifact_id: str = "",
    run_metadata: Path | None = None,
    artifact_metadata: Path | None = None,
    native_operation: object = None,
    hosted_origin: HostedReadbackContext | None = None,
) -> str:
    """Admit exact aggregate bytes, revision, and the entire existing candidate profile."""
    if _REVISION.fullmatch(revision) is None or _SHA256.fullmatch(receipt_sha256) is None:
        raise ValueError("candidate revision/receipt digest is invalid")
    root = root.resolve()
    if _checkout_revision(root) != revision:
        raise ValueError("candidate checkout does not match the exact handoff revision")
    hosted_inputs = (repository, run_id, artifact_id, run_metadata, artifact_metadata)
    if any(hosted_inputs):
        if not all(hosted_inputs) or run_metadata is None or artifact_metadata is None:
            raise ValueError("hosted candidate admission requires every external handoff identity and API observation")
        validate_hosted_handoff(
            _metadata(run_metadata),
            _metadata(artifact_metadata),
            repository=repository,
            revision=revision,
            run_id=run_id,
            artifact_id=artifact_id,
        )
    if native_operation is not None:
        from infrastructure.reporting.native_format_joint_source import NativeReaderOperation

        if not isinstance(native_operation, NativeReaderOperation):
            raise ValueError("candidate native admission requires its independently held current reader")
        if native_operation.source.bindings.current_root != root:
            raise ValueError("candidate native reader belongs to a different current checkout")
    reader = SnapshotReader(root, native_operation=native_operation, hosted_origin=hosted_origin)
    receipt = reader.read(RECEIPT_PATH)
    payload = receipt.json_object()
    if receipt.sha256 != receipt_sha256 or payload.get("source_commit") != revision:
        raise ValueError("acceptance receipt hash or exact source revision differs from the handoff")
    if any(hosted_inputs):
        binding = payload.get("hosted_origin_artifact")
        if (
            not isinstance(binding, dict)
            or set(binding) != {"path", "sha256"}
            or not all(isinstance(binding[key], str) for key in ("path", "sha256"))
        ):
            raise ValueError("hosted candidate lacks the complete hash-bound origin manifest")
        context = HostedReadbackContext(
            manifest_binding=binding,
            repository=repository,
            run_id=positive_id(run_id),
            head_sha=revision,
        )
        if hosted_origin is not None and hosted_origin != context:
            raise ValueError("candidate hosted context differs from the exact authenticated handoff")
        reader = SnapshotReader(root, hosted_origin=context, native_operation=native_operation)
        # Hold the same aggregate bytes in the context-aware reader as well.
        if reader.read(RECEIPT_PATH).sha256 != receipt_sha256:
            raise ValueError("acceptance receipt changed during hosted-context admission")
    evidence = collect_profile(root, root / RECEIPT_PATH, reader)
    if native_operation is not None:
        native_operation.verify(reader)
    if not reader.unchanged() or _checkout_revision(root) != revision:
        raise ValueError("acceptance evidence changed during required-profile admission")
    return evidence.candidate_state


def _metadata(path: Path) -> dict[str, Any]:
    return json_object_from_bytes(read_bytes_confined(path.absolute().parent, path.absolute(), max_bytes=1024 * 1024))


def main(argv: Sequence[str] | None = None) -> int:
    """Return nonzero for absent, invalid, stale, blocked or incomplete handoffs."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inputs = commands.add_parser("inputs")
    inputs.add_argument("--repo-root", type=Path, default=Path.cwd())
    inputs.add_argument("--run-id", default="")
    inputs.add_argument("--artifact-id", default="")
    inputs.add_argument("--receipt-sha256", default="")
    hosted = commands.add_parser("hosted")
    hosted.add_argument("--run-metadata", type=Path, required=True)
    hosted.add_argument("--artifact-metadata", type=Path, required=True)
    hosted.add_argument("--repository", required=True)
    hosted.add_argument("--revision", required=True)
    hosted.add_argument("--run-id", required=True)
    hosted.add_argument("--artifact-id", required=True)
    archive = commands.add_parser("archive")
    archive.add_argument("--repo-root", type=Path, default=Path.cwd())
    archive.add_argument("--archive", type=Path, required=True)
    archive.add_argument("--artifact-metadata", type=Path, required=True)
    candidate = commands.add_parser("candidate")
    candidate.add_argument("--repo-root", type=Path, default=Path.cwd())
    candidate.add_argument("--revision", required=True)
    candidate.add_argument("--receipt-sha256", required=True)
    candidate.add_argument("--repository", default="")
    candidate.add_argument("--run-id", default="")
    candidate.add_argument("--artifact-id", default="")
    candidate.add_argument("--run-metadata", type=Path)
    candidate.add_argument("--artifact-metadata", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "inputs":
            required = validate_handoff_inputs(args.repo_root, args.run_id, args.artifact_id, args.receipt_sha256)
            print(f"required={str(required).lower()}")
        elif args.command == "hosted":
            validate_hosted_handoff(
                _metadata(args.run_metadata),
                _metadata(args.artifact_metadata),
                repository=args.repository,
                revision=args.revision,
                run_id=args.run_id,
                artifact_id=args.artifact_id,
            )
        elif args.command == "archive":
            admit_acceptance_archive(args.repo_root, args.archive, artifact_metadata=_metadata(args.artifact_metadata))
        else:
            state = validate_candidate_handoff(
                args.repo_root,
                revision=args.revision,
                receipt_sha256=args.receipt_sha256,
                repository=args.repository,
                run_id=args.run_id,
                artifact_id=args.artifact_id,
                run_metadata=args.run_metadata,
                artifact_metadata=args.artifact_metadata,
            )
            print(f"required candidate acceptance: {state}")
            return {"pass": 0, "fail": 1, "blocked": 75, "unknown": 2}[state]
    except MissingAcceptanceHandoff as error:
        print(f"root release blocked: {error}")
        return 75
    except (OSError, ValueError, TypeError, zipfile.BadZipFile, RuntimeError, subprocess.SubprocessError) as error:
        print(f"root release acceptance refused: {error}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "ARTIFACT_NAME",
    "RECEIPT_PATH",
    "MissingAcceptanceHandoff",
    "positive_id",
    "validate_handoff_inputs",
    "validate_hosted_handoff",
    "admit_acceptance_archive",
    "validate_candidate_handoff",
    "main",
]
