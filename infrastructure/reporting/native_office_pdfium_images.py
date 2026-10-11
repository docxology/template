"""Actual selected PDFium process image mapping observations; no memory grant."""

from __future__ import annotations

import ctypes
import os
import sys
from pathlib import Path
from typing import Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_office_pdfium_provider import MAX_FILES


def _loaded_image(library: Path, deadline: float, *, require: bool = True) -> dict[str, Any]:
    """Observe this actual process's selected mapped image through the OS.

    This identifies the selected PDFium image, not every operating-system
    library or the contents of process memory. The external original launcher
    independently authenticates these observations and their enclosing Code.
    """
    remaining(deadline)
    matches = []
    if sys.platform == "darwin":
        process = ctypes.CDLL(None)
        count = process._dyld_image_count
        count.argtypes, count.restype = [], ctypes.c_uint32
        image_name = process._dyld_get_image_name
        image_name.argtypes, image_name.restype = [ctypes.c_uint32], ctypes.c_char_p
        image_header = process._dyld_get_image_header
        image_header.argtypes, image_header.restype = [ctypes.c_uint32], ctypes.c_void_p
        length = count()
        if length > MAX_FILES:
            raise ValueError("PDFium actual process image inventory exceeds its finite bound")
        for index in range(length):
            remaining(deadline)
            value = image_name(index)
            if value is not None and os.fsdecode(value) == str(library):
                address = image_header(index)
                if type(address) is not int or address <= 0:
                    raise ValueError("PDFium actual mapped image has no genuine image-header address")
                matches.append({"path": str(library), "header_address": address})
        if len(matches) != 1 and (require or matches):
            raise ValueError("PDFium actual Darwin selected image is missing or ambiguous")
    elif sys.platform.startswith("linux"):
        data = Path("/proc/self/maps").read_bytes()
        if len(data) > 8 * 1024 * 1024:
            raise ValueError("PDFium actual process mapping inventory exceeds its finite bound")
        identity = library.stat()
        for line in data.splitlines():
            remaining(deadline)
            row = line.decode().split(maxsplit=5)
            if len(row) == 6 and row[5] == str(library):
                major, minor = (int(value, 16) for value in row[3].split(":"))
                if os.makedev(major, minor) != identity.st_dev or int(row[4]) != identity.st_ino:
                    raise ValueError("PDFium mapped image device/inode differs from admitted library")
                matches.append(
                    {
                        "range": row[0],
                        "permissions": row[1],
                        "offset": row[2],
                        "path": row[5],
                        "device": identity.st_dev,
                        "inode": identity.st_ino,
                    }
                )
        if not matches and require:
            raise ValueError("PDFium actual Linux selected image is not mapped")
    else:
        raise ValueError("PDFium actual mapped-image custody is unsupported on this operating system")
    remaining(deadline)
    return {"platform": sys.platform, "owner_pid": os.getpid(), "images": matches}
