"""Stable wire vocabulary and bounded pagination for fixed hosted observations."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

WORKFLOW = ".github/workflows/platform-required-acceptance.yml"
ARL_WORKFLOW = ".github/workflows/platform-native-preflight.yml"
MAX_ARCHIVE = 64 * 1024 * 1024
MAX_RUN_ARTIFACTS = 1024
MAX_LISTING_PAGES = 11
DOWNLOAD_SCRIPT = """import sys,subprocess,json,hashlib,tempfile
from pathlib import Path
p=Path(sys.argv[1]); limit=64*1024*1024; written=0
with p.open('xb') as output, tempfile.TemporaryFile() as errors:
 child=subprocess.Popen(sys.argv[2:],stdout=subprocess.PIPE,stderr=errors)
 while True:
  chunk=child.stdout.read(65536)
  if not chunk: break
  written+=len(chunk)
  if written>limit:
   child.kill();child.wait();sys.exit(75)
  output.write(chunk)
 code=child.wait()
 errors.seek(0);sys.stderr.buffer.write(errors.read(1024*1024))
print(json.dumps({'original_exit_code':code,'archive_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}))
sys.exit(code)
"""


def _context(repository: str, run_id: int, head_sha: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) or any(
        part in {".", ".."} for part in repository.split("/")
    ):
        raise ValueError("invalid designated repository")
    if type(run_id) is not int or run_id <= 0 or not re.fullmatch(r"[0-9a-f]{40}", head_sha):
        raise ValueError("invalid original run or exact commit")


def _process(raw: dict[str, Any], command: list[str]) -> None:
    if (
        raw.get("command") != command
        or type(raw.get("exit_code")) is not int
        or raw["exit_code"] != 0
        or type(raw.get("original_exit_code")) is not int
        or raw["original_exit_code"] != 0
        or raw.get("timed_out") is not False
        or raw.get("custody_refused") is not False
        or raw.get("diagnostic") != ""
    ):
        raise ValueError("original hosted observation process was not successful")


def _api_command(endpoint: str) -> list[str]:
    return [
        "gh",
        "api",
        "--hostname",
        "github.com",
        "-H",
        "Accept: application/vnd.github+json",
        "-H",
        "X-GitHub-Api-Version: 2022-11-28",
        endpoint,
    ]


def _merge_listing_pages(pages: list[dict[str, Any]], *, complete: bool) -> dict[str, Any]:
    """Require full ordered finite pagination, including fixed artifacts beyond100."""
    if not pages or len(pages) > MAX_LISTING_PAGES:
        raise ValueError("hosted artifact pagination is absent or exceeds its Source bound")
    count = pages[0].get("total_count")
    if type(count) is not int or not 0 <= count <= MAX_RUN_ARTIFACTS:
        raise ValueError("hosted artifact census exceeds its Source-owned1024 bound")
    rows: list[dict[str, Any]] = []
    for ordinal, page in enumerate(pages):
        current = page.get("artifacts")
        if (
            page.get("total_count") != count
            or not isinstance(current, list)
            or len(current) > 100
            or (ordinal < len(pages) - 1 and len(current) != 100)
            or any(not isinstance(row, dict) or type(row.get("id")) is not int for row in current)
        ):
            raise ValueError("hosted artifact pagination is truncated, changed or malformed")
        rows.extend(current)
    if len(rows) > count or len({row["id"] for row in rows}) != len(rows) or (complete and len(rows) != count):
        raise ValueError("hosted artifact census is incomplete, ambiguous or changed")
    return {"total_count": count, "artifacts": rows}


def collect_artifact_pages(read_page: Callable[[int], dict[str, Any]]) -> tuple[dict[str, Any], int]:
    """Read and validate the complete bounded listing in original page order."""
    pages = []
    for page in range(1, MAX_LISTING_PAGES + 1):
        pages.append(read_page(page))
        listing = _merge_listing_pages(pages, complete=False)
        if len(listing["artifacts"]) == listing["total_count"]:
            break
    return _merge_listing_pages(pages, complete=True), len(pages)
