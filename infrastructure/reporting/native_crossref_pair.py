"""Exactly two real filter children behind one immutable Source-selected launcher."""

from __future__ import annotations

import os
from contextlib import ExitStack, contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_crossref_filter import SourceCrossrefFilter, prepare_source_crossref_filter
from infrastructure.reporting.native_format_acceptance_contracts import create_private_native_directory
from infrastructure.reporting.native_environment_custody import loader_environment_injections, value_commitment
from infrastructure.reporting.native_loader_build import CompiledNativeLoader
from infrastructure.reporting.native_loader_observation import NativeLoaderObservation
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

if TYPE_CHECKING:
    from infrastructure.reporting.native_tool_process import NativeLiveToolProcess

SCHEMA = "template-source-crossref-two-invocation-declaration-v1"
LEG_SCHEMA = "template-source-owned-crossref-paired-filter-leg-v1"
PARENT_SCHEMA = "template-source-crossref-paired-parent-v1"
_KEY = object()


def pair_launcher(root: Path, declaration: dict[str, Any], python: str, output_format: str) -> bytes:
    """Reconstruct the fixed launcher; no producer-supplied executable code."""
    slots = [(str(root / item["launcher"]["path"]), item["launcher"]["sha256"]) for item in declaration["slots"]]
    directory = str(root / declaration["directory"])
    injections = declaration["parent_loader"]["environment_injections"]
    return (
        f"#!{python} -I\nimport hashlib,json,os,stat,sys,time\n"
        f"if sys.argv[1:]!={[output_format]!r}: raise ValueError('actual paired filter format differs')\n"
        f"deadline={declaration['deadline_monotonic']!r}\n"
        "if time.monotonic()>=deadline: raise TimeoutError('paired filter original clock exhausted')\n"
        f"directory={directory!r}\n"
        "if os.path.realpath(directory)!=directory: raise ValueError('paired filter directory changed')\n"
        "directory_fd=os.open(directory,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)\n"
        "try:\n"
        " for slot in range(2):\n"
        "  try: claim_fd=os.open('invocation-'+str(slot)+'.json',"
        "os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=directory_fd)\n"
        "  except FileExistsError: continue\n"
        "  break\n"
        " else: raise ValueError('Source paired filter permits exactly two invocations')\n"
        " try:\n"
        "  claim=json.dumps({'slot':slot,'pid':os.getpid(),'ppid':os.getppid(),'uid':os.getuid()},"
        "sort_keys=True).encode()+b'\\n'\n"
        "  with os.fdopen(claim_fd,'wb',closefd=True) as stream: "
        "stream.write(claim);stream.flush();os.fsync(stream.fileno())\n"
        " except BaseException: raise\n"
        "finally: os.close(directory_fd)\n"
        f"injections={injections!r}\n"
        "selected=injections if slot==1 else {}\n"
        "present={key for key in os.environ if key in injections or key=='LD_PRELOAD' "
        "or key.startswith('DYLD_') or key.startswith('TEMPLATE_LOADER_')}\n"
        "if present!=set(selected): raise ValueError('paired filter inherited an unadmitted parent audit overlay')\n"
        "if any(hashlib.sha256(os.environ[key].encode('utf-8')).hexdigest()!=value "
        "for key,value in selected.items()): "
        "raise ValueError('paired filter inherited a changed parent audit injection')\n"
        "for key in selected: os.environ.pop(key)\n"
        f"slots={slots!r}\n"
        "path,expected=slots[slot]\n"
        "with os.fdopen(os.open(path,os.O_RDONLY|os.O_NOFOLLOW),'rb') as stream:\n"
        " before=os.fstat(stream.fileno())\n"
        " if not stat.S_ISREG(before.st_mode) or not 0<before.st_size<=8*1024*1024: "
        "raise ValueError('paired filter launcher is not a bounded regular Source body')\n"
        " body=stream.read(8*1024*1024+1)\n"
        " after=os.fstat(stream.fileno())\n"
        " identity=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_nlink)\n"
        " if identity(after)!=identity(before) or len(body)!=before.st_size or "
        "hashlib.sha256(body).hexdigest()!=expected: "
        "raise ValueError('paired filter selected Source launcher changed')\n"
        "if time.monotonic()>=deadline: raise TimeoutError('paired filter admission exhausted original clock')\n"
        "exec(compile(body,path,'exec'),{'__name__':'__main__','__file__':path})\n"
    ).encode()


