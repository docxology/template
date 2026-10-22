"""Finite loopback-only Chromium DevTools driver using the standard library."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import stat
import sys
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


def _html_source_physical(path: Path, maximum: int = 1024 * 1024) -> dict[str, Any]:
    if path.is_symlink() or path != path.resolve(strict=True):
        raise ValueError("HTML Python child Source requires an exact physical path")
    before = path.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_size > maximum:
        raise ValueError("HTML Python child Source exceeds its regular byte bound")
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    after = path.stat()
    fields = ("st_dev", "st_ino", "st_mode", "st_nlink", "st_size", "st_mtime_ns", "st_ctime_ns")
    if len(raw) > maximum or any(getattr(before, key) != getattr(after, key) for key in fields):
        raise ValueError("HTML Python child Source changed while consumed")
    return {
        "path": str(path),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "identity": {key: getattr(after, key) for key in fields},
    }


_HTML_CHILD_PLAN = None
_HTML_CHILD_AUDIT = None
_HTML_CHILD_START = None
if __name__ == "__main__":
    # This module-level frame is the actual copied script startup Code. The
    # serialized request is DATA; its genuine parent authenticates the actual
    # original process separately. No SDK package or SourceDATA is imported.
    import importlib.util

    _plan_path = Path(os.environ["TEMPLATE_HTML_CHILD_PLAN_PATH"]).absolute()
    _plan_binding = _html_source_physical(_plan_path, 4 * 1024 * 1024)
    if _plan_binding["sha256"] != os.environ["TEMPLATE_HTML_CHILD_PLAN_SHA256"]:
        raise ValueError("HTML child Source request differs from its actual parent's selected bytes")
    _HTML_CHILD_PLAN = json.loads(_plan_path.read_bytes())
    _deadline = _HTML_CHILD_PLAN["deadline_monotonic"]
    if (
        type(_deadline) not in (int, float)
        or not math.isfinite(_deadline)
        or time.monotonic() >= _deadline
        or _HTML_CHILD_PLAN["schema_version"] != "template-source-html-python-child-plan-v1"
        or _HTML_CHILD_PLAN["parent_pid"] != os.getppid()
        or _HTML_CHILD_PLAN["driver_path"] != str(Path(__file__).absolute())
    ):
        raise ValueError("HTML child lacks its actual original parent's bounded Source request")
    _driver = Path(__file__).absolute()
    _child_root = Path(_HTML_CHILD_PLAN["child_root"])
    if _child_root != _child_root.resolve(strict=True) or not _driver.is_relative_to(_child_root):
        raise ValueError("HTML child Source script escaped its actual parent operation")
    _programs = _HTML_CHILD_PLAN["programs"]
    if not isinstance(_programs, dict) or set(_programs) not in (
        {_driver.name, "native_format_browser_runtime.py"},
        {_driver.name, "native_format_browser_runtime.py", "native_format_html_platform_font_dom.py"},
    ):
        raise ValueError("HTML child Source programs have an undeclared role")
    _before_programs = {name: _html_source_physical(_driver.with_name(name)) for name in _programs}
    if {name: row["sha256"] for name, row in _before_programs.items()} != _programs:
        raise ValueError("HTML child copied programs differ from selected current SDK Source")
    _prefix = Path(_HTML_CHILD_PLAN["cache_prefix"])
    _closure = Path(_HTML_CHILD_PLAN["closure_path"])
    if (
        _prefix.parent != _plan_path.parent
        or _closure.parent != _plan_path.parent
        or _prefix.is_symlink()
        or _prefix != _prefix.resolve(strict=True)
        or any(_prefix.iterdir())
        or _closure.exists()
        or _closure.is_symlink()
    ):
        raise ValueError("HTML child requires the actual parent's fresh retained execution prefix")
    sys.pycache_prefix = str(_prefix)
    _hook = Path(_HTML_CHILD_PLAN["hook_path"])
    _hook_before = _html_source_physical(_hook)
    if (
        _hook != Path(_HTML_CHILD_PLAN["selected_sdk_root"]) / "infrastructure/core/bytecode_audit.py"
        or _hook_before["sha256"] != "aa13244989c39811cf6174e8e51a7a85f8f7432bbe038d7e1dc79ced68085e88"
        or _hook_before["sha256"] != _HTML_CHILD_PLAN["hook_sha256"]
    ):
        raise ValueError("HTML child raw audit Source differs from its selected SDK")
    _hook_spec = importlib.util.spec_from_file_location("_html_actual_raw_audit", _hook)
    if (
        _hook_spec is None
        or _hook_spec.loader is None
        or _hook_spec.cached is None
        or not Path(_hook_spec.cached).is_relative_to(_prefix)
        or Path(_hook_spec.cached).exists()
    ):
        raise ValueError("HTML child audit must load exact source through its fresh standard loader")
    _HTML_CHILD_AUDIT = importlib.util.module_from_spec(_hook_spec)
    _hook_spec.loader.exec_module(_HTML_CHILD_AUDIT)
    if _html_source_physical(_hook) != _hook_before:
        raise ValueError("HTML child raw audit Source changed while loaded")
    _HTML_CHILD_AUDIT.install_bytecode_audit(
        (str(_driver.parent),),
        fresh_pycache_prefix=str(_prefix),
        source_sha256=_hook_before["sha256"],
        startup_code=sys._getframe().f_code,
    )
    _HTML_CHILD_START = {
        "pid": os.getpid(),
        "parent_pid": os.getppid(),
        "plan_sha256": _plan_binding["sha256"],
        "deadline_monotonic": _deadline,
        "programs_before": _before_programs,
        "python_executable_before": _html_source_physical(Path(sys.executable).resolve(strict=True), 512 * 1024 * 1024),
    }


MAX_MESSAGE = 128 * 1024 * 1024


def _browser_endpoint(
    endpoint: Path, browser: subprocess.Popen[Any], deadline: float, *, stderr_fd: int | None = None
) -> tuple[int, str]:
    """Keep actual early signed exits distinct from the original startup clock."""

    def stderr_tail() -> str:
        if stderr_fd is None:
            return ""
        observed = os.fstat(stderr_fd)
        if not stat.S_ISREG(observed.st_mode):
            raise ValueError("Chrome startup diagnostic requires its owned regular stderr")
        maximum = 2048
        content = os.pread(stderr_fd, min(maximum, observed.st_size), max(0, observed.st_size - maximum))
        return "; Chrome stderr tail: " + repr(content.decode("utf-8", errors="replace"))

    while True:
        if time.monotonic() >= deadline:
            raise TimeoutError("fresh Chrome did not publish its endpoint within original deadline" + stderr_tail())
        original_exit = browser.poll()
        if original_exit is not None:
            raise RuntimeError(
                f"fresh Chrome exited before endpoint publication; original signed exit={original_exit}" + stderr_tail()
            )
        try:
            lines = endpoint.read_text().splitlines()
        except FileNotFoundError:
            lines = []
        # Chrome creates the file before writing both fields; existence is not readiness.
        if (
            len(lines) == 2
            and lines[0].isdecimal()
            and 0 < int(lines[0]) < 65536
            and lines[1].startswith("/devtools/browser/")
        ):
            return int(lines[0]), lines[1]
        time.sleep(0.02)


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
            hashlib.sha1(
                (key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode(),
                usedforsecurity=False,
            ).digest()
        ).decode()
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

    def call(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        session: str | None = None,
    ) -> dict[str, Any]:
        self.identifier += 1
        request: dict[str, Any] = {
            "id": self.identifier,
            "method": method,
            "params": params or {},
        }
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
    platform_font_observer: Path | None = None,
) -> dict[str, Any]:
    """Observe source bytes through a fresh actual browser, including full pixels."""
    if profile.exists() or source.is_symlink() or output.exists():
        raise ValueError("browser driver requires fresh confined artifacts")
    runtime_path = Path(__file__).with_name("native_format_browser_runtime.py")
    runtime_source = runtime_path.read_bytes()
    namespace: dict[str, Any] = {"__name__": "native_browser_runtime"}
    exec(compile(runtime_source, str(runtime_path), "exec"), namespace)  # nosec B102 - exact admitted source-owned bytes
    observe_runtime = namespace["observe_runtime"]
    collect_fonts = None
    font_source = b""
    if platform_font_observer is not None:
        if platform_font_observer.parent != Path(__file__).parent or platform_font_observer.is_symlink():
            raise ValueError("native platform font observer must be the exact copied SDK sibling")
        font_source = platform_font_observer.read_bytes()
        if len(font_source) > 1024 * 1024:
            raise ValueError("native platform font observer exceeds its finite SDK byte bound")
        import importlib.util

        spec = importlib.util.spec_from_file_location("native_platform_font_observer", platform_font_observer)
        if spec is None or spec.loader is None or (spec.cached is not None and Path(spec.cached).exists()):
            raise ValueError("native platform font observer requires exact fresh source without reused bytecode")
        font_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(font_module)
        if platform_font_observer.read_bytes() != font_source:
            raise ValueError("native platform font observer SDK bytes changed during standard source loading")
        collect_fonts = font_module.collect_platform_font_usage
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
    with stdout.open("xb") as out, stderr.open("xb+") as err:
        try:
            browser = subprocess.Popen(command, stdout=out, stderr=err)  # nosec B603 - admitted fixed command, fresh isolated profile
            endpoint = profile / "DevToolsActivePort"
            port, route = _browser_endpoint(endpoint, browser, deadline, stderr_fd=err.fileno())
            client = DevTools(port, route, deadline)
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
                "Fetch.enable",
                {"patterns": [{"urlPattern": "http://*"}, {"urlPattern": "https://*"}]},
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
                    "width": width,
                    "height": 900,
                    "deviceScaleFactor": 1,
                    "mobile": False,
                },
                session=session,
            )
            script = observer_script.read_text()
            client.call(
                "Page.addScriptToEvaluateOnNewDocument",
                {"source": script},
                session=session,
            )
            client.call(
                "Page.navigate",
                {"url": origin + "/" + source.relative_to(asset_root).as_posix()},
                session=session,
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
            if collect_fonts is not None:
                collect_fonts(client, session, dom, deadline=deadline)
            if dom["height"] > 30000:
                raise ValueError("full-page screenshot exceeds finite height budget")
            image = client.call(
                "Page.captureScreenshot",
                {
                    "format": "png",
                    "captureBeyondViewport": True,
                    "clip": {
                        "x": 0,
                        "y": 0,
                        "width": width,
                        "height": max(900, dom["height"]),
                        "scale": 1,
                    },
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
            if platform_font_observer is not None and platform_font_observer.read_bytes() != font_source:
                raise ValueError("native platform font observer SDK bytes changed during browser execution")
            return {
                "dom": dom,
                **(
                    {"platform_font_observer_sha256": hashlib.sha256(font_source).hexdigest()}
                    if platform_font_observer is not None
                    else {}
                ),
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
            if closed and time.monotonic() >= deadline:
                raise TimeoutError("browser exhausted original caller clock during native cleanup")


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
    parser.add_argument("--platform-font-observer", type=Path)
    args = parser.parse_args()
    if _HTML_CHILD_PLAN is None or _HTML_CHILD_START is None:
        raise ValueError("HTML standalone execution requires its genuine live Source parent")
    # The real ToolAPI selected this absolute sub-operation deadline once.
    # Original argv remains unchanged; no later phase receives a fresh window.
    args.deadline = min(args.deadline, _HTML_CHILD_PLAN["deadline_monotonic"])
    if not args.output.absolute().is_relative_to(Path(_HTML_CHILD_PLAN["child_root"])):
        raise ValueError("HTML child result escaped its actual parent's output operation")
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
        platform_font_observer=args.platform_font_observer,
    )
    observation["python_source_request_sha256"] = _HTML_CHILD_START["plan_sha256"]
    args.output.write_text(json.dumps(observation, sort_keys=True, allow_nan=False) + "\n")
    return 0


if __name__ == "__main__":
    _original_return = None
    _original_exception = None
    _original_traceback = None
    _closing_errors = []
    try:
        _original_return = main()
    except BaseException as error:
        _original_exception, _original_traceback = error, error.__traceback__
    finally:
        _proof = {
            "schema_version": "template-source-html-python-child-closure-v1",
            **(_HTML_CHILD_START or {}),
            "requested_program_return": _original_return,
            "original_exception": (
                {"type": type(_original_exception).__name__, "message": str(_original_exception)}
                if _original_exception is not None
                else None
            ),
            "audit_hook_sha256": "aa13244989c39811cf6174e8e51a7a85f8f7432bbe038d7e1dc79ced68085e88",
        }
        try:
            if _HTML_CHILD_AUDIT is None or _HTML_CHILD_PLAN is None or _HTML_CHILD_START is None:
                raise ValueError("HTML native Source audit was not installed before helper execution")
            _HTML_CHILD_AUDIT.verify_executed_source_code(
                Path(__file__).absolute().parent, Path(_HTML_CHILD_PLAN["cache_prefix"])
            )
            # Browser work and its executed Source audit are now closed. Lazy
            # stdlib imports during terminal serialization must not add cache
            # files after the retained inventory is taken (notably on Linux).
            # The parent still checks the exact final file set and every byte.
            sys.dont_write_bytecode = True
            _after_programs = {
                name: _html_source_physical(Path(__file__).absolute().with_name(name))
                for name in _HTML_CHILD_PLAN["programs"]
            }
            _proof["program_sha256_before"] = {
                name: row["sha256"] for name, row in _HTML_CHILD_START["programs_before"].items()
            }
            _proof["program_sha256_after"] = {name: row["sha256"] for name, row in _after_programs.items()}
            _proof["programs_after"] = _after_programs
            _proof["python_executable_after"] = _html_source_physical(
                Path(sys.executable).resolve(strict=True), 512 * 1024 * 1024
            )
            if (
                _after_programs != _HTML_CHILD_START["programs_before"]
                or _proof["python_executable_before"] != _proof["python_executable_after"]
                or _html_source_physical(Path(_HTML_CHILD_PLAN["hook_path"])) != _hook_before
                or _html_source_physical(_plan_path, 4 * 1024 * 1024) != _plan_binding
            ):
                raise ValueError("HTML child actual source/request/executable physical custody changed")
            _cache: list[dict[str, Any]] = []
            _cache_bytes = 0
            for _path in sorted(Path(_HTML_CHILD_PLAN["cache_prefix"]).rglob("*")):
                if _path.is_file():
                    _row = _html_source_physical(_path, 16 * 1024 * 1024)
                    _cache_bytes += _row["bytes"]
                    if len(_cache) >= 4096 or _cache_bytes > 64 * 1024 * 1024:
                        raise ValueError("HTML child retained fresh execution cache exceeds finite custody budget")
                    _cache.append(_row)
            _proof["fresh_cache"] = _cache
            if time.monotonic() >= _HTML_CHILD_PLAN["deadline_monotonic"]:
                raise TimeoutError("HTML child Source closure exhausted its original operation clock")
        except BaseException as error:
            _closing_errors.append({"type": type(error).__name__, "message": str(error)})
        _proof["executed_code_source_cache_closed"] = not _closing_errors
        _proof["closing_errors"] = _closing_errors
        _proof["closed_at_monotonic"] = time.monotonic()
        try:
            _encoded = json.dumps(_proof, sort_keys=True, allow_nan=False) + "\n"
            if _HTML_CHILD_PLAN is None or time.monotonic() >= _HTML_CHILD_PLAN["deadline_monotonic"]:
                raise TimeoutError("HTML child terminal Source retention exhausted its original clock")
            with Path(_HTML_CHILD_PLAN["closure_path"]).open("x") as _stream:
                _stream.write(_encoded)
            if time.monotonic() >= _HTML_CHILD_PLAN["deadline_monotonic"]:
                raise TimeoutError("HTML child completed terminal Source retention after its original clock")
        except BaseException as error:
            _closing_errors.append({"type": type(error).__name__, "message": str(error)})
            sys.stderr.write(json.dumps({"html_child_closure_error": _closing_errors[-1]}) + "\n")
    if _original_exception is not None:
        raise _original_exception.with_traceback(_original_traceback)
    if _original_return == 0 and _closing_errors:
        raise SystemExit(124 if any(row["type"] == "TimeoutError" for row in _closing_errors) else 75)
    raise SystemExit(_original_return)
