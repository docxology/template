"""Genuine preimport Source/provider controls, not native execution acceptance.

Run explicitly with -m external_fixture and TEMPLATE_TEST_PDFIUM_WHEEL naming
an authentic local platform wheel already declared by the complete Source lock.
Every case installs a private copy offline; the selected developer environment
and the externally nominated wheel are never mutation targets.
"""

from __future__ import annotations

import importlib
import importlib.machinery
import json
import os
import shutil
import subprocess
import sys
import sysconfig
import time
from pathlib import Path
from types import FrameType
from typing import Any
from uuid import uuid4

import pytest

import infrastructure
from infrastructure.core.implementation_custody import capture_implementation_custody
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting import native_office_pdfium_provider as installed_module
from infrastructure.reporting import native_pdfium_source_wheel as wheel_module
from infrastructure.reporting import native_source_external_admission as source_module
from infrastructure.reporting.native_full_worker_pdfium import (
    NativePDFiumProvider,
    NativePDFiumSelection,
    admit_full_worker_pdfium_providers,
)
from tests.infra_tests.project.test_public_reference import (
    _clone_complete_reference,
    complete_reference as complete_reference,
)

pytestmark = [pytest.mark.external_fixture, pytest.mark.timeout(1800)]
SCOPE = "templates/template_code_project"
CONTROLS = (
    "positive",
    "wheel-bytes",
    "wheel-replaced",
    "site-body",
    "site-record",
    "site-extra",
    "site-alias",
    "site-replaced",
    "import-origin",
    "source-aba",
    "source-after-parser",
    "source-after-installed",
    "source-after-final-git",
)


def _namespace_absent() -> None:
    assert not any(
        name == package or name.startswith(package + ".")
        for name in sys.modules
        for package in installed_module.PROVIDERS
    ), "The actual PDFium namespaces must remain unimported in this fresh process"


