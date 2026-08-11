"""Opt-in fresh-checkout release rehearsal planning and execution."""

from __future__ import annotations

import hashlib
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from typing import Sequence

from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy
from infrastructure.publishing.release_receipts import CleanCheckoutReceipt, CommandReceipt, ReceiptStatus

REHEARSAL_RECEIPT_TOKEN = "__REHEARSAL_RECEIPT__"
_REPRESENTATIVE_OUTPUT_PREFIX = "projects/templates/template_code_project/output/"

DEFAULT_REHEARSAL_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("uv", "sync", "--locked", "--offline"),
    (
        "uv",
        "run",
        "python",
        "-m",
        "infrastructure.core.health",
        "--json",
        "--quiet",
        "--workers",
        "2",
    ),
    ("uv", "run", "python", "scripts/docgen/counts.py", "--check"),
    ("uv", "run", "python", "scripts/docgen/status_evidence.py", "--check"),
    ("uv", "run", "python", "scripts/audit/check_claim_bindings.py"),
    ("uv", "run", "python", "scripts/audit/check_backlog.py"),
    ("uv", "run", "python", "scripts/audit/check_public_template_contract.py", "--strict"),
    (
        "uv",
        "run",
        "python",
        "scripts/pipeline/stage_01_test.py",
        "--project-only",
        "--all-projects",
        "--public-projects",
        "--profile",
        "release",
        "--project-workers",
        "serial",
        "--receipt",
        REHEARSAL_RECEIPT_TOKEN,
    ),
    (
        "uv",
        "run",
        "python",
        "scripts/pipeline/stage_03_render.py",
        "--project",
        "templates/template_code_project",
        "--skip-manuscript-hydration",
    ),
)


@dataclass(frozen=True)
class CleanCheckoutPlan:
    """Dry-run plan that makes network and mutation boundaries explicit."""

    revision: str
    commands: tuple[tuple[str, ...], ...]
    network_allowed: bool = False
    runs: int = 2
    status: str = "skipped"
    skip_reason: str = "dry-run by default; pass --execute to create fresh clones"

    def to_dict(self) -> dict[str, object]:
        """Return deterministic plan data."""
        return {
            "revision": self.revision,
            "commands": [list(command) for command in self.commands],
            "network_allowed": self.network_allowed,
            "runs": self.runs,
            "status": self.status,
            "skip_reason": self.skip_reason,
        }


def build_clean_checkout_plan(
    repo_root: Path | str,
    *,
    revision: str = "HEAD",
    commands: Sequence[Sequence[str]] = DEFAULT_REHEARSAL_COMMANDS,
) -> CleanCheckoutPlan:
    """Build a no-side-effect rehearsal plan for a requested revision."""
    root = Path(repo_root).resolve()
    if not root.is_dir():
        raise ValueError(f"repository root is not a directory: {root}")
    normalized = tuple(tuple(str(part) for part in command) for command in commands)
    if not normalized or any(not command for command in normalized):
        raise ValueError("fresh-checkout rehearsal requires at least one non-empty command")
    return CleanCheckoutPlan(revision=revision, commands=normalized)


def _digest_output(stdout: str, stderr: str) -> str:
    """Hash command diagnostics without placing them in the receipt."""
    return hashlib.sha256(f"{stdout}\n{stderr}".encode("utf-8", errors="replace")).hexdigest()


def _run_command(command: Sequence[str], cwd: Path, *, timeout_seconds: float = 1800) -> CommandReceipt:
    """Run one rehearsal command through the shared bounded policy."""
    started = monotonic()
    result = run_with_policy(
        command,
        cwd=cwd,
        env=dict(os.environ),
        policy=SubprocessPolicy(
            policy_id="release-rehearsal-command",
            source_path="infrastructure/publishing/rehearsal.py",
            timeout_seconds=timeout_seconds,
            capture_output=True,
        ),
    )
    status: ReceiptStatus = "pass" if result.returncode == 0 and not result.timed_out else "blocked"
    return CommandReceipt(
        command=tuple(command),
        status=status,
        exit_code=result.returncode,
        duration_seconds=round(monotonic() - started, 3),
        output_sha256=_digest_output(result.stdout, result.stderr),
        skip_reason="" if status == "pass" else result.command_error or "command failed",
    )


