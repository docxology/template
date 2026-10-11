"""Source-owned finite platform font providers, reconstructed by each reader.

The Linux cohorts cover the original DejaVu control and the Source renderer's
Liberation Serif/Mono/Sans regular, bold and italic physical faces. Other families
need their own declared source/provider/outline model.
A callable provider does not discharge OS, shaping, style or hinting obligations.
"""

from __future__ import annotations

import hashlib
import json
import sys
from infrastructure.rendering._web_font_assets import FONT_BODIES
from dataclasses import dataclass
from typing import Any

from infrastructure.reporting.native_format_html_platform_font_probe import (
    probe_platform_fonts,
)
from infrastructure.reporting.native_format_html_source_metadata import (
    remaining_seconds,
)

_TOKEN = object()
LINUX_POSTSCRIPT_NAMES = (
    "DejaVuSansMono",
    "LiberationSerif",
    "LiberationSerif-Bold",
    "LiberationSerif-Italic",
    "LiberationSerif-BoldItalic",
    "LiberationMono",
    "LiberationMono-Bold",
    "LiberationMono-Italic",
    "LiberationMono-BoldItalic",
    "LiberationSans",
    "LiberationSans-Bold",
    "LiberationSans-Italic",
    "LiberationSans-BoldItalic",
)
UNSUPPORTED_PLATFORM = "HTML source font provider has no equivalent declared physical platform/font cohort"


@dataclass(frozen=True)
class HTMLFontProvider:
    """A current Source factory result; a profile JSON is never this capability."""

    _token: object
    platform: str
    cohort: tuple[str, ...]
    source_assets: bool = False

    def description(self) -> dict[str, Any]:
        if self._token is not _TOKEN:
            raise ValueError("HTML font provider did not originate in current Source")
        data = {
            "schema_version": "template-source-html-font-provider-profile-v1",
            "platform": self.platform,
            "cohort": list(self.cohort),
            "implementation_module": "infrastructure.reporting.native_format_html_platform_font_probe",
            "mapping": "Source font body/HarfBuzz"
            if self.source_assets
            else "CoreText"
            if self.platform == "darwin"
            else "Fontconfig/FreeType",
            "source_declared_family_cohorts": [
                "original-dejavu-mono-control",
                "renderer-liberation-serif-mono-sans",
            ],
            "whole_style_shaping_OS_admission": False,
        }
        return {
            **data,
            "sha256": hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        }

    def validate_request(self, request: dict[str, Any], *, deadline: float) -> None:
        remaining_seconds(deadline)
        if self._token is not _TOKEN or self.platform != sys.platform:
            raise ValueError("HTML font provider is not this reader's actual current Source platform")
        fonts = request.get("fonts")
        if request.get("schema_version") != "template-native-html-platform-font-request-v1" or not isinstance(
            fonts, list
        ):
            raise ValueError("HTML provider needs the independently compiled source/font request")
        if self.source_assets != (request.get("font_provider") == "source-web-font-assets-v1"):
            raise ValueError("Source font body/system provider role changed")
        names = tuple(sorted({row["postscript_name"] for row in fonts}))
        if self.source_assets and (not names or any(name not in FONT_BODIES for name in names)):
            raise ValueError("Source web font request is outside its independently nominated body cohort")
        if (
            not self.source_assets
            and self.platform == "linux"
            and (not names or any(name not in LINUX_POSTSCRIPT_NAMES for name in names))
        ):
            raise ValueError(UNSUPPORTED_PLATFORM)
        if names != self.cohort:
            raise ValueError("HTML Source provider physical face cohort changed")
        remaining_seconds(deadline)

    def probe(self, request: dict[str, Any], *, deadline: float) -> dict[str, Any]:
        """Actual Source callable for separately scheduled component controls."""
        self.validate_request(request, deadline=deadline)
        result = probe_platform_fonts(request, deadline=deadline)
        self.validate_probe(request, result, deadline=deadline)
        return result

    def validate_probe(self, request: dict[str, Any], probe: dict[str, Any], *, deadline: float) -> None:
        self.validate_request(request, deadline=deadline)
        if probe["platform"]["system"] != ("Linux" if self.platform == "linux" else "Darwin"):
            raise ValueError("genuine font probe was executed on a different physical Source provider platform")
        fonts = probe["fonts"]
        if len(fonts) != len(request["fonts"]):
            raise ValueError("actual font provider omitted requested Source faces")
        for expected, actual in zip(request["fonts"], fonts, strict=True):
            if (
                actual["postscript_name"] != expected["postscript_name"]
                or actual["characters"] != expected["characters"]
            ):
                raise ValueError("actual font provider substituted Source face/codepoints")
            if self.source_assets and (
                actual.get("provider") != "Source font body/HarfBuzz" or actual.get("face_index") != 0
            ):
                raise ValueError("actual Source font body provider lacked its genuine physical face")
            if (
                not self.source_assets
                and self.platform == "linux"
                and (actual.get("provider") != "Fontconfig/FreeType" or type(actual.get("face_index")) is not int)
            ):
                raise ValueError("Linux physical Source provider lacked genuine FreeType face-index mapping")
        remaining_seconds(deadline)


def select_html_font_provider(request: dict[str, Any], *, deadline: float) -> HTMLFontProvider | None:
    """Select a genuine finite provider before removing a platform blocker."""
    remaining_seconds(deadline)
    rows = request.get("fonts")
    if not isinstance(rows, list):
        raise ValueError("HTML Source font request is malformed")
    cohort = tuple(sorted({row["postscript_name"] for row in rows}))
    source_assets = request.get("font_provider") == "source-web-font-assets-v1"
    if source_assets:
        if sys.platform not in ("darwin", "linux") or any(name not in FONT_BODIES for name in cohort):
            return None
        return HTMLFontProvider(_TOKEN, sys.platform, cohort, True)
    if sys.platform not in ("darwin", "linux") or (
        sys.platform == "linux" and any(name not in LINUX_POSTSCRIPT_NAMES for name in cohort)
    ):
        return None
    return HTMLFontProvider(_TOKEN, sys.platform, cohort)
