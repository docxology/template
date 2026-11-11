"""Live parent admission of copied standalone HTML Python source execution.

A Source-owned parent capability prepares each actual launch and authenticates
its DIRECT process result. Serialized child plans and observations are DATA;
neither constructs a native/Source/provider authority or an original launch.
"""

from __future__ import annotations

import contextlib
import contextvars
import hashlib
import json
import math
import os
import stat
import sys
import tempfile
import time
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from infrastructure.core import bytecode_audit
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

PLAN_PATH_ENV = "TEMPLATE_HTML_CHILD_PLAN_PATH"
PLAN_HASH_ENV = "TEMPLATE_HTML_CHILD_PLAN_SHA256"
HOOK_SHA256 = "aa13244989c39811cf6174e8e51a7a85f8f7432bbe038d7e1dc79ced68085e88"
PLAN_SCHEMA = "template-source-html-python-child-plan-v1"
CLOSURE_SCHEMA = "template-source-html-python-child-closure-v1"
_TOKEN = object()
_CURRENT: contextvars.ContextVar[HTMLChildCustodian | None] = contextvars.ContextVar(
    "actual_html_child_custodian", default=None
)


def _clock(deadline: float) -> None:
    if type(deadline) not in (float, int) or not math.isfinite(deadline) or time.monotonic() >= deadline:
        raise TimeoutError("HTML Python Source custody exhausted its original caller deadline")


def _file(path: Path, deadline: float, maximum: int = 1024 * 1024) -> tuple[bytes, dict[str, Any]]:
    _clock(deadline)
    if path.is_symlink() or path != path.resolve(strict=True):
        raise ValueError("HTML child Source/plan must be an exact physical path")
    before = path.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_size > maximum:
        raise ValueError("HTML child Source/plan exceeds its finite regular-file bound")
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    after = path.stat()
    fields = (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    )
    if len(raw) > maximum or any(getattr(before, key) != getattr(after, key) for key in fields):
        raise ValueError("HTML child Source/plan changed during observation")
    _clock(deadline)
    return raw, {
        "path": str(path),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "identity": {key: getattr(after, key) for key in fields},
    }


def _live_sdk(deadline: float) -> tuple[Path, Path, dict[str, str]]:
    """Derive selected SDK from actual loaded package and preimport Code only."""
    _clock(deadline)
    package = sys.modules.get("infrastructure")
    filename = getattr(package, "__file__", None)
    registry = getattr(sys, "_template_executed_bytecode_audit", None)
    if not isinstance(filename, str) or not isinstance(registry, types.MappingProxyType):
        raise ValueError("HTML parent requires its actually preimport-audited SDK package")
    sdk = Path(filename).absolute().parents[1]
    hook = Path(bytecode_audit.__file__).absolute()
    if (
        hook != sdk / "infrastructure/core/bytecode_audit.py"
        or registry.get("hook_source_path") != str(hook)
        or registry.get("hook_source_sha256") != HOOK_SHA256
        or _file(hook, deadline)[1]["sha256"] != HOOK_SHA256
    ):
        raise ValueError("HTML parent cannot infer SDK/provider authority from RootDATA or a transport path")
    prefix = Path(registry["prefix"])
    bytecode_audit.verify_executed_source_code(sdk / "infrastructure", prefix)
    bytecode_audit.verify_executed_source_code(Path(__file__).absolute(), prefix)
    leaf = Path(__file__).absolute().parent
    sources = {
        name: _file(leaf / name, deadline)[1]["sha256"]
        for name in (
            "native_format_browser_driver.py",
            "native_format_browser_runtime.py",
            "native_format_html_platform_font_dom.py",
        )
    }
    _clock(deadline)
    return sdk, hook, sources