def _materialize_command(command: Sequence[str], receipt_path: Path) -> tuple[str, ...]:
    """Resolve the disposable receipt token outside the fresh checkout."""
    return tuple(str(receipt_path) if part == REHEARSAL_RECEIPT_TOKEN else str(part) for part in command)


def _status_paths(status_output: str) -> tuple[str, ...]:
    """Parse porcelain paths without accepting ambiguous rename records."""
    paths: list[str] = []
    for line in status_output.splitlines():
        if not line.strip():
            continue
        if len(line) < 4:
            return ("<malformed-status>",)
        if line.startswith("?? "):
            paths.append(line)
            continue
        path = line[3:]
        if " -> " in path:
            return ("<rename-status>",)
        paths.append(path)
    return tuple(paths)


def _clean_generated_render_output(checkout: Path, status_output: str) -> tuple[bool, str]:
    """Restore only the representative render's declared generated output.

    A representative render is expected to exercise the real renderer, which
    can rewrite tracked canonical output files.  A fresh-checkout rehearsal
    must still fail closed for edits outside that output root.  Once the
    allowed paths have been observed in the renderer's command receipt, this
    helper restores them inside the disposable clone so the final cleanliness
    check tests for leaked state rather than platform-specific generated-byte
    differences.  It never runs against the caller's checkout.
    """
    paths = _status_paths(status_output)
    if not paths:
        return True, ""
    if any(path == "<malformed-status>" or path == "<rename-status>" for path in paths):
        return False, "representative render produced an ambiguous git status record"
    outside = [
        path[3:] if path.startswith("?? ") else path
        for path in paths
        if not (path[3:] if path.startswith("?? ") else path).startswith(_REPRESENTATIVE_OUTPUT_PREFIX)
    ]
    if outside:
        return False, "representative render changed non-generated paths: " + ", ".join(sorted(outside)[:8])

    tracked = [path for path in paths if not path.startswith("?? ")]
    untracked = [path[3:] for path in paths if path.startswith("?? ")]
    if tracked:
        restored = run_with_policy(
            ("git", "restore", "--source=HEAD", "--staged", "--worktree", "--", *tracked),
            cwd=checkout,
            env=dict(os.environ),
            policy=SubprocessPolicy(
                policy_id="release-rehearsal-generated-restore",
                source_path="infrastructure/publishing/rehearsal.py",
                timeout_seconds=60,
                capture_output=True,
            ),
        )
        if restored.returncode != 0 or restored.timed_out:
            return False, restored.command_error or "could not restore generated render output"
    if untracked:
        cleaned = run_with_policy(
            ("git", "clean", "-fd", "--", *untracked),
            cwd=checkout,
            env=dict(os.environ),
            policy=SubprocessPolicy(
                policy_id="release-rehearsal-generated-clean",
                source_path="infrastructure/publishing/rehearsal.py",
                timeout_seconds=60,
                capture_output=True,
            ),
        )
        if cleaned.returncode != 0 or cleaned.timed_out:
            return False, cleaned.command_error or "could not remove generated render output"
    return True, f"restored {len(paths)} generated render path(s) in disposable checkout"


