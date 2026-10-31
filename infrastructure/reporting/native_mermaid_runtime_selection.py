"""Source-pinned npm Mermaid selection under a genuine live Source owner.

The parent and worker independently nominate actual paths. Frozen JSON records
these selections and complete byte inventories; it never creates a custodian.
"""

from __future__ import annotations

from infrastructure.reporting.native_worker_startup_diagnostics import (
    _worker_execution_entry,
    _worker_execution_phase,
)

import base64
import hashlib
import re
import stat
from dataclasses import dataclass
from contextlib import contextmanager
from contextvars import ContextVar
from collections.abc import Iterator
from pathlib import Path, PurePosixPath
from typing import Any

from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.native_format_acceptance_checks import native_tool_record
from infrastructure.reporting.native_mermaid_runtime_custody import (
    MAX_BYTES,
    MAX_FILES,
    _budget,
    _file,
)
from infrastructure.reporting.native_format_browser_runtime import observe_runtime, validate_runtime
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.native_tool_producer import NativeProducerOperation, current_native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader, json_object_from_bytes

SCHEMA = "template-native-source11-npm-mermaid-runtime-v2"
SELECTION_SCHEMA = "template-native-source11-mermaid-selection-v1"
CLI_NAME = "@mermaid-js/mermaid-cli"
CLI_VERSION = "11.16.0"
CLI_RELATIVE = "@mermaid-js/mermaid-cli"
_SEAL = object()


@dataclass(frozen=True)
class NativeMermaidSelection:
    """Independent controller/worker nomination, never inferred from receipts."""

    package_root: Path
    dependency_root: Path
    node_executable: Path
    chrome_executable: Path

    def __post_init__(self) -> None:
        for value in (self.package_root, self.dependency_root, self.node_executable, self.chrome_executable):
            if not isinstance(value, Path) or not value.is_absolute() or ".." in value.parts:
                raise ValueError("Mermaid nomination requires four explicit absolute paths")

    def spec_data(self) -> dict[str, str]:
        return {
            "schema_version": SELECTION_SCHEMA,
            "package_root_path": str(self.package_root),
            "dependency_root_path": str(self.dependency_root),
            "node_executable_path": str(self.node_executable),
            "chrome_executable_path": str(self.chrome_executable),
        }


def _source_json(source: NativeSourceContext, relative: str, deadline: float) -> dict[str, Any]:
    _budget(deadline)
    original = source.reference.read(relative)
    current = source.current_source_reader.read(relative)
    if current.content != original or len(original) > 4 * 1024 * 1024:
        raise ValueError("Mermaid source npm input changed or exceeds its existing bounded input size")
    json_object_from_bytes(original)
    return {"sha256": hashlib.sha256(original).hexdigest(), "bytes": len(original), "utf8": original.decode("utf-8")}


def _source_inputs(source: NativeSourceContext, deadline: float) -> dict[str, Any]:
    return {name: _source_json(source, name, deadline) for name in ("package.json", "package-lock.json")}


