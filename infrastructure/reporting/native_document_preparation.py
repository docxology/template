"""Prepare exact Source-selected document providers; no runtime acceptance claim."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import stat
import subprocess
import tarfile
import tempfile
import time
import zipfile
from io import BytesIO
from pathlib import Path, PurePosixPath
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_document_elf import read_physical_file, require_glibc_executable
from infrastructure.reporting.native_document_provider_contracts import (
    MAX_ARCHIVE_BYTES,
    MAX_BINARY_BYTES,
    MAX_MANIFEST_BYTES,
    PIN_SOURCE,
    select_document_provider,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

_MAX_JSON = 256 * 1024 * 1024
_MAX_EXPANDED = 1024 * 1024 * 1024
# Do not accept flake-local settings or the optional undo.it cache. These are
# the reviewed signed upstream caches; source/recipe checks remain independent.
_NIX_OPTIONS = (
    "--extra-experimental-features",
    "nix-command flakes",
    "--option",
    "accept-flake-config",
    "false",
    "--option",
    "substituters",
    "https://cache.nixos.org https://cache.iog.io https://pandoc-crossref.cachix.org",
    "--option",
    "extra-trusted-public-keys",
    "hydra.iohk.io:f/Ea+s+dFdN+3Y/G+FDgSq+a5NEWhJGzdjvKNGv0/EQ= "
    "pandoc-crossref.cachix.org-1:LI9ABFTkGpPCTkUTzoopVSSpb1a26RSTJNMsqVbDtPM=",
    "--option",
    "require-sigs",
    "true",
    "--option",
    "max-jobs",
    "2",
    "--option",
    "cores",
    "2",
)


def _record(directory: Path, name: str, value: Any) -> None:
    atomic_write_bytes_confined(directory, directory / name, (json.dumps(value, indent=2) + "\n").encode())


def _directory(path: Path, *, fresh: bool) -> Path:
    path = path.absolute()
    if path.is_symlink() or (fresh and path.exists()):
        raise ValueError("document preparation requires a real fresh destination/cache directory")
    path.mkdir(parents=True, exist_ok=not fresh)
    if not stat.S_ISDIR(path.lstat().st_mode) or path.resolve(strict=True) != path:
        raise ValueError("document preparation refuses aliased directory ancestry")
    return path


def _run(command: list[str], directory: Path, label: str, *, deadline: float, limit: int = _MAX_JSON) -> bytes:
    """Keep genuine stderr/exit diagnostics; capture stdout under a finite bound."""
    output = directory / f"{label}.stdout"
    with output.open("xb") as stream:
        result = subprocess.run(
            command, stdin=subprocess.DEVNULL, stdout=stream, check=False, timeout=remaining(deadline)
        )
    _record(directory, f"{label}.command.json", {"argv": command, "returncode": result.returncode})
    if result.returncode:
        raise subprocess.CalledProcessError(result.returncode, command)
    content = read_bytes_confined(directory, output, max_bytes=limit)
    remaining(deadline)
    return content


def _json_command(command: list[str], directory: Path, label: str, *, deadline: float) -> Any:
    return json.loads(_run(command, directory, label, deadline=deadline))


def _member_name(name: str) -> str:
    path = PurePosixPath(name)
    if (
        not name
        or "\\" in name
        or "\0" in name
        or path.is_absolute()
        or ".." in path.parts
        or not path.parts
        or path.as_posix() != name.rstrip("/")
    ):
        raise ValueError("document archive has an unsafe or ambiguous member")
    return path.as_posix()


def _zip_member(content: bytes, pin: dict[str, Any], *, deadline: float) -> bytes:
    selected: bytes | None = None
    total = 0
    names: set[str] = set()
    with zipfile.ZipFile(BytesIO(content)) as archive:
        rows = archive.infolist()
        if not 0 < len(rows) <= 1000:
            raise ValueError("document ZIP has an empty or excessive complete member roster")
        for row in rows:
            remaining(deadline)
            name = _member_name(row.filename)
            mode = row.external_attr >> 16
            member_type = stat.S_IFMT(mode)
            if name in names or row.flag_bits & 1 or member_type not in {0, stat.S_IFREG, stat.S_IFDIR, stat.S_IFLNK}:
                raise ValueError("document ZIP has duplicate, encrypted or unsupported members")
            names.add(name)
            total += row.file_size
            if not 0 <= row.file_size <= MAX_BINARY_BYTES or total > _MAX_EXPANDED:
                raise ValueError("document ZIP exceeds its finite expanded payload bound")
            if name == pin["member"]:
                # Official archives may carry other command aliases; never
                # extract or follow them, and never select one as the body.
                if selected is not None or row.is_dir() or member_type not in {0, stat.S_IFREG} or not mode & 0o111:
                    raise ValueError("document ZIP selected member is not one real executable")
                with archive.open(row) as stream:
                    selected = stream.read(MAX_BINARY_BYTES + 1)
                if not selected or len(selected) != row.file_size:
                    raise ValueError("document ZIP executable is empty, excessive or truncated")
    if selected is None:
        raise ValueError("document ZIP lacks its exact Source executable member")
    remaining(deadline)
    return selected


def document_archive_member(content: bytes, pin: dict[str, Any], *, deadline: float) -> bytes:
    """Verify the full transport and exact member; source builds pin the body."""
    if not 0 < len(content) <= MAX_ARCHIVE_BYTES:
        raise ValueError("document archive exceeds its complete compressed byte bound")
    if pin["kind"] == "official-archives":
        if len(content) != pin["archive_bytes"]:
            raise ValueError(f"document archive size mismatch: {pin['asset']}")
        if hashlib.sha256(content).hexdigest() != pin["archive_sha256"]:
            raise ValueError(f"document archive SHA-256 mismatch: {pin['asset']}")
        if pin["format"] == "zip":
            return _zip_member(content, pin, deadline=deadline)
    from infrastructure.reporting.native_document_provider_archives import provider_archive_member

    _, body = provider_archive_member(content, pin, deadline=deadline)
    return body


def _archive(archives: Path, pin: dict[str, Any], *, deadline: float) -> tuple[Path, bytes] | None:
    path = archives / pin["asset"]
    if not path.exists() and not path.is_symlink():
        return None
    content = read_physical_file(path, limit=MAX_ARCHIVE_BYTES)
    return path, document_archive_member(content, pin, deadline=deadline)


def _official_archive(archives: Path, pin: dict[str, Any], *, deadline: float) -> tuple[Path, bytes]:
    existing = _archive(archives, pin, deadline=deadline)
    if existing is not None:
        return existing
    with tempfile.TemporaryDirectory(prefix=".document-download-", dir=archives) as temporary:
        path = Path(temporary) / pin["asset"]
        subprocess.run(
            [
                "curl",
                "--proto",
                "=https",
                "--proto-redir",
                "=https",
                "--fail",
                "--location",
                "--retry",
                "2",
                "--max-time",
                "180",
                "--max-filesize",
                str(pin["archive_bytes"]),
                "--output",
                str(path),
                pin["url"],
            ],
            stdin=subprocess.DEVNULL,
            check=True,
            timeout=remaining(deadline),
        )
        content = read_physical_file(path, limit=MAX_ARCHIVE_BYTES)
        body = document_archive_member(content, pin, deadline=deadline)
        target = archives / pin["asset"]
        if target.exists() or target.is_symlink():
            raise ValueError("document archive cache changed during acquisition")
        atomic_write_bytes_confined(archives, target, content, mode=0o600)
    return target, body


def _canonical_archive(body: bytes, member: str) -> bytes:
    stream = BytesIO()
    with tarfile.open(fileobj=stream, mode="w:xz", format=tarfile.USTAR_FORMAT, preset=6) as archive:
        row = tarfile.TarInfo(member)
        row.size, row.mode, row.mtime = len(body), 0o755, 0
        archive.addfile(row, BytesIO(body))
    content = stream.getvalue()
    if len(content) > MAX_ARCHIVE_BYTES:
        raise ValueError("document source-built archive exceeds its complete compressed byte bound")
    return content


def _require_derivation_graph(graph: Any, build: dict[str, Any]) -> None:
    """Compare actual Nix JSON, including documented v3/v4 basename paths."""
    if type(graph) is not dict:
        raise ValueError("actual Nix recursive compiler/dependency derivation evidence is incomplete")
    paths = {build["derivation"], Path(build["derivation"]).name}
    roots = [(path, row) for path, row in graph.items() if path in paths]
    if len(roots) != 1 or type(roots[0][1]) is not dict:
        raise ValueError("actual Nix recursive derivations omit or duplicate the exact Source root")
    path, root = roots[0]
    version = root.get("version")
    if version is not None and (type(version) is not int or version not in {1, 2, 3, 4}):
        raise ValueError("actual Nix derivation JSON version is unsupported")
    expected_paths = {build["derivation"]}
    expected_outputs = {build["output"]}
    if version in {3, 4}:
        expected_paths.add(Path(build["derivation"]).name)
        expected_outputs.add(Path(build["output"]).name)
    outputs = root.get("outputs")
    if (
        path not in expected_paths
        or root.get("system") != "x86_64-linux"
        or type(outputs) is not dict
        or type(outputs.get("out")) is not dict
        or type(outputs["out"].get("path")) is not str
        or outputs["out"]["path"] not in expected_outputs
    ):
        raise ValueError("actual Nix derivation declares a different machine or output")


def _source_build(
    provider: dict[str, Any],
    archives: Path,
    destination: Path,
    *,
    build_inputs: dict[str, bytes],
    nix: Path,
    nix_sudo: bool,
    machine: str,
    deadline: float,
) -> dict[str, Any]:
    build = provider["build"]
    for relative, body in build_inputs.items():
        atomic_write_bytes_confined(destination, destination / Path(relative).name, body, mode=0o600)
    recipe = destination / Path(build["recipe_path"]).name
    local_arguments = ["--file", str(recipe)]
    command = (["sudo", "-n"] if nix_sudo else []) + [
        str(nix),
        *(["--store", "local"] if nix_sudo else []),
        *_NIX_OPTIONS,
    ]
    source_url = build["flake_url"]
    metadata = _json_command(
        command + ["flake", "metadata", "--json", "--no-write-lock-file", "--no-update-lock-file", source_url],
        destination,
        "nix-source",
        deadline=deadline,
    )
    if (
        type(metadata) is not dict
        or type(metadata.get("locked")) is not dict
        or metadata["locked"].get("rev") != build["revision"]
        or metadata["locked"].get("narHash") != build["nar_hash"]
    ):
        raise ValueError("actual Nix source revision/NAR differs from the complete Source build pin")
    source = Path(metadata["path"])
    if not source.is_absolute() or not source.is_relative_to("/nix/store") or source.resolve(strict=True) != source:
        raise ValueError("actual Nix source is not a physical installed store tree")
    actual_nar = (
        _run(
            command + ["hash", "path", "--type", "sha256", str(source)],
            destination,
            "nix-source-nar",
            deadline=deadline,
            limit=4096,
        )
        .decode("ascii")
        .strip()
    )
    if actual_nar != build["nar_hash"]:
        raise ValueError("actual complete Nix source tree differs from its Source-pinned NAR hash")
    for name, field in (("flake.lock", "flake_lock_sha256"), ("cabal.project.freeze", "upstream_freeze_sha256")):
        body = read_physical_file(source / name, limit=MAX_MANIFEST_BYTES)
        if hashlib.sha256(body).hexdigest() != build[field]:
            raise ValueError("actual Nix source lock/freeze differs from the exact frozen dependency recipe")
        atomic_write_bytes_confined(destination, destination / name, body, mode=0o600)
    compiler = read_physical_file(source / "stack.yaml", limit=MAX_MANIFEST_BYTES).decode("utf-8")
    if [row for row in compiler.splitlines() if row.startswith("resolver:")] != [
        "resolver: " + build["upstream_compiler"]
    ]:
        raise ValueError("actual upstream source does not select its separately declared upstream compiler")
    evaluation = """value: {
      derivation = value.provider.drvPath; output = value.provider.outPath;
      compiler_derivation = value.compiler.drvPath; compiler_output = value.compiler.outPath;
      plan_derivation = value.plan.drvPath; plan_output = value.plan.outPath;
      resolved_freeze = toString value.resolvedFreeze;
    }"""
    evaluated = _json_command(
        command
        + ["eval", "--json", "--no-write-lock-file", "--no-update-lock-file", *local_arguments, "--apply", evaluation],
        destination,
        "nix-evaluation",
        deadline=deadline,
    )
    expected_fields = (
        "derivation",
        "output",
        "compiler_derivation",
        "compiler_output",
        "plan_derivation",
        "plan_output",
    )
    if (
        type(evaluated) is not dict
        or set(evaluated) != {*expected_fields, "resolved_freeze"}
        or any(evaluated[field] != build[field] for field in expected_fields)
        or type(evaluated["resolved_freeze"]) is not str
    ):
        raise ValueError("actual Nix compiler/plan/provider evaluation differs from the complete Source build pin")
    graph = _json_command(
        command
        + [
            "derivation",
            "show",
            "--recursive",
            build["derivation"],
            build["compiler_derivation"],
            build["plan_derivation"],
        ],
        destination,
        "nix-recursive-derivations",
        deadline=deadline,
    )
    for prefix in ("", "compiler_", "plan_"):
        _require_derivation_graph(
            graph, {"derivation": build[prefix + "derivation"], "output": build[prefix + "output"]}
        )
    outputs = _json_command(
        command
        + [
            "build",
            "--json",
            "--no-write-lock-file",
            "--no-update-lock-file",
            "--out-link",
            str(destination / "nix-runtime"),
            *local_arguments,
            "provider",
        ],
        destination,
        "nix-build",
        deadline=deadline,
    )
    if (
        type(outputs) is not list
        or len(outputs) != 1
        or outputs[0].get("drvPath") != build["derivation"]
        or outputs[0].get("outputs") != {"out": build["output"]}
    ):
        raise ValueError("actual completed Nix build differs from the exact declared derivation/output")
    output = Path(build["output"])
    if (
        output.resolve(strict=True) != output
        or not output.is_dir()
        or (destination / "nix-runtime").resolve(strict=True) != output
    ):
        raise ValueError("actual Nix output/retained runtime GC root differs from the declared build")
    closure = _json_command(
        command + ["path-info", "--recursive", "--json", str(output)],
        destination,
        "nix-runtime-closure",
        deadline=deadline,
    )
    if type(closure) is dict:
        closure_paths = set(closure)
    elif type(closure) is list and all(type(row) is dict and type(row.get("path")) is str for row in closure):
        closure_paths = {row["path"] for row in closure}
    else:
        raise ValueError("actual Nix runtime closure has an unsupported path-info schema")
    if str(output) not in closure_paths:
        raise ValueError("actual Nix runtime closure omits the exact declared output")
    _run(
        command + ["store", "verify", "--recursive", str(output)],
        destination,
        "nix-runtime-verification",
        deadline=deadline,
    )
    resolved_freeze = Path(evaluated["resolved_freeze"])
    if not resolved_freeze.is_absolute() or not resolved_freeze.is_relative_to("/nix/store"):
        raise ValueError("actual resolved dependency freeze is outside the installed Nix store")
    resolved_body = read_physical_file(resolved_freeze, limit=MAX_MANIFEST_BYTES)
    if hashlib.sha256(resolved_body).hexdigest() != build["resolved_freeze_sha256"]:
        raise ValueError("actual resolved dependency freeze differs from the exact Source plan")
    atomic_write_bytes_confined(destination, destination / "resolved-cabal.project.freeze", resolved_body, mode=0o600)
    observed: dict[str, Any] = {}
    for name, pin in provider["tools"].items():
        executable = "pandoc" if name == "pandoc" else "pandoc-crossref"
        selected = output / "bin" / executable
        physical = selected.resolve(strict=True)
        if (
            not physical.is_relative_to("/nix/store")
            or len(physical.parts) < 5
            or str(Path(*physical.parts[:4])) not in closure_paths
        ):
            raise ValueError("actual Nix executable resolves outside the retained store closure")
        body = read_physical_file(physical, limit=MAX_BINARY_BYTES, executable=True)
        actual_sha256 = hashlib.sha256(body).hexdigest()
        if len(body) != pin["binary_bytes"] or actual_sha256 != pin["binary_sha256"]:
            raise ValueError(
                f"actual source-built {executable} differs from the Source-authoritative body pin: "
                f"bytes={len(body)} expected={pin['binary_bytes']}; "
                f"sha256={actual_sha256} expected={pin['binary_sha256']}"
            )
        interpreter = require_glibc_executable(physical, machine=machine)
        tool_pin = {**pin, "kind": provider["kind"], "build": build}
        cached = _archive(archives, tool_pin, deadline=deadline)
        if cached is None:
            content = _canonical_archive(body, pin["member"])
            if document_archive_member(content, tool_pin, deadline=deadline) != body:
                raise ValueError("canonical source-built archive changed its unchanged executable member")
            target = archives / pin["asset"]
            if target.exists() or target.is_symlink():
                raise ValueError("document source-built cache changed before archive persistence")
            atomic_write_bytes_confined(archives, target, content, mode=0o600)
        elif cached[1] != body:
            raise ValueError("cached source-built archive differs from the exact actual Nix executable")
        target = destination / executable
        atomic_write_bytes_confined(destination, target, body, mode=0o755)
        if read_physical_file(target, limit=MAX_BINARY_BYTES, executable=True) != body:
            raise ValueError("prepared executable differs from the complete Source-pinned built member")
        require_glibc_executable(target, machine=machine)
        observed[name] = {
            "selected_path": str(selected),
            "physical_path": str(physical),
            "prepared_path": str(target),
            "binary_sha256": pin["binary_sha256"],
            "binary_bytes": len(body),
            "pt_interp": interpreter,
            "archive": str(archives / pin["asset"]),
        }
    return observed


def prepare_document_providers(
    source_root: Path,
    archives: Path,
    destination: Path,
    *,
    host: dict[str, str] | None = None,
    nix: Path | None = None,
    nix_sudo: bool = False,
    deadline: float,
) -> dict[str, Any]:
    """Prepare the selected binaries and retain genuine non-authoritative provenance."""
    host = host if host is not None else {"system": platform.system(), "machine": platform.machine()}
    reader = SnapshotReader(source_root, operation_deadline=deadline)
    source_pin = reader.read(PIN_SOURCE, max_bytes=MAX_MANIFEST_BYTES)
    provider = select_document_provider(source_pin.content, host)
    build_inputs: dict[str, bytes] = {}
    if provider["kind"] == "nix-source-build":
        for name in ("recipe", "freeze"):
            snapshot = reader.read(provider["build"][name + "_path"], max_bytes=MAX_MANIFEST_BYTES)
            if snapshot.sha256 != provider["build"][name + "_sha256"]:
                raise ValueError("document Root recipe/freeze differs from the complete Source build pin")
            build_inputs[provider["build"][name + "_path"]] = snapshot.content
    archives = _directory(archives, fresh=False)
    # Refuse restored tampering before any download, build or tool execution.
    for pin in provider["tools"].values():
        _archive(
            archives,
            {
                **pin,
                "kind": provider["kind"],
                **({"build": provider["build"]} if provider["kind"] == "nix-source-build" else {}),
            },
            deadline=deadline,
        )
    destination = _directory(destination, fresh=True)
    if provider["kind"] == "nix-source-build":
        found = str(nix) if nix is not None else shutil.which("nix")
        if not found:
            raise ValueError("document source preparation requires the runner's installed Nix client")
        tools = _source_build(
            provider,
            archives,
            destination,
            build_inputs=build_inputs,
            nix=Path(found),
            nix_sudo=nix_sudo,
            machine=host["machine"],
            deadline=deadline,
        )
    else:
        tools = {}
        for name, row in provider["tools"].items():
            pin = {**row, "kind": provider["kind"]}
            archive, body = _official_archive(archives, pin, deadline=deadline)
            target = destination / ("pandoc" if name == "pandoc" else "pandoc-crossref")
            atomic_write_bytes_confined(destination, target, body, mode=0o755)
            if read_physical_file(target, limit=MAX_BINARY_BYTES, executable=True) != body:
                raise ValueError("prepared official executable differs from the exact archive member")
            tools[name] = {
                "prepared_path": str(target),
                "archive": str(archive),
                "binary_sha256": hashlib.sha256(body).hexdigest(),
                "binary_bytes": len(body),
            }
    for name, tool in tools.items():
        tool["version_stdout"] = _run(
            [tool["prepared_path"], "--version"], destination, name + "-version", deadline=deadline, limit=1024 * 1024
        ).decode("utf-8")
    if not reader.unchanged():
        raise ValueError("document Source pin changed during actual preparation")
    provenance = {
        "schema_version": "template-document-provider-preparation-v2",
        "host": host,
        "pin_source": PIN_SOURCE,
        "pin_sha256": source_pin.sha256,
        "provider": provider,
        "build_inputs": {
            path: {"sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)}
            for path, body in build_inputs.items()
        },
        "tools": tools,
        "runtime_acceptance": False,
        "role": "actual document provider preparation only",
    }
    _record(destination, "document-provider-provenance.json", provenance)
    return provenance


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--archives", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--nix-executable", type=Path)
    parser.add_argument("--nix-sudo", action="store_true")
    parser.add_argument("--timeout", type=int, default=7200)
    args = parser.parse_args()
    if not 0 < args.timeout <= 14400:
        parser.error("document preparation timeout must be positive and at most 14400 seconds")
    result = prepare_document_providers(
        args.source_root,
        args.archives,
        args.destination,
        nix=args.nix_executable,
        nix_sudo=args.nix_sudo,
        deadline=time.monotonic() + args.timeout,
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
