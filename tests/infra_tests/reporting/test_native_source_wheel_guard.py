"""Genuine Source/wheel guards retain closing custody and reject real mutations."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from types import FrameType
from typing import Any
from uuid import uuid4

import pytest

import infrastructure
from infrastructure.core.implementation_custody import capture_implementation_custody
import infrastructure.reporting.native_pdfium_source_wheel as wheel_module
import infrastructure.reporting.native_source_external_admission as source_module
from tests.infra_tests.project.test_public_reference import (
    _clone_complete_reference,
    complete_reference as complete_reference,
)

pytestmark = [pytest.mark.external_fixture, pytest.mark.timeout(1800)]


def _source_aba(target: Path) -> None:
    original = target.read_bytes()
    before = target.stat()
    try:
        target.write_bytes(original + b"\nOwned Source wheel guard ABA control.\n")
        assert target.read_bytes() != original
    finally:
        target.write_bytes(original)
    after = target.stat()
    assert target.read_bytes() == original
    assert (before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    ), "Filesystem did not expose the real ABA; refusal must not be claimed"


class _WheelObservation:
    def __init__(self, source: source_module.NativeSourceContext, control: str) -> None:
        self.source = source
        self.control = control
        self.guard_code = source_module.NativeSourceContext._correspondence_guard.__wrapped__.__code__
        self.guard_frames: list[FrameType] = []
        self.events: list[str] = []
        self.deadlines: list[float] = []
        self.git_returns = 0
        self.mutated = False
        self.direct_codes = {
            source_module._verify_selected_sdk.__code__: "sdk",
            type(source.reference).verify_unchanged.__code__: "reference",
            source_module.inventory.__code__: "git",
            source_module.NativeSourceContext._verify_current_source.__code__: "current",
        }

    def __call__(self, frame: FrameType, event: str, argument: Any) -> None:
        code = frame.f_code
        parent = frame.f_back
        parent_code = None if parent is None else parent.f_code
        if event == "call":
            if code is self.guard_code and frame.f_locals.get("self") is self.source:
                if not any(held is frame for held in self.guard_frames):
                    self.guard_frames.append(frame)
                    self.events.append("guard")
                    self.deadlines.append(frame.f_locals["deadline"])
            elif parent_code is self.guard_code and code in self.direct_codes:
                self.events.append(self.direct_codes[code])
            elif code is wheel_module.inspect_pdfium_locked_wheel.__code__:
                self.events.append("parser")
                self.deadlines.append(frame.f_locals["deadline"])
        if event != "return" or argument is None:
            return
        if code is source_module.inventory.__code__ and parent_code is self.guard_code:
            self.git_returns += 1
        parser_return = code is wheel_module.inspect_pdfium_locked_wheel.__code__
        final_git_return = (
            code is source_module.inventory.__code__ and parent_code is self.guard_code and self.git_returns == 3
        )
        if not self.mutated and (
            (parser_return and self.control in {"current-after-parser", "original-after-parser"})
            or (final_git_return and self.control == "current-after-final-git")
        ):
            target_root = (
                self.source.reference.root
                if self.control == "original-after-parser"
                else self.source.bindings.current_root
            )
            _source_aba(target_root / "README.md")
            self.mutated = True
            self.events.append("aba")

    def inspect(self, filename: str, raw: bytes, deadline: float) -> tuple[dict[str, bytes], dict[str, Any]]:
        previous = sys.getprofile()
        assert previous is None, "A genuine control must not replace an existing profiler"
        try:
            sys.setprofile(self)
            return wheel_module.inspect_pdfium_source_wheel(self.source, filename, raw, deadline=deadline)
        finally:
            sys.setprofile(previous)

    def assert_single_complete_guard(self, deadline: float) -> None:
        assert len(self.guard_frames) == 1, self.events
        assert self.events == [
            "guard",
            "sdk",
            "reference",
            "git",
            "current",
            "parser",
            "git",
            "reference",
            "sdk",
            "git",
            "current",
        ]
        assert self.git_returns == 3
        assert self.deadlines == [deadline, deadline]


@pytest.mark.parametrize(
    "control",
    ["positive", "wheel-bytes", "current-after-parser", "original-after-parser", "current-after-final-git"],
)
def test_genuine_source_wheel_single_guard(
    complete_reference: tuple[Path, str, str], tmp_path: Path, control: str
) -> None:
    nominated = os.environ.get("TEMPLATE_TEST_PDFIUM_WHEEL")
    assert nominated, "Prerequisite missing: authentic local Source-locked platform PDFium wheel"
    wheel = Path(nominated)
    assert wheel.is_absolute() and wheel.is_file() and not wheel.is_symlink()
    raw = wheel.read_bytes()
    deadline = time.monotonic() + 900
    workspace = tmp_path.resolve()
    original = _clone_complete_reference(complete_reference, workspace / "original", deadline=deadline)
    mirror = _clone_complete_reference(complete_reference, workspace / "mirror", deadline=deadline)
    metadata = mirror.stat()
    assert infrastructure.__file__ is not None
    source = source_module.admit_external_native_source(
        source_module.NativeExternalSourceBindings(
            original,
            complete_reference[1],
            complete_reference[2],
            mirror,
            (metadata.st_dev, metadata.st_ino),
            Path(infrastructure.__file__).absolute().parent,
            json.dumps(capture_implementation_custody(), sort_keys=True).encode(),
            uuid4().hex,
        ),
        deadline=deadline,
    )
    positive = _WheelObservation(source, "positive")
    expected = positive.inspect(wheel.name, raw, deadline)
    positive.assert_single_complete_guard(deadline)
    observed = _WheelObservation(source, control)
    if control == "positive":
        assert observed.inspect(wheel.name, raw, deadline) == expected
        observed.assert_single_complete_guard(deadline)
        with pytest.raises(TimeoutError):
            wheel_module.inspect_pdfium_source_wheel(source, wheel.name, raw, deadline=time.monotonic() - 1)
    elif control == "wheel-bytes":
        with pytest.raises(ValueError):
            observed.inspect(wheel.name, raw + b"Owned invalid wheel bytes", deadline)
        observed.assert_single_complete_guard(deadline)
    else:
        with pytest.raises(ValueError):
            observed.inspect(wheel.name, raw, deadline)
        assert observed.mutated, "The actual nominated production return boundary was not reached"
        assert len(observed.guard_frames) == 1
        if control == "current-after-final-git":
            assert observed.git_returns == 3
            assert observed.events[-1] == "current"
