"""Optional platform4 admission and audited argv for full verification.

The scientific package remains standalone. This dev-only adapter reuses the
platform's actual source-code audit and existing selected-runtime probe. Runtime
dependency metadata is declaration identity, not universal member-byte custody.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from .verification_execution import VerificationCommandFailed, VerificationRuntimeUnavailable


def _platform() -> None:
    try:
        installed = version("research-project-template")
    except PackageNotFoundError as exc:
        raise VerificationRuntimeUnavailable("Prepare the verifier dev extra with platform4.4.0 explicitly") from exc
    if installed != "4.4.0":
        raise VerificationRuntimeUnavailable("Full verification requires prepared platform4.4.0")


@dataclass(frozen=True)
class VerificationRuntime:
    """One admitted selected runtime used by every verifier child."""

    project_root: Path
    interpreter: Path
    binding: dict[str, object]

    def command(self, command: list[str]) -> list[str]:
        from infrastructure.core.testing.project_test_runtime import build_audited_project_test_command

        if not command or Path(command[0]).absolute() != self.interpreter:
            raise ValueError("Verifier command differs from its admitted lexical interpreter")
        if command[1:3] == ["-m", "pytest"]:
            # The Stage-01 verifier clears ambient pytest options. Nominate the
            # same default-only storage control as the generic project runner
            # directly, so optional benchmark setup cannot create Source dirs.
            arguments = tuple(command[3:])
            option_end = arguments.index("--") if "--" in arguments else len(arguments)
            controls = (
                "-p",
                "infrastructure.core.testing._pytest_runtime_controls",
                f"--template-benchmark-storage={self.project_root / 'output/.pipeline/benchmarks'}",
            )
            arguments = (*arguments[:option_end], *controls, *arguments[option_end:])
            return list(
                build_audited_project_test_command(self.project_root, self.interpreter, arguments, module="pytest")
            )
        if len(command) < 2:
            raise ValueError("Verifier requires a project script or pytest module")
        target = Path(command[1])
        if not target.is_absolute():
            target = self.project_root / target
        relative = target.relative_to(self.project_root)
        if not relative.parts or ".." in relative.parts or relative.parts[0] != "scripts" or target.suffix != ".py":
            raise ValueError("Verifier scripts must be explicit project scripts/*.py paths")
        return list(
            build_audited_project_test_command(self.project_root, self.interpreter, tuple(command[2:]), script=target)
        )

    def verify(self) -> None:
        from infrastructure.core.runtime.python_binding import analysis_runtime_binding

        if analysis_runtime_binding(self.project_root, interpreter=self.interpreter) != self.binding:
            raise VerificationRuntimeUnavailable("Selected verifier runtime declarations changed during execution")


def prepare_verification_runtime(project_root: Path, interpreter: str, deadline: float) -> VerificationRuntime:
    """Require actual selected platform/test versions before any domain child."""
    _platform()
    try:
        from infrastructure.core.testing.project_test_runtime import (
            ProjectTestRuntimeError,
            admit_project_test_runtime,
        )
    except ImportError as exc:
        raise VerificationRuntimeUnavailable("Prepared platform audit helper is unavailable") from exc
    try:
        selected, packet = admit_project_test_runtime(
            project_root,
            deadline=deadline,
            interpreter=Path(interpreter),
            required_distributions={"research-project-template": "4.4.0"},
        )
    except ProjectTestRuntimeError as exc:
        if exc.exit_code in {124, 130}:
            raise VerificationCommandFailed(
                str(exc), original_exit_code=exc.original_exit_code, timed_out=exc.exit_code == 124
            ) from exc
        raise VerificationRuntimeUnavailable(str(exc)) from exc
    binding = packet["binding"]
    if not isinstance(binding, dict):
        raise VerificationRuntimeUnavailable("Prepared runtime admission did not bind its declarations")
    return VerificationRuntime(project_root.absolute(), selected, binding)
