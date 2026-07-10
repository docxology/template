#!/usr/bin/env python3
"""Start a software TPM backend for Kmyth seal/unseal on macOS.

This script:
1. Initializes and starts swtpm (Software TPM emulator) in socket mode
2. Starts the swtpm_mssim_proxy that bridges the mssim TCTI protocol to swtpm
3. Prints the environment variables needed for kmyth-seal/kmyth-unseal

Usage:
    python3 infrastructure/steganography/start_tpm_backend.py
    python3 infrastructure/steganography/start_tpm_backend.py --stop
    python3 infrastructure/steganography/start_tpm_backend.py --check

Prerequisites:
    - swtpm installed: brew install swtpm
    - TPM2-TSS libraries at ~/.kmyth-prefix/lib
    - kmyth-seal/kmyth-unseal built at infrastructure/steganography/kmyth/bin
    - .so symlinks for TCTI libraries (created automatically)

Environment variables set by this script (use `eval "$(python3 ... start)"`):
    TSS2_TCTI_DEFAULT=mssim:host=127.0.0.1,port=2321
    DYLD_LIBRARY_PATH=~/.kmyth-prefix/lib:...
"""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROXY_SCRIPT = SCRIPT_DIR / "swtpm_mssim_proxy.py"
KMYTH_PREFIX = Path.home() / ".kmyth-prefix"

SWTPM_STATE_DIR = Path("/tmp/swtpm-kmyth-state")  # nosec B108 - local dev TPM emulator state, fixed rendezvous path
SWTPM_LOG = Path("/tmp/swtpm-kmyth.log")  # nosec B108 - local dev TPM emulator log
SWTPM_PID_FILE = Path("/tmp/swtpm-kmyth.pid")  # nosec B108 - local dev TPM emulator pidfile
PROXY_PID_FILE = Path("/tmp/swtpm-kmyth-proxy.pid")  # nosec B108 - local dev TPM emulator proxy pidfile

SWTPM_DATA_PORT = 3321
SWTPM_CTRL_PORT = 3322
PROXY_DATA_PORT = 2321
PROXY_CTRL_PORT = 2322


def _ensure_so_symlinks() -> None:
    """Create .so symlinks for TCTI libraries so dlopen can find them."""
    lib_dir = KMYTH_PREFIX / "lib"
    if not lib_dir.exists():
        return
    for f in lib_dir.glob("libtss2-tcti-*.dylib"):
        base = f.stem  # e.g., libtss2-tcti-mssim.0
        so_path = lib_dir / f"{base}.so"
        if not so_path.exists():
            so_path.symlink_to(f)
    for f in lib_dir.glob("libtss2-tcti-*.0.dylib"):
        base = f.stem  # e.g., libtss2-tcti-mssim.0
        so_path = lib_dir / f"{base}.so.0"
        if not so_path.exists():
            so_path.symlink_to(f)


def _read_pid(pid_file: Path) -> int | None:
    if not pid_file.exists():
        return None
    try:
        return int(pid_file.read_text().strip())
    except (ValueError, OSError):
        return None


def _kill_pid(pid: int) -> bool:
    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(1)
        try:
            os.kill(pid, 0)
            os.kill(pid, signal.SIGKILL)
            time.sleep(0.5)
        except ProcessLookupError:
            pass
        return True
    except ProcessLookupError:
        return False


def stop() -> int:
    """Stop swtpm and proxy processes."""
    for pid_file in [SWTPM_PID_FILE, PROXY_PID_FILE]:
        pid = _read_pid(pid_file)
        if pid:
            _kill_pid(pid)
            print(f"Stopped process {pid} ({pid_file.name})")
            pid_file.unlink(missing_ok=True)
    return 0


def check() -> int:
    """Check if swtpm and proxy are running."""
    swtpm_pid = _read_pid(SWTPM_PID_FILE)
    proxy_pid = _read_pid(PROXY_PID_FILE)

    swtpm_ok = swtpm_pid is not None and _is_running(swtpm_pid)
    proxy_ok = proxy_pid is not None and _is_running(proxy_pid)

    print(f"swtpm: {'RUNNING' if swtpm_ok else 'STOPPED'} (pid={swtpm_pid})")
    print(f"proxy: {'RUNNING' if proxy_ok else 'STOPPED'} (pid={proxy_pid})")

    if swtpm_ok and proxy_ok:
        print("\nEnvironment variables for kmyth-seal:")
        print(f'  export TSS2_TCTI_DEFAULT="mssim:host=127.0.0.1,port={PROXY_DATA_PORT}"')
        print(f'  export DYLD_LIBRARY_PATH="{KMYTH_PREFIX}/lib:$DYLD_LIBRARY_PATH"')
        return 0
    return 1


