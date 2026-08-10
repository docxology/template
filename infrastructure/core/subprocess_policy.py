"""Typed policy boundaries for intentional repository subprocesses."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from infrastructure.core.execution_boundary import (
    BoundedSubprocessResult,
    build_bounded_env,
    run_bounded_subprocess,
)


class SubprocessPolicyError(RuntimeError):
    """Raised when a checked subprocess violates its declared policy."""

    def __init__(self, policy_id: str, result: BoundedSubprocessResult) -> None:
        detail = result.command_error or result.stderr.strip() or result.stdout.strip() or "no diagnostic output"
        super().__init__(f"subprocess policy {policy_id!r} rejected exit={result.returncode}: {detail[-1000:]}")
        self.policy_id = policy_id
        self.result = result


@dataclass(frozen=True)
class SubprocessPolicy:
    """Declared timeout, cwd, output, and credential policy for one wrapper."""

    policy_id: str
    source_path: str
    timeout_seconds: float
    cwd_required: bool = True
    check: bool = False
    capture_output: bool = True
    credential_free: bool = True
    process_group: bool = True

    def validate(self, repo_root: Path | None = None) -> None:
        """Reject incomplete or unsafe policy declarations."""
        if not self.policy_id.strip():
            raise ValueError("subprocess policy id must not be empty")
        if not self.source_path.strip():
            raise ValueError(f"subprocess policy {self.policy_id!r} needs a source path")
        if self.timeout_seconds <= 0:
            raise ValueError(f"subprocess policy {self.policy_id!r} needs a positive timeout")
        if not self.process_group:
            raise ValueError(f"subprocess policy {self.policy_id!r} must use a process-group boundary")
        if repo_root is not None and not (repo_root / self.source_path).is_file():
            raise ValueError(f"subprocess policy {self.policy_id!r} names missing source {self.source_path!r}")


@dataclass(frozen=True)
class SubprocessPolicyRecord:
    """Serializable inventory row for one intentional subprocess wrapper."""

    policy_id: str
    source_path: str
    timeout_seconds: float
    cwd_required: bool
    check: bool
    capture_output: bool
    credential_free: bool
    process_group: bool

    @classmethod
    def from_policy(cls, policy: SubprocessPolicy) -> SubprocessPolicyRecord:
        """Build an inventory record from a validated policy."""
        return cls(
            policy_id=policy.policy_id,
            source_path=policy.source_path,
            timeout_seconds=policy.timeout_seconds,
            cwd_required=policy.cwd_required,
            check=policy.check,
            capture_output=policy.capture_output,
            credential_free=policy.credential_free,
            process_group=policy.process_group,
        )


def validate_policy_inventory(policies: Sequence[SubprocessPolicy], repo_root: Path | None = None) -> list[str]:
    """Return actionable errors for a source-owned wrapper inventory."""
    errors: list[str] = []
    seen: set[str] = set()
    for policy in policies:
        if policy.policy_id in seen:
            errors.append(f"DUPLICATE-POLICY: {policy.policy_id}")
        seen.add(policy.policy_id)
        try:
            policy.validate(repo_root)
        except ValueError as exc:
            errors.append(f"INVALID-POLICY: {exc}")
    return errors


INTENTIONAL_SUBPROCESS_POLICIES: tuple[SubprocessPolicy, ...] = (
    SubprocessPolicy(
        policy_id="project-test-matrix",
        source_path="infrastructure/core/project_test_matrix.py",
        timeout_seconds=1800,
        check=False,
        capture_output=False,
        credential_free=True,
    ),
    SubprocessPolicy(
        policy_id="renderer-helper",
        source_path="infrastructure/rendering/security.py",
        timeout_seconds=600,
        check=False,
        capture_output=True,
    ),
    SubprocessPolicy(
        policy_id="git-metadata",
        source_path="infrastructure/validation/publication/rendered_provenance.py",
        timeout_seconds=30,
        check=False,
        capture_output=True,
    ),
    SubprocessPolicy(
        policy_id="git-metadata-test-runner",
        source_path="infrastructure/core/test_runner_cache.py",
        timeout_seconds=30,
        check=False,
        capture_output=True,
    ),
    SubprocessPolicy(
        policy_id="git-cache-identity",
        source_path="infrastructure/core/test_runner_cache.py",
        timeout_seconds=30,
        check=False,
        capture_output=True,
    ),
    SubprocessPolicy(
        policy_id="coverage-combine",
        source_path="infrastructure/core/test_runner.py",
        timeout_seconds=300,
        check=False,
        capture_output=False,
    ),
    SubprocessPolicy(
        policy_id="coverage-gate",
        source_path="infrastructure/core/test_runner.py",
        timeout_seconds=300,
        check=False,
        capture_output=False,
    ),
    SubprocessPolicy(
        policy_id="validation-spine",
        source_path="infrastructure/validation/security_gate.py",
        timeout_seconds=300,
        check=False,
        capture_output=True,
    ),
    SubprocessPolicy(
        policy_id="formal-side-spec",
        source_path="projects/templates/template_formal/scripts/check_formal_specs.sh",
        timeout_seconds=1800,
        check=True,
        capture_output=True,
    ),
    SubprocessPolicy(
        policy_id="release-rehearsal-clone",
        source_path="infrastructure/publishing/rehearsal.py",
        timeout_seconds=1800,
        check=False,
        capture_output=True,
    ),
    SubprocessPolicy(
        policy_id="release-rehearsal-command",
        source_path="infrastructure/publishing/rehearsal.py",
        timeout_seconds=1800,
        check=False,
        capture_output=True,
    ),
    SubprocessPolicy(
        policy_id="release-rehearsal-clean-status",
        source_path="infrastructure/publishing/rehearsal.py",
        timeout_seconds=60,
        check=False,
        capture_output=True,
    ),
    SubprocessPolicy(
        policy_id="test-impact-git",
        source_path="scripts/audit/test_impact.py",
        timeout_seconds=30,
        check=False,
        capture_output=True,
    ),
    SubprocessPolicy(
        policy_id="coverage-measurement",
        source_path="infrastructure/documentation/counts_coverage.py",
        timeout_seconds=1800,
        check=False,
        capture_output=True,
    ),
    SubprocessPolicy(
        policy_id="coverage-report",
        source_path="infrastructure/documentation/counts_coverage.py",
        timeout_seconds=300,
        check=False,
        capture_output=True,
    ),
    SubprocessPolicy(
        policy_id="coverage-source-inventory",
        source_path="infrastructure/documentation/counts_coverage.py",
        timeout_seconds=30,
        check=False,
        capture_output=True,
    ),
)


def run_with_policy(
    argv: Sequence[str],
    *,
    cwd: Path,
    env: dict[str, str] | None,
    policy: SubprocessPolicy,
) -> BoundedSubprocessResult:
    """Run an argv list through the shared timeout/process-group boundary."""
    policy.validate()
    workdir = cwd.resolve()
    if policy.cwd_required and not workdir.is_dir():
        raise ValueError(f"subprocess policy {policy.policy_id!r} requires an existing cwd: {cwd}")
    inherited = dict(os.environ if env is None else env)
    safe_env = build_bounded_env(inherited) if policy.credential_free else inherited
    result = run_bounded_subprocess(
        argv,
        cwd=workdir,
        env=safe_env,
        timeout=policy.timeout_seconds,
        capture_output=policy.capture_output,
    )
    if policy.check and result.returncode != 0:
        raise SubprocessPolicyError(policy.policy_id, result)
    return result


__all__ = [
    "INTENTIONAL_SUBPROCESS_POLICIES",
    "SubprocessPolicy",
    "SubprocessPolicyError",
    "SubprocessPolicyRecord",
    "run_with_policy",
    "validate_policy_inventory",
]
