"""Bounded actual XeTeX references with explicit backend and dependency custody."""

from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined
from infrastructure.reporting.native_format_acceptance_checks import native_tool_record
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SCHEMA = "template-native-source-tex-reference-v1"
MAX_DEPENDENCIES = 2048
MAX_DEPENDENCY_BYTES = 256 * 1024 * 1024


def _process(
    root: Path,
    directory: Path,
    tool: str,
    arguments: list[str],
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    purpose: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    record = native_tool_record(
        root, directory, tool, arguments, env=env, deadline=deadline, run_id=run_id, purpose=purpose
    )
    raw = json.loads(SnapshotReader(root).read(record["artifact"]["path"]).content)
    if raw["original_exit_code"] != 0 or raw["exit_code"] != 0:
        raise ValueError(f"actual source-reference {purpose} failed")
    return record, raw


def _binding(root: Path, path: Path) -> dict[str, str]:
    snapshot = SnapshotReader(root).read(path.relative_to(root).as_posix())
    return {"path": snapshot.relative, "sha256": snapshot.sha256}


def observe_tex_reference(
    root: Path, directory: Path, tex_bytes: bytes, *, env: dict[str, str], deadline: float, run_id: str
) -> dict[str, Any]:
    """Execute source-only TeX, freeze actual dependencies, then rerun unchanged.

    The discovery run is retained but cannot stand in for the final reference.
    Native backend font/maps are observed separately because TeX FLS omits them.
    """
    if not tex_bytes or len(tex_bytes) > 4 * 1024 * 1024:
        raise ValueError("source-only TeX exceeds its finite byte budget")
    started = time.monotonic()
    budget_seconds = deadline - started
    if not 0 < budget_seconds <= 3600:
        raise ValueError("source reference requires an original finite execution budget")
    source = directory / "reference.tex"
    atomic_write_bytes_confined(root, source, tex_bytes, mode=0o600)
    environment = dict(env)
    for name in ("TEXMFHOME", "TEXMFCONFIG", "TEXMFVAR"):
        path = directory / name.lower()
        path.mkdir(parents=True, exist_ok=True, mode=0o700)
        environment[name] = str(path)
    environment["openin_any"] = "p"
    environment["openout_any"] = "p"
    tools = []
    runtime = {}
    for name in ("xelatex", "xdvipdfmx", "kpsewhich"):
        record, process = _process(
            root,
            directory,
            name,
            ["--version"],
            env=environment,
            deadline=deadline,
            run_id=run_id,
            purpose=f"reference-{name}-version",
        )
        tools.append(record)
        runtime[name] = {
            "path": process["executable"],
            "sha256": process["executable_sha256"],
            "version": process["stdout"],
        }
    allowed_roots = []
    for variable in ("TEXMFDIST", "TEXMFROOT"):
        record, process = _process(
            root,
            directory,
            "kpsewhich",
            [f"--var-value={variable}"],
            env=environment,
            deadline=deadline,
            run_id=run_id,
            purpose=f"reference-{variable.lower()}",
        )
        tools.append(record)
        path = Path(process["stdout"].strip()).resolve(strict=True)
        if not path.is_dir() or not path.is_absolute():
            raise ValueError("source reference distribution root is invalid")
        allowed_roots.append(path)
    compiler_args = [
        "-fmt=xelatex",
        "-no-pdf",
        "-no-shell-escape",
        "-recorder",
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-jobname=reference",
        f"-output-directory={directory}",
        str(source),
    ]
    backend_args = [
        "--kpathsea-debug=4",
        "-vv",
        "-o",
        str(directory / "reference.pdf"),
        str(directory / "reference.xdv"),
    ]

    def compile_reference(label: str) -> tuple[bytes, str]:
        record, process = _process(
            root,
            directory,
            "xelatex",
            compiler_args,
            env=environment,
            deadline=deadline,
            run_id=run_id,
            purpose=f"reference-{label}-compiler",
        )
        tools.append(record)
        log = SnapshotReader(root).read((directory / "reference.log").relative_to(root).as_posix()).content
        if re.search(
            rb"Undefined control sequence|Missing character:|undefined references|undefined citations|LaTeX Error", log
        ):
            raise ValueError("source reference compiler has unresolved source glyphs or identities")
        xdv = SnapshotReader(root).read((directory / "reference.xdv").relative_to(root).as_posix()).content
        atomic_write_bytes_confined(root, directory / f"{label}-xdv.bin", xdv, mode=0o600)
        atomic_write_bytes_confined(root, directory / f"{label}-compiler-log.bin", log, mode=0o600)
        record, process = _process(
            root,
            directory,
            "xdvipdfmx",
            backend_args,
            env=environment,
            deadline=deadline,
            run_id=run_id,
            purpose=f"reference-{label}-backend",
        )
        tools.append(record)
        if (directory / "reference.xdv").read_bytes() != xdv:
            raise ValueError("actual native backend input changed during consumption")
        fls = SnapshotReader(root).read((directory / "reference.fls").relative_to(root).as_posix()).content
        return fls, process["stderr"] + process["stdout"]

    discovery_fls, discovery_backend = compile_reference("discovery")
    atomic_write_bytes_confined(root, directory / "discovery.fls", discovery_fls, mode=0o600)

    def dependencies(fls: bytes, backend: str) -> list[Path]:
        admitted: set[Path] = set()
        for line in fls.decode().splitlines():
            if not line.startswith("INPUT "):
                continue
            path = Path(line.removeprefix("INPUT "))
            path = path if path.is_absolute() else root / path
            if path.resolve().is_relative_to(directory.resolve()):
                if path.suffix not in {".tex", ".aux", ".out"}:
                    raise ValueError("unexpected generated TeX input")
                continue
            admitted.add(path)
        opened = re.findall(r"kdebug:fopen\(([^,\n]+), r(?:b)?\) => (0x[0-9a-fA-F]+)", backend)
        if not opened:
            raise ValueError("native backend omitted its actual file-open observations")
        for name, pointer in opened:
            if int(pointer, 16) == 0:
                continue
            path = Path(name)
            path = path if path.is_absolute() else root / path
            if path.resolve().is_relative_to(directory.resolve()):
                if path.suffix not in {".xdv", ".tex", ".aux", ".out"}:
                    raise ValueError("unexpected private native backend input")
                continue
            admitted.add(path)
        if not any(path.suffix.lower() in {".otf", ".ttf", ".pfb", ".pk"} for path in admitted):
            raise ValueError("native source reference omitted actual font-file opens")
        if not admitted or len(admitted) > MAX_DEPENDENCIES:
            raise ValueError("source reference dependency set is empty or exceeds its budget")
        for path in admitted:
            resolved = path.resolve(strict=True)
            if not any(resolved.is_relative_to(base) for base in allowed_roots) or not resolved.is_file():
                raise ValueError("native reference dependency escapes the admitted public TeX distribution")
        return sorted(admitted, key=str)

    discovered = dependencies(discovery_fls, discovery_backend)
    retained: list[dict[str, Any]] = []
    total = 0
    for index, path in enumerate(discovered):
        resolved = path.resolve(strict=True)
        content = read_bytes_confined(resolved.parent, resolved, max_bytes=64 * 1024 * 1024)
        total += len(content)
        if total > MAX_DEPENDENCY_BYTES:
            raise ValueError("source reference dependency bytes exceed their finite budget")
        target = directory / "dependencies" / f"{index:04d}-{resolved.name}.bin"
        atomic_write_bytes_confined(root, target, content, mode=0o600)
        retained.append(
            {
                "original_path": str(path),
                "resolved_path": str(resolved),
                "size_bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
                "artifact": _binding(root, target),
            }
        )
    final_fls, final_backend = compile_reference("final")
    final_paths = dependencies(final_fls, final_backend)
    if [str(path) for path in final_paths] != [item["original_path"] for item in retained]:
        raise ValueError("actual reference dependency closure changed during final execution")
    for item in retained:
        path = Path(item["original_path"])
        if (
            str(path.resolve(strict=True)) != item["resolved_path"]
            or hashlib.sha256(
                read_bytes_confined(
                    Path(item["resolved_path"]).parent, Path(item["resolved_path"]), max_bytes=64 * 1024 * 1024
                )
            ).hexdigest()
            != item["sha256"]
        ):
            raise ValueError("actual reference dependency changed before/after final execution")
    if source.read_bytes() != tex_bytes:
        raise ValueError("source reference changed during compilation")
    runtime_after = {}
    for name, before in runtime.items():
        executable = Path(before["path"])
        digest = hashlib.sha256(executable.read_bytes()).hexdigest()
        if digest != before["sha256"]:
            raise ValueError("native reference executable changed during execution")
        runtime_after[name] = {**before, "sha256": digest}
    atomic_write_bytes_confined(root, directory / "final.fls", final_fls, mode=0o600)
    if time.monotonic() >= deadline:
        raise TimeoutError("source reference exhausted its original finite execution budget")
    return {
        "schema_version": SCHEMA,
        "execution_budget_seconds": budget_seconds,
        "elapsed_seconds": time.monotonic() - started,
        "source": _binding(root, source),
        "pdf": _binding(root, directory / "reference.pdf"),
        "discovery_fls": _binding(root, directory / "discovery.fls"),
        "final_fls": _binding(root, directory / "final.fls"),
        "backend_inputs": {label: _binding(root, directory / f"{label}-xdv.bin") for label in ("discovery", "final")},
        "compiler_logs": {
            label: _binding(root, directory / f"{label}-compiler-log.bin") for label in ("discovery", "final")
        },
        "consumed_backend_path": (directory / "reference.xdv").relative_to(root).as_posix(),
        "runtime_before": runtime,
        "runtime_after": runtime_after,
        "dependencies_before": retained,
        "dependencies_after": retained,
        "backend_input_policy": "actual successful Kpathsea file opens plus native fonts/metrics and every TeX FLS input",
        "tool_artifacts": tools,
        "environment": {
            name: environment[name] for name in ("TEXMFHOME", "TEXMFCONFIG", "TEXMFVAR", "openin_any", "openout_any")
        },
        "status": "pass",
    }