@dataclass(frozen=True)
class PreparedHTMLChild:
    """An actual parent's private capability, never constructed from JSON."""

    custodian: HTMLChildCustodian
    token: object
    command: tuple[str, ...]
    environment: dict[str, str]
    deadline: float
    plan: Path
    plan_hash: str
    closure: Path
    programs: dict[str, str]

    def authenticate(self, actual: dict[str, Any], *, caller_deadline: float) -> dict[str, Any]:
        """Consume the DIRECT trusted Source helper result after its real Popen."""
        if self.token is not _TOKEN or self.custodian.owner_pid != os.getpid():
            raise ValueError("HTML child custody capability belongs to a different actual parent")
        _clock(caller_deadline)
        self.custodian.close_source(caller_deadline)
        if (
            actual.get("owner_pid") != os.getpid()
            or type(actual.get("pid")) is not int
            or actual.get("original_deadline_monotonic") != self.deadline
            or tuple(actual.get("command", ())) != self.command
            or type(actual.get("original_exit_code")) is not int
            or actual.get("root_reaped") is None
            or not actual.get("accepted")
            or actual.get("timed_out")
            or actual.get("diagnostics")
        ):
            raise ValueError("HTML child did not match the actual originating process observation")
        stamps = [
            actual[key]["monotonic"]
            for key in (
                "operation_begin",
                "launch_begin",
                "launch_returned",
                "root_reaped",
                "operation_end",
            )
        ]
        cleanup = actual["cleanup"]
        if (
            any(type(value) not in (int, float) or not math.isfinite(value) for value in stamps)
            or stamps != sorted(stamps)
            or not stamps[-1] < self.deadline
            or type(cleanup.get("guardian_pid")) is not int
            or not cleanup.get("guardian_armed")
            or not cleanup.get("guardian_finished")
            or cleanup.get("guardian_original_exit_code") != 0
            or not cleanup.get("root_reaped")
            or cleanup.get("final_token_sweep_matched_pids") != []
        ):
            raise ValueError("HTML original child PID/guardian/raw operation did not close on the same clock")
        for channel in ("stdout", "stderr"):
            stream = actual["raw_" + channel]
            if _file(Path(stream["path"]), caller_deadline, 8 * 1024 * 1024)[1]["sha256"] != stream["sha256"]:
                raise ValueError("HTML original child binary stream changed")
        if _file(self.plan, caller_deadline)[1]["sha256"] != self.plan_hash:
            raise ValueError("actual parent's HTML child Source request changed")
        raw, binding = _file(self.closure, caller_deadline, 16 * 1024 * 1024)
        proof = json.loads(raw)
        if (
            proof.get("schema_version") != CLOSURE_SCHEMA
            or proof.get("pid") != actual["pid"]
            or proof.get("parent_pid") != os.getpid()
            or proof.get("plan_sha256") != self.plan_hash
            or proof.get("deadline_monotonic") != self.deadline
            or proof.get("program_sha256_before") != self.programs
            or proof.get("program_sha256_after") != self.programs
            or proof.get("audit_hook_sha256") != HOOK_SHA256
            or proof.get("python_executable_before") != proof.get("python_executable_after")
            or proof["python_executable_after"]["sha256"] != actual["executable_observation_after"]["sha256"]
            or not proof.get("executed_code_source_cache_closed")
            or proof.get("closing_errors") != []
            or type(proof.get("closed_at_monotonic")) not in (int, float)
            or not proof["closed_at_monotonic"] < self.deadline
        ):
            raise ValueError("HTML child actual Code/Source/cache/executable closure differs")
        if actual["original_exit_code"] == 0 and (
            proof.get("requested_program_return") != 0 or proof.get("original_exception") is not None
        ):
            raise ValueError("HTML Source program did not retain its genuine original successful outcome")
        physical = proof["python_executable_after"]["identity"]
        expected_identity = {
            "device": physical["st_dev"],
            "inode": physical["st_ino"],
            "mode": physical["st_mode"],
            "size": physical["st_size"],
            "mtime_ns": physical["st_mtime_ns"],
            "ctime_ns": physical["st_ctime_ns"],
            "links": physical["st_nlink"],
        }
        if (
            actual["executable_identity_before"] != expected_identity
            or actual["executable_identity_after"] != expected_identity
        ):
            raise ValueError("HTML child executable physical identity differs from actual Popen provider")
        declaration = json.loads(_file(self.plan, caller_deadline)[0])
        cache_root = Path(declaration["cache_prefix"])
        rows = proof["fresh_cache"]
        actual_paths = {path for path in cache_root.rglob("*") if path.is_file()}
        if len(rows) > 4096 or {Path(row["path"]) for row in rows} != actual_paths:
            raise ValueError("HTML child retained fresh Code cache inventory differs")
        total = 0
        for row in rows:
            path = Path(row["path"])
            if not path.is_relative_to(cache_root) or _file(path, caller_deadline, 16 * 1024 * 1024)[1] != row:
                raise ValueError("HTML child retained fresh Code cache bytes changed")
            total += row["bytes"]
        if total > 64 * 1024 * 1024:
            raise ValueError("HTML child retained Code cache exceeds original finite byte bound")
        graph_paths = [self.plan, self.closure, *(Path(row["path"]) for row in rows)]
        graph_paths.extend(Path(self.command[1]).with_name(name) for name in self.programs)
        graph_bindings = []
        for path in graph_paths:
            if not path.is_relative_to(self.custodian.artifact_root):
                raise ValueError("HTML retained child graph escapes its explicitly declared original artifact root")
            _, held = _file(path, caller_deadline, 16 * 1024 * 1024)
            graph_bindings.append(
                {
                    "path": path.relative_to(self.custodian.artifact_root).as_posix(),
                    "sha256": held["sha256"],
                    "bytes": held["bytes"],
                }
            )
        observation = {
            "closure": binding,
            "proof": proof,
            "actual_pid": actual["pid"],
            "actual_signed_os_exit": actual["original_exit_code"],
            "same_original_deadline_monotonic": self.deadline,
            "source_code_closed": True,
            "whole_python_or_kernel_runtime_admission": False,
            "retained_artifact_graph": {
                "schema_version": "template-original-html-child-relative-artifact-graph-v1",
                "original_root_label": str(self.custodian.artifact_root),
                "bindings": graph_bindings,
            },
        }
        self.custodian.register(self, observation)
        _clock(caller_deadline)
        return observation


