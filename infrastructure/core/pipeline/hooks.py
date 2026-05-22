"""Explicit pipeline stage hooks.

Hooks are declared in ``pipeline.yaml``. They are deliberately narrow:
commands run with ``shell=False``, receive a stable environment, and are
disabled under CI unless the stage explicitly opts in with ``run_in_ci``.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Mapping

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


def run_stage_hooks(
    hooks: StageHooks,
    event: HookEvent,
    context: StageHookContext,
    *,
    extra_env: Mapping[str, str] | None = None,
    allow_in_ci: bool = False,
) -> list[HookExecutionResult]:
    """Run hook commands for ``event`` and return per-command results."""
    if os.environ.get("CI") and not hooks.run_in_ci and not allow_in_ci:
        return []

    commands = _commands_for_event(hooks, event)
    if not commands:
        return []

    context_path = _write_context_file(context)
    env = _build_env(context, context_path, extra_env)
    results: list[HookExecutionResult] = []
    for command in commands:
        argv = _normalize_command(command)
        if not argv:
            continue
        started = time.monotonic()
        try:
            completed = subprocess.run(
                argv,
                cwd=str(context.run_dir),
                env=env,
                capture_output=True,
                text=True,
                timeout=hooks.timeout_seconds,
                check=False,
            )
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
                )
            )
        except subprocess.TimeoutExpired as exc:
            results.append(
                HookExecutionResult(
                    event=event,
                    command=argv,
                    success=False,
                    duration=time.monotonic() - started,
                    exit_code=124,
                    stdout=exc.stdout or "",
                    stderr=exc.stderr or "",
                    error_message=f"hook timed out after {hooks.timeout_seconds}s",
                )
            )
        except OSError as exc:
            results.append(
                HookExecutionResult(
                    event=event,
                    command=argv,
                    success=False,
                    duration=time.monotonic() - started,
                    exit_code=1,
                    error_message=str(exc),
                )
            )

    return results


def any_hook_failed(results: list[HookExecutionResult]) -> bool:
    """Return true when at least one executed hook failed."""
    return any(not result.success for result in results)


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
    hook_dir.mkdir(parents=True, exist_ok=True)
    path = hook_dir / f"stage-{context.stage_num:02d}-{context.stage_name.lower().replace(' ', '-')}.json"
    path.write_text(json.dumps(context.to_dict(), indent=2), encoding="utf-8")
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