def _source_aba(target: Path) -> dict[str, Any]:
    original = target.read_bytes()
    before = target.stat()
    try:
        target.write_bytes(original + b"\nOwned genuine Source ABA control.\n")
        assert target.read_bytes() != original
    finally:
        target.write_bytes(original)
    after = target.stat()
    assert target.read_bytes() == original
    before_identity = (before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
    after_identity = (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
    assert before_identity != after_identity, "Filesystem did not expose this ABA; do not claim a negative control"
    return {"before": before_identity, "after": after_identity, "bytes_restored": True}


class _VerifyObservation:
    """Observe real frames; only named negative cases mutate owned Source DATA.

    A contextmanager generator produces call events on entry AND resumption.
    Retaining distinct frame objects counts complete guards rather than resumes.
    No callable, result, clock, factory key, or capability is substituted.
    """

    def __init__(self, provider: NativePDFiumProvider, control: str = "positive") -> None:
        self.provider = provider
        self.control = control
        self.guard_code = source_module.NativeSourceContext._correspondence_guard.__wrapped__.__code__
        self.verify_code = NativePDFiumProvider.verify_current.__code__
        self.guard_frames: list[FrameType] = []
        self.events: list[str] = []
        self.clock_values: list[float] = []
        self.inventory_returns = 0
        self.mutation: dict[str, Any] | None = None
        self.direct_guard_codes = {
            source_module._verify_selected_sdk.__code__: "sdk",
            type(provider.source.reference).verify_unchanged.__code__: "reference",
            source_module.inventory.__code__: "git",
            source_module.NativeSourceContext._verify_current_source.__code__: "current",
        }

    def __call__(self, frame: FrameType, event: str, argument: Any) -> None:
        parent = frame.f_back
        parent_code = None if parent is None else parent.f_code
        code = frame.f_code
        label = None
        if event == "call":
            if code is self.guard_code:
                if not any(held is frame for held in self.guard_frames):
                    self.guard_frames.append(frame)
                    label = "guard"
            elif parent_code is self.guard_code:
                label = self.direct_guard_codes.get(code)
            elif parent_code is self.verify_code:
                if code is installed_module._file.__code__ and frame.f_locals["path"] == self.provider.selection.wheel:
                    label = "wheel"
                elif code is wheel_module.inspect_pdfium_locked_wheel.__code__:
                    label = "parser"
                elif code is installed_module._installed.__code__:
                    label = "installed"
                elif (
                    code is type(self.provider.source.current_source_reader).read.__code__
                    and frame.f_locals["self"] is self.provider.source.current_source_reader
                    and frame.f_locals["relative"] == "uv.lock"
                ):
                    label = "lock"
            if label is not None:
                self.events.append(label)
                if "deadline" in frame.f_locals:
                    self.clock_values.append(frame.f_locals["deadline"])
        if event != "return" or argument is None:
            return
        if code is source_module.inventory.__code__ and parent_code is self.guard_code:
            self.inventory_returns += 1
        trigger = (
            (
                self.control == "source-after-parser"
                and code is wheel_module.inspect_pdfium_locked_wheel.__code__
                and parent_code is self.verify_code
            )
            or (
                self.control == "source-after-installed"
                and code is installed_module._installed.__code__
                and parent_code is self.verify_code
            )
            or (
                self.control == "source-after-final-git"
                and code is source_module.inventory.__code__
                and parent_code is self.guard_code
                and self.inventory_returns == 3
            )
        )
        if trigger and self.mutation is None:
            self.mutation = _source_aba(self.provider.source.bindings.current_root / "README.md")
            self.events.append("aba")

    def verify(self, deadline: float) -> None:
        previous = sys.getprofile()
        assert previous is None, "Run the child without another profiler; do not replace an existing observer"
        try:
            sys.setprofile(self)
            self.provider.verify_current(deadline=deadline)
        finally:
            sys.setprofile(previous)

    def assert_complete_single_guard(self, deadline: float) -> None:
        assert len(self.guard_frames) == 1, self.events
        assert self.events[:5] == ["guard", "sdk", "reference", "git", "current"], self.events
        assert sorted(self.events[5:-5]) == ["installed", "lock", "parser", "wheel"], self.events
        assert self.events[-5:] == ["git", "reference", "sdk", "git", "current"], self.events
        assert self.inventory_returns == 3
        assert self.clock_values and all(value == deadline for value in self.clock_values)


def _child_control(payload: dict[str, Any]) -> None:
    """Use real admission in a fresh interpreter with a disposable actual install."""
    deadline = payload["deadline"]
    remaining(deadline)
    _namespace_absent()
    original = Path(payload["original"])
    mirror = Path(payload["mirror"])
    metadata = mirror.stat()
    context = source_module.admit_external_native_source(
        source_module.NativeExternalSourceBindings(
            original,
            payload["commit"],
            payload["fingerprint"],
            mirror,
            (metadata.st_dev, metadata.st_ino),
            Path(infrastructure.__file__).absolute().parent,
            json.dumps(capture_implementation_custody(), sort_keys=True).encode(),
            uuid4().hex,
        ),
        deadline=deadline,
    )
    site = Path(sysconfig.get_path("purelib")).absolute()
    assert site.parents[2] == Path(sys.prefix).absolute()
    assert Path(sys.prefix).absolute() == Path(payload["environment"])
    selection = NativePDFiumSelection(site, Path(payload["wheel"]))
    provider = admit_full_worker_pdfium_providers(context, ((SCOPE, selection),), deadline=deadline)[SCOPE]
    binding = json.dumps(provider.held_inputs(), sort_keys=True)
    observed_monotonic = provider.observed_monotonic
    original_readme = (original / "README.md").read_bytes()
    positive = _VerifyObservation(provider)
    positive.verify(deadline)
    positive.assert_complete_single_guard(deadline)
    assert json.dumps(provider.held_inputs(), sort_keys=True) == binding
    assert context.current_source_reader.unchanged()
    control = payload["control"]
    result: dict[str, Any] = {"control": control, "positive_events": positive.events}
    if control == "positive":
        repeated = _VerifyObservation(provider)
        repeated.verify(deadline)
        repeated.assert_complete_single_guard(deadline)
        assert json.dumps(provider.held_inputs(), sort_keys=True) == binding
        assert context.current_source_reader.unchanged()
        remaining(deadline)
        with pytest.raises(TimeoutError):
            provider.verify_current(deadline=time.monotonic() - 1)
        with pytest.raises(ValueError, match="cannot renew its original caller clock"):
            provider.verify_current(deadline=deadline + 1)
        result["repeated_events"] = repeated.events
    elif control.startswith("source-after-"):
        closing = _VerifyObservation(provider, control)
        with pytest.raises(ValueError):
            closing.verify(deadline)
        assert closing.mutation is not None, "The actual nominated return boundary must be reached"
        assert len(closing.guard_frames) == 1
        assert closing.events[-1] == "current", closing.events
        assert closing.events.index("aba") < len(closing.events) - 1
        assert closing.inventory_returns == 3
        assert closing.clock_values and all(value == deadline for value in closing.clock_values)
        assert (mirror / "README.md").read_bytes() == original_readme
        assert not context.current_source_reader.unchanged()
        result.update(events=closing.events, mutation=closing.mutation)
    else:
        target = site / "pypdfium2/__init__.py"
        if control == "wheel-bytes":
            selection.wheel.write_bytes(selection.wheel.read_bytes() + b"Owned changed wheel bytes\n")
        elif control == "wheel-replaced":
            before = selection.wheel.stat()
            replacement = selection.wheel.with_suffix(".replacement")
            shutil.copy2(selection.wheel, replacement)
            replacement.replace(selection.wheel)
            after = selection.wheel.stat()
            assert (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino)
        elif control == "site-body":
            target.write_bytes(target.read_bytes() + b"\nOWNED_REGRESSION = True\n")
        elif control == "site-record":
            records = tuple(site.glob("pypdfium2-*.dist-info/RECORD"))
            assert len(records) == 1
            records[0].write_bytes(records[0].read_bytes() + b"owned-unlisted.txt,,\n")
        elif control == "site-extra":
            (target.parent / "owned-unlisted.txt").write_bytes(b"undeclared owned member\n")
        elif control == "site-alias":
            target.unlink()
            target.symlink_to(site / "pypdfium2_raw/__init__.py")
        elif control == "site-replaced":
            before = target.stat()
            replacement = target.with_suffix(".replacement")
            shutil.copy2(target, replacement)
            replacement.replace(target)
            after = target.stat()
            assert (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino)
        elif control == "import-origin":
            shadow = Path(payload["environment"]).parent / "owned-import-shadow"
            (shadow / "pypdfium2").mkdir(parents=True)
            shutil.copy2(target, shadow / "pypdfium2/__init__.py")
            sys.path.insert(0, str(shadow))
            importlib.invalidate_caches()
            actual = importlib.machinery.PathFinder.find_spec("pypdfium2", sys.path)
            assert actual is not None and actual.origin == str(shadow / "pypdfium2/__init__.py")
        elif control == "source-aba":
            result["mutation"] = _source_aba(mirror / "README.md")
            assert not context.current_source_reader.unchanged()
        else:
            raise AssertionError(f"Unknown owned control: {control}")
        with pytest.raises(ValueError):
            provider.verify_current(deadline=deadline)
        if control != "source-aba":
            assert context.current_source_reader.unchanged(), "Provider negative must not be a Source failure"
    assert (original / "README.md").read_bytes() == original_readme
    assert provider.deadline == deadline
    assert provider.observed_monotonic == observed_monotonic
    _namespace_absent()
    remaining(deadline)
    Path(payload["result"]).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")


def _run_owned(arguments: list[str], *, cwd: Path, deadline: float, label: str) -> None:
    environment = dict(os.environ)
    environment.update(UV_OFFLINE="1", UV_PYTHON_DOWNLOADS="never", UV_COMPILE_BYTECODE="0")
    stdout_path = cwd / f"{label}.stdout"
    stderr_path = cwd / f"{label}.stderr"
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        result = subprocess.run(
            arguments,
            cwd=cwd,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=stderr,
            check=False,
            timeout=remaining(deadline),
        )
    (cwd / f"{label}.exit").write_text(str(result.returncode) + "\n")
    assert result.returncode == 0, (label, result.returncode, str(stdout_path), str(stderr_path))
    remaining(deadline)


@pytest.mark.parametrize("control", CONTROLS)
def test_genuine_pdfium_use_time_guard(complete_reference: tuple[Path, str, str], tmp_path: Path, control: str) -> None:
    """The fixture is genuine owned Source, not published candidate acceptance."""
    nominated = os.environ.get("TEMPLATE_TEST_PDFIUM_WHEEL")
    assert nominated, "Prerequisite missing: nominate the authentic local Source-locked platform PDFium wheel"
    external_wheel = Path(nominated)
    assert external_wheel.is_absolute() and external_wheel.is_file()
    assert not external_wheel.is_symlink()
    uv = shutil.which("uv")
    assert uv is not None, "Prerequisite missing: installed uv for offline disposable installation"
    deadline = time.monotonic() + 900
    workspace = tmp_path.resolve()
    original, commit, fingerprint = complete_reference
    mirror = _clone_complete_reference(complete_reference, workspace / "current-full-git-mirror", deadline=deadline)
    wheel = workspace / external_wheel.name
    shutil.copy2(external_wheel, wheel)
    wheel_module.inspect_pdfium_locked_wheel(
        wheel.name, wheel.read_bytes(), (original / "uv.lock").read_bytes(), deadline=deadline
    )
    environment = workspace / "pdfium-environment"
    _run_owned(
        [sys.executable, "-I", "-B", "-m", "venv", "--without-pip", str(environment)],
        cwd=workspace,
        deadline=deadline,
        label="venv",
    )
    interpreter = environment / "bin/python"
    _run_owned(
        [
            uv,
            "--offline",
            "--no-config",
            "--no-cache",
            "pip",
            "install",
            "--python",
            str(interpreter),
            "--no-deps",
            "--link-mode",
            "copy",
            str(wheel),
        ],
        cwd=workspace,
        deadline=deadline,
        label="install",
    )
    result_path = workspace / "regression-observation.json"
    payload = {
        "original": str(original),
        "commit": commit,
        "fingerprint": fingerprint,
        "mirror": str(mirror),
        "environment": str(environment),
        "wheel": str(wheel),
        "deadline": deadline,
        "control": control,
        "result": str(result_path),
        "test_file": str(Path(__file__).resolve()),
        "sdk_parent": str(Path(infrastructure.__file__).resolve().parent.parent),
        "dependency_paths": [str(Path(path).resolve()) for path in sys.path if path and Path(path).is_dir()],
    }
    payload_path = workspace / "regression-input.json"
    payload_path.write_text(json.dumps(payload, sort_keys=True))
    bootstrap = (
        "import json, pathlib, runpy, sys\n"
        "payload = json.loads(pathlib.Path(sys.argv[1]).read_text())\n"
        "sys.path.insert(0, payload['sdk_parent'])\n"
        "sys.path.extend(path for path in payload['dependency_paths'] if path not in sys.path)\n"
        "runpy.run_path(payload['test_file'])['_child_control'](payload)\n"
    )
    _run_owned(
        [str(interpreter), "-I", "-B", "-c", bootstrap, str(payload_path)],
        cwd=workspace,
        deadline=deadline,
        label="control",
    )
    result = json.loads(result_path.read_text())
    assert result["control"] == control