def _validate_source_inputs(inputs: object) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(inputs, dict) or set(inputs) != {"package.json", "package-lock.json"}:
        raise ValueError("Mermaid source package/lock byte bindings differ")
    parsed = []
    for name in ("package.json", "package-lock.json"):
        item = inputs[name]
        if not isinstance(item, dict) or set(item) != {"sha256", "bytes", "utf8"} or not isinstance(item["utf8"], str):
            raise ValueError("Mermaid source npm bytes are not literal bound data")
        raw = item["utf8"].encode("utf-8")
        if type(item["bytes"]) is not int or not len(raw) == item["bytes"] <= 4 * 1024 * 1024:
            raise ValueError("Mermaid source npm byte length differs/unbounded")
        if hashlib.sha256(raw).hexdigest() != item["sha256"]:
            raise ValueError("Mermaid source npm byte digest differs")
        parsed.append(json_object_from_bytes(raw))
    package, lock = parsed
    if package.get("devDependencies", {}).get(CLI_NAME) != CLI_VERSION:
        raise ValueError("Source does not declare this exact Mermaid11 profile")
    packages = lock.get("packages")
    if lock.get("lockfileVersion") != 3 or not isinstance(packages, dict) or not 1 < len(packages) <= MAX_FILES:
        raise ValueError("Source npm lock lacks its finite complete v3 package map")
    if packages.get("", {}).get("devDependencies") != package.get("devDependencies"):
        raise ValueError("Source npm package and locked direct dependency declarations differ")
    if package.get("engines") != {"node": "24.x"} or packages.get("", {}).get("engines") != package["engines"]:
        raise ValueError("Source npm package and locked Root Node24 engine declarations differ")
    cli = packages.get("node_modules/" + CLI_RELATIVE, {})
    if cli.get("version") != CLI_VERSION or cli.get("engines", {}).get("node") != "^18.19 || >=20.0":
        raise ValueError("Source Mermaid lock differs from the exact Source-pinned Mermaid11 package profile")
    for relative, row in packages.items():
        if relative == "":
            continue
        path = PurePosixPath(relative)
        if (
            not isinstance(row, dict)
            or path.is_absolute()
            or ".." in path.parts
            or path.as_posix() != relative
            or not relative.startswith("node_modules/")
            or row.get("link")
            or not isinstance(row.get("version"), str)
            or not isinstance(row.get("resolved"), str)
            or not row["resolved"].startswith("https://registry.npmjs.org/")
        ):
            raise ValueError("Source npm dependency resolution is not a literal locked registry package")
        integrity = row.get("integrity")
        if not isinstance(integrity, str) or not integrity.startswith("sha512-"):
            raise ValueError("Source npm dependency lacks an exact SHA512 distribution integrity")
        try:
            digest = base64.b64decode(integrity[7:], validate=True)
        except ValueError as error:
            raise ValueError("Source npm distribution integrity is malformed") from error
        if len(digest) != 64:
            raise ValueError("Source npm distribution integrity length differs")
    return package, lock


def _inventory(root: Path, deadline: float) -> dict[str, Any]:
    """Admit every installed dependency byte and confined alias, within old caps."""
    if root.absolute() != root.resolve(strict=True) or not stat.S_ISDIR(root.lstat().st_mode):
        raise ValueError("Source Mermaid dependency root must be an actual unaliased directory")
    identity = (root.stat().st_dev, root.stat().st_ino)
    rows: list[dict[str, Any]] = []
    total = 0
    for path in sorted(root.rglob("*")):
        _budget(deadline)
        info = path.lstat()
        if stat.S_ISDIR(info.st_mode):
            continue
        if len(rows) >= MAX_FILES:
            raise ValueError("Source Mermaid complete npm dependency member bound exceeded")
        relative = path.relative_to(root).as_posix()
        if stat.S_ISLNK(info.st_mode):
            target = path.resolve(strict=True)
            if not target.is_relative_to(root):
                raise ValueError("Source Mermaid dependency alias escapes its explicit full npm root")
            rows.append({"path": relative, "kind": "alias", "target": target.relative_to(root).as_posix()})
        elif stat.S_ISREG(info.st_mode):
            observed = _file(path, deadline=deadline)
            total += observed["bytes"]
            if total > MAX_BYTES:
                raise ValueError("Source Mermaid complete npm dependency byte bound exceeded")
            rows.append({"path": relative, "kind": "file", **observed})
        else:
            raise ValueError("Source Mermaid npm closure contains an unsupported filesystem node")
    if identity != (root.stat().st_dev, root.stat().st_ino):
        raise ValueError("Source Mermaid npm dependency root was physically replaced")
    result = {"members": rows, "bytes": total}
    return {**result, "content_digest": canonical_digest(result)}