class HTMLChildCustodian:
    """Live separately declared HTML control/producer domain with audited SDK."""

    def __init__(
        self,
        token: object,
        directory: Path,
        child_root: Path,
        deadline: float,
        artifact_root: Path,
    ) -> None:
        if token is not _TOKEN:
            raise ValueError("HTML child custodian must originate in its actual Source parent factory")
        self.owner_pid, self.deadline = os.getpid(), deadline
        self.sdk, self.hook, self.sources = _live_sdk(deadline)
        self.directory, self.child_root = directory.absolute(), child_root.absolute()
        self.artifact_root = artifact_root.absolute()
        if (
            self.artifact_root != self.artifact_root.resolve(strict=True)
            or not self.directory.is_relative_to(self.artifact_root)
            or not self.child_root.is_relative_to(self.artifact_root)
        ):
            raise ValueError("HTML evidence role does not confine both actual child and retained artifact roots")
        if (
            self.directory != self.directory.resolve(strict=True)
            or not self.directory.is_dir()
            or self.child_root != self.child_root.resolve()
            or self.directory.is_relative_to(self.sdk)
            or self.child_root.is_relative_to(self.sdk)
        ):
            raise ValueError("HTML child operation needs separate genuine output/fixture roles")
        self.prepared: list[PreparedHTMLChild] = []
        self.observed: dict[str, dict[str, Any]] = {}

    def close_source(self, deadline: float) -> None:
        sdk, hook, sources = _live_sdk(deadline)
        if self.owner_pid != os.getpid() or sdk != self.sdk or hook != self.hook or sources != self.sources:
            raise ValueError("HTML live originating SDK/Code/Source capability changed")

    def prepare(self, command: list[str], env: dict[str, str], deadline: float) -> PreparedHTMLChild:
        self.close_source(deadline)
        if deadline > self.deadline or Path(command[0]).resolve(strict=True) != Path(sys.executable).resolve(
            strict=True
        ):
            raise ValueError("HTML child changed its original parent clock/interpreter")
        driver = Path(command[1]).absolute()
        if not driver.is_relative_to(self.child_root) or driver != driver.resolve(strict=True):
            raise ValueError("HTML copied Source driver escapes its actual parent operation")
        programs = {
            driver.name: self.sources["native_format_browser_driver.py"],
            "native_format_browser_runtime.py": self.sources["native_format_browser_runtime.py"],
        }
        if "--platform-font-observer" in command:
            font = Path(command[command.index("--platform-font-observer") + 1]).absolute()
            if font != driver.with_name("native_format_html_platform_font_dom.py"):
                raise ValueError("HTML child replaced its actual Source-owned font sibling")
            programs[font.name] = self.sources[font.name]
        for name, expected in programs.items():
            if _file(driver.with_name(name), deadline)[1]["sha256"] != expected:
                raise ValueError("HTML parent copied a different selected SDK Source program")
        phase = Path(tempfile.mkdtemp(prefix="html-python-source-", dir=self.directory))
        cache = phase / "cache"
        cache.mkdir(mode=0o700)
        plan, closure = phase / "plan.json", phase / "closure.json"
        declaration = {
            "schema_version": PLAN_SCHEMA,
            "parent_pid": self.owner_pid,
            "selected_sdk_root": str(self.sdk),
            "hook_path": str(self.hook),
            "hook_sha256": HOOK_SHA256,
            "driver_path": str(driver),
            "programs": programs,
            "child_root": str(self.child_root),
            "deadline_monotonic": deadline,
            "cache_prefix": str(cache),
            "closure_path": str(closure),
        }
        with plan.open("x") as stream:
            stream.write(json.dumps(declaration, sort_keys=True) + "\n")
        plan_hash = _file(plan, deadline)[1]["sha256"]
        environment = dict(env)
        environment[PLAN_PATH_ENV], environment[PLAN_HASH_ENV] = str(plan), plan_hash
        selected = str(Path(command[0]).absolute())
        child = PreparedHTMLChild(
            self,
            _TOKEN,
            (selected, *command[1:]),
            environment,
            deadline,
            plan,
            plan_hash,
            closure,
            programs,
        )
        self.prepared.append(child)
        return child

    def register(self, child: PreparedHTMLChild, observation: dict[str, Any]) -> None:
        if child not in self.prepared or str(child.plan) in self.observed:
            raise ValueError("HTML live child registration is duplicated or foreign")
        self.observed[str(child.plan)] = observation

    def close(self) -> None:
        self.close_source(self.deadline)
        if len(self.prepared) != len(self.observed):
            raise ValueError("HTML original child execution has not been authenticated by its genuine parent")


