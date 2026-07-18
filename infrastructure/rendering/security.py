"""Security profiles for renderer subprocesses."""

from __future__ import annotations

import os
import re
import signal
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from infrastructure.core.exceptions import RenderingError

_UNTRUSTED_SOURCE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "unsafe HTML or event handler",
        re.compile(r"<\s*(?:script|iframe|object|embed)\b|\bon(?:error|load|click)\s*=", re.IGNORECASE),
    ),
    (
        "file or command inclusion",
        re.compile(
            r"file://|(?:\.\./)+|!include\b|\\(?:input|include|openin|read|write18|shellescape)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "unsafe URL scheme",
        re.compile(r"(?:javascript:|data:text/html)", re.IGNORECASE),
    ),
)


@dataclass(frozen=True)
class RenderSecurityProfile:
    """Describe the process boundary used for renderer child processes."""

    name: str = "trusted-local"
    timeout_seconds: int = 600
    temp_root: Path | None = None

    @property
    def untrusted(self) -> bool:
        """Return whether the profile must strip inherited credentials."""
        return self.name == "untrusted"

    def validate_output(self, path: Path) -> None:
        """Require untrusted outputs to be inside the caller-provided temp root."""
        if not self.untrusted:
            return
        if self.temp_root is None:
            raise RenderingError("untrusted rendering requires an isolated temporary output root")
        root = self.temp_root.resolve()
        try:
            path.resolve().relative_to(root)
        except ValueError as exc:
            raise RenderingError(f"untrusted renderer output escapes temporary root: {path}") from exc

    def validate_source(self, path: Path) -> None:
        """Reject known inclusion and active-content primitives for untrusted input."""
        if not self.untrusted:
            return
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise RenderingError(f"untrusted renderer cannot read source: {path}") from exc
        for label, pattern in _UNTRUSTED_SOURCE_PATTERNS:
            if pattern.search(content):
                raise RenderingError(f"untrusted renderer rejected {label}: {path}")

    def environment(self) -> dict[str, str] | None:
        """Return a credential-free child environment for untrusted rendering."""
        if not self.untrusted:
            return None
        if self.temp_root is None:
            raise RenderingError("untrusted rendering requires an isolated temporary output root")
        self.temp_root.mkdir(parents=True, exist_ok=True)
        inherited = os.environ
        safe = {key: inherited[key] for key in ("PATH", "LANG", "LC_ALL") if key in inherited}
        safe.update({"HOME": str(self.temp_root), "TMPDIR": str(self.temp_root)})
        return safe


class SubprocessOptions(TypedDict):
    """Typed kwargs accepted by renderer subprocess calls."""

    timeout: int
    env: dict[str, str] | None


def subprocess_options(profile: RenderSecurityProfile, timeout: int) -> SubprocessOptions:
    """Build subprocess kwargs while applying profile timeout and environment."""
    return {
        "timeout": min(timeout, profile.timeout_seconds),
        "env": profile.environment(),
    }


def run_isolated_subprocess(
    args: list[str],
    *,
    timeout: int,
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a renderer helper and terminate its descendant process group on timeout.

    ``subprocess.run(timeout=...)`` terminates the direct child but does not
    reliably reap browser descendants spawned by tools such as Mermaid CLI.
    A fresh session gives the renderer a process-group boundary; timeout
    cleanup then terminates the complete group before reaping the pipes.
    """
    process = subprocess.Popen(
        args,
        cwd=str(cwd) if cwd is not None else None,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        _terminate_process_group(process)
        try:
            process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            # A descendant can retain the pipes even after the direct child
            # exits. Re-issue group termination and make one short reap
            # attempt before propagating the original timeout.
            _terminate_process_group(process, force=True)
            try:
                process.communicate(timeout=1)
            except subprocess.TimeoutExpired:
                pass
        raise
    return subprocess.CompletedProcess(args=args, returncode=process.returncode or 0, stdout=stdout, stderr=stderr)


def _terminate_process_group(process: subprocess.Popen[str], *, force: bool = False) -> None:
    """Best-effort termination of a timed-out renderer process tree."""
    if os.name != "posix" and process.poll() is not None and not force:
        return
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
    else:  # pragma: no cover - Windows-only fallback
        process.terminate()
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                return
        else:  # pragma: no cover - Windows-only fallback
            process.kill()


__all__ = ["RenderSecurityProfile", "SubprocessOptions", "run_isolated_subprocess", "subprocess_options"]
