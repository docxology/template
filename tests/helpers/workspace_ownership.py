"""Read-only detection of persistent test workspaces; no unowned cleanup."""

from __future__ import annotations

from contextlib import contextmanager
from collections.abc import Iterator
from pathlib import Path

TEST_WORKSPACE_NAMES = ("project1", "project2", "test", "test_project")


def _present(path: Path) -> bool:
    """Include dangling symlinks without inspecting their target contents."""
    return path.is_symlink() or path.exists()


@contextmanager
def guard_test_workspaces(projects_dir: Path) -> Iterator[None]:
    """Preserve preexisting and newly created paths; flag unowned test leaks.

    Generic names cannot prove ownership. Pytest's tmp_path/tmp_path_factory
    owns ephemeral trees; session teardown has no authority to remove a
    persistent projects/ path, including one created concurrently.
    """
    before = {name for name in TEST_WORKSPACE_NAMES if _present(projects_dir / name)}
    yield
    leaked = [name for name in TEST_WORKSPACE_NAMES if name not in before and _present(projects_dir / name)]
    if leaked:
        raise RuntimeError(
            "Root tests left persistent named workspaces under projects/: "
            + ", ".join(leaked)
            + ". All contents were preserved; use tmp_path or an explicitly owned disposable tree."
        )