@contextlib.contextmanager
def html_child_custodian(
    directory: Path,
    child_root: Path,
    *,
    deadline: float,
    artifact_root: Path | None = None,
) -> Iterator[HTMLChildCustodian]:
    if _CURRENT.get() is not None:
        raise ValueError("HTML actual child custodian cannot replace another live operation")
    owner = HTMLChildCustodian(_TOKEN, directory, child_root, deadline, artifact_root or directory)
    token = _CURRENT.set(owner)
    original: BaseException | None = None
    try:
        yield owner
    except BaseException as error:
        original = error
        raise
    finally:
        try:
            owner.close()
        except BaseException as error:
            if original is not None:
                original.add_note("HTML child Source closure " + type(error).__name__ + ": " + str(error))
            else:
                raise
        finally:
            _CURRENT.reset(token)


def prepare_html_child_launch(command: list[str], env: dict[str, str], deadline: float) -> PreparedHTMLChild | None:
    """Source ToolAPI entry: unrelated tools do not acquire HTML authority."""
    if len(command) < 2 or Path(command[1]).name not in (
        "browser-driver.py",
        "native_format_browser_driver.py",
    ):
        return None
    owner = _CURRENT.get()
    if owner is None:
        raise ValueError("copied HTML Python driver requires its genuine live Source custodian")
    return owner.prepare(command, env, deadline)


