"""Finite official npm asset preparation, bound to exact source lock integrity."""

from __future__ import annotations

import argparse
import base64
import hashlib
import os
from pathlib import Path
from urllib.parse import urlsplit
from typing import Any

from infrastructure.core.execution_boundary import run_bounded_subprocess
from infrastructure.project.public_acceptance_evidence import read_json, write_json

PACKAGES = {
    "mathjax": "mathjax-4.0.0.tgz",
    "@mathjax/mathjax-newcm-font": "mathjax-mathjax-newcm-font-4.0.0.tgz",
}
MAX_ARCHIVE = 64 * 1024 * 1024


def declaration(root: Path, name: str) -> dict[str, str]:
    """Require exact public registry identities from both source declarations."""
    package = read_json(root, root / "package.json")
    lock = read_json(root, root / "package-lock.json")
    version = package.get("dependencies", {}).get(name) or package.get("devDependencies", {}).get(name)
    row = lock.get("packages", {}).get(f"node_modules/{name}", {})
    url = str(row.get("resolved", ""))
    parsed = urlsplit(url)
    expected = f"/{name}/-/" + name.rsplit("/", 1)[-1] + "-4.0.0.tgz"
    integrity = str(row.get("integrity", ""))
    if (
        name not in PACKAGES
        or version != "4.0.0"
        or row.get("version") != "4.0.0"
        or parsed.scheme != "https"
        or parsed.netloc != "registry.npmjs.org"
        or parsed.path != expected
        or parsed.query
        or parsed.fragment
        or not integrity.startswith("sha512-")
    ):
        raise ValueError("native asset lacks exact official source lock identity")
    digest = base64.b64decode(integrity.removeprefix("sha512-"), validate=True)
    if len(digest) != 64 or "sha512-" + base64.b64encode(digest).decode() != integrity:
        raise ValueError("native asset lock integrity is ambiguous")
    return {"resolved": url, "integrity": integrity}


def verify_archive(path: Path, integrity: str) -> None:
    """Independently bind actual bounded archive bytes before CDN inspection."""
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= MAX_ARCHIVE:
        raise ValueError("native asset archive is absent or oversized")
    actual = "sha512-" + base64.b64encode(hashlib.sha512(path.read_bytes()).digest()).decode()
    if actual != integrity:
        raise ValueError("native asset archive differs from source SHA-512 integrity")


def prepare(root: Path) -> dict[str, Any]:
    root = root.resolve(strict=True)
    from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

    source_reader = SnapshotReader(root)
    sources = {name: source_reader.read(name).sha256 for name in ("package.json", "package-lock.json")}
    directory = root / "output/readiness/native-dependencies"
    directory.mkdir(parents=True, exist_ok=False)
    observations: dict[str, Any] = {}
    for name, filename in PACKAGES.items():
        row = declaration(root, name)
        path = directory / filename
        command = [
            "curl",
            "--fail",
            "--show-error",
            "--silent",
            "--proto",
            "=https",
            "--max-time",
            "120",
            "--connect-timeout",
            "30",
            "--max-filesize",
            str(MAX_ARCHIVE),
            "--output",
            str(path),
            row["resolved"],
        ]
        result = run_bounded_subprocess(command, cwd=root, env=os.environ.copy(), timeout=150, capture_output=True)
        record = {
            "command": command,
            "exit_code": result.returncode,
            "original_exit_code": result.original_returncode,
            "timed_out": result.timed_out,
            "custody_refused": result.custody_refused,
            "diagnostic": result.command_error,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
        process = write_json(root, directory / f"{filename}-process.json", record)
        if (
            result.returncode != 0
            or result.original_returncode != 0
            or result.timed_out
            or result.custody_refused
            or result.command_error
        ):
            raise ValueError("original native asset download did not complete successfully")
        verify_archive(path, row["integrity"])
        observations[name] = {
            **row,
            "process_artifact": process,
            "archive_artifact": {
                "path": path.relative_to(root).as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            },
        }
    from infrastructure.reporting.native_format_browser_cdn import compile_cdn_assets

    reader = SnapshotReader(root)
    assets = compile_cdn_assets(reader)
    if not reader.unchanged() or not source_reader.unchanged():
        raise ValueError("native source/asset bytes changed during independent inspection")
    return write_json(
        root,
        directory / "preparation.json",
        {
            "schema_version": "template-native-dependency-preparation-v1",
            "declarations": sources,
            "downloads": observations,
            "independently_inspected_assets": len(assets),
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    print(prepare(parser.parse_args().repo_root))


if __name__ == "__main__":
    main()
