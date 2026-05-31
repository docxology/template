"""Canonical ephemeral project scaffold factory for infrastructure tests.

Synthetic projects live under ``tmp_path`` only — never under the real
``projects/`` tree. Default slug ``template_test`` gives tests a stable,
readable stand-in without coupling to the six public exemplars.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence


def write_doc(path: Path, body: str) -> None:
    """Write a UTF-8 text file, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def project_path(
    root: Path,
    name: str,
    *,
    program: str | None = None,
    repo_layout: bool = True,
) -> Path:
    """Return the on-disk path for a synthetic project under *root*."""
    if not repo_layout:
        return root / name
    if program:
        return root / "projects" / program / name
    return root / "projects" / name


def make_project(
    root: Path,
    name: str = "template_test",
    *,
    program: str | None = None,
    repo_layout: bool = True,
    with_manuscript: bool = False,
    with_scripts: bool = False,
    with_output: bool = False,
    with_pdf: bool = False,
    src_module: str = "stub",
    src_body: str | None = None,
) -> Path:
    """Create a minimum-valid project tree that passes ``validate_project_structure``.

    Args:
        root: Repository root (typically ``tmp_path``).
        name: Project directory name. Defaults to ``template_test``.
        program: When set, nest under ``projects/<program>/<name>/`` so
            discovery yields qualified name ``<program>/<name>``.
        repo_layout: When ``False``, create ``<root>/<name>/`` instead of
            ``<root>/projects/<name>/`` (for integration fixtures).
        with_manuscript: Create ``manuscript/config.yaml``.
        with_scripts: Create ``scripts/`` with ``__init__.py``.
        with_output: Create ``output/`` with standard subdirectories.
        with_pdf: Create ``output/pdf/<name>_combined.pdf`` (implies ``with_output``).
        src_module: Basename of the stub module under ``src/`` (without ``.py``).
        src_body: Optional Python source for the stub module.

    Returns:
        Absolute path to the project directory.
    """
    proj = project_path(root, name, program=program, repo_layout=repo_layout)
    (proj / "src").mkdir(parents=True, exist_ok=True)
    (proj / "tests").mkdir(parents=True, exist_ok=True)
    write_doc(proj / "src" / "__init__.py", "")
    module_source = src_body if src_body is not None else f'"""Synthetic module for {name}."""\n'
    write_doc(proj / "src" / f"{src_module}.py", module_source)
    write_doc(proj / "tests" / "__init__.py", "")

    if with_scripts:
        (proj / "scripts").mkdir(parents=True, exist_ok=True)
        write_doc(proj / "scripts" / "__init__.py", "")

    if with_manuscript:
        (proj / "manuscript").mkdir(parents=True, exist_ok=True)
        write_doc(
            proj / "manuscript" / "config.yaml",
            "paper:\n  title: Synthetic Test Project\n",
        )

    if with_pdf or with_output:
        output_dir = proj / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        for subdir in ("pdf", "figures", "data", "web", "slides", "reports", "logs"):
            (output_dir / subdir).mkdir(parents=True, exist_ok=True)

    if with_pdf:
        write_doc(proj / "output" / "pdf" / f"{name}_combined.pdf", "PDF" * 1000)

    return proj


def make_repo(
    root: Path,
    names: Sequence[str] = ("template_test",),
    *,
    program: str | None = None,
    **project_kwargs: object,
) -> Path:
    """Create ``projects/`` under *root* with one or more synthetic projects.

    Args:
        root: Repository root (typically ``tmp_path``).
        names: Project directory names to scaffold.
        program: Optional program directory for nested layout.
        **project_kwargs: Forwarded to each ``make_project`` call.

    Returns:
        *root* (the repository root).
    """
    (root / "projects").mkdir(parents=True, exist_ok=True)
    for project_name in names:
        make_project(root, project_name, program=program, **project_kwargs)  # type: ignore[arg-type]
    return root
