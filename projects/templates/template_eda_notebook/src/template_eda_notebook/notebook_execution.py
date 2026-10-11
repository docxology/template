"""Execute a source-bound notebook in a fresh selected-interpreter kernel.

Runtime I/O belongs here, outside the pure EDA transforms. The canonical script
also applies the repository's subprocess guardian around this finite client run.
"""

from __future__ import annotations

import argparse
import asyncio
import atexit
import hashlib
import io
import json
import math
import os
import signal
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import nbformat
import pandas as pd
from jupyter_client import AsyncKernelManager
from jupyter_client.kernelspec import KernelSpecManager
from nbclient import NotebookClient
from nbclient.exceptions import CellTimeoutError
from infrastructure.core import bytecode_audit
from infrastructure.core.execution_boundary import build_bounded_env, run_bounded_subprocess
from infrastructure.core.files.secure_write import (
    atomic_write_bytes_confined,
    atomic_write_text_confined,
    read_bytes_confined,
    unlink_confined,
)
from .notebook_publication import public_execution_summary
from infrastructure.core.implementation_custody import bytecode_audit_bootstrap, source_file_manifest

from .eda.notebook_oracle import verify_observations


_AUDIT_SOURCE = Path(bytecode_audit.__file__).resolve()


@dataclass(frozen=True)
class ExecutionLimits:
    """Positive startup/cell deadlines in seconds and a total execution budget."""

    startup: int = 30
    cell: int = 60
    total: float = 180

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if isinstance(value, bool) or not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} deadline must be finite and positive: {value!r}")
        if not isinstance(self.startup, int) or not isinstance(self.cell, int):
            raise ValueError("startup and cell deadlines must be integer seconds")


class NotebookAcceptanceError(RuntimeError):
    """Execution, custody or independent computation acceptance failed."""


_OBSERVATION_CELL = """\
import json as _json
import os as _os
import sys as _sys
from dataclasses import asdict as _asdict
from IPython.display import display as _display
_observations = {
    "report": _asdict(report),
    "missing": {str(k): int(v) for k, v in raw.isna().sum().items()},
    "clean": _json.loads(clean.to_json(orient="split", double_precision=15)),
    "summaries": [_asdict(value) for value in summaries],
    "means": _json.loads(means.to_json(orient="split", double_precision=15)),
    "matrix": _json.loads(matrix.to_json(orient="split", double_precision=15)),
    "pairs": [list(value) for value in pairs],
    "histogram": _asdict(hist), "heatmap": _asdict(heat), "groups": _asdict(groups),
    "normalized": _json.loads(norm[["height_cm", "weight_kg", "resting_hr_bpm"]].to_json(
        orient="split", double_precision=15)),
}
_display({"application/json": {
    "observations": _observations, "interpreter": _sys.executable, "kernel_pid": _os.getpid(),
    "loaded_sources": {name: module.__file__ for name, module in _sys.modules.items()
        if name.startswith("template_eda_notebook") and getattr(module, "__file__", None)},
    "pycache_prefix": _sys.pycache_prefix,
}}, raw=True)
"""


def _admitted_bytes(root: Path, notebook: Path, deadline: float | None = None) -> dict[str, bytes]:
    """Consume bounded regular bytes through held no-follow directory chains."""
    deadline = deadline if deadline is not None else time.monotonic() + 30

    def manifest(lane: str) -> dict[str, str]:
        return source_file_manifest(root / lane, frozenset({".py"}), deadline=deadline, max_entries=1024, max_depth=64)

    selected = {notebook.relative_to(root).as_posix(), "data/measurements.csv"}
    manifests = {}
    for lane in ("src", "scripts"):
        manifests[lane] = manifest(lane)
        selected.update(f"{lane}/{relative}" for relative in manifests[lane])
    if len(selected) > 1024:
        raise NotebookAcceptanceError("notebook input/source inventory exceeds its file ceiling")
    result = {}
    total_bytes = 0
    for relative in sorted(selected):
        if time.monotonic() >= deadline:
            raise NotebookAcceptanceError("notebook exceeded total deadline during input admission")
        raw = read_bytes_confined(root, root / relative, max_bytes=min(8 * 1024 * 1024, 32 * 1024 * 1024 - total_bytes))
        total_bytes += len(raw)
        result[relative] = raw
    for lane, observed in manifests.items():
        if observed != manifest(lane) or any(
            hashlib.sha256(result[f"{lane}/{name}"]).hexdigest() != digest for name, digest in observed.items()
        ):
            raise NotebookAcceptanceError("notebook/input/source custody changed during admission")
    return result