def run_clean_checkout_rehearsal(
    repo_root: Path | str,
    plan: CleanCheckoutPlan,
    *,
    platform_name: str,
    timeout_seconds: float = 1800,
) -> CleanCheckoutReceipt:
    """Run two independent local clones for an explicit opt-in rehearsal."""
    root = Path(repo_root).resolve()
    run_receipts: list[CommandReceipt] = []
    run_command_receipts: list[tuple[CommandReceipt, ...]] = []
    output_clean = True
    with tempfile.TemporaryDirectory(prefix="template-release-rehearsal-") as temp_dir:
        parent = Path(temp_dir)
        for index in range(plan.runs):
            checkout = parent / f"checkout-{index}"
            clone_started = monotonic()
            clone = run_with_policy(
                ("git", "clone", "--no-local", "--revision", plan.revision, str(root), str(checkout)),
                cwd=root.parent,
                env=dict(os.environ),
                policy=SubprocessPolicy(
                    policy_id="release-rehearsal-clone",
                    source_path="infrastructure/publishing/rehearsal.py",
                    timeout_seconds=timeout_seconds,
                    capture_output=True,
                ),
            )
            if clone.returncode != 0 or clone.timed_out:
                clone_receipt = CommandReceipt(
                    command=("git", "clone", "--revision", plan.revision),
                    status="blocked",
                    exit_code=clone.returncode,
                    duration_seconds=round(monotonic() - clone_started, 3),
                    output_sha256=_digest_output(clone.stdout, clone.stderr),
                    skip_reason=clone.command_error or "fresh clone failed",
                )
                run_command_receipts.append((clone_receipt,))
                run_receipts.append(clone_receipt)
                output_clean = False
                continue
            receipt_path = parent / f"public-matrix-rehearsal-{index}.json"
            command_receipts = [
                _run_command(_materialize_command(command, receipt_path), checkout, timeout_seconds=timeout_seconds)
                for command in plan.commands
            ]
            pre_clean = run_with_policy(
                ("git", "status", "--porcelain", "--untracked-files=all"),
                cwd=checkout,
                env=dict(os.environ),
                policy=SubprocessPolicy(
                    policy_id="release-rehearsal-clean-status",
                    source_path="infrastructure/publishing/rehearsal.py",
                    timeout_seconds=60,
                    capture_output=True,
                ),
            )
            clean_ok = pre_clean.returncode == 0
            clean_reason = ""
            if clean_ok and pre_clean.stdout.strip():
                clean_ok, clean_reason = _clean_generated_render_output(checkout, pre_clean.stdout)
            clean = run_with_policy(
                ("git", "status", "--porcelain", "--untracked-files=all"),
                cwd=checkout,
                env=dict(os.environ),
                policy=SubprocessPolicy(
                    policy_id="release-rehearsal-clean-status-final",
                    source_path="infrastructure/publishing/rehearsal.py",
                    timeout_seconds=60,
                    capture_output=True,
                ),
            )
            clean_ok = clean_ok and clean.returncode == 0 and not clean.stdout.strip()
            clean_receipt = CommandReceipt(
                command=("git", "status", "--porcelain", "--untracked-files=all"),
                status="pass" if clean_ok else "blocked",
                exit_code=clean.returncode,
                duration_seconds=0.0,
                output_sha256=_digest_output(clean.stdout, clean.stderr),
                skip_reason="" if clean_ok else (clean_reason or "fresh checkout produced tracked or untracked output"),
            )
            command_receipts.append(clean_receipt)
            failed = next((receipt for receipt in command_receipts if receipt.status != "pass"), None)
            status: ReceiptStatus = "pass" if failed is None else "blocked"
            digest = hashlib.sha256(
                "\n".join(receipt.output_sha256 for receipt in command_receipts).encode("ascii")
            ).hexdigest()
            run_command_receipts.append(tuple(command_receipts))
            run_receipts.append(
                CommandReceipt(
                    command=("release-rehearsal", f"run-{index + 1}", plan.revision),
                    status=status,
                    exit_code=0 if status == "pass" else (failed.exit_code if failed else 1),
                    duration_seconds=round(monotonic() - clone_started, 3),
                    output_sha256=digest,
                    skip_reason="" if status == "pass" else (failed.skip_reason if failed else "command failed"),
                )
            )
            output_clean = output_clean and clean_ok
    overall_status: ReceiptStatus = (
        "pass"
        if len(run_receipts) == plan.runs and all(run.status == "pass" for run in run_receipts) and output_clean
        else "blocked"
    )
    return CleanCheckoutReceipt(
        revision=plan.revision,
        platform=platform_name,
        status=overall_status,
        runs=tuple(run_receipts),
        run_commands=tuple(run_command_receipts),
        output_clean=output_clean,
        skip_reason="" if overall_status == "pass" else "fresh-checkout command or clean-output check failed",
    )


__all__ = [
    "CleanCheckoutPlan",
    "DEFAULT_REHEARSAL_COMMANDS",
    "REHEARSAL_RECEIPT_TOKEN",
    "build_clean_checkout_plan",
    "run_clean_checkout_rehearsal",
]
