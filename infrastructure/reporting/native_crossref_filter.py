"""Source-owned live Pandoc/filter handshake; portable records remain DATA."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import socket
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_crossref_exit_dispatch import (
    SourceFilterExitObserver,
    register_filter_exit,
    require_filter_exit_capability,
    validate_filter_kernel_exit,
)
from infrastructure.reporting.native_crossref_protocol import (
    peer_pid,
    process_birth,
    receive,
    send,
)
from infrastructure.reporting.native_format_acceptance_contracts import (
    create_private_native_directory,
)
from infrastructure.reporting.native_format_joint_source import source_environment
from infrastructure.reporting.native_pdf_citation_runtime import file_observation
from infrastructure.reporting.native_source_external_admission import (
    NativeSourceContext,
)
from infrastructure.reporting.native_source_provider_bootstrap import (
    format_selected_sdk_native_bootstrap,
)
from infrastructure.reporting.native_tool_process import NativeLiveToolProcess
from infrastructure.reporting.native_tool_producer import (
    current_native_producer_operation,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SCHEMA = "template-source-owned-crossref-filter-v3"
WORKER = "infrastructure.reporting.native_crossref_worker"
_KEY = object()
BLOCKERS = (
    "crossref actual loaded native-library closure requires independent admission",
    "crossref official Source-pinned archive to extracted executable body requires independent admission",
)


class SourceCrossrefFilter:
    """Prepared by the genuine live Source owner before its actual Pandoc launch."""

    def __init__(
        self,
        source: NativeSourceContext,
        reader: SnapshotReader,
        listener: socket.socket,
        declaration: dict[str, str],
        launcher: dict[str, str],
        *,
        deadline: float,
        key: object,
    ) -> None:
        if key is not _KEY:
            raise ValueError("filter custody requires the actual Source preparation factory")
        self.source, self.reader, self.listener = source, reader, listener
        self.declaration, self.launcher, self.deadline = declaration, launcher, deadline
        self.environment: dict[str, str] = {}
        self.owner = current_native_producer_operation()
        self.actual: dict[str, Any] | None = None
        self.pair_invocation: dict[str, Any] | None = None
        self.exit_observer: SourceFilterExitObserver | None = None
        self.verify()

    def close(self) -> None:
        if self.exit_observer is not None:
            self.exit_observer.close()

    def verify(self) -> None:
        remaining(self.deadline)
        if (
            self.owner is None
            or current_native_producer_operation() is not self.owner
            or self.owner.source is not self.source
        ):
            raise ValueError("filter preparation lost its genuine enclosing Source producer")
        self.owner.verify(self.reader, run_id=self.owner.run_id, deadline=self.owner.deadline)
        for binding in (self.declaration, self.launcher):
            if self.reader.read(binding["path"]).sha256 != binding["sha256"]:
                raise ValueError("filter actual prelaunch Source/request body changed")
        if self.pair_invocation is not None:
            for name in ("declaration", "launcher"):
                binding = self.pair_invocation[name]
                if self.reader.read(binding["path"]).sha256 != binding["sha256"]:
                    raise ValueError("filter immutable paired declaration/parent launcher changed")

    def observe(self, live: NativeLiveToolProcess) -> None:
        """Authenticate socket PID and kernel birth through the real live Popen."""
        self.verify()
        if type(live) is not NativeLiveToolProcess or self.actual is not None or not self.deadline <= live.deadline:
            raise ValueError("filter needs one actual finite live Pandoc operation")
        command = live.command
        launcher = self.launcher if self.pair_invocation is None else self.pair_invocation["launcher"]
        wrapper = str(self.reader.root / launcher["path"])
        if command.count(wrapper) != 1 or (
            command.index(wrapper) < 1 or command[command.index(wrapper) - 1] != "--filter"
        ):
            raise ValueError("actual Pandoc argv omitted its exact Source-selected filter wrapper")
        parent = process_birth(live.pid, deadline=self.deadline)
        self.listener.settimeout(remaining(self.deadline))
        connection, _ = self.listener.accept()
        with connection:
            pid = peer_pid(connection, deadline=self.deadline)
            child = process_birth(pid, deadline=self.deadline)
            if child["ppid"] != live.pid or receive(connection, deadline=self.deadline) != {
                "phase": "ready",
                "specification_sha256": self.declaration["sha256"],
            }:
                raise ValueError("filter kernel peer is not this actual Pandoc process's declared Source child")
            if self.pair_invocation is not None:
                from infrastructure.reporting.native_crossref_pair import validate_pair_leg

                pair = self.reader.read(self.pair_invocation["declaration"]["path"]).json_object()
                claim = self.reader.read(
                    pair["directory"] + "/invocation-" + str(self.pair_invocation["slot"]) + ".json"
                )
                self.pair_invocation["claim"] = {"path": claim.relative, "sha256": claim.sha256}
                if (
                    validate_pair_leg(
                        self.pair_invocation,
                        self.declaration,
                        self.launcher,
                        self.reader.read(self.declaration["path"]).json_object(),
                        child,
                        self.reader,
                    )
                    != wrapper
                ):
                    raise ValueError("actual paired Pandoc command differs from its kernel child claim")
            if (
                process_birth(live.pid, deadline=self.deadline) != parent
                or process_birth(pid, deadline=self.deadline) != child
            ):
                raise ValueError("filter parent/child birth changed before the original handshake")
            live.verify_live()
            observer = register_filter_exit(self.source, self.reader, live, connection, deadline=self.deadline)
            self.exit_observer = observer
            if observer.facts["parent"] != parent or observer.facts["child"] != child:
                raise ValueError("filter live kernel registration differs from its authenticated original handshake")
            observer.mark_admitted()
            send(
                connection,
                {"phase": "admitted", "parent": parent, "child": child},
                deadline=self.deadline,
            )
            completed = receive(connection, deadline=self.deadline)
            if set(completed) != {
                "phase",
                "specification_sha256",
                "observation",
                "source_exit_intent",
            } or (
                completed["phase"] != "sealed"
                or completed["specification_sha256"] != self.declaration["sha256"]
                or type(completed["source_exit_intent"]) is not int
                or completed["source_exit_intent"] != 0
            ):
                raise ValueError("filter side channel did not close with its exact original sealed outcome")
            observation = self.reader.read(completed["observation"]["path"])
            if observation.sha256 != completed["observation"]["sha256"]:
                raise ValueError("filter side-channel Source output seal differs from retained exact bytes")
            if (
                process_birth(live.pid, deadline=self.deadline) != parent
                or process_birth(pid, deadline=self.deadline) != child
            ):
                raise ValueError("filter actual parent/child birth changed before sealed output release")
            live.verify_live()
            self.actual = {
                "schema_version": SCHEMA,
                "specification": self.declaration,
                "launcher": self.launcher,
                "parent": parent,
                "child": child,
                "observation": completed["observation"],
                "source_exit_intent": 0,
            }
            if self.pair_invocation is not None:
                from infrastructure.reporting.native_crossref_pair import LEG_SCHEMA

                self.actual.update(schema_version=LEG_SCHEMA, pair_invocation=dict(self.pair_invocation))
            observer.mark_released()
            send(connection, {"phase": "release"}, deadline=self.deadline)
            try:
                self.actual["kernel_exit"] = observer.observe_exit()
            except BaseException:
                if observer.observation is not None:
                    self.actual["kernel_exit"] = observer.observation
                    self.verify()
                    specification = self.reader.read(self.declaration["path"]).json_object()
                    write_json(
                        self.reader.root,
                        self.reader.root / specification["directory"] / "kernel-exit-refused.json",
                        self.actual,
                    )
                    self.verify()
                raise
        self.verify()

    def finish(self, parent_tool: dict[str, str]) -> dict[str, str]:
        """Close direct original facts after the parent ToolAPI retains its OS exit."""
        from infrastructure.reporting.native_format_acceptance_validation import _file

        self.verify()
        if self.actual is None or self.owner is None or "kernel_exit" not in self.actual:
            raise ValueError("filter original child never completed its actual parent handshake")
        process = _file(parent_tool, self.reader).json_object()
        self.owner.validate_tool(parent_tool, process, self.reader, run_id=self.owner.run_id)
        if (
            process["pid"] != self.actual["parent"]["pid"]
            or process["original_exit_code"] != 0
            or process["exit_code"] != 0
        ):
            raise ValueError("filter original parent outcome differs from the actual live Pandoc owner")
        if self.pair_invocation is not None:
            from infrastructure.reporting.native_crossref_pair import validate_pair_parent_environment

            validate_pair_parent_environment(self.pair_invocation, process, self.reader)
        specification = _file(self.declaration, self.reader).json_object()
        validate_filter_kernel_exit(
            self.actual["kernel_exit"],
            parent=self.actual["parent"],
            child=self.actual["child"],
            observer_pid=specification["parent_owner_pid"],
            run_id=self.owner.run_id,
            original_deadline=self.deadline,
            caller_deadline=process["caller_deadline_monotonic"],
            original_completion=process["started_at_monotonic"] + process["duration_seconds"],
        )
        closure = self.reader.read(specification["directory"] + "/closure/receipt.json")
        if closure.json_object()["worker_outcome"] != {
            "kind": "raised",
            "class": "SystemExit",
            "module": "builtins",
            "system_exit_code": 0,
        }:
            raise ValueError("filter child lacks its actual selected-SDK terminal Code closure")
        from infrastructure.reporting.native_crossref_closure import validate_crossref_child_closure

        validate_crossref_child_closure(
            self.source,
            specification,
            {"path": closure.relative, "sha256": closure.sha256},
            self.reader,
            deadline=self.deadline,
        )
        result = {
            **self.actual,
            "parent_tool": parent_tool,
            "closure": {"path": closure.relative, "sha256": closure.sha256},
            "blockers": _file(self.actual["observation"], self.reader).json_object()["blockers"],
        }
        path = self.reader.root / specification["directory"] / "parent-observation.json"
        binding = write_json(self.reader.root, path, result)
        self.verify()
        return binding


@contextmanager
def prepare_source_crossref_filter(
    root: Path,
    directory: Path,
    scope: str,
    reader: SnapshotReader,
    *,
    env: dict[str, str],
    deadline: float,
    output_format: str,
) -> Iterator[SourceCrossrefFilter]:
    """Nominate current Source/SDK/wrapper before Pandoc consumes any filter JSON."""
    remaining(deadline)
    require_filter_exit_capability()
    if output_format not in {"latex", "html", "docx", "epub", "epub3", "json"}:
        raise ValueError("filter requires one exact Source-selected Pandoc output format")
    owner = current_native_producer_operation()
    if owner is None or reader.root != root.resolve() or owner.deadline < deadline:
        raise ValueError("filter preparation requires a genuine current Source/Pandoc owner and original clock")
    source = owner.source
    owner.verify(reader, run_id=owner.run_id, deadline=owner.deadline)
    create_private_native_directory(root, directory)
    selected = shutil.which("pandoc-crossref", path=env.get("PATH"))
    if selected is None:
        raise ValueError("filter lacks its independently nominated current crossref executable")
    crossref = file_observation(Path(selected).resolve(strict=True))
    official_archive = None
    if platform.system() == "Linux":
        from infrastructure.reporting.native_crossref_archive import _pin, PIN_SOURCE, observe_crossref_official_archive

        action = source.current_source_reader.read(PIN_SOURCE)
        host = {"system": platform.system(), "machine": platform.machine()}
        pin = _pin(action.content, host)
        archive_root = env.get("RUNNER_TEMP")
        if not archive_root or not Path(archive_root).is_absolute():
            raise ValueError("Source native Linux filter lacks the actual setup-action archive directory nomination")
        official_archive = observe_crossref_official_archive(
            source,
            directory / "official-archive",
            Path(archive_root) / "template-acceptance-document-archives" / pin["asset"],
            Path(crossref["path"]),
            reader,
            deadline=owner.deadline,
        )
    implementation_path = directory / "implementation.json"
    atomic_write_bytes_confined(
        root,
        implementation_path,
        source.bindings.expected_implementation_bytes,
        mode=0o600,
    )
    implementation = reader.read(implementation_path.relative_to(root).as_posix())
    runtime = json.loads(implementation.content)["runtime_environment"]
    python = runtime["python_executable"]
    if not isinstance(python, str) or any(character.isspace() for character in python):
        raise ValueError("filter requires an unambiguous admitted shebang interpreter nomination")
    closure = directory / "closure"
    create_private_native_directory(root, closure)
    identity = closure.stat()
    hook = source.current_source_reader.read("infrastructure/core/bytecode_audit.py").content
    if (
        json.loads(implementation.content)["files"]["infrastructure/core/bytecode_audit.py"]
        != hashlib.sha256(hook).hexdigest()
    ):
        raise ValueError("filter bytecode hook differs from independently admitted Source/SDK")
    # A short, exclusively owned socket path is required by Darwin's 104-byte ABI.
    with tempfile.TemporaryDirectory(prefix="template-crossref-") as socket_directory:
        endpoint = str(Path(socket_directory) / "peer.sock")
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            listener.bind(endpoint)
            os.chmod(endpoint, 0o600)
            listener.listen(1)
            specification = {
                "schema_version": SCHEMA,
                "scope": scope,
                "run_id": owner.run_id,
                "directory": directory.relative_to(root).as_posix(),
                "source": json.loads(source.descriptor(scope, deadline=deadline)),
                "implementation": {
                    "path": implementation.relative,
                    "sha256": implementation.sha256,
                },
                "parent_owner_pid": owner.owner_pid,
                "deadline_monotonic": deadline,
                "caller_deadline_monotonic": owner.deadline,
                "crossref": crossref,
                "official_archive": official_archive,
                "socket_address": endpoint,
                "closure_identity": [identity.st_dev, identity.st_ino],
                "expected_exit": 0,
                "output_format": output_format,
            }
            spec = write_json(root, directory / "specification.json", specification)
            bootstrap = format_selected_sdk_native_bootstrap(
                hook,
                source.bindings.selected_sdk_package_root,
                (),
                implementation_path,
                implementation.sha256,
                closure,
                (identity.st_dev, identity.st_ino),
                deadline,
                required_worker_module=WORKER,
            )
            argv = [
                "--root",
                str(root),
                "--specification",
                spec["path"],
                "--specification-sha256",
                spec["sha256"],
                "--implementation-sha256",
                implementation.sha256,
                "--deadline",
                repr(deadline),
                "--run-id",
                owner.run_id,
            ]
            script = (
                f"#!{python} -I\nimport sys\n"
                f"if sys.argv[1:]!={[output_format]!r}: raise ValueError('actual Pandoc filter format differs')\n"
                f"sys.argv={['native-crossref-worker', *argv]!r}\n" + bootstrap
            )
            launcher_path = directory / "source-crossref-filter"
            atomic_write_bytes_confined(root, launcher_path, script.encode(), mode=0o700)
            launch = reader.read(launcher_path.relative_to(root).as_posix())
            filter_owner = SourceCrossrefFilter(
                source,
                reader,
                listener,
                spec,
                {"path": launch.relative, "sha256": launch.sha256},
                deadline=deadline,
                key=_KEY,
            )
            # The actual process environment consumes Source admission labels only.
            filter_owner.environment = {**env, **source_environment(source)}
            try:
                yield filter_owner
                filter_owner.verify()
            finally:
                filter_owner.close()
        finally:
            listener.close()