def custody_digests(project_root: Path, notebook: Path) -> dict[str, str]:
    """Bind admitted input/source bytes, excluding generated outputs."""
    root = project_root.absolute()
    return {name: hashlib.sha256(raw).hexdigest() for name, raw in _admitted_bytes(root, notebook.absolute()).items()}


async def _execute(payload: Any, root: Path, interpreter: Path, limits: ExecutionLimits, deadline: float) -> None:
    # Never register a global kernel or trust a machine's default python3 spec.
    with TemporaryDirectory(prefix="template-eda-kernel-") as temporary:
        control = Path(temporary).resolve()
        cache = control / "pycache"
        cache.mkdir(mode=0o700)
        bootstrap = bytecode_audit_bootstrap((root / "src",), cache, audit_path=_AUDIT_SOURCE)
        launch = bootstrap + (
            "from ipykernel.kernelapp import IPKernelApp\n"
            "_app=IPKernelApp.instance()\n_app.initialize()\n"
            "_app.shell.user_ns['_template_eda_verify_code']=_audit_scope['verify_executed_source_code']\n"
            "_app.start()\n"
        )
        spec = control / "template-eda-acceptance"
        spec.mkdir()
        (spec / "kernel.json").write_text(
            json.dumps(
                {
                    "argv": [
                        str(interpreter),
                        "-I",
                        "-X",
                        f"pycache_prefix={cache}",
                        "-c",
                        launch,
                        "-f",
                        "{connection_file}",
                    ],
                    "display_name": "EDA acceptance",
                    "language": "python",
                }
            ),
            encoding="utf-8",
        )
        manager = AsyncKernelManager(
            kernel_name=spec.name,
            kernel_spec_manager=KernelSpecManager(kernel_dirs=[temporary], ensure_native_kernel=False),
        )
        client = NotebookClient(
            payload,
            km=manager,
            timeout=limits.cell,
            startup_timeout=limits.startup,
            allow_errors=False,
            force_raise_errors=True,
            raise_on_iopub_timeout=True,
            iopub_timeout=limits.cell,
            shutdown_kernel="immediate",
        )
        try:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise NotebookAcceptanceError("notebook exceeded total deadline before kernel startup")
            await asyncio.wait_for(client.async_execute(cwd=str(root), cleanup_kc=True), timeout=remaining)
        except CellTimeoutError:
            # NBClient's cell timeout inherits TimeoutError; preserve that boundary.
            raise
        except TimeoutError as exc:
            raise NotebookAcceptanceError(f"notebook exceeded total deadline {limits.total}s") from exc
        finally:
            # NBClient startup failures occur before its own cleanup context yields.
            try:
                if manager.has_kernel:
                    await asyncio.wait_for(manager.shutdown_kernel(now=True), timeout=limits.startup)
            finally:
                # NBClient registers these before startup, while its unregister
                # runs only after startup succeeds. Avoid dangling exit callbacks.
                atexit.unregister(client._cleanup_kernel)
                if os.name == "posix":
                    for signum in (signal.SIGINT, signal.SIGTERM):
                        asyncio.get_running_loop().remove_signal_handler(signum)


