"""Lock-integrity-authenticated offline responses for exact reviewed CDN URLs."""

from __future__ import annotations

import base64
import hashlib
import tarfile
from io import BytesIO
from functools import lru_cache
from pathlib import Path
from typing import Any

from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

PACKAGES = {
    "mathjax": ("mathjax-4.0.0.tgz", "https://cdn.jsdelivr.net/npm/mathjax@4.0.0/"),
    "@mathjax/mathjax-newcm-font": (
        "mathjax-mathjax-newcm-font-4.0.0.tgz",
        "https://cdn.jsdelivr.net/npm/@mathjax/mathjax-newcm-font@4.0.0/",
    ),
}


def compile_cdn_assets(reader: SnapshotReader) -> list[dict[str, Any]]:
    """Verify official npm archive integrity before deriving every response byte."""
    declarations = reader.read("package.json").json_object()
    lock = reader.read("package-lock.json").json_object()
    results: list[dict[str, Any]] = []
    total = 0
    for name, (filename, prefix) in PACKAGES.items():
        if (
            declarations.get("dependencies", {}).get(name) or declarations.get("devDependencies", {}).get(name)
        ) != "4.0.0":
            raise ValueError("offline CDN dependency is not exact source-declared version")
        entry = lock.get("packages", {}).get(f"node_modules/{name}", {})
        if entry.get("version") != "4.0.0" or not str(entry.get("resolved", "")).startswith(
            "https://registry.npmjs.org/"
        ):
            raise ValueError("offline CDN archive lacks official exact source lock identity")
        archive = reader.read(f"output/readiness/native-dependencies/{filename}")
        integrity = "sha512-" + base64.b64encode(hashlib.sha512(archive.content).digest()).decode()
        if entry.get("integrity") != integrity:
            raise ValueError("offline CDN archive bytes differ from official npm lock integrity")
        with tarfile.open(fileobj=BytesIO(archive.content), mode="r:gz") as package:
            seen = set()
            for member in package.getmembers():
                path = Path(member.name)
                if not path.parts or path.parts[0] != "package" or ".." in path.parts or path.is_absolute():
                    raise ValueError("offline dependency archive member escapes package")
                if member.isdir():
                    continue
                if not member.isfile() or member.name in seen or member.size > 8 * 1024 * 1024:
                    raise ValueError("offline dependency archive member is not a bounded unique regular file")
                seen.add(member.name)
                relative = path.relative_to("package").as_posix()
                if name != "mathjax" and not (
                    relative.startswith("chtml/") or relative in {"chtml.js", "package.json"}
                ):
                    continue
                handle = package.extractfile(member)
                if handle is None:
                    raise ValueError("offline archive omitted declared member bytes")
                content = handle.read(8 * 1024 * 1024 + 1)
                total += len(content)
                if total > 96 * 1024 * 1024 or len(results) >= 3000:
                    raise ValueError("offline CDN dependency closure exceeds finite budget")
                results.append(
                    {
                        "url": prefix + relative,
                        "archive": {"path": archive.relative, "sha256": archive.sha256},
                        "member": member.name,
                        "sha256": hashlib.sha256(content).hexdigest(),
                    }
                )
    return sorted(results, key=lambda row: row["url"])


def cdn_member_bytes(row: dict[str, Any], reader: SnapshotReader) -> bytes:
    archive = reader.read(row["archive"]["path"])
    if archive.sha256 != row["archive"]["sha256"]:
        raise ValueError("offline CDN archive changed after admission")
    content = _archive_members(archive.content)[row["member"]]
    if hashlib.sha256(content).hexdigest() != row["sha256"]:
        raise ValueError("offline CDN response differs from independently authenticated member")
    return content


@lru_cache(maxsize=2)
def _archive_members(content: bytes) -> dict[str, bytes]:
    """Decode each admitted immutable archive once, with a bounded memory cache."""
    members: dict[str, bytes] = {}
    total = 0
    with tarfile.open(fileobj=BytesIO(content), mode="r:gz") as archive:
        for member in archive.getmembers():
            if member.isdir():
                continue
            if not member.isfile() or member.size > 8 * 1024 * 1024 or member.name in members:
                raise ValueError("CDN archive has an unsupported member")
            handle = archive.extractfile(member)
            if handle is None:
                raise ValueError("CDN archive omitted a member")
            data = handle.read(8 * 1024 * 1024 + 1)
            total += len(data)
            if total > 96 * 1024 * 1024 or len(members) >= 3000:
                raise ValueError("CDN decoded cache exceeds finite bounds")
            members[member.name] = data
    return members