def validate_pair_leg(
    value: dict[str, Any],
    specification: dict[str, str],
    launcher: dict[str, str],
    spec: dict[str, Any],
    child: dict[str, Any],
    reader: SnapshotReader,
) -> str:
    """A DATA predicate; its caller must authenticate the actual parent/child."""
    from infrastructure.reporting.native_format_acceptance_validation import _file

    if set(value) != {"declaration", "launcher", "slot", "claim"} or type(value["slot"]) is not int:
        raise ValueError("paired filter invocation lacks its exact fixed fieldset/ordinal")
    slot = value["slot"]
    if slot not in (0, 1):
        raise ValueError("paired filter ordinal is outside the exactly-two Source roster")
    declaration = _file(value["declaration"], reader)
    pair = declaration.json_object()
    fields = {
        "schema_version",
        "scope",
        "run_id",
        "directory",
        "source_binding",
        "owner_pid",
        "deadline_monotonic",
        "slots",
        "parent_loader",
    }
    source_binding = [spec["source"]["original_source"]["commit"], spec["source"]["original_source"]["source_identity"]]
    # The Source descriptor owns these names; do not infer a Source capability from them.
    if (
        set(pair) != fields
        or pair["schema_version"] != SCHEMA
        or pair["scope"] != spec["scope"]
        or pair["run_id"] != spec["run_id"]
        or pair["source_binding"] != source_binding
        or pair["owner_pid"] != spec["parent_owner_pid"]
        or pair["deadline_monotonic"] != spec["deadline_monotonic"]
        or not isinstance(pair["slots"], list)
        or len(pair["slots"]) != 2
        or pair["slots"][slot] != {"specification": specification, "launcher": launcher}
    ):
        raise ValueError("paired filter declaration differs from its actual Source/owner/clock/slot")
    loader = pair["parent_loader"]
    if not isinstance(loader, dict) or set(loader) != {
        "compiler",
        "purpose",
        "owner_pid",
        "deadline_monotonic",
        "environment_injections",
    }:
        raise ValueError("paired filter lacks its exact concrete parent loader selection")
    if loader["owner_pid"] != pair["owner_pid"] or loader["deadline_monotonic"] != pair["deadline_monotonic"]:
        raise ValueError("paired parent loader changed its genuine Source owner/original clock")
    from infrastructure.reporting.native_loader_observation import ENV_KEYS

    injections = loader["environment_injections"]
    if not isinstance(injections, dict) or set(injections) != ENV_KEYS - {"LD_PRELOAD"}:
        raise ValueError("paired parent loader lacks its exact five injection commitments")
    directory = Path(pair["directory"])
    if (
        directory.is_absolute()
        or ".." in directory.parts
        or declaration.relative != (directory / "invocations.json").as_posix()
    ):
        raise ValueError("paired filter declaration escapes its original private directory")
    for index, item in enumerate(pair["slots"]):
        if not isinstance(item, dict) or set(item) != {"specification", "launcher"}:
            raise ValueError("paired filter slot lacks its exact Source members")
        nominated_spec = _file(item["specification"], reader).json_object()
        leaf = directory / ("slot-" + str(index))
        if (
            item["specification"]["path"] != (leaf / "specification.json").as_posix()
            or item["launcher"]["path"] != (leaf / "source-crossref-filter").as_posix()
            or nominated_spec["directory"] != leaf.as_posix()
            or any(
                nominated_spec[key] != spec[key]
                for key in (
                    "schema_version",
                    "scope",
                    "run_id",
                    "source",
                    "parent_owner_pid",
                    "deadline_monotonic",
                    "caller_deadline_monotonic",
                    "crossref",
                    "expected_exit",
                    "output_format",
                )
            )
        ):
            raise ValueError("paired filter changed the complete two-slot Source selection")
    implementation = _file(spec["implementation"], reader).json_object()
    python = implementation["runtime_environment"]["python_executable"]
    original_root = Path(spec["source"]["current_mirror"]["root"])
    parent_launcher = _file(value["launcher"], reader)
    if parent_launcher.relative != (
        directory / "source-crossref-pair"
    ).as_posix() or parent_launcher.content != pair_launcher(original_root, pair, python, spec["output_format"]):
        raise ValueError("paired parent launcher differs from independently reconstructed Source bytes")
    claim = _file(value["claim"], reader)
    if claim.relative != (directory / ("invocation-" + str(slot) + ".json")).as_posix() or claim.json_object() != {
        "slot": slot,
        "pid": child["pid"],
        "ppid": child["ppid"],
        "uid": child["uid"],
    }:
        raise ValueError("paired launcher claim is not this actual authenticated kernel child")
    return str(original_root / parent_launcher.relative)