def _installation(root: Path, lock: dict[str, Any], deadline: float) -> dict[str, Any]:
    _budget(deadline)
    hidden_path = root / ".package-lock.json"
    metadata = root.stat()
    hidden_bytes = read_bytes_confined(
        root,
        hidden_path,
        max_bytes=4 * 1024 * 1024,
        expected_root_identity=(metadata.st_dev, metadata.st_ino),
    )
    _budget(deadline)
    hidden = json_object_from_bytes(hidden_bytes)
    packages = hidden.get("packages")
    if hidden.get("lockfileVersion") != 3 or not isinstance(packages, dict) or not 0 < len(packages) <= MAX_FILES:
        raise ValueError("Source Mermaid npm installation lacks its finite complete installed package map")
    originals = lock["packages"]
    manifests = []
    for relative, row in packages.items():
        _budget(deadline)
        if relative not in originals or row != originals[relative] or relative == "":
            raise ValueError("installed npm package differs from its exact Source version/resolution/integrity")
        suffix = PurePosixPath(relative).relative_to("node_modules")
        manifest = root / suffix / "package.json"
        if manifest.is_symlink() or manifest.stat().st_size > 1024 * 1024:
            raise ValueError("installed Source npm package manifest is absent/unbounded/aliased")
        raw = json_object_from_bytes(manifest.read_bytes())
        name = suffix.parts[-1]
        if len(suffix.parts) >= 2 and suffix.parts[-2].startswith("@"):
            name = "/".join(suffix.parts[-2:])
        if raw.get("name") != name or raw.get("version") != row["version"]:
            raise ValueError("actual installed npm manifest differs from its locked package name/version")
        manifests.append({"path": manifest.relative_to(root).as_posix(), **_file(manifest, deadline=deadline)})
    declared_roots = {root / PurePosixPath(relative).relative_to("node_modules") for relative in packages}
    resolver_roots = {
        root,
        *(package / "node_modules" for package in declared_roots if (package / "node_modules").exists()),
    }
    for resolver_root in sorted(resolver_roots):
        for entry in resolver_root.iterdir():
            _budget(deadline)
            if entry.name == ".package-lock.json" and resolver_root == root:
                continue
            if entry.name == ".bin":
                if not entry.is_dir() or entry.is_symlink():
                    raise ValueError("Source npm CLI alias directory is not an actual confined directory")
                continue
            candidates = tuple(entry.iterdir()) if entry.name.startswith("@") and entry.is_dir() else (entry,)
            for candidate in candidates:
                if candidate not in declared_roots or candidate.is_symlink() or not candidate.is_dir():
                    raise ValueError("Source npm dependency resolver can select an undeclared package or root member")
    missing = []
    for relative, row in originals.items():
        if relative and relative not in packages:
            if row.get("optional") is not True:
                raise ValueError("installed npm closure omits a required Source-locked package")
            missing.append(relative)
    cli = json_object_from_bytes((root / CLI_RELATIVE / "package.json").read_bytes())
    if (
        cli.get("name") != CLI_NAME
        or cli.get("version") != CLI_VERSION
        or cli.get("exports", {}).get(".", {}).get("default") != "./src/index.js"
        or cli.get("engines", {}).get("node") != "^18.19 || >=20.0"
        or cli.get("bin") != {"mmdc": "./src/cli.js"}
    ):
        raise ValueError("actual installed Mermaid11 API/CLI/Node declaration differs")
    result = {
        "hidden_lock": {"sha256": hashlib.sha256(hidden_bytes).hexdigest(), "bytes": len(hidden_bytes)},
        "locked_installed_packages": packages,
        "package_manifests": manifests,
        "missing_optional_packages": sorted(missing),
    }
    return {**result, "content_digest": canonical_digest(result)}


