"""Explicit licensed Source11 typography; renderer inputs are whole font bytes.

This is the template's declared default, rather than an installed-font alias.
Project Mermaid directives and explicit font CSS continue to override it.
The profile is DATA; actual Source and native process custody remain required.
"""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.rendering._web_font_assets import (
    FONT_BODIES,
    LICENSE_SHA256,
    read_source_web_font,
    source_web_font_directory,
)

SCHEMA = "template-source-mermaid-licensed-default-font-v1"
FAMILY = "Template Liberation Sans"
NAMES = ("LiberationSans", "LiberationSans-Bold", "LiberationSans-Italic", "LiberationSans-BoldItalic")
PROFILE_NAME = "source-font-default.json"
SCRIPT_NAME = "_mermaid_source_font_default.mjs"
MAX_FONT_BYTES = 128 * 1024 * 1024


def default_font_profile(*, deadline: float | None = None) -> dict[str, Any]:
    """Read the fixed packaged cohort; never nominate a font from a receipt."""
    directory = source_web_font_directory()
    license_path = directory / "OFL.txt"
    before = license_path.stat()
    license_bytes = read_bytes_confined(directory, license_path, max_bytes=8192)
    if license_path.stat() != before or hashlib.sha256(license_bytes).hexdigest() != LICENSE_SHA256:
        raise ValueError("Source Mermaid font distribution notice changed")
    faces = []
    total = 0
    for name in NAMES:
        # The shared asset reader checks whole body/physical identity. A native
        # caller supplies its original deadline; ordinary rendering remains
        # covered by its original enclosing operation and child timeout.
        if deadline is None:
            path = directory / FONT_BODIES[name]["filename"]
            prior = path.stat()
            body = read_bytes_confined(directory, path, max_bytes=512 * 1024)
            if path.stat() != prior or hashlib.sha256(body).hexdigest() != FONT_BODIES[name]["sha256"]:
                raise ValueError("Source Mermaid fixed font bytes changed")
        else:
            body, _ = read_source_web_font(name, deadline=deadline)
        total += len(body)
        if total > MAX_FONT_BYTES or len(body) != FONT_BODIES[name]["bytes"]:
            raise ValueError("Source Mermaid fixed faces exceed unchanged whole-body admission")
        faces.append(
            {
                "postscript_name": name,
                "family": FAMILY,
                "weight": FONT_BODIES[name]["weight"],
                "style": FONT_BODIES[name]["style"],
                "sha256": FONT_BODIES[name]["sha256"],
                "bytes": len(body),
                "data": base64.b64encode(body).decode("ascii"),
            }
        )
    return {"schema_version": SCHEMA, "family": FAMILY, "faces": faces, "license": license_bytes.decode("utf-8")}


def default_font_profile_bytes(*, deadline: float | None = None) -> bytes:
    return (json.dumps(default_font_profile(deadline=deadline), sort_keys=True, separators=(",", ":")) + "\n").encode()


def default_font_script_bytes() -> bytes:
    path = Path(__file__).with_name(SCRIPT_NAME)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 64 * 1024:
        raise ValueError("Source Mermaid before-layout constructor is not a bounded SDK asset")
    return path.read_bytes()


def default_font_loader_expression(profile: dict[str, Any]) -> str:
    """Use exactly the same Source constructor in the independent CDP reader."""
    script = default_font_script_bytes().decode("utf-8")
    marker = "export async function loadSourceDefaultFonts(profile) {"
    begin = script.index(marker) + len("export ")
    end = script.index("\n// END_SOURCE_BROWSER_CONSTRUCTOR", begin)
    function = script[begin:end]
    return "(" + function + ")(" + json.dumps(profile, separators=(",", ":")) + ")"


def validate_default_font_buffers(raw: object, *, deadline: float | None = None) -> None:
    """Check portable DATA against Source bytes; this grants no process owner."""
    expected = default_font_profile(deadline=deadline)
    faces = [
        {key: face[key] for key in ("postscript_name", "family", "weight", "style", "sha256", "bytes")}
        for face in expected["faces"]
    ]
    if raw != {"schema_version": SCHEMA, "family": FAMILY, "faces": faces, "status": "loaded-before-layout"}:
        raise ValueError("actual Source font constructor buffers differ from the declared licensed default")


def validate_embedded_default_font_style(text: str) -> None:
    """Admit only exact Source-owned used-face CSS and its complete OFL notice."""
    profile = default_font_profile()
    prefix = "/*" + profile["license"].replace("*/", "* /") + "*/\n"
    if not text.startswith(prefix):
        raise ValueError("Source SVG licensed-font notice differs")
    remainder = text[len(prefix) :]
    originals = {
        "@font-face{font-family:'Template Liberation Sans';font-style:"
        + face["style"]
        + ";font-weight:"
        + face["weight"]
        + ";src:url(data:font/ttf;base64,"
        + face["data"]
        + ")}\n"
        for face in profile["faces"]
    }
    seen = set()
    while remainder:
        matches = [face for face in originals if remainder.startswith(face)]
        if len(matches) != 1 or matches[0] in seen:
            raise ValueError("Source SVG font style is not the exact fixed licensed face body")
        seen.add(matches[0])
        remainder = remainder[len(matches[0]) :]
    if not seen:
        raise ValueError("Source SVG font style lacks an actual used face")
