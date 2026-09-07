"""Tests for infrastructure.rendering.pipeline override/hydration script delegation.

Real subprocesses against temporary scripts — no mocking.
"""

from __future__ import annotations

import os
import venv
from pathlib import Path

import pytest

from infrastructure.rendering.pipeline import (
    _run_manuscript_variable_script,
    _run_override_script,
)


# ---------------------------------------------------------------------------
# _run_override_script  (real subprocess — no mocking)
# ---------------------------------------------------------------------------


def test_run_override_script_success(tmp_path: Path) -> None:
    """Returns 0 when a real override script exits successfully."""
    override = tmp_path / "scripts" / "_render_pdf_override.py"
    override.parent.mkdir(parents=True)
    override.write_text("import sys\nsys.exit(0)\n")

    result = _run_override_script(tmp_path, override)

    assert result == 0


def test_run_override_script_failure(tmp_path: Path) -> None:
    """Returns non-zero when a real override script exits with error."""
    override = tmp_path / "scripts" / "_render_pdf_override.py"
    override.parent.mkdir(parents=True)
    override.write_text("import sys\nsys.exit(1)\n")

    result = _run_override_script(tmp_path, override)

    assert result == 1


def test_run_override_script_non_zero_exit_code(tmp_path: Path) -> None:
    """Returns the specific non-zero exit code from the override script."""
    override = tmp_path / "scripts" / "_render_pdf_override.py"
    override.parent.mkdir(parents=True)
    override.write_text("import sys\nsys.exit(42)\n")

    result = _run_override_script(tmp_path, override)

    assert result == 42


def test_run_override_script_subprocess_error(tmp_path: Path) -> None:
    """Returns a non-zero code when the interpreter rejects malformed source."""
    override = tmp_path / "scripts" / "_render_pdf_override.py"
    override.parent.mkdir(parents=True)
    # A syntax error is portable across Python versions; arbitrary invalid
    # bytes were accepted as an empty script by one supported interpreter.
    override.write_text("def broken(:\n", encoding="utf-8")

    result = _run_override_script(tmp_path, override)

    # Malformed source run through Python must fail (exit non-zero or raise).
    assert result != 0


def test_run_override_script_missing_file(tmp_path: Path) -> None:
    """Returns non-zero when the override script path does not exist."""
    missing = tmp_path / "scripts" / "nonexistent.py"

    result = _run_override_script(tmp_path, missing)

    assert result != 0


@pytest.mark.skipif(os.name == "nt", reason="POSIX symlink semantics")
def test_run_manuscript_variable_script_uses_project_venv_python(tmp_path: Path) -> None:
    project = tmp_path / "project"
    script = project / "scripts" / "z_generate_manuscript_variables.py"
    script.parent.mkdir(parents=True)
    script.write_text(
        "\n".join(
            [
                "import os",
                "import sys",
                "from pathlib import Path",
                'Path("hydration_result.txt").write_text(',
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
    template_root = tmp_path / "template"
    template_root.mkdir()

    result = _run_manuscript_variable_script(project, template_repo_root=template_root)

    assert result == 0
    executable, injected_template_root = (project / "hydration_result.txt").read_text(encoding="utf-8").splitlines()
    assert executable == str(venv_python)
    assert injected_template_root == str(template_root)
