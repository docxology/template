"""One genuinely supervised original SVG-only browser, fresh ordered targets.

The interactive callback is invoked by the actual Popen/guardian owner. All
occurrence observations bind to that shared real process after its signed exit;
no transported JSON or synthetic per-image PID constructs a browser owner.
"""

from __future__ import annotations

import base64
import hashlib
import shutil
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_citation_process_custody import (
    OriginalCitationToolObserver,
)
from infrastructure.reporting.native_format_browser_driver import DevTools
from infrastructure.reporting.native_format_pdf_source_decode_bounds import (
    SourceImageDecodeBudget,
)
from infrastructure.reporting.native_format_html_source_shaping import select_source_html_shaper
from infrastructure.reporting.native_mermaid_font_bodies import NativeMermaidFontBodies
from infrastructure.reporting.native_mermaid_runtime_selection import (
    NativeMermaidRuntimeAdmission,
)
from infrastructure.reporting.native_mermaid_svg_paint import (
    MAX_PIXELS,
    PAINT_BROWSER_FLAGS,
    REMAINING_ADMISSION,
    SCHEMA as PAINT_SCHEMA,
    _evaluate,
    _platform_fonts,
    png_pixels,
    preflight_original_mermaid_svg,
)
from infrastructure.reporting.native_pdf_citation_runtime import CitationRuntime
from infrastructure.reporting.native_tool_process import NativeLiveToolProcess

SCHEMA = "template-native-original-svg-ordered-batch-paint-v1"


def _live_endpoint(endpoint: Path, live: NativeLiveToolProcess) -> tuple[int, str]:
    while True:
        live.verify_live()
        try:
            if endpoint.stat().st_size > 4096 or endpoint.is_symlink():
                raise ValueError("actual Source browser endpoint is unbounded/aliased")
            lines = endpoint.read_text().splitlines()
        except FileNotFoundError:
            lines = []
        if (
            len(lines) == 2
            and lines[0].isdecimal()
            and 0 < int(lines[0]) < 65536
            and lines[1].startswith("/devtools/browser/")
        ):
            return int(lines[0]), lines[1]
        time.sleep(0.02)


