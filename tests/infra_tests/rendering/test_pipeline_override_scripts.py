"""Tests for infrastructure.rendering.pipeline override/hydration script delegation.

Real subprocesses against temporary scripts — no mocking.
"""

from __future__ import annotations

import hashlib
import os
import venv
from pathlib import Path

import pytest

from infrastructure.rendering.manuscript_composition import (
    COMBINED_RELATIVE_PATH,
    COMPOSITION_RELATIVE_PATH,
    read_manuscript_composition,
)
from infrastructure.rendering.pipeline import (
    _write_override_composition,
    execute_render_pipeline,
    run_manuscript_variable_script,
    run_override_script,
)
from ._pipeline_helpers import _dependencies_for, _write_minimal_project_tree


# ---------------------------------------------------------------------------
# run_override_script  (real subprocess — no mocking)
# ---------------------------------------------------------------------------


def test_run_override_script_success(tmp_path: Path) -> None:
    """Returns 0 when a real override script exits successfully."""
    override = tmp_path / "scripts" / "_render_pdf_override.py"
    override.parent.mkdir(parents=True)
    override.write_text("import sys\nsys.exit(0)\n")

    result = run_override_script(tmp_path, override)

    assert result == 0


def test_run_override_script_failure(tmp_path: Path) -> None:
    """Returns non-zero when a real override script exits with error."""
    override = tmp_path / "scripts" / "_render_pdf_override.py"
    override.parent.mkdir(parents=True)
    override.write_text("import sys\nsys.exit(1)\n")

    result = run_override_script(tmp_path, override)

    assert result == 1


def test_run_override_script_non_zero_exit_code(tmp_path: Path) -> None:
    """Returns the specific non-zero exit code from the override script."""
    override = tmp_path / "scripts" / "_render_pdf_override.py"
    override.parent.mkdir(parents=True)
    override.write_text("import sys\nsys.exit(42)\n")

    result = run_override_script(tmp_path, override)

    assert result == 42


def test_run_override_script_subprocess_error(tmp_path: Path) -> None:
    """Returns a non-zero code when the interpreter rejects malformed source."""
    override = tmp_path / "scripts" / "_render_pdf_override.py"
    override.parent.mkdir(parents=True)
    # A syntax error is portable across Python versions; arbitrary invalid
    # bytes were accepted as an empty script by one supported interpreter.
    override.write_text("def broken(:\n", encoding="utf-8")

    result = run_override_script(tmp_path, override)

    # Malformed source run through Python must fail (exit non-zero or raise).
    assert result != 0


def test_run_override_script_missing_file(tmp_path: Path) -> None:
    """Returns non-zero when the override script path does not exist."""
    missing = tmp_path / "scripts" / "nonexistent.py"

    result = run_override_script(tmp_path, missing)

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

    result = run_manuscript_variable_script(project, template_repo_root=template_root)

    assert result == 0
    executable, injected_template_root = (project / "hydration_result.txt").read_text(encoding="utf-8").splitlines()
    assert executable == str(venv_python)
    assert injected_template_root == str(template_root)


# ---------------------------------------------------------------------------
# _write_override_composition  (real files in tmp_path — no mocking)
# ---------------------------------------------------------------------------


def _override_project(
    tmp_path: Path,
    *,
    name: str = "proj",
    temp_text: str = "# Intro\n\nHello.\n\n# Next\n\nMore.\n",
) -> Path:
    """Build a temp project: populated manuscript source + override combined markdown."""
    project = tmp_path / name
    manuscript = project / "manuscript"
    manuscript.mkdir(parents=True)
    (manuscript / "01_intro.md").write_text("# Intro\n\nHello.\n", encoding="utf-8")
    (manuscript / "02_next.md").write_text("# Next\n\nMore.\n", encoding="utf-8")
    pdf_dir = project / "output" / "pdf"
    pdf_dir.mkdir(parents=True)
    (pdf_dir / "temp_combined.md").write_text(temp_text, encoding="utf-8")
    return project


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_write_override_composition_binds_receipt(tmp_path: Path) -> None:
    """Receipt binds ordered input digests and the promoted combined markdown."""
    project = _override_project(tmp_path)

    _write_override_composition(project, "proj")

    combined = project / COMBINED_RELATIVE_PATH
    assert combined.is_file()
    assert combined.read_text(encoding="utf-8") == (project / "output" / "pdf" / "temp_combined.md").read_text(
        encoding="utf-8"
    )
    receipt = project / COMPOSITION_RELATIVE_PATH
    composition = read_manuscript_composition(receipt)
    assert composition.algorithm == "shared-combined-markdown-v1"
    assert composition.combined_path == COMBINED_RELATIVE_PATH.as_posix()
    assert composition.combined_sha256 == _sha256_file(combined)
    assert [row.path for row in composition.ordered_inputs] == [
        "manuscript/01_intro.md",
        "manuscript/02_next.md",
    ]
    for row in composition.ordered_inputs:
        assert row.sha256 == _sha256_file(project / row.path)