def validate_retained_html_child(
    artifact: dict[str, Any],
    result: dict[str, Any],
    programs: dict[str, str],
    reader: SnapshotReader,
    *,
    custody: dict[str, str],
    deadline: float,
) -> None:
    """Check DATA after the caller authenticated its actual original ToolAPI.

    The caller's live Source operation or independently owned completed native
    launch remains mandatory in `_tool`; this JSON check constructs neither.
    Original physical identities are compared within their own observation;
    relocated portable files are checked against their original byte bindings.
    """
    _clock(deadline)
    tool_snapshot = reader.read(artifact["path"])
    if tool_snapshot.sha256 != artifact["sha256"]:
        raise ValueError("authenticated original HTML ToolAPI bytes changed")
    tool = tool_snapshot.json_object()
    observation = tool.get("html_python_source_closure")
    if not isinstance(observation, dict) or tool.get("html_python_source_closure_error") is not None:
        raise ValueError("actual original HTML Python child lacks its Source custodian closure")
    proof = observation["proof"]
    original_root = Path(custody["root"])
    graph = observation.get("retained_artifact_graph")
    if (
        not isinstance(graph, dict)
        or graph.get("schema_version") != "template-original-html-child-relative-artifact-graph-v1"
        or graph.get("original_root_label") != str(original_root)
    ):
        raise ValueError("original HTML child has no confined relative Source/cache artifact graph")
    expected_paths = [Path(observation["closure"]["path"])]
    expected_paths.append(Path(observation["closure"]["path"]).parent / "plan.json")
    expected_paths.extend(Path(row["path"]) for row in proof["fresh_cache"])
    expected_paths.extend(Path(row["path"]) for row in proof["programs_after"].values())
    expected_relative = {path.relative_to(original_root).as_posix() for path in expected_paths}
    graph_rows = graph.get("bindings")
    if (
        not isinstance(graph_rows, list)
        or len(graph_rows) != len(expected_relative)
        or {row["path"] for row in graph_rows} != expected_relative
    ):
        raise ValueError("HTML child relative artifact graph omits or duplicates required plan/Source/cache bytes")
    for graph_row in graph_rows:
        held = reader.read(graph_row["path"])
        if held.sha256 != graph_row["sha256"] or len(held.content) != graph_row["bytes"]:
            raise ValueError("original HTML child relative retained bytes changed")
        if graph_row["path"] == (expected_paths[1].relative_to(original_root).as_posix()):
            if held.sha256 != proof["plan_sha256"]:
                raise ValueError("original HTML child retained plan differs from its actual executed request")
    closure_path = Path(observation["closure"]["path"])
    if not closure_path.is_relative_to(original_root):
        raise ValueError("HTML original child closure escapes its original evidence role")
    closure = reader.read(closure_path.relative_to(original_root).as_posix())
    expected_programs = dict(programs)
    expected_programs["browser-driver.py"] = expected_programs.pop("native_format_browser_driver.py")
    if (
        closure.sha256 != observation["closure"]["sha256"]
        or closure.json_object() != proof
        or proof["schema_version"] != CLOSURE_SCHEMA
        or proof["pid"] != tool["pid"]
        or proof["parent_pid"] != tool["owner_pid"]
        or proof["requested_program_return"] != 0
        or proof["original_exception"] is not None
        or proof["closing_errors"] != []
        or proof["deadline_monotonic"] != tool["original_deadline_monotonic"]
        or proof["closed_at_monotonic"] >= proof["deadline_monotonic"]
        or proof["program_sha256_before"] != expected_programs
        or proof["program_sha256_after"] != expected_programs
        or proof["programs_before"] != proof["programs_after"]
        or proof["audit_hook_sha256"] != HOOK_SHA256
        or proof["python_executable_before"] != proof["python_executable_after"]
        or proof["python_executable_after"]["sha256"] != tool["executable_sha256"]
        or not proof["executed_code_source_cache_closed"]
        or not observation["source_code_closed"]
        or observation["actual_signed_os_exit"] != 0
        or tool["original_exit_code"] != 0
        or result.get("python_source_request_sha256") != proof["plan_sha256"]
    ):
        raise ValueError("authenticated original copied HTML Code/Source/cache/process closure differs")
    total = 0
    if len(proof["fresh_cache"]) > 4096:
        raise ValueError("original HTML fresh cache exceeds finite inventory bound")
    for row in proof["fresh_cache"]:
        path = Path(row["path"])
        if not path.is_relative_to(closure_path.parent / "cache"):
            raise ValueError("original HTML Code cache escapes its original fresh prefix")
        cache = reader.read(path.relative_to(original_root).as_posix())
        if cache.sha256 != row["sha256"] or len(cache.content) != row["bytes"] or row["bytes"] > 16 * 1024 * 1024:
            raise ValueError("original retained HTML Code cache bytes differ")
        total += row["bytes"]
    if total > 64 * 1024 * 1024 or not reader.unchanged():
        raise ValueError("original HTML Code cache budget/evidence changed")
    _clock(deadline)
