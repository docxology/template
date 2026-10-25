"""Real selected environments bind provider roots before audited execution."""

from __future__ import annotations

import importlib.util
import os
import sys
import sysconfig
import venv
from pathlib import Path

import pytest

from infrastructure.core.execution_boundary import run_bounded_subprocess
from infrastructure.core.testing.project_test_runtime import (
    ProjectTestRuntimeError,
    build_audited_project_test_command,
    project_test_audit_roots,
    project_test_deadline,
)


def _selected_provider(project: Path) -> tuple[Path, Path, Path]:
    environment = project / ".venv"
    venv.EnvBuilder(with_pip=False, symlinks=os.name != "nt").create(environment)
    selected = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    site = environment / (
        "Lib/site-packages"
        if os.name == "nt"
        else f"lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages"
    )
    # Share the actual prepared dependency installation, without replacing code
    # or installing a package. The provider itself exists only in this venv.
    (site / "prepared_dependencies.pth").write_text(sysconfig.get_path("purelib") + "\n")
    provider = site / "template_selected_provider"
    provider.mkdir()
    marker = project / "provider-imported.txt"
    (provider / "__init__.py").write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('actual import')\nVALUE = 7\n"
    )
    (project / "pyproject.toml").write_text(
        '[project]\nname="selected-consumer"\nversion="1.0.0"\ndependencies=["template-selected-provider==1.0.0"]\n'
    )
    (project / "src").mkdir()
    (project / "scripts").mkdir()
    assert importlib.util.find_spec("template_selected_provider") is None
    return selected, provider, marker


@pytest.mark.timeout(120)
@pytest.mark.parametrize("corrupt,leaf_exit", [(False, 0), (True, 0), (True, 7)])
def test_real_selected_only_provider_is_audited(tmp_path: Path, corrupt: bool, leaf_exit: int) -> None:
    selected, provider, marker = _selected_provider(tmp_path)
    script = tmp_path / "scripts/verify.py"
    script.write_text(
        "import template_selected_provider as provider\nassert provider.VALUE == 7\n"
        + ("from pathlib import Path\nPath(provider.__file__).write_text('VALUE = 9\\n')\n" if corrupt else "")
        + f"raise SystemExit({leaf_exit})\n"
    )
    command = build_audited_project_test_command(tmp_path, selected, (), script=script)
    assert not marker.exists(), "Provider lookup must not execute its package"
    result = run_bounded_subprocess(command, cwd=tmp_path, env=os.environ.copy(), timeout=60)
    assert marker.read_text() == "actual import"
    expected = leaf_exit if leaf_exit else 75 if corrupt else 0
    assert result.returncode == expected, result.stderr
    if corrupt:
        assert "custody refused" in result.stderr
    else:
        assert str(provider) in command[4]


@pytest.mark.timeout(120)
def test_real_selected_provider_probe_expires_before_import(tmp_path: Path) -> None:
    selected, _provider, marker = _selected_provider(tmp_path)
    with pytest.raises(ProjectTestRuntimeError) as refused:
        project_test_audit_roots(tmp_path, interpreter=selected, deadline=project_test_deadline(0.000001))
    assert refused.value.exit_code == 124
    assert not marker.exists()


@pytest.mark.timeout(120)
def test_real_unavailable_selected_provider_probe_refuses_without_fallback(tmp_path: Path) -> None:
    _selected, _provider, marker = _selected_provider(tmp_path)
    with pytest.raises(ProjectTestRuntimeError) as refused:
        project_test_audit_roots(tmp_path, interpreter=tmp_path / "absent-python")
    assert refused.value.exit_code == 75
    assert not marker.exists()


@pytest.mark.timeout(120)
def test_real_selected_provider_uses_project_src_before_site_packages(tmp_path: Path) -> None:
    selected, installed, marker = _selected_provider(tmp_path)
    local = tmp_path / "src/template_selected_provider"
    local.mkdir()
    (local / "__init__.py").write_text("VALUE = 11\n")
    roots = project_test_audit_roots(tmp_path, interpreter=selected)
    assert local in roots
    assert installed not in roots
    assert not marker.exists()
    script = tmp_path / "scripts/verify.py"
    script.write_text("import template_selected_provider\nassert template_selected_provider.VALUE == 11\n")
    command = build_audited_project_test_command(tmp_path, selected, (), script=script)
    result = run_bounded_subprocess(command, cwd=tmp_path, env=os.environ.copy(), timeout=60)
    assert result.returncode == 0, result.stderr
    assert not marker.exists()


@pytest.mark.timeout(120)
def test_supplied_incomplete_roots_refused_before_provider_execution(tmp_path: Path) -> None:
    selected, provider, marker = _selected_provider(tmp_path)
    complete = project_test_audit_roots(tmp_path, interpreter=selected)
    script = tmp_path / "scripts/verify.py"
    script.write_text("import template_selected_provider\n")
    with pytest.raises(ProjectTestRuntimeError) as refused:
        build_audited_project_test_command(
            tmp_path, selected, (), script=script, audit_roots=tuple(root for root in complete if root != provider)
        )
    assert refused.value.exit_code == 75
    assert not marker.exists()


@pytest.mark.timeout(120)
@pytest.mark.parametrize("evidence", ["not-json", '{"executable":"incorrect","roots":["../relative"]}'])
def test_actual_malformed_selected_probe_evidence_is_refused(tmp_path: Path, evidence: str) -> None:
    if os.name == "nt":
        pytest.skip("POSIX executable-wrapper control")
    _selected, _provider, marker = _selected_provider(tmp_path)
    wrapper = tmp_path / "malformed-interpreter"
    wrapper.write_text(f"#!/bin/sh\nprintf '%s' '{evidence}'\n")
    wrapper.chmod(0o700)
    with pytest.raises(ProjectTestRuntimeError) as refused:
        project_test_audit_roots(tmp_path, interpreter=wrapper)
    assert refused.value.exit_code == 75
    assert "invalid evidence" in str(refused.value)
    assert not marker.exists()
