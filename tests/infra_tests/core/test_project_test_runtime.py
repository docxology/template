"""Existing-environment admission uses actual child metadata, never resolution."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import venv
from importlib.metadata import distribution
from pathlib import Path

import pytest
from packaging.requirements import Requirement

from infrastructure.core.testing.project_test_runtime import (
    ProjectTestRuntimeError,
    admit_project_test_runtime,
    project_test_deadline,
)
from infrastructure.core.testing.pytest_profiles import resolve_xdist_args


def _copy_actual_core_runner(runtime: Path) -> tuple[Path, list[Path]]:
    """Copy genuine same-ABI distributions into one benchmark-free interpreter."""
    venv.EnvBuilder(with_pip=False).create(runtime)
    python = runtime / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    observed = subprocess.run(
        [str(python), "-I", "-B", "-c", "import sysconfig; print(sysconfig.get_path('purelib'))"],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    site = Path(observed.stdout.strip())
    pending = [Requirement(name) for name in ("pytest", "pytest-cov", "pytest-timeout", "pytest-xdist", "coverage")]
    visited: set[tuple[str, tuple[str, ...]]] = set()
    selected = {}
    while pending:
        requirement = pending.pop()
        if requirement.marker is not None and not requirement.marker.evaluate():
            continue
        installed = distribution(requirement.name)
        assert requirement.specifier.contains(installed.version, prereleases=True)
        extras = tuple(sorted(requirement.extras))
        name = installed.metadata["Name"].lower().replace("_", "-")
        key = (name, extras)
        if key in visited:
            continue
        visited.add(key)
        selected[name] = installed
        for raw in installed.requires or ():
            dependency = Requirement(raw)
            if dependency.marker is None or any(
                dependency.marker.evaluate({"extra": extra}) for extra in ("", *extras)
            ):
                dependency.marker = None
                pending.append(dependency)
    assert "pytest-benchmark" not in selected
    timeout_members = []
    for name, installed in selected.items():
        assert installed.files
        for member in installed.files:
            # -m pytest needs distribution bodies/metadata, not external scripts or caches.
            if ".." in member.parts or member.suffix == ".pyc":
                continue
            origin = Path(installed.locate_file(member)).absolute()
            assert origin.is_file() and not origin.is_symlink()
            assert origin.resolve(strict=True) == origin
            target = site / member
            target.parent.mkdir(parents=True, exist_ok=True)
            digest = hashlib.sha256(origin.read_bytes()).digest()
            if not target.exists():
                shutil.copyfile(origin, target, follow_symlinks=False)
            assert hashlib.sha256(target.read_bytes()).digest() == digest
            assert hashlib.sha256(origin.read_bytes()).digest() == digest
            if name == "pytest-timeout":
                timeout_members.append(target)
    assert timeout_members
    return python, timeout_members


@pytest.mark.timeout(90)
def test_actual_current_prepared_stack_admission(tmp_path: Path) -> None:
    selected, receipt = admit_project_test_runtime(tmp_path)
    assert selected == Path(sys.executable).absolute()
    assert receipt["scope"] == "executable-prefix-metadata-versions"
    assert receipt["probe"]["missing"] == []

    # Ordinary project tests need the real core stack, not an unused benchmark plugin.
    python, timeout_members = _copy_actual_core_runner(tmp_path / ".venv")
    selected, core_receipt = admit_project_test_runtime(tmp_path, interpreter=python)
    assert selected == python
    assert "pytest-benchmark" not in core_receipt["probe"]["versions"]
    assert core_receipt["probe"]["missing"] == []
    absent = subprocess.run(
        [
            str(python),
            "-I",
            "-B",
            "-c",
            "import importlib.util; assert importlib.util.find_spec('pytest_benchmark') is None",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert absent.returncode == 0, absent.stderr

    project = tmp_path / "parallel-project"
    project.mkdir()
    (project / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    (project / "test_actual_parallel.py").write_text(
        "def test_real_file(tmp_path):\n"
        " path=tmp_path/'value.txt'; path.write_text('actual'); assert path.read_text()=='actual'\n"
        "def test_real_calculation():\n assert sum(range(8)) == 28\n",
        encoding="utf-8",
    )
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("COV_CORE_", "COVERAGE_", "TEMPLATE_PYTEST_"))
    }
    for key in ("PYTEST_PLUGINS", "PYTEST_ADDOPTS", "PYTEST_DISABLE_PLUGIN_AUTOLOAD", "PYTHONPATH", "PYTHONHOME"):
        environment.pop(key, None)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    command = [
        str(python),
        "-I",
        "-B",
        "-m",
        "pytest",
        "-c",
        "pytest.ini",
        "--no-cov",
        "-q",
        *resolve_xdist_args(2, env={}),
    ]
    actual = subprocess.run(command, cwd=project, env=environment, capture_output=True, text=True, timeout=60)
    assert actual.returncode == 0, actual.stdout + actual.stderr
    assert "2 passed" in actual.stdout

    # Removing a genuine required dependency from only this owned copy still blocks.
    timeout_metadata = {
        parent for member in timeout_members for parent in member.parents if parent.name.endswith(".dist-info")
    }
    assert timeout_metadata
    assert all(
        python.parent.parent in directory.parents
        and directory.name.lower().replace("_", "-").startswith("pytest-timeout-")
        and not directory.is_symlink()
        for directory in timeout_metadata
    )
    for member in timeout_members:
        member.unlink()
    for directory in timeout_metadata:
        shutil.rmtree(directory)
    with pytest.raises(ProjectTestRuntimeError, match="required exact runner stack") as refused:
        admit_project_test_runtime(tmp_path, interpreter=python)
    assert refused.value.exit_code == 75


@pytest.mark.timeout(90)
def test_real_empty_existing_venv_is_blocked_without_acquisition(tmp_path: Path) -> None:
    environment = tmp_path / ".venv"
    venv.EnvBuilder(with_pip=False).create(environment)
    before = sorted(str(path.relative_to(environment)) for path in environment.rglob("*"))
    with pytest.raises(ProjectTestRuntimeError) as refused:
        admit_project_test_runtime(tmp_path)
    assert refused.value.exit_code == 75
    assert sorted(str(path.relative_to(environment)) for path in environment.rglob("*")) == before


@pytest.mark.timeout(90)
def test_actual_probe_expiry_remains_timeout(tmp_path: Path) -> None:
    with pytest.raises(ProjectTestRuntimeError) as refused:
        admit_project_test_runtime(tmp_path, deadline=project_test_deadline(0.000001))
    assert refused.value.exit_code == 124


@pytest.mark.parametrize("value", [False, 0, -1, float("nan"), float("inf")])
def test_invalid_budget_is_configuration_error(value: float) -> None:
    with pytest.raises(ProjectTestRuntimeError) as refused:
        project_test_deadline(value)
    assert refused.value.exit_code == 2


@pytest.mark.timeout(90)
def test_actual_probe_interruption_precedence(tmp_path: Path) -> None:
    import os

    if os.name == "nt":
        pytest.skip("POSIX executable-wrapper control")
    environment = tmp_path / ".venv"
    venv.EnvBuilder(with_pip=False, symlinks=False).create(environment)
    selected = environment / "bin/python"
    selected.unlink()
    selected.write_text("#!/bin/sh\nexit 130\n")
    selected.chmod(0o700)
    with pytest.raises(ProjectTestRuntimeError) as refused:
        admit_project_test_runtime(tmp_path)
    assert refused.value.exit_code == 130
    assert refused.value.original_exit_code == 130


@pytest.mark.parametrize("entry", ["script", "pytest"])
@pytest.mark.timeout(120)
def test_actual_nested_child_ignores_timestamp_valid_poisoned_project_cache(tmp_path: Path, entry: str) -> None:
    import os
    import py_compile

    from infrastructure.core.execution_boundary import run_bounded_subprocess
    from infrastructure.core.testing.project_test_runtime import build_audited_project_test_command

    source = tmp_path / "src"
    source.mkdir()
    module = source / "demo.py"
    module.write_text("ANSWER = 7\n")
    original = module.stat()
    module.write_text("ANSWER = 9\n")
    os.utime(module, ns=(original.st_atime_ns, original.st_mtime_ns))
    py_compile.compile(str(module), doraise=True, invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP)
    module.write_text("ANSWER = 7\n")
    os.utime(module, ns=(original.st_atime_ns, original.st_mtime_ns))
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    if entry == "script":
        script = scripts / "verify.py"
        script.write_text("import demo\nassert demo.ANSWER == 7\nprint('ACTUAL_PROJECT_VALUE',demo.ANSWER)\n")
        command = build_audited_project_test_command(tmp_path, Path(sys.executable).absolute(), (), script=script)
    else:
        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "test_value.py").write_text("def test_value():\n import demo\n assert demo.ANSWER == 7\n")
        command = build_audited_project_test_command(
            tmp_path, Path(sys.executable).absolute(), ("tests", "-q", "--no-cov"), module="pytest"
        )
    outcome = run_bounded_subprocess(command, cwd=tmp_path, env=os.environ.copy(), timeout=60)
    assert outcome.returncode == 0, outcome.stderr
    assert "ACTUAL_PROJECT_VALUE 7" in outcome.stdout if entry == "script" else "1 passed" in outcome.stdout


@pytest.mark.timeout(120)
def test_actual_removed_project_module_mutation_is_refused_after_child(tmp_path: Path) -> None:
    import os

    from infrastructure.core.execution_boundary import run_bounded_subprocess
    from infrastructure.core.testing.project_test_runtime import build_audited_project_test_command

    (tmp_path / "src").mkdir()
    (tmp_path / "scripts").mkdir()
    (tmp_path / "src/demo.py").write_text("ANSWER = 7\n")
    script = tmp_path / "scripts/verify.py"
    script.write_text(
        "import demo,sys\nfrom pathlib import Path\nsys.modules.pop('demo')\n"
        "Path('src/demo.py').write_text('ANSWER = 8\\n')\nprint('ACTUAL_CHILD_COMPLETED')\n"
    )
    command = build_audited_project_test_command(tmp_path, Path(sys.executable).absolute(), (), script=script)
    outcome = run_bounded_subprocess(command, cwd=tmp_path, env=os.environ.copy(), timeout=60)
    assert outcome.returncode == 75
    assert "ACTUAL_CHILD_COMPLETED" in outcome.stdout
    assert "executed-code custody refused" in outcome.stderr


@pytest.mark.parametrize("actual_exit", [2, 7])
@pytest.mark.timeout(120)
def test_source_mutating_real_failure_keeps_original_child_exit(tmp_path: Path, actual_exit: int) -> None:
    import os

    from infrastructure.core.execution_boundary import run_bounded_subprocess
    from infrastructure.core.testing.project_test_runtime import build_audited_project_test_command

    (tmp_path / "src").mkdir()
    (tmp_path / "scripts").mkdir()
    (tmp_path / "src/demo.py").write_text("ANSWER = 7\n")
    script = tmp_path / "scripts/verify.py"
    script.write_text(
        "import demo\nfrom pathlib import Path\nPath('src/demo.py').write_text('ANSWER = 8\\n')\n"
        f"raise SystemExit({actual_exit})\n"
    )
    command = build_audited_project_test_command(tmp_path, Path(sys.executable).absolute(), (), script=script)
    outcome = run_bounded_subprocess(command, cwd=tmp_path, env=os.environ.copy(), timeout=60)
    assert outcome.returncode == actual_exit
    assert "executed-code custody refused" in outcome.stderr


def test_audit_roots_include_only_exactly_pinned_resolvable_exemplar_providers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from infrastructure.core.testing.project_test_runtime import project_test_audit_roots

    site = tmp_path / "site"
    provider = site / "template_owned_provider"
    provider.mkdir(parents=True)
    (provider / "__init__.py").write_text("VALUE = 1\n", encoding="utf-8")
    other = site / "template_ranged_provider"
    other.mkdir()
    (other / "__init__.py").write_text("VALUE = 2\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(site))
    project = tmp_path / "project"
    project.mkdir()
    (project / "pyproject.toml").write_text(
        "[project]\nname = 'consumer'\nversion = '1.0'\ndependencies = [\n"
        "  'template-owned-provider==1.0',\n"
        "  'template-ranged-provider>=1.0',\n"
        "  'template-absent-provider==1.0',\n"
        "  'research-project-template==4.0.1',\n]\n",
        encoding="utf-8",
    )
    roots = project_test_audit_roots(project)
    assert provider.absolute() in roots
    assert other.absolute() not in roots
    assert not any("absent" in root.name for root in roots)
    assert "template_owned_provider" not in sys.modules  # resolved without executing it


@pytest.mark.parametrize("failure", ["none", "test", "conftest"])
@pytest.mark.timeout(120)
def test_actual_audited_pytest_keeps_conftest_and_test_assertions(tmp_path: Path, failure: str) -> None:
    import os

    from infrastructure.core.execution_boundary import run_bounded_subprocess
    from infrastructure.core.testing.project_test_runtime import (
        build_audited_project_test_command,
    )

    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "pytest.ini").write_text("[pytest]\n")
    marker = tmp_path / "conftest-executed.txt"
    (tmp_path / "conftest.py").write_text(
        "import pytest\nfrom pathlib import Path\n"
        + ("assert False, 'ACTUAL_CONFTEST_ASSERTION'\n" if failure == "conftest" else "assert 7 == 7\n")
        + "Path('conftest-executed.txt').write_text('actual conftest payload')\n"
        + "@pytest.fixture\ndef actual_value():\n return 7\n"
    )
    expected = 9 if failure == "test" else 7
    (tmp_path / "tests/test_value.py").write_text(
        f"def test_value(actual_value):\n assert actual_value == {expected}\n"
    )
    args = (
        "-c",
        str(tmp_path / "pytest.ini"),
        "--rootdir",
        str(tmp_path),
        "--confcutdir",
        str(tmp_path),
        "--assert=rewrite",
        "-p",
        "no:benchmark",
        "--no-cov",
        "-q",
        *(("--", "tests") if failure == "none" else ("tests",)),
    )
    command = build_audited_project_test_command(tmp_path, Path(sys.executable).absolute(), args, module="pytest")
    option_end = args.index("--") if "--" in args else len(args)
    assert command[4:] == (*args[:option_end], "--assert=plain", *args[option_end:])
    result = run_bounded_subprocess(command, cwd=tmp_path, env=os.environ.copy(), timeout=60)
    combined = result.stdout + result.stderr
    assert "executed public module differs" not in combined
    assert "executed-code custody refused" not in combined
    if failure == "conftest":
        assert result.returncode == 4, combined
        assert "ACTUAL_CONFTEST_ASSERTION" in combined
        assert not marker.exists()
    else:
        assert marker.read_text() == "actual conftest payload"
        assert result.returncode == (1 if failure == "test" else 0), combined
        assert ("1 failed" if failure == "test" else "1 passed") in result.stdout
