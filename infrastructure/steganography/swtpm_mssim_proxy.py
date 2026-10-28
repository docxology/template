#!/usr/bin/env python3
"""
TCP proxy that bridges the Microsoft TPM Simulator (mssim) TCTI protocol
to swtpm's socket control protocol.

The mssim TCTI in TPM2-TSS sends platform commands (POWER_ON, NV_ON) to a
control port (data_port + 1) and TPM commands to a data port. swtpm uses
its own CMD_* protocol on its control channel, which is incompatible with
the MS simulator protocol.

This proxy listens on two ports:
  - data_port  (default 2321): forwards TPM commands directly to swtpm
  - ctrl_port  (default 2322): translates MS_SIM platform commands to
    swtpm CMD_* format and forwards to swtpm's control port

MS simulator platform commands (4-byte big-endian uint32):
  MS_SIM_POWER_ON = 1
  MS_SIM_NV_ON    = 2

swtpm CMD_* protocol (8 bytes: 4-byte cmd_type + 4-byte data):
  CMD_GET_CAPABILITY = 1
  CMD_INIT           = 2  (data = init_flags, e.g. 1 = DELETE_VOLATILE)
  CMD_SHUTDOWN       = 3

The proxy translates:
  MS_SIM_POWER_ON (1) -> CMD_INIT (2) with flags=1
  MS_SIM_NV_ON    (2) -> CMD_INIT (2) with flags=0 (idempotent)
  Other commands  -> forwarded as-is (best effort)

Usage:
  python3 swtpm_mssim_proxy.py --swtpm-data-port 3321 --swtpm-ctrl-port 3322 \\
      --proxy-data-port 2321 --proxy-ctrl-port 2322
"""

from __future__ import annotations

import argparse
import logging
import socket
import struct
import threading
import time
from collections.abc import Callable

# Global flag: set to True after a flush (CMD_INIT) resets the TPM.
# The data handler checks this to decide whether to send TPM2_Startup.
_tpm_needs_startup = threading.Event()

logger = logging.getLogger("swtpm-mssim-proxy")

# MS simulator platform commands (sent by mssim TCTI to control port)
# From tss2_tcti_mssim.h in TPM2-TSS
MS_SIM_POWER_ON = 1
MS_SIM_POWER_OFF = 2
MS_SIM_TPM_SEND_COMMAND = 8
MS_SIM_CANCEL_ON = 9
MS_SIM_CANCEL_OFF = 10
MS_SIM_NV_ON = 11
TPM_SESSION_END = 20

# swtpm CMD_* protocol command numbers
SWTPM_CMD_GET_CAPABILITY = 1
SWTPM_CMD_INIT = 2
SWTPM_CMD_SHUTDOWN = 3

# swtpm CMD_INIT flags
SWTPM_INIT_FLAG_DELETE_VOLATILE = 1


def handle_ctrl_client(
    client_sock: socket.socket,
    client_addr: tuple[str, int],
    swtpm_ctrl_host: str,
    swtpm_ctrl_port: int,
) -> None:
    """Handle a control-channel connection from the mssim TCTI.

    The mssim TCTI sends platform commands as 4-byte big-endian uint32 values.
    We translate them to swtpm's CMD_* protocol (8 bytes: cmd + data).
    """
    logger.debug("ctrl: connection from %s", client_addr)
    try:
        swtpm_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        swtpm_sock.settimeout(10)
        swtpm_sock.connect((swtpm_ctrl_host, swtpm_ctrl_port))
    except (ConnectionRefusedError, OSError) as exc:
        logger.error("ctrl: cannot connect to swtpm at %s:%d: %s", swtpm_ctrl_host, swtpm_ctrl_port, exc)
        client_sock.close()
        return

    try:
        while True:
            # Read 4-byte command from mssim TCTI
            data = recv_exactly(client_sock, 4)
            if data is None:
                logger.debug("ctrl: client disconnected")
                break

            cmd = struct.unpack(">I", data)[0]
            logger.debug("ctrl: received MS_SIM command %d (0x%08x)", cmd, cmd)

            if cmd == MS_SIM_POWER_ON:
                # swtpm with startup-clear already handled power-on and startup.
                # Don't send CMD_INIT (which would reset the TPM state and
                # require a new TPM2_Startup). Just return success.
                logger.debug("ctrl: POWER_ON -> returning success (no-op, startup-clear handles it)")
                client_sock.sendall(struct.pack(">I", 0))

            elif cmd == MS_SIM_NV_ON:
                # swtpm doesn't have a separate NV_ON command.
                # CMD_INIT already handles both power-on and NV init.
                # Just return success to the mssim TCTI.
                logger.debug("ctrl: NV_ON (11) -> returning success (no-op)")
                client_sock.sendall(struct.pack(">I", 0))

            elif cmd == MS_SIM_POWER_OFF:
                # Translate to swtpm CMD_SHUTDOWN
                swtpm_cmd = struct.pack(">II", SWTPM_CMD_SHUTDOWN, 0)
                logger.debug("ctrl: translating POWER_OFF -> CMD_SHUTDOWN")
                swtpm_sock.sendall(swtpm_cmd)
                resp = recv_exactly(swtpm_sock, 4)
                if resp:
                    logger.debug("ctrl: swtpm CMD_SHUTDOWN response: %s", resp.hex())
                client_sock.sendall(struct.pack(">I", 0))

            elif cmd == MS_SIM_CANCEL_ON:
                # Cancel is not supported, but return success
                logger.debug("ctrl: CANCEL_ON -> returning success (no-op)")
                client_sock.sendall(struct.pack(">I", 0))

            elif cmd == MS_SIM_CANCEL_OFF:
                logger.debug("ctrl: CANCEL_OFF -> returning success (no-op)")
                client_sock.sendall(struct.pack(">I", 0))

            elif cmd == TPM_SESSION_END:
                logger.debug("ctrl: TPM_SESSION_END -> closing control session")
                client_sock.sendall(struct.pack(">I", 0))
                break

            else:
                # Unknown command - return success.
                logger.debug("ctrl: unknown command %d -> returning success (no-op)", cmd)
                client_sock.sendall(struct.pack(">I", 0))

    except (ConnectionResetError, BrokenPipeError, OSError) as exc:
        logger.debug("ctrl: connection error: %s", exc)
    finally:
        client_sock.close()
        swtpm_sock.close()