def execute_notebook(
    project_root: Path,
    *,
    notebook_path: str = "notebooks/eda_walkthrough.ipynb",
    interpreter: str | Path | None = None,
    limits: ExecutionLimits | None = None,
) -> dict[str, Any]:
    """Execute a copy, verify fresh computations and return a local custody receipt.

    No saved output or execution count is accepted as evidence. A temporary
    observation cell reads the results already produced by this kernel without
    rewriting the source notebook. Cell errors and timeouts propagate as failure.
    """
    root = Path(project_root).absolute()
    notebook = (root / notebook_path).absolute()
    if ".." in notebook.parts:
        raise ValueError("notebook path cannot contain parent traversal")
    notebook.relative_to(root)
    python = Path(interpreter or sys.executable).absolute()
    if not python.is_file() or not os.access(python, os.X_OK):
        raise ValueError(f"selected interpreter is not executable: {python}")
    deadlines = limits or ExecutionLimits()
    deadline = time.monotonic() + deadlines.total
    admitted = _admitted_bytes(root, notebook, deadline)
    before = {name: hashlib.sha256(raw).hexdigest() for name, raw in admitted.items()}
    payload = nbformat.reads(admitted[notebook.relative_to(root).as_posix()].decode("utf-8"), as_version=4)
    nbformat.validate(payload)
    for cell in payload.cells:
        if cell.cell_type == "code":
            cell.execution_count = None
            cell.outputs = []
    with TemporaryDirectory(prefix="template-eda-inputs-") as temporary:
        consumed_root = Path(temporary).resolve()
        for relative, raw in admitted.items():
            target = consumed_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            target.chmod(0o400)
        payload.cells.append(
            nbformat.v4.new_code_cell(
                f"_template_eda_verify_code(Path({str(consumed_root / 'src')!r}), Path(sys.pycache_prefix))\n"
                + _OBSERVATION_CELL
            )
        )
        asyncio.run(_execute(payload, consumed_root, python, deadlines, deadline))
        if _admitted_bytes(consumed_root, consumed_root / notebook.relative_to(root), deadline) != admitted:
            raise NotebookAcceptanceError("consumed notebook/input/source custody changed during execution")
    counts = [cell.execution_count for cell in payload.cells if cell.cell_type == "code"]
    if counts != list(range(1, len(counts) + 1)):
        raise NotebookAcceptanceError("not every code cell executed in source order")
    snapshots = [
        output.data["application/json"]
        for output in payload.cells[-1].outputs
        if output.output_type == "display_data" and "application/json" in output.data
    ]
    if len(snapshots) != 1:
        raise NotebookAcceptanceError("kernel did not produce exactly one observation snapshot")
    snapshot = snapshots[0]
    if Path(snapshot["interpreter"]).absolute() != python:
        raise NotebookAcceptanceError("kernel interpreter differs from the selected interpreter")
    loaded = snapshot["loaded_sources"]
    for path in loaded.values():
        relative = str(Path(path).absolute().relative_to(consumed_root))
        if relative not in before:
            raise NotebookAcceptanceError(f"kernel imported an unbound project source: {relative}")
    if not loaded or _admitted_bytes(root, notebook, deadline) != admitted:
        raise NotebookAcceptanceError("notebook/input/source custody changed during execution")
    issues = verify_observations(snapshot["observations"], pd.read_csv(io.BytesIO(admitted["data/measurements.csv"])))
    if issues:
        raise NotebookAcceptanceError("independent oracle disagreement: " + "; ".join(issues[:8]))
    if time.monotonic() >= deadline:
        raise NotebookAcceptanceError("notebook exceeded total deadline during final custody/oracle checks")
    return {
        "schema_version": "template-eda-notebook-execution-v1",
        "status": "passed",
        "notebook": str(notebook.relative_to(root)),
        "custody_sha256": before,
        "limits_seconds": asdict(deadlines),
        "code_cells_executed": sum(cell.cell_type == "code" for cell in payload.cells[:-1]),
        "consumed_project_root": str(consumed_root),
        "source_execution_audit": "passed",
        **snapshot,
    }


# Loaded implementation locations can retain harmless import-path aliases such
# as tests/../src. Admit their canonical locations before installing the strict
# no-traversal audit; consumed project inputs still use no-follow file custody.
_PACKAGE = Path(__file__).resolve().parent
_PROJECT = _PACKAGE.parent.parent if _PACKAGE.parent.name == "src" else None


