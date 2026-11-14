"""Same-run preparation DATA, never a substitute for Source/provider acceptance.

Preserve the genuine complete SQLite registrations, including signatures,
ultimate flags and CA metadata. Never merge registrations or invent trust.
Only a fresh root-owned store and the exact producer Source/run/client may
consume a snapshot. The caller bounds this privileged operation to 900 seconds.
Normal document preparation must still evaluate, build and verify its pins.
"""
from __future__ import annotations

import argparse
import fcntl
import grp
import gzip
import hashlib
import json
import os
import re
import shutil
import sqlite3
import stat
import subprocess
import sys
import tempfile
import traceback
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

SCHEMA = "template-same-run-nix-store/v1"
DB = Path("/nix/var/nix/db")
STORE = Path("/nix/store")
CHUNK = 1024 * 1024
MAX_MANIFEST = 64 * 1024 * 1024
STORE_PATH = re.compile(r"/nix/store/[0123456789abcdfghijklmnpqrsvwxyz]{32}-[A-Za-z0-9+._?=-]{1,211}")
CHILD_ENV = {"PATH": "/usr/bin:/bin", "HOME": "/root", "LC_ALL": "C.UTF-8"}


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate snapshot field: {key}")
        result[key] = value
    return result


def _sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _binding(nix: Path) -> dict[str, Any]:
    from infrastructure.reporting.native_document_provider_contracts import (
        BUILD_COMPILER_PATCHES,
        BUILD_FREEZE,
        BUILD_RECIPE,
        PIN_SOURCE,
    )

    names = ("GITHUB_REPOSITORY", "GITHUB_SHA", "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT")
    values = {name: os.environ[name] for name in names}
    if not re.fullmatch(r"[0-9a-f]{40}", values["GITHUB_SHA"]):
        raise ValueError("snapshot requires the exact hosted Source")
    if any(not values[name].isdigit() for name in names[2:]):
        raise ValueError("snapshot requires the exact hosted run and attempt")
    if os.environ.get("GITHUB_ACTIONS") != "true" or not re.fullmatch(r"[^/\s]+/[^/\s]+", values["GITHUB_REPOSITORY"]):
        raise ValueError("snapshot requires the actual hosted repository context")
    actual_source = subprocess.check_output(
        ["git", "-c", f"safe.directory={ROOT}", "-C", str(ROOT), "rev-parse", "HEAD"],
        env=CHILD_ENV, text=True, timeout=30,
    ).strip()
    if actual_source != values["GITHUB_SHA"]:
        raise ValueError("snapshot physical checkout differs from its hosted Source")
    version = subprocess.check_output([str(nix), "--version"], env=CHILD_ENV, text=True, timeout=30).strip()
    if version != "nix (Nix) 2.18.1":
        raise ValueError("snapshot transport is qualified only for the signed-APT Nix 2.18.1 client")
    return {
        **values, "nix_version": version, "nix_sha256": _sha(nix),
        "source_inputs": {name: _sha(ROOT / name) for name in
                          (PIN_SOURCE, BUILD_RECIPE, BUILD_FREEZE, *BUILD_COMPILER_PATCHES)},
    }


def _root_store(nix: Path) -> Path:
    if os.geteuid() != 0 or sys.platform != "linux" or os.uname().machine != "x86_64":
        raise ValueError("snapshot transport requires the owned root Linux x86_64 preparation process")
    if nix != Path("/usr/bin/nix"):
        raise ValueError("snapshot transport requires the existing signed-APT client path")
    for path in (Path("/nix"), Path("/nix/var"), Path("/nix/var/nix"), DB, STORE):
        meta = path.lstat()
        if not stat.S_ISDIR(meta.st_mode) or meta.st_uid != 0 or meta.st_mode & 0o002:
            raise ValueError(f"snapshot refuses a linked, non-root or world-writable store: {path}")
        if path != STORE and meta.st_mode & 0o020:
            raise ValueError(f"snapshot refuses a group-writable store control directory: {path}")
        if path == STORE and meta.st_mode & 0o020:
            if not meta.st_mode & 0o1000 or meta.st_gid != grp.getgrnam("nixbld").gr_gid:
                raise ValueError("snapshot refuses a foreign writable store group")
    for path in (nix, nix.with_name("nix-store"), DB / "db.sqlite", DB / "schema"):
        if path.parent == DB and path.is_symlink():
            raise ValueError("snapshot refuses linked store control files")
        actual = path.resolve(strict=True)
        meta = actual.stat()
        if not stat.S_ISREG(meta.st_mode) or meta.st_uid != 0 or meta.st_mode & 0o022:
            raise ValueError(f"snapshot refuses an untrusted store control file: {path}")
    store_binary = nix.with_name("nix-store")
    if _sha(store_binary) != _sha(nix):
        raise ValueError("nix-store must be the same signed client body as nix")
    return store_binary


