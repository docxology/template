"""Finite loopback-only Chromium DevTools driver using the standard library."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import socket
import struct
import subprocess  # nosec B404 - fixed admitted executable/arguments
import time
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit
from pathlib import Path
from typing import Any, cast

MAX_MESSAGE = 128 * 1024 * 1024


class DevTools:
    """Minimal RFC6455 client for one fresh Chrome loopback endpoint."""

    def __init__(self, port: int, route: str, deadline: float) -> None:
        if not 0 < port < 65536 or not route.startswith("/devtools/browser/"):
            raise ValueError("invalid fresh browser endpoint")
        self.deadline = deadline
        self.socket = socket.create_connection(("127.0.0.1", port), timeout=self.remaining())
        key = base64.b64encode(os.urandom(16)).decode()
        request = (
            f"GET {route} HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nUpgrade: websocket\r\n"
            f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
        )
        self.socket.sendall(request.encode())
        header = bytearray()
        while not header.endswith(b"\r\n\r\n"):
            header.extend(self._read(1))
            if len(header) > 16384:
                raise ValueError("oversized DevTools handshake")
        expected = base64.b64encode(
            hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()
        ).decode()  # nosec B324 - RFC6455
        lines = header.decode().split("\r\n")
        headers = {line.split(": ", 1)[0].lower(): line.split(": ", 1)[1] for line in lines[1:] if ": " in line}
        if not lines[0].startswith("HTTP/1.1 101 ") or headers.get("sec-websocket-accept") != expected:
            raise ValueError("DevTools handshake did not authenticate its fresh key")
        self.identifier = 0
        self.events: list[dict[str, Any]] = []
        self.allowed_origin: str | None = None
        self.cdn_responses: dict[str, bytes] = {}
        self.fulfilled: list[dict[str, str]] = []

    def remaining(self) -> float:
        value = self.deadline - time.monotonic()
        if value <= 0:
            raise TimeoutError("native browser original deadline expired")
        return min(value, 30)

    def _read(self, size: int) -> bytes:
        out = bytearray()
        while len(out) < size:
            self.socket.settimeout(self.remaining())
            chunk = self.socket.recv(size - len(out))
            if not chunk:
                raise ValueError("native browser unexpectedly closed DevTools")
            out.extend(chunk)
        return bytes(out)

    def _send(self, value: dict[str, Any]) -> None:
        content = json.dumps(value, separators=(",", ":")).encode()
        if len(content) > MAX_MESSAGE:
            raise ValueError("DevTools request too large")
        mask = os.urandom(4)
        size = len(content)
        prefix = (
            bytes([0x81, 0x80 | size])
            if size < 126
            else bytes([0x81, 0xFE]) + struct.pack("!H", size)
            if size < 65536
            else bytes([0x81, 0xFF]) + struct.pack("!Q", size)
        )
        self.socket.sendall(prefix + mask + bytes(v ^ mask[i % 4] for i, v in enumerate(content)))

    def _receive(self) -> dict[str, Any]:
        first, second = self._read(2)
        if first != 0x81 or second & 0x80:
            raise ValueError("unsupported native DevTools frame")
        size = second & 127
        if size == 126:
            size = struct.unpack("!H", self._read(2))[0]
        elif size == 127:
            size = struct.unpack("!Q", self._read(8))[0]
        if size > MAX_MESSAGE:
            raise ValueError("DevTools response exceeds finite budget")
        value = json.loads(self._read(size))
        if not isinstance(value, dict):
            raise ValueError("DevTools response is not an object")
        return value

    def call(self, method: str, params: dict[str, Any] | None = None, *, session: str | None = None) -> dict[str, Any]:
        self.identifier += 1
        request: dict[str, Any] = {"id": self.identifier, "method": method, "params": params or {}}
        if session:
            request["sessionId"] = session
        request_id = self.identifier
        self._send(request)
        while True:
            message = self._receive()
            if message.get("method") == "Fetch.requestPaused":
                paused = message["params"]
                self.identifier += 1
                allowed = self.allowed_origin and paused["request"]["url"].startswith(self.allowed_origin + "/")
                action: dict[str, Any] = {
                    "id": self.identifier,
                    "sessionId": message["sessionId"],
                    "method": "Fetch.continueRequest" if allowed else "Fetch.failRequest",
                    "params": {"requestId": paused["requestId"]},
                }
                url = paused["request"]["url"]
                if url in self.cdn_responses:
                    content = self.cdn_responses[url]
                    mime = (
                        "font/woff2"
                        if url.endswith(".woff2")
                        else "application/javascript"
                        if url.endswith(".js")
                        else "application/octet-stream"
                    )
                    action["method"] = "Fetch.fulfillRequest"
                    action["params"] = {
                        "requestId": paused["requestId"],
                        "responseCode": 200,
                        "responseHeaders": [
                            {"name": "Content-Type", "value": mime},
                            {"name": "Access-Control-Allow-Origin", "value": "*"},
                        ],
                        "body": base64.b64encode(content).decode(),
                    }
                    self.fulfilled.append({"url": url, "sha256": hashlib.sha256(content).hexdigest()})
                elif not allowed:
                    action["params"]["errorReason"] = "BlockedByClient"
                self._send(action)
            if message.get("id") == request_id:
                if "error" in message:
                    raise ValueError(f"native DevTools rejected {method}: {message['error']}")
                return cast(dict[str, Any], message["result"])
            self.events.append(message)
            if len(self.events) > 20000:
                raise ValueError("DevTools event budget exceeded")


def observe(
    chrome: Path,
    source: Path,
    profile: Path,
    width: int,
    output: Path,
    *,
    deadline: float,
    observer_script: Path,
    asset_root: Path,
    cdn_map: Path | None = None,
) -> dict[str, Any]:
    """Observe source bytes through a fresh actual browser, including full pixels."""
    if profile.exists() or source.is_symlink() or output.exists():
        raise ValueError("browser driver requires fresh confined artifacts")
    runtime_path = Path(__file__).with_name("native_format_browser_runtime.py")
    runtime_source = runtime_path.read_bytes()
    namespace: dict[str, Any] = {"__name__": "native_browser_runtime"}
    exec(compile(runtime_source, str(runtime_path), "exec"), namespace)  # nosec B102 - exact admitted source-owned bytes
    observe_runtime = namespace["observe_runtime"]
    runtime_before = observe_runtime(chrome, deadline=deadline)
    executable_sha256 = hashlib.sha256(chrome.read_bytes()).hexdigest()
    command = [
        str(chrome),
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--disable-background-networking",
        "--disable-extensions",
        "--disable-sync",
        "--remote-debugging-port=0",
        "--proxy-server=http://127.0.0.1:9",
        "--proxy-bypass-list=127.0.0.1",
        f"--user-data-dir={profile}",
        "about:blank",
    ]
    admitted_files = {p.resolve() for p in asset_root.rglob("*") if p.is_file() and not p.is_symlink()}

    class Assets(SimpleHTTPRequestHandler):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, directory=str(asset_root), **kwargs)

        def do_GET(self) -> None:
            candidate = (asset_root / unquote(urlsplit(self.path).path).lstrip("/")).resolve()
            if candidate not in admitted_files or candidate.is_symlink():
                self.send_error(404)
                return
            super().do_GET()

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
    stdout = output.with_suffix(".stdout")
    stderr = output.with_suffix(".stderr")
    with stdout.open("xb") as out, stderr.open("xb") as err:
        try:
            browser = subprocess.Popen(command, stdout=out, stderr=err)  # nosec B603 - admitted fixed command, fresh isolated profile
            endpoint = profile / "DevToolsActivePort"
            while not endpoint.exists():
                if time.monotonic() >= deadline or browser.poll() is not None:
                    raise TimeoutError("fresh Chrome did not create its endpoint within original deadline")
                time.sleep(0.02)
            port, route = endpoint.read_text().splitlines()[:2]
            client = DevTools(int(port), route, deadline)
            client.allowed_origin = origin
            if cdn_map is not None:
                mapping = json.loads(cdn_map.read_bytes())
                if not isinstance(mapping, dict) or len(mapping) > 3000:
                    raise ValueError("CDN response closure is unbounded")
                for url, binding in mapping.items():
                    candidate = (asset_root / binding["path"]).resolve()
                    if candidate not in admitted_files or not url.startswith("https://cdn.jsdelivr.net/npm/"):
                        raise ValueError("CDN mapping escapes admitted response bytes")
                    content = candidate.read_bytes()
                    if hashlib.sha256(content).hexdigest() != binding["sha256"]:
                        raise ValueError("CDN response bytes changed after admission")
                    client.cdn_responses[url] = content
            browser_version = client.call("Browser.getVersion")
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
                {"width": width, "height": 900, "deviceScaleFactor": 1, "mobile": False},
                session=session,
            )
            script = observer_script.read_text()
            client.call("Page.addScriptToEvaluateOnNewDocument", {"source": script}, session=session)
            client.call(
                "Page.navigate", {"url": origin + "/" + source.relative_to(asset_root).as_posix()}, session=session
            )
            dom = None
            while dom is None:
                observation = client.call(
                    "Runtime.evaluate",
                    {
                        "expression": "document.querySelector('#native-browser-observation')?.textContent",
                        "returnByValue": True,
                    },
                    session=session,
                )
                value = observation.get("result", {}).get("value")
                if value:
                    dom = json.loads(value)
                elif time.monotonic() >= deadline:
                    raise TimeoutError("browser did not complete actual DOM observation")
                else:
                    time.sleep(0.02)
            if dom["height"] > 30000:
                raise ValueError("full-page screenshot exceeds finite height budget")
            image = client.call(
                "Page.captureScreenshot",
                {
                    "format": "png",
                    "captureBeyondViewport": True,
                    "clip": {"x": 0, "y": 0, "width": width, "height": max(900, dom["height"]), "scale": 1},
                },
                session=session,
            )
            pixels = base64.b64decode(image["data"], validate=True)
            if len(pixels) > 64 * 1024 * 1024:
                raise ValueError("native screenshot byte budget exceeded")
            output.with_suffix(".png").write_bytes(pixels)
            runtime_after = observe_runtime(chrome, deadline=deadline)
            if runtime_after != runtime_before:
                raise ValueError("browser complete application runtime changed during execution")
            events = client.events.copy()
            client.call("Browser.close")
            closed = True
            exit_code = browser.wait(timeout=max(0.001, deadline - time.monotonic()))
            if exit_code != 0 or hashlib.sha256(chrome.read_bytes()).hexdigest() != executable_sha256:
                raise ValueError("native browser did not preserve original exit0 and executable custody")
            return {
                "dom": dom,
                "events": events,
                "browser_command": command,
                "runtime_observer_sha256": hashlib.sha256(runtime_source).hexdigest(),
                "runtime_observation_before": runtime_before,
                "runtime_observation_after": runtime_after,
                "browser_sha256": executable_sha256,
                "browser_version": browser_version,
                **({"fulfilled_cdn": client.fulfilled} if cdn_map is not None else {}),
                "asset_origin": origin,
                "executable_observation_before": {
                    "schema_version": "template-native-executable-observation-v1",
                    "path": str(chrome.resolve()),
                    "sha256": executable_sha256,
                },
                "executable_observation_after": {
                    "schema_version": "template-native-executable-observation-v1",
                    "path": str(chrome.resolve()),
                    "sha256": executable_sha256,
                },
                "browser_original_exit": exit_code,
                "elapsed_seconds": round(time.monotonic() - started, 6),
                "screenshot_sha256": hashlib.sha256(pixels).hexdigest(),
            }
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
                output.with_suffix(".failed").write_text(
                    "actual browser did not finish its required close/exit contract\n"
                )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chrome", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--width", type=int, choices=(390, 1280), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--deadline", type=float, required=True)
    parser.add_argument("--observer-script", type=Path, required=True)
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--cdn-map", type=Path)
    args = parser.parse_args()
    observation = observe(
        args.chrome,
        args.source,
        args.profile,
        args.width,
        args.output,
        deadline=args.deadline,
        observer_script=args.observer_script,
        asset_root=args.asset_root,
        cdn_map=args.cdn_map,
    )
    args.output.write_text(json.dumps(observation, sort_keys=True, allow_nan=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
