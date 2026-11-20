"""Admit a composed required-acceptance receipt for a locally provable release.

A composed receipt states, per required class, the exact source commit, the
producer, the artifact byte identity and the class closure. It is admissible only
when every required class is present, current, pass, bound to this commit and
locally provable. A missing, stale, unknown or hosted-only class refuses; there
is no partial or best-effort admission.

This path does not replace the hosted carrier. Which one is required is decided
by the source-owned class table: if any required class is hosted-only, the hosted
handoff stays mandatory and this receipt cannot authorize publication.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.reporting.evidence_class import class_binding, hosted_required
from infrastructure.reporting.readiness_receipts import source_fingerprint
from infrastructure.reporting.release_readiness_profile import _check_class_binding, required_profile
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SCHEMA = "template-composed-acceptance-v1"
COMPOSED_RECEIPT_PATH = "output/readiness/composed-acceptance/receipt.json"
_MAX_BYTES = 1048576


def _checkout_revision(root: Path) -> str:
    """Observe the actual committed revision this receipt must bind."""
    import re
    import subprocess

    observed = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
        env={"PATH": "/usr/bin:/bin", "LC_ALL": "C", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null"},
    )
    revision = observed.stdout.strip()
    if observed.returncode or re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        raise ValueError("composed receipt requires an admitted Git revision")
    return revision


def validate_composed_receipt(root: Path, receipt_path: Path) -> dict[str, Any]:
    """Refuse unless every required class is present, current and locally provable."""
    root = root.resolve(strict=True)
    target = receipt_path if receipt_path.is_absolute() else root / receipt_path
    payload = _load(root, target)
    if payload.get("schema_version") != SCHEMA:
        raise ValueError("composed receipt schema is unsupported")
    revision = _checkout_revision(root)
    if payload.get("source_commit") != revision:
        raise ValueError("composed receipt binds a different source commit")
    fingerprint = source_fingerprint(root)
    requirements, faults = required_profile(root, SnapshotReader(root), fingerprint)
    if faults or not requirements:
        raise ValueError("composed receipt requires a complete current required profile")
    from infrastructure.reporting.evidence_class import hosted_required, stage_digest

    # A hosted-only class must be resolved by the environment that observed it.
    # If this checkout cannot observe that environment, the receipt is unverifiable
    # here and is refused rather than downgraded to a claim.
    unresolved = sorted(requirement.id for requirement in requirements if hosted_required((requirement,)))
    if unresolved and not hosted_origin_resolvable(root):
        raise ValueError(
            "composed receipt cannot be verified from this checkout: hosted classes require a resolvable "
            f"hosted origin ({len(unresolved)} class(es))"
        )
    classes = payload.get("classes")
    if not isinstance(classes, dict):
        raise ValueError("composed receipt must declare its classes")
    required = {requirement.id: requirement for requirement in requirements}
    missing = sorted(set(required) - set(classes))
    if missing:
        raise ValueError(f"composed receipt is missing required classes: {missing[:5]}")
    extra = sorted(set(classes) - set(required))
    if extra:
        raise ValueError(f"composed receipt declares unknown classes: {extra[:5]}")
    stage = stage_digest(root)
    reader = SnapshotReader(root)
    for gate, requirement in required.items():
        entry = classes[gate]
        if not isinstance(entry, dict):
            raise ValueError(f"composed receipt class {gate} is malformed")
        _check_entry(root, gate, entry, requirement, reader, fingerprint, revision, stage)
    if not reader.unchanged() or source_fingerprint(root) != fingerprint or _checkout_revision(root) != revision:
        raise ValueError("composed receipt source or artifacts changed during admission")
    return payload


def _load(root: Path, target: Path) -> dict[str, Any]:
    """Read one bounded composed receipt through confined public custody."""
    if ".." in target.parts:
        raise ValueError("composed receipt path must stay inside the repository")
    content = read_bytes_confined(target.parent.absolute(), target.absolute(), max_bytes=_MAX_BYTES)
    import json

    try:
        payload = json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError("composed receipt is not valid JSON") from error
    if not isinstance(payload, dict):
        raise ValueError("composed receipt must be a JSON object")
    return payload


def hosted_origin_resolvable(root: Path) -> bool:
    """Return whether this environment can authenticate a hosted origin read.

    Composed admission reads hosted run metadata. Without a token and an
    authenticated ``gh``, those reads cannot distinguish a real run from a
    fabricated identifier, so the receipt is unverifiable here and must refuse
    rather than treat a claim as proof.
    """
    import os
    import shutil
    import subprocess

    if not (os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")):
        return False
    if shutil.which("gh") is None:
        return False
    try:
        observed = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
            env={**os.environ, "LC_ALL": "C"},
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return observed.returncode == 0


def _resolve_hosted_origin(origin: dict[str, str]) -> str:
    """Return ``observed`` only when the named run resolves and concluded success.

    Three outcomes, and they are not interchangeable:

    * ``observed`` -- the run exists and its conclusion is ``success``;
    * ``declared`` -- the run could not be resolved here (no token, no network,
      transient API failure). The claim is recorded as unverified, never as proof;
    * raise -- the run resolved and its conclusion is **not** success. A claimed
      success whose run says otherwise is a false statement, not a downgrade.

    Environment access is read-only and bounded. Nothing is written or published.
    """
    import json
    import os
    import subprocess

    repository, run_id = origin["repository"], origin["run_id"]
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    command = [
        "gh",
        "api",
        "--hostname",
        "github.com",
        f"repos/{repository}/actions/runs/{run_id}",
        "--jq",
        "{status,conclusion,head_sha,path}",
    ]
    try:
        observed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
            env={
                "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
                "LC_ALL": "C",
                "GH_TOKEN": token or "",
                "GITHUB_TOKEN": token or "",
            },
        )
    except (OSError, subprocess.SubprocessError):
        return "declared"
    if observed.returncode != 0 or not observed.stdout.strip():
        # Unresolvable is not the same as failed; it is simply not verified.
        return "declared"
    try:
        payload = json.loads(observed.stdout)
    except json.JSONDecodeError:
        return "declared"
    if not isinstance(payload, dict):
        return "declared"
    return _origin_verdict(payload, expected_head_sha=origin["head_sha"])


def _origin_verdict(payload: dict[str, Any], *, expected_head_sha: str) -> str:
    """Decide one hosted origin from its API observation, without any I/O.

    Pure so the decision can be controlled directly: a run that resolved and did
    not succeed is a refusal, a run bound to another commit is a refusal, and an
    incomplete observation is only ever ``declared``.
    """
    conclusion = payload.get("conclusion")
    status = payload.get("status")
    if not isinstance(conclusion, str) or not isinstance(status, str):
        return "declared"
    if status != "completed":
        raise ValueError("composed receipt hosted origin run is not completed")
    if conclusion != "success":
        raise ValueError("composed receipt hosted origin run did not succeed")
    if payload.get("head_sha") != expected_head_sha:
        raise ValueError("composed receipt hosted origin run is bound to another commit")
    return "observed"


def _check_hosted_origin(gate: str, entry: dict[str, Any], requirement: Any) -> str:
    """Require a hosted producer for hosted-only classes, and refuse one otherwise.

    A macOS window-server observation, a real upload/retrieval custody proof or a
    Darwin Root cell is a property of the host, not of the commit. Such a class
    must name the hosted run and artifact that produced it. A class that is
    provable from a local checkout must not claim a hosted origin, so the
    receipt cannot launder local evidence through an unrelated run.

    The returned evidence state distinguishes an independently resolved origin
    from a claim. A receipt that cannot tell "I checked" from "I was told" would
    be read as the former, which is why the state is recorded rather than implied.
    """
    import re

    origin = entry.get("hosted_origin")
    required = hosted_required((requirement,))
    if not required:
        if origin is not None:
            raise ValueError(f"composed receipt class {gate} is locally provable but claims a hosted origin")
        return "observed"
    if not isinstance(origin, dict):
        raise ValueError(f"composed receipt class {gate} requires a hosted origin")
    if set(origin) != {"repository", "run_id", "artifact_id", "head_sha"}:
        raise ValueError(f"composed receipt class {gate} hosted origin is malformed")
    repository, run_id, artifact_id = origin["repository"], origin["run_id"], origin["artifact_id"]
    if not isinstance(repository, str) or re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) is None:
        raise ValueError(f"composed receipt class {gate} hosted repository is invalid")
    if not isinstance(run_id, str) or not isinstance(artifact_id, str) or not isinstance(origin["head_sha"], str):
        raise ValueError(f"composed receipt class {gate} hosted ids must be strings")
    if re.fullmatch(r"[0-9a-f]{40}", origin["head_sha"]) is None:
        raise ValueError(f"composed receipt class {gate} hosted head_sha is invalid")
    from infrastructure.publishing.release_acceptance import positive_id

    positive_id(run_id)
    positive_id(artifact_id)
    return _resolve_hosted_origin(origin)


def _check_entry(
    root: Path,
    gate: str,
    entry: dict[str, Any],
    requirement: Any,
    reader: SnapshotReader,
    fingerprint: str,
    revision: str,
    stage: str | None,
) -> None:
    """Refuse a class that is not present, current, passing and byte-bound."""
    if entry.get("status") != "pass":
        raise ValueError(f"composed receipt class {gate} is not pass")
    if entry.get("source_commit") != revision:
        raise ValueError(f"composed receipt class {gate} binds a different commit")
    producer = entry.get("producer")
    if not isinstance(producer, list) or not producer or any(not isinstance(arg, str) or not arg for arg in producer):
        raise ValueError(f"composed receipt class {gate} must name its producer argv")
    evidence_state = _check_hosted_origin(gate, entry, requirement)
    if hosted_required((requirement,)) and evidence_state != "observed":
        raise ValueError(
            f"composed receipt class {gate} requires a hosted origin that could not be verified "
            f"(resolved {evidence_state!r}); unverified hosted origins are not release evidence"
        )
    if entry.get("evidence_state") != evidence_state:
        raise ValueError(
            f"composed receipt class {gate} evidence_state does not match the observed origin "
            f"(declared {entry.get('evidence_state')!r}, resolved {evidence_state!r})"
        )
    artifact = entry.get("artifact")
    digest = entry.get("artifact_sha256")
    if not isinstance(artifact, str) or not artifact or not isinstance(digest, str):
        raise ValueError(f"composed receipt class {gate} must bind artifact bytes")
    held = reader.read(artifact)
    if held.sha256 != digest:
        raise ValueError(f"composed receipt class {gate} artifact differs from its recorded bytes")
    if held.json_object().get("gate") != gate:
        raise ValueError(f"composed receipt class {gate} artifact names another class")
    # Reuse the single class-binding decision the required profile already makes.
    _check_class_binding(requirement, held.json_object(), root, fingerprint, stage=stage)
    recorded = entry.get("class_binding")
    expected = class_binding(requirement, root, repository_fingerprint=fingerprint, stage=stage)
    if recorded != expected.to_dict():
        raise ValueError(f"composed receipt class {gate} closure is stale for this Source")


__all__ = ["COMPOSED_RECEIPT_PATH", "SCHEMA", "validate_composed_receipt"]
