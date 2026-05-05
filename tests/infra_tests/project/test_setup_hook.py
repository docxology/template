"""Tests for ``infrastructure.project.setup_hook``.

Real-subprocess, real-file tests — strict No-Mocks policy.

Each test builds a minimal ``projects/<name>/scripts/`` layout under
``tmp_path`` and exercises the public API:

* :func:`infrastructure.project.setup_hook.find_setup_hook`
* :func:`infrastructure.project.setup_hook.preflight_setup_hook`
* :func:`infrastructure.project.setup_hook.run_project_setup_hook`

Hook scripts write a sentinel file so we can verify (a) the hook actually ran
or (b) — for dry-run mode — the hook did **not** run.
"""

from __future__ import annotations

import platform
import stat
import sys
from pathlib import Path

import pytest

from infrastructure.project.setup_hook import (
    DEFAULT_TIMEOUT_SEC,
    find_setup_hook,
    preflight_setup_hook,
    run_project_setup_hook,
)

# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #


def _make_project(tmp_path: Path) -> Path:
    """Create a minimal valid project skeleton under ``tmp_path``."""
    project_dir = tmp_path / "demo"
    (project_dir / "src").mkdir(parents=True)
    (project_dir / "src" / "__init__.py").write_text("")
    (project_dir / "tests").mkdir()
    (project_dir / "scripts").mkdir()
    return project_dir


def _write_py_hook(project_dir: Path, *, sentinel: Path, exit_code: int = 0) -> Path:
    """Write a Python setup_hook that touches ``sentinel`` then exits.

    Args:
        project_dir: Project root.
        sentinel: File the hook should create as a side effect.
        exit_code: Process exit code the hook should return.
    """
    hook = project_dir / "scripts" / "setup_hook.py"
    hook.write_text(
        "#!/usr/bin/env python3\n"
        "import pathlib, sys\n"
        f"pathlib.Path(r'{sentinel}').write_text('ran')\n"
        f"sys.exit({exit_code})\n"
    )
    hook.chmod(hook.stat().st_mode | stat.S_IXUSR)
    return hook


def _write_sh_hook(project_dir: Path, *, sentinel: Path, exit_code: int = 0) -> Path:
    """Write a POSIX shell setup_hook that touches ``sentinel`` then exits."""
    hook = project_dir / "scripts" / "setup_hook.sh"
    hook.write_text(f"#!/usr/bin/env bash\necho 'ran' > '{sentinel}'\nexit {exit_code}\n")
    hook.chmod(hook.stat().st_mode | stat.S_IXUSR)
    return hook


def _write_manifest(project_dir: Path, contents: str) -> Path:
    """Write ``setup_hook.yaml`` alongside the hook."""
    manifest = project_dir / "scripts" / "setup_hook.yaml"
    manifest.write_text(contents)
    return manifest


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Strip env vars this module reads so tests don't leak into one another."""
    for var in (
        "PROJECT_SETUP_HOOK_TIMEOUT_SEC",
        "PROJECT_SETUP_HOOK_DRY_RUN",
        "CI_NO_HOOKS",
        "HF_TOKEN",
        "DEMO_REQUIRED_VAR",
    ):
        monkeypatch.delenv(var, raising=False)


# --------------------------------------------------------------------------- #
# find_setup_hook                                                             #
# --------------------------------------------------------------------------- #


class TestFindSetupHook:
    def test_returns_none_when_no_hook(self, tmp_path: Path) -> None:
        project_dir = _make_project(tmp_path)
        assert find_setup_hook(project_dir) is None

    def test_returns_py_hook_when_present(self, tmp_path: Path) -> None:
        project_dir = _make_project(tmp_path)
        sentinel = tmp_path / "marker"
        hook = _write_py_hook(project_dir, sentinel=sentinel)
        found = find_setup_hook(project_dir)
        assert found == hook

    def test_prefers_py_over_sh(self, tmp_path: Path) -> None:
        project_dir = _make_project(tmp_path)
        sentinel = tmp_path / "marker"
        py_hook = _write_py_hook(project_dir, sentinel=sentinel)
        _write_sh_hook(project_dir, sentinel=sentinel)
        assert find_setup_hook(project_dir) == py_hook

    @pytest.mark.skipif(platform.system() == "Windows", reason="POSIX-only fallback")
    def test_returns_sh_hook_on_posix(self, tmp_path: Path) -> None:
        project_dir = _make_project(tmp_path)
        sentinel = tmp_path / "marker"
        sh_hook = _write_sh_hook(project_dir, sentinel=sentinel)
        assert find_setup_hook(project_dir) == sh_hook

    def test_returns_none_when_scripts_missing(self, tmp_path: Path) -> None:
        # No ``scripts/`` directory at all.
        project_dir = tmp_path / "no_scripts"
        project_dir.mkdir()
        assert find_setup_hook(project_dir) is None