def test_write_override_composition_missing_temp_combined_is_clean_skip(tmp_path: Path) -> None:
    """A missing override combined markdown skips cleanly instead of raising."""
    project = _override_project(tmp_path)
    (project / "output" / "pdf" / "temp_combined.md").unlink()

    _write_override_composition(project, "proj")

    assert not (project / COMPOSITION_RELATIVE_PATH).exists()
    assert not (project / COMBINED_RELATIVE_PATH).exists()


def test_write_override_composition_identical_combined_md_unchanged(tmp_path: Path) -> None:
    """An already-identical stable combined markdown is not rewritten."""
    temp_text = "# Intro\n\nHello.\n\n# Next\n\nMore.\n"
    project = _override_project(tmp_path, temp_text=temp_text)
    combined = project / COMBINED_RELATIVE_PATH
    combined.parent.mkdir(parents=True)
    combined.write_text(temp_text, encoding="utf-8")
    before = combined.stat()

    _write_override_composition(project, "proj")

    assert combined.read_text(encoding="utf-8") == temp_text
    assert (combined.stat().st_mtime_ns, combined.stat().st_size) == (before.st_mtime_ns, before.st_size)
    composition = read_manuscript_composition(project / COMPOSITION_RELATIVE_PATH)
    assert composition.combined_sha256 == _sha256_file(combined)


def test_write_override_composition_differing_combined_md_replaced(tmp_path: Path) -> None:
    """A stale stable combined markdown is replaced with the override's content."""
    temp_text = "# Intro\n\nHello.\n\n# Next\n\nMore.\n"
    project = _override_project(tmp_path, temp_text=temp_text)
    combined = project / COMBINED_RELATIVE_PATH
    combined.parent.mkdir(parents=True)
    combined.write_text("# Stale combined content\n", encoding="utf-8")

    _write_override_composition(project, "proj")

    assert combined.read_text(encoding="utf-8") == temp_text
    composition = read_manuscript_composition(project / COMPOSITION_RELATIVE_PATH)
    assert composition.combined_sha256 == _sha256_file(combined)


def test_write_override_composition_no_manuscript_inputs_skipped(tmp_path: Path) -> None:
    """An empty manuscript source skips the receipt without raising."""
    project = _override_project(tmp_path)
    (project / "manuscript" / "01_intro.md").unlink()
    (project / "manuscript" / "02_next.md").unlink()

    _write_override_composition(project, "proj")

    assert not (project / COMPOSITION_RELATIVE_PATH).exists()
    assert not (project / COMBINED_RELATIVE_PATH).exists()


def test_execute_render_pipeline_override_success_binds_receipt(tmp_path: Path) -> None:
    """A successful override render leaves the composition receipt behind."""
    project = tmp_path / "override_receipt"
    _write_minimal_project_tree(project)
    override = project / "scripts" / "_render_pdf_override.py"
    override.write_text(
        "\n".join(
            [
                "from pathlib import Path",
                "out = Path('output/pdf')",
                "out.mkdir(parents=True, exist_ok=True)",
                "(out / 'temp_combined.md').write_text('# Intro\\n\\nHello.\\n', encoding='utf-8')",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    rc = execute_render_pipeline(
        "override_receipt",
        repo_root=tmp_path,
        dependencies=_dependencies_for(project),
    )

    assert rc == 0
    composition = read_manuscript_composition(project / COMPOSITION_RELATIVE_PATH)
    assert composition.algorithm == "shared-combined-markdown-v1"
    assert composition.combined_sha256 == _sha256_file(project / COMBINED_RELATIVE_PATH)
    assert [row.path for row in composition.ordered_inputs] == ["manuscript/01_intro.md"]
