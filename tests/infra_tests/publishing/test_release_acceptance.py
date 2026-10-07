"""Actual metadata, Git revisions, and archives for root acceptance handoffs."""

from __future__ import annotations

import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

import pytest

from infrastructure.publishing.release_acceptance import (
    ARTIFACT_NAME,
    RECEIPT_PATH,
    MissingAcceptanceHandoff,
    admit_acceptance_archive,
    main,
    positive_id,
    validate_candidate_handoff,
    validate_handoff_inputs,
    validate_hosted_handoff,
)
from infrastructure.publishing.root_release_contract import RUNTIME_VERSION_PROVIDER_SOURCE
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.readiness_receipts import SCHEMA_VERSION, source_fingerprint


def _root(root: Path, version: str = "4.0.0") -> str:
    (root / "pyproject.toml").write_text(f'[project]\nname="research-project-template"\nversion="{version}"\n')
    (root / "CHANGELOG.md").write_text(f"## [{version}] - Unreleased\n")
    (root / ".python-version").write_text("3.14\n")
    (root / "infrastructure").mkdir()
    (root / "infrastructure/_version.py").write_text(RUNTIME_VERSION_PROVIDER_SOURCE)
    for argv in (
        ["git", "init", "--quiet", str(root)],
        [
            "git",
            "-C",
            str(root),
            "add",
            "pyproject.toml",
            "CHANGELOG.md",
            ".python-version",
            "infrastructure/_version.py",
        ],
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=Public Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "public candidate fixture",
        ],
    ):
        subprocess.run(argv, check=True, capture_output=True, timeout=10)
    return subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"], check=True, capture_output=True, text=True, timeout=5
    ).stdout.strip()


def _hosted(revision: str = "a" * 40) -> tuple[dict, dict]:
    run = {
        "id": 123,
        "status": "completed",
        "conclusion": "success",
        "head_sha": revision,
        "path": ".github/workflows/platform-required-acceptance.yml",
        "repository": {"id": 456, "full_name": "docxology/template"},
        "head_repository": {"id": 456, "full_name": "docxology/template"},
    }
    artifact = {
        "id": 789,
        "name": ARTIFACT_NAME,
        "expired": False,
        "size_in_bytes": 1024,
        "digest": "sha256:" + "b" * 64,
        "workflow_run": {"id": 123, "head_sha": revision, "repository_id": 456, "head_repository_id": 456},
    }
    return run, artifact


@pytest.mark.parametrize("value", ["", "0", "-1", "+1", "01", "1/zip", "1\n", "true", str(2**63)])
def test_noncanonical_ids_refuse_endpoint_construction(value: str) -> None:
    with pytest.raises(ValueError, match="positive integers"):
        positive_id(value)


def test_root_4_requires_explicit_handoff_and_older_major_does_not(tmp_path: Path) -> None:
    _root(tmp_path)
    with pytest.raises(MissingAcceptanceHandoff):
        validate_handoff_inputs(tmp_path, "", "", "")
    assert main(["inputs", "--repo-root", str(tmp_path)]) == 75
    assert validate_handoff_inputs(tmp_path, "123", "789", "a" * 64)
    (tmp_path / "pyproject.toml").write_text('[project]\nname="research-project-template"\nversion="3.8.0"\n')
    assert not validate_handoff_inputs(tmp_path, "", "", "")


@pytest.mark.parametrize(
    "field,value",
    [
        ("status", "in_progress"),
        ("conclusion", "failure"),
        ("head_sha", "b" * 40),
        ("id", True),
        ("repository", {"id": 456, "full_name": "foreign/repository"}),
        ("head_repository", {"id": 987, "full_name": "fork/template"}),
    ],
)
def test_wrong_or_unsuccessful_run_refuses(field: str, value: object) -> None:
    run, artifact = _hosted()
    run[field] = value
    with pytest.raises(ValueError, match="successful tagged-revision"):
        validate_hosted_handoff(
            run, artifact, repository="docxology/template", revision="a" * 40, run_id="123", artifact_id="789"
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("id", 788),
        ("expired", True),
        ("expired", 0),
        ("name", "coverage-only"),
        ("size_in_bytes", True),
        ("size_in_bytes", 0),
        ("size_in_bytes", 64 * 1024 * 1024 + 1),
        ("workflow_run", {"id": 123, "head_sha": "b" * 40, "repository_id": 456, "head_repository_id": 456}),
        ("workflow_run", {"id": 124, "head_sha": "a" * 40, "repository_id": 456, "head_repository_id": 456}),
    ],
)
def test_wrong_or_expired_artifact_refuses(field: str, value: object) -> None:
    run, artifact = _hosted()
    artifact[field] = value
    with pytest.raises(ValueError, match="successful tagged-revision"):
        validate_hosted_handoff(
            run, artifact, repository="docxology/template", revision="a" * 40, run_id="123", artifact_id="789"
        )


