"""Real diagnostic CLI refusal controls, before any expensive native preparation."""

from __future__ import annotations

import hashlib
import subprocess
import sys
import time
from pathlib import Path

import pytest

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.native_installed_preflight import PREFLIGHT_SCOPE, diagnostic_exit_code
from infrastructure.reporting.native_preflight_budget import PREFLIGHT_MAX_OPERATION_SECONDS


@pytest.mark.parametrize("code", (1, 75, 124, 130))
def test_preflight_keeps_original_early_failure_without_positive_scope_fields(code: int) -> None:
    assert (
        diagnostic_exit_code(
            {"exit_code": code, "blockers": [{"reason": "actual early refusal"}]}, deadline=time.monotonic() - 1
        )
        == code
    )


@pytest.mark.parametrize("summary", (None, {}, {"complete_selection": True, "selected_projects": [PREFLIGHT_SCOPE]}))
def test_success_cannot_masquerade_as_complete_release_acceptance(summary: object) -> None:
    with pytest.raises(ValueError, match="cannot claim the complete release selection"):
        diagnostic_exit_code({"exit_code": 0, "native_formats": summary}, deadline=time.monotonic() + 10)


def test_preflight_success_remains_exactly_one_incomplete_scope() -> None:
    assert (
        diagnostic_exit_code(
            {"exit_code": 0, "native_formats": {"complete_selection": False, "selected_projects": [PREFLIGHT_SCOPE]}},
            deadline=time.monotonic() + 10,
        )
        == 0
    )


def test_zero_exit_after_the_original_deadline_remains_refused() -> None:
    with pytest.raises(TimeoutError, match="public reference deadline exhausted"):
        diagnostic_exit_code(
            {"exit_code": 0, "native_formats": {"complete_selection": False, "selected_projects": [PREFLIGHT_SCOPE]}},
            deadline=time.monotonic() - 1,
        )


def _arguments(tmp_path: Path) -> list[str]:
    manifest = tmp_path / "implementation.json"
    manifest.write_bytes(b'{"owned_fixture":true}\n')
    arguments = [sys.executable, "-m", "infrastructure.reporting.native_installed_preflight"]
    for name in (
        "repo-root",
        "current-analysis-root",
        "evidence-dir",
        "sdk-package-root",
        "pdfium-site",
        "pdfium-wheel",
        "mermaid-package-root",
        "mermaid-dependency-root",
        "mermaid-node-executable",
        "mermaid-chrome-executable",
    ):
        arguments.extend(("--" + name, str(tmp_path / name)))
    arguments.extend(
        (
            "--implementation-input",
            str(manifest),
            "--implementation-sha256",
            hashlib.sha256(manifest.read_bytes()).hexdigest(),
            "--expected-platform",
            "Linux",
        )
    )
    return arguments


