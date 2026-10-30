"""Real manuscript hydration subprocesses, runtime admission and original outcomes."""

from __future__ import annotations

import json
import os
import venv
from pathlib import Path

import pytest

from infrastructure.rendering.pipeline import run_manuscript_variable_script


@pytest.mark.skipif(os.name == "nt", reason="POSIX symlink semantics")
@pytest.mark.timeout(120)
def test_run_manuscript_variable_script_uses_project_venv_python(tmp_path: Path) -> None:
    template_root = tmp_path / "template"
    project = template_root / "projects" / "project"
    script = project / "scripts" / "z_generate_manuscript_variables.py"
    script.parent.mkdir(parents=True)
    script.write_text(
        "\n".join(
            [
                "import os",
                "import sys",
                "from pathlib import Path",
                'Path("output").mkdir(exist_ok=True)',
                'Path("output/hydration_result.txt").write_text(',
                '    sys.executable + "\\n" + os.environ.get("TEMPLATE_REPO_ROOT", ""),',
                '    encoding="utf-8",',
                ")",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    venv_python = project / ".venv" / "bin" / "python"
    # Build a real virtual environment. A bare symlink to the host interpreter
    # is not a virtual environment and, on Python 3.14, correctly reports the
    # resolved host binary as ``sys.executable`` even when invoked via that
    # symlink. The production contract is specifically the project venv.
    # Keep relocatable macOS interpreters beside their shared libpython rather
    # than copying only the executable away from its @rpath library.
    venv.EnvBuilder(with_pip=False, symlinks=True).create(project / ".venv")
    result = run_manuscript_variable_script(project, template_repo_root=template_root)

    assert result == 0
    executable, injected_template_root = (
        (project / "output" / "hydration_result.txt").read_text(encoding="utf-8").splitlines()
    )
    assert executable == str(venv_python)
    assert injected_template_root == str(template_root)
    receipt = json.loads(next((project / "output" / ".pipeline" / "analysis").glob("*/*.json")).read_text())
    assert receipt["worker"]["request"]["cwd"] == str(project)
    assert receipt["worker"]["completion"]["actual_runtime"]["prefix"] == str(project / ".venv")
    assert receipt["outcome"]["child_exit_code"] == 0


@pytest.mark.parametrize("actual_exit", [1, 7, 42, 75, 124, 130])
@pytest.mark.timeout(120)
def test_hydration_retains_typed_actual_child_outcomes(tmp_path: Path, actual_exit: int) -> None:
    root = tmp_path / "template"
    project = root / "projects" / "project"
    script = project / "scripts" / "z_generate_manuscript_variables.py"
    script.parent.mkdir(parents=True)
    script.write_text(f"raise SystemExit({actual_exit})\n")
    venv.EnvBuilder(with_pip=False, symlinks=True).create(project / ".venv")
    code = run_manuscript_variable_script(project, template_repo_root=root)
    assert code == (actual_exit if actual_exit in (75, 124, 130) else 1)
    receipt = json.loads(next((project / "output" / ".pipeline" / "analysis").glob("*/*.json")).read_text())
    assert receipt["outcome"]["child_exit_code"] == actual_exit
    assert receipt["complete"] is False


@pytest.mark.parametrize("nomination", ["missing", "broken-link"])
def test_hydration_refuses_broken_nominated_runtime_without_fallback(tmp_path: Path, nomination: str) -> None:
    project = tmp_path / "project"
    script = project / "scripts" / "z_generate_manuscript_variables.py"
    script.parent.mkdir(parents=True)
    script.write_text("from pathlib import Path\nPath('hydration_started').touch()\n")
    (project / ".venv" / "bin").mkdir(parents=True)
    if nomination == "broken-link":
        (project / ".venv" / "bin" / "python").symlink_to(tmp_path / "gone")
    assert run_manuscript_variable_script(project) == 75
    assert not (project / "hydration_started").exists()
    assert not (project / "output").exists()


@pytest.mark.parametrize("timeout", ["0", "-1", "nan", "inf", "invalid"])
def test_invalid_hydration_timeout_refuses_before_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, timeout: str
) -> None:
    script = tmp_path / "scripts" / "z_generate_manuscript_variables.py"
    script.parent.mkdir()
    script.write_text("from pathlib import Path\nPath('hydration_started').touch()\n")
    monkeypatch.setenv("MANUSCRIPT_HYDRATION_TIMEOUT", timeout)
    assert run_manuscript_variable_script(tmp_path) == 2
    assert not (tmp_path / "hydration_started").exists()
    assert not (tmp_path / "output").exists()


def test_hydration_rejects_malformed_actual_source(tmp_path: Path) -> None:
    root = tmp_path / "template"
    project = root / "projects/project"
    script = project / "scripts/z_generate_manuscript_variables.py"
    script.parent.mkdir(parents=True)
    script.write_text("def broken(:\n", encoding="utf-8")
    venv.EnvBuilder(with_pip=False, symlinks=True).create(project / ".venv")

    assert run_manuscript_variable_script(project, template_repo_root=root) == 1
    receipt = json.loads(next((project / "output/.pipeline/analysis").glob("*/*.json")).read_text())
    assert receipt["outcome"]["child_exit_code"] == 1
    assert receipt["complete"] is False


def test_absent_hydration_script_requires_no_producer(tmp_path: Path) -> None:
    assert run_manuscript_variable_script(tmp_path) == 0
    assert not (tmp_path / "output").exists()