def test_exact_hosted_run_and_artifact_admit() -> None:
    run, artifact = _hosted()
    validate_hosted_handoff(
        run, artifact, repository="docxology/template", revision="a" * 40, run_id="123", artifact_id="789"
    )


@pytest.mark.parametrize(
    "name",
    [
        "../outside",
        "pyproject.toml",
        "/tmp/outside",
        "output/readiness/../private",
        "output/readiness/.env",
        "output/readiness/run/../receipt.json",
    ],
)
def test_unsafe_archive_members_refuse_before_any_write(tmp_path: Path, name: str) -> None:
    root = tmp_path / "candidate"
    root.mkdir()
    sentinel = root / "pyproject.toml"
    sentinel.write_bytes(b"preserved public source")
    archive = tmp_path / "acceptance.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr(RECEIPT_PATH, b"{}")
        bundle.writestr(name, b"wrong")
    with pytest.raises(ValueError):
        admit_acceptance_archive(root, archive, artifact_metadata=_archive_metadata(archive))
    assert sentinel.read_bytes() == b"preserved public source"
    assert not (root / "output").exists()


def test_linked_archive_members_and_existing_evidence_refuse(tmp_path: Path) -> None:
    root = tmp_path / "candidate"
    root.mkdir()
    archive = tmp_path / "acceptance.zip"
    member = zipfile.ZipInfo("output/readiness/run/link")
    member.create_system = 3
    member.external_attr = 0o120777 << 16
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr(RECEIPT_PATH, b"{}")
        bundle.writestr(member, b"/outside")
    with pytest.raises(ValueError, match="unsafe"):
        admit_acceptance_archive(root, archive, artifact_metadata=_archive_metadata(archive))
    assert not (root / "output").exists()
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr(RECEIPT_PATH, b"new")
    receipt = root / RECEIPT_PATH
    receipt.parent.mkdir(parents=True)
    receipt.write_bytes(b"original observation")
    with pytest.raises(ValueError, match="cannot replace"):
        admit_acceptance_archive(root, archive, artifact_metadata=_archive_metadata(archive))
    assert receipt.read_bytes() == b"original observation"


def test_admitted_archive_preserves_exact_public_evidence_bytes(tmp_path: Path) -> None:
    root = tmp_path / "candidate"
    root.mkdir()
    archive = tmp_path / "acceptance.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr(RECEIPT_PATH, b'{"source_commit":"public"}')
        bundle.writestr("output/readiness/run/raw.bin", b"\x00\xff\x80")
    admit_acceptance_archive(root, archive, artifact_metadata=_archive_metadata(archive))
    assert (root / "output/readiness/run/raw.bin").read_bytes() == b"\x00\xff\x80"


def _archive_metadata(path: Path) -> dict[str, object]:
    content = path.read_bytes()
    return {"digest": "sha256:" + hashlib.sha256(content).hexdigest(), "size_in_bytes": len(content)}


def test_foreign_workflow_and_missing_archive_digest_refuse() -> None:
    run, artifact = _hosted()
    for field, value in (("path", ".github/workflows/foreign.yml"), ("path", None)):
        with pytest.raises(ValueError, match="successful tagged-revision"):
            validate_hosted_handoff(
                {**run, field: value},
                artifact,
                repository="docxology/template",
                revision="a" * 40,
                run_id="123",
                artifact_id="789",
            )
    with pytest.raises(ValueError, match="successful tagged-revision"):
        validate_hosted_handoff(
            run,
            {**artifact, "digest": None},
            repository="docxology/template",
            revision="a" * 40,
            run_id="123",
            artifact_id="789",
        )


@pytest.mark.parametrize("field,value", [("digest", "sha256:" + "0" * 64), ("size_in_bytes", True)])
def test_api_archive_digest_and_size_refuse_before_extraction(tmp_path: Path, field: str, value: object) -> None:
    root = tmp_path / "candidate"
    root.mkdir()
    archive = tmp_path / "acceptance.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr(RECEIPT_PATH, b"{}")
    metadata = _archive_metadata(archive)
    metadata[field] = value
    with pytest.raises(ValueError, match="digest/size differs"):
        admit_acceptance_archive(root, archive, artifact_metadata=metadata)
    assert not (root / "output").exists()


def test_duplicate_hosted_json_fields_refuse(tmp_path: Path) -> None:
    from infrastructure.publishing.release_acceptance import _metadata

    metadata = tmp_path / "metadata.json"
    metadata.write_bytes(b'{"repository":{"id":1,"id":2}}')
    with pytest.raises(ValueError, match="repeats JSON field"):
        _metadata(metadata)


