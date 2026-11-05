"""Finite real citation tools and observed TeX dependency custody.

Discovery is diagnostic. Only the subsequent fresh compilation, with every
discovered immutable dependency observed before and after, supplies a reference.
Receipts preserve local observations; hashes do not authenticate remote origin.
"""

from __future__ import annotations

import hashlib
import math
import re
import shutil
import time
from pathlib import Path
from typing import Any, TYPE_CHECKING

from infrastructure.core.files.secure_write import (
    atomic_write_bytes_confined,
    read_bytes_confined,
)
from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.reporting.native_format_acceptance_checks import (
    NativeToolUnavailable,
)
from infrastructure.reporting.native_format_acceptance_contracts import (
    CITATION_TOOL_FIELDS,
    TOOL_SCHEMA,
    create_private_native_directory,
)
from infrastructure.reporting.native_citation_process_custody import (
    CitationOriginalInvocation,
    OriginalCitationToolObserver,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

if TYPE_CHECKING:
    from infrastructure.reporting.native_tool_process import NativeLiveToolProcess
    from typing import Callable
    from infrastructure.reporting.native_loader_observation import NativeLoaderObservation

DEPENDENCY_SCHEMA = "template-native-citation-dependency-observation-v1"
EXECUTABLE_SCHEMA = "template-native-executable-observation-v1"


def budget(deadline: float) -> float:
    """Use the caller's original clock and the existing native child ceiling."""
    if type(deadline) not in {int, float} or not math.isfinite(deadline):
        raise ValueError("citation observation requires an original finite deadline")
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("citation observer exhausted its original finite deadline")
    return min(remaining, 120)


def file_observation(path: Path) -> dict[str, Any]:
    """Observe installed dependency bytes through confined no-follow reads."""
    selected = path.resolve(strict=True)
    content = read_bytes_confined(selected.parent, selected, max_bytes=512 * 1024 * 1024)
    return {
        "path": str(selected),
        "name": selected.name,
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
    }


class CitationRuntime:
    """Private source inputs, real outcomes and immutable before/after records."""

    def __init__(
        self,
        root: Path,
        directory: Path,
        *,
        env: dict[str, str],
        deadline: float,
        run_id: str,
        on_original_tool: OriginalCitationToolObserver | None = None,
    ):
        budget(deadline)
        self.root = root.absolute()
        self.directory = directory.absolute()
        create_private_native_directory(self.root, self.directory)
        self.env, self.deadline, self.run_id = dict(env), deadline, run_id
        self.on_original_tool = on_original_tool
        self.inputs: dict[Path, dict[str, Any]] = {}
        self.tools: list[dict[str, Any]] = []

    def freeze(self, name: str, content: bytes) -> Path:
        if not name or Path(name).name != name or name in {".", ".."}:
            raise ValueError("citation private input name is invalid")
        path = self.directory / name
        if path.exists():
            raise ValueError("citation private inputs must be fresh")
        atomic_write_bytes_confined(self.root, path, content, mode=0o600)
        self.inputs[path] = file_observation(path)
        return path

    def unchanged(self) -> None:
        budget(self.deadline)
        if any(file_observation(path) != row for path, row in self.inputs.items()):
            raise ValueError("citation source/private input changed during original observation")

    def tool(
        self,
        name: str,
        arguments: list[str],
        purpose: str,
        *,
        input_paths: tuple[Path, ...] = (),
        while_live: Callable[[NativeLiveToolProcess], None] | None = None,
        stdin_path: Path | None = None,
        loader: NativeLoaderObservation | None = None,
        cwd: Path | None = None,
        phase_deadline: float | None = None,
        preserve_nominated_launcher: bool = False,
    ) -> dict[str, Any]:
        """Retain direct native OS custody and notify its actual Source owner."""
        from infrastructure.reporting.native_tool_process import run_native_tool_process
        from infrastructure.reporting.native_tool_producer import (
            current_native_producer_operation,
        )

        operation_deadline = min(self.deadline, time.monotonic() + 120.0)
        if phase_deadline is not None:
            budget(phase_deadline)
            if phase_deadline > operation_deadline:
                raise ValueError("citation Source-selected phase clock cannot extend the native tool ceiling")
            operation_deadline = phase_deadline
        if loader is not None:
            budget(loader.deadline)
            if loader.deadline > operation_deadline:
                raise ValueError("loader Source clock exceeds the actual native tool ceiling")
            operation_deadline = loader.deadline
        selected_cwd = self.directory if cwd is None else cwd.absolute()
        if (
            selected_cwd != selected_cwd.resolve(strict=True)
            or not selected_cwd.is_relative_to(self.root)
            or not selected_cwd.is_dir()
            or (stdin_path is not None and stdin_path.parent != selected_cwd)
        ):
            raise ValueError("citation cwd/stdin differs from a confined real Source-selected directory")
        if stdin_path is not None:
            if stdin_path not in self.inputs:
                raise ValueError("citation stdin must be a genuine runtime-frozen original input")
            if stdin_path not in input_paths:
                input_paths = (*input_paths, stdin_path)
        self.unchanged()
        producer = current_native_producer_operation()
        if self.on_original_tool is not None and producer is None:
            raise ValueError("citation original callback requires the actual live Source owner before launch")
        if producer is not None:
            producer.verify(SnapshotReader(self.root), run_id=self.run_id, deadline=self.deadline)
        selected = shutil.which(name, path=self.env.get("PATH"))
        if not selected:
            raise NativeToolUnavailable(f"{name} is not installed in the selected citation environment")
        executable = Path(selected).resolve(strict=True)
        before = file_observation(executable)
        extra_before = [file_observation(path) for path in input_paths]
        consumed = []
        for index, (path, observation) in enumerate(zip(input_paths, extra_before, strict=True)):
            content = self.read(path)
            if hashlib.sha256(content).hexdigest() != observation["sha256"]:
                raise ValueError("citation generated input changed before original process admission")
            frozen = self.freeze(f"consumed-{purpose}-{index:02d}.input", content)
            consumed.append(
                {
                    "observation": observation,
                    "artifact": {
                        "path": frozen.relative_to(self.root).as_posix(),
                        "sha256": observation["sha256"],
                    },
                }
            )
        if time.monotonic() >= operation_deadline:
            raise TimeoutError("citation tool Source admission exhausted its existing native ceiling")
        result = run_native_tool_process(
            self.directory,
            name,
            arguments,
            cwd=selected_cwd,
            env=self.env,
            deadline=operation_deadline,
            purpose=purpose,
            while_live=while_live,
            stdin_path=stdin_path,
            loader=loader,
            preserve_nominated_launcher=preserve_nominated_launcher,
        )
        if result["nomination"] is None:
            raise NativeToolUnavailable("citation actual native tool nomination was unavailable")
        nominated = str(Path(selected).absolute())
        if (
            result["nomination"] != {"tool": name, "path": nominated, "resolved_path": str(executable)}
            or result["launcher_preserved"] is not preserve_nominated_launcher
            or result["command"] != [nominated if preserve_nominated_launcher else str(executable), *arguments]
        ):
            raise ValueError("citation actual nominated native executable or selected launcher changed")
        after = file_observation(executable)
        original = result["original_exit_code"]
        complete = result["accepted"]
        code = 124 if result["timed_out"] else 75 if not complete and original in (None, 0, 75) else original
        reader = SnapshotReader(self.root)
        process = reader.read((self.directory / f"{purpose}.native-process.json").relative_to(self.root).as_posix())
        streams = {}
        for channel in ("stdout", "stderr"):
            raw = result.get(f"raw_{channel}")
            if raw is not None:
                snapshot = reader.read(Path(raw["path"]).relative_to(self.root).as_posix())
                if snapshot.sha256 != raw["sha256"] or len(snapshot.content) != raw["bytes"]:
                    raise ValueError("citation original raw native stream changed before retention")
                streams[channel] = {
                    "path": snapshot.relative,
                    "sha256": snapshot.sha256,
                    "bytes": len(snapshot.content),
                }
        payload = {
            "schema_version": TOOL_SCHEMA,
            "run_id": self.run_id,
            "tool": name,
            "purpose": purpose,
            "executable": str(executable),
            "executable_sha256": before["sha256"],
            "executable_observation_before": result["executable_observation_before"],
            "executable_observation_after": result["executable_observation_after"],
            "executable_identity_before": result.get("executable_identity_before"),
            "executable_identity_after": result.get("executable_identity_after"),
            "command": result["command"],
            "pid": result["pid"],
            "owner_pid": result["owner_pid"],
            "started_at_monotonic": result["operation_begin"]["monotonic"],
            "duration_seconds": result["operation_end"]["monotonic"] - result["operation_begin"]["monotonic"],
            "original_deadline_monotonic": operation_deadline,
            "caller_deadline_monotonic": self.deadline,
            "cwd": str(selected_cwd),
            "environment_digest": canonical_digest(self.env),
            "input_observations_before": [*self.inputs.values(), *extra_before],
            "consumed_input_artifacts": consumed,
            "exit_code": code,
            "original_exit_code": original,
            "timed_out": result["timed_out"],
            "custody_refused": not complete,
            "diagnostic": "; ".join(result["diagnostics"]),
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "raw_stdout": streams.get("stdout"),
            "raw_stderr": streams.get("stderr"),
            "native_process_artifact": {
                "path": process.relative,
                "sha256": process.sha256,
            },
        }
        self.unchanged()
        extra_after = [file_observation(path) for path in input_paths]
        payload["input_observations_after"] = [
            *[file_observation(path) for path in self.inputs],
            *extra_after,
        ]
        if set(payload) != CITATION_TOOL_FIELDS:
            raise ValueError("citation ToolAPI differs from the exact shared original fieldset")
        binding = write_json(self.root, self.directory / f"{purpose}.json", payload)
        self.tools.append(binding)
        if before != after or extra_before != extra_after or not reader.unchanged():
            raise ValueError("citation executable/input/original native artifacts changed during execution")
        if producer is not None and complete:
            producer._retain_actual_tool(
                self.root,
                binding,
                payload["native_process_artifact"],
                result,
                run_id=self.run_id,
                deadline=self.deadline,
            )
            if self.on_original_tool is not None:
                self.on_original_tool(
                    CitationOriginalInvocation(
                        producer,
                        self.root,
                        binding["path"],
                        binding["sha256"],
                        operation_deadline,
                        time.monotonic(),
                    )
                )
        if not complete:
            if result["timed_out"]:
                raise TimeoutError("actual citation tool exhausted its original finite deadline")
            raise NativeToolUnavailable(
                "citation original native guardian/evidence custody refused: " + payload["diagnostic"]
            )
        if code != 0 or original != 0 or payload["diagnostic"]:
            raise ValueError(
                f"actual citation {name} failed ({code}/{original}): "
                f"{payload['diagnostic'] or payload['stderr'] or payload['stdout']}"
            )
        self.unchanged()
        if producer is not None:
            producer.verify(SnapshotReader(self.root), run_id=self.run_id, deadline=self.deadline)
        if time.monotonic() >= operation_deadline:
            raise TimeoutError("citation original ToolAPI/callback retention exceeded its existing tool clock")
        return payload

    def read(self, path: Path) -> bytes:
        budget(self.deadline)
        snapshot = SnapshotReader(self.root).read(path.relative_to(self.root).as_posix())
        return snapshot.content


def tex_dependencies(runtime: CitationRuntime, fls: Path) -> tuple[dict[str, Any], ...]:
    """Every external INPUT from XeTeX's actual recorder, including fonts/styles."""
    external: dict[str, dict[str, Any]] = {}
    total = 0
    for line in runtime.read(fls).decode("utf-8").splitlines():
        budget(runtime.deadline)
        if not line.startswith("INPUT "):
            continue
        path = Path(line[6:])
        if not path.is_absolute():
            path = runtime.directory / path
        path = path.resolve(strict=True)
        if path.is_relative_to(runtime.directory):
            continue  # Generated aux/bbl are retained diagnostics, never reference inputs.
        if str(path) in external:
            continue
        row = file_observation(path)
        total += row["bytes"]
        if len(external) >= 10000 or total > 2 * 1024 * 1024 * 1024:
            raise ValueError("citation dependency inventory exceeds existing native runtime bounds")
        external[str(path)] = row
    if not external:
        raise ValueError("actual TeX recorder omitted external dependency observations")
    return tuple(external[key] for key in sorted(external))


def dependency_identity(
    rows: tuple[dict[str, Any], ...] | list[dict[str, Any]],
) -> list[list[Any]]:
    """Content identities survive relocation without reopening producer paths."""
    return sorted([[row["name"], row["sha256"], row["bytes"]] for row in rows])


def _backend_dependencies(runtime: CitationRuntime, transcript: str, phase: str) -> tuple[dict[str, Any], ...]:
    selected: set[Path] = set()
    opened = re.findall(r"kdebug:fopen\(([^,\n]+), r(?:b)?\) => (0x[0-9a-fA-F]+)", transcript)
    if not opened:
        raise ValueError("actual native backend omitted successful file-open observations")
    for name, pointer in opened:
        if int(pointer, 16) == 0:
            continue
        path = Path(name)
        path = (path if path.is_absolute() else runtime.directory / path).resolve(strict=True)
        if not path.is_relative_to(runtime.directory):
            selected.add(path)
    rows = tuple(file_observation(path) for path in sorted(selected, key=str))
    if not any(row["name"].endswith((".otf", ".ttf", ".pfb")) for row in rows):
        raise ValueError("actual native backend omitted font file custody")
    return rows


def compile_reference(runtime: CitationRuntime, tex: bytes) -> tuple[bytes, dict[str, Any]]:
    """Discover, then freshly compile under observed unchanged dependencies."""
    runtime.freeze("oracle.tex", tex)

    def compile_chain(phase: str) -> str:
        for number, name in enumerate(("xelatex", "bibtex", "xelatex", "xelatex"), 1):
            args = (
                [
                    "-fmt=xelatex",
                    "-progname=xelatex",
                    "-no-pdf",
                    "-recorder",
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    "-no-shell-escape",
                    "oracle.tex",
                ]
                if name == "xelatex"
                else ["oracle"]
            )
            runtime.tool(
                name,
                args,
                f"{phase}-{number:02d}-{name}",
                input_paths=(runtime.directory / "oracle.aux",) if name == "bibtex" else (),
                preserve_nominated_launcher=name == "xelatex",
            )
        backend = runtime.tool(
            "xdvipdfmx",
            ["--kpathsea-debug=4", "-vv", "-o", "oracle.pdf", "oracle.xdv"],
            f"{phase}-native-backend",
            input_paths=(runtime.directory / "oracle.xdv",),
        )
        return str(backend["stdout"]) + "\n" + str(backend["stderr"])

    discovery_backend = compile_chain("discovery")
    before_map = {
        row["path"]: row
        for row in (
            *tex_dependencies(runtime, runtime.directory / "oracle.fls"),
            *_backend_dependencies(runtime, discovery_backend, "discovery"),
        )
    }
    before = tuple(before_map[key] for key in sorted(before_map))
    # Include BibTeX's actual resolved style, absent from XeTeX's .fls.
    style = runtime.tool("kpsewhich", ["plainnat.bst"], "style-resolution")["stdout"].strip()
    if not style or "\n" in style:
        raise ValueError("actual plainnat style resolution is absent or ambiguous")
    style_before = file_observation(Path(style))
    blg = runtime.read(runtime.directory / "oracle.blg").decode("utf-8")
    if "The style file: plainnat.bst" not in blg:
        raise ValueError("actual BibTeX did not consume the admitted plainnat style")
    retained = []
    for number, row in enumerate((*before, style_before)):
        path = Path(row["path"])
        content = read_bytes_confined(path.parent, path, max_bytes=512 * 1024 * 1024)
        if hashlib.sha256(content).hexdigest() != row["sha256"]:
            raise ValueError("citation dependency changed before final reference admission")
        frozen = runtime.freeze(f"dependency-{number:06d}.input", content)
        retained.append(
            {
                **row,
                "artifact": {
                    "path": frozen.relative_to(runtime.root).as_posix(),
                    "sha256": row["sha256"],
                },
            }
        )
    # This stem is entirely observer-owned. Remove only generated discovery outputs.
    for suffix in ("aux", "bbl", "blg", "log", "out", "fls", "pdf", "xdv", "toc"):
        (runtime.directory / f"oracle.{suffix}").unlink(missing_ok=True)
    final_backend = compile_chain("reference")
    after_map = {
        row["path"]: row
        for row in (
            *tex_dependencies(runtime, runtime.directory / "oracle.fls"),
            *_backend_dependencies(runtime, final_backend, "reference"),
        )
    }
    after = tuple(after_map[key] for key in sorted(after_map))
    if before != after or style_before != file_observation(Path(style)):
        raise ValueError("citation dependency/font/style changed or final recorder inventory diverged")
    log = runtime.read(runtime.directory / "oracle.log").decode("utf-8")
    if "undefined" in log.lower() or "Citation(s) may have changed" in log or "Missing character" in log:
        raise ValueError("independent natbib reference retains undefined or unstable citations")
    runtime.unchanged()
    pdf = runtime.read(runtime.directory / "oracle.pdf")
    custody: dict[str, Any] = {
        "schema_version": DEPENDENCY_SCHEMA,
        "before": list(before),
        "after": list(after),
        "style_before": style_before,
        "style_after": file_observation(Path(style)),
        "dependency_identity": dependency_identity(before),
        "phase": "fresh-reference-after-discovery",
        "retained": retained,
        "diagnostic_outputs": {},
    }
    for suffix in ("tex", "aux", "bbl", "blg", "log", "fls", "pdf"):
        content = runtime.read(runtime.directory / f"oracle.{suffix}")
        custody["diagnostic_outputs"][suffix] = {
            "sha256": hashlib.sha256(content).hexdigest(),
            "bytes": len(content),
        }
    return pdf, custody
