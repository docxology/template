"""Canonical PyPI model/public-interface controls; retired helpers have no aliases."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from infrastructure.publishing.pypi.models import PyPIConfig, PyPIResult
from infrastructure.publishing.pypi_release import Deadline, _display_command, _twine_token_env, run_command


def test_pypi_config_defaults() -> None:
    cfg = PyPIConfig()
    assert cfg.test is False and cfg.token is None
    assert cfg.upload_repository == "pypi"
    assert cfg.index_url == "https://pypi.org/simple/"
    assert cfg.repository_url == "https://upload.pypi.org/legacy/"
    assert cfg.timeout == 120.0


def test_pypi_config_test_mode() -> None:
    cfg = PyPIConfig(test=True, token="invented-test-token")
    assert cfg.upload_repository == "testpypi"
    assert cfg.index_url == "https://test.pypi.org/simple/"
    assert cfg.token == "invented-test-token"


@pytest.mark.parametrize(
    "state,ok",
    [
        ("ok", True),
        ("dry-run", True),
        ("fail", False),
        ("blocked", False),
        ("timed_out", False),
        ("interrupted", False),
        ("error", False),
    ],
)
def test_pypi_result_describes_operation_outcome(state: str, ok: bool) -> None:
    receipt = {"assurance": "local operation only", "program_acceptance": "not established"}
    result = PyPIResult(state, "research-project-template", "4.0.0", receipt=receipt)
    assert result.ok is ok
    assert result.package_name == "research-project-template" and result.version == "4.0.0"
    assert result.receipt == receipt


def test_testpypi_release_helpers_keep_token_out_of_displayed_command() -> None:
    token = "invented-pypi-sensitive-token"
    env = _twine_token_env(token)
    displayed = _display_command(["python", "-m", "twine", "upload", token], (token,))
    assert env["TWINE_USERNAME"] == "__token__" and env["TWINE_PASSWORD"] == token
    assert token not in displayed and "<redacted>" in displayed


@pytest.mark.timeout(45)
@pytest.mark.parametrize(
    "first", ["infrastructure.project.installed_acceptance_artifacts", "infrastructure.publishing.pypi"]
)
def test_cold_real_imports_do_not_cycle_and_retired_routes_are_absent(tmp_path: Path, first: str) -> None:
    root = Path(__file__).resolve().parents[3]
    code = (
        "import importlib,sys; sys.path.insert(0,sys.argv[1]); "
        f"first=importlib.import_module({first!r}); "
        "artifacts=importlib.import_module('infrastructure.project.installed_acceptance_artifacts'); "
        "publishing=importlib.import_module('infrastructure.publishing'); "
        "pypi=importlib.import_module('infrastructure.publishing.pypi'); "
        "assert artifacts.AdmittedWheel.__name__=='AdmittedWheel'; "
        "assert pypi.PyPIAdapter.name=='pypi'; "
        "assert all(not hasattr(module,name) for module in (publishing,pypi) "
        "for name in ('build_dist','upload_dist','check_dist','verify_install')); "
        "assert all(importlib.util.find_spec(name) is None for name in "
        "('infrastructure.publishing.pypi.build','infrastructure.publishing.pypi.upload','infrastructure.publishing.pypi.verify'))"
    )
    result = run_command((sys.executable, "-I", "-c", code, str(root)), tmp_path, deadline=Deadline.start(30))
    assert result.returncode == 0
