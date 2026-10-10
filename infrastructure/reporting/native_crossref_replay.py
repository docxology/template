"""Typed portable replay of a genuine externally held Pandoc filter child."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_crossref_filter import BLOCKERS, SCHEMA, WORKER
from infrastructure.reporting.native_crossref_worker import filter_json
from infrastructure.reporting.native_format_joint_source import require_native_operation
from infrastructure.reporting.native_source_external_admission import (
    NativeSourceContext,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

if TYPE_CHECKING:
    from infrastructure.reporting.native_stage_child_custody import NativeStageChildReaderOperation


class CrossrefFilterReaderOperation:
    """The external native operation authenticates parent facts before child DATA."""

    _renderer_binding: dict[str, str]
    _renderer_stage_owner: NativeStageChildReaderOperation
    _renderer_parent_tool: dict[str, str]
    _renderer_parent_qualification: dict[str, str] | None

    def __init__(
        self,
        source: NativeSourceContext,
        binding: dict[str, str],
        parent_reader: SnapshotReader,
        *,
        scope: str,
        run_id: str,
        deadline: float,
    ) -> None:
        operation = require_native_operation(parent_reader)
        if type(source) is not NativeSourceContext or operation.source is not source or deadline != operation.deadline:
            raise ValueError(
                "crossref reader requires its genuine current Source/native original custodian and same clock"
            )
        self.source, self.binding, self.parent_reader = source, binding, parent_reader
        self.scope, self.run_id, self.deadline = scope, run_id, deadline
        self._authority: dict[str, Any] | None = None
        self.verify()

    @classmethod
    def from_renderer_stage(
        cls,
        renderer_binding: dict[str, str],
        parent_reader: SnapshotReader,
        stage_owner: NativeStageChildReaderOperation,
    ) -> CrossrefFilterReaderOperation:
        """Admit only the actual renderer's causally retained observed child.

        Full parent qualification is owned by replay, once. Nested artifact
        authentication derives the child from these actual Source pointers and
        does not recursively replay its parent pair.
        """
        from infrastructure.reporting.native_format_acceptance_validation import _file
        from infrastructure.reporting.native_loader_qualification import SCHEMA as PAIR_SCHEMA, _FIELDS
        from infrastructure.reporting.native_stage_child_custody import NativeStageChildReaderOperation
        from infrastructure.reporting.native_stage_loader_replay import renderer_crossref_data

        if (
            cls is not CrossrefFilterReaderOperation
            or type(stage_owner) is not NativeStageChildReaderOperation
            or parent_reader.native_control_operation is not stage_owner
        ):
            raise ValueError("renderer Crossref admission needs the exact genuine fixed Stage reader")
        stage_owner.verify(parent_reader)
        authority = stage_owner.authenticate_artifact(
            renderer_binding,
            parent_reader,
            run_id=stage_owner.run_id,
            required_sdk_modules=("reporting/native_renderer_source_call.py", "reporting/native_crossref_filter.py"),
        )
        renderer = authority["event"].json_object()
        raw, _ = renderer_crossref_data(renderer, parent_reader)
        selected = raw["filter"]
        parent_tool = renderer["tool_artifacts"][-1]
        if (
            set(raw) != {"schema_version", "scope", "run_id", "filter", "parent_loader_qualification"}
            or raw["scope"] != stage_owner.scope
            or raw["run_id"] != stage_owner.run_id
        ):
            raise ValueError("renderer Crossref envelope changed its exact Source scope/run fields")
        qualification_binding = raw["parent_loader_qualification"]
        pair = _file(qualification_binding, parent_reader).json_object()
        if (
            set(pair) != _FIELDS
            or pair["schema_version"] != PAIR_SCHEMA
            or pair["run_id"] != stage_owner.run_id
            or pair["source_binding"]
            != [stage_owner.source.reference.commit, stage_owner.source.reference.source_identity]
            or not isinstance(pair["crossref_filters"], list)
            or len(pair["crossref_filters"]) != 2
            or pair["crossref_filters"][-1] != raw["filter"]
            or pair["observed_tool"] != parent_tool
        ):
            raise ValueError("renderer Crossref envelope replaced its genuine parent pair/observed child")
        selected = raw["filter"]
        leg = _file(selected, parent_reader).json_object()
        if leg["parent_tool"] != parent_tool:
            raise ValueError("renderer Crossref child does not belong to its actual final Pandoc parent")
        result = cls.__new__(cls)
        result.source, result.binding, result.parent_reader = stage_owner.source, selected, parent_reader
        result.scope, result.run_id, result.deadline = stage_owner.scope, stage_owner.run_id, stage_owner.deadline
        result._authority = None
        result._renderer_binding, result._renderer_stage_owner = renderer_binding, stage_owner
        result._renderer_parent_tool, result._renderer_parent_qualification = parent_tool, qualification_binding
        result.verify()
        return result

    @classmethod
    def from_renderer_pair_leg(
        cls, renderer_role: CrossrefFilterReaderOperation, binding: dict[str, str]
    ) -> CrossrefFilterReaderOperation:
        """Admit one exact baseline/observed slot from the same real renderer."""
        from infrastructure.reporting.native_crossref_pair import LEG_SCHEMA
        from infrastructure.reporting.native_format_acceptance_validation import _file

        if (
            cls is not CrossrefFilterReaderOperation
            or type(renderer_role) is not cls
            or getattr(renderer_role, "_renderer_stage_owner", None) is None
            or renderer_role._renderer_parent_qualification is None
        ):
            raise ValueError("renderer pair leg requires the exact genuine paired renderer role")
        renderer_role.verify()
        pair = _file(renderer_role._renderer_parent_qualification, renderer_role.parent_reader).json_object()
        filters = pair["crossref_filters"]
        if not isinstance(filters, list) or len(filters) != 2 or filters.count(binding) != 1:
            raise ValueError("renderer pair leg is not exactly one actual retained Source ordinal")
        slot = filters.index(binding)
        parent_tool = pair["baseline_tool" if slot == 0 else "observed_tool"]
        leg = _file(binding, renderer_role.parent_reader).json_object()
        renderer = _file(renderer_role._renderer_binding, renderer_role.parent_reader).json_object()
        if (
            leg["schema_version"] != LEG_SCHEMA
            or leg["parent_tool"] != parent_tool
            or leg["pair_invocation"]["slot"] != slot
            or parent_tool not in renderer["tool_artifacts"]
        ):
            raise ValueError("renderer pair leg changed its actual Source ordinal/retained Pandoc parent")
        result = cls.__new__(cls)
        result.source, result.binding, result.parent_reader = renderer_role.source, binding, renderer_role.parent_reader
        result.scope, result.run_id, result.deadline = renderer_role.scope, renderer_role.run_id, renderer_role.deadline
        result._authority = None
        result._renderer_binding, result._renderer_stage_owner = (
            renderer_role._renderer_binding,
            renderer_role._renderer_stage_owner,
        )
        result._renderer_parent_tool, result._renderer_parent_qualification = parent_tool, None
        result.verify()
        return result

    def verify(self) -> None:
        stage = getattr(self, "_renderer_stage_owner", None)
        if stage is not None:
            from infrastructure.reporting.native_stage_child_custody import NativeStageChildReaderOperation
            from infrastructure.reporting.native_stage_loader_replay import require_current_stage_reader

            if (
                type(stage) is not NativeStageChildReaderOperation
                or stage.source is not self.source
                or stage.scope != self.scope
                or stage.run_id != self.run_id
                or stage.deadline != self.deadline
                or self.parent_reader.native_control_operation is not stage
            ):
                raise ValueError("renderer Crossref changed its genuine Stage Source/run/clock")
            stage.verify(self.parent_reader)
            if self.parent_reader.native_operation is None:
                require_current_stage_reader(self.parent_reader, stage)
            else:
                operation = require_native_operation(self.parent_reader)
                if operation.source is not self.source or operation.deadline != self.deadline:
                    raise ValueError("renderer Crossref changed its actual external Original Source/clock")
            remaining(self.deadline)
            return
        operation = require_native_operation(self.parent_reader)
        if operation.source is not self.source or operation.deadline != self.deadline:
            raise ValueError("crossref reader changed its actual external Source/original operation")
        control = self.parent_reader.native_control_operation
        if control is not None:
            from infrastructure.reporting.native_stage_child_custody import NativeStageChildReaderOperation
            from infrastructure.reporting.native_print_child_custody import (
                BasicBrowserControlReaderOperation,
                OfficeScientificControlReaderOperation,
                PrintControlReaderOperation,
                SemanticBrowserControlReaderOperation,
                SlideControlReaderOperation,
                WholePDFControlReaderOperation,
            )

            if (
                type(control)
                not in (
                    BasicBrowserControlReaderOperation,
                    OfficeScientificControlReaderOperation,
                    PrintControlReaderOperation,
                    SemanticBrowserControlReaderOperation,
                    SlideControlReaderOperation,
                    WholePDFControlReaderOperation,
                    NativeStageChildReaderOperation,
                )
                or control.source is not self.source
            ):
                raise ValueError("crossref parent requires one exact Source-owned original child custodian")
            control.verify(self.parent_reader)
        remaining(self.deadline)

    def _child(self) -> dict[str, Any]:
        from infrastructure.reporting.native_format_acceptance_validation import _file
        from infrastructure.reporting.native_tool_replay import (
            authenticate_original_native_artifact,
            validate_native_tool_data,
        )
        from infrastructure.reporting.native_crossref_closure import validate_crossref_child_closure

        self.verify()
        # Exact graph membership comes from a live external NativeOriginalLaunch.
        stage = getattr(self, "_renderer_stage_owner", None)
        renderer_authority = None
        if stage is not None:
            renderer_authority = authenticate_original_native_artifact(
                self._renderer_binding,
                self.parent_reader,
                run_id=self.run_id,
                required_sdk_modules=(
                    "reporting/native_renderer_source_call.py",
                    "reporting/native_crossref_filter.py",
                    "reporting/native_crossref_exit.py",
                    "reporting/native_crossref_exit_dispatch.py",
                    "reporting/native_crossref_linux_exit.py",
                    "reporting/native_crossref_linux_abi.py",
                    "reporting/native_tool_process.py",
                ),
            )
            selected = _file(self.binding, self.parent_reader)
            if selected.json_object()["parent_tool"] != self._renderer_parent_tool:
                raise ValueError("renderer Crossref leg changed its causally authenticated Pandoc parent")
            authority = {**renderer_authority, "event": selected}
        else:
            authority = authenticate_original_native_artifact(
                self.binding,
                self.parent_reader,
                run_id=self.run_id,
                required_sdk_modules=(
                    "reporting/native_crossref_filter.py",
                    "reporting/native_crossref_exit.py",
                    "reporting/native_crossref_exit_dispatch.py",
                    "reporting/native_crossref_linux_exit.py",
                    "reporting/native_crossref_linux_abi.py",
                    "reporting/native_tool_process.py",
                ),
            )
        raw = authority["event"].json_object()
        from infrastructure.reporting.native_crossref_pair import LEG_SCHEMA, PARENT_SCHEMA, validate_pair_leg

        if raw.get("schema_version") == PARENT_SCHEMA:
            from infrastructure.reporting.native_loader_qualification import replay_native_loader_qualification

            if (
                set(raw) != {"schema_version", "scope", "run_id", "filter", "parent_loader_qualification"}
                or raw["scope"] != self.scope
                or raw["run_id"] != self.run_id
            ):
                raise ValueError("paired Crossref envelope differs from its genuine scope/run/fieldset")
            qualification = replay_native_loader_qualification(
                raw["parent_loader_qualification"], self.parent_reader, run_id=self.run_id
            )
            if qualification["crossref_filters"] is None or qualification["crossref_filters"][-1] != raw["filter"]:
                raise ValueError("paired parent qualification does not retain this actual observed filter")
            authority = authenticate_original_native_artifact(
                raw["filter"],
                self.parent_reader,
                run_id=self.run_id,
                required_sdk_modules=(
                    "reporting/native_crossref_pair.py",
                    "reporting/native_crossref_filter.py",
                    "reporting/native_tool_process.py",
                ),
            )
            raw = authority["event"].json_object()

        paired = raw.get("schema_version") == LEG_SCHEMA
        if (
            set(raw)
            != {
                "schema_version",
                "specification",
                "launcher",
                "parent",
                "child",
                "observation",
                "source_exit_intent",
                "kernel_exit",
                "parent_tool",
                "closure",
                "blockers",
            }
            | ({"pair_invocation"} if paired else set())
            or raw["schema_version"] not in {SCHEMA, LEG_SCHEMA}
            or raw["blockers"] not in ([], list(BLOCKERS))
        ):
            raise ValueError("crossref retained original parent observation fieldset differs")
        if paired and stage is not None:
            authenticate_original_native_artifact(
                self._renderer_binding,
                self.parent_reader,
                run_id=self.run_id,
                required_sdk_modules=("reporting/native_crossref_pair.py", "reporting/native_crossref_filter.py"),
            )
        elif paired:
            authenticate_original_native_artifact(
                self.binding,
                self.parent_reader,
                run_id=self.run_id,
                required_sdk_modules=("reporting/native_crossref_pair.py", "reporting/native_crossref_filter.py"),
            )
        specification = _file(raw["specification"], self.parent_reader)
        spec = specification.json_object()
        fields = {
            "schema_version",
            "scope",
            "run_id",
            "directory",
            "source",
            "implementation",
            "parent_owner_pid",
            "deadline_monotonic",
            "caller_deadline_monotonic",
            "crossref",
            "official_archive",
            "socket_address",
            "closure_identity",
            "expected_exit",
            "output_format",
        }
        parent_tool = _file(raw["parent_tool"], self.parent_reader).json_object()
        parent_authority = authenticate_original_native_artifact(
            raw["parent_tool"],
            self.parent_reader,
            run_id=self.run_id,
            required_sdk_modules=(
                "reporting/native_crossref_filter.py",
                "reporting/native_crossref_exit.py",
                "reporting/native_crossref_exit_dispatch.py",
                "reporting/native_crossref_linux_exit.py",
                "reporting/native_crossref_linux_abi.py",
                "reporting/native_tool_process.py",
            ),
        )
        if parent_authority["event"].json_object() != parent_tool:
            raise ValueError("crossref parent ToolAPI is absent from the actual original native graph")
        validate_native_tool_data(
            parent_tool,
            self.parent_reader,
            original_deadline=authority["original"].original_deadline,
            original_completion=authority["original"].observed_completion,
        )
        if paired:
            from infrastructure.reporting.native_crossref_pair import validate_pair_parent_environment

            validate_pair_parent_environment(raw["pair_invocation"], parent_tool, self.parent_reader)
        if (
            set(spec) != fields
            or spec["schema_version"] != SCHEMA
            or spec["scope"] != self.scope
            or (
                spec["run_id"] != self.run_id
                or spec["source"] != authority["source"]
                or spec["parent_owner_pid"] != authority["process"]["pid"]
                or spec["expected_exit"] != 0
                or type(raw["source_exit_intent"]) is not int
                or raw["source_exit_intent"] != 0
                or parent_tool["tool"] != "pandoc"
                or parent_tool["run_id"] != self.run_id
                or parent_tool["original_exit_code"] != 0
                or parent_tool["exit_code"] != 0
                or not spec["deadline_monotonic"] <= parent_tool["original_deadline_monotonic"]
                or spec["caller_deadline_monotonic"] != parent_tool["caller_deadline_monotonic"]
            )
        ):
            raise ValueError("crossref child role/source/run/original Pandoc process/clock differs")
        leaf = Path(spec["directory"])
        launcher = _file(raw["launcher"], self.parent_reader)
        implementation = _file(spec["implementation"], self.parent_reader)
        if (
            specification.relative != (leaf / "specification.json").as_posix()
            or launcher.relative != (leaf / "source-crossref-filter").as_posix()
        ):
            raise ValueError("crossref exact specification/launcher belongs to a different original attempt")
        from infrastructure.reporting.native_source_provider_bootstrap import (
            format_selected_sdk_native_bootstrap,
        )

        original_root = Path(spec["source"]["current_mirror"]["root"])
        sdk = Path(spec["source"]["selected_sdk"]["package_root"])
        original_directory = original_root / leaf
        bootstrap = format_selected_sdk_native_bootstrap(
            self.source.current_source_reader.read("infrastructure/core/bytecode_audit.py").content,
            sdk,
            (),
            original_root / spec["implementation"]["path"],
            implementation.sha256,
            original_directory / "closure",
            tuple(spec["closure_identity"]),
            spec["deadline_monotonic"],
            required_worker_module=WORKER,
        )
        python = implementation.json_object()["runtime_environment"]["python_executable"]
        argv = [
            "--root",
            str(original_root),
            "--specification",
            specification.relative,
            "--specification-sha256",
            specification.sha256,
            "--implementation-sha256",
            implementation.sha256,
            "--deadline",
            repr(spec["deadline_monotonic"]),
            "--run-id",
            self.run_id,
        ]
        script = (
            f"#!{python} -I\nimport sys\n"
            f"if sys.argv[1:]!={[spec['output_format']]!r}: raise ValueError('actual Pandoc filter format differs')\n"
            f"sys.argv={['native-crossref-worker', *argv]!r}\n" + bootstrap
        )
        original_launcher = str(original_root / launcher.relative)
        if paired:
            original_launcher = validate_pair_leg(
                raw["pair_invocation"],
                raw["specification"],
                raw["launcher"],
                spec,
                raw["child"],
                self.parent_reader,
            )
        command = parent_tool["command"]
        if (
            launcher.content != script.encode()
            or command.count(original_launcher) != 1
            or (command.index(original_launcher) < 1 or command[command.index(original_launcher) - 1] != "--filter")
        ):
            raise ValueError(
                "crossref actual Pandoc launch differs from independently reconstructed Source/SDK wrapper bytes"
            )
        parent, child = raw["parent"], raw["child"]
        for birth in (parent, child):
            if (
                not isinstance(birth, dict)
                or set(birth) != {"pid", "ppid", "uid", "birth", "platform"}
                or (
                    type(birth["pid"]) is not int
                    or birth["pid"] <= 0
                    or type(birth["ppid"]) is not int
                    or type(birth["uid"]) is not int
                    or not isinstance(birth["birth"], list)
                    or len(birth["birth"]) != (2 if birth["platform"] == "Darwin" else 1)
                    or any(type(value) is not int or value < 0 for value in birth["birth"])
                    or birth["platform"] not in {"Linux", "Darwin"}
                    or not any(birth["birth"])
                )
            ):
                raise ValueError("crossref original kernel birth labels are invalid")
        if (
            parent["pid"] != parent_tool["pid"]
            or parent["ppid"] != spec["parent_owner_pid"]
            or (
                child["ppid"] != parent["pid"]
                or child["pid"] in {parent["pid"], spec["parent_owner_pid"]}
                or child["uid"] != parent["uid"]
                or child["platform"] != parent["platform"]
            )
        ):
            raise ValueError("crossref original kernel parent/child relation differs")
        from infrastructure.reporting.native_crossref_exit_dispatch import validate_filter_kernel_exit

        validate_filter_kernel_exit(
            raw["kernel_exit"],
            parent=parent,
            child=child,
            observer_pid=spec["parent_owner_pid"],
            run_id=self.run_id,
            original_deadline=spec["deadline_monotonic"],
            caller_deadline=spec["caller_deadline_monotonic"],
            original_completion=authority["original"].observed_completion,
        )
        observation = _file(raw["observation"], self.parent_reader)
        payload = observation.json_object()
        if (
            observation.relative != (leaf / "filter-observation.json").as_posix()
            or payload["schema_version"] != SCHEMA
            or (
                payload["parent"] != parent
                or payload["child"] != child
                or payload["specification_sha256"] != specification.sha256
                or type(payload["source_exit_intent"]) is not int
                or payload["source_exit_intent"] != 0
                or payload["run_id"] != self.run_id
                or payload["output_format"] != spec["output_format"]
                or payload["blockers"] != raw["blockers"]
            )
        ):
            raise ValueError("crossref sealed child observation belongs to a different actual original")
        closed = validate_crossref_child_closure(
            self.source, spec, raw["closure"], self.parent_reader, deadline=self.deadline
        )
        # No original executable/font/provider path is opened in a portable reader.
        actual = {
            **authority,
            "process": {"pid": child["pid"]},
            "closure": closed,
            "source": spec["source"],
            "specification": spec,
            "child_observation": payload,
        }
        if renderer_authority is not None:
            actual["renderer_stage_specification"] = renderer_authority["specification"]
            actual["renderer_parent_observation"] = raw
        self.verify()
        return actual

    def authenticate_artifact(
        self,
        binding: dict[str, Any],
        reader: SnapshotReader,
        *,
        run_id: str,
        required_sdk_modules: tuple[str, ...],
    ) -> dict[str, Any]:
        from infrastructure.reporting.native_format_acceptance_validation import _file

        if run_id != self.run_id or reader.root != self.parent_reader.root:
            raise ValueError("crossref nested original tool differs from the held external current reader/run")
        authority = self._child()
        selected = _file(binding, reader)
        payload = authority["child_observation"]
        if binding not in payload["tool_artifacts"]:
            raise ValueError("crossref tool is absent from the actual sealed child observation")
        sdk = Path(authority["source"]["selected_sdk"]["package_root"])
        executed = {row["source_path"] for row in authority["closure"]["executions"] if row["runs"]}
        if not {str(sdk / name) for name in required_sdk_modules} <= executed:
            raise ValueError("crossref original tool lacks actual admitted child SDK helper execution")
        # The child ToolAPI must finish before its real Pandoc parent completion.
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class Completion:
            original_deadline: float
            observed_completion: float

        original = authority["original"]
        return {
            **authority,
            "event": selected,
            "original": Completion(
                authority["specification"]["deadline_monotonic"],
                original.observed_completion,
            ),
        }

    def replay(self) -> dict[str, Any]:
        """Authenticate actual nested OS outcomes, then independently inspect JSON."""
        from infrastructure.reporting.native_format_acceptance_validation import (
            _file,
            _tool,
        )

        parent_qualification = None
        stage: NativeStageChildReaderOperation | None = getattr(self, "_renderer_stage_owner", None)
        selected_pair = getattr(self, "_renderer_parent_qualification", None)
        if selected_pair is not None:
            from infrastructure.reporting.native_stage_loader_replay import replay_stage_loader_qualification

            if stage is None:
                raise ValueError("paired renderer qualification requires its genuine Stage owner")

            parent_qualification = replay_stage_loader_qualification(
                selected_pair, self.parent_reader, stage_owner=stage, renderer_binding=self._renderer_binding
            )
        authority = self._child()
        spec, payload = authority["specification"], authority["child_observation"]
        if not isinstance(payload, dict):
            raise ValueError("crossref original child observation is not an exact object")
        if (
            set(payload)
            != {
                "schema_version",
                "run_id",
                "specification_sha256",
                "parent",
                "child",
                "input",
                "output",
                "tool_artifacts",
                "official_archive",
                "loader_qualifications",
                "source_exit_intent",
                "version",
                "output_format",
                "blockers",
            }
            or payload["official_archive"] != spec["official_archive"]
            or len(payload["tool_artifacts"]) != (6 if payload["loader_qualifications"] is not None else 2)
        ):
            raise ValueError("crossref actual original tool/input/output cohort differs")
        reader = SnapshotReader(
            self.parent_reader.root,
            native_operation=self.parent_reader.native_operation,
            native_producer_operation=self.parent_reader.native_producer_operation,
            native_control_operation=self,
        )
        version = _tool(
            payload["tool_artifacts"][3 if payload["loader_qualifications"] is not None else 0],
            reader,
            self.run_id,
            "pandoc-crossref",
            "crossref-filter-version",
            ["--version"],
        )
        process = _tool(
            payload["tool_artifacts"][5 if payload["loader_qualifications"] is not None else 1],
            reader,
            self.run_id,
            "pandoc-crossref",
            "crossref-filter-json",
            [spec["output_format"]],
        )
        if any(
            row["executable"] != spec["crossref"]["path"] or row["executable_sha256"] != spec["crossref"]["sha256"]
            for row in (version, process)
        ):
            raise ValueError("actual crossref original binary differs from its exact Source prelaunch nomination")
        stdin, stdout = (
            _file(payload["input"], reader),
            _file(payload["output"], reader),
        )
        raw_stdout = _file(
            {
                "path": process["raw_stdout"]["path"],
                "sha256": process["raw_stdout"]["sha256"],
            },
            reader,
        )
        if (
            stdin.content != _file(process["consumed_input_artifacts"][0]["artifact"], reader).content
            or stdout.content != raw_stdout.content
        ):
            raise ValueError("crossref stdin/output differs from actual original consumed/returned raw bytes")
        if (
            filter_json(stdin.content)["pandoc-api-version"] != filter_json(stdout.content)["pandoc-api-version"]
            or payload["version"] != version["stdout"]
        ):
            raise ValueError("crossref original complete JSON API/version interpretation differs")
        qualifications = payload["loader_qualifications"]
        if stage is not None and reader.native_operation is None:
            from infrastructure.reporting.native_stage_loader_replay import require_current_stage_reader
            import platform

            require_current_stage_reader(reader, stage)
            host = {"system": platform.system(), "machine": platform.machine()}
            if authority["renderer_stage_specification"]["parent_platform"] != host["system"]:
                raise ValueError("Crossref actual Current host differs from its genuine fixed Stage parent")
        else:
            original = require_native_operation(reader).originals[self.scope]
            host = reader.read(original.process_relative).json_object()["host_before"]
        if host["system"] == "Linux":
            from infrastructure.reporting.native_loader_qualification import replay_native_loader_qualification
            from infrastructure.reporting.native_crossref_archive import replay_crossref_official_archive

            if not isinstance(qualifications, list) or len(qualifications) != 2 or payload["blockers"]:
                raise ValueError("Source Linux Crossref lacks its two real loader/archive obligations")
            for index, qualification in enumerate(qualifications):
                if stage is not None:
                    from infrastructure.reporting.native_stage_loader_replay import replay_stage_loader_qualification

                    pair = replay_stage_loader_qualification(qualification, reader, stage_owner=stage)
                else:
                    pair = replay_native_loader_qualification(qualification, reader, run_id=self.run_id)
                if pair["observed_tool"] != payload["tool_artifacts"][3 + index * 2]:
                    raise ValueError("Crossref loader pair differs from the actually consumed binary invocation")
                if pair["baseline_tool"] != payload["tool_artifacts"][2 + index * 2]:
                    raise ValueError("Crossref loader pair differs from its exact actual baseline invocation")
            if stage is not None:
                from infrastructure.reporting.native_stage_crossref_archive_replay import (
                    replay_stage_crossref_official_archive,
                )

                replay_stage_crossref_official_archive(
                    self, spec["official_archive"], payload["tool_artifacts"][5], reader
                )
            else:
                replay_crossref_official_archive(
                    self.source,
                    spec["official_archive"],
                    payload["tool_artifacts"][5],
                    self.parent_reader,
                    tool_reader=reader,
                    scope=self.scope,
                    run_id=self.run_id,
                    deadline=self.deadline,
                )
        elif (
            qualifications is not None or spec["official_archive"] is not None or payload["blockers"] != list(BLOCKERS)
        ):
            raise ValueError("unsupported consuming host cannot claim Linux loader/archive qualification")
        self.verify()
        if parent_qualification is not None:
            return {**payload, "parent_loader_qualification": parent_qualification}
        return payload