def observe_original_svg_batch_paint(
    root: Path,
    directory: Path,
    originals: tuple[tuple[str, bytes], ...],
    *,
    runtime_admission: NativeMermaidRuntimeAdmission,
    font_bodies: NativeMermaidFontBodies,
    decoded_pixel_budget: SourceImageDecodeBudget,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    on_original_tool: OriginalCitationToolObserver,
) -> dict[str, Any]:
    remaining(deadline)
    if not 0 < len(originals) <= 100 or len({identity for identity, _ in originals}) != len(originals):
        raise ValueError("Source-only batch paint requires every ordered distinct original occurrence")
    if font_bodies.source is not runtime_admission.source or font_bodies.producer is not runtime_admission.producer:
        raise ValueError("Source-only batch paint requires the same genuine Source runtime/font body owners")
    font_bodies.verify_live(deadline=deadline)
    shaper = select_source_html_shaper(deadline=deadline)
    before = runtime_admission.observe(deadline=deadline)["chrome"]
    tool = CitationRuntime(
        root,
        directory,
        env=env,
        deadline=deadline,
        run_id=run_id,
        on_original_tool=on_original_tool,
    )
    assets: dict[str, bytes] = {}
    source_paths = []
    for ordinal, (identity, svg) in enumerate(originals):
        preflight_original_mermaid_svg(svg)
        source = tool.freeze(f"source-{ordinal:04d}.svg", svg)
        source_paths.append(source)
        html = (
            '<!doctype html><html><head><meta charset="utf-8"></head>'
            '<body style="background:white"><div id="container">' + svg.decode("utf-8") + "</div></body></html>"
        ).encode()
        tool.freeze(f"source-{ordinal:04d}.html", html)
        assets[f"/source-{ordinal:04d}.html"] = html

    class Assets(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            data = assets.get(self.path)
            if data is None:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; font-src 'none'; connect-src 'none'",
            )
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, format: str, *args: Any) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Assets)
    server.daemon_threads = True
    serving = threading.Thread(target=server.serve_forever, daemon=True)
    serving.start()
    origin = f"http://127.0.0.1:{server.server_port}"
    profile = tool.directory / "profile"
    chrome = runtime_admission.selection.chrome_executable.resolve(strict=True)
    arguments = [*PAINT_BROWSER_FLAGS, f"--user-data-dir={profile}", "about:blank"]
    rows: list[dict[str, Any]] = []
    observed_owner = None
    started = time.monotonic()

    def paint(live: NativeLiveToolProcess) -> None:
        nonlocal observed_owner
        live.verify_live()
        observed_owner = live.pid
        if tuple(live.command) != (str(chrome), *arguments) or live.deadline > deadline:
            raise ValueError("actual supervised Source-only browser command/original clock differs")
        # The endpoint is created by this actual held browser; its process
        # capability remains live during each CDP request and original target.
        port, route = _live_endpoint(profile / "DevToolsActivePort", live)
        client = DevTools(port, route, deadline)
        client.allowed_origin = origin
        try:
            version = client.call("Browser.getVersion")
            for ordinal, (identity, svg) in enumerate(originals):
                live.verify_live()
                font_bodies.verify_live(deadline=deadline)
                client.events.clear()
                target = client.call("Target.createTarget", {"url": "about:blank"})["targetId"]
                session = client.call("Target.attachToTarget", {"targetId": target, "flatten": True})["sessionId"]
                try:
                    client.call("Page.enable", session=session)
                    client.call("Network.enable", session=session)
                    client.call(
                        "Fetch.enable",
                        {
                            "patterns": [
                                {"urlPattern": "http://*"},
                                {"urlPattern": "https://*"},
                            ]
                        },
                        session=session,
                    )
                    client.call(
                        "Network.setBlockedURLs",
                        {"urls": ["ws://*", "wss://*"]},
                        session=session,
                    )
                    client.call(
                        "Emulation.setDeviceMetricsOverride",
                        {
                            "width": 1400,
                            "height": 900,
                            "deviceScaleFactor": 1,
                            "mobile": False,
                        },
                        session=session,
                    )
                    url = origin + f"/source-{ordinal:04d}.html"
                    client.call("Page.navigate", {"url": url}, session=session)
                    while True:
                        live.verify_live()
                        readiness = client.call(
                            "Runtime.evaluate",
                            {
                                "expression": "document.readyState==='complete' && !!document.querySelector('svg')",
                                "returnByValue": True,
                            },
                            session=session,
                        )
                        if readiness.get("result", {}).get("value") is True:
                            break
                        remaining(deadline)
                        time.sleep(0.02)
                    original_dom = _evaluate(client, session)
                    clip = original_dom["clip"]
                    if (
                        any(type(clip[key]) is not int for key in ("x", "y", "width", "height"))
                        or min(clip["x"], clip["y"]) < 0
                        or min(clip["width"], clip["height"]) <= 0
                        or clip["width"] * clip["height"] > MAX_PIXELS
                        or clip["height"] > 30000
                        or clip["width"] > 4096
                    ):
                        raise ValueError("Source-only original exact clip exceeds unchanged finite admission")
                    client.call(
                        "Emulation.setDeviceMetricsOverride",
                        {
                            "width": clip["x"] + clip["width"],
                            "height": clip["y"] + clip["height"],
                            "deviceScaleFactor": 1,
                            "mobile": False,
                        },
                        session=session,
                    )
                    painted_dom = _evaluate(client, session)
                    owners, usage = _platform_fonts(client, session)
                    fonts = font_bodies.portable_fonts(usage, deadline=deadline)
                    glyph_bodies = [
                        {
                            "owner_index": owner["owner_index"],
                            "original_text": owner["text"],
                            "declared_face_bodies": [
                                font_bodies.unshaped_glyph_bodies(
                                    font["postScriptName"],
                                    owner["text"],
                                    deadline=deadline,
                                )
                                for font in owner["platform_fonts"]
                            ],
                        }
                        for owner in owners
                    ]
                    shaped_bodies = [
                        {
                            "owner_index": owner["owner_index"],
                            "original_text": owner["text"],
                            "declared_face_shaping": [
                                font_bodies.shaped_source_glyph_bodies(
                                    shaper, font["postScriptName"], owner["text"], deadline=deadline
                                )
                                for font in owner["platform_fonts"]
                            ],
                        }
                        for owner in owners
                    ]
                    decoded_pixel_budget.admit_header(clip["width"], clip["height"])
                    capture = client.call(
                        "Page.captureScreenshot",
                        {"format": "png", "captureBeyondViewport": True, "clip": clip},
                        session=session,
                    )
                    pixels = base64.b64decode(capture["data"], validate=True)
                    observed_pixels = png_pixels(pixels, decoded_pixel_budget=decoded_pixel_budget)
                    if (observed_pixels["width"], observed_pixels["height"]) != (
                        clip["width"],
                        clip["height"],
                    ):
                        raise ValueError("actual Source-only native paint omitted complete original clip")
                    pixel_path = tool.directory / f"paint-{ordinal:04d}.png"
                    pixel_path.write_bytes(pixels)
                    events = client.events.copy()
                    for event in events:
                        if (
                            event.get("method") == "Network.requestWillBeSent"
                            and event["params"]["request"]["url"] != url
                        ):
                            raise ValueError("actual Source-only original SVG fetched an undeclared resource")
                        if event.get("method") == "Network.loadingFailed":
                            raise ValueError("actual Source-only SVG retains failed resource load")
                    font_bodies.verify_live(deadline=deadline)
                    rows.append(
                        {
                            "ordinal": ordinal,
                            "identity": identity,
                            "preflight": preflight_original_mermaid_svg(svg),
                            "original_dom": original_dom,
                            "painted_dom": painted_dom,
                            "text_owners": owners,
                            "fonts": fonts,
                            "paint": observed_pixels,
                            "paint_path": pixel_path,
                            "browser_version": version,
                            "font_body_glyphs": glyph_bodies,
                            "font_shaped_bodies": shaped_bodies,
                            "events": events,
                        }
                    )
                finally:
                    client.call("Target.closeTarget", {"targetId": target})
            live.verify_live()
            client.call("Browser.close")
        finally:
            client.socket.close()

    try:
        process = tool.tool(str(chrome), arguments, "original-svg-ordered-batch-paint", while_live=paint)
    finally:
        server.shutdown()
        server.server_close()
        serving.join(timeout=max(0, min(2, deadline - time.monotonic())))
        shaper.close(deadline=deadline)
    if observed_owner != process["pid"] or len(rows) != len(originals):
        raise ValueError("actual Source-only batch browser invocation/ordered completion differs")
    after = runtime_admission.observe(deadline=deadline)["chrome"]
    if before != after:
        raise ValueError("actual complete Source-only browser body closure changed during batch paint")
    font_bodies.verify_terminal_bytes(deadline=deadline)
    if profile.exists():
        shutil.rmtree(profile)
    tool.unchanged()
    paintings = []
    for row, source_path in zip(rows, source_paths, strict=True):
        if source_path.read_bytes() != originals[row["ordinal"]][1]:
            raise ValueError("actual Source-only batch input changed before original retention")
        paint_path = row.pop("paint_path")
        result = {
            "schema_version": PAINT_SCHEMA,
            **{key: value for key, value in row.items() if key not in {"ordinal", "identity"}},
            "browser_command": process["command"],
            "browser_original_exit": process["original_exit_code"],
            "browser_pid": process["pid"],
            "stdout_sha256": process["raw_stdout"]["sha256"],
            "stderr_sha256": process["raw_stderr"]["sha256"],
            "runtime_before": before,
            "runtime_after": after,
            "elapsed_seconds": round(time.monotonic() - started, 6),
            "remaining_admission": list(REMAINING_ADMISSION),
        }
        observation = {**result, "content_digest": canonical_digest(result)}
        paintings.append(
            {
                "ordinal": row["ordinal"],
                "identity": row["identity"],
                "paint": observation,
                "paint_artifact": {
                    "path": paint_path.relative_to(root).as_posix(),
                    "bytes": paint_path.stat().st_size,
                    "sha256": hashlib.sha256(paint_path.read_bytes()).hexdigest(),
                },
            }
        )
    result = {
        "schema_version": SCHEMA,
        "run_id": run_id,
        "shared_process": process,
        "shared_process_artifact": dict(tool.tools[-1]),
        "occurrences": paintings,
    }
    return {**result, "content_digest": canonical_digest(result)}
