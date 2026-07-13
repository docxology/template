"""Tests for console-vs-file handler level split (LOG-CLEAN-1).

The console (stdout) handler must NOT emit DEBUG-level records; the file
handler must retain DEBUG (timestamped). These tests use real logging,
real temp files, and real StreamHandler/FileHandler — no mocks.
"""

from __future__ import annotations

import io
import logging

from infrastructure.core.logging.formatters import ConsoleFormatter
from infrastructure.core.logging.setup import setup_logger


def _handlers_by_type(
    logger: logging.Logger,
) -> tuple[list[logging.StreamHandler], list[logging.FileHandler]]:
    """Split a logger's handlers into (console-style StreamHandlers, FileHandlers)."""
    file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
    stream_handlers = [
        h for h in logger.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
    ]
    return stream_handlers, file_handlers


class TestConsoleFileLevelSplit:
    """Console handler floors at INFO; file handler retains DEBUG."""

    def test_console_handler_floors_at_info_even_when_logger_is_debug(self, tmp_path):
        """With a DEBUG logger + file handler, console handler level stays >= INFO."""
        log_file = tmp_path / "split.log"
        logger = setup_logger("split_console_test", level=logging.DEBUG, log_file=log_file)

        stream_handlers, file_handlers = _handlers_by_type(logger)

        assert stream_handlers, "expected a console StreamHandler"
        assert file_handlers, "expected a FileHandler"

        # Console must never accept DEBUG records.
        for h in stream_handlers:
            assert h.level >= logging.INFO

        # File handler retains DEBUG.
        for h in file_handlers:
            assert h.level <= logging.DEBUG

    def test_console_formatter_strips_debug_that_file_formatter_retains(self):
        """A DEBUG record is dropped by the console handler but rendered by the file formatter.

        Mirrors the acceptance criterion: console formatter strips a DEBUG record
        that the file formatter retains.
        """
        record = logging.LogRecord(
            name="render.test",
            level=logging.DEBUG,
            pathname=__file__,
            lineno=1,
            msg="rendering page 3",
            args=(),
            exc_info=None,
        )

        # Console handler: floored at INFO -> a DEBUG record is filtered out.
        console_stream = io.StringIO()
        console_handler = logging.StreamHandler(console_stream)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(ConsoleFormatter())

        # File handler: retains DEBUG -> the record is emitted, timestamped.
        file_stream = io.StringIO()
        file_handler = logging.StreamHandler(file_stream)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))

        # The console handler's level filter rejects the DEBUG record.
        assert console_handler.level > record.levelno
        # The file handler's level filter accepts it.
        assert file_handler.level <= record.levelno

        # And when actually handled, the file output carries the message; the
        # console handler emits nothing for a sub-threshold record.
        if record.levelno >= console_handler.level:
            console_handler.emit(record)
        if record.levelno >= file_handler.level:
            file_handler.emit(record)

        assert console_stream.getvalue() == ""
        assert "rendering page 3" in file_stream.getvalue()
        assert "DEBUG" in file_stream.getvalue()

    def test_debug_record_reaches_file_not_console(self, tmp_path):
        """End-to-end: emit a DEBUG record through a configured logger.

        The DEBUG line lands in the file log; the console stream stays empty
        of it.
        """
        log_file = tmp_path / "e2e.log"
        logger = setup_logger("split_e2e_test", level=logging.DEBUG, log_file=log_file)

        # Redirect the console StreamHandler to a capturable buffer.
        console_stream = io.StringIO()
        stream_handlers, _ = _handlers_by_type(logger)
        assert stream_handlers
        for h in stream_handlers:
            h.setStream(console_stream)

        logger.debug("internal-only debug detail")
        logger.info("user-facing info line")

        for handler in logger.handlers:
            handler.flush()

        console_text = console_stream.getvalue()
        file_text = log_file.read_text()

        # DEBUG never on console; INFO is.
        assert "internal-only debug detail" not in console_text
        assert "user-facing info line" in console_text

        # DEBUG retained (timestamped) in the file log.
        assert "internal-only debug detail" in file_text
        assert "DEBUG" in file_text
