"""Project selection compatibility imports and the interactive picker."""

from collections.abc import Callable, Sequence
from typing import TextIO

from infrastructure.project.discovery import (
    discover_qualified_names,
    resolve_project_info,
    validate_project_slug,
)
from infrastructure.project.project_info import ProjectInfo

__all__ = [
    "discover_qualified_names",
    "resolve_project_info",
    "select_project_interactive",
    "validate_project_slug",
]


def select_project_interactive(
    projects: Sequence[ProjectInfo],
    *,
    current: str | None = None,
    reader: Callable[[], str] = input,
    writer: TextIO | None = None,
) -> str | None:
    """Interactive project picker.

    Args:
        projects: Discovered projects to choose from.
        current: Currently-selected project (highlighted).
        reader: Zero-arg callable that returns the user input line. The
            production caller passes :func:`input`. Tests pass a closure
            over a queue of canned responses.
        writer: Optional text stream for the prompt UI. Defaults to ``None``
            (silent) which is what most tests want; production callers pass
            ``sys.stdout``.

    Returns:
        The qualified name of the selected project, or ``"all"`` if the
        user typed ``a``, or ``None`` if the user typed ``q``.
    """

    def _emit(line: str) -> None:
        if writer is not None:
            writer.write(line + "\n")

    if not projects:
        _emit("No projects available")
        return None

    while True:
        _emit("Available projects:")
        for idx, info in enumerate(projects):
            marker = "→" if info.qualified_name == current else " "
            _emit(f"  {marker} {idx}. {info.qualified_name}")
        _emit("  a. Run all projects")
        _emit("  q. Quit")

        if writer is not None:
            writer.write("Choice [index / a=all / q=quit]: ")
            writer.flush()

        try:
            choice = reader().strip()
        except EOFError:
            return None

        if not choice:
            continue
        if choice in {"q", "Q"}:
            return None
        if choice in {"a", "A"}:
            return "all"
        if choice.isdigit():
            idx = int(choice)
            if 0 <= idx < len(projects):
                return projects[idx].qualified_name
        _emit(f"Invalid selection: {choice!r}")