def handle_data_client(
    client_sock: socket.socket,
    client_addr: tuple[str, int],
    swtpm_data_host: str,
    swtpm_data_port: int,
    swtpm_ctrl_host: str = "127.0.0.1",
    swtpm_ctrl_port: int = 3322,
) -> None:
    """Handle a data-channel connection: translate mssim wire protocol to raw TPM.

    The mssim TCTI wraps TPM commands with:
      TX: 4B locality | 4B cmd_size | cmd_size bytes raw TPM command
      RX: 4B resp_size | resp_size bytes raw TPM response | 4B status (0=ok)

    swtpm's data channel expects raw TPM command bytes and returns raw
    TPM response bytes. This handler strips the mssim wrapper on TX and
    adds it back on RX.
    """
    logger.debug("data: connection from %s", client_addr)

    # No pre-connection flush - kmyth-seal now flushes its own transient
    # objects (storage key) via Tss2_Sys_FlushContext before exiting.

    try:
        swtpm_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        swtpm_sock.settimeout(30)
        swtpm_sock.connect((swtpm_data_host, swtpm_data_port))
    except (ConnectionRefusedError, OSError) as exc:
        logger.error("data: cannot connect to swtpm at %s:%d: %s", swtpm_data_host, swtpm_data_port, exc)
        client_sock.close()
        return

    try:
        while True:
            # Read mssim header: 4B cmd_type + 1B locality + 4B tpm_size = 9 bytes
            # From tpm2-tss tcti-mssim.c send_sim_cmd_setup():
            #   UINT32 MS_SIM_TPM_SEND_COMMAND + UINT8 locality + UINT32 size
            header = recv_exactly(client_sock, 9)
            if header is None:
                logger.debug("data: client disconnected")
                break

            cmd_type = struct.unpack(">I", header[0:4])[0]
            locality = header[4]  # uint8
            tpm_cmd_size = struct.unpack(">I", header[5:9])[0]

            if cmd_type == MS_SIM_TPM_SEND_COMMAND:
                logger.debug("data: TPM_SEND_COMMAND locality=%d tpm_size=%d", locality, tpm_cmd_size)

                # Read the full TPM command
                tpm_cmd = recv_exactly(client_sock, tpm_cmd_size) or b""
                if len(tpm_cmd) != tpm_cmd_size:
                    logger.warning("data: truncated command (got %d, expected %d)", len(tpm_cmd), tpm_cmd_size)
                    break

                # The flush (Shutdown+Startup) already re-initialized the
                # TPM, so no need to send Startup here.

                # Forward raw TPM command to swtpm
                swtpm_sock.sendall(tpm_cmd)

                # Read raw TPM response from swtpm
                # TPM response: tag(2B) + size(4B) + body
                resp_header = recv_exactly(swtpm_sock, 6)
                if resp_header is None:
                    logger.warning("data: no response from swtpm")
                    break

                resp_size = struct.unpack(">I", resp_header[2:6])[0]
                resp_remaining = resp_size - 6
                resp_body = b""
                if resp_remaining > 0:
                    resp_body = recv_exactly(swtpm_sock, resp_remaining) or b""

                full_resp = resp_header + resp_body
                logger.debug("data: response_size=%d", len(full_resp))

                # Wrap response in mssim protocol:
                # 4B response_size + response_data + 4B status(0)
                client_sock.sendall(struct.pack(">I", len(full_resp)))
                client_sock.sendall(full_resp)
                client_sock.sendall(struct.pack(">I", 0))

            elif cmd_type == TPM_SESSION_END:
                logger.debug("data: TPM_SESSION_END")
                break

            else:
                logger.warning("data: unknown cmd_type=%d", cmd_type)
                client_sock.sendall(struct.pack(">II", 0, 0))
    except (ConnectionResetError, BrokenPipeError, OSError) as exc:
        logger.debug("data: connection error: %s", exc)
    finally:
        client_sock.close()
        swtpm_sock.close()

    # No post-connection flush - the pre-connection flush handles it.