def _parent_loader_selection(loader: NativeLoaderObservation) -> dict[str, Any]:
    return {
        "compiler": loader.compiled.binding,
        "purpose": loader.purpose,
        "owner_pid": loader.owner_pid,
        "deadline_monotonic": loader.deadline,
        "environment_injections": {
            key: value_commitment(value) for key, value in loader_environment_injections(loader).items()
        },
    }


def validate_pair_parent_environment(
    value: dict[str, Any], parent_tool: dict[str, Any], reader: SnapshotReader
) -> None:
    """Link the checked child handoff to its separately authenticated actual parent."""
    from infrastructure.reporting.native_format_acceptance_validation import _file

    pair = _file(value["declaration"], reader).json_object()
    selected = pair["parent_loader"]
    native = _file(parent_tool["native_process_artifact"], reader).json_object()
    expected = None if value["slot"] == 0 else selected["environment_injections"]
    if native["environment_custody"]["loader_injections"] != expected:
        raise ValueError("paired child handoff differs from its actual parent's committed Popen environment")
    if value["slot"] == 0:
        if native.get("loader_lifecycle") is not None:
            raise ValueError("paired baseline inherited an unselected parent loader")
    else:
        lifecycle = _file(native["loader_lifecycle"], reader).json_object()
        if any(
            lifecycle[key] != selected[label]
            for key, label in (
                ("compiler", "compiler"),
                ("purpose", "purpose"),
                ("owner_pid", "owner_pid"),
                ("original_deadline_monotonic", "deadline_monotonic"),
                ("environment_injections", "environment_injections"),
            )
        ):
            raise ValueError("paired child handoff changed its actual observed parent loader owner/clock/compiler")


def parent_observation(binding: dict[str, str], reader: SnapshotReader) -> dict[str, Any]:
    """Read the retained observed leg; this DATA helper grants no authority."""
    from infrastructure.reporting.native_format_acceptance_validation import _file

    raw = _file(binding, reader).json_object()
    if raw.get("schema_version") == PARENT_SCHEMA:
        if set(raw) != {"schema_version", "scope", "run_id", "filter", "parent_loader_qualification"}:
            raise ValueError("paired Crossref parent envelope fieldset differs")
        return _file(raw["filter"], reader).json_object()
    return raw


def parent_launcher_binding(raw: dict[str, Any]) -> dict[str, str]:
    """Select the exact retained parent operand after the enclosing replay."""
    binding: dict[str, str] = raw["launcher"] if "pair_invocation" not in raw else raw["pair_invocation"]["launcher"]
    return binding