@contextmanager
def _store_lock() -> Iterator[None]:
    # Nix 2.18 uses flock and holds this inode shared for each LocalStore.
    # Dump/restore are the two nix-store operations that do not open a store.
    fd = os.open(DB / "big-lock", os.O_RDWR | os.O_NOFOLLOW)
    try:
        meta = os.fstat(fd)
        if not stat.S_ISREG(meta.st_mode) or meta.st_uid != 0 or meta.st_mode & 0o022:
            raise ValueError("snapshot refuses an untrusted Nix store lock")
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(fd)


def _db_info(path: Path) -> dict[str, Any]:
    with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as connection:
        connection.execute("PRAGMA trusted_schema=OFF")
        if connection.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
            raise ValueError("snapshot database integrity failed")
        if connection.execute("PRAGMA foreign_key_check").fetchall():
            raise ValueError("snapshot database references are incomplete")
        schema = connection.execute("SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name").fetchall()
        # Explicit schema/table/column/row order, not Python's iterdump or an
        # SQLite query-plan-dependent scan. Producer3.14 and consumer3.15 may
        # carry different SQLite/Python implementations.
        dump = hashlib.sha256(json.dumps(schema, separators=(",", ":")).encode())
        paths = connection.execute("SELECT path,hash,narSize FROM ValidPaths ORDER BY path").fetchall()
        nonempty = []
        for (name,) in connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
            quoted = '"' + name.replace('"', '""') + '"'
            columns = [row[1] for row in connection.execute(f"PRAGMA table_info({quoted})")]
            ordering = ",".join('"' + column.replace('"', '""') + '"' for column in columns)
            dump.update(json.dumps([name, columns], separators=(",", ":")).encode() + b"\n")
            found = False
            for row in connection.execute(f"SELECT * FROM {quoted} ORDER BY {ordering}"):
                if not found:
                    nonempty.append(name)
                    found = True
                values = [{"blob": value.hex()} if isinstance(value, bytes) else value for value in row]
                dump.update(json.dumps(values, allow_nan=False, separators=(",", ":")).encode() + b"\n")
    return {"schema": schema, "logical_sha256": dump.hexdigest(), "paths": paths, "nonempty": nonempty}


def _backup(source: Path, destination: Path, *, standalone: bool) -> None:
    with sqlite3.connect(source.as_uri() + "?mode=ro", uri=True) as reader:
        with sqlite3.connect(destination) as writer:
            reader.backup(writer)
            writer.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            if standalone:
                writer.execute("PRAGMA journal_mode=DELETE")


