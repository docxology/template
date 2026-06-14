"""Tests for infrastructure.core.runtime._python_env."""

import os
import sys

import pytest

from infrastructure.core.runtime._python_env import (
    build_analysis_script_cmd_and_env,
    check_python_version,
    check_uv_available,
    get_python_command,
    get_subprocess_env,
    resolve_test_python,
    validate_interpreter,
)


class TestCheckPythonVersion:
    def test_returns_true(self):
        # We are running Python 3.10+, so this should pass
        assert check_python_version() is True


class TestCheckUvAvailable:
    def test_returns_bool(self):
        result = check_uv_available()
        assert isinstance(result, bool)
        # In this env, uv should be available
        assert result is True


class TestGetPythonCommand:
    def test_returns_list_with_executable(self):
        cmd = get_python_command()
        assert isinstance(cmd, list)
        assert len(cmd) == 1
        assert cmd[0] == sys.executable


class TestValidateInterpreter:
    def test_returns_bool(self):
        result = validate_interpreter()
        assert isinstance(result, bool)
        # Should generally return True in test environments


class TestGetSubprocessEnv:
    def test_returns_dict(self):
        env = get_subprocess_env()
        assert isinstance(env, dict)
        # Should at least have PATH
        assert "PATH" in env

    def test_with_custom_base_env(self):
        base = {"MY_VAR": "hello", "PATH": "/usr/bin"}
        env = get_subprocess_env(base_env=base)
        assert "MY_VAR" in env
        assert env["MY_VAR"] == "hello"


class TestBuildAnalysisScriptCmdAndEnv:
    def test_basic(self, tmp_path):
        script = tmp_path / "analysis.py"
        script.write_text("print('hello')")
        project_root = tmp_path / "project"
        project_root.mkdir()
        repo_root = tmp_path

        cmd, env = build_analysis_script_cmd_and_env(script, project_root, repo_root)
        assert isinstance(cmd, list)
        assert str(script) in cmd
        assert isinstance(env, dict)
        assert "PYTHONPATH" in env
        assert "MPLBACKEND" in env
        assert env["MPLBACKEND"] == "Agg"
        assert env["PROJECT_DIR"] == str(project_root)

    def test_with_project_venv(self, tmp_path):
        script = tmp_path / "analysis.py"
        script.write_text("print('hello')")
        project_root = tmp_path / "project"
        project_root.mkdir()
        # Create a .venv directory in the project
        (project_root / ".venv").mkdir()
        repo_root = tmp_path

        cmd, env = build_analysis_script_cmd_and_env(script, project_root, repo_root)
        # If uv is available, should use uv run
        if check_uv_available():
            assert "uv" in cmd[0] or "run" in cmd
        assert "PYTHONPATH" in env

    def test_pythonpath_includes_project_src(self, tmp_path):
        script = tmp_path / "script.py"
        script.write_text("")
        project_root = tmp_path / "project"
        project_root.mkdir()
        repo_root = tmp_path

        cmd, env = build_analysis_script_cmd_and_env(script, project_root, repo_root)
        paths = env["PYTHONPATH"].split(os.pathsep)
        assert str(project_root / "src") in paths
        assert str(repo_root) in paths

    def test_pythonpath_includes_project_root_for_src_package_imports(self, tmp_path):
        """Project root must be on PYTHONPATH so ``from src.<pkg> import ...``

        resolves ``src`` as a package. Regression: analysis scripts that do not
        self-bootstrap sys.path failed with ``No module named 'src'`` because
        only ``project_root/src`` (not ``project_root``) was on the path.
        """
        script = tmp_path / "script.py"
        script.write_text("")
        project_root = tmp_path / "project"
        project_root.mkdir()
        repo_root = tmp_path

        _, env = build_analysis_script_cmd_and_env(script, project_root, repo_root)
        paths = env["PYTHONPATH"].split(os.pathsep)
        assert str(project_root) in paths
        # Root must precede project_root/src so ``src`` resolves as a package.
        assert paths.index(str(project_root)) < paths.index(str(project_root / "src"))


@pytest.mark.skipif(os.name == "nt", reason="POSIX symlink semantics")
class TestResolveTestPython:
    """Regression coverage for the broken-venv-symlink crash.

    A ``.venv/`` directory can survive with a dangling ``bin/python`` symlink
    (base interpreter moved/removed). The previous logic keyed off
    ``.venv``-is-a-directory and handed subprocess a dead path, crashing the
    test stage with ``FileNotFoundError: .../.venv/bin/python``. These tests
    use real directories and real symlinks (no mocks) to lock the fallback.
    """

    def test_missing_venv_dir_falls_back(self, tmp_path):
        cmd = resolve_test_python(tmp_path / ".venv")
        assert cmd == get_python_command()

    def test_venv_without_interpreter_falls_back(self, tmp_path):
        (tmp_path / ".venv" / "bin").mkdir(parents=True)
        cmd = resolve_test_python(tmp_path / ".venv")
        assert cmd == get_python_command()

    def test_broken_symlink_falls_back(self, tmp_path):
        """The exact production failure: bin/python -> removed interpreter."""
        venv = tmp_path / ".venv"
        (venv / "bin").mkdir(parents=True)
        (venv / "bin" / "python").symlink_to(tmp_path / "does_not_exist" / "python3")
        assert venv.is_dir()  # the old guard would pass here…
        cmd = resolve_test_python(venv)
        assert cmd == get_python_command()  # …but we now fall back cleanly

    def test_valid_interpreter_is_used(self, tmp_path):
        venv = tmp_path / ".venv"
        (venv / "bin").mkdir(parents=True)
        link = venv / "bin" / "python"
        link.symlink_to(sys.executable)
        cmd = resolve_test_python(venv)
        assert cmd == [str(link)]

    def test_broken_venv_fallback_is_loud(self, tmp_path, caplog):
        """A broken (present-but-dead) venv must warn, not fall back silently."""
        venv = tmp_path / ".venv"
        (venv / "bin").mkdir(parents=True)
        (venv / "bin" / "python").symlink_to(tmp_path / "gone" / "python3")
        with caplog.at_level("WARNING"):
            resolve_test_python(venv)
        assert any("no usable interpreter" in r.message for r in caplog.records)

    def test_absent_venv_fallback_is_quiet(self, tmp_path, caplog):
        """A genuinely absent venv is the normal venv-less path — no warning."""
        with caplog.at_level("WARNING"):
            resolve_test_python(tmp_path / ".venv")
        assert not any("no usable interpreter" in r.message for r in caplog.records)