class SourceCrossrefPair:
    """Two existing genuine filter owners; this object never mints a ToolAPI."""

    def __init__(
        self,
        filters: tuple[SourceCrossrefFilter, SourceCrossrefFilter],
        reader: SnapshotReader,
        declaration: dict[str, str],
        launcher: dict[str, str],
        *,
        key: object,
        parent_loader: NativeLoaderObservation,
    ) -> None:
        if key is not _KEY:
            raise ValueError("paired filter requires its actual Source preparation")
        self.filters, self.reader = filters, reader
        self.declaration, self.launcher = declaration, launcher
        self.parent_loader = parent_loader
        self.owner = current_native_producer_operation()
        self.deadline = filters[0].deadline
        self.environment = dict(filters[0].environment)
        self.completed: list[dict[str, str]] = []
        self.verify()

    def verify(self) -> None:
        remaining(self.deadline)
        if (
            self.owner is None
            or current_native_producer_operation() is not self.owner
            or self.owner.owner_pid != os.getpid()
        ):
            raise ValueError("paired filter lost its genuine live Source owner")
        self.owner.verify(self.reader, run_id=self.owner.run_id, deadline=self.owner.deadline)
        if any(
            item.owner is not self.owner or item.deadline != self.deadline or item.environment != self.environment
            for item in self.filters
        ):
            raise ValueError("paired filters changed their actual Source owner/clock/selected environment")
        for binding in (self.declaration, self.launcher):
            if self.reader.read(binding["path"]).sha256 != binding["sha256"]:
                raise ValueError("paired filter immutable declaration/launcher changed")
        if (
            type(self.parent_loader) is not NativeLoaderObservation
            or self.parent_loader.compiled.owner is not self.owner
        ):
            raise ValueError("paired filter lost its concrete Source parent loader")
        self.parent_loader.compiled.verify(deadline=self.deadline)
        loader = self.reader.read(self.declaration["path"]).json_object()["parent_loader"]
        if loader != _parent_loader_selection(self.parent_loader):
            raise ValueError("paired filter changed its exact Source-selected parent audit overlay")
        for item in self.filters:
            item.verify()

    def observe(self, slot: int, live: NativeLiveToolProcess) -> None:
        self.verify()
        if slot != len(self.completed) or slot not in (0, 1):
            raise ValueError("paired filter requires exactly two sequential actual native invocations")
        self.filters[slot].observe(live)

    def finish(self, slot: int, parent_tool: dict[str, str]) -> None:
        self.verify()
        if slot != len(self.completed) or slot not in (0, 1):
            raise ValueError("paired filter cannot repeat or substitute a completed actual parent")
        self.completed.append(self.filters[slot].finish(parent_tool))
        self.verify()


@contextmanager
def prepare_source_crossref_pair(
    root: Path,
    directory: Path,
    scope: str,
    reader: SnapshotReader,
    *,
    env: dict[str, str],
    deadline: float,
    output_format: str,
    compiled: CompiledNativeLoader,
    purpose: str,
) -> Iterator[SourceCrossrefPair]:
    """Prepare both genuine child slots before either actual parent Popen."""
    owner = current_native_producer_operation()
    if owner is None:
        raise ValueError("paired filter preparation requires the actual Source producer")
    owner.verify(reader, run_id=owner.run_id, deadline=owner.deadline)
    create_private_native_directory(root, directory)
    with ExitStack() as stack:
        compiled.verify(deadline=deadline)
        leaf = compiled.directory / ("callbacks-" + purpose)
        create_private_native_directory(root, leaf)
        observer = NativeLoaderObservation(compiled, leaf, purpose=purpose, deadline=deadline)
        stack.callback(observer.socket_directory.cleanup)
        stack.callback(observer.abort)
        filters = tuple(
            stack.enter_context(
                prepare_source_crossref_filter(
                    root,
                    directory / ("slot-" + str(index)),
                    scope,
                    reader,
                    env=env,
                    deadline=deadline,
                    output_format=output_format,
                )
            )
            for index in range(2)
        )
        if len(filters) != 2:
            raise ValueError("Source paired filter lacks its complete fixed roster")
        declaration_data = {
            "schema_version": SCHEMA,
            "scope": scope,
            "run_id": owner.run_id,
            "directory": directory.relative_to(root).as_posix(),
            "source_binding": [owner.source.reference.commit, owner.source.reference.source_identity],
            "owner_pid": owner.owner_pid,
            "deadline_monotonic": deadline,
            "slots": [{"specification": item.declaration, "launcher": item.launcher} for item in filters],
            "parent_loader": _parent_loader_selection(observer),
        }
        declaration = write_json(root, directory / "invocations.json", declaration_data)
        implementation = reader.read(filters[0].declaration["path"]).json_object()["implementation"]
        python = reader.read(implementation["path"]).json_object()["runtime_environment"]["python_executable"]
        launcher_path = directory / "source-crossref-pair"
        atomic_write_bytes_confined(
            root, launcher_path, pair_launcher(root, declaration_data, python, output_format), mode=0o700
        )
        observed = reader.read(launcher_path.relative_to(root).as_posix())
        launcher = {"path": observed.relative, "sha256": observed.sha256}
        for slot, item in enumerate(filters):
            item.pair_invocation = {"declaration": declaration, "launcher": launcher, "slot": slot}
        pair = SourceCrossrefPair(
            (filters[0], filters[1]), reader, declaration, launcher, key=_KEY, parent_loader=observer
        )
        yield pair
        pair.verify()
        if len(pair.completed) != 2:
            raise ValueError("Source paired filter did not complete exactly two genuine parent/child invocations")
