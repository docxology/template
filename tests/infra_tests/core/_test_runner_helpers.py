"""Shared helpers for the split test-runner test modules (formerly test_test_runner.py)."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent


def _write_project(
    repo_root: Path,
    name: str,
    *,
    fail: bool = False,
    extra_module: str | None = None,
    sleep_seconds: float = 0.0,
    marker_file: Path | None = None,
    order_log: Path | None = None,
) -> None:
    """Create ``projects/<name>/`` with ``src/`` and ``tests/`` directories.

    The module under ``src/`` exposes a single function whose value is
    asserted by a test in ``tests/test_basic.py``. When ``fail=True`` the
    assertion is intentionally wrong so the project's pytest run fails.
    """
    project_root = repo_root / "projects" / name
    src_dir = project_root / "src"
    tests_dir = project_root / "tests"
    src_dir.mkdir(parents=True)
    tests_dir.mkdir()

    module_name = extra_module or f"mod_{name}"
    (src_dir / "__init__.py").write_text("")
    (src_dir / f"{module_name}.py").write_text(
        dedent(
            f"""
            \"\"\"Tiny module under test for project '{name}'.\"\"\"


            def value() -> int:
                return 42
            """
        ).lstrip()
    )

    (tests_dir / "__init__.py").write_text("")
    expected = "42" if not fail else "999"
    marker_path = str(marker_file) if marker_file is not None else None
    order_log_path = str(order_log) if order_log is not None else None
    (tests_dir / "conftest.py").write_text(
        dedent(
            f"""
            \"\"\"Project-local conftest for '{name}'.

            Both projects deliberately ship a conftest.py here so the test
            asserts that ``run_per_project_pytest`` invokes one pytest
            process per project (otherwise pytest refuses to register two
            conftest plugins with the same basename).
            \"\"\"

            import sys
            from pathlib import Path

            sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
            """
        ).lstrip()
    )
    (tests_dir / "test_basic.py").write_text(
        dedent(
            f"""
            import time
            from pathlib import Path

            from {module_name} import value

            MARKER_PATH = {marker_path!r}
            ORDER_LOG_PATH = {order_log_path!r}


            def test_value() -> None:
                if {sleep_seconds!r}:
                    time.sleep({sleep_seconds!r})
                if MARKER_PATH:
                    Path(MARKER_PATH).write_text({name!r}, encoding="utf-8")
                if ORDER_LOG_PATH:
                    with Path(ORDER_LOG_PATH).open("a", encoding="utf-8") as handle:
                        handle.write({name!r} + "\\n")
                assert value() == {expected}
            """
        ).lstrip()
    )


def _write_template_repo_skeleton(repo_root: Path) -> None:
    """Create the minimal ``infrastructure/`` and ``projects/`` skeleton.

    ``run_per_project_pytest`` calls
    :func:`infrastructure.project.discovery.discover_projects` with the
    synthetic ``repo_root`` when no explicit ``projects=`` argument is
    given; that helper requires ``projects/`` to exist. The infrastructure
    package itself is imported from the real installation, not from
    ``tmp_path``.
    """
    (repo_root / "projects").mkdir()


def _coverage_lines_recorded(coverage_file: Path) -> int:
    """Return the number of lines recorded in a ``.coverage`` SQLite file.

    Uses the public ``coverage.CoverageData`` API rather than poking the
    SQLite file directly so the test stays robust across coverage versions.
    """
    from coverage import CoverageData

    data = CoverageData(basename=str(coverage_file))
    data.read()
    total = 0
    for filename in data.measured_files():
        executed = data.lines(filename) or []
        total += len(executed)
    return total
