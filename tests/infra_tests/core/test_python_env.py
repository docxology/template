"""Tests for infrastructure.core.runtime._python_env."""

import os
import sys
import venv
from pathlib import Path

import pytest

from infrastructure.core.runtime._python_env import (
    build_analysis_script_cmd_and_env,
    _python_version_supported,
    check_python_version,
    check_uv_available,
    get_python_command,
    get_subprocess_env,
    validate_analysis_script_path,
    validate_interpreter,
)
from infrastructure.core.runtime.python_binding import AnalysisRuntimeUnavailable, select_analysis_python


@pytest.fixture(autouse=True)
def _candidate_epoch(monkeypatch):
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")


class TestCheckPythonVersion:
    def test_returns_true(self):
        # The supported project runtime is Python 3.14+.
        assert check_python_version() is True

    @pytest.mark.parametrize(
        "version,expected",
        [
            ((3, 9), False),
            ((3, 10), False),
            ((3, 11), False),
            ((3, 12), False),
            ((3, 13), False),
            ((3, 14), True),
            ((3, 15), True),
            ((4, 0), True),
        ],
    )
    def test_runtime_floor_rejects_older_versions(self, version, expected):
        assert _python_version_supported(version) is expected


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
        project_root = tmp_path / "project"
        script = project_root / "scripts" / "analysis.py"
        script.parent.mkdir(parents=True)
        script.write_text("print('hello')")
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
        project_root = tmp_path / "project"
        script = project_root / "scripts" / "analysis.py"
        script.parent.mkdir(parents=True)
        script.write_text("print('hello')")
        venv.EnvBuilder(with_pip=False, symlinks=True).create(project_root / ".venv")
        repo_root = tmp_path

        cmd, env = build_analysis_script_cmd_and_env(script, project_root, repo_root)
        assert cmd == [str(project_root / ".venv/bin/python"), str(script)]
        assert "PYTHONPATH" in env

    def test_missing_nominated_project_runtime_refuses_without_resolver(self, tmp_path):
        project_root = tmp_path / "project"
        script = project_root / "scripts/analysis.py"
        script.parent.mkdir(parents=True)
        script.write_text("raise SystemExit(99)")
        (project_root / ".venv").mkdir()
        with pytest.raises(AnalysisRuntimeUnavailable):
            build_analysis_script_cmd_and_env(script, project_root, tmp_path)

    def test_pythonpath_includes_project_src(self, tmp_path):
        project_root = tmp_path / "project"
        script = project_root / "scripts" / "script.py"
        script.parent.mkdir(parents=True)
        script.write_text("")
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
        project_root = tmp_path / "project"
        script = project_root / "scripts" / "script.py"
        script.parent.mkdir(parents=True)
        script.write_text("")
        repo_root = tmp_path

        _, env = build_analysis_script_cmd_and_env(script, project_root, repo_root)
        paths = env["PYTHONPATH"].split(os.pathsep)
        assert str(project_root) in paths
        # Root must precede project_root/src so ``src`` resolves as a package.
        assert paths.index(str(project_root)) < paths.index(str(project_root / "src"))

    def test_rejects_script_outside_project_boundary(self, tmp_path):
        project_root = tmp_path / "project"
        (project_root / "scripts").mkdir(parents=True)
        outside = tmp_path / "outside.py"
        outside.write_text("")

        with pytest.raises(ValueError, match="under"):
            validate_analysis_script_path(outside, project_root)

    def test_redacts_credentials_by_default_and_allows_explicit_opt_in(self, tmp_path, monkeypatch):
        project_root = tmp_path / "project"
        script = project_root / "scripts" / "script.py"
        script.parent.mkdir(parents=True)
        script.write_text("")
        monkeypatch.setenv("PAPERCLIP_API_KEY", "secret")

        _, redacted = build_analysis_script_cmd_and_env(script, project_root, tmp_path, allow_secret_env=False)
        assert "PAPERCLIP_API_KEY" not in redacted

        _, opted_in = build_analysis_script_cmd_and_env(script, project_root, tmp_path, allow_secret_env=True)
        assert opted_in["PAPERCLIP_API_KEY"] == "secret"

    def test_admitted_base_policy_is_copied_and_ambient_state_does_not_replace_it(self, tmp_path, monkeypatch):
        project_root = tmp_path / "project"
        script = project_root / "scripts/script.py"
        script.parent.mkdir(parents=True)
        script.write_text("pass\n")
        baseline = {
            "SOURCE_DATE_EPOCH": "1700000001",
            "TEMPLATE_EXECUTION_MODE": "live",
            "TEMPLATE_PROJECT_OPTION": "original",
            "PAPERCLIP_API_KEY": "private-test-value",
        }
        original = dict(baseline)
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000002")
        monkeypatch.setenv("TEMPLATE_EXECUTION_MODE", "core")
        monkeypatch.setenv("TEMPLATE_PROJECT_OPTION", "changed")
        _, env = build_analysis_script_cmd_and_env(script, project_root, tmp_path, base_env=baseline)
        assert env["SOURCE_DATE_EPOCH"] == "1700000001" and env["TEMPLATE_EXECUTION_MODE"] == "live"
        assert env["TEMPLATE_PROJECT_OPTION"] == "original" and "PAPERCLIP_API_KEY" not in env
        assert baseline == original


@pytest.mark.skipif(os.name == "nt", reason="POSIX symlink semantics")
class TestSelectAnalysisPython:
    """Existing lexical runtimes are explicit; missing nominations never fall back."""

    def test_absent_venv_selects_current_interpreter(self, tmp_path):
        assert select_analysis_python(tmp_path) == Path(sys.executable).absolute()

    def test_nominated_venv_without_interpreter_is_refused(self, tmp_path):
        (tmp_path / ".venv" / "bin").mkdir(parents=True)
        with pytest.raises(AnalysisRuntimeUnavailable, match="no usable Python interpreter"):
            select_analysis_python(tmp_path)

    def test_broken_nominated_symlink_is_refused(self, tmp_path):
        environment = tmp_path / ".venv"
        (environment / "bin").mkdir(parents=True)
        (environment / "bin" / "python").symlink_to(tmp_path / "gone" / "python3")
        with pytest.raises(AnalysisRuntimeUnavailable, match="no usable Python interpreter"):
            select_analysis_python(tmp_path)

    def test_valid_lexical_nomination_is_used(self, tmp_path):
        environment = tmp_path / ".venv"
        (environment / "bin").mkdir(parents=True)
        binary = environment / "bin" / "python"
        binary.symlink_to(sys.executable)
        assert select_analysis_python(tmp_path) == binary