def worker_main(argv: list[str] | None = None) -> int:
    """Execute within the admitted package and write only an accepted local receipt."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--startup-timeout", type=int, required=True)
    parser.add_argument("--cell-timeout", type=int, required=True)
    parser.add_argument("--run-timeout", type=float, required=True)
    args = parser.parse_args(argv)
    receipt = execute_notebook(
        args.project,
        interpreter=sys.executable,
        limits=ExecutionLimits(args.startup_timeout, args.cell_timeout, args.run_timeout),
    )
    atomic_write_text_confined(
        args.result.absolute().parent,
        args.result.absolute(),
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        mode=0o600,
    )
    return 0


def run_notebook(
    project_root: Path | None = None,
    *,
    interpreter: str | Path | None = None,
    limits: ExecutionLimits | None = None,
    output_path: Path | None = None,
) -> Path:
    """Retain complete local evidence and publish a portable scientific summary."""
    started = time.monotonic()
    selected_root = project_root if project_root is not None else _PROJECT
    if selected_root is None:
        raise ValueError("installed notebook execution requires an explicit project_root")
    root = selected_root.resolve()
    python = Path(interpreter or sys.executable).absolute()
    deadlines = limits or ExecutionLimits()
    deadline = started + deadlines.total
    output = output_path or root / "output" / "reports" / "notebook_execution.json"
    local = root / "output" / ".pipeline" / "notebook_execution.json"
    # Retain exact previous evidence before removing either latest-success
    # pointer. This also migrates the formerly published machine-local receipt.
    for previous in (local, output):
        if previous.exists():
            raw = read_bytes_confined(root, previous)
            historical = local.parent / "notebook_execution_history" / (hashlib.sha256(raw).hexdigest() + ".json")
            atomic_write_bytes_confined(root, historical, raw, mode=0o600)
            unlink_confined(root, previous)
    environment = build_bounded_env()
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONSTARTUP", None)
    with TemporaryDirectory(prefix="template-eda-run-") as temporary:
        control = Path(temporary).resolve()
        result_path = control / "receipt.json"
        cache = control / "pycache"
        cache.mkdir(mode=0o700)
        platform = _AUDIT_SOURCE.parents[1]
        roots: tuple[Path, ...] = (_PACKAGE, platform)
        if _PROJECT is not None and (_PROJECT / "scripts").is_dir():
            roots += (_PROJECT / "scripts",)
        if (platform.parent / "scripts").is_dir():
            roots += (platform.parent / "scripts",)
        bootstrap = bytecode_audit_bootstrap(roots, cache, audit_path=_AUDIT_SOURCE)
        launch = bootstrap + (
            f"sys.path.insert(0,{str(platform.parent)!r})\n"
            "import infrastructure\n"
            f"if infrastructure.__file__ is None or Path(infrastructure.__file__).resolve() != Path({str(platform / '__init__.py')!r}):\n"
            "    raise RuntimeError('the admitted platform provider changed before worker startup')\n"
            f"sys.path.insert(0,{str(_PACKAGE.parent)!r})\n"
            "from template_eda_notebook.notebook_execution import worker_main\n"
            "_code=worker_main()\n"
            + "".join(
                f"_audit_scope['verify_executed_source_code'](Path({str(path)!r}),Path(sys.pycache_prefix))\n"
                for path in roots
            )
            + "raise SystemExit(_code)\n"
        )
        # The bootstrap remains stdlib-only until the pre-import audit exists.
        launch = "from pathlib import Path\n" + launch
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise NotebookAcceptanceError(
                "notebook acceptance failed: hard run deadline exceeded before worker startup"
            )
        result = run_bounded_subprocess(
            [
                str(python),
                "-I",
                "-X",
                f"pycache_prefix={cache}",
                "-c",
                launch,
                "--project",
                str(root),
                "--result",
                str(result_path),
                "--startup-timeout",
                str(deadlines.startup),
                "--cell-timeout",
                str(deadlines.cell),
                "--run-timeout",
                str(deadlines.total),
            ],
            cwd=root,
            env=environment,
            timeout=remaining,
        )
        if result.timed_out or result.returncode != 0:
            reason = "hard run deadline exceeded" if result.timed_out else result.command_error or result.stderr
            raise NotebookAcceptanceError(f"notebook acceptance failed: {reason}")
        receipt = json.loads(result_path.read_text(encoding="utf-8"))
    if time.monotonic() >= deadline:
        raise NotebookAcceptanceError("notebook acceptance failed: hard run deadline exceeded during final custody")
    atomic_write_text_confined(root, local, json.dumps(receipt, indent=2, sort_keys=True) + "\n", mode=0o600)
    summary = public_execution_summary(receipt, root)
    atomic_write_text_confined(root, output, json.dumps(summary, indent=2, sort_keys=True) + "\n")
    if time.monotonic() >= deadline:
        unlink_confined(root, local)
        unlink_confined(root, output)
        raise NotebookAcceptanceError(
            "notebook acceptance failed: hard run deadline exceeded during receipt persistence"
        )
    return output


def cli_main(argv: list[str] | None = None) -> int:
    """Expose interpreter and finite deadlines for canonical analysis discovery."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=_PROJECT)
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument("--startup-timeout", type=int, default=30)
    parser.add_argument("--cell-timeout", type=int, default=60)
    parser.add_argument("--run-timeout", type=float, default=180)
    args = parser.parse_args(argv)
    print(
        run_notebook(
            args.project_root,
            interpreter=args.python,
            limits=ExecutionLimits(args.startup_timeout, args.cell_timeout, args.run_timeout),
        )
    )
    return 0


__all__ = [
    "ExecutionLimits",
    "NotebookAcceptanceError",
    "custody_digests",
    "execute_notebook",
    "run_notebook",
    "cli_main",
    "worker_main",
]
