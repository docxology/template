"""Bind root release assets to the exact admitted installed wheel and source."""

from __future__ import annotations

import argparse
import gzip
import os
import re
import hashlib
import json
import tarfile
import tomllib
from email.parser import BytesParser
from io import BytesIO
from pathlib import Path
from typing import Any

from infrastructure.core.execution_boundary import run_bounded_subprocess
from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined
from infrastructure.project.public_capabilities import CANONICAL_CI_PYTHON_VERSIONS
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.publishing.root_release_contract import validate_root_release_tag
from infrastructure.reporting.readiness_receipts import public_source_paths, source_fingerprint
from infrastructure.reporting.release_readiness_profile import required_profile
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader, json_object_from_bytes
from infrastructure.reporting.release_readiness_validators import validate_acceptance

_LIMIT = 64 * 1024 * 1024


def admit_sdist_bytes(root: Path, content: bytes, *, reader: SnapshotReader | None = None) -> None:
    """Require a bounded source archive to contain exactly the authored SDK."""
    if not content or len(content) > _LIMIT:
        raise ValueError("root sdist exceeds the bounded archive contract")
    reader = reader or SnapshotReader(root)
    root = reader.root
    project = tomllib.loads(reader.read("pyproject.toml").content.decode())["project"]
    expected = {
        path.relative_to(root).as_posix(): reader.read(path.relative_to(root).as_posix()).sha256
        for path in public_source_paths(root)
        if path.is_relative_to(root / "infrastructure")
    }
    expected.update(
        {name: reader.read(name).sha256 for name in ("README.md", "LICENSE", "pyproject.toml", ".gitignore")}
    )
    with gzip.GzipFile(fileobj=BytesIO(content)) as compressed:
        expanded = compressed.read(_LIMIT + 1)
    if len(expanded) > _LIMIT:
        raise ValueError("root sdist exceeds the decompressed byte ceiling")
    with tarfile.open(fileobj=BytesIO(expanded), mode="r:") as archive:
        members: list[tarfile.TarInfo] = []
        seen: set[str] = set()
        for member in archive:
            if member.name in seen or len(members) >= 10000:
                raise ValueError("root sdist member inventory is duplicated or oversized")
            seen.add(member.name)
            members.append(member)
        if (
            not members
            or sum(member.size for member in members) > _LIMIT
            or any(
                not (member.isfile() or member.isdir())
                or member.size < 0
                or Path(member.name).is_absolute()
                or ".." in Path(member.name).parts
                or "\\" in member.name
                or "\0" in member.name
                or member.name != Path(member.name).as_posix()
                for member in members
            )
        ):
            raise ValueError("root sdist has unsafe or oversized members")
        prefixes = {Path(member.name).parts[0] for member in members}
        if len(prefixes) != 1:
            raise ValueError("root sdist requires exactly one package directory")
        prefix = next(iter(prefixes)) + "/"
        if prefix != project["name"].replace("-", "_") + "-" + project["version"] + "/":
            raise ValueError("root sdist package directory differs from the candidate")
        actual = {}
        for member in members:
            if member.isfile():
                stream = archive.extractfile(member)
                if stream is None:
                    raise ValueError("root sdist member is unreadable")
                actual[member.name.removeprefix(prefix)] = stream.read()
        metadata_bytes = actual.pop("PKG-INFO", b"")
        fields = BytesParser().parsebytes(metadata_bytes)
        if (
            fields.get_all("Name") != [project["name"]]
            or fields.get_all("Version") != [project["version"]]
            or fields.get_all("Requires-Python") != [project["requires-python"]]
        ):
            raise ValueError("root sdist metadata differs from the candidate")
        if {name: hashlib.sha256(value).hexdigest() for name, value in actual.items()} != expected:
            raise ValueError("root sdist omitted, changed or invented authored source members")
    if not reader.unchanged():
        raise ValueError("root sdist source changed during admission")


