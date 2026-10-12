"""Distribution contract for the reusable Layer-1 Python package."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - Python 3.10
    import tomli as tomllib

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_root_declares_buildable_layer_one_distribution() -> None:
    payload = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert payload["build-system"]["build-backend"] == "hatchling.build"
    assert payload["tool"]["uv"]["package"] is True
    assert payload["project"]["scripts"]["research-template"] == "infrastructure.orchestration.cli:main"
    assert payload["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"] == ["infrastructure"]
    for extra in ("rendering", "publishing", "scientific", "steganography"):
        assert payload["project"]["optional-dependencies"][extra]


def test_default_pipeline_is_a_packaged_resource() -> None:
    pipeline = REPO_ROOT / "infrastructure" / "core" / "pipeline" / "pipeline.yaml"
    assert pipeline.is_file()
    assert "stages:" in pipeline.read_text(encoding="utf-8")


def test_lint_toolchain_is_locked_and_shared_by_ci_and_hooks(capsys: pytest.CaptureFixture[str]) -> None:
    """CI and the pre-commit hook lint the same public scope with the locked ruff.

    CI validates both scopes with ``public_scope ci-paths``, then resolves each
    lint command through ``public_scope lint-paths`` under ``pipefail``. The hook
    resolves the same lint paths, and both must name the identical public scope.
    """
    from infrastructure.project.public_scope import main as public_scope_main

    payload = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dev_dependencies = payload["dependency-groups"]["dev"]

    assert any(dependency.startswith("ruff>=") for dependency in dev_dependencies)
    assert not any(dependency.startswith("black") for dependency in dev_dependencies)

    scope_commands = {
        ".github/workflows/ci.yml": "public_scope ci-paths",
        ".pre-commit-config.yaml": "public_scope lint-paths",
    }
    for relative_path, scope_command in scope_commands.items():
        config = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        assert "uv run ruff check" in config
        assert "uv run ruff format" in config
        assert scope_command in config
        assert "uvx ruff" not in config

    ci = (REPO_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    lint_steps = yaml.safe_load(ci)["jobs"]["lint"]["steps"]
    check_source = next(step["run"] for step in lint_steps if step.get("name") == "Check public source")
    assert check_source.strip().splitlines() == [
        "set -euo pipefail",
        "uv run python -m infrastructure.project.public_scope lint-paths | xargs uv run ruff check",
        "uv run python -m infrastructure.project.public_scope lint-paths | xargs uv run ruff format --check",
        "uv run python -m infrastructure.project.public_scope source-paths | xargs uv run mypy",
    ]

    assert public_scope_main(["ci-paths", "--repo-root", str(REPO_ROOT)]) == 0
    ci_outputs = dict(line.split("=", 1) for line in capsys.readouterr().out.splitlines())
    assert public_scope_main(["lint-paths", "--repo-root", str(REPO_ROOT)]) == 0
    hook_lint_paths = capsys.readouterr().out.strip()
    assert set(ci_outputs) == {"lint_paths", "source_paths"}
    assert ci_outputs["lint_paths"] == hook_lint_paths != ""
