"""Tests for ``infrastructure.rendering.dockerfile_gen``.

Pure string-rendering tests — no mocks, no network, no Docker required.
"""

from __future__ import annotations

import pytest

from infrastructure.rendering.dockerfile_gen import (
    DEFAULT_BASE_IMAGE,
    DEFAULT_LATEX_PACKAGES,
    DEFAULT_UV_VERSION,
    DockerfileConfig,
    build_compose_yaml,
    build_dockerfile,
)


def test_build_dockerfile_includes_project_name() -> None:
    text = build_dockerfile(DockerfileConfig(project_name="example_project", python_version="3.12"))
    assert "example_project" in text


def test_build_dockerfile_starts_from_default_base_image() -> None:
    text = build_dockerfile(DockerfileConfig(project_name="x", python_version="3.12"))
    assert f"FROM {DEFAULT_BASE_IMAGE}" in text


def test_build_dockerfile_includes_python_version() -> None:
    text = build_dockerfile(DockerfileConfig(project_name="x", python_version="3.11"))
    assert "python3.11" in text


def test_build_dockerfile_includes_default_latex_packages() -> None:
    text = build_dockerfile(DockerfileConfig(project_name="x", python_version="3.12"))
    for pkg in DEFAULT_LATEX_PACKAGES:
        assert pkg in text, f"Missing LaTeX package {pkg}"


def test_build_dockerfile_uses_custom_latex_packages() -> None:
    text = build_dockerfile(
        DockerfileConfig(
            project_name="x",
            python_version="3.12",
            latex_packages=("texlive-only-one",),
        )
    )
    assert "texlive-only-one" in text
    # Should not include defaults if overridden
    assert "texlive-fonts-extra" not in text


def test_build_dockerfile_installs_uv() -> None:
    text = build_dockerfile(DockerfileConfig(project_name="x", python_version="3.12"))
    assert "astral.sh/uv/" in text
    assert "install.sh" in text


def test_build_dockerfile_pins_uv_version_by_default() -> None:
    text = build_dockerfile(DockerfileConfig(project_name="x", python_version="3.12"))
    # Default config pins uv: the installer URL is versioned, not the floating endpoint.
    assert f"https://astral.sh/uv/{DEFAULT_UV_VERSION}/install.sh" in text
    assert "https://astral.sh/uv/install.sh" not in text


def test_build_dockerfile_latest_uses_unversioned_installer() -> None:
    text = build_dockerfile(DockerfileConfig(project_name="x", python_version="3.12", uv_version="latest"))
    assert "https://astral.sh/uv/install.sh" in text


def test_build_dockerfile_is_deterministic_no_timestamp() -> None:
    cfg = DockerfileConfig(project_name="x", python_version="3.12")
    first = build_dockerfile(cfg)
    second = build_dockerfile(cfg)
    assert first == second
    # No wall-clock timestamp comment leaks into the output.
    assert "Generated at" not in first


def test_build_dockerfile_runs_uv_sync_frozen() -> None:
    text = build_dockerfile(DockerfileConfig(project_name="x", python_version="3.12"))
    assert "uv sync --frozen" in text


def test_build_dockerfile_sets_headless_matplotlib() -> None:
    text = build_dockerfile(DockerfileConfig(project_name="x", python_version="3.12"))
    assert "MPLBACKEND=Agg" in text


def test_build_dockerfile_default_cmd_invokes_pipeline() -> None:
    text = build_dockerfile(DockerfileConfig(project_name="my_proj", python_version="3.12"))
    assert "--project my_proj" in text
    assert "--core-only" in text


def test_build_dockerfile_includes_tlmgr_packages() -> None:
    text = build_dockerfile(
        DockerfileConfig(
            project_name="x",
            python_version="3.12",
            tlmgr_packages=("multirow", "cleveref"),
        )
    )
    assert "tlmgr install multirow cleveref" in text


def test_build_compose_yaml_includes_four_services() -> None:
    text = build_compose_yaml("example")
    for service in ("reproduce:", "tests:", "render:", "verify:"):
        assert service in text


def test_build_compose_yaml_uses_project_name_in_image_tag() -> None:
    text = build_compose_yaml("my_proj")
    assert "template-bundle-my_proj:latest" in text


def test_dockerfile_config_immutable() -> None:
    cfg = DockerfileConfig(project_name="x", python_version="3.12")
    with pytest.raises((AttributeError, Exception)):
        cfg.project_name = "y"  # type: ignore[misc]