def _nar_hash(value: str) -> str:
    # The actual 2.18 ValidPaths schema stores the typed base16 representation.
    if not isinstance(value, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", value):
        raise ValueError("snapshot requires a complete SHA-256 NAR registration")
    return value.removeprefix("sha256:")


def _canonical_metadata(path: Path) -> None:
    """Restore Nix 2.18 metadata omitted by NAR; never follow a link.

    local-store.cc canonicaliseTimestampAndPermissions: read-only 0444/0555,
    unchanged executable bit and mtimeStore=1. Fresh NAR nodes belong to this
    root process; foreign ownership or inherited Linux ACLs must not be adopted.
    """
    meta = path.lstat()
    if not (stat.S_ISREG(meta.st_mode) or stat.S_ISDIR(meta.st_mode) or stat.S_ISLNK(meta.st_mode)):
        raise ValueError("restored NAR has an unsupported node type")
    if meta.st_uid != os.geteuid():
        raise ValueError("restored NAR has foreign ownership")
    # Nix itself handles extended attributes only in its Linux branch.
    if sys.platform == "linux":
        if os.listxattr(path, follow_symlinks=False):
            raise ValueError("restored NAR has inherited attributes")
    if not stat.S_ISLNK(meta.st_mode):
        os.chmod(path, 0o555 if meta.st_mode & stat.S_IXUSR else 0o444)
    os.utime(path, ns=(meta.st_atime_ns, 1_000_000_000), follow_symlinks=False)
    if stat.S_ISDIR(meta.st_mode):
        with os.scandir(path) as entries:
            for entry in entries:
                _canonical_metadata(Path(entry.path))


def _entry(path: Path) -> dict[str, Any]:
    return {"file": path.name, "size": path.stat().st_size, "sha256": _sha(path)}


def capture(directory: Path, store_binary: Path, binding: dict[str, Any]) -> dict[str, Any]:
    uid, gid = int(os.environ["SUDO_UID"]), int(os.environ["SUDO_GID"])
    if uid <= 0 or gid < 0:
        raise ValueError("snapshot requires the actual non-root caller identity")
    destination = directory
    # A caller-writable parent cannot rename/replace this privileged work tree.
    directory = Path(tempfile.mkdtemp(prefix="template-nix-capture-", dir=DB.parent))
    with _store_lock():
        _backup(DB / "db.sqlite", directory / "database.sqlite", standalone=True)
        shutil.copyfile(DB / "schema", directory / "schema")
        database = _db_info(directory / "database.sqlite")
        if not database["paths"]:
            raise ValueError("snapshot refuses an empty producer store")
        entries = []
        for ordinal, (path, nar_hash, nar_size) in enumerate(database["paths"]):
            if not STORE_PATH.fullmatch(path) or type(nar_size) is not int or nar_size <= 0:
                raise ValueError("snapshot has an unsafe or incomplete registered path")
            payload = directory / f"path-{ordinal:05d}.nar.gz"
            digest = hashlib.sha256()
            size = 0
            with payload.open("xb") as encoded:
                with gzip.GzipFile(filename="", mode="wb", fileobj=encoded, compresslevel=1, mtime=0) as compressed:
                    with subprocess.Popen([str(store_binary), "--dump", path], env=CHILD_ENV,
                                          stdout=subprocess.PIPE) as process:
                        assert process.stdout is not None
                        while chunk := process.stdout.read(CHUNK):
                            size += len(chunk)
                            if size > nar_size:
                                raise ValueError("snapshot dump exceeds its genuine NAR registration")
                            digest.update(chunk)
                            compressed.write(chunk)
                        if process.wait() != 0:
                            raise ValueError(f"original Nix dump failed: {path}")
            if size != nar_size or digest.hexdigest() != _nar_hash(nar_hash):
                raise ValueError(f"original Nix dump differs from its registered content: {path}")
            entries.append({**_entry(payload), "path": path, "nar_sha256": digest.hexdigest(), "nar_size": size})
        if _db_info(DB / "db.sqlite")["logical_sha256"] != database["logical_sha256"]:
            raise ValueError("producer registrations changed during snapshot custody")
        manifest = {"schema": SCHEMA, "binding": binding, "database": _entry(directory / "database.sqlite"),
                    "schema_file": _entry(directory / "schema"), "database_logical_sha256": database["logical_sha256"],
                    "paths": entries}
        (directory / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    # Freeze the producer authority before any file becomes caller-writable.
    result = {"manifest_sha256": _sha(directory / "manifest.json"), "registered_paths": len(entries),
              "nar_bytes": sum(entry["nar_size"] for entry in entries), "preparation_DATA_only": True}
    names = ["manifest.json", "database.sqlite", "schema", *(entry["file"] for entry in entries)]
    for name in names:
        path = directory / name
        os.chmod(path, 0o600)
        os.chown(path, uid, gid, follow_symlinks=False)
    os.chown(directory, uid, gid, follow_symlinks=False)
    # Only an irrevocably unprivileged child resolves the caller's destination.
    # Same-device moves avoid duplicating the large NAR payloads; cross-device
    # moves copy as the caller. No privileged caller-path access follows handoff.
    child = os.fork()
    if child == 0:
        try:
            os.setgroups([])
            os.setgid(gid)
            os.setuid(uid)
            destination.mkdir(mode=0o700)
            for name in names:
                shutil.move(str(directory / name), str(destination / name))
            os._exit(0)
        except BaseException:
            traceback.print_exc()
            os._exit(1)
    _, status = os.waitpid(child, 0)
    if not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0:
        raise ValueError("unprivileged snapshot handoff failed")
    os.rmdir(directory)  # Protected parent; refuse unexpected remaining entries.
    return result


def validate_manifest(content: bytes, expected_sha256: str, binding: dict[str, Any]) -> dict[str, Any]:
    if len(content) > MAX_MANIFEST or hashlib.sha256(content).hexdigest() != expected_sha256:
        raise ValueError("snapshot manifest differs from the same-run producer output")
    manifest = json.loads(content, object_pairs_hook=_object)
    fields = {"schema", "binding", "database", "schema_file", "database_logical_sha256", "paths"}
    if type(manifest) is not dict or set(manifest) != fields or manifest["schema"] != SCHEMA:
        raise ValueError("snapshot has an unknown or incomplete closed schema")
    if manifest["binding"] != binding:
        raise ValueError("snapshot differs from the exact Source, run, attempt, client or provider inputs")
    if not re.fullmatch(r"[0-9a-f]{64}", str(manifest["database_logical_sha256"])):
        raise ValueError("snapshot lacks complete registration custody")
    entries = manifest["paths"]
    if type(entries) is not list or not 0 < len(entries) <= 100000:
        raise ValueError("snapshot requires a finite complete registered path set")
    previous = ""
    for ordinal, entry in enumerate(entries):
        if type(entry) is not dict or set(entry) != {"file", "size", "sha256", "path", "nar_sha256", "nar_size"}:
            raise ValueError("snapshot path row has unknown or missing fields")
        if entry["file"] != f"path-{ordinal:05d}.nar.gz" or not isinstance(entry["path"], str):
            raise ValueError("snapshot path must use its exact flat transport name")
        if not STORE_PATH.fullmatch(entry["path"]) or entry["path"] <= previous:
            raise ValueError("snapshot store paths are unsafe, duplicated or unordered")
        previous = entry["path"]
        if type(entry["nar_size"]) is not int or not 0 < entry["nar_size"] <= 64 * 1024**3:
            raise ValueError("snapshot NAR size is not positive and finite")
        if not re.fullmatch(r"[0-9a-f]{64}", str(entry["nar_sha256"])):
            raise ValueError("snapshot NAR lacks complete content custody")
    for key, name in (("database", "database.sqlite"), ("schema_file", "schema")):
        if (type(manifest[key]) is not dict or set(manifest[key]) != {"file", "size", "sha256"}
                or manifest[key]["file"] != name):
            raise ValueError("snapshot control file is not the exact flat file")
    for entry in [manifest["database"], manifest["schema_file"], *entries]:
        if type(entry["size"]) is not int or not 0 < entry["size"] <= 64 * 1024**3:
            raise ValueError("snapshot payload size is not positive and finite")
        if not re.fullmatch(r"[0-9a-f]{64}", str(entry["sha256"])):
            raise ValueError("snapshot payload lacks complete content custody")
    return manifest


def seal_snapshot(directory: Path, destination: Path, expected_sha256: str, binding: dict[str, Any]) -> dict[str, Any]:
    # Authenticate the bounded manifest in memory before creating privileged
    # staging. Only an admitted envelope may quarantine and hash its flat files.
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    created = False
    try:
        manifest_fd = os.open("manifest.json", os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
        with os.fdopen(manifest_fd, "rb") as source:
            before = os.fstat(source.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > MAX_MANIFEST:
                raise ValueError("snapshot manifest is linked, non-ordinary or oversized")
            content = source.read(MAX_MANIFEST + 1)
            after = os.fstat(source.fileno())
            if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns
            ):
                raise ValueError("snapshot manifest changed during custody")
        manifest = validate_manifest(content, expected_sha256, binding)
        entries = [manifest["database"], manifest["schema_file"], *manifest["paths"]]
        if set(os.listdir(fd)) != {"manifest.json", *(entry["file"] for entry in entries)}:
            raise ValueError("snapshot directory has missing or unexpected payloads")
        destination.mkdir(mode=0o700)
        created = True
        (destination / "manifest.json").write_bytes(content)
        for entry in entries:
            name = entry["file"]
            source_fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
            with os.fdopen(source_fd, "rb") as source:
                before = os.fstat(source.fileno())
                if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                    raise ValueError("snapshot refuses linked or non-ordinary transport files")
                digest, size = hashlib.sha256(), 0
                with (destination / name).open("xb") as target:
                    while chunk := source.read(CHUNK):
                        size += len(chunk)
                        if size > entry["size"]:
                            raise ValueError("snapshot payload exceeds its attested byte size")
                        digest.update(chunk)
                        target.write(chunk)
                after = os.fstat(source.fileno())
                if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                    after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns
                ):
                    raise ValueError("snapshot payload changed during custody")
                if size != entry["size"] or digest.hexdigest() != entry["sha256"]:
                    raise ValueError("snapshot payload differs from its attested bytes")
        return manifest
    except BaseException:
        if created:
            shutil.rmtree(destination)  # Only the fresh private quarantine.
        raise
    finally:
        os.close(fd)


def restore(
    directory: Path, expected_sha256: str, nix: Path, store_binary: Path, binding: dict[str, Any],
) -> dict[str, Any]:
    from infrastructure.reporting.native_document_preparation import _NIX_OPTIONS

    stage = DB.parent / ("template-nix-snapshot-" + uuid.uuid4().hex)
    manifest = seal_snapshot(directory, stage, expected_sha256, binding)
    database = _db_info(stage / "database.sqlite")
    expected_paths = [
        (entry["path"], "sha256:" + entry["nar_sha256"], entry["nar_size"]) for entry in manifest["paths"]
    ]
    if database["paths"] != expected_paths or database["logical_sha256"] != manifest["database_logical_sha256"]:
        raise ValueError("snapshot NAR roster differs from its complete genuine database")
    with _store_lock():
        current = _db_info(DB / "db.sqlite")
        if (current["nonempty"] or current["schema"] != database["schema"]
                or _sha(DB / "schema") != manifest["schema_file"]["sha256"]):
            raise ValueError("snapshot refuses a nonempty or incompatible destination database")
        if any(
            path.name != ".links" or not path.is_dir() or path.is_symlink() or any(path.iterdir())
            for path in STORE.iterdir()
        ):
            raise ValueError("snapshot refuses a nonempty or linked destination store")
        for entry in manifest["paths"]:
            if os.path.lexists(entry["path"]):
                raise ValueError("snapshot refuses to overwrite a store path")
            digest, size = hashlib.sha256(), 0
            with gzip.open(stage / entry["file"], "rb") as decoded:
                with subprocess.Popen([str(store_binary), "--restore", entry["path"]], env=CHILD_ENV,
                                      stdin=subprocess.PIPE) as process:
                    assert process.stdin is not None
                    try:
                        while chunk := decoded.read(CHUNK):
                            size += len(chunk)
                            if size > entry["nar_size"]:
                                raise ValueError("snapshot decoded NAR exceeds its attested registration")
                            digest.update(chunk)
                            process.stdin.write(chunk)
                    finally:
                        process.stdin.close()
                    if process.wait() != 0:
                        raise ValueError(f"original Nix restore failed: {entry['path']}")
            if size != entry["nar_size"] or digest.hexdigest() != entry["nar_sha256"]:
                raise ValueError("snapshot decoded NAR differs from its genuine registration")
            _canonical_metadata(Path(entry["path"]))
        _backup(stage / "database.sqlite", DB / "db.sqlite", standalone=False)
        if _db_info(DB / "db.sqlite")["logical_sha256"] != database["logical_sha256"]:
            raise ValueError("snapshot restoration changed genuine registration or trust metadata")
    subprocess.run([str(nix), *_NIX_OPTIONS, "--store", "local", "store", "verify", "--all"],
                   env=CHILD_ENV, check=True)
    shutil.rmtree(stage)  # Only this process's newly created root-private copy.
    return {"manifest_sha256": expected_sha256, "registered_paths": len(expected_paths),
            "original_trust_metadata_preserved": True, "preparation_DATA_only": True}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("capture", "restore"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--nix-binary", required=True, type=Path)
    parser.add_argument("--manifest-sha256", default="")
    arguments = parser.parse_args()
    nix = arguments.nix_binary.absolute()
    store_binary = _root_store(nix)
    binding = _binding(nix)
    if arguments.operation == "capture":
        if arguments.manifest_sha256:
            parser.error("capture cannot adopt an existing manifest")
        result = capture(arguments.directory.absolute(), store_binary, binding)
    else:
        if not re.fullmatch(r"[0-9a-f]{64}", arguments.manifest_sha256):
            parser.error("restore requires the exact same-run producer manifest SHA-256")
        result = restore(arguments.directory.absolute(), arguments.manifest_sha256, nix, store_binary, binding)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
