"""Tests for ``infrastructure.rendering.dockerfile_gen``.

Pure string-rendering tests — no mocks, no network, no Docker required.
"""

from __future__ import annotations

import pytest

from infrastructure.rendering.dockerfile_gen import (
    DEFAULT_BASE_IMAGE,
    DEFAULT_LATEX_PACKAGES,
    DEFAULT_UV_INSTALL_SHA256,
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
    assert "github.com/astral-sh/uv/releases/download/" in text
    assert "uv-installer.sh" in text


def test_build_dockerfile_pins_uv_version_by_default() -> None:
    text = build_dockerfile(DockerfileConfig(project_name="x", python_version="3.12"))
    # Default config pins uv: the installer URL is versioned, not the floating endpoint.
    assert f"https://github.com/astral-sh/uv/releases/download/{DEFAULT_UV_VERSION}/uv-installer.sh" in text
    assert "https://astral.sh/uv/install.sh" not in text
    assert DEFAULT_UV_INSTALL_SHA256 in text
    assert "sha256sum -c -" in text
    assert "curl --proto '=https' --tlsv1.2 -fsSL" in text
    assert "curl -fsSL https://astral.sh/uv/0.12.0/install.sh | sh" not in text


def test_build_dockerfile_latest_uses_unversioned_installer() -> None:
    text = build_dockerfile(DockerfileConfig(project_name="x", python_version="3.12", uv_version="latest"))
    assert "https://astral.sh/uv/install.sh" in text
    assert "latest is intentionally floating" in text


def test_build_dockerfile_requires_digest_for_concrete_custom_uv() -> None:
    with pytest.raises(ValueError, match="uv_sha256"):
        build_dockerfile(DockerfileConfig(project_name="x", python_version="3.12", uv_version="0.12.0", uv_sha256=None))

    with pytest.raises(ValueError, match="64 hexadecimal"):
        build_dockerfile(DockerfileConfig(project_name="x", python_version="3.12", uv_sha256="not-a-digest"))


def test_build_dockerfile_accepts_digest_for_concrete_custom_uv() -> None:
    digest = "a" * 64
    text = build_dockerfile(
        DockerfileConfig(project_name="x", python_version="3.12", uv_version="0.12.0", uv_sha256=digest)
    )
    assert "https://github.com/astral-sh/uv/releases/download/0.12.0/uv-installer.sh" in text
    assert digest in text


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
    assert "--mode core" in text


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


def test_build_dockerfile_bootstraps_deadsnakes_for_non_native_python() -> None:
    # ubuntu:24.04 ships Python 3.12; requesting 3.14 without the deadsnakes
    # PPA produced an image build that failed with "Unable to locate package
    # python3.14". The generator must emit the PPA bootstrap for any version
    # the base image does not natively provide.
    text = build_dockerfile(DockerfileConfig(project_name="x", python_version="3.14"))
    assert "add-apt-repository -y ppa:deadsnakes/ppa" in text
    assert "python3.14" in text


def test_build_dockerfile_omits_deadsnakes_for_native_python() -> None:
    text = build_dockerfile(DockerfileConfig(project_name="x", python_version="3.12"))
    assert "deadsnakes" not in text


def test_build_compose_yaml_verify_service_collects_payload_tests() -> None:
    # EXECUTABLE-BUNDLE-MAJ-2: the payload is single-project and vendored, so
    # `verify` proves collection cleanliness against source/ instead of running
    # repo-root regression tests that no bundle carries.
    text = build_compose_yaml("templates/my_proj")
    assert "cd /workspace/source" in text
    assert "pytest --collect-only -q" in text


def test_dockerfile_config_immutable() -> None:
    cfg = DockerfileConfig(project_name="x", python_version="3.12")
    with pytest.raises((AttributeError, Exception)):
        cfg.project_name = "y"  # type: ignore[misc]


@pytest.mark.parametrize("version", ["3.15", "3.14"])
def test_build_dockerfile_binds_selected_python(version: str) -> None:
    text = build_dockerfile(DockerfileConfig(project_name="x", python_version=version))
    assert f"UV_PYTHON={version}" in text
    assert "UV_UNMANAGED_INSTALL=/usr/local/bin" in text
    assert "uv 0.13.0" in text
    assert "--proto '=https' --tlsv1.2" in text


@pytest.mark.parametrize("version", ["3.15\nRUN false", "latest", "python3.15"])
def test_build_dockerfile_rejects_invalid_python_tag(version: str) -> None:
    with pytest.raises(ValueError, match="python_version"):
        build_dockerfile(DockerfileConfig(project_name="x", python_version=version))


@pytest.mark.parametrize("version", ["0.13.0;false", "0.13.0\nRUN false"])
def test_build_dockerfile_rejects_invalid_uv_version(version: str) -> None:
    with pytest.raises(ValueError, match="uv_version"):
        build_dockerfile(
            DockerfileConfig(project_name="x", python_version="3.15", uv_version=version, uv_sha256="a" * 64)
        )