def _observe(selection: NativeMermaidSelection, source: NativeSourceContext, deadline: float) -> dict[str, Any]:
    inputs = _source_inputs(source, deadline)
    _, lock = _validate_source_inputs(inputs)
    package = selection.package_root.resolve(strict=True)
    dependency = selection.dependency_root.resolve(strict=True)
    if (
        selection.dependency_root != dependency
        or selection.package_root != package
        or package != dependency / CLI_RELATIVE
    ):
        raise ValueError("Source11 Mermaid package is not the exact explicitly nominated npm dependency member")
    node = selection.node_executable.resolve(strict=True)
    chrome = selection.chrome_executable.resolve(strict=True)
    result = {
        "schema_version": SCHEMA,
        "package_root_label": str(package),
        "dependency_root_label": str(dependency),
        "node_executable_label": str(node),
        "package_name": CLI_NAME,
        "version": CLI_VERSION,
        "cli_member": CLI_RELATIVE + "/src/cli.js",
        "source_npm_inputs": inputs,
        "installation": _installation(dependency, lock, deadline),
        "dependency_tree": _inventory(dependency, deadline),
        "node": _file(node, deadline=deadline),
        "chrome": observe_runtime(chrome, deadline=deadline),
    }
    observed = {**result, "content_digest": canonical_digest(result)}
    validate_source_mermaid_runtime(observed)
    return observed


@dataclass(frozen=True)
class NativeMermaidRuntimeAdmission:
    """A genuine current Source/npm/process admission held outside spec DATA."""

    selection: NativeMermaidSelection
    source: NativeSourceContext
    producer: NativeProducerOperation
    runtime: dict[str, Any]
    node_version_artifact: dict[str, str]
    deadline: float
    _seal: object

    def __post_init__(self) -> None:
        if self._seal is not _SEAL:
            raise ValueError("Mermaid runtime admission requires its actual Source-owned factory")

    def observe(self, *, deadline: float) -> dict[str, Any]:
        if not deadline <= self.deadline or current_native_producer_operation() is not self.producer:
            raise ValueError("Mermaid runtime admission lost its genuine Source owner or original clock")
        reader = SnapshotReader(self.source.bindings.current_root, native_producer_operation=self.producer)
        with self.producer._verification_guard(reader, run_id=self.source.bindings.run_id, deadline=deadline):
            observed = reader.read(self.node_version_artifact["path"])
            self.producer._validate_tool_data(
                self.node_version_artifact, observed.json_object(), reader, run_id=self.source.bindings.run_id
            )
            current = _observe(self.selection, self.source, deadline)
            if current != self.runtime or not reader.unchanged():
                raise ValueError("Source-pinned npm/Node/Chrome runtime changed after genuine admission")
        return current

    def admit_node_version_process(self, record: dict[str, Any]) -> None:
        """Admit only the actual retained generic ToolAPI Node24 invocation."""
        reader = SnapshotReader(self.source.bindings.current_root, native_producer_operation=self.producer)
        self.producer.verify(reader, run_id=self.source.bindings.run_id, deadline=self.deadline)
        snapshot = reader.read(self.node_version_artifact["path"])
        if snapshot.sha256 != self.node_version_artifact["sha256"] or snapshot.json_object() != record:
            raise ValueError("Source11 Node24 process differs from its actual original invocation")
        self.producer.validate_tool(self.node_version_artifact, record, reader, run_id=self.source.bindings.run_id)
        if not reader.unchanged():
            raise ValueError("Source11 original Node24 process custody changed")

    def node_version_proof(self) -> dict[str, Any]:
        reader = SnapshotReader(self.source.bindings.current_root, native_producer_operation=self.producer)
        snapshot = reader.read(self.node_version_artifact["path"])
        record = snapshot.json_object()
        self.admit_node_version_process(record)
        return {"artifact": dict(self.node_version_artifact), "process": record}

    def spec_data(self) -> dict[str, str]:
        return {**self.selection.spec_data(), "runtime_content_digest": self.runtime["content_digest"]}


