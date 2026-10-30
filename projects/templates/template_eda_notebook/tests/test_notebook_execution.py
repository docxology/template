"""Real-kernel acceptance, independent numerical reference and failing controls."""

from __future__ import annotations

import copy
from functools import cache
import hashlib
import importlib.metadata
import json
import os
import py_compile
import shutil
import shlex
import subprocess
import sys
from pathlib import Path

import nbformat
import numpy as np
import pandas as pd
import pytest
from nbclient.exceptions import CellExecutionError, CellTimeoutError

from template_eda_notebook.eda.notebook_oracle import reference_observations, verify_observations
from template_eda_notebook.notebook_execution import (
    ExecutionLimits,
    NotebookAcceptanceError,
    cli_main,
    custody_digests,
    execute_notebook,
    run_notebook,
    worker_main,
)
from template_eda_notebook.notebook_publication import public_execution_summary


PROJECT = Path(__file__).resolve().parents[1]
NOTEBOOK = "notebooks/eda_walkthrough.ipynb"


@cache
def _selected_platform_source() -> Path:
    """Bind the actual isolated environment, which can differ from copied Source."""
    result = subprocess.run(
        [sys.executable, "-I", "-c", "import infrastructure; print(infrastructure.__file__)"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return Path(result.stdout.strip()).resolve(strict=True).parent


def _copy_selected_platform(root: Path) -> Path:
    """Copy actual provider bytes for a cache fixture, without inventing a checkout.

    This owned source replica tests launcher cache selection. It is not an
    installed-wheel execution receipt; that remains the installed matrix's job.
    """
    source = _selected_platform_source()
    shutil.copytree(source, root / "infrastructure", ignore=shutil.ignore_patterns("__pycache__"))
    checkout = source.parent
    if all((checkout / name).is_file() for name in ("pyproject.toml", "uv.lock", ".python-version")):
        for name in ("pyproject.toml", "uv.lock", ".python-version"):
            shutil.copy2(checkout / name, root / name)
        shutil.copytree(checkout / "scripts", root / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
    else:
        selected = importlib.metadata.distribution("research-project-template")
        assert selected.version == "4.4.0" and selected.files is not None
        records = [path for path in selected.files if str(path).endswith(".dist-info/RECORD")]
        assert len(records) == 1
        metadata = records[0].parent
        assert not metadata.is_absolute() and ".." not in metadata.parts and len(metadata.parts) == 1
        # Preserve genuine METADATA/RECORD bytes. This is a source/cache fixture,
        # so entrypoint installation and RECORD closure are not asserted here.
        shutil.copytree(Path(selected.locate_file(metadata)), root / str(metadata))
        for name in ("METADATA", "RECORD"):
            assert (root / str(metadata) / name).read_bytes() == Path(
                selected.locate_file(metadata / name)
            ).read_bytes()
    return root


def _copy_project(root: Path) -> Path:
    for name in ("src", "data", "notebooks", "scripts"):
        shutil.copytree(PROJECT / name, root / name, ignore=shutil.ignore_patterns("__pycache__"))
    return root


@pytest.fixture(scope="module")
def executed_receipt(tmp_path_factory):
    root = _copy_project(tmp_path_factory.mktemp("executed-notebook"))
    return execute_notebook(root, interpreter=sys.executable)


@pytest.fixture
def copied_project(tmp_path):
    return _copy_project(tmp_path)


def append_cell(root: Path, source: str, *, tags: list[str] | None = None) -> None:
    notebook = nbformat.read(root / NOTEBOOK, as_version=4)
    cell = nbformat.v4.new_code_cell(source)
    cell.metadata["tags"] = tags or []
    # Saved success/error metadata is deliberately stale: acceptance must execute.
    cell.execution_count = 999
    cell.outputs = [nbformat.v4.new_output("stream", name="stdout", text="stale success\n")]
    notebook.cells.append(cell)
    nbformat.write(notebook, root / NOTEBOOK)


def _process_running(pid: int) -> bool:
    """True while ``pid`` exists and is not a terminated, unreaped zombie.

    Containers whose PID 1 does not reap orphans keep killed descendants as
    zombies; a zombie executes nothing, so it is not a surviving process.
    """
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    stat = Path(f"/proc/{pid}/stat")
    if stat.exists():
        try:
            return stat.read_text().rsplit(")", 1)[1].split()[0] != "Z"
        except (OSError, IndexError):
            return True
    return True


class TestNotebookExecution:
    def test_package_worker_writes_accepted_private_receipt(self, copied_project):
        result = copied_project / "worker.json"
        assert (
            worker_main(
                [
                    "--project",
                    str(copied_project),
                    "--result",
                    str(result),
                    "--startup-timeout",
                    "30",
                    "--cell-timeout",
                    "60",
                    "--run-timeout",
                    "180",
                ]
            )
            == 0
        )
        receipt = json.loads(result.read_text())
        assert receipt["status"] == "passed" and receipt["source_execution_audit"] == "passed"
        assert receipt["custody_sha256"] == custody_digests(copied_project, copied_project / NOTEBOOK)
        assert result.stat().st_mode & 0o777 == 0o600

    def test_fresh_selected_interpreter_preserves_sources(self, executed_receipt):
        receipt = executed_receipt
        assert receipt["status"] == "passed"
        assert receipt["interpreter"] == sys.executable
        assert receipt["kernel_pid"] != os.getpid()
        assert receipt["custody_sha256"] == custody_digests(PROJECT, PROJECT / NOTEBOOK)
        notebook = nbformat.read(PROJECT / NOTEBOOK, as_version=4)
        assert receipt["code_cells_executed"] == sum(cell.cell_type == "code" for cell in notebook.cells)
        assert all(
            cell.execution_count is None and not cell.outputs for cell in notebook.cells if cell.cell_type == "code"
        )
        consumed = Path(receipt["consumed_project_root"])
        assert all(Path(path).is_relative_to(consumed / "src") for path in receipt["loaded_sources"].values())
        assert receipt["source_execution_audit"] == "passed"
        assert receipt["pycache_prefix"] and not consumed.exists()

    def test_computations_match_independent_numpy_pandas(self, executed_receipt):
        observed = executed_receipt["observations"]
        raw = pd.read_csv(PROJECT / "data" / "measurements.csv")
        assert verify_observations(observed, raw) == ()
        numeric = raw[["height_cm", "weight_kg", "resting_hr_bpm"]].dropna().to_numpy()
        np.testing.assert_allclose(observed["matrix"]["data"], np.corrcoef(numeric, rowvar=False), atol=1e-12)
        np.testing.assert_allclose([row["mean"] for row in observed["summaries"]], numeric.mean(axis=0), atol=1e-12)

    def test_each_run_starts_a_new_kernel(self, executed_receipt, copied_project):
        second = execute_notebook(copied_project)
        assert second["kernel_pid"] != executed_receipt["kernel_pid"]
        assert second["observations"] == executed_receipt["observations"]

    def test_saved_outputs_and_error_tags_cannot_hide_cell_errors(self, copied_project):
        append_cell(copied_project, 'raise RuntimeError("controlled-cell-error")', tags=["raises-exception"])
        with pytest.raises(CellExecutionError, match="controlled-cell-error"):
            execute_notebook(copied_project)

    def test_real_kernel_disagreement_fails_acceptance(self, copied_project):
        append_cell(copied_project, "means.iloc[0, 0] += 10.0")
        with pytest.raises(NotebookAcceptanceError, match="independent oracle disagreement.*means"):
            execute_notebook(copied_project)

    def test_skipped_cell_fails_acceptance(self, copied_project):
        append_cell(copied_project, 'print("must execute")', tags=["skip-execution"])
        with pytest.raises(NotebookAcceptanceError, match="not every code cell executed"):
            execute_notebook(copied_project)

    def test_source_mutation_fails_custody(self, copied_project):
        append_cell(
            copied_project, f'Path({str(copied_project / "data/measurements.csv")!r}).write_text("changed input")'
        )
        with pytest.raises(NotebookAcceptanceError, match="custody changed"):
            execute_notebook(copied_project)

    def test_cell_deadline_terminates_a_real_kernel(self, copied_project):
        pid_file = copied_project / "kernel.pid"
        notebook = nbformat.read(copied_project / NOTEBOOK, as_version=4)
        notebook.cells.insert(
            0,
            nbformat.v4.new_code_cell(
                "import os, time\nfrom pathlib import Path\n"
                f"Path({str(pid_file)!r}).write_text(str(os.getpid()))\ntime.sleep(20)"
            ),
        )
        nbformat.write(notebook, copied_project / NOTEBOOK)
        with pytest.raises(CellTimeoutError):
            execute_notebook(copied_project, limits=ExecutionLimits(cell=1))
        pid = int(pid_file.read_text())
        with pytest.raises(ProcessLookupError):
            os.kill(pid, 0)

    def test_startup_deadline_terminates_an_unresponsive_process(self, copied_project):
        stalled = copied_project / "stalled-kernel"
        pid_path = copied_project / "stalled.pid"
        stalled.write_text(f'#!/bin/sh\nprintf "%s" "$$" > {shlex.quote(str(pid_path))}\nexec /bin/sleep 20\n')
        stalled.chmod(0o700)
        with pytest.raises(RuntimeError, match="Kernel didn't respond"):
            execute_notebook(copied_project, interpreter=stalled, limits=ExecutionLimits(startup=3, total=10))
        with pytest.raises(ProcessLookupError):
            os.kill(int((copied_project / "stalled.pid").read_text()), 0)

    def test_total_deadline_fails_without_success_receipt(self, copied_project):
        with pytest.raises(NotebookAcceptanceError, match="total deadline"):
            execute_notebook(copied_project, limits=ExecutionLimits(total=0.05))

    def test_outer_hard_deadline_removes_stale_receipt(self, copied_project):
        output = copied_project / "output" / "reports" / "notebook_execution.json"
        output.parent.mkdir(parents=True)
        output.write_text('{"status": "passed"}')
        with pytest.raises(NotebookAcceptanceError, match="hard run deadline"):
            run_notebook(copied_project, output_path=output, limits=ExecutionLimits(total=0.05))
        assert not output.exists()

    def test_outer_boundary_runs_the_actual_selected_kernel(self, copied_project):
        previous = copied_project / "output" / "reports" / "notebook_execution.json"
        previous.parent.mkdir(parents=True)
        original = b'{"schema_version":"historical-real-evidence","interpreter":"/Users/private-host/python"}\n'
        previous.write_bytes(original)
        receipt_path = run_notebook(copied_project, interpreter=sys.executable)
        receipt = json.loads(receipt_path.read_text())
        assert receipt["schema_version"] == "template-eda-notebook-summary-v1"
        assert receipt["kernel"]["interpreter_path_sha256"] == hashlib.sha256(sys.executable.encode()).hexdigest()
        assert receipt["status"] == "passed"
        assert receipt["custody_sha256"] == custody_digests(copied_project, copied_project / NOTEBOOK)
        assert str(copied_project) not in receipt_path.read_text()
        assert str(Path.home()) not in receipt_path.read_text()
        local = copied_project / "output" / ".pipeline" / "notebook_execution.json"
        complete = json.loads(local.read_text())
        assert complete["interpreter"] == sys.executable and complete["kernel_pid"] != os.getpid()
        assert local.stat().st_mode & 0o777 == 0o600
        historical = local.parent / "notebook_execution_history" / (hashlib.sha256(original).hexdigest() + ".json")
        assert historical.read_bytes() == original

    def test_actual_import_path_aliases_admit_canonical_audit_roots(self, copied_project, tmp_path):
        provider_parent = _selected_platform_source().parent
        launch = (
            "import sys\nfrom pathlib import Path\n"
            f"sys.path[:0]=[{str(copied_project / 'scripts/../src')!r},"
            f"{str(provider_parent / 'infrastructure/..')!r}]\n"
            "import infrastructure.core.bytecode_audit as audit\n"
            "import template_eda_notebook.notebook_execution as execution\n"
            "assert '..' in Path(audit.__file__).parts\n"
            "assert '..' in Path(execution.__file__).parts\n"
            f"print(execution.run_notebook(Path({str(copied_project)!r}),interpreter=sys.executable))\n"
        )
        completed = subprocess.run(
            [sys.executable, "-I", "-c", launch],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=210,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        summary = json.loads(Path(completed.stdout.strip()).read_text())
        assert summary["status"] == "passed" and summary["source_execution_audit"] == "passed"
        assert summary["custody_sha256"] == custody_digests(copied_project, copied_project / NOTEBOOK)
        assert verify_observations(summary["observations"], pd.read_csv(copied_project / "data/measurements.csv")) == ()

    def test_cli_arguments_run_real_kernel_and_portable_summary(self, copied_project, capsys):
        assert cli_main(["--project-root", str(copied_project), "--python", sys.executable]) == 0
        artifact = Path(capsys.readouterr().out.strip())
        assert artifact == copied_project / "output/reports/notebook_execution.json"
        receipt = json.loads(artifact.read_text())
        assert receipt["schema_version"] == "template-eda-notebook-summary-v1"
        assert receipt["source_execution_audit"] == "passed"

    def test_portable_summary_omits_private_runtime_fields_without_changing_computations(self, executed_receipt):
        receipt = copy.deepcopy(executed_receipt)
        receipt["unrelated_host_detail"] = "/Users/private-host/credential-location"
        before = copy.deepcopy(receipt)
        summary = public_execution_summary(receipt, PROJECT)
        assert receipt == before
        assert summary["observations"] == receipt["observations"]
        assert summary["custody_sha256"] == receipt["custody_sha256"]
        encoded = json.dumps(summary)
        assert str(PROJECT) not in encoded and str(Path.home()) not in encoded
        assert "/Users/" not in encoded
        assert "interpreter" not in summary and "kernel_pid" not in summary

    @pytest.mark.parametrize(
        "malformation",
        [
            "absolute-custody",
            "windows-custody",
            "bad-digest",
            "unbound-notebook",
            "external-source",
            "bad-module",
            "not-passed",
        ],
    )
    def test_portable_summary_refuses_unbound_receipt_paths(self, executed_receipt, malformation):
        receipt = copy.deepcopy(executed_receipt)
        if malformation == "absolute-custody":
            receipt["custody_sha256"]["/Users/private-host/data.csv"] = "a" * 64
        elif malformation == "windows-custody":
            receipt["custody_sha256"][r"C:\Users\private-host\data.csv"] = "a" * 64
        elif malformation == "bad-digest":
            receipt["custody_sha256"][NOTEBOOK] = "invalid"
        elif malformation == "unbound-notebook":
            receipt["notebook"] = "/Users/private-host/notebook.ipynb"
        elif malformation == "external-source":
            receipt["loaded_sources"]["template_eda_notebook.external"] = "/Users/private-host/external.py"
        elif malformation == "bad-module":
            receipt["loaded_sources"]["template_eda_notebook/private-host"] = str(
                PROJECT / "src/template_eda_notebook/__init__.py"
            )
        else:
            receipt["status"] = "failed"
        with pytest.raises(ValueError):
            public_execution_summary(receipt, PROJECT)

    def test_outer_deadline_kills_kernel_and_detached_descendant(self, copied_project):
        notebook = nbformat.read(copied_project / NOTEBOOK, as_version=4)
        notebook.cells.insert(
            0,
            nbformat.v4.new_code_cell(
                "import os, sys, subprocess, time\nfrom pathlib import Path\n"
                f"Path({str(copied_project / 'outer-kernel.pid')!r}).write_text(str(os.getpid()))\n"
                'child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], '
                "start_new_session=True)\n"
                f"Path({str(copied_project / 'outer-child.pid')!r}).write_text(str(child.pid))\ntime.sleep(30)",
            ),
        )
        nbformat.write(notebook, copied_project / NOTEBOOK)
        with pytest.raises(NotebookAcceptanceError, match="hard run deadline"):
            run_notebook(copied_project, limits=ExecutionLimits(total=20))
        for filename in ("outer-kernel.pid", "outer-child.pid"):
            pid = int((copied_project / filename).read_text())
            assert not _process_running(pid), f"{filename} survived the hard run deadline"
        assert not (copied_project / "output" / "reports" / "notebook_execution.json").exists()

    def test_valid_stale_timestamp_cache_cannot_execute_marker(self, copied_project):
        source = copied_project / "src/template_eda_notebook/eda/statistics.py"
        marker = copied_project / "stale-cache-executed"
        baseline = source.read_bytes()
        original = baseline + b"\n# " + b" " * 512 + b"\n"
        source.write_bytes(original)
        observed = source.stat()
        poison = (
            baseline
            + (
                f"\nfrom pathlib import Path as _PoisonPath\n_PoisonPath({str(marker)!r}).write_text('stale')\n"
            ).encode()
        )
        assert len(poison) < len(original)
        source.write_bytes(poison + b"#" + b" " * (len(original) - len(poison) - 1))
        os.utime(source, ns=(observed.st_atime_ns, observed.st_mtime_ns))
        cache = source.parent / "__pycache__" / f"{source.stem}.{sys.implementation.cache_tag}.pyc"
        cache.parent.mkdir(exist_ok=True)
        py_compile.compile(
            str(source), cfile=str(cache), doraise=True, invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP
        )
        source.write_bytes(original)
        os.utime(source, ns=(observed.st_atime_ns, observed.st_mtime_ns))
        header = cache.read_bytes()[:16]
        assert int.from_bytes(header[4:8], "little") == 0
        assert int.from_bytes(header[8:12], "little") == int(observed.st_mtime) & 0xFFFFFFFF
        assert int.from_bytes(header[12:16], "little") == len(original)
        receipt = execute_notebook(copied_project)
        assert receipt["status"] == "passed" and receipt["source_execution_audit"] == "passed"
        assert not marker.exists()
        assert source.read_bytes() == original
        assert verify_observations(receipt["observations"], pd.read_csv(copied_project / "data/measurements.csv")) == ()

    def test_kernel_consumes_frozen_input_during_original_input_aba(self, copied_project):
        original_path = copied_project / "data/measurements.csv"
        append_cell(
            copied_project,
            (
                f"_original_input = Path({str(original_path)!r})\n"
                "_saved_input = _original_input.read_bytes()\n"
                "try:\n"
                "    _original_input.write_text('different mutable input')\n"
                "    _frozen_input = load_dataset()\n"
                "    assert _frozen_input.equals(raw)\n"
                "finally:\n"
                "    _original_input.write_bytes(_saved_input)\n"
            ),
        )
        receipt = execute_notebook(copied_project)
        assert receipt["status"] == "passed"
        assert (
            receipt["custody_sha256"]["data/measurements.csv"] == hashlib.sha256(original_path.read_bytes()).hexdigest()
        )

    def test_actual_kernel_audit_rejects_poison_in_its_selected_cache(self, copied_project):
        marker = copied_project / "selected-cache-executed"
        poison = f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\nVALUE=1\n"
        append_cell(
            copied_project,
            (
                "import importlib, py_compile\n"
                "_probe = PROJECT_ROOT / 'src/template_eda_notebook/eda/audit_probe.py'\n"
                f"_poison = {poison!r}\n"
                "_source = 'VALUE=1\\n#' + ' ' * len(_poison)\n"
                "_probe.write_text(_source)\n_stat = _probe.stat()\n"
                "_probe.write_text(_poison + '#' + ' ' * (len(_source) - len(_poison) - 1))\n"
                "os.utime(_probe, ns=(_stat.st_atime_ns, _stat.st_mtime_ns))\n"
                "py_compile.compile(str(_probe), doraise=True, "
                "invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP)\n"
                "_probe.write_text(_source)\n"
                "os.utime(_probe, ns=(_stat.st_atime_ns, _stat.st_mtime_ns))\n"
                "importlib.import_module('template_eda_notebook.eda.audit_probe')\n"
                "sys.modules.pop('template_eda_notebook.eda.audit_probe')\n"
            ),
        )
        with pytest.raises(CellExecutionError, match="executed public module differs.*audit_probe"):
            execute_notebook(copied_project)
        assert not marker.exists()

    @pytest.mark.parametrize("poison_target", ["adapter", "platform"])
    def test_documented_standalone_script_ignores_valid_adapter_and_platform_caches(
        self, copied_project, tmp_path, poison_target
    ):
        platform = _copy_selected_platform(tmp_path / "selected-platform")
        source = (
            copied_project / "src/template_eda_notebook/notebook_execution.py"
            if poison_target == "adapter"
            else platform / "infrastructure/core/execution_boundary.py"
        )
        marker = tmp_path / "standalone-stale-code-executed"
        baseline = source.read_bytes()
        original = baseline
        metadata = source.stat()
        poison = f"from pathlib import Path as _Marker\n_Marker({str(marker)!r}).write_text('stale')\n".encode()
        assert len(poison) < len(original)
        source.write_bytes(poison + b"#" + b" " * (len(original) - len(poison) - 1))
        os.utime(source, ns=(metadata.st_atime_ns, metadata.st_mtime_ns))
        cache = source.parent / "__pycache__" / f"{source.stem}.{sys.implementation.cache_tag}.pyc"
        cache.parent.mkdir(exist_ok=True)
        py_compile.compile(
            str(source), cfile=str(cache), doraise=True, invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP
        )
        source.write_bytes(original)
        os.utime(source, ns=(metadata.st_atime_ns, metadata.st_mtime_ns))
        header = cache.read_bytes()[:16]
        assert int.from_bytes(header[4:8], "little") == 0
        assert int.from_bytes(header[8:12], "little") == int(metadata.st_mtime) & 0xFFFFFFFF
        assert int.from_bytes(header[12:16], "little") == len(original)
        poison_cache = cache.read_bytes()
        assert cache.is_relative_to(copied_project if poison_target == "adapter" else platform)
        module = (
            "template_eda_notebook.notebook_execution"
            if poison_target == "adapter"
            else "infrastructure.core.execution_boundary"
        )
        ordinary = (
            "import sys\nsys.pycache_prefix=None\n"
            f"sys.path[:0]=[{str(platform)!r},{str(copied_project / 'src')!r}]\n"
            f"import importlib\nimportlib.import_module({module!r})\n"
        )
        # A real ordinary interpreter must consume the timestamp-valid old
        # cache. The audited launcher below must instead consume exact source.
        probe = subprocess.run(
            [sys.executable, "-I", "-B", "-c", ordinary], cwd=tmp_path, capture_output=True, text=True, timeout=60
        )
        assert marker.is_file(), probe.stdout + probe.stderr
        assert marker.read_text() == "stale" and cache.read_bytes() == poison_cache
        marker.unlink()
        source_caches = {path: path.read_bytes() for root in (copied_project, platform) for path in root.rglob("*.pyc")}
        temporary = tmp_path / "private-runtime"
        temporary.mkdir()
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(platform)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["TMPDIR"] = str(temporary)
        completed = subprocess.run(
            [
                sys.executable,
                str(copied_project / "scripts/execute_notebook.py"),
                "--project-root",
                str(copied_project),
                "--run-timeout",
                "90",
            ],
            cwd=tmp_path,
            env=environment,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        assert not marker.exists()
        assert source.read_bytes() == original and cache.read_bytes() == poison_cache
        assert {
            path: path.read_bytes() for root in (copied_project, platform) for path in root.rglob("*.pyc")
        } == source_caches
        assert not list(temporary.glob("template-eda-launch-*"))
        published = copied_project / "output/reports/notebook_execution.json"
        receipt = json.loads(published.read_text())
        assert receipt["source_execution_audit"] == "passed"
        assert str(tmp_path) not in published.read_text()

    def test_standalone_launcher_selects_declared_sdk_before_own_source(self, copied_project, tmp_path):
        shadow = copied_project / "src/infrastructure"
        shadow.mkdir()
        marker = tmp_path / "own-sdk-shadow-executed"
        (shadow / "__init__.py").write_text(
            f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n"
            "raise RuntimeError('own source cannot select the platform')\n"
        )
        completed = subprocess.run(
            [
                sys.executable,
                "-I",
                str(copied_project / "scripts/execute_notebook.py"),
                "--project-root",
                str(copied_project),
                "--run-timeout",
                "90",
            ],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        assert not marker.exists()
        published = json.loads((copied_project / "output/reports/notebook_execution.json").read_text())
        assert published["status"] == "passed" and published["source_execution_audit"] == "passed"
        assert (
            verify_observations(published["observations"], pd.read_csv(copied_project / "data/measurements.csv")) == ()
        )

    def test_standalone_pytest_selects_declared_sdk_before_own_source(self, copied_project, tmp_path):
        for relative in ("pyproject.toml", "tests/conftest.py"):
            target = copied_project / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(PROJECT / relative, target)
        shadow = copied_project / "src/infrastructure"
        shadow.mkdir()
        marker = tmp_path / "pytest-own-sdk-shadow-executed"
        (shadow / "__init__.py").write_text(
            f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n"
            "raise RuntimeError('pytest own source cannot select the platform')\n"
        )
        fixture = copied_project / "tests/test_declared_sdk.py"
        fixture.write_text(
            "from pathlib import Path\nimport infrastructure\nimport template_eda_notebook\n"
            "def test_actual_declared_sdk():\n"
            f"    assert Path(infrastructure.__file__).resolve() == Path({str(_selected_platform_source() / '__init__.py')!r})\n"
            f"    assert Path(template_eda_notebook.__file__).resolve().is_relative_to(Path({str(copied_project / 'src')!r}))\n"
            f"    assert not Path({str(marker)!r}).exists()\n"
        )
        completed = subprocess.run(
            [
                sys.executable,
                "-I",
                "-m",
                "pytest",
                "-c",
                str(copied_project / "pyproject.toml"),
                str(fixture),
                "--no-cov",
                "-q",
            ],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=90,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        assert "1 passed" in completed.stdout and not marker.exists()

    @pytest.mark.parametrize("target", ["notebook", "source-directory", "input-fifo"])
    def test_input_admission_refuses_links_and_special_files(self, copied_project, tmp_path, target):
        if target == "notebook":
            notebook = copied_project / NOTEBOOK
            outside = tmp_path / "external.ipynb"
            notebook.rename(outside)
            notebook.symlink_to(outside)
        elif target == "source-directory":
            directory = copied_project / "src/template_eda_notebook/eda"
            outside = tmp_path / "external-source"
            directory.rename(outside)
            directory.symlink_to(outside, target_is_directory=True)
        else:
            data = copied_project / "data/measurements.csv"
            data.unlink()
            os.mkfifo(data)
        with pytest.raises((OSError, ValueError), match="symlink|regular|directory|links"):
            execute_notebook(copied_project, limits=ExecutionLimits(total=5))

    @pytest.mark.parametrize(
        "kwargs",
        [{"startup": 0}, {"cell": -1}, {"total": float("inf")}, {"total": float("nan")}, {"cell": 0.5}, {"cell": True}],
    )
    def test_invalid_deadlines_are_rejected(self, kwargs):
        with pytest.raises(ValueError, match="deadline"):
            ExecutionLimits(**kwargs)

    def test_missing_interpreter_and_notebook_escape_are_rejected(self, copied_project):
        with pytest.raises(ValueError, match="not executable"):
            execute_notebook(copied_project, interpreter=copied_project / "missing-python")
        with pytest.raises(ValueError):
            execute_notebook(copied_project, notebook_path="../escape.ipynb")


class TestNotebookOracle:
    @pytest.mark.parametrize("mutation", ["keys", "shape", "value", "nan", "bool", "label"])
    def test_independent_oracle_rejects_malformed_observations(self, mutation):
        raw = pd.read_csv(PROJECT / "data" / "measurements.csv")
        observations = copy.deepcopy(reference_observations(raw))
        if mutation == "keys":
            observations.pop("matrix")
        elif mutation == "shape":
            observations["matrix"]["data"].pop()
        elif mutation == "value":
            observations["matrix"]["data"][0][1] += 0.1
        elif mutation == "nan":
            observations["matrix"]["data"][0][1] = float("nan")
        elif mutation == "bool":
            observations["report"]["rows_out"] = True
        else:
            observations["groups"]["labels"][0] = "wrong-group"
        assert verify_observations(observations, raw)
