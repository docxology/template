"""Tests for infrastructure.core.runtime._python_env."""

import os
import sys

from infrastructure.core.runtime._python_env import (
    build_analysis_script_cmd_and_env,
    check_python_version,
    check_uv_available,
    get_python_command,
    get_subprocess_env,
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