def admit_source_mermaid_selection(
    selection: NativeMermaidSelection,
    source: NativeSourceContext,
    *,
    deadline: float,
    directory: Path,
    env: dict[str, str],
) -> NativeMermaidRuntimeAdmission:
    """Admit Source11 plus actual Node24 using registered original ToolAPI facts."""
    producer = current_native_producer_operation()
    if not isinstance(selection, NativeMermaidSelection) or not isinstance(source, NativeSourceContext):
        raise ValueError("Mermaid selection requires independently held nominations and genuine Source")
    if producer is None or producer.source is not source:
        raise ValueError("Mermaid selection lacks its actual currently active Source producer")
    if env.get("NODE_OPTIONS") or env.get("NODE_PATH"):
        raise ValueError("Source Mermaid cannot admit environment-supplied JavaScript/module overrides")
    root = source.bindings.current_root
    if not directory.absolute().is_relative_to(root):
        raise ValueError("Mermaid version proof must be retained beneath the actual Source operation root")
    reader = SnapshotReader(root, native_producer_operation=producer)
    with _worker_execution_phase("mermaid-producer-verify"):
        producer.verify(reader, run_id=source.bindings.run_id, deadline=deadline)
    with _worker_execution_phase("mermaid-observe-before"):
        before = _observe(selection, source, deadline)
    with _worker_execution_phase("mermaid-tool-api"):
        proof = native_tool_record(
            root,
            directory,
            str(selection.node_executable),
            ["--version"],
            env=env,
            deadline=deadline,
            run_id=source.bindings.run_id,
            purpose="source-mermaid-node-version",
        )
    with _worker_execution_phase("mermaid-post-node"):
        with _worker_execution_entry(
            "mermaid-post-node-guard",
            producer._verification_guard(reader, run_id=source.bindings.run_id, deadline=deadline),
        ):
            with _worker_execution_phase("mermaid-post-node-data"):
                snapshot = reader.read(proof["artifact"]["path"])
                raw = snapshot.json_object()
                producer._validate_tool_data(proof["artifact"], raw, reader, run_id=source.bindings.run_id)
                if (
                    raw["executable"] != before["node_executable_label"]
                    or raw["executable_sha256"] != before["node"]["sha256"]
                    or raw["command"] != [before["node_executable_label"], "--version"]
                    or raw["original_exit_code"] != 0
                    or raw["exit_code"] != 0
                    or not re.fullmatch(r"v24\.[0-9]+\.[0-9]+\n?", raw["stdout"])
                    or raw["stderr"]
                ):
                    raise ValueError(
                        "actual Source-nominated Node process is not the genuine successful Node24 profile"
                    )
            with _worker_execution_phase("mermaid-observe-after"):
                after = _observe(selection, source, deadline)
            with _worker_execution_phase("mermaid-post-node-unchanged"):
                if before != after or not reader.unchanged():
                    raise ValueError("Source Mermaid runtime changed during actual Node24 process admission")
    return NativeMermaidRuntimeAdmission(selection, source, producer, before, dict(proof["artifact"]), deadline, _SEAL)


def readmit_source_mermaid_selection(
    expected: dict[str, Any],
    selection: NativeMermaidSelection,
    source: NativeSourceContext,
    *,
    deadline: float,
    directory: Path,
    env: dict[str, str],
) -> NativeMermaidRuntimeAdmission:
    """Worker re-admits independent command-pinned roots; DATA supplies no roots."""
    if not isinstance(expected, dict) or set(expected) != set(selection.spec_data()) | {"runtime_content_digest"}:
        raise ValueError("Mermaid worker spec selection fields differ")
    if any(expected[name] != value for name, value in selection.spec_data().items()):
        raise ValueError("Mermaid worker spec differs from its independently command-pinned nominations")
    admission = admit_source_mermaid_selection(selection, source, deadline=deadline, directory=directory, env=env)
    if expected != admission.spec_data():
        raise ValueError("Mermaid worker Source/runtime byte custody differs from original controller admission")
    return admission


