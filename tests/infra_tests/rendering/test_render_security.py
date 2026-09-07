"""Tests for trusted and hostile-input rendering subprocess profiles."""

import os
import subprocess
from pathlib import Path

import pytest

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.security import RenderSecurityProfile, run_isolated_subprocess, subprocess_options


def test_untrusted_profile_strips_credentials_and_bounds_timeout(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "must-not-inherit")
    profile = RenderSecurityProfile(name="untrusted", timeout_seconds=7, temp_root=tmp_path)

    options = subprocess_options(profile, 600)

    assert options["timeout"] == 7
    child_env = options["env"]
    assert isinstance(child_env, dict)
    assert "GITHUB_TOKEN" not in child_env
    assert child_env["HOME"] == str(tmp_path)


def test_untrusted_profile_rejects_output_escape(tmp_path: Path) -> None:
    profile = RenderSecurityProfile(name="untrusted", temp_root=tmp_path / "isolated")

    with pytest.raises(RenderingError, match="escapes temporary root"):
        profile.validate_output(tmp_path / "outside.html")


@pytest.mark.parametrize(
    "content",
    [
        "<script>fetch('file:///etc/passwd')</script>",
        "![secret](file:///etc/passwd)",
        r"\\input{/etc/passwd}",
        "```mermaid\n!include /etc/passwd\n```",
        "[run](javascript:alert(1))",
    ],
)
def test_untrusted_profile_rejects_active_or_inclusion_content(tmp_path: Path, content: str) -> None:
    source = tmp_path / "hostile.md"
    source.write_text(content, encoding="utf-8")
    profile = RenderSecurityProfile(name="untrusted", temp_root=tmp_path)

    with pytest.raises(RenderingError, match="rejected"):
        profile.validate_source(source)


def test_trusted_profile_preserves_existing_source_contract(tmp_path: Path) -> None:
    source = tmp_path / "trusted.md"
    source.write_text("<script>fixture</script>", encoding="utf-8")

    RenderSecurityProfile().validate_source(source)


def test_rendering_config_exposes_explicit_security_profile(tmp_path: Path) -> None:
    config = RenderingConfig(
        security_profile="untrusted",
        untrusted_temp_root=str(tmp_path),
    )

    assert config.security().untrusted is True
    assert config.security().temp_root == tmp_path


@pytest.mark.parametrize("profile", ("", "untrustd", "UNTRUSTED", "trusted"))
def test_rendering_config_rejects_unknown_security_profile(profile: str) -> None:
    with pytest.raises(ValueError, match="security_profile must be"):
        RenderingConfig(security_profile=profile)  # type: ignore[arg-type]


def test_untrusted_rendering_config_requires_nonempty_temp_root() -> None:
    with pytest.raises(ValueError, match="requires untrusted_temp_root"):
        RenderingConfig(security_profile="untrusted")

    with pytest.raises(ValueError, match="non-empty path string"):
        RenderingConfig(security_profile="untrusted", untrusted_temp_root="")


@pytest.mark.parametrize("profile", ("", "untrustd", "UNTRUSTED", "trusted"))
def test_direct_security_profile_rejects_unknown_name(profile: str) -> None:
    with pytest.raises(ValueError, match="render security profile must be"):
        RenderSecurityProfile(name=profile)  # type: ignore[arg-type]


def test_direct_untrusted_security_profile_requires_temp_root() -> None:
    with pytest.raises(ValueError, match="isolated temporary output root"):
        RenderSecurityProfile(name="untrusted")


def test_environment_security_profile_is_validated(tmp_path: Path) -> None:
    config = RenderingConfig.from_env(
        {
            "RENDER_SECURITY_PROFILE": "untrusted",
            "RENDER_UNTRUSTED_TEMP_ROOT": str(tmp_path),
        }
    )

    assert config.security().untrusted is True
    assert config.security().temp_root == tmp_path

    with pytest.raises(ValueError, match="security_profile must be"):
        RenderingConfig.from_env({"RENDER_SECURITY_PROFILE": "untrustd"})


@pytest.mark.skipif(os.name != "posix", reason="process groups differ on Windows")
def test_isolated_subprocess_reaps_descendant_processes_on_timeout() -> None:
    """Timeout cleanup must terminate the shell's child process group."""
    with pytest.raises(subprocess.TimeoutExpired):
        run_isolated_subprocess(["/bin/sh", "-c", "sleep 30"], timeout=1)


@pytest.mark.skipif(os.name != "posix", reason="process groups differ on Windows")
def test_isolated_subprocess_kills_descendant_that_outlives_parent() -> None:
    """Cleanup must also handle a parent that exits while a child holds pipes."""
    with pytest.raises(subprocess.TimeoutExpired):
        run_isolated_subprocess(["/bin/sh", "-c", "sleep 30 & exit 0"], timeout=1)
