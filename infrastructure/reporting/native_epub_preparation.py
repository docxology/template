"""Prepare the pinned official EPUBCheck bundle in a fresh owned directory."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile
import urllib.request
from http.client import HTTPException, HTTPMessage, HTTPResponse
from typing import IO, cast
from urllib.parse import urlsplit
import zipfile

URL = "https://github.com/w3c/epubcheck/releases/download/v5.4.0/epubcheck-5.4.0.zip"
API_URL = "https://api.github.com/repos/w3c/epubcheck/releases/assets/565327111"
SIZE = 33_093_170
SHA256 = "33350c61038e71dfb3d45a76aed04bf5481e6d5500cb780f6e98db8bbd15a28c"
MAX_EXPANDED = 64 * 1024 * 1024
PREFIX = "epubcheck-5.4.0"


def extract_bundle(archive: Path, destination: Path) -> Path:
    """Inspect the complete bounded archive before writing any member."""
    with zipfile.ZipFile(archive) as bundle:
        rows = bundle.infolist()
        if not rows or len(rows) > 1000:
            raise ValueError("EPUBCheck archive member count is invalid")
        names: set[str] = set()
        total = 0
        for row in rows:
            name = row.filename
            path = PurePosixPath(name)
            mode = row.external_attr >> 16
            if (
                name in names
                or path.is_absolute()
                or "\\" in name
                or "\x00" in name
                or not path.parts
                or path.parts[0] != PREFIX
                or ".." in path.parts
                or str(path) != name.rstrip("/")
                or row.flag_bits & 1
                or stat.S_ISLNK(mode)
                or (stat.S_IFMT(mode) not in {0, stat.S_IFREG, stat.S_IFDIR})
            ):
                raise ValueError("EPUBCheck archive member is unsafe or ambiguous")
            names.add(name)
            total += row.file_size
            if row.file_size > MAX_EXPANDED or total > MAX_EXPANDED:
                raise ValueError("EPUBCheck expanded archive exceeds budget")
        if f"{PREFIX}/epubcheck.jar" not in names:
            raise ValueError("EPUBCheck main JAR is absent")
        destination.mkdir(parents=True, exist_ok=False)
        try:
            for row in rows:
                target = destination.joinpath(*PurePosixPath(row.filename).parts)
                if row.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with bundle.open(row) as source, target.open("xb") as output:
                        shutil.copyfileobj(source, output, 1024 * 1024)
                    if target.stat().st_size != row.file_size:
                        raise ValueError("EPUBCheck extracted member size changed")
        except BaseException:
            shutil.rmtree(destination)
            raise
    return destination / PREFIX / "epubcheck.jar"


class _HTTPSOnlyRedirect(urllib.request.HTTPRedirectHandler):
    """Keep every acquisition redirect on HTTPS before opening it."""

    def redirect_request(
        self, req: urllib.request.Request, fp: IO[bytes], code: int, msg: str, headers: HTTPMessage, newurl: str
    ) -> urllib.request.Request | None:
        if urlsplit(newurl).scheme != "https":
            raise ValueError("EPUBCheck download left HTTPS")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _download_response(request: urllib.request.Request) -> HTTPResponse:
    """Refuse non-HTTPS acquisition before any network or local file access."""
    if urlsplit(request.full_url).scheme != "https":
        raise ValueError("EPUBCheck download requires HTTPS")
    opener = urllib.request.build_opener(_HTTPSOnlyRedirect())
    return cast(HTTPResponse, opener.open(request, timeout=60))


def _download_archive(request: urllib.request.Request, archive: Path) -> None:
    """Stream and verify one candidate against the pinned release bytes."""
    digest = hashlib.sha256()
    size = 0
    with _download_response(request) as response, archive.open("xb") as output:
        if not response.geturl().startswith("https://"):
            raise ValueError("EPUBCheck download left HTTPS")
        while chunk := response.read(1024 * 1024):
            size += len(chunk)
            if size > SIZE:
                raise ValueError("EPUBCheck download exceeds exact release size")
            digest.update(chunk)
            output.write(chunk)
    if size != SIZE or digest.hexdigest() != SHA256:
        raise ValueError("EPUBCheck official release size/digest mismatch")


def prepare(destination: Path) -> Path:
    """Download the pinned EPUBCheck bundle from its official release routes."""
    destination = destination.absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError("EPUBCheck preparation requires a fresh destination")
    destination.parent.mkdir(parents=True, exist_ok=True)
    headers = {
        "User-Agent": "template-native-preparation",
        "Accept": "application/octet-stream",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    failures = []
    with tempfile.TemporaryDirectory(prefix=f".{destination.name}.", dir=destination.parent) as scratch:
        for name, url in (("asset-api", API_URL), ("release-url", URL)):
            archive = Path(scratch) / f"{name}.zip"
            request = urllib.request.Request(url, headers=headers)
            try:
                _download_archive(request, archive)
            except (HTTPException, OSError) as error:
                failures.append(f"{name} ({type(error).__name__})")
            else:
                return extract_bundle(archive, destination)
    raise ValueError("EPUBCheck verified download failed via " + ", ".join(failures))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    print(prepare(args.destination))


if __name__ == "__main__":
    main()
