"""Project test fixtures."""

from __future__ import annotations

import os
import sys
from collections.abc import Callable, Iterator
from pathlib import Path
import shutil
import subprocess

import pytest

SOURCE_PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Expose only this project's unique test helper and domain source package.
sys.path.insert(0, str(SOURCE_PROJECT_ROOT / "tests"))
sys.path.insert(0, str(SOURCE_PROJECT_ROOT / "src"))

from autoresearch_source_provider import SourceProvider, resolve_source_provider
from template_autoresearch_project.loop.models import AutoResearchLoopResult

_COPY_IGNORE = shutil.ignore_patterns(
    ".git",
    ".coverage*",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "htmlcov",
    "*.egg-info",
)


@pytest.fixture(scope="session")
def initialize_git_repository() -> Callable[[Path], None]:
    """Create real test-owned Git boundaries, isolated from ancestor repositories."""
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)

    def initialize(root: Path) -> None:
        subprocess.run(
            ["git", "init", "--quiet", str(root)],
            env=environment,
            stdin=subprocess.DEVNULL,
            check=True,
            capture_output=True,
            timeout=30,
        )

    return initialize


@pytest.fixture(scope="session")
def platform_source_provider() -> Iterator[SourceProvider]:
    """Admit actual source inputs without changing installed platform imports."""
    provider = resolve_source_provider(SOURCE_PROJECT_ROOT, os.environ)
    yield provider
    provider.assert_unchanged()


@pytest.fixture(scope="session")
def project_root(
    tmp_path_factory: pytest.TempPathFactory,
    platform_source_provider: SourceProvider,
    initialize_git_repository: Callable[[Path], None],
) -> Path:
    """Return a real repository sandbox so tests never mutate tracked public outputs."""
    actual_repo_root = platform_source_provider.root
    repository = tmp_path_factory.mktemp("autoresearch-repo") / "repo"
    destination = repository / "projects" / "templates" / SOURCE_PROJECT_ROOT.name
    destination.parent.mkdir(parents=True)
    shutil.copytree(SOURCE_PROJECT_ROOT, destination, ignore=_COPY_IGNORE)
    # The infrastructure source runtime resolves its version from this canonical
    # metadata when the independent project environment has no platform wheel.
    shutil.copy2(actual_repo_root / "pyproject.toml", repository / "pyproject.toml")
    (repository / "infrastructure").symlink_to(actual_repo_root / "infrastructure", target_is_directory=True)
    (repository / "scripts").symlink_to(actual_repo_root / "scripts", target_is_directory=True)
    # Public inventory must use this sandbox's ignores, not the enclosing vault's.
    initialize_git_repository(repository)
    return destination


@pytest.fixture(scope="session")
def repo_root(platform_source_provider: SourceProvider) -> Path:
    """Return the admitted source provider for actual pipeline/build inputs."""
    return platform_source_provider.root


@pytest.fixture(scope="session")
def autoresearch_loop_result(project_root: Path, repo_root: Path) -> AutoResearchLoopResult:
    """Run the full deterministic loop once for read-only output assertions."""
    from template_autoresearch_project.loop.loop import run_autoresearch_loop

    return run_autoresearch_loop(project_root, repo_root)
