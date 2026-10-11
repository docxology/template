"""Shared bounded kernel-map reconstruction; it supplies no native authority."""

from __future__ import annotations

import os
from typing import Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_loader_protocol import CHUNK


def parse_maps(raw: bytes, *, deadline: float) -> list[dict[str, Any]]:
    if not 0 < len(raw) <= CHUNK:
        raise ValueError("consuming-process kernel map exceeds its finite ceiling")
    rows = []
    previous = 0
    for line in raw.splitlines():
        remaining(deadline)
        columns = line.split(None, 5)
        if len(columns) not in (5, 6):
            raise ValueError("consuming-process kernel map has an unknown ABI row")
        extent, protection, offset, device, inode = columns[:5]
        low, high = (int(value, 16) for value in extent.split(b"-"))
        major, minor = (int(value, 16) for value in device.split(b":"))
        if low < previous or low >= high or len(protection) != 4 or protection[3:4] not in {b"p", b"s"}:
            raise ValueError("consuming-process map extent/order/protection is invalid")
        if any(value not in expected for value, expected in zip(protection[:3], (b"r-", b"w-", b"x-"), strict=True)):
            raise ValueError("consuming-process map has an unknown protection ABI")
        rows.append(
            {
                "low": low,
                "high": high,
                "protection": protection.decode("ascii"),
                "offset": int(offset, 16),
                "device": os.makedev(major, minor),
                "inode": int(inode),
                "label": columns[5].decode("utf-8", "strict") if len(columns) == 6 else "",
            }
        )
        previous = high
    return rows


def census_images(
    rows: list[dict[str, Any]],
    opened: dict[int, dict[str, Any]],
    active: dict[int, dict[str, Any]],
    closed: list[int],
    *,
    deadline: float,
) -> dict[int, dict[str, Any]]:
    """Select live loads plus already-closed but still mapped fini residents."""
    images = dict(active)
    for key in reversed(closed):
        remaining(deadline)
        candidate = opened[key]
        if not any(
            segment["flags"] & 1 and any(row["low"] <= segment["address"] < row["high"] for row in rows)
            for segment in candidate["segments"]
        ):
            continue
        if any(other["base"] == candidate["base"] and other["body"] == candidate["body"] for other in images.values()):
            continue
        images[key] = candidate
    return images


def executable_census(
    rows: list[dict[str, Any]],
    images: dict[int, dict[str, Any]],
    *,
    helper_identity: dict[str, int],
    compiler: dict[str, str],
    page: int,
    deadline: float,
) -> dict[str, Any]:
    """Independently cover every executable map with one actual Source load."""
    if page not in {4096, 16384, 65536}:
        raise ValueError("loader census requires a reviewed original host page ABI")
    helper_rows = [row for row in rows if all(row[key] == helper_identity[key] for key in ("device", "inode"))]
    if not helper_rows:
        raise ValueError("callback process did not map its exact fixed Source auditor body")
    selected = []
    for row in rows:
        remaining(deadline)
        if "x" not in row["protection"][:3]:
            continue
        if row["label"] == "[vsyscall]" and row["inode"] == 0 and row["protection"][:3] == "--x":
            selected.append({"mapping": row, "kind": "kernel-vsyscall", "readable_code": False})
            continue
        if row["protection"][:3] != "r-x":
            raise ValueError("consuming callback process has unsupported executable protection")
        if row in helper_rows:
            selected.append({"mapping": row, "kind": "source-instrumentation", "compiler": compiler})
            continue
        matches = set()
        for object_id, image in images.items():
            for segment in image["segments"]:
                remaining(deadline)
                if not segment["flags"] & 1:
                    continue
                low = segment["address"] // page * page
                high = (segment["address"] + segment["memory_bytes"] + page - 1) // page * page
                body = image["body"]
                if not low <= row["low"] < row["high"] <= high:
                    continue
                if body is None:
                    match = row["label"] == "[vdso]" and row["inode"] == 0
                else:
                    match = (
                        row["device"] == body["identity"]["device"]
                        and row["inode"] == body["identity"]["inode"]
                        and row["offset"] == segment["file_offset"] // page * page + row["low"] - low
                    )
                if match:
                    matches.add(object_id)
        if len(matches) != 1:
            raise ValueError("executable kernel map lacks one complete actual callback/body nomination")
        selected.append({"mapping": row, "kind": "consumer-image", "object_id": matches.pop()})
    if not selected or not any(row["kind"] == "consumer-image" for row in selected):
        raise ValueError("kernel census lacks a complete actual consuming executable image")
    return {"schema_version": "template-loader-kernel-executable-census-v1", "page_bytes": page, "rows": selected}
