"""Distribution contract for the reusable Layer-1 Python package."""

from __future__ import annotations

import os
import subprocess
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


def test_lint_toolchain_is_locked_and_shared_by_ci_and_hooks(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    """CI and the pre-commit hook lint the same public scope with the locked ruff.

    The actual CI Bash resolves both scopes once, preserves producer failure,
    and passes the same nonempty lint array to both Ruff commands. The hook
    resolves the same public scope through its legacy single-value command.
    """
    from infrastructure.project.public_scope import main as public_scope_main

    payload = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dev_dependencies = payload["dependency-groups"]["dev"]

    assert any(dependency.startswith("ruff>=") for dependency in dev_dependencies)
    assert not any(dependency.startswith("black") for dependency in dev_dependencies)

    scope_commands = {
        ".github/actions/run-public-lint/action.yml": "public_scope ci-paths",
        ".pre-commit-config.yaml": "public_scope lint-paths",
    }
    for relative_path, scope_command in scope_commands.items():
        config = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        assert "uv run ruff check" in config
        assert "uv run ruff format" in config
        assert scope_command in config
        assert "uvx ruff" not in config

    # CI keeps one implementation of the public gates: the lint job delegates to
    # the shared composite action, and the action owns the scope producer.
    ci = yaml.safe_load((REPO_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    lint_steps = ci["jobs"]["lint"]["steps"]
    public_lint = next(step for step in lint_steps if step.get("uses") == "./.github/actions/run-public-lint")
    assert public_lint.get("with", {}).get("safety-scan") == "true"
    action_text = (REPO_ROOT / ".github/actions/run-public-lint/action.yml").read_text(encoding="utf-8")
    assert action_text.count("public_scope ci-paths") == 1
    check_source = yaml.safe_load(action_text)["runs"]["steps"][0]["run"]
    assert 'uv run ruff check "${PUBLIC_CI_LINT_PATHS[@]}"' in check_source
    assert 'uv run ruff format --check "${PUBLIC_CI_LINT_PATHS[@]}"' in check_source
    assert 'uv run mypy "${PUBLIC_CI_SOURCE_PATHS[@]}"' in check_source
    # The producer and its nonempty admission are one blocking preamble that ends
    # before any concurrent gate starts.
    producer_start = check_source.index("PUBLIC_CI_PATHS=$(")
    scope_preparation = "set -euo pipefail\n" + check_source[producer_start : check_source.index("log_directory=")]

    assert public_scope_main(["ci-paths", "--repo-root", str(REPO_ROOT)]) == 0
    ci_outputs = dict(line.split("=", 1) for line in capsys.readouterr().out.splitlines())
    assert public_scope_main(["lint-paths", "--repo-root", str(REPO_ROOT)]) == 0
    hook_lint_paths = capsys.readouterr().out.strip()
    assert set(ci_outputs) == {"lint_paths", "source_paths"}
    assert ci_outputs["lint_paths"] == hook_lint_paths != ""

    for name, key in (("PUBLIC_CI_LINT_PATHS", "lint_paths"), ("PUBLIC_CI_SOURCE_PATHS", "source_paths")):
        result = subprocess.run(
            ["bash", "-c", scope_preparation + f'printf "%s\\0" "${{{name}[@]}}"'],
            cwd=REPO_ROOT,
            env=dict(os.environ, UV_FROZEN="true"),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.split("\0")[:-1] == ci_outputs[key].split()

    marker = tmp_path / "consumer-reached"
    # A genuinely rejected CLI command exercises the producer's real nonzero
    # exit; no lint/type executable or dependency is replaced by this control.
    failed_producer = scope_preparation.replace("public_scope ci-paths", "public_scope invalid-ci-paths")
    result = subprocess.run(
        ["bash", "-c", failed_producer + 'touch "$CONSUMER_MARKER"'],
        cwd=REPO_ROOT,
        env=dict(os.environ, UV_FROZEN="true", CONSUMER_MARKER=str(marker)),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode != 0 and "invalid choice" in result.stderr
    assert not marker.exists(), "CI continued after the source-scope producer failed"
