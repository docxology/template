"""Versioned, opt-in installation projection separate from exact schema-2 exports."""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.publishing.publication_tree import (
    INVENTORY_NAME,
    _Budget,
    _file,
    _protected,
    _records,
    _root,
    copy_publication_source,
    publication_export_sha256,
)
from infrastructure.publishing.standalone_install_lock import (
    META_PACKAGE,
    PROVIDER_URLS,
    ROOT_PACKAGE,
    checkout_providers,
    normalized_name,
    transform_install_files,
)

PROJECTION_NAME = ".template-install-projection.json"
PROJECTION_SCHEMA = "template-standalone-install-projection/1"


@dataclass(frozen=True)
class GitInstallProvider:
    """A real prepared checkout at an existing full Git commit, never a future label."""

    checkout: Path
    commit: str


def _json(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _git(provider: GitInstallProvider, args: list[str]) -> str:
    from infrastructure.publishing.standalone_mirror import _git as actual_git

    return actual_git(args, provider.checkout).stdout


def _admit_provider(provider: GitInstallProvider, package: str, version: str) -> dict[str, str]:
    from infrastructure.publishing._standalone_provider_admission import _git_provider_closing, _git_provider_opening
    from infrastructure.publishing.standalone_mirror import _verify_committed

    checkout = provider.checkout.absolute()
    if checkout.resolve(strict=True) != checkout or not checkout.is_dir():
        raise ValueError("install provider must be a real no-follow checkout")
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", provider.commit):
        raise ValueError("install provider requires its existing full commit identity")
    repository = PROVIDER_URLS[package]
    _git_provider_opening(checkout, provider.commit, repository)
    content = read_bytes_confined(checkout, checkout / "pyproject.toml", max_bytes=4 * 1024 * 1024)
    metadata = tomllib.loads(content.decode("utf-8"))
    if normalized_name(metadata["project"]["name"]) != package or metadata["project"].get("version") != version:
        raise ValueError("install provider committed package identity/version disagrees with the source lock")
    header, path = _git(provider, ["ls-tree", "-z", provider.commit, "--", "pyproject.toml"]).rstrip("\0").split("\t")
    mode, kind, identity = header.split()
    if kind != "blob" or mode not in {"100644", "100755"}:
        raise ValueError("install provider metadata must be a committed regular file")
    _verify_committed(path, content, mode, {path: (mode, identity)})
    tree = _git_provider_closing(checkout, provider.commit)
    return {
        "package": package,
        "version": version,
        "repository": repository,
        "commit": provider.commit,
        "tree": tree,
        "metadata_sha256": hashlib.sha256(content).hexdigest(),
    }


def _assert_canonical_original(
    original: Path, root: GitInstallProvider, platform_version: str
) -> tuple[str, dict[str, dict[str, Any]]]:
    from infrastructure.publishing.standalone_mirror import populate_mirror_tree

    before = _records(original, _Budget())
    content = read_bytes_confined(original, original / ".template-export.json", max_bytes=64 * 1024 * 1024)
    manifest = json.loads(content)
    scope = manifest.get("source_project")
    if (
        manifest.get("schema_version") != 2
        or scope not in PUBLIC_PROJECT_NAMES
        or manifest.get("source_commit") != root.commit
        or manifest.get("infrastructure_version") != platform_version
        or manifest.get("files")
        != {name: row["sha256"] for name, row in before.items() if name != ".template-export.json"}
    ):
        raise ValueError("projection requires a complete exact committed schema-2 public export")
    with tempfile.TemporaryDirectory(prefix="projection-source-") as temporary:
        canonical = Path(temporary).resolve(strict=True) / "canonical"
        populate_mirror_tree(root.checkout, f"projects/{scope}", canonical, source_revision=root.commit)
        if _records(canonical, _Budget()) != before:
            raise ValueError("projection original differs from its actual committed canonical public source")
    if _records(original, _Budget()) != before:
        raise ValueError("projection original changed during source admission")
    return scope, before


def _prepared(
    original: Path,
    scope: str,
    records: dict[str, dict[str, Any]],
    platform: dict[str, str],
    pins: dict[str, dict[str, str]],
) -> tuple[dict[str, Any], dict[str, bytes]]:
    metadata = read_bytes_confined(original, original / "pyproject.toml", max_bytes=4 * 1024 * 1024)
    lock = read_bytes_confined(original, original / "uv.lock", max_bytes=64 * 1024 * 1024)
    projected_metadata, projected_lock, third_party = transform_install_files(metadata, lock, pins)
    edits = {"pyproject.toml": projected_metadata, "uv.lock": projected_lock}
    projected = {name: dict(row) for name, row in records.items()}
    transformations = {}
    for name, content in edits.items():
        digest = hashlib.sha256(content).hexdigest()
        if digest != records[name]["sha256"]:
            transformations[name] = {"original_sha256": records[name]["sha256"], "projected_sha256": digest}
        projected[name]["sha256"] = digest
    manifest = {
        "schema_version": PROJECTION_SCHEMA,
        "source_project": scope,
        "source_commit": platform["commit"],
        "original_export_sha256": publication_export_sha256(original),
        "original_manifest_sha256": records[".template-export.json"]["sha256"],
        "original_files": records,
        "projected_files": projected,
        "transformations": transformations,
        "third_party_lock_sha256": third_party,
        "platform_provider": platform,
        "install_providers": pins,
    }
    if _records(original, _Budget()) != records:
        raise ValueError("projection original changed while preparing installation fields")
    return manifest, edits


def _admit_meta_provider(
    meta: GitInstallProvider, root: GitInstallProvider, platform: dict[str, str], version: str
) -> dict[str, str]:
    """Only already projected Meta at this exact Root revision can provide Advanced."""
    from infrastructure.publishing.standalone_mirror import _verify_committed, populate_mirror_tree

    admitted = _admit_provider(meta, META_PACKAGE, version)
    with tempfile.TemporaryDirectory(prefix="projection-meta-") as temporary:
        original = Path(temporary).resolve(strict=True) / "original"
        populate_mirror_tree(
            root.checkout, "projects/templates/template_literature_meta_analysis", original, source_revision=root.commit
        )
        records = _records(original, _Budget())
        manifest, _ = _prepared(
            original, "templates/template_literature_meta_analysis", records, platform, {ROOT_PACKAGE: platform}
        )
        expected = {
            **manifest["projected_files"],
            PROJECTION_NAME: {"sha256": hashlib.sha256(_json(manifest)).hexdigest(), "mode": 0o644},
        }
        checkout, identity = _root(meta.checkout)
        budget = _Budget()
        metadata = tomllib.loads(
            read_bytes_confined(checkout, checkout / "pyproject.toml", max_bytes=4 * 1024 * 1024).decode()
        )
        build = metadata.get("build-system", {})
        settings = metadata.get("tool", {}).get("setuptools", {})
        packages, directories = settings.get("packages"), settings.get("package-dir")
        if (
            build.get("build-backend") != "setuptools.build_meta"
            or "backend-path" in build
            or not isinstance(packages, list)
            or not packages
            or not all(isinstance(name, str) for name in packages)
            or not isinstance(directories, dict)
            or not directories
            or not all(isinstance(path, str) for path in directories.values())
            or "data-files" in settings
        ):
            raise ValueError("Meta provider needs its explicit admitted setuptools package/build-input contract")
        source_roots = tuple(Path(path) for path in directories.values())
        if any(
            path.is_absolute() or not path.parts or any(part in {".", ".."} for part in path.parts)
            for path in source_roots
        ):
            raise ValueError("Meta installation source roots must be confined explicit directories")
        # Publication extras may remain in a mirror. They cannot enlarge any
        # package tree or add conventional executable/build/license inputs.
        committed: dict[str, tuple[str, str]] = {}
        for count, entry in enumerate(_git(meta, ["ls-tree", "-r", "-z", meta.commit]).split("\0"), start=1):
            if not entry:
                continue
            budget.check()
            if count > budget.limits.max_files:
                raise ValueError("Meta committed provider exceeds its finite file inventory")
            header, name = entry.split("\t", 1)
            mode, kind, object_identity = header.split()
            if kind != "blob" or mode not in {"100644", "100755"}:
                raise ValueError("Meta provider requires regular committed source and publication evidence")
            if name in committed or re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", object_identity) is None:
                raise ValueError("Meta provider has a repeated path or invalid committed object identity")
            committed[name] = (mode, object_identity)
            install_path = Path(name)
            build_input = (
                any(install_path.is_relative_to(source) for source in source_roots)
                or name in {"setup.py", "setup.cfg", "MANIFEST.in"}
                or install_path.parent == Path(".")
                and install_path.name.casefold().startswith(("license", "licence", "copying", "notice", "authors"))
            )
            if name not in expected and (build_input or name != INVENTORY_NAME and not _protected(name)):
                raise ValueError(
                    "Meta provider contains installation inputs outside the exact reviewed Root projection"
                )
        for name, record in expected.items():
            if _file(checkout, name, identity, budget) != record:
                raise ValueError("Meta provider is not the exact reviewed projection of this Root revision")
            content = read_bytes_confined(checkout, checkout / name, max_bytes=64 * 1024 * 1024)
            # Reuse only this admission's full committed tree. Physical bytes,
            # modes and closing provider admission are still checked afresh.
            _verify_committed(name, content, "100755" if record["mode"] == 0o755 else "100644", committed)
    if _admit_provider(meta, META_PACKAGE, version) != admitted:
        raise ValueError("Meta provider changed during projection admission")
    return admitted


def _expected(
    original: Path, root: GitInstallProvider, meta: GitInstallProvider | None
) -> tuple[dict[str, Any], dict[str, bytes]]:
    from infrastructure.publishing.root_release_contract import root_package_version

    platform_version = root_package_version(root.checkout)
    if re.fullmatch(r"4\.\d+\.\d+", platform_version) is None:
        raise ValueError("installation projection requires genuine platform 4 Source metadata")
    platform = _admit_provider(root, ROOT_PACKAGE, platform_version)
    scope, records = _assert_canonical_original(original, root, platform_version)
    versions = checkout_providers(
        read_bytes_confined(original, original / "pyproject.toml", max_bytes=4 * 1024 * 1024),
        read_bytes_confined(original, original / "uv.lock", max_bytes=64 * 1024 * 1024),
    )
    pins = {ROOT_PACKAGE: platform} if ROOT_PACKAGE in versions else {}
    if META_PACKAGE in versions:
        if (
            scope != "templates/template_advanced_literature_review"
            or meta is None
            or versions[META_PACKAGE] != "0.2.0"
        ):
            raise ValueError("Advanced installation projection requires its actual committed Meta provider")
        pins[META_PACKAGE] = _admit_meta_provider(meta, root, platform, versions[META_PACKAGE])
    manifest, edits = _prepared(original, scope, records, platform, pins)
    if META_PACKAGE in pins:
        if meta is None or _admit_meta_provider(meta, root, platform, "0.2.0") != pins[META_PACKAGE]:
            raise ValueError("Meta provider changed while preparing installation fields")
    if _admit_provider(root, ROOT_PACKAGE, platform_version) != platform:
        raise ValueError("Root provider changed during installation projection")
    return manifest, edits


def project_standalone_installation(
    original: Path,
    destination: Path,
    *,
    root_provider: GitInstallProvider,
    meta_provider: GitInstallProvider | None = None,
) -> dict[str, Any]:
    """Create a fresh projected tree; preserve the pristine schema-2 source and manifest."""
    original = original.absolute()
    destination = destination.absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError("installation projection destination must be fresh and absent")
    if ".." in destination.parts or destination.parent.resolve(strict=True) != destination.parent:
        raise ValueError("installation projection requires a real existing no-follow destination parent")
    manifest, edits = _expected(original, root_provider, meta_provider)
    destination.mkdir()
    copy_publication_source(original, destination)
    for name, content in edits.items():
        atomic_write_bytes_confined(
            destination, destination / name, content, mode=manifest["projected_files"][name]["mode"]
        )
    atomic_write_bytes_confined(destination, destination / PROJECTION_NAME, _json(manifest))
    validate_standalone_installation(original, destination, root_provider=root_provider, meta_provider=meta_provider)
    return manifest


def validate_standalone_installation(
    original: Path,
    projected: Path,
    *,
    root_provider: GitInstallProvider,
    meta_provider: GitInstallProvider | None = None,
) -> dict[str, Any]:
    """Independently rebuild expected transformations from actual source/providers."""
    expected, _ = _expected(original.absolute(), root_provider, meta_provider)
    records = _records(projected.absolute(), _Budget())
    manifest_record = {"sha256": hashlib.sha256(_json(expected)).hexdigest(), "mode": 0o644}
    if records != {**expected["projected_files"], PROJECTION_NAME: manifest_record}:
        raise ValueError("installation projection bytes, names, modes or provenance differ from exact admission")
    return expected
