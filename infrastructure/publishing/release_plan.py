"""Reviewable patch-release metadata plans; never publication authority.

No resolver runs here. Parsed before/after objects must differ only in the
root version, exact SDK requirements and exemplar compatibility bindings.
Exemplar own versions, provider declarations and third-party locks stay exact.
"""

from __future__ import annotations

import copy
import ast
import hashlib
import json
import os
import re
import stat
import subprocess
import tomllib
from pathlib import Path
from typing import Any

import yaml
from yaml.nodes import MappingNode, ScalarNode
from yaml.tokens import AliasToken

from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.publishing.root_release_contract import validate_runtime_version_provider

SCHEMA = "template-coordinated-release-plan-v1"
CONTRACT = "infrastructure/config/release-plan-contract.json"
ROOT_PACKAGE = "research-project-template"
MAX_BYTES = 16 * 1024 * 1024


def canonical(value: object) -> bytes:
    """Stable finite review bytes, including one terminal newline."""
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def git(root: Path, *arguments: str) -> bytes:
    """Use only the nominated repository, without inherited Git routing."""
    environment = {"PATH": os.defpath, "LC_ALL": "C", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
    return subprocess.check_output(
        ["git", "-c", "core.fsmonitor=false", "-C", str(root), *arguments],
        env=environment,
        stderr=subprocess.PIPE,
        timeout=30,
    )


def read_input(root: Path, relative: str) -> tuple[bytes, int]:
    """Refuse aliases and unsupported paths before bounded metadata reads."""
    if Path(relative).as_posix() != relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError("release input must be a canonical relative path")
    path = root / relative
    for item in (root, *reversed(path.parents[:-1]), path):
        if item.is_symlink():
            raise ValueError("release inputs cannot contain symlink components")
    before = path.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_BYTES or stat.S_IMODE(before.st_mode) > 0o777:
        raise ValueError("release input is not a bounded regular file")
    body = read_bytes_confined(root, path, max_bytes=MAX_BYTES)
    after = path.stat()
    if (before.st_dev, before.st_ino, before.st_mtime_ns, before.st_ctime_ns, before.st_mode) != (
        after.st_dev,
        after.st_ino,
        after.st_mtime_ns,
        after.st_ctime_ns,
        after.st_mode,
    ) or len(body) != before.st_size:
        raise ValueError("release input changed during observation")
    return body, stat.S_IMODE(before.st_mode)


def _field(text: str, section: str, key: str, old: str, new: str) -> str:
    def replacement(match: re.Match[str]) -> str:
        return match[1] + match[2] + new + match[2]

    chunks = re.split(r"(?m)(?=^\[)", text)
    found = 0
    for index, chunk in enumerate(chunks):
        if chunk.splitlines()[:1] == [f"[{section}]"]:
            pattern = rf'(?m)^({re.escape(key)}\s*=\s*)(["\']){re.escape(old)}\2(?=\s*(?:#.*)?$)'
            chunks[index], count = re.subn(pattern, replacement, chunk)
            found += count
    if found != 1:
        raise ValueError(f"expected one literal [{section}].{key} at the old version")
    return "".join(chunks)


def _pins(value: Any, old: str, new: str) -> Any:
    if isinstance(value, dict):
        return {key: _pins(child, old, new) for key, child in value.items()}
    if isinstance(value, list):
        return [_pins(child, old, new) for child in value]
    if isinstance(value, str) and value.startswith(ROOT_PACKAGE) and value != ROOT_PACKAGE:
        if value != f"{ROOT_PACKAGE}=={old}":
            raise ValueError("SDK requirement must be the exact current root pin")
        return f"{ROOT_PACKAGE}=={new}"
    return value


def _metadata(body: bytes, scope: str, old: str, new: str) -> bytes:
    text = body.decode()
    before = tomllib.loads(text)
    expected = _pins(before, old, new)
    if scope == "root":
        if before["project"]["name"] != ROOT_PACKAGE or before["project"]["version"] != old:
            raise ValueError("root metadata does not identify the expected current package")
        expected["project"]["version"] = new
        text = _field(text, "project", "version", old, new)
    else:
        if before.get("tool", {}).get("template", {}).get("platform_version") != old:
            raise ValueError("exemplar compatibility binding differs from current SDK")
        expected["tool"]["template"]["platform_version"] = new
        text = _field(text, "tool.template", "platform_version", old, new)
    text = text.replace(f'"{ROOT_PACKAGE}=={old}"', f'"{ROOT_PACKAGE}=={new}"')
    text = text.replace(f"'{ROOT_PACKAGE}=={old}'", f"'{ROOT_PACKAGE}=={new}'")
    if tomllib.loads(text) != expected:
        raise ValueError("metadata transformation changed fields outside the admitted release delta")
    return text.encode()


def _lock(body: bytes, old: str, new: str, root: Path, base: Path) -> bytes:
    text = body.decode()
    before = tomllib.loads(text)
    expected = copy.deepcopy(before)
    roots = [row for row in expected["package"] if row["name"] == ROOT_PACKAGE]
    if len(roots) > 1:
        raise ValueError("lock contains ambiguous root packages")
    for row in roots:
        if row["version"] != old or set(row.get("source", {})) != {"editable"}:
            raise ValueError("lock root must be the current local editable SDK")
        if Path(os.path.abspath(base / row["source"]["editable"])) != root:
            raise ValueError("lock root editable path escapes the canonical SDK")
        row["version"] = new
    chunks = re.split(r"(?m)(?=^\[\[package\]\]$)", text)
    for index, chunk in enumerate(chunks):
        if re.search(rf'(?m)^name = "{ROOT_PACKAGE}"$', chunk):
            chunks[index] = re.sub(rf'(?m)^version = "{re.escape(old)}"$', f'version = "{new}"', chunk, count=1)
    result = "".join(chunks)
    if tomllib.loads(result) != expected:
        raise ValueError("lock transformation changed a non-root record or unsupported version reference")
    return result.encode()


def _publication(body: bytes, old: str, new: str) -> bytes:
    """Replace one literal publication SDK scalar, preserving all other YAML."""
    text = body.decode()
    if any(isinstance(token, AliasToken) for token in yaml.scan(text, Loader=yaml.SafeLoader)):
        raise ValueError("publication metadata cannot contain YAML aliases")
    tree = yaml.compose(text, Loader=yaml.SafeLoader)

    def unique_field(node: object, key: str) -> object:
        matches = (
            [value for field, value in node.value if isinstance(field, ScalarNode) and field.value == key]
            if isinstance(node, MappingNode)
            else []
        )
        if len(matches) != 1:
            raise ValueError(f"publication metadata requires one explicit {key} binding")
        return matches[0]

    publication = unique_field(tree, "publication")
    version = unique_field(publication, "platform_version")
    if not isinstance(version, ScalarNode) or version.value != old:
        raise ValueError("publication platform binding differs from current SDK")
    token = text[version.start_mark.index : version.end_mark.index]
    if token not in (old, f'"{old}"', f"'{old}'"):
        raise ValueError("publication platform binding must be a unique literal scalar")
    before = yaml.safe_load(text)
    expected = copy.deepcopy(before)
    expected["publication"]["platform_version"] = new
    replacement = token.replace(old, new)
    result = text[: version.start_mark.index] + replacement + text[version.end_mark.index :]
    if yaml.safe_load(result) != expected:
        raise ValueError("publication transformation changed fields outside the SDK binding")
    return result.encode()


def _provider_order(root: Path, metadata: dict[str, dict[str, Any]]) -> list[str]:
    locations = {root: "root", **{root / "projects" / scope: scope for scope in PUBLIC_PROJECT_NAMES}}

    def normalize(value: str) -> str:
        return re.sub(r"[-_.]+", "-", value).lower()

    edges: dict[str, list[str]] = {}
    for scope, payload in metadata.items():
        base = root if scope == "root" else root / "projects" / scope
        providers = []
        for package, declaration in payload.get("tool", {}).get("uv", {}).get("sources", {}).items():
            if not isinstance(declaration, dict) or "path" not in declaration:
                raise ValueError("release plan requires explicit local provider declarations")
            location = Path(os.path.abspath(base / declaration["path"]))
            provider = locations.get(location)
            if provider is None or normalize(metadata[provider]["project"]["name"]) != normalize(package):
                raise ValueError("local provider is outside the canonical public package roster")
            providers.append(provider)
        edges[scope] = sorted(set(providers))
    order: list[str] = []
    visiting: set[str] = set()

    def visit(scope: str) -> None:
        if scope in visiting:
            raise ValueError("release provider graph contains a cycle")
        if scope not in order:
            visiting.add(scope)
            for provider in edges[scope]:
                visit(provider)
            visiting.remove(scope)
            order.append(scope)

    for scope in ("root", *PUBLIC_PROJECT_NAMES):
        visit(scope)
    return order


def build_release_plan(root: Path, target_version: str, *, expected_current: str) -> dict[str, Any]:
    """Read-only next-patch plan; unknown scopes and legacy roots fail closed."""
    return _prepare(root, target_version, expected_current)[0]


def _prepare(root: Path, target: str, old: str) -> tuple[dict[str, Any], dict[str, bytes]]:
    root = root.absolute()
    if git(root, "rev-parse", "--show-toplevel").decode().strip() != str(root):
        raise ValueError("release plan needs its actual Git top-level directory")
    commit = git(root, "rev-parse", "HEAD").decode().strip()
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("release plan needs an exact committed base")
    versions = [
        tuple(map(int, v.split(".")))
        for v in (old, target)
        if re.fullmatch(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)", v)
    ]
    if len(versions) != 2 or versions[0][0] < 4 or versions[1] != (*versions[0][:2], versions[0][2] + 1):
        raise ValueError("release plan supports root 4+ exact next patch versions only")
    fixed = [CONTRACT, "infrastructure/_version.py", "infrastructure/project/public_scope.py"]
    scopes = ("root", *PUBLIC_PROJECT_NAMES)
    inputs: dict[str, bytes] = {}
    modes = {}
    for path in [
        *fixed,
        *(
            prefix + name
            for scope in scopes
            for prefix in ["" if scope == "root" else f"projects/{scope}/"]
            for name in ("pyproject.toml", "uv.lock")
        ),
        *(f"projects/{scope}/manuscript/config.yaml" for scope in PUBLIC_PROJECT_NAMES),
    ]:
        inputs[path], modes[path] = read_input(root, path)
        if git(root, "ls-files", "--error-unmatch", "--", path).decode().strip() != path:
            raise ValueError("release input must be tracked at its exact path")
    contract = json.loads(inputs[CONTRACT])
    if contract != CONTRACT_VALUE:
        raise ValueError("source-owned release-plan contract differs from this implementation")
    roster_nodes = [
        node.value
        for node in ast.parse(inputs["infrastructure/project/public_scope.py"]).body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "PUBLIC_PROJECT_NAMES"
    ]
    if len(roster_nodes) != 1 or roster_nodes[0] is None or ast.literal_eval(roster_nodes[0]) != PUBLIC_PROJECT_NAMES:
        raise ValueError("selected implementation and Source public rosters differ")
    validate_runtime_version_provider(inputs["infrastructure/_version.py"].decode())
    metadata: dict[str, dict[str, Any]] = {}
    transformed = {}
    packages = []
    for scope in scopes:
        prefix = "" if scope == "root" else f"projects/{scope}/"
        path = prefix + "pyproject.toml"
        payload = metadata[scope] = tomllib.loads(inputs[path].decode())
        transformed[path] = _metadata(inputs[path], scope, old, target)
        lock = prefix + "uv.lock"
        transformed[lock] = _lock(
            inputs[lock], old, target, root, root if scope == "root" else root / "projects" / scope
        )
        if scope != "root":
            publication = prefix + "manuscript/config.yaml"
            transformed[publication] = _publication(inputs[publication], old, target)
        packages.append(
            {
                "scope": scope,
                "package": payload["project"]["name"],
                "own_version": payload["project"]["version"],
                "sdk_before": old,
                "sdk_after": target,
            }
        )
    # Read back every held byte before returning a plan; no filesystem cache.
    if git(root, "rev-parse", "HEAD").decode().strip() != commit or any(
        read_input(root, path) != (body, modes[path]) for path, body in inputs.items()
    ):
        raise ValueError("release inputs changed during planning")
    plan = {
        "schema_version": SCHEMA,
        "role": "metadata-preparation-only",
        "base_commit": commit,
        "root_before": old,
        "root_after": target,
        "public_roster": list(PUBLIC_PROJECT_NAMES),
        "packages": packages,
        "provider_order": _provider_order(root, metadata),
        "inputs": [
            {"path": path, "sha256": sha256(body), "mode": modes[path]} for path, body in sorted(inputs.items())
        ],
        "changes": [
            {"path": path, "before_sha256": sha256(inputs[path]), "after_sha256": sha256(body)}
            for path, body in sorted(transformed.items())
            if body != inputs[path]
        ],
        "required_followup": contract["required_followup"],
    }
    return plan, transformed


CONTRACT_VALUE = {
    "schema_version": "template-release-plan-contract-v1",
    "root_package": ROOT_PACKAGE,
    "version_rule": "root-4+-next-patch; preserve-exemplar-own-versions",
    "public_roster_authority": "infrastructure.project.public_scope.PUBLIC_PROJECT_NAMES",
    "lock_rule": "root-editable-version-only; no-resolution-or-third-party-delta",
    "publication_rule": "all-canonical-publication-platform-bindings-only; preserve-intended-and-own-versions",
    "required_followup": [
        "locked-offline-metadata-checks",
        "source-bound-coverage-and-publication-validation",
        "all-public-wheel-admission",
        "fresh-final-source-census-and-policy-admission",
        "exact-main-all-29-obligations",
        "independent-installed-release-handoff",
        "explicit-GitHub-publication",
    ],
}


def check_release_plan(root: Path, plan: dict[str, Any]) -> None:
    """Reject altered, stale, expanded or unknown-scope review plans."""
    if plan != build_release_plan(root, plan.get("root_after", ""), expected_current=plan.get("root_before", "")):
        raise ValueError("reviewed release plan differs from the actual bounded transaction")