def _tested_wheel(root: Path, installed_receipt: Path, reader: SnapshotReader) -> tuple[str, bytes, dict[str, str]]:
    relative = installed_receipt.absolute().relative_to(root).as_posix()
    receipt = reader.read(relative)
    report = receipt.json_object()
    fingerprint = source_fingerprint(root)
    matrix = report.get("installed_matrix", {})
    expected_cells = len(CANONICAL_CI_PYTHON_VERSIONS) * (len(PUBLIC_PROJECT_NAMES) + 1)
    if (
        type(report.get("exit_code")) is not int
        or report["exit_code"] != 0
        or report.get("source_fingerprint") != fingerprint
        or matrix.get("matrix_complete") is not True
        or matrix.get("source_current") is not True
        or matrix.get("expected_cells") != expected_cells
        or matrix.get("observed_cells") != expected_cells
        or matrix.get("counts") != {"pass": expected_cells, "fail": 0, "blocked": 0}
    ):
        raise ValueError("root release requires the complete current installed matrix")
    if report.get("roster") != list(PUBLIC_PROJECT_NAMES):
        raise ValueError("root installed matrix roster is incomplete")
    profile, faults = required_profile(root, reader, fingerprint)
    if faults:
        raise ValueError("root release source-owned acceptance profile is invalid")
    installed_requirements = [item for item in profile if item.kind == "installed"]
    if {item.scope for item in installed_requirements} != {"root", *PUBLIC_PROJECT_NAMES}:
        raise ValueError("root installed matrix source scope is incomplete")
    all_cells = []
    root_payload = None
    for requirement in installed_requirements:
        binding = report["gates"][requirement.id]
        gate = reader.read(binding["artifact"])
        if binding.get("status") != "pass" or gate.sha256 != binding.get("artifact_sha256"):
            raise ValueError("installed gate differs from its original receipt")
        payload = gate.json_object()
        expected = {
            "schema_version": "template-required-acceptance-v1",
            "gate": requirement.id,
            "status": "pass",
            "platform_version": requirement.platform_version,
            "version": requirement.version,
            "scope": requirement.scope,
            "source_fingerprint": fingerprint,
            "source_identity": requirement.source_identity,
        }
        if requirement.scope != "root":
            expected["deliverables_identity"] = requirement.deliverables_identity
        if any(payload.get(key) != value for key, value in expected.items()):
            raise ValueError("installed gate source/version/scope identity differs from the candidate")
        validate_acceptance(requirement, payload, reader)
        all_cells.extend(payload["details"]["runtime_observations"])
        if requirement.scope == "root":
            root_payload = payload
    results = matrix.get("results")
    if not isinstance(results, list) or len(results) != expected_cells or len(all_cells) != expected_cells:
        raise ValueError("installed matrix omits its original runtime cells")
    identities = [(cell["scope"], cell["python_version"]) for cell in all_cells]
    if (
        len(set(identities)) != expected_cells
        or set(identities)
        != {(scope, minor) for scope in ("root", *PUBLIC_PROJECT_NAMES) for minor in CANONICAL_CI_PYTHON_VERSIONS}
        or sorted(results, key=lambda cell: (cell["scope"], cell["python_version"]))
        != sorted(all_cells, key=lambda cell: (cell["scope"], cell["python_version"]))
    ):
        raise ValueError("installed matrix cells differ from the independently admitted originals")
    if root_payload is None:
        raise ValueError("root installed gate is missing")
    payload = root_payload
    cells = [cell for cell in payload["details"]["runtime_observations"] if cell["python_version"] == "3.14"]
    if len(cells) != 1 or cells[0].get("status") != "pass":
        raise ValueError("root release requires one original passing 3.14 installed cell")
    wheel_binding = cells[0]["details"]["wheel_artifact"]
    wheel = reader.read(wheel_binding["path"])
    if wheel.sha256 != wheel_binding["sha256"]:
        raise ValueError("root installed wheel changed after execution")
    return (
        wheel.path.name,
        wheel.content,
        {"path": relative, "sha256": receipt.sha256, "wheel_path": wheel.relative, "wheel_sha256": wheel.sha256},
    )