def _run(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(arguments, capture_output=True, text=True, check=False, timeout=30)


@pytest.mark.parametrize("timeout", ("0", "-1", str(PREFLIGHT_MAX_OPERATION_SECONDS + 1), "14400"))
def test_preflight_refuses_extended_or_missing_operation_budget(tmp_path: Path, timeout: str) -> None:
    result = _run(
        [*_arguments(tmp_path), "--timeout", timeout, "--operation-started-monotonic", str(time.monotonic() - 1)]
    )
    assert result.returncode == 2
    assert f"at-most-{PREFLIGHT_MAX_OPERATION_SECONDS}-second outer clock" in result.stderr
    assert not (tmp_path / "evidence-dir").exists()


@pytest.mark.parametrize("clock", ("0", "-1", "nan", "inf", "future"))
def test_preflight_refuses_invalid_or_restarted_clock(tmp_path: Path, clock: str) -> None:
    started = str(time.monotonic() + 1000) if clock == "future" else clock
    result = _run(
        [
            *_arguments(tmp_path),
            "--timeout",
            str(PREFLIGHT_MAX_OPERATION_SECONDS),
            "--operation-started-monotonic",
            started,
        ]
    )
    assert result.returncode == 2
    assert f"at-most-{PREFLIGHT_MAX_OPERATION_SECONDS}-second outer clock" in result.stderr
    assert not (tmp_path / "evidence-dir").exists()


def test_preflight_retains_expired_original_deadline(tmp_path: Path) -> None:
    result = _run(
        [*_arguments(tmp_path), "--timeout", "1", "--operation-started-monotonic", str(time.monotonic() - 60)]
    )
    assert result.returncode != 0
    assert "TimeoutError: public reference deadline exhausted" in result.stderr
    assert not (tmp_path / "evidence-dir").exists()


@pytest.mark.parametrize("nomination", ("missing", "duplicate", "unknown"))
def test_preflight_requires_all_actual_unique_provider_nominations(tmp_path: Path, nomination: str) -> None:
    arguments = [
        *_arguments(tmp_path),
        "--timeout",
        "900",
        "--operation-started-monotonic",
        str(time.monotonic() - 1),
    ]
    if nomination == "duplicate":
        for _ in range(2):
            arguments.extend(("--provider-wheel", PUBLIC_PROJECT_NAMES[0] + "=" + str(tmp_path / "wheel.whl")))
    elif nomination == "unknown":
        arguments.extend(("--provider-wheel", "templates/unknown=" + str(tmp_path / "wheel.whl")))
    result = _run(arguments)
    assert result.returncode != 0
    assert "provider" in result.stderr
    assert not (tmp_path / "evidence-dir").exists()


def test_preflight_refuses_mismatched_externally_held_implementation(tmp_path: Path) -> None:
    arguments = _arguments(tmp_path)
    arguments[arguments.index("--implementation-sha256") + 1] = "a" * 64
    result = _run([*arguments, "--timeout", "900", "--operation-started-monotonic", str(time.monotonic() - 1)])
    assert result.returncode != 0
    assert "differs from the actual externally held input" in result.stderr
    assert not (tmp_path / "evidence-dir").exists()


@pytest.mark.parametrize("mode", ("original", "reader", "handoff"))
def test_complete_native_modes_keep_the_public_roster_without_diagnostic_selection(tmp_path: Path, mode: str) -> None:
    from infrastructure.reporting.native_installed_launcher import native_preparation_scopes

    assert native_preparation_scopes(mode, tmp_path) == PUBLIC_PROJECT_NAMES
    with pytest.raises(ValueError, match="unknown"):
        native_preparation_scopes("unknown", tmp_path)


def test_preflight_build_selection_follows_genuine_transitive_local_metadata(tmp_path: Path) -> None:
    from infrastructure.reporting.native_installed_launcher import native_preparation_scopes
    from infrastructure.reporting.native_installed_preflight import preflight_provider_scopes

    peer = "templates/template_template"
    assert peer != PREFLIGHT_SCOPE and peer in PUBLIC_PROJECT_NAMES
    code = tmp_path / "projects" / PREFLIGHT_SCOPE
    dependency = tmp_path / "projects" / peer
    code.mkdir(parents=True)
    dependency.mkdir(parents=True)
    (code / "pyproject.toml").write_text(
        '[project]\nname="owned-code"\nversion="1"\ndependencies=["owned-peer>=1"]\n'
        '[tool.uv.sources]\nowned-peer={path="../template_template"}\n'
    )
    (dependency / "pyproject.toml").write_text('[project]\nname="owned-peer"\nversion="1"\n')
    assert preflight_provider_scopes(tmp_path) == (PREFLIGHT_SCOPE, peer)
    assert native_preparation_scopes("preflight", tmp_path) == (PREFLIGHT_SCOPE, peer)
    leaf = next(scope for scope in PUBLIC_PROJECT_NAMES if scope not in {PREFLIGHT_SCOPE, peer})
    leaf_root = tmp_path / "projects" / leaf
    leaf_root.mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text('[project]\nname="research-project-template"\nversion="1"\n')
    (leaf_root / "pyproject.toml").write_text(
        '[project]\nname="owned-leaf"\nversion="1"\ndependencies=["research-project-template>=1"]\n'
        '[tool.uv.sources]\nresearch-project-template={path="../../.."}\n'
    )
    (dependency / "pyproject.toml").write_text(
        '[project]\nname="owned-peer"\nversion="1"\ndependencies=["owned-leaf>=1"]\n'
        f'[tool.uv.sources]\nowned-leaf={{path="../{Path(leaf).name}"}}\n'
    )
    assert preflight_provider_scopes(tmp_path) == (PREFLIGHT_SCOPE, leaf, peer)
    (dependency / "pyproject.toml").write_text(
        '[project]\nname="owned-peer"\nversion="1"\ndependencies=["owned-code>=1"]\n'
        '[tool.uv.sources]\nowned-code={path="../template_code_project"}\n'
    )
    with pytest.raises(ValueError, match="cycle"):
        preflight_provider_scopes(tmp_path)
    (code / "pyproject.toml").write_text('[project]\nname="owned-code"\nversion="1"\n')
    assert preflight_provider_scopes(tmp_path) == (PREFLIGHT_SCOPE,)
    (code / "pyproject.toml").write_text(
        '[project]\nname="owned-code"\nversion="1"\ndependencies=["owned-peer>=1"]\n'
        '[tool.uv.sources]\nowned-peer={path="../../working/private"}\n'
    )
    with pytest.raises(ValueError, match="outside canonical"):
        preflight_provider_scopes(tmp_path)