def _receipt(root: Path, revision: str) -> str:
    path = root / RECEIPT_PATH
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": SCHEMA_VERSION,
                "platform_version": "4.0.0",
                "source_commit": revision,
                "source_fingerprint": source_fingerprint(root),
                "roster": list(PUBLIC_PROJECT_NAMES),
                "gates": {},
            }
        )
    )
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_wrong_receipt_hash_revision_and_actual_checkout_refuse(tmp_path: Path) -> None:
    revision = _root(tmp_path)
    digest = _receipt(tmp_path, revision)
    with pytest.raises(ValueError, match="hash or exact source revision"):
        validate_candidate_handoff(tmp_path, revision=revision, receipt_sha256="0" * 64)
    path = tmp_path / RECEIPT_PATH
    payload = json.loads(path.read_text())
    payload["source_commit"] = "b" * 40
    path.write_text(json.dumps(payload))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="hash or exact source revision"):
        validate_candidate_handoff(tmp_path, revision=revision, receipt_sha256=digest)
    with pytest.raises(ValueError, match="checkout does not match"):
        validate_candidate_handoff(tmp_path, revision="b" * 40, receipt_sha256=digest)


def test_hash_bound_incomplete_candidate_cannot_authorize_release(tmp_path: Path) -> None:
    revision = _root(tmp_path)
    digest = _receipt(tmp_path, revision)
    assert validate_candidate_handoff(tmp_path, revision=revision, receipt_sha256=digest) == "unknown"
    assert main(["candidate", "--repo-root", str(tmp_path), "--revision", revision, "--receipt-sha256", digest]) == 2


def test_workflow_cannot_create_root_4_release_before_required_acceptance() -> None:
    root = Path(__file__).resolve().parents[3]
    workflow = (root / ".github/workflows/release.yml").read_text()
    for command in (
        "release_acceptance inputs",
        "release_acceptance hosted",
        "release_acceptance archive",
        "release_acceptance candidate",
    ):
        assert workflow.index(command) < workflow.index("name: Create GitHub Release\n        uses:")
    assert '"repos/$GITHUB_REPOSITORY/actions/runs/$ACCEPTANCE_RUN_ID"' in workflow
    assert '"repos/$GITHUB_REPOSITORY/actions/artifacts/$ACCEPTANCE_ARTIFACT_ID/zip"' in workflow
    assert "actions: read" in workflow


def test_candidate_requires_all_external_hosted_context_fields(tmp_path: Path) -> None:
    revision = _root(tmp_path)
    digest = _receipt(tmp_path, revision)
    with pytest.raises(ValueError, match="every external handoff"):
        validate_candidate_handoff(tmp_path, revision=revision, receipt_sha256=digest, repository="docxology/template")


def test_candidate_revalidates_hosted_api_before_admitting_portable_origin(tmp_path: Path) -> None:
    revision = _root(tmp_path)
    digest = _receipt(tmp_path, revision)
    run, artifact = _hosted(revision)
    run["head_sha"] = "b" * 40
    run_path = tmp_path / "actual-run.json"
    artifact_path = tmp_path / "actual-artifact.json"
    run_path.write_text(json.dumps(run))
    artifact_path.write_text(json.dumps(artifact))
    with pytest.raises(ValueError, match="successful tagged-revision"):
        validate_candidate_handoff(
            tmp_path,
            revision=revision,
            receipt_sha256=digest,
            repository="docxology/template",
            run_id="123",
            artifact_id="789",
            run_metadata=run_path,
            artifact_metadata=artifact_path,
        )
    run["head_sha"] = revision
    run_path.write_text(json.dumps(run))
    with pytest.raises(ValueError, match="hash-bound origin manifest"):
        validate_candidate_handoff(
            tmp_path,
            revision=revision,
            receipt_sha256=digest,
            repository="docxology/template",
            run_id="123",
            artifact_id="789",
            run_metadata=run_path,
            artifact_metadata=artifact_path,
        )


def test_release_workflow_passes_external_api_context_to_candidate() -> None:
    root = Path(__file__).resolve().parents[3]
    workflow = (root / ".github/workflows/release.yml").read_text()
    candidate_step = workflow.split("name: Verify every required candidate acceptance gate", 1)[1].split(
        "name: Verify core test contract on tagged SHA", 1
    )[0]
    for required in (
        '--repository "$GITHUB_REPOSITORY"',
        '--run-id "$ACCEPTANCE_RUN_ID"',
        '--artifact-id "$ACCEPTANCE_ARTIFACT_ID"',
        '--run-metadata "$RUNNER_TEMP/root-release-acceptance-run.json"',
        '--artifact-metadata "$RUNNER_TEMP/root-release-acceptance-artifact.json"',
    ):
        assert required in candidate_step
