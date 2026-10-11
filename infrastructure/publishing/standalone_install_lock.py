"""Strict byte-preserving conversion of admitted checkout providers to Git pins."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import tomllib
from typing import Any

ROOT_PACKAGE = "research-project-template"
META_PACKAGE = "template-literature-meta-analysis"
PROVIDER_PATHS = {ROOT_PACKAGE: "../../..", META_PACKAGE: "../template_literature_meta_analysis"}
PROVIDER_URLS = {
    ROOT_PACKAGE: "https://github.com/docxology/template",
    META_PACKAGE: "https://github.com/docxology/template_literature_meta_analysis",
}


def normalized_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _path_matches(value: Any, package: str) -> bool:
    return isinstance(value, str) and value.rstrip("/") == PROVIDER_PATHS[package]


def _package_blocks(text: str) -> dict[str, str]:
    parts = re.split(r"(?m)(?=^\[\[package\]\]$)", text)
    blocks = {}
    for part in parts[1:]:
        package = tomllib.loads(part)["package"][0]
        name = normalized_name(package["name"])
        if name in blocks:
            raise ValueError("projection refuses duplicate locked package identities")
        blocks[name] = part
    return blocks


def third_party_lock_sha256(content: bytes, project_name: str) -> str:
    blocks = _package_blocks(content.decode("utf-8"))
    retained = {
        key: value for key, value in blocks.items() if key not in {*PROVIDER_PATHS, normalized_name(project_name)}
    }
    return hashlib.sha256(json.dumps(retained, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def checkout_providers(metadata: bytes, lock: bytes) -> dict[str, str]:
    """Require complete declarations and refuse unknown external checkout shapes."""
    project = tomllib.loads(metadata.decode("utf-8"))
    sources = project.get("tool", {}).get("uv", {}).get("sources", {})
    if not isinstance(sources, dict):
        raise ValueError("projection UV sources must be a table")
    selected = {}
    for raw_name, source in sources.items():
        if not isinstance(source, dict):
            raise ValueError("projection refuses conditional or non-table UV sources")
        if "path" not in source:
            continue
        name = normalized_name(raw_name)
        if (
            name not in PROVIDER_PATHS
            or raw_name != name
            or name in selected
            or set(source) != {"path", "editable"}
            or source["editable"] is not True
            or not _path_matches(source["path"], name)
        ):
            raise ValueError("projection refuses an undeclared external checkout provider")
        selected[name] = source["path"]
    packages = tomllib.loads(lock.decode("utf-8")).get("package", [])
    if not packages:
        raise ValueError("projection requires a genuine nonempty UV lock")
    own = normalized_name(project["project"]["name"])
    found = {}
    for package in packages:
        name = normalized_name(package["name"])
        source = package.get("source", {})
        if "editable" in source or "directory" in source or "virtual" in source:
            if name == own and source in ({"editable": "."}, {"virtual": "."}):
                continue
            if name not in selected or source.keys() != {"editable"} or not _path_matches(source["editable"], name):
                raise ValueError("projection lock contains an unadmitted local provider")
            found[name] = package["version"]
    if found.keys() != selected.keys():
        raise ValueError("projection checkout declarations and locked providers disagree")
    return found


def _replace_rows(text: str, pins: dict[str, dict[str, str]], *, metadata: bool) -> str:
    lines = text.splitlines(keepends=True)
    in_sources = False
    current_package = ""
    for index, line in enumerate(lines):
        if metadata and line.startswith("["):
            in_sources = line.strip() == "[tool.uv.sources]"
        if not metadata and line.startswith("[[package]]"):
            current_package = ""
        if not metadata and not current_package and re.match(r"^name\s*=", line):
            current_package = normalized_name(tomllib.loads(line)["name"])
        if metadata and in_sources and "=" in line and not line.lstrip().startswith("#"):
            key = normalized_name(line.split("=", 1)[0].strip().strip('"'))
            if key in pins:
                source = {"git": pins[key]["repository"], "rev": pins[key]["commit"]}
                ending = "\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else ""
                lines[index] = (
                    f"{line.split('=', 1)[0]}= {{ git = {json.dumps(source['git'])}, "
                    f"rev = {json.dumps(source['rev'])} }}{ending}"
                )
        elif not metadata and "editable" in line:
            row_name = re.search(r'\bname\s*=\s*"([^"]+)"', line)
            key = (
                normalized_name(row_name[1]) if row_name else current_package if re.match(r"^source\s*=", line) else ""
            )
            if key in pins:
                git = f"{pins[key]['repository']}?rev={pins[key]['commit']}"
                if row_name is None:
                    git += f"#{pins[key]['commit']}"
                lines[index], count = re.subn(r'\beditable\s*=\s*"[^"]+"', f"git = {json.dumps(git)}", line)
                if count != 1:
                    raise ValueError("projection local-provider row is ambiguous")
    return "".join(lines)


def transform_install_files(metadata: bytes, lock: bytes, pins: dict[str, dict[str, str]]) -> tuple[bytes, bytes, str]:
    """Only admitted source fields may change; every other TOML fact/lock block stays exact."""
    providers = checkout_providers(metadata, lock)
    if providers.keys() != pins.keys() or any(providers[name] != pin["version"] for name, pin in pins.items()):
        raise ValueError("projection provider package versions differ from the original lock")
    before_metadata = tomllib.loads(metadata.decode("utf-8"))
    expected_metadata = copy.deepcopy(before_metadata)
    for name, pin in pins.items():
        expected_metadata["tool"]["uv"]["sources"][name] = {"git": pin["repository"], "rev": pin["commit"]}
    expected_lock = tomllib.loads(lock.decode("utf-8"))

    def replace_references(value: Any) -> None:
        if isinstance(value, dict):
            name = normalized_name(value.get("name", ""))
            if "editable" in value:
                if name not in pins or not _path_matches(value["editable"], name):
                    raise ValueError("projection metadata includes an unadmitted local reference")
                value.pop("editable")
                value["git"] = f"{pins[name]['repository']}?rev={pins[name]['commit']}"
            for child in value.values():
                replace_references(child)
        elif isinstance(value, list):
            for child in value:
                replace_references(child)

    for package in expected_lock["package"]:
        name = normalized_name(package["name"])
        if name in pins:
            pin = pins[name]
            package["source"] = {"git": f"{pin['repository']}?rev={pin['commit']}#{pin['commit']}"}
        if "metadata" in package:
            replace_references(package["metadata"])
    transformed_metadata = _replace_rows(metadata.decode("utf-8"), pins, metadata=True).encode("utf-8")
    transformed_lock = _replace_rows(lock.decode("utf-8"), pins, metadata=False).encode("utf-8")
    if (
        tomllib.loads(transformed_metadata.decode("utf-8")) != expected_metadata
        or tomllib.loads(transformed_lock.decode("utf-8")) != expected_lock
    ):
        raise ValueError("projection changed facts outside its precise source-field contract")
    own = normalized_name(before_metadata["project"]["name"])
    third_party = third_party_lock_sha256(lock, own)
    if third_party_lock_sha256(transformed_lock, own) != third_party:
        raise ValueError("projection changed third-party locked package bytes")
    return transformed_metadata, transformed_lock, third_party