def validate_source_mermaid_runtime(raw: dict[str, Any]) -> None:
    """Validate portable Source11 byte inventories without reopening origin paths."""
    expected = {
        "schema_version",
        "package_root_label",
        "dependency_root_label",
        "node_executable_label",
        "package_name",
        "version",
        "cli_member",
        "source_npm_inputs",
        "installation",
        "dependency_tree",
        "node",
        "chrome",
        "content_digest",
    }
    if set(raw) != expected or raw.get("schema_version") != SCHEMA:
        raise ValueError("portable Source11 Mermaid runtime schema differs")
    for name in ("package_root_label", "dependency_root_label", "node_executable_label"):
        value = raw[name]
        if not isinstance(value, str) or not Path(value).is_absolute() or ".." in Path(value).parts:
            raise ValueError("portable Source11 runtime label is not an explicit confined absolute path")
    if (
        raw["package_name"] != CLI_NAME
        or raw["version"] != CLI_VERSION
        or raw["cli_member"] != CLI_RELATIVE + "/src/cli.js"
        or Path(raw["package_root_label"]) != Path(raw["dependency_root_label"]) / CLI_RELATIVE
    ):
        raise ValueError("portable Source11 runtime package/CLI/dependency-root identity differs")
    _, lock = _validate_source_inputs(raw["source_npm_inputs"])
    tree = raw["dependency_tree"]
    if not isinstance(tree, dict) or set(tree) != {"members", "bytes", "content_digest"}:
        raise ValueError("portable Source11 dependency byte inventory fields differ")
    members = tree["members"]
    if not isinstance(members, list) or not 0 < len(members) <= MAX_FILES:
        raise ValueError("portable Source11 npm dependency census is absent/unbounded")
    files: dict[str, dict[str, Any]] = {}
    aliases = []
    seen = set()
    total = 0
    for item in members:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise ValueError("portable Source11 dependency member is not literal")
        path = PurePosixPath(item["path"])
        if (
            path.is_absolute()
            or not path.parts
            or ".." in path.parts
            or path.as_posix() != item["path"]
            or item["path"] in seen
        ):
            raise ValueError("portable Source11 dependency member is unconfined/duplicate")
        seen.add(item["path"])
        if item.get("kind") == "file" and set(item) == {"path", "kind", "sha256", "bytes"}:
            _validate_identity({"sha256": item["sha256"], "bytes": item["bytes"]})
            files[item["path"]] = item
            total += item["bytes"]
        elif item.get("kind") == "alias" and set(item) == {"path", "kind", "target"}:
            if not isinstance(item["target"], str):
                raise ValueError("portable Source11 dependency alias is not literal")
            target = PurePosixPath(item["target"])
            if target.is_absolute() or not target.parts or ".." in target.parts:
                raise ValueError("portable Source11 dependency alias escapes its declared npm root")
            aliases.append(item["target"])
        else:
            raise ValueError("portable Source11 dependency member fields differ")
    if type(tree["bytes"]) is not int or not total == tree["bytes"] <= MAX_BYTES or raw["cli_member"] not in files:
        raise ValueError("portable Source11 full npm dependency bytes/CLI closure differs")
    if any(target not in seen and not any(name.startswith(target + "/") for name in seen) for target in aliases):
        raise ValueError("portable Source11 dependency alias lacks its declared original target")
    installation = raw["installation"]
    if not isinstance(installation, dict) or set(installation) != {
        "hidden_lock",
        "locked_installed_packages",
        "package_manifests",
        "missing_optional_packages",
        "content_digest",
    }:
        raise ValueError("portable Source11 installed npm lock fields differ")
    _validate_identity(installation["hidden_lock"])
    hidden = files.get(".package-lock.json")
    if hidden is None or {key: hidden[key] for key in ("sha256", "bytes")} != installation["hidden_lock"]:
        raise ValueError("portable Source11 hidden npm lock bytes omitted from complete dependency closure")
    packages = installation["locked_installed_packages"]
    if not isinstance(packages, dict) or not 0 < len(packages) <= MAX_FILES:
        raise ValueError("portable Source11 installed locked package census is absent/unbounded")
    expected_manifests = set()
    for relative, item in packages.items():
        if relative == "" or lock["packages"].get(relative) != item:
            raise ValueError("portable Source11 installed package resolution/integrity differs from Source")
        expected_manifests.add(PurePosixPath(relative).relative_to("node_modules").as_posix() + "/package.json")
    manifests = installation["package_manifests"]
    if not isinstance(manifests, list) or len(manifests) != len(expected_manifests):
        raise ValueError("portable Source11 complete installed package manifest census differs")
    observed_manifests = set()
    for item in manifests:
        if not isinstance(item, dict) or set(item) != {"path", "sha256", "bytes"} or item["path"] in observed_manifests:
            raise ValueError("portable Source11 package manifest binding fields differ/duplicate")
        _validate_identity({key: item[key] for key in ("sha256", "bytes")})
        member = files.get(item["path"])
        if member is None or {key: member[key] for key in item} != item:
            raise ValueError("portable Source11 installed manifest bytes differ from complete dependency census")
        observed_manifests.add(item["path"])
    if observed_manifests != expected_manifests:
        raise ValueError("portable Source11 installed package manifest identities differ")
    missing = sorted(set(lock["packages"]) - set(packages) - {""})
    if installation["missing_optional_packages"] != missing or any(
        lock["packages"][name].get("optional") is not True for name in missing
    ):
        raise ValueError("portable Source11 omits a required Source package or alters optional absence census")
    _validate_identity(raw["node"])
    chrome = raw["chrome"]
    executable = PurePosixPath(chrome["executable"]).relative_to(PurePosixPath(chrome["root"])).as_posix()
    digest = next(
        (item["sha256"] for item in chrome["files"] if item["path"] == executable and item["kind"] == "file"), None
    )
    if digest is None:
        raise ValueError("portable Source11 Chrome executable is absent from its complete application closure")
    validate_runtime(chrome, chrome["executable"], digest)
    for item in (tree, installation, raw):
        if item["content_digest"] != canonical_digest(
            {key: value for key, value in item.items() if key != "content_digest"}
        ):
            raise ValueError("portable Source11 runtime/package/dependency digest differs")


