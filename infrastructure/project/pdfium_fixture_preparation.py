"""Prepare Source-locked public wheel DATA, never native execution authority."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlsplit

from packaging.tags import sys_tags
from packaging.utils import parse_wheel_filename

LIMIT = 64 * 1024 * 1024


@dataclass(frozen=True)
class WheelFixture:
    """Exact public transport and bytes nominated by the selected Source lock."""

    url: str
    filename: str
    sha256: str
    size: int


def select_pdfium_wheel(lock: bytes) -> WheelFixture:
    """Select the actual interpreter's best compatible locked platform wheel."""
    if len(lock) > LIMIT:
        raise ValueError("Source lock exceeds the finite fixture bound")
    packages = [row for row in tomllib.loads(lock.decode())["package"] if row["name"] == "pypdfium2"]
    if len(packages) != 1:
        raise ValueError("Source must declare one exact PDFium package")
    package = packages[0]
    preference = {tag: ordinal for ordinal, tag in enumerate(sys_tags())}
    compatible = []
    for row in package["wheels"]:
        url = row["url"]
        parsed = urlsplit(url)
        if (
            parsed.scheme != "https"
            or parsed.netloc != "files.pythonhosted.org"
            or parsed.query
            or parsed.fragment
            or any(character.isspace() for character in url)
            or re.fullmatch(r"/packages/[A-Za-z0-9._/-]+\.whl", parsed.path) is None
            or any(part in (".", "..") for part in parsed.path.split("/"))
        ):
            raise ValueError("Only exact public HTTPS wheel locators are permitted")
        filename = parsed.path.rsplit("/", 1)[-1]
        name, version, _, tags = parse_wheel_filename(filename)
        if name != "pypdfium2" or str(version) != package["version"]:
            raise ValueError("Wheel name/version differs from the Source package")
        digest = row["hash"]
        size = row["size"]
        if not isinstance(digest, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is None:
            raise ValueError("Source wheel requires an exact SHA256")
        if type(size) is not int or not 0 < size <= LIMIT:
            raise ValueError("Source wheel size exceeds the finite fixture bound")
        ranks = [preference[tag] for tag in tags if tag in preference]
        if ranks:
            compatible.append((min(ranks), filename, WheelFixture(url, filename, digest[7:], size)))
    if not compatible:
        raise ValueError("No Source-locked wheel supports this interpreter's platform")
    compatible.sort(key=lambda entry: (entry[0], entry[1]))
    selected = compatible[0][2]
    if sum(entry[1] == selected.filename for entry in compatible) != 1:
        raise ValueError("Source wheel nomination is ambiguous")
    return selected


def verify_download(path: Path, selection: WheelFixture) -> None:
    """Authenticate actual finite bytes without importing or installing them."""
    if type(selection.size) is not int or not 0 < selection.size <= LIMIT:
        raise ValueError("Wheel fixture size exceeds the finite bound")
    if path != path.resolve(strict=True) or not path.is_file() or path.name != selection.filename:
        raise ValueError("Wheel fixture must be the nominated physical regular file")
    with path.open("rb") as stream:
        body = stream.read(selection.size + 1)
    if len(body) != selection.size or hashlib.sha256(body).hexdigest() != selection.sha256:
        raise ValueError("Downloaded wheel differs from exact Source size/hash")


def admit_fixture_scratch(root: Path, temporary_root: Path) -> Path:
    """Require a physical external scratch directory without altering Source."""
    if (
        not temporary_root.is_absolute()
        or temporary_root != temporary_root.resolve(strict=True)
        or not temporary_root.is_dir()
        or temporary_root.is_relative_to(root.resolve(strict=True))
        or temporary_root.is_relative_to(Path(sys.prefix).resolve(strict=True))
    ):
        raise ValueError("Fixture scratch must be physical and outside Source and the selected runtime")
    return temporary_root


def require_bounded_curl(body: bytes) -> None:
    """Unknown-length transfer bounds require the documented curl 8.4 behavior."""
    if len(body) > 4096:
        raise ValueError("Curl capability observation exceeds its finite bound")
    matched = re.match(rb"curl ([0-9]+)\.([0-9]+)\.([0-9]+) ", body)
    if matched is None or tuple(int(value) for value in matched.groups()) < (8, 4, 0):
        raise ValueError("Exact bounded wheel preparation requires curl 8.4.0 or newer")


def _run_curl(curl: str, arguments: list[str], directory: Path, label: str, timeout: int) -> int:
    outcome: dict[str, object] = {"status": "pending", "original_exit_code": None}
    with (directory / f"{label}.stdout").open("xb") as stdout, (directory / f"{label}.stderr").open("xb") as stderr:
        try:
            result = subprocess.run(
                [curl, "--disable", *arguments],
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                env={"PATH": os.defpath, "LANG": "C", "LC_ALL": "C"},
                check=False,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            outcome["status"] = "timeout"
            raise
        except OSError:
            outcome["status"] = "spawn-error"
            raise
        else:
            outcome.update(status="exited", original_exit_code=result.returncode)
            (directory / f"{label}.exit").write_text(str(result.returncode) + "\n")
            return result.returncode
        finally:
            (directory / f"{label}.outcome.json").write_text(json.dumps(outcome, sort_keys=True) + "\n")


def prepare_pdfium_wheel(root: Path, temporary_root: Path) -> Path:
    """Download into a new owned directory with no redirects or installation."""
    root = root.resolve(strict=True)
    temporary_root = admit_fixture_scratch(root, temporary_root)
    with (root / "uv.lock").open("rb") as stream:
        lock = stream.read(LIMIT + 1)
    selected = select_pdfium_wheel(lock)
    curl = shutil.which("curl")
    if curl is None:
        raise ValueError("Fixture preparation requires the real curl executable")
    directory = Path(tempfile.mkdtemp(prefix="template-pdfium-wheel-", dir=temporary_root))
    selection = {"selection": asdict(selected), "lock_sha256": hashlib.sha256(lock).hexdigest()}
    (directory / "selection.json").write_text(json.dumps(selection, sort_keys=True) + "\n")
    if _run_curl(curl, ["--version"], directory, "capability", 10) != 0:
        raise ValueError(f"Curl capability observation failed; retained evidence: {directory}")
    with (directory / "capability.stdout").open("rb") as stream:
        require_bounded_curl(stream.read(4097))
    wheel = directory / selected.filename
    code = _run_curl(
        curl,
        [
            "--globoff",
            "--fail",
            "--silent",
            "--show-error",
            "--proto",
            "=https",
            "--max-time",
            "120",
            "--max-filesize",
            str(selected.size),
            "--write-out",
            "%{http_code}",
            "--output",
            str(wheel),
            selected.url,
        ],
        directory,
        "download",
        125,
    )
    with (directory / "download.stdout").open("rb") as stream:
        status = stream.read(4)
    if code != 0 or status != b"200":
        raise ValueError(f"Exact wheel download failed without redirect fallback; retained evidence: {directory}")
    verify_download(wheel, selected)
    (directory / "fixture.json").write_text(json.dumps(selection, sort_keys=True) + "\n")
    return wheel


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--temporary-root", required=True, type=Path)
    arguments = parser.parse_args()
    print(prepare_pdfium_wheel(arguments.repo_root, arguments.temporary_root))


if __name__ == "__main__":
    main()
