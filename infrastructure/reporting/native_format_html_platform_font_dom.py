"""Actual CDP platform-font usage, without candidate DOM mutation."""

from __future__ import annotations

import math
import time
from typing import Any, Protocol


def _remaining(deadline: float) -> None:
    if type(deadline) not in {int, float} or not math.isfinite(deadline) or time.monotonic() >= deadline:
        raise TimeoutError("native font capture exhausted the original finite caller deadline")


class FontDevTools(Protocol):
    def call(
        self, method: str, params: dict[str, Any] | None = None, *, session: str | None = None
    ) -> dict[str, Any]: ...


def collect_platform_font_usage(client: FontDevTools, session: str, dom: dict[str, Any], *, deadline: float) -> None:
    """Collect real font usage for each text row's native parent element.

    CDP reports all fonts rendering child text nodes, rather than a physical
    byte identity or per-codepoint shaping result. Consumers must retain the
    multi-face/fallback ambiguity and independently resolve exact font bytes.
    """
    _remaining(deadline)
    rows = dom.get("text")
    if not isinstance(rows, list) or len(rows) > 200000:
        raise ValueError("actual font observations exceed the existing text census bound")
    client.call("DOM.enable", session=session)
    client.call("CSS.enable", session=session)
    client.call("DOM.getDocument", {"depth": 0}, session=session)
    for index, row in enumerate(rows):
        _remaining(deadline)
        observed = client.call(
            "Runtime.evaluate",
            {"expression": f"globalThis.__native_glyph_text_nodes[{index}].parentElement", "returnByValue": False},
            session=session,
        )
        if observed.get("exceptionDetails") or not isinstance(observed.get("result", {}).get("objectId"), str):
            raise ValueError("native font capture lost its original text-node identity")
        object_id = observed["result"]["objectId"]
        try:
            node = client.call("DOM.requestNode", {"objectId": object_id}, session=session)
            fonts = client.call("CSS.getPlatformFontsForNode", {"nodeId": node["nodeId"]}, session=session).get("fonts")
            if not isinstance(fonts, list) or len(fonts) > 256:
                raise ValueError("actual platform font usage is missing/unbounded")
            for font in fonts:
                if (
                    not isinstance(font.get("familyName"), str)
                    or not isinstance(font.get("postScriptName"), str)
                    or type(font.get("isCustomFont")) is not bool
                    or type(font.get("glyphCount")) not in {int, float}
                    or not 0 < font["glyphCount"] <= 200000
                ):
                    raise ValueError("actual CDP platform font row is malformed")
            row["platform_fonts"] = fonts
        finally:
            client.call("Runtime.releaseObject", {"objectId": object_id}, session=session)
    _remaining(deadline)
