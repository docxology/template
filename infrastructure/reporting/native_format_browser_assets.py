"""Confined source-owned HTML/CSS and declared MathJax dependency closure."""

from __future__ import annotations

import hashlib
import os
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader


class References(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.resources: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag in {"img", "script", "source", "video", "audio", "iframe", "object", "embed"}:
            for key in ("src", "poster", "data"):
                if values.get(key):
                    self.resources.append(str(values[key]))
            if values.get("srcset"):
                self.resources.extend(part.strip().split()[0] for part in str(values["srcset"]).split(","))
        if tag == "link" and set(str(values.get("rel", "")).split()) & {
            "stylesheet",
            "icon",
            "preload",
            "modulepreload",
        }:
            if values.get("href"):
                self.resources.append(str(values["href"]))


def compile_browser_assets(root: Path, artifact: ArtifactSnapshot, reader: SnapshotReader) -> dict[str, Any]:
    """Reconstruct closure from exact original HTML/CSS and pinned asset manifest."""
    parser = References()
    parser.feed(artifact.content.decode())
    pending: list[tuple[Path, str]] = [(artifact.path.parent, url) for url in parser.resources]
    pending.extend((artifact.path.parent, url) for url in _css_urls(artifact.content.decode()))
    snapshots: dict[str, ArtifactSnapshot] = {}
    cdn_assets: list[dict[str, Any]] = []
    blockers: list[str] = []
    seen: set[tuple[str, str]] = set()
    while pending:
        base, value = pending.pop(0)
        if (str(base), value) in seen:
            continue
        seen.add((str(base), value))
        parsed = urlsplit(value)
        if parsed.scheme == "data" or not parsed.path:
            continue
        if value == "https://cdn.jsdelivr.net/npm/mathjax@4.0.0/tex-chtml.js":
            from infrastructure.reporting.native_format_browser_cdn import compile_cdn_assets

            cdn_assets = compile_cdn_assets(reader)
            for row in cdn_assets:
                archive = reader.read(row["archive"]["path"])
                snapshots[archive.relative] = archive
            continue
        if parsed.scheme or parsed.netloc or parsed.path.startswith("/"):
            blockers.append(f"external/absolute browser resource: {value}")
            continue
        source = base / unquote(parsed.path)
        # Normalize legitimate ../figures references before the no-symlink reader.
        relative = Path(os.path.normpath(str(source))).relative_to(root).as_posix()
        snapshot = reader.read(relative)
        snapshots[relative] = snapshot
        if snapshot.path.suffix == ".css":
            pending.extend((snapshot.path.parent, url) for url in _css_urls(snapshot.content.decode()))
    manifest_path = artifact.path.parent / "assets/mathjax-4.0.0/asset-manifest.json"
    if any("assets/mathjax-4.0.0/" in url for url in parser.resources):
        manifest = reader.read(manifest_path.relative_to(root).as_posix())
        data = manifest.json_object()
        declarations = reader.read("package.json").json_object()
        lock = reader.read("package-lock.json")
        expected = {"mathjax": "4.0.0", "@mathjax/mathjax-newcm-font": "4.0.0"}
        if (
            data.get("schema_version") != "template-local-mathjax-assets-v1"
            or data.get("packages") != expected
            or data.get("package_lock_sha256") != lock.sha256
        ):
            raise ValueError("browser MathJax closure differs from source-owned lock identities")
        for name, version in expected.items():
            if (
                declarations.get("dependencies", {}).get(name) or declarations.get("devDependencies", {}).get(name)
            ) != version:
                raise ValueError("browser MathJax package version is not source declared")
            entry = lock.json_object().get("packages", {}).get(f"node_modules/{name}", {})
            if entry.get("version") != version or not str(entry.get("integrity", "")).startswith("sha512-"):
                raise ValueError("browser MathJax lock lacks exact integrity")
        rows = data.get("files")
        if not isinstance(rows, list) or not rows or len(rows) > 2000:
            raise ValueError("browser MathJax closure is absent or unbounded")
        names = set()
        for row in rows:
            if not isinstance(row, dict) or set(row) != {"path", "sha256", "package"} or row["package"] not in expected:
                raise ValueError("browser MathJax closure member changed")
            name = row["path"]
            if (
                not isinstance(name, str)
                or not name.startswith("assets/mathjax-4.0.0/")
                or name in names
                or ".." in Path(name).parts
            ):
                raise ValueError("browser MathJax member escapes or duplicates its source-owned closure")
            names.add(name)
            snapshot = reader.read((artifact.path.parent / name).relative_to(root).as_posix())
            if snapshot.sha256 != row["sha256"]:
                raise ValueError("browser consumed MathJax asset bytes changed")
            snapshots[snapshot.relative] = snapshot
        snapshots[manifest.relative] = manifest
        from infrastructure.rendering._web_assets import MATHJAX_INTEGRITY
        import base64

        loader = snapshots[
            (artifact.path.parent / "assets/mathjax-4.0.0/mathjax/tex-chtml.js").relative_to(root).as_posix()
        ]
        if "sha384-" + base64.b64encode(hashlib.sha384(loader.content).digest()).decode() != MATHJAX_INTEGRITY:
            raise ValueError("browser MathJax loader differs from reviewed source SRI")
    if len(snapshots) > 3000 or sum(len(item.content) for item in snapshots.values()) > 96 * 1024 * 1024:
        raise ValueError("browser resource closure exceeds its finite budget")
    return {
        "schema_version": "template-native-browser-assets-v1",
        "artifact": {"path": artifact.relative, "sha256": artifact.sha256},
        "assets": [
            {"path": item.relative, "sha256": item.sha256}
            for item in sorted(snapshots.values(), key=lambda item: item.relative)
        ],
        "blockers": sorted(set(blockers)),
        **({"cdn_assets": cdn_assets} if cdn_assets else {}),
    }


def _css_urls(text: str) -> list[str]:
    return [item.strip().strip("\"'") for item in re.findall(r"url\(\s*([^)]*?)\s*\)", text)] + re.findall(
        r"@import\s+[\"']([^\"']+)[\"']", text
    )