def _source_commit(root: Path) -> str:
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update(GIT_OPTIONAL_LOCKS="0", GIT_NO_REPLACE_OBJECTS="1")
    result = run_bounded_subprocess(
        ["git", "-c", "core.fsmonitor=false", "rev-parse", "HEAD"], cwd=root, env=environment, timeout=30
    )
    commit = result.stdout.strip()
    if result.returncode != 0 or re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", commit) is None:
        raise ValueError("root release requires its actual Git revision")
    return commit


def _binding(name: str, content: bytes) -> dict[str, Any]:
    return {"name": name, "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}


def admit_root_release_artifacts(root: Path, tag: str, installed_receipt: Path) -> tuple[Path, str]:
    """Publish the already executed wheel; independently bind the final sdist."""
    root = root.resolve()
    version = validate_root_release_tag(root, tag)
    reader = SnapshotReader(root)
    name, wheel, installed = _tested_wheel(root, installed_receipt, reader)
    directory = root / "dist"
    entries = list(directory.iterdir())
    if len(entries) != 1 or entries[0].suffixes[-2:] != [".tar", ".gz"]:
        raise ValueError("root asset admission requires one fresh sdist and no preexisting wheel or manifest")
    sdist = entries[0]
    source_archive = read_bytes_confined(root, sdist, max_bytes=_LIMIT)
    admit_sdist_bytes(root, source_archive, reader=reader)
    image = reader.read(f"docs/releases/template-{tag}-overview.png")
    manifest = {
        "schema_version": "template-root-release-assets-v1",
        "tag": tag,
        "version": version,
        "source_fingerprint": source_fingerprint(root),
        "source_commit": _source_commit(root),
        "installed_receipt": installed,
        "assets": [
            _binding(name, wheel),
            _binding(sdist.name, source_archive),
            _binding(image.path.name, image.content),
        ],
    }
    if not reader.unchanged():
        raise ValueError("root release inputs changed during final asset admission")
    atomic_write_bytes_confined(root, directory / name, wheel, mode=0o400)
    manifest_path = directory / f"template-{tag}-artifacts.json"
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    atomic_write_bytes_confined(root, manifest_path, manifest_bytes, mode=0o400)
    verify_root_release_artifacts(root, tag, installed_receipt, manifest_sha256=manifest_sha256)
    return manifest_path, manifest_sha256


def verify_root_release_artifacts(
    root: Path, tag: str, installed_receipt: Path, *, manifest_sha256: str, retrieved: Path | None = None
) -> None:
    """Recheck the same admitted local assets and optional retrieved release bytes."""
    root = root.resolve()
    validate_root_release_tag(root, tag)
    reader = SnapshotReader(root)
    name, wheel, installed = _tested_wheel(root, installed_receipt, reader)
    directory = root / "dist"
    manifest_name = f"template-{tag}-artifacts.json"
    manifest_bytes = read_bytes_confined(root, directory / manifest_name, max_bytes=1024 * 1024)
    if (
        not isinstance(manifest_sha256, str)
        or re.fullmatch(r"[0-9a-f]{64}", manifest_sha256) is None
        or hashlib.sha256(manifest_bytes).hexdigest() != manifest_sha256
    ):
        raise ValueError("root release manifest differs from its separately sealed admission hash")
    manifest = json_object_from_bytes(manifest_bytes)
    expected = manifest.get("assets", [])
    if (
        manifest.get("schema_version") != "template-root-release-assets-v1"
        or manifest.get("tag") != tag
        or manifest.get("version") != tag.removeprefix("v")
        or manifest.get("source_fingerprint") != source_fingerprint(root)
        or manifest.get("source_commit") != _source_commit(root)
        or manifest.get("installed_receipt") != installed
        or len(expected) != 3
        or expected[0] != _binding(name, wheel)
        or not isinstance(expected[1].get("name"), str)
        or not expected[1]["name"].endswith(".tar.gz")
        or expected[2].get("name") != f"template-{tag}-overview.png"
    ):
        raise ValueError("root release asset manifest differs from its admitted source and installed wheel")
    contents = [wheel]
    for index, item in enumerate(expected):
        filename = item["name"]
        if filename != Path(filename).name or "\\" in filename:
            raise ValueError("root release asset has an unsafe filename")
        path = root / "docs/releases" / filename if index == 2 else directory / filename
        content = read_bytes_confined(root, path, max_bytes=_LIMIT)
        if _binding(filename, content) != item:
            raise ValueError("root release asset changed after admission")
        if index == 1:
            admit_sdist_bytes(root, content, reader=reader)
        if index:
            contents.append(content)
    _verify_asset_files(root, manifest_name, manifest_bytes, expected, contents, retrieved=retrieved)
    if not reader.unchanged():
        raise ValueError("root release evidence changed during verification")


def _verify_asset_files(
    root: Path,
    manifest_name: str,
    manifest_bytes: bytes,
    expected: list[dict[str, Any]],
    contents: list[bytes],
    *,
    retrieved: Path | None = None,
) -> None:
    """Check actual local/retrieved files against independently held byte inputs.

    This leaf establishes file custody only. The public caller must first admit
    every original installed cell, source archive, version and sealed manifest.
    """
    directory = root / "dist"
    if len(expected) != 3 or len(contents) != 3 or manifest_name != Path(manifest_name).name:
        raise ValueError("root release requires its exact held asset inventory")
    if any(
        not isinstance(item.get("name"), str) or item["name"] != Path(item["name"]).name or "\\" in item["name"]
        for item in expected
    ):
        raise ValueError("root release asset has an unsafe filename")
    if {path.name for path in directory.iterdir()} != {manifest_name, expected[0]["name"], expected[1]["name"]}:
        raise ValueError("root dist contains assets outside the admitted inventory")
    if retrieved is not None:
        retrieved = retrieved.absolute()
        if {path.name for path in retrieved.iterdir()} != {manifest_name, *(item["name"] for item in expected)}:
            raise ValueError("retrieved release has missing or unexpected assets")
        if read_bytes_confined(retrieved, retrieved / manifest_name, max_bytes=1024 * 1024) != manifest_bytes:
            raise ValueError("retrieved release manifest differs from the admitted bytes")
        for item, content in zip(expected, contents, strict=True):
            if read_bytes_confined(retrieved, retrieved / item["name"], max_bytes=_LIMIT) != content:
                raise ValueError("retrieved release asset differs from the admitted bytes")
    if read_bytes_confined(root, directory / manifest_name, max_bytes=1024 * 1024) != manifest_bytes:
        raise ValueError("root release manifest changed during verification")
    for index, (item, content) in enumerate(zip(expected, contents, strict=True)):
        path = root / "docs/releases" / item["name"] if index == 2 else directory / item["name"]
        if read_bytes_confined(root, path, max_bytes=_LIMIT) != content:
            raise ValueError("root release asset changed during verification")


def main(argv: list[str] | None = None) -> int:
    """Admit, recheck, or authenticate retrieved assets without publishing."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--tag", required=True)
    parser.add_argument("--installed-receipt", type=Path, required=True)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--retrieved", type=Path)
    parser.add_argument("--manifest-sha256")
    args = parser.parse_args(argv)
    try:
        if args.verify or args.retrieved is not None:
            verify_root_release_artifacts(
                args.repo_root,
                args.tag,
                args.installed_receipt,
                manifest_sha256=args.manifest_sha256,
                retrieved=args.retrieved,
            )
        else:
            _path, digest = admit_root_release_artifacts(args.repo_root, args.tag, args.installed_receipt)
            print("manifest_sha256=" + digest)
    except (OSError, ValueError, KeyError, TypeError, StopIteration, tarfile.TarError) as exc:
        print(f"root release asset custody refused: {exc}")
        return 75
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["admit_root_release_artifacts", "admit_sdist_bytes", "main", "verify_root_release_artifacts"]