def _is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


def start() -> int:
    """Start swtpm and proxy."""
    # Stop existing processes first
    stop()

    # Ensure swtpm is available
    if not shutil.which("swtpm"):
        print("ERROR: swtpm not found. Install with: brew install swtpm", file=sys.stderr)
        return 1
    if not shutil.which("swtpm_setup"):
        print("ERROR: swtpm_setup not found. Install with: brew install swtpm", file=sys.stderr)
        return 1
    if not PROXY_SCRIPT.exists():
        print(f"ERROR: Proxy script not found at {PROXY_SCRIPT}", file=sys.stderr)
        return 1

    # Ensure .so symlinks
    _ensure_so_symlinks()

    # Initialize swtpm state
    SWTPM_STATE_DIR.mkdir(parents=True, exist_ok=True)
    for f in SWTPM_STATE_DIR.iterdir():
        if f.is_file():
            f.unlink()

    print("Initializing TPM state...", file=sys.stderr)
    result = subprocess.run(
        ["swtpm_setup", "--tpmstate", str(SWTPM_STATE_DIR), "--tpm2", "--createek", "--lock-nvram"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        print(f"ERROR: swtpm_setup failed: {result.stderr}", file=sys.stderr)
        return 1

    # Start swtpm
    print("Starting swtpm...", file=sys.stderr)
    swtpm_proc = subprocess.Popen(
        [
            "swtpm",
            "socket",
            "--tpmstate",
            f"dir={SWTPM_STATE_DIR}",
            "--ctrl",
            f"type=tcp,port={SWTPM_CTRL_PORT}",
            "--server",
            f"type=tcp,port={SWTPM_DATA_PORT}",
            "--tpm2",
            "--flags",
            "startup-clear",
            "--log",
            f"level=20,file={SWTPM_LOG}",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    SWTPM_PID_FILE.write_text(str(swtpm_proc.pid))
    time.sleep(2)

    if not _is_running(swtpm_proc.pid):
        print("ERROR: swtpm failed to start", file=sys.stderr)
        return 1

    # Start proxy
    print("Starting mssim proxy...", file=sys.stderr)
    proxy_proc = subprocess.Popen(
        [
            sys.executable,
            str(PROXY_SCRIPT),
            "--proxy-data-port",
            str(PROXY_DATA_PORT),
            "--proxy-ctrl-port",
            str(PROXY_CTRL_PORT),
            "--swtpm-data-port",
            str(SWTPM_DATA_PORT),
            "--swtpm-ctrl-port",
            str(SWTPM_CTRL_PORT),
            "--log-level",
            "WARNING",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    PROXY_PID_FILE.write_text(str(proxy_proc.pid))
    time.sleep(1)

    if not _is_running(proxy_proc.pid):
        print("ERROR: proxy failed to start", file=sys.stderr)
        _kill_pid(swtpm_proc.pid)
        return 1

    print(f"swtpm started (pid={swtpm_proc.pid}) on ports {SWTPM_DATA_PORT}/{SWTPM_CTRL_PORT}", file=sys.stderr)
    print(f"proxy started (pid={proxy_proc.pid}) on ports {PROXY_DATA_PORT}/{PROXY_CTRL_PORT}", file=sys.stderr)
    print("", file=sys.stderr)

    # Print env vars for eval
    print(f'export TSS2_TCTI_DEFAULT="mssim:host=127.0.0.1,port={PROXY_DATA_PORT}"')
    print(f'export DYLD_LIBRARY_PATH="{KMYTH_PREFIX}/lib:$DYLD_LIBRARY_PATH"')
    print("", file=sys.stderr)
    print("TPM backend ready. Use 'eval' to set env vars:", file=sys.stderr)
    print(f'  eval "$(python3 {Path(__file__).name} start)"', file=sys.stderr)
    print("Then run kmyth-seal/kmyth-unseal or the secure pipeline.", file=sys.stderr)

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("action", nargs="?", default="start", choices=["start", "stop", "check"])
    group.add_argument("--start", action="store_true", help="Start swtpm and proxy")
    group.add_argument("--stop", action="store_true", help="Stop swtpm and proxy")
    group.add_argument("--check", action="store_true", help="Check if running")
    args = parser.parse_args()

    if args.stop or args.action == "stop":
        return stop()
    elif args.check or args.action == "check":
        return check()
    else:
        return start()


if __name__ == "__main__":
    raise SystemExit(main())