# --------------------------------------------------------------------------- #
# preflight_setup_hook                                                        #
# --------------------------------------------------------------------------- #


class TestPreflight:
    def test_no_hook_returns_ok(self, tmp_path: Path) -> None:
        project_dir = _make_project(tmp_path)
        ok, errors = preflight_setup_hook(project_dir)
        assert ok is True
        assert errors == []

    def test_no_manifest_returns_ok(self, tmp_path: Path) -> None:
        project_dir = _make_project(tmp_path)
        _write_py_hook(project_dir, sentinel=tmp_path / "marker")
        ok, errors = preflight_setup_hook(project_dir)
        assert ok is True
        assert errors == []

    def test_missing_required_tool_reports_error(self, tmp_path: Path) -> None:
        project_dir = _make_project(tmp_path)
        _write_py_hook(project_dir, sentinel=tmp_path / "marker")
        _write_manifest(
            project_dir,
            "required_tools: ['definitely_not_a_real_binary_xyz123']\n",
        )
        ok, errors = preflight_setup_hook(project_dir)
        assert ok is False
        assert any("definitely_not_a_real_binary_xyz123" in e for e in errors)
        assert any("not on PATH" in e for e in errors)

    def test_missing_required_env_reports_error(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        project_dir = _make_project(tmp_path)
        _write_py_hook(project_dir, sentinel=tmp_path / "marker")
        _write_manifest(project_dir, "required_env: ['DEMO_REQUIRED_VAR']\n")
        monkeypatch.delenv("DEMO_REQUIRED_VAR", raising=False)
        ok, errors = preflight_setup_hook(project_dir)
        assert ok is False
        assert any("DEMO_REQUIRED_VAR" in e for e in errors)

    def test_satisfied_required_env_passes(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        project_dir = _make_project(tmp_path)
        _write_py_hook(project_dir, sentinel=tmp_path / "marker")
        _write_manifest(project_dir, "required_env: ['DEMO_REQUIRED_VAR']\n")
        monkeypatch.setenv("DEMO_REQUIRED_VAR", "set")
        ok, errors = preflight_setup_hook(project_dir)
        assert ok is True
        assert errors == []

    def test_skip_if_env_short_circuits(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        project_dir = _make_project(tmp_path)
        _write_py_hook(project_dir, sentinel=tmp_path / "marker")
        # Even when required tools are missing, skip_if_env wins.
        _write_manifest(
            project_dir,
            "skip_if_env: ['CI_NO_HOOKS']\nrequired_tools: ['definitely_not_a_real_binary_xyz123']\n",
        )
        monkeypatch.setenv("CI_NO_HOOKS", "1")
        ok, errors = preflight_setup_hook(project_dir)
        assert ok is True
        assert errors == ["skipped: CI_NO_HOOKS"]

    def test_skip_if_env_falsy_does_not_skip(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        project_dir = _make_project(tmp_path)
        _write_py_hook(project_dir, sentinel=tmp_path / "marker")
        _write_manifest(project_dir, "skip_if_env: ['CI_NO_HOOKS']\n")
        monkeypatch.setenv("CI_NO_HOOKS", "0")
        ok, errors = preflight_setup_hook(project_dir)
        assert ok is True
        assert errors == []

    def test_satisfied_tool_passes(self, tmp_path: Path) -> None:
        project_dir = _make_project(tmp_path)
        _write_py_hook(project_dir, sentinel=tmp_path / "marker")
        # ``python`` is guaranteed to be on PATH in CI; sys.executable resolves it.
        py_basename = Path(sys.executable).name
        _write_manifest(project_dir, f"required_tools: ['{py_basename}']\n")
        ok, errors = preflight_setup_hook(project_dir)
        assert ok is True, errors

    def test_malformed_yaml_treated_as_no_manifest(self, tmp_path: Path) -> None:
        project_dir = _make_project(tmp_path)
        _write_py_hook(project_dir, sentinel=tmp_path / "marker")
        _write_manifest(project_dir, "this: is: not: valid: yaml: ::\n")
        ok, errors = preflight_setup_hook(project_dir)
        # Malformed manifest must not break setup — treated as empty.
        assert ok is True
        assert errors == []


# --------------------------------------------------------------------------- #
# run_project_setup_hook                                                      #
# --------------------------------------------------------------------------- #


class TestRunHook:
    def test_no_hook_is_noop_returns_true(self, tmp_path: Path) -> None:
        project_dir = _make_project(tmp_path)
        assert run_project_setup_hook(project_dir) is True

    def test_runs_py_hook_and_creates_side_effect(self, tmp_path: Path) -> None:
        project_dir = _make_project(tmp_path)
        sentinel = tmp_path / "ran.txt"
        _write_py_hook(project_dir, sentinel=sentinel)
        assert run_project_setup_hook(project_dir) is True
        assert sentinel.is_file()

    def test_hook_failure_returns_false(self, tmp_path: Path) -> None:
        project_dir = _make_project(tmp_path)
        sentinel = tmp_path / "ran.txt"
        _write_py_hook(project_dir, sentinel=sentinel, exit_code=7)
        assert run_project_setup_hook(project_dir) is False
        assert sentinel.is_file()  # the sentinel write happens before sys.exit

    def test_preflight_failure_skips_invocation(self, tmp_path: Path) -> None:
        """A missing required_tools entry must surface as an error and the
        hook must NOT execute (no side-effect file)."""
        project_dir = _make_project(tmp_path)
        sentinel = tmp_path / "should_not_exist.txt"
        _write_py_hook(project_dir, sentinel=sentinel)
        _write_manifest(
            project_dir,
            "required_tools: ['definitely_not_a_real_binary_xyz123']\n",
        )
        assert run_project_setup_hook(project_dir) is False
        assert not sentinel.exists()

    def test_dry_run_does_not_invoke_hook(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """``PROJECT_SETUP_HOOK_DRY_RUN=1`` must short-circuit subprocess
        execution. The hook would write ``sentinel`` but it must not exist
        afterwards."""
        project_dir = _make_project(tmp_path)
        sentinel = tmp_path / "should_not_exist_dry.txt"
        _write_py_hook(project_dir, sentinel=sentinel)
        monkeypatch.setenv("PROJECT_SETUP_HOOK_DRY_RUN", "1")
        assert run_project_setup_hook(project_dir) is True
        assert not sentinel.exists()

    def test_dry_run_with_failing_preflight_still_returns_false(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Dry-run does not bypass preflight — a missing tool is still surfaced."""
        project_dir = _make_project(tmp_path)
        sentinel = tmp_path / "should_not_exist.txt"
        _write_py_hook(project_dir, sentinel=sentinel)
        _write_manifest(
            project_dir,
            "required_tools: ['definitely_not_a_real_binary_xyz123']\n",
        )
        monkeypatch.setenv("PROJECT_SETUP_HOOK_DRY_RUN", "1")
        assert run_project_setup_hook(project_dir) is False
        assert not sentinel.exists()

    def test_skip_if_env_short_circuits_run(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        project_dir = _make_project(tmp_path)
        sentinel = tmp_path / "should_not_run.txt"
        _write_py_hook(project_dir, sentinel=sentinel)
        _write_manifest(project_dir, "skip_if_env: ['CI_NO_HOOKS']\n")
        monkeypatch.setenv("CI_NO_HOOKS", "true")
        assert run_project_setup_hook(project_dir) is True
        assert not sentinel.exists()

    def test_manifest_timeout_override_accepted(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Manifest ``timeout_sec`` must override env-var and default.

        We verify this *behaviourally* with dry-run: dry-run logs the
        resolved timeout. Direct assertion uses the internal helper because
        we're testing real behaviour rather than mocking subprocess.run.
        """
        project_dir = _make_project(tmp_path)
        sentinel = tmp_path / "ran.txt"
        hook = _write_py_hook(project_dir, sentinel=sentinel)
        _write_manifest(project_dir, "timeout_sec: 1234\n")
        monkeypatch.setenv("PROJECT_SETUP_HOOK_TIMEOUT_SEC", "9999")

        from infrastructure.project.setup_hook import _resolved_timeout  # noqa: PLC0415

        assert _resolved_timeout(hook) == 1234

    def test_env_timeout_used_when_no_manifest(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        project_dir = _make_project(tmp_path)
        hook = _write_py_hook(project_dir, sentinel=tmp_path / "ran.txt")
        monkeypatch.setenv("PROJECT_SETUP_HOOK_TIMEOUT_SEC", "42")

        from infrastructure.project.setup_hook import _resolved_timeout  # noqa: PLC0415

        assert _resolved_timeout(hook) == 42

    def test_default_timeout_when_unset(self, tmp_path: Path) -> None:
        project_dir = _make_project(tmp_path)
        hook = _write_py_hook(project_dir, sentinel=tmp_path / "ran.txt")

        from infrastructure.project.setup_hook import _resolved_timeout  # noqa: PLC0415

        assert _resolved_timeout(hook) == DEFAULT_TIMEOUT_SEC

    def test_env_timeout_invalid_falls_back_to_default(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        project_dir = _make_project(tmp_path)
        hook = _write_py_hook(project_dir, sentinel=tmp_path / "ran.txt")
        monkeypatch.setenv("PROJECT_SETUP_HOOK_TIMEOUT_SEC", "not-an-int")

        from infrastructure.project.setup_hook import _resolved_timeout  # noqa: PLC0415

        assert _resolved_timeout(hook) == DEFAULT_TIMEOUT_SEC

    @pytest.mark.skipif(platform.system() == "Windows", reason="POSIX-only fallback")
    def test_runs_sh_hook_on_posix(self, tmp_path: Path) -> None:
        project_dir = _make_project(tmp_path)
        sentinel = tmp_path / "ran.txt"
        _write_sh_hook(project_dir, sentinel=sentinel)
        assert run_project_setup_hook(project_dir) is True
        assert sentinel.is_file()

    def test_dry_run_with_skip_if_env_returns_true_and_skips(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """skip_if_env path must be honoured before dry-run logging."""
        project_dir = _make_project(tmp_path)
        sentinel = tmp_path / "should_not_exist.txt"
        _write_py_hook(project_dir, sentinel=sentinel)
        _write_manifest(project_dir, "skip_if_env: ['CI_NO_HOOKS']\n")
        monkeypatch.setenv("CI_NO_HOOKS", "yes")
        monkeypatch.setenv("PROJECT_SETUP_HOOK_DRY_RUN", "1")
        assert run_project_setup_hook(project_dir) is True
        assert not sentinel.exists()


# --------------------------------------------------------------------------- #
# Public API stability                                                        #
# --------------------------------------------------------------------------- #


def test_public_api_exports() -> None:
    """The public API is re-exported from ``infrastructure.project``."""
    from infrastructure.project import (  # noqa: PLC0415
        find_setup_hook as exported_find,
        preflight_setup_hook as exported_pre,
        run_project_setup_hook as exported_run,
    )

    assert exported_find is find_setup_hook
    assert exported_pre is preflight_setup_hook
    assert exported_run is run_project_setup_hook


def test_module_works_when_yaml_loads_returns_none(tmp_path: Path) -> None:
    """An empty manifest (``yaml.safe_load`` returns ``None``) is a no-op."""
    project_dir = _make_project(tmp_path)
    _write_py_hook(project_dir, sentinel=tmp_path / "ran.txt")
    _write_manifest(project_dir, "")  # empty file
    ok, errors = preflight_setup_hook(project_dir)
    assert ok is True
    assert errors == []
