"""Explicit pipeline stage hooks.

Hooks are declared in ``pipeline.yaml``. They are deliberately narrow:
commands run with ``shell=False``, receive a stable environment, and are
disabled under CI unless the stage explicitly opts in with ``run_in_ci``.
"""

from __future__ import annotations

import json
import os
import shlex
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Mapping

from infrastructure.core.execution_boundary import (
    build_bounded_env,
    run_bounded_subprocess,
)
from infrastructure.core.files.secure_write import atomic_write_text_confined
from infrastructure.core.pipeline.types import StageHooks


class HookEvent(str, Enum):
    """Supported hook event names."""

    PRE_STAGE = "pre_stage"
    POST_STAGE = "post_stage"
    ON_FAIL = "on_fail"
    ON_PAUSE = "on_pause"


@dataclass(frozen=True)
class StageHookContext:
    """Context exposed to hook commands through JSON and environment."""

    project_name: str
    stage_name: str
    stage_num: int
    run_dir: Path
    status: str
    error_message: str = ""
    deadline_monotonic: float | None = None

    def to_dict(self) -> dict[str, str | int]:
        """Serialize the context into a JSON-safe mapping."""
        return {
            "project_name": self.project_name,
            "stage_name": self.stage_name,
            "stage_num": self.stage_num,
            "run_dir": str(self.run_dir),
            "status": self.status,
            "error_message": self.error_message,
        }


@dataclass(frozen=True)
class HookExecutionResult:
    """Result from one hook command."""

    event: HookEvent
    command: tuple[str, ...]
    success: bool
    duration: float
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    error_message: str = ""
    original_exit_code: int | None = None


def run_stage_hooks(
    hooks: StageHooks,
    event: HookEvent,
    context: StageHookContext,
    *,
    extra_env: Mapping[str, str] | None = None,
    allow_in_ci: bool = False,
    strip_secrets: bool = True,
) -> list[HookExecutionResult]:
    """Run hook commands for ``event`` and return per-command results.

    Hooks run through the bounded execution boundary: a fresh process
    group (so a timeout kills the whole tree, not just the hook), and —
    when ``strip_secrets`` is true — credential-like environment variables
    are removed before launch (secret policy, SECURE-RUN-1).
    """
    if os.environ.get("CI") and not hooks.run_in_ci and not allow_in_ci:
        return []

    commands = _commands_for_event(hooks, event)
    if not commands:
        return []

    context_path = _write_context_file(context)
    raw_env = _build_env(context, context_path, extra_env)
    bounded_env = build_bounded_env(raw_env) if strip_secrets else dict(raw_env)
    results: list[HookExecutionResult] = []
    for command in commands:
        argv = _normalize_command(command)
        if not argv:
            continue
        started = time.monotonic()
        remaining = (
            context.deadline_monotonic - started
            if context.deadline_monotonic is not None
            else float(hooks.timeout_seconds)
        )
        timeout = min(float(hooks.timeout_seconds), remaining)
        if timeout <= 0:
            results.append(
                HookExecutionResult(
                    event, argv, False, 0.0, 124, error_message="Run deadline expired before hook launch"
                )
            )
            break
        completed = run_bounded_subprocess(
            argv,
            cwd=context.run_dir,
            env=bounded_env,
            timeout=timeout,
        )
        if completed.original_returncode in {130, -2} or completed.returncode in {130, -2}:
            results.append(
                HookExecutionResult(
                    event=event,
                    command=argv,
                    success=False,
                    duration=time.monotonic() - started,
                    exit_code=130,
                    stdout=completed.stdout,
                    stderr=completed.stderr,
                    error_message=completed.command_error or "hook interrupted",
                    original_exit_code=completed.original_returncode,
                )
            )
        elif completed.timed_out or completed.original_returncode == 124 or completed.returncode == 124:
            results.append(
                HookExecutionResult(
                    event=event,
                    command=argv,
                    success=False,
                    duration=time.monotonic() - started,
                    exit_code=124,
                    stdout=completed.stdout,
                    stderr=completed.stderr,
                    error_message=completed.command_error or f"hook timed out after {timeout:g}s",
                    original_exit_code=completed.original_returncode,
                )
            )
        elif completed.command_error:
            results.append(
                HookExecutionResult(
                    event=event,
                    command=argv,
                    success=False,
                    duration=time.monotonic() - started,
                    exit_code=1,
                    error_message=completed.command_error,
                    original_exit_code=completed.original_returncode,
                )
            )
        else:
            results.append(
                HookExecutionResult(
                    event=event,
                    command=argv,
                    success=completed.returncode == 0,
                    duration=time.monotonic() - started,
                    exit_code=completed.returncode,
                    stdout=completed.stdout,
                    stderr=completed.stderr,
                    error_message=completed.stderr.strip(),
                    original_exit_code=completed.original_returncode,
                )
            )
        if results[-1].exit_code in {130, 124}:
            break

    return results


def any_hook_failed(results: list[HookExecutionResult]) -> bool:
    """Return true when at least one executed hook failed."""
    return any(not result.success for result in results)


def hook_failure_exit_code(results: list[HookExecutionResult]) -> int:
    """Preserve interruption and timeout precedence across hook diagnostics."""
    codes = {result.exit_code for result in results if not result.success}
    return 130 if 130 in codes else 124 if 124 in codes else 1


def summarize_hook_failures(results: list[HookExecutionResult]) -> str:
    """Build a concise failure summary for stage errors."""
    failures = [result for result in results if not result.success]
    if not failures:
        return ""
    parts = []
    for failure in failures:
        command = " ".join(failure.command)
        detail = failure.error_message or failure.stderr.strip() or "hook failed"
        parts.append(f"{failure.event.value} hook `{command}` failed: {detail}")
    return "; ".join(parts)


def _commands_for_event(hooks: StageHooks, event: HookEvent) -> tuple[tuple[str, ...], ...]:
    if event == HookEvent.PRE_STAGE:
        return hooks.pre_stage
    if event == HookEvent.POST_STAGE:
        return hooks.post_stage
    if event == HookEvent.ON_FAIL:
        return hooks.on_fail
    if event == HookEvent.ON_PAUSE:
        return hooks.on_pause
    return ()


def _normalize_command(command: tuple[str, ...]) -> tuple[str, ...]:
    if len(command) == 1:
        return tuple(shlex.split(command[0]))
    return command


def _write_context_file(context: StageHookContext) -> Path:
    hook_dir = context.run_dir / ".pipeline" / "hooks"
    path = hook_dir / f"stage-{context.stage_num:02d}-{context.stage_name.lower().replace(' ', '-')}.json"
    atomic_write_text_confined(context.run_dir, path, json.dumps(context.to_dict(), indent=2), mode=0o600)
    return path


def _build_env(
    context: StageHookContext,
    context_path: Path,
    extra_env: Mapping[str, str] | None,
) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "TEMPLATE_PROJECT": context.project_name,
            "TEMPLATE_STAGE_NAME": context.stage_name,
            "TEMPLATE_STAGE_NUM": str(context.stage_num),
            "TEMPLATE_RUN_DIR": str(context.run_dir),
            "TEMPLATE_STAGE_CONTEXT": str(context_path),
        }
    )
    if extra_env:
        env.update(dict(extra_env))
    return env
