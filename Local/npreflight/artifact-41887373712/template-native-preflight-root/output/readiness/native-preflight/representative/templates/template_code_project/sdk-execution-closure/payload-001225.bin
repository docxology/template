"""Fresh SVG-only Chromium paint and actual glyph/font/process observations.

This reader executes no Mermaid/Node code. It paints a strictly preflighted
original SVG, preserving the original CLI's body/container, viewport and exact
floor/ceil SVG clip. Independent source graph/topology and original producer
custody must separately be admitted before the enclosing occurrence is covered.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import math
import re
import shutil
import subprocess  # nosec B404 - explicit admitted browser, fixed private flags
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, cast

from defusedxml.ElementTree import fromstring
from PIL import Image

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.native_format_browser_driver import DevTools, _browser_endpoint
from infrastructure.reporting.native_format_browser_runtime import observe_runtime, validate_runtime
from infrastructure.reporting.native_format_pdf_source_decode_bounds import SourceImageDecodeBudget
from infrastructure.reporting.native_mermaid_runtime_custody import (
    observe_platform_font_files,
    validate_platform_font_files,
)

SCHEMA = "template-native-mermaid-original-svg-paint-original-ink-styles-v3"
MAX_SVG_BYTES = 8 * 1024 * 1024
MAX_PIXELS = 60_000_000
# The selected official CLI's Puppeteer launcher fixes sRGB and headless-shell
# paint. The independent Source-only reader must use that declared profile;
# display-default color management or an added GPU override changes pixels.
# These literals come from admitted primary Source, never from target pixels.
PAINT_BROWSER_FLAGS = (
    "--headless",
    "--hide-scrollbars",
    "--mute-audio",
    "--force-color-profile=srgb",
    "--no-first-run",
    "--disable-background-networking",
    "--disable-extensions",
    "--disable-sync",
    "--remote-debugging-port=0",
    "--proxy-server=http://127.0.0.1:9",
    "--proxy-bypass-list=127.0.0.1",
)
REMAINING_ADMISSION = (
    "independent unclipped source glyph/stroke/marker ink and SVG clip/mask/filter semantics",
    "outer original browser process and loaded operating-system library custody",
)


def preflight_original_mermaid_svg(data: bytes) -> dict[str, Any]:
    """Reject active/external resources before handing any SVG to the browser."""
    if not data or len(data) > MAX_SVG_BYTES or re.search(rb"<!DOCTYPE|<!ENTITY|<\?", data, re.I):
        raise ValueError("original Mermaid SVG has an unbounded/active XML envelope")
    root = fromstring(data)
    nodes = list(root.iter())
    if root.tag != "{http://www.w3.org/2000/svg}svg" or not 0 < len(nodes) <= 20000:
        raise ValueError("original Mermaid SVG root/node census is absent/unbounded")
    forbidden = {
        "script",
        "iframe",
        "object",
        "embed",
        "image",
        "a",
        "animate",
        "animateMotion",
        "animateTransform",
        "set",
    }
    for node in nodes:
        tag = node.tag.rsplit("}", 1)[-1]
        if tag in forbidden:
            raise ValueError("original Mermaid SVG contains an active/external element")
        for key, value in node.attrib.items():
            name = key.rsplit("}", 1)[-1]
            if name.lower().startswith("on") or name in {"src", "srcset"}:
                raise ValueError("original Mermaid SVG contains an active event/resource attribute")
            if name == "href" and not re.fullmatch(r"#[A-Za-z_][A-Za-z0-9_.:-]*", value):
                raise ValueError("original Mermaid SVG resource escapes its literal local member closure")
            if name == "style":
                _css(value)
        if tag == "style":
            text = "".join(node.itertext())
            if node.get("id") == "template-source-mermaid-licensed-fonts":
                from infrastructure.rendering._mermaid_source_font_default import validate_embedded_default_font_style

                validate_embedded_default_font_style(text)
            else:
                _css(text)
    return {"svg_sha256": hashlib.sha256(data).hexdigest(), "svg_bytes": len(data), "nodes": len(nodes)}


def _css(value: str) -> None:
    if re.search(r"@import|@font-face|expression\s*\(|javascript\s*:|https?\s*:|data\s*:", value, re.I):
        raise ValueError("original SVG CSS contains unsupported external/active font/resource semantics")
    for match in re.finditer(r"url\s*\(([^)]*)\)", value, re.I):
        if not re.fullmatch(r"\s*['\"]?#[A-Za-z_][A-Za-z0-9_.:-]*['\"]?\s*", match[1]):
            raise ValueError("original SVG CSS resource is not a literal local marker")


def png_pixels(data: bytes, *, decoded_pixel_budget: SourceImageDecodeBudget) -> dict[str, Any]:
    """Admit PNG dimensions before decoded full-page RGB allocation."""
    if len(data) > 64 * 1024 * 1024:
        raise ValueError("original SVG paint PNG exceeds finite encoded bytes")
    with Image.open(io.BytesIO(data)) as image:
        width, height = image.size
        if image.format != "PNG" or width <= 0 or height <= 0 or width * height > MAX_PIXELS:
            raise ValueError("original SVG paint dimensions exceed decoded-pixel admission")
        if image.mode not in {"RGB", "RGBA"}:
            raise ValueError("original SVG paint uses unsupported native PNG color channels")
        decoded_pixel_budget.admit_header(width, height)
        image.load()
        if image.mode == "RGBA":
            alpha = image.getchannel("A")
            try:
                if alpha.getextrema() != (255, 255):
                    raise ValueError("original SVG white-background paint has nonopaque native pixels")
            finally:
                alpha.close()
        rgb = image.convert("RGB")
        try:
            digest = hashlib.sha256(rgb.tobytes()).hexdigest()
            extrema = rgb.getextrema()
        finally:
            rgb.close()
    if not isinstance(extrema, tuple) or len(extrema) != 3:
        raise ValueError("original SVG paint omitted exact RGB channel extrema")
    blank = True
    for band in extrema:
        if not isinstance(band, tuple) or len(band) != 2:
            raise ValueError("original SVG paint contains invalid RGB channel extrema")
        if band != (255, 255):
            blank = False
    if blank:
        raise ValueError("actual original SVG paint is blank")
    return {"width": width, "height": height, "rgb_sha256": digest, "png_sha256": hashlib.sha256(data).hexdigest()}


_OBSERVE = r"""(async()=>{
await document.fonts.ready;
const svg=document.querySelector('svg');
if(!svg || document.querySelectorAll('svg').length!==1) throw Error('one original SVG required');
const rect=(r)=>({x:r.x,y:r.y,width:r.width,height:r.height});
const root=rect(svg.getBoundingClientRect());
const elements=[...svg.querySelectorAll('*')];
if(elements.length>20000) throw Error('original SVG DOM bound exceeded');
const originalStyle=(s)=>({
fontFamily:s.fontFamily,fontSize:s.fontSize,fontWeight:s.fontWeight,fontStyle:s.fontStyle,
fill:s.fill,stroke:s.stroke,color:s.color,opacity:s.opacity,
fillOpacity:s.fillOpacity,strokeOpacity:s.strokeOpacity,strokeWidth:s.strokeWidth,
strokeLinecap:s.strokeLinecap,strokeLinejoin:s.strokeLinejoin,strokeMiterlimit:s.strokeMiterlimit,
display:s.display,visibility:s.visibility,vectorEffect:s.vectorEffect,clipPath:s.clipPath,mask:s.mask,filter:s.filter,overflow:s.overflow,
fontKerning:s.fontKerning,fontVariantLigatures:s.fontVariantLigatures,
markerStart:s.markerStart,markerMid:s.markerMid,markerEnd:s.markerEnd});
const rows=elements.map((e,i)=>{
const s=getComputedStyle(e); const r=e.getBoundingClientRect();
return {index:i,tag:e.localName,id:e.id,text:[...e.childNodes].filter(n=>n.nodeType===3).map(n=>n.textContent).join(''),
box:rect(r),visible:s.display!=='none'&&s.visibility==='visible'&&s.opacity!=='0',
style:originalStyle(s),
attributes:Object.fromEntries([...e.attributes].map(a=>[a.name,a.value]))};});
return {root,rows,root_style:originalStyle(getComputedStyle(svg)),
root_attributes:Object.fromEntries([...svg.attributes].map(a=>[a.name,a.value])),fonts_status:document.fonts.status,
clip:{x:Math.floor(root.x),y:Math.floor(root.y),width:Math.ceil(root.width),height:Math.ceil(root.height),scale:1}};
})()"""


def _evaluate(client: DevTools, session: str) -> dict[str, Any]:
    result = client.call(
        "Runtime.evaluate", {"expression": _OBSERVE, "returnByValue": True, "awaitPromise": True}, session=session
    )
    if "exceptionDetails" in result or not isinstance(result.get("result", {}).get("value"), dict):
        raise ValueError("fresh SVG-only browser refused actual DOM/glyph observation")
    return cast(dict[str, Any], result["result"]["value"])


def _platform_fonts(client: DevTools, session: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    client.call("DOM.enable", session=session)
    client.call("CSS.enable", session=session)
    tree = client.call("DOM.getDocument", {"depth": -1, "pierce": True}, session=session)["root"]
    selected = []
    stack = [tree]
    total = 0
    while stack:
        node = stack.pop()
        total += 1
        if total > 40000:
            raise ValueError("actual SVG platform-font DOM census exceeds finite bound")
        children = node.get("children", [])
        if node.get("nodeType") == 1 and any(
            child.get("nodeType") == 3 and child.get("nodeValue", "").strip() for child in children
        ):
            if node.get("localName") not in {"style", "title", "desc"}:
                selected.append(node)
        stack.extend(reversed(children))
    if not 0 < len(selected) <= 1000:
        raise ValueError("actual SVG painted text-node census is absent/unbounded")
    owners, usage = [], []
    for index, node in enumerate(selected):
        fonts = client.call("CSS.getPlatformFontsForNode", {"nodeId": node["nodeId"]}, session=session)["fonts"]
        active = [row for row in fonts if row["glyphCount"] > 0]
        if not active:
            raise ValueError("actual source SVG label has no native painted glyph/font witness")
        owners.append(
            {
                "owner_index": index,
                "tag": node["localName"],
                "text": "".join(
                    child.get("nodeValue", "") for child in node.get("children", []) if child.get("nodeType") == 3
                ),
                "platform_fonts": active,
            }
        )
        usage.extend(active)
    return owners, usage


def observe_original_svg_paint(
    chrome: Path,
    svg: bytes,
    directory: Path,
    *,
    deadline: float,
    font_files: tuple[Path, ...],
    decoded_pixel_budget: SourceImageDecodeBudget,
    viewport_width: int = 1400,
    viewport_height: int = 900,
) -> dict[str, Any]:
    """Execute original SVG-only paint under actual before/after runtime holds."""
    if not math.isfinite(deadline) or time.monotonic() >= deadline:
        raise TimeoutError("original SVG paint requires its original finite deadline")
    if directory.exists() or not directory.parent.is_dir() or directory.parent.is_symlink():
        raise ValueError("original SVG paint requires a fresh private directory")
    if (
        type(viewport_width) is not int
        or type(viewport_height) is not int
        or not 1 <= viewport_width <= 4096
        or not 1 <= viewport_height <= 30000
    ):
        raise ValueError("original SVG paint viewport is outside its explicit finite bounds")
    preflight = preflight_original_mermaid_svg(svg)
    directory.mkdir(mode=0o700)
    source = directory / "original.svg"
    source.write_bytes(svg)
    html = (
        '<!doctype html><html><head><meta charset="utf-8"></head><body style="background:white"><div id="container">'
        + svg.decode("utf-8")
        + "</div></body></html>"
    ).encode()
    (directory / "original.html").write_bytes(html)
    chrome = chrome.resolve(strict=True)
    runtime_before = observe_runtime(chrome, deadline=deadline)
    profile = directory / "profile"
    command = [
        str(chrome),
        *PAINT_BROWSER_FLAGS,
        f"--user-data-dir={profile}",
        "about:blank",
    ]

    class Assets(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path != "/original.html":
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; font-src 'none'; connect-src 'none'",
            )
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)

        def log_message(self, format: str, *args: Any) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Assets)
    server.daemon_threads = True
    serving = threading.Thread(target=server.serve_forever, daemon=True)
    serving.start()
    origin = f"http://127.0.0.1:{server.server_port}"
    browser = None
    client = None
    closed = False
    started = time.monotonic()
    with (directory / "chrome.stdout").open("xb") as out, (directory / "chrome.stderr").open("xb") as err:
        try:
            browser = subprocess.Popen(command, stdout=out, stderr=err)  # nosec B603 - explicit admitted browser/fixed private flags
            port, route = _browser_endpoint(profile / "DevToolsActivePort", browser, deadline)
            client = DevTools(port, route, deadline)
            client.allowed_origin = origin
            version = client.call("Browser.getVersion")
            target = client.call("Target.createTarget", {"url": "about:blank"})["targetId"]
            session = client.call("Target.attachToTarget", {"targetId": target, "flatten": True})["sessionId"]
            client.call("Page.enable", session=session)
            client.call("Network.enable", session=session)
            client.call(
                "Fetch.enable", {"patterns": [{"urlPattern": "http://*"}, {"urlPattern": "https://*"}]}, session=session
            )
            client.call("Network.setBlockedURLs", {"urls": ["ws://*", "wss://*"]}, session=session)
            client.call(
                "Emulation.setDeviceMetricsOverride",
                {"width": viewport_width, "height": viewport_height, "deviceScaleFactor": 1, "mobile": False},
                session=session,
            )
            client.call("Page.navigate", {"url": origin + "/original.html"}, session=session)
            while True:
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
                if time.monotonic() >= deadline:
                    raise TimeoutError("original SVG did not reach genuine source-paint readiness")
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
                raise ValueError("original SVG exact native clip exceeds finite pixel/coordinate admission")
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
            fonts = observe_platform_font_files(usage, font_files, deadline=deadline)
            decoded_pixel_budget.admit_header(clip["width"], clip["height"])
            capture = client.call(
                "Page.captureScreenshot",
                {"format": "png", "captureBeyondViewport": True, "clip": clip},
                session=session,
            )
            pixels = base64.b64decode(capture["data"], validate=True)
            paint = png_pixels(pixels, decoded_pixel_budget=decoded_pixel_budget)
            if (paint["width"], paint["height"]) != (clip["width"], clip["height"]):
                raise ValueError("actual SVG native pixels do not cover the complete exact original clip")
            (directory / "paint.png").write_bytes(pixels)
            if observe_platform_font_files(usage, font_files, deadline=deadline) != fonts:
                raise ValueError("actual native platform fonts changed during original SVG screenshot")
            events = client.events.copy()
            for event in events:
                if event.get("method") == "Network.requestWillBeSent":
                    url = event["params"]["request"]["url"]
                    if url != origin + "/original.html":
                        raise ValueError("actual source SVG attempted an undeclared external/resource fetch")
                if event.get("method") == "Network.loadingFailed":
                    raise ValueError("actual original SVG paint retains a failed native resource load")
            client.call("Browser.close")
            closed = True
            exit_code = browser.wait(timeout=max(0.001, deadline - time.monotonic()))
            if exit_code != 0:
                raise ValueError("actual source-only SVG browser failed original exit0")
            if profile.exists():
                shutil.rmtree(profile)
            runtime_after = observe_runtime(chrome, deadline=deadline)
            if runtime_before != runtime_after or source.read_bytes() != svg:
                raise ValueError("original SVG/complete Chrome runtime changed during genuine paint")
            result = {
                "schema_version": SCHEMA,
                "preflight": preflight,
                "original_dom": original_dom,
                "painted_dom": painted_dom,
                "text_owners": owners,
                "fonts": fonts,
                "paint": paint,
                "browser_command": command,
                "browser_version": version,
                "browser_original_exit": exit_code,
                "browser_pid": browser.pid,
                "stdout_sha256": hashlib.sha256((directory / "chrome.stdout").read_bytes()).hexdigest(),
                "stderr_sha256": hashlib.sha256((directory / "chrome.stderr").read_bytes()).hexdigest(),
                "runtime_before": runtime_before,
                "runtime_after": runtime_after,
                "events": events,
                "elapsed_seconds": round(time.monotonic() - started, 6),
                "remaining_admission": list(REMAINING_ADMISSION),
            }
            (directory / "paint-observation.json").write_text(
                json.dumps(result, sort_keys=True, allow_nan=False) + "\n"
            )
            return {**result, "content_digest": canonical_digest(result)}
        finally:
            server.shutdown()
            server.server_close()
            serving.join(timeout=2)
            if client:
                client.socket.close()
            if browser and browser.poll() is None:
                browser.terminate()
                try:
                    browser.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    browser.kill()
                    browser.wait(timeout=2)
            if not closed:
                (directory / "paint.failed").write_text(
                    "actual SVG browser did not complete its original close/exit contract\n"
                )


def validate_original_svg_paint(
    raw: dict[str, Any],
    svg: bytes,
    painted_png: bytes,
    runtime: dict[str, Any],
    *,
    decoded_pixel_budget: SourceImageDecodeBudget,
) -> None:
    """Read original evidence without treating producer paths/claims as authority."""
    if raw.get("schema_version") != SCHEMA or raw.get("content_digest") != canonical_digest(
        {key: value for key, value in raw.items() if key != "content_digest"}
    ):
        raise ValueError("portable original SVG paint schema/digest differs")
    if raw.get("remaining_admission") != list(REMAINING_ADMISSION):
        raise ValueError("portable SVG paint omitted its unresolved original visibility/runtime obligations")
    if (
        preflight_original_mermaid_svg(svg) != raw["preflight"]
        or png_pixels(painted_png, decoded_pixel_budget=decoded_pixel_budget) != raw["paint"]
    ):
        raise ValueError("portable original SVG/paint consumed bytes differ")
    before, after = raw["runtime_before"], raw["runtime_after"]
    if before != after or before != runtime["chrome"]:
        raise ValueError("portable SVG paint omitted complete original held Chrome runtime")
    validate_runtime(
        before,
        before["executable"],
        next(
            row["sha256"]
            for row in before["files"]
            if row["kind"] == "file"
            and row["path"] == Path(before["executable"]).relative_to(before["root"]).as_posix()
        ),
    )
    validate_platform_font_files(raw["fonts"])
    if (
        type(raw["browser_original_exit"]) is not int
        or raw["browser_original_exit"] != 0
        or type(raw.get("browser_pid")) is not int
        or raw["browser_pid"] <= 0
    ):
        raise ValueError("portable original SVG paint omitted genuine browser exit/PID")
    command = raw["browser_command"]
    fixed = [
        before["executable"],
        *PAINT_BROWSER_FLAGS,
    ]
    if (
        not isinstance(command, list)
        or len(command) != len(fixed) + 2
        or command[: len(fixed)] != fixed
        or not command[-2].startswith("--user-data-dir=/")
        or command[-1] != "about:blank"
    ):
        raise ValueError("portable original SVG-only browser command/network isolation differs")
    owners = raw["text_owners"]
    if (
        not isinstance(owners, list)
        or not 0 < len(owners) <= 1000
        or [row["owner_index"] for row in owners] != list(range(len(owners)))
    ):
        raise ValueError("portable actual source SVG text/font ownership is incomplete")
    if [font for owner in owners for font in owner["platform_fonts"]] != raw["fonts"]["platform_fonts"]:
        raise ValueError("portable actual SVG label glyphs do not consume complete admitted platform-font faces")
    for dom in (raw["original_dom"], raw["painted_dom"]):
        if dom["fonts_status"] != "loaded" or not isinstance(dom["rows"], list) or not 0 < len(dom["rows"]) <= 20000:
            raise ValueError("portable actual SVG DOM/font readiness is incomplete")
        for box in [dom["root"], *(row["box"] for row in dom["rows"])]:
            if set(box) != {"x", "y", "width", "height"} or any(
                type(value) not in {int, float} or not math.isfinite(value) for value in box.values()
            ):
                raise ValueError("portable actual SVG glyph/geometry has invalid coordinates")
    clip = raw["original_dom"]["clip"]
    if (raw["paint"]["width"], raw["paint"]["height"]) != (clip["width"], clip["height"]):
        raise ValueError("portable complete original SVG clip does not match painted pixel dimensions")


def inspect_original_svg_native_pixels(
    paint: dict[str, Any], original_native_png: bytes, *, decoded_pixel_budget: SourceImageDecodeBudget
) -> dict[str, Any]:
    """Require complete decoded dimensions and every RGB pixel, without tolerance."""
    native = png_pixels(original_native_png, decoded_pixel_budget=decoded_pixel_budget)
    if any(paint["paint"][key] != native[key] for key in ("width", "height", "rgb_sha256")):
        raise ValueError("independently painted source SVG differs from original native Mermaid pixels")
    return {
        "source_svg_sha256": paint["preflight"]["svg_sha256"],
        "source_paint": paint["paint"],
        "native_paint": native,
    }
