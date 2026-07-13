"""Project test fixtures."""

from __future__ import annotations

from pathlib import Path
import shutil

import pytest

from src.models import AutoResearchLoopResult

SOURCE_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_COPY_IGNORE = shutil.ignore_patterns(
    ".coverage*",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "htmlcov",
    "*.egg-info",
)


@pytest.fixture(scope="session")
def project_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Return a session sandbox so tests never mutate tracked public outputs."""
    actual_repo_root = next(
        candidate
        for candidate in (SOURCE_PROJECT_ROOT, *SOURCE_PROJECT_ROOT.parents)
        if (candidate / "infrastructure").is_dir()
    )
    repository = tmp_path_factory.mktemp("autoresearch-repo") / "repo"
    destination = repository / "projects" / "templates" / SOURCE_PROJECT_ROOT.name
    destination.parent.mkdir(parents=True)
    shutil.copytree(SOURCE_PROJECT_ROOT, destination, ignore=_COPY_IGNORE)
    (repository / "infrastructure").symlink_to(actual_repo_root / "infrastructure", target_is_directory=True)
    (repository / "scripts").symlink_to(actual_repo_root / "scripts", target_is_directory=True)
    return destination


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Return the template repository root.

    Walk upward from the source project directory until the directory containing
    ``infrastructure/`` is found. Deriving the root by marker rather than a
    fixed ``parents[N]`` index keeps the fixture correct across lifecycle moves
    of the project under ``projects/`` (notably the ``projects/templates/<name>``
    layout introduced by the 5-folder lifecycle refactor, which a hard-coded
    ``parents[1]`` resolved to ``projects/`` instead of the repo root).
    """
    for candidate in (SOURCE_PROJECT_ROOT, *SOURCE_PROJECT_ROOT.parents):
        if (candidate / "infrastructure").is_dir():
            return candidate
    raise RuntimeError(f"Could not locate repo root: no infrastructure/ directory above {SOURCE_PROJECT_ROOT}")


@pytest.fixture(scope="session")
def autoresearch_loop_result(project_root: Path, repo_root: Path) -> AutoResearchLoopResult:
    """Run the full deterministic loop once for read-only output assertions."""
    from src.loop import run_autoresearch_loop

    return run_autoresearch_loop(project_root, repo_root)