def _flush_tpm_state(
    ctrl_host: str,
    ctrl_port: int,
    data_host: str,
    data_port: int,
) -> None:
    """Flush transient TPM objects by:
    1. Sending CMD_INIT via the control channel (swtpm ioctl)
    2. Sending TPM2_Startup(CLEAR) via the data channel

    CMD_INIT clears all TPM state (including transient objects).
    TPM2_Startup(CLEAR) re-initializes the TPM for the next client.
    """
    # Step 1: CMD_INIT via control channel
    try:
        ctrl_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ctrl_sock.settimeout(5)
        ctrl_sock.connect((ctrl_host, ctrl_port))
        # CMD_INIT = 2, flags = 1 (DELETE_VOLATILE)
        ctrl_sock.sendall(struct.pack(">II", SWTPM_CMD_INIT, SWTPM_INIT_FLAG_DELETE_VOLATILE))
        resp = recv_exactly(ctrl_sock, 4)
        if resp:
            logger.debug("flush: CMD_INIT response: %s", resp.hex())
        ctrl_sock.close()
    except (ConnectionRefusedError, OSError) as exc:
        logger.warning("flush: CMD_INIT failed: %s", exc)
        return

    # Step 2: TPM2_Startup(CLEAR) via data channel
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((data_host, data_port))

        startup_cmd = bytes([0x80, 0x01, 0x00, 0x00, 0x00, 0x0A, 0x00, 0x00, 0x01, 0x44, 0x00, 0x00])
        sock.sendall(startup_cmd)
        resp = recv_exactly(sock, 10)
        if resp:
            sz = struct.unpack(">I", resp[2:6])[0]
            if sz > 10:
                recv_exactly(sock, sz - 10)
            rc = struct.unpack(">I", resp[6:10])[0]
            logger.debug("flush: Startup rc=0x%08x", rc)
        sock.close()
    except (ConnectionRefusedError, OSError) as exc:
        logger.warning("flush: Startup failed: %s", exc)


def recv_exactly(sock: socket.socket, n: int) -> bytes | None:
    """Read exactly n bytes from a socket, or None on EOF."""
    data = bytearray()
    while len(data) < n:
        try:
            chunk = sock.recv(n - len(data))
        except socket.timeout:
            return None
        except (ConnectionResetError, BrokenPipeError, OSError):
            return None
        if not chunk:
            return None
        data.extend(chunk)
    return bytes(data)


def serve(
    host: str,
    port: int,
    handler: Callable[..., None],
    swtpm_host: str,
    swtpm_port: int,
    label: str,
) -> None:
    """Run a TCP server that spawns a thread per connection."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(8)
    logger.info("%s: listening on %s:%d -> swtpm %s:%d", label, host, port, swtpm_host, swtpm_port)
    while True:
        try:
            client_sock, client_addr = server.accept()
        except OSError:
            break
        thread = threading.Thread(
            target=handler,
            args=(client_sock, client_addr, swtpm_host, swtpm_port),
            daemon=True,
        )
        thread.start()


def main() -> int:
    """Parse CLI arguments and start the mssim-to-swtpm proxy servers."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proxy-host", default="127.0.0.1")
    parser.add_argument("--proxy-data-port", type=int, default=2321)
    parser.add_argument("--proxy-ctrl-port", type=int, default=2322)
    parser.add_argument("--swtpm-host", default="127.0.0.1")
    parser.add_argument("--swtpm-data-port", type=int, default=3321)
    parser.add_argument("--swtpm-ctrl-port", type=int, default=3322)
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    ctrl_thread = threading.Thread(
        target=serve,
        args=(args.proxy_host, args.proxy_ctrl_port, handle_ctrl_client, args.swtpm_host, args.swtpm_ctrl_port, "ctrl"),
        daemon=True,
    )
    data_thread = threading.Thread(
        target=serve,
        args=(args.proxy_host, args.proxy_data_port, handle_data_client, args.swtpm_host, args.swtpm_data_port, "data"),
        daemon=True,
    )
    ctrl_thread.start()
    data_thread.start()

    logger.info("swtpm-mssim-proxy ready. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
