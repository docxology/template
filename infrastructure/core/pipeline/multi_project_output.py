"""Bound worker stdout while it is produced, independently of scheduler polling."""

from __future__ import annotations

import os
import select
import tempfile
import threading
from typing import IO

WORKER_OUTPUT_LIMIT = 8 * 1024 * 1024


class BoundedWorkerOutput:
    """Continuously drain a pipe into a capped private spool; overflow is failure."""

    def __init__(self, pipe: IO[bytes]) -> None:
        self.pipe = pipe
        self.log = tempfile.TemporaryFile()
        self.overflow = threading.Event()
        self.stop = threading.Event()
        self.error = ""
        self.size = 0
        self.thread = threading.Thread(target=self._drain, name="multi-project-output", daemon=True)
        try:
            os.set_blocking(pipe.fileno(), False)
            self.thread.start()
        except BaseException:
            self.log.close()
            pipe.close()
            raise

    def _drain(self) -> None:
        try:
            descriptor = self.pipe.fileno()
            while not self.stop.is_set():
                if not select.select([descriptor], [], [], 0.05)[0]:
                    continue
                try:
                    chunk = os.read(descriptor, 64 * 1024)
                except BlockingIOError:
                    continue
                if not chunk:
                    break
                remaining = WORKER_OUTPUT_LIMIT - self.size
                kept = chunk[:remaining]
                self.log.write(kept)
                self.size += len(kept)
                if len(chunk) > remaining:
                    self.overflow.set()
        except (OSError, ValueError) as exc:
            self.error = f"Worker output capture failed: {exc}"
        finally:
            try:
                self.log.flush()
            except (OSError, ValueError) as exc:
                self.error = self.error or f"Worker output spool failed: {exc}"

    def finish(self) -> str:
        """Call after child/descendant cleanup and close the reader within a bound."""
        self.thread.join(timeout=2)
        if self.thread.is_alive():
            self.stop.set()
            self.thread.join(timeout=1)
            self.error = self.error or "Worker output pipe remained open after descendant cleanup"
        self.pipe.close()
        return self.error

    def read(self) -> bytes:
        if self.thread.is_alive():
            raise ValueError("Worker output cannot be read before capture cleanup")
        self.log.seek(0)
        return self.log.read(WORKER_OUTPUT_LIMIT)

    def close(self) -> None:
        self.log.close()