def _validate_identity(value: object) -> None:
    if (
        not isinstance(value, dict)
        or set(value) != {"bytes", "sha256"}
        or type(value["bytes"]) is not int
        or not 0 <= value["bytes"] <= 512 * 1024 * 1024
        or not isinstance(value["sha256"], str)
        or re.fullmatch(r"[0-9a-f]{64}", value["sha256"]) is None
    ):
        raise ValueError("portable Source11 runtime file identity is invalid/unbounded")


# Process-local custody is seeded only by the actual Source-owned factory. It is
# a held capability, separate from CLI nominations and JSON specification DATA.
_CURRENT_RUNTIME: ContextVar[NativeMermaidRuntimeAdmission | None] = ContextVar(
    "template_source_mermaid_runtime_admission", default=None
)


def current_source_mermaid_runtime_admission() -> NativeMermaidRuntimeAdmission | None:
    """Return the genuinely active current owner; no path or receipt discovery."""
    admission = _CURRENT_RUNTIME.get()
    if admission is None:
        return None
    producer = current_native_producer_operation()
    if producer is None or producer is not admission.producer or producer.source is not admission.source:
        raise ValueError("Source Mermaid runtime scope lost its actual process owner")
    reader = SnapshotReader(admission.source.bindings.current_root, native_producer_operation=producer)
    producer.verify(reader, run_id=admission.source.bindings.run_id, deadline=admission.deadline)
    return admission


@contextmanager
def source_mermaid_runtime_operation(
    admission: NativeMermaidRuntimeAdmission,
    *,
    source: NativeSourceContext,
    deadline: float,
) -> Iterator[NativeMermaidRuntimeAdmission]:
    """Hold the genuine admission through callers inside the same original clock."""
    if (
        not isinstance(admission, NativeMermaidRuntimeAdmission)
        or admission._seal is not _SEAL
        or admission.source is not source
        or current_native_producer_operation() is not admission.producer
        or not deadline <= admission.deadline
        or _CURRENT_RUNTIME.get() is not None
    ):
        raise ValueError("Source Mermaid runtime scope cannot be minted from DATA or replace another actual owner")
    admission.observe(deadline=deadline)
    token = _CURRENT_RUNTIME.set(admission)
    try:
        yield admission
    finally:
        try:
            admission.observe(deadline=deadline)
        finally:
            _CURRENT_RUNTIME.reset(token)
