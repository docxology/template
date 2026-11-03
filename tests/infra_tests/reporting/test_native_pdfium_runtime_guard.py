"""Genuine audited runtime controls; not installed or scientific acceptance.

Every case retains one original 900-second operation clock. Each subprocess
uses its remaining budget; synchronous filesystem setup checks it cooperatively.
The module fixture precedes the case clock. A private offline installation and
fresh child audit precede SDK/provider imports. No production callable or
admission authority is replaced.
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
from contextlib import nullcontext
from pathlib import Path
from types import FrameType, MappingProxyType
from typing import Any
from uuid import uuid4

import pytest

import infrastructure
import infrastructure.reporting.native_office_diagram_runtime as runtime_module
import infrastructure.reporting.native_office_pdfium_provider as installed_module
import infrastructure.reporting.native_pdfium_runtime_data as data_module
import infrastructure.reporting.native_pdfium_source_wheel as wheel_module
import infrastructure.reporting.native_source_external_admission as source_module
from infrastructure.core.implementation_custody import bytecode_audit_bootstrap, capture_implementation_custody
from infrastructure.project.public_acceptance_scope import RuntimeScope
from infrastructure.project.public_reference import _canonical_inventory
from infrastructure.project.public_reference_git import inventory, remaining
from infrastructure.reporting.native_full_worker_pdfium import (
    NativePDFiumSelection,
    admit_full_worker_pdfium_providers,
    full_worker_pdfium_execution,
)
from tests.infra_tests.project.test_public_reference import (
    complete_reference as complete_reference,
)
from tests.infra_tests.reporting.test_native_pdfium_verify_current import _namespace_absent, _run_owned, _source_aba

pytestmark = [pytest.mark.external_fixture, pytest.mark.timeout(1800)]
SCOPE = "templates/template_code_project"
CONTROLS = (
    "positive",
    "current-after-data",
    "original-after-data",
    "current-after-final-git",
    "wheel-bytes",
    "wheel-replaced",
    "site-body",
    "site-record",
    "import-origin",
    "loaded-positive",
    "loaded-body",
    "loaded-code",
    "loaded-bytecode",
    "deadline",
)
SEQUENCE = [
    "owner",
    "guard",
    "sdk",
    "reference",
    "git",
    "current",
    "data",
    "data-return",
    "git",
    "reference",
    "sdk",
    "git",
    "current",
]


class _RuntimeObservation:
    """Observe actual frames and mutate only explicitly selected disposable DATA."""

    def __init__(self, runtime: runtime_module.PDFiumRuntimeAdmission, control: str = "positive") -> None:
        self.runtime = runtime
        self.control = control
        self.guard_code = source_module.NativeSourceContext._correspondence_guard.__wrapped__.__code__
        self.verify_code = runtime_module.PDFiumRuntimeAdmission.verify.__code__
        self.data_code = data_module.observe_runtime_data.__code__
        self.guard_frames: list[FrameType] = []
        self.events: list[str] = []
        self.deadlines: list[float] = []
        self.git_returns: dict[int, int] = {}
        self.data_returned = False
        self.mutation: dict[str, Any] | None = None
        self.direct_codes = {
            source_module._verify_selected_sdk.__code__: "sdk",
            type(runtime.source.reference).verify_unchanged.__code__: "reference",
            source_module.inventory.__code__: "git",
            source_module.NativeSourceContext._verify_current_source.__code__: "current",
        }

    def __call__(self, frame: FrameType, event: str, argument: Any) -> None:
        code = frame.f_code
        parent = frame.f_back
        parent_code = None if parent is None else parent.f_code
        label = None
        if event == "call":
            if code is self.guard_code and frame.f_locals.get("self") is self.runtime.source:
                if not any(held is frame for held in self.guard_frames):
                    self.guard_frames.append(frame)
                    self.git_returns[id(frame)] = 0
                    label = "guard"
            elif parent_code is self.guard_code:
                label = self.direct_codes.get(code)
            elif parent_code is self.verify_code:
                if code is data_module.validate_runtime_owner.__code__:
                    label = "owner"
                elif code is self.data_code:
                    label = "data"
            if label is not None:
                self.events.append(label)
                if "deadline" in frame.f_locals:
                    self.deadlines.append(frame.f_locals["deadline"])
                if "runtime" in frame.f_locals:
                    assert frame.f_locals["runtime"] is self.runtime
                    self.deadlines.append(self.runtime.deadline)
        if event != "return" or argument is None:
            return
        data_return = code is self.data_code and parent_code is self.verify_code
        if data_return:
            assert argument == self.runtime.before
            self.data_returned = True
            self.events.append("data-return")
        final_git_return = False
        if code is source_module.inventory.__code__ and parent_code is self.guard_code:
            self.git_returns[id(parent)] += 1
            final_git_return = self.data_returned and self.git_returns[id(parent)] == 3
        if self.mutation is not None:
            return
        if (data_return and self.control in {"current-after-data", "original-after-data"}) or (
            final_git_return and self.control == "current-after-final-git"
        ):
            root = (
                self.runtime.source.reference.root
                if self.control == "original-after-data"
                else self.runtime.source.bindings.current_root
            )
            self.mutation = _source_aba(root / "README.md")
            self.events.append("aba")
        elif (
            code is installed_module._installed.__code__
            and parent_code is self.data_code
            and self.control in {"loaded-body", "loaded-code"}
        ):
            assert argument == self.runtime.before
            assert parent is not None
            target = (
                parent.f_locals["loaded"]
                if self.control == "loaded-body"
                else self.runtime.site / "pypdfium2_raw/bindings.py"
            )
            assert isinstance(target, Path) and target.is_relative_to(self.runtime.site)
            before = installed_module._file(target, self.runtime.deadline)
            replacement = target.with_name(target.name + ".owned-replacement")
            assert not replacement.exists()
            addition = b"\0" if self.control == "loaded-body" else b"\nOWNED_RUNTIME_CONTROL = True\n"
            replacement.write_bytes(before[0] + addition)
            replacement.replace(target)
            after = installed_module._file(target, self.runtime.deadline)
            assert before != after and before[1]["inode"] != after[1]["inode"]
            self.mutation = {"target": str(target), "before": before[1], "after": after[1]}
            self.events.append("installed-return-mutation")

    def verify(self, *, loaded: Path | None = None) -> dict[str, Any]:
        previous = sys.getprofile()
        assert previous is None, "Do not replace another profiler in the genuine child"
        try:
            sys.setprofile(self)
            return self.runtime.verify(loaded=loaded)
        finally:
            sys.setprofile(previous)

    def assert_single_guard(self) -> None:
        assert len(self.guard_frames) == 1, self.events
        assert self.events == SEQUENCE, self.events
        assert list(self.git_returns.values()) == [3]
        self.assert_clock()

    def assert_clock(self) -> None:
        assert self.deadlines and all(value == self.runtime.deadline for value in self.deadlines)


def _provider_mutation(runtime: runtime_module.PDFiumRuntimeAdmission, control: str, workspace: Path) -> str:
    target = runtime.site / "pypdfium2/__init__.py"
    if control == "wheel-bytes":
        runtime.wheel.write_bytes(runtime.wheel.read_bytes() + b"Owned changed wheel bytes\n")
        return "Source-nominated wheel identity changed"
    if control == "wheel-replaced":
        before = runtime.wheel.stat()
        replacement = runtime.wheel.with_suffix(".replacement")
        shutil.copy2(runtime.wheel, replacement)
        replacement.replace(runtime.wheel)
        assert runtime.wheel.stat().st_ino != before.st_ino
        return "Source-nominated wheel identity changed"
    if control == "site-body":
        target.write_bytes(target.read_bytes() + b"\nOWNED_RUNTIME_CONTROL = True\n")
        return "actual installed file differs from its exact RECORD hash/size"
    if control == "site-record":
        records = tuple(runtime.site.glob("pypdfium2-*.dist-info/RECORD"))
        assert len(records) == 1
        records[0].write_bytes(records[0].read_bytes() + b"owned-unlisted.txt,,\n")
        return "installed complete file set differs from the original Source wheel"
    if control == "import-origin":
        shadow = workspace / "owned-import-shadow"
        (shadow / "pypdfium2").mkdir(parents=True)
        shutil.copy2(target, shadow / "pypdfium2/__init__.py")
        sys.path.insert(0, str(shadow))
        importlib.invalidate_caches()
        actual = importlib.machinery.PathFinder.find_spec("pypdfium2", sys.path)
        assert actual is not None and actual.origin == str(shadow / "pypdfium2/__init__.py")
        _namespace_absent()
        return "actual selected PDFium import provider differs"
    raise AssertionError(f"Unknown provider control: {control}")


def _loaded_control(runtime: runtime_module.PDFiumRuntimeAdmission, control: str) -> dict[str, Any]:
    provider = admit_full_worker_pdfium_providers(
        runtime.source, ((SCOPE, NativePDFiumSelection(runtime.site, runtime.wheel)),), deadline=runtime.deadline
    )[SCOPE]
    observation = _RuntimeObservation(runtime, control)
    expected = {
        "loaded-body": "actual loaded library body/physical identity changed",
        "loaded-code": "executed public module differs from current source bytes",
        "loaded-bytecode": "loaded public module cache differs from execution-time bytes",
    }
    directory = runtime.source.bindings.current_root / "output/readiness/owned-runtime-control"
    expectation = nullcontext() if control == "loaded-positive" else pytest.raises(ValueError, match=expected[control])
    with expectation as failure:
        with full_worker_pdfium_execution(
            provider, directory=directory, deadline=runtime.deadline, runtime_admission=runtime
        ) as execution:
            raw = sys.modules["pypdfium2_raw.bindings"]
            loaded = Path(raw._libs["pdfium"]._name).resolve(strict=True)
            assert loaded.is_relative_to(runtime.site)
            if control == "loaded-positive":
                for _ in range(2):
                    observation = _RuntimeObservation(runtime)
                    assert observation.verify(loaded=loaded) == runtime.before
                    observation.assert_single_guard()
            else:
                if control == "loaded-bytecode":
                    assert isinstance(raw.__spec__, importlib.machinery.ModuleSpec)
                    assert isinstance(raw.__spec__.cached, str)
                    cache = Path(raw.__spec__.cached)
                    assert cache.is_relative_to(runtime.prefix) and cache.is_file()
                    cache.write_bytes(cache.read_bytes() + b"Owned changed audited cache\n")
                observation.verify(loaded=loaded)
                raise AssertionError("The nominated runtime verification must itself refuse")
    if control == "loaded-positive":
        assert execution.completed_binding is not None
        return {"events": observation.events, "completed_binding": execution.completed_binding}
    assert failure is not None
    observation.assert_clock()
    assert observation.events[-5:] == ["git", "reference", "sdk", "git", "current"]
    if control != "loaded-bytecode":
        assert observation.mutation is not None, "The actual installed DATA return was not reached"
    assert runtime.source.current_source_reader.unchanged()
    return {"refusal": str(failure.value), "events": observation.events, "mutation": observation.mutation}


def _child_control(payload: dict[str, Any]) -> None:
    deadline = payload["deadline"]
    remaining(deadline)
    _namespace_absent()
    original, mirror = Path(payload["original"]), Path(payload["mirror"])
    prefix, site = Path(payload["prefix"]), Path(sysconfig.get_path("purelib")).absolute()
    assert site == Path(payload["site"]) and Path(sys.prefix).absolute() == Path(payload["environment"])
    registry = getattr(sys, "_template_executed_bytecode_audit", None)
    assert isinstance(registry, MappingProxyType)
    assert registry["prefix"] == str(prefix) and tuple(registry["source_roots"]) == tuple(payload["audit_roots"])
    assert infrastructure.__file__ is not None
    sdk = Path(infrastructure.__file__).absolute().parent
    assert sdk == Path(payload["sdk_parent"]) / "infrastructure"
    metadata = mirror.stat()
    source = source_module.admit_external_native_source(
        source_module.NativeExternalSourceBindings(
            original,
            payload["commit"],
            payload["fingerprint"],
            mirror,
            (metadata.st_dev, metadata.st_ino),
            sdk,
            json.dumps(capture_implementation_custody(fresh_pycache_prefix=prefix), sort_keys=True).encode(),
            uuid4().hex,
        ),
        deadline=deadline,
        fresh_pycache_prefix=prefix,
    )
    control = payload["control"]
    runtime_deadline = deadline - 15 if control == "deadline" else deadline
    runtime = runtime_module.admit_pdfium_runtime(
        source, scope=SCOPE, site=site, wheel=Path(payload["wheel"]), deadline=runtime_deadline
    )
    assert runtime.deadline == runtime_deadline and runtime.owner_pid == os.getpid()
    held_seal, held_before = runtime.seal, json.dumps(runtime.before, sort_keys=True)
    readmes = {root: (root / "README.md").read_bytes() for root in (original, mirror)}
    observation = _RuntimeObservation(runtime, control)
    result: dict[str, Any] = {"control": control, "case_deadline": deadline, "runtime_deadline": runtime_deadline}
    if control == "positive":
        traces = []
        for _ in range(2):
            observation = _RuntimeObservation(runtime)
            assert observation.verify() == runtime.before
            observation.assert_single_guard()
            traces.append(observation.events)
        result["repeated_events"] = traces
    elif control.startswith("loaded-"):
        result.update(_loaded_control(runtime, control))
    elif control == "deadline":
        remaining(runtime_deadline)
        while time.monotonic() <= runtime_deadline:
            time.sleep(min(0.05, max(0.001, runtime_deadline - time.monotonic())))
        with pytest.raises(TimeoutError) as failure:
            observation.verify()
        assert not observation.events and not observation.guard_frames
        result.update(refusal=str(failure.value), refused_monotonic=time.monotonic())
    elif control.startswith(("current-", "original-")):
        with pytest.raises(ValueError) as failure:
            observation.verify()
        assert observation.data_returned and observation.mutation is not None
        observation.assert_clock()
        assert observation.events[-1] == ("reference" if control == "original-after-data" else "current")
        if control == "current-after-final-git":
            assert observation.events[-2:] == ["aba", "current"]
            assert list(observation.git_returns.values())[-1] == 3
        reader = source.reference.reader if control == "original-after-data" else source.current_source_reader
        assert not reader.unchanged()
        result.update(refusal=str(failure.value), events=observation.events, mutation=observation.mutation)
    else:
        expected = _provider_mutation(runtime, control, Path(payload["environment"]).parent)
        with pytest.raises(ValueError, match=expected) as failure:
            observation.verify()
        observation.assert_clock()
        assert observation.events[-5:] == ["git", "reference", "sdk", "git", "current"]
        assert source.current_source_reader.unchanged()
        result.update(refusal=str(failure.value), events=observation.events)
    if not control.startswith("loaded-"):
        _namespace_absent()
    for root, content in readmes.items():
        assert (root / "README.md").read_bytes() == content
    assert runtime.seal == held_seal and json.dumps(runtime.before, sort_keys=True) == held_before
    assert runtime.deadline == runtime_deadline and runtime.owner_pid == os.getpid()
    remaining(deadline)
    Path(payload["result"]).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")


def _clone_with_deadline(fixture: tuple[Path, str, str], destination: Path, *, deadline: float) -> Path:
    original, commit, source = fixture
    expected = inventory(original, commit, deadline)
    assert not destination.exists()
    assert len(expected.gitlinks) == 1
    link = expected.gitlinks[0]
    assert link.path == "infrastructure/steganography/kmyth"
    executable = shutil.which("git", path=os.defpath)
    assert executable is not None
    commands = (
        (destination.parent, ["clone", "--quiet", "--no-local", "--no-hardlinks", str(original), str(destination)]),
        (
            destination,
            ["clone", "--quiet", "--no-local", "--no-hardlinks", "--no-checkout", str(original / link.path), link.path],
        ),
        (destination / link.path, ["checkout", "--quiet", "--detach", link.oid]),
    )
    environment = {"PATH": os.defpath, "LC_ALL": "C", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
    for position, (cwd, arguments) in enumerate(commands):
        label = destination.name + "-git-" + str(position)
        with (
            (destination.parent / (label + ".stdout")).open("xb") as stdout,
            (destination.parent / (label + ".stderr")).open("xb") as stderr,
        ):
            result = subprocess.run(
                [
                    executable,
                    "-c",
                    "user.name=Public reference fixture",
                    "-c",
                    "user.email=fixture@example.invalid",
                    *arguments,
                ],
                cwd=cwd,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                check=False,
                timeout=remaining(deadline),
            )
        (destination.parent / (label + ".exit")).write_text(str(result.returncode) + "\n")
        assert result.returncode == 0, label
        remaining(deadline)
    for relative, kind, _ in _canonical_inventory(original):
        remaining(deadline)
        if kind == "directory":
            (destination / relative).mkdir(parents=True, exist_ok=True)
    assert inventory(destination, commit, deadline) == expected == inventory(original, commit, deadline)
    assert _canonical_inventory(destination) == _canonical_inventory(original)
    assert RuntimeScope(destination, "root").source_identity() == source
    for directory in (destination, destination / link.path):
        assert not (directory / ".git/objects/info/alternates").exists()
    remaining(deadline)
    return destination


@pytest.mark.parametrize("control", CONTROLS)
def test_genuine_pdfium_runtime_guard(complete_reference: tuple[Path, str, str], tmp_path: Path, control: str) -> None:
    deadline = time.monotonic() + 900
    nominated = os.environ.get("TEMPLATE_TEST_PDFIUM_WHEEL")
    assert nominated, "Prerequisite missing: nominate an authentic local Source-locked platform PDFium wheel"
    external = Path(nominated)
    assert external.is_absolute() and external.is_file() and not external.is_symlink()
    uv = shutil.which("uv")
    assert uv is not None, "Prerequisite missing: installed uv for offline disposable installation"
    external_before = installed_module._file(external, deadline)
    workspace = tmp_path.resolve()
    original = _clone_with_deadline(complete_reference, workspace / "original", deadline=deadline)
    mirror = _clone_with_deadline(complete_reference, workspace / "current", deadline=deadline)
    wheel = workspace / external.name
    shutil.copy2(external, wheel)
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
    _run_owned(
        [str(interpreter), "-I", "-B", "-c", "import sysconfig; print(sysconfig.get_path('purelib'))"],
        cwd=workspace,
        deadline=deadline,
        label="site",
    )
    site = Path((workspace / "site.stdout").read_text().strip()).absolute()
    assert site.is_dir() and site.is_relative_to(environment)
    assert infrastructure.__file__ is not None
    sdk = Path(infrastructure.__file__).resolve().parent
    prefix = workspace / "fresh-pycache"
    prefix.mkdir(mode=0o700)
    roots = (sdk, *(site / name for name in installed_module.PROVIDERS))
    result_path = workspace / "runtime-observation.json"
    payload = {
        "original": str(original),
        "mirror": str(mirror),
        "commit": complete_reference[1],
        "fingerprint": complete_reference[2],
        "wheel": str(wheel),
        "environment": str(environment),
        "site": str(site),
        "prefix": str(prefix),
        "audit_roots": [str(root) for root in roots],
        "deadline": deadline,
        "control": control,
        "result": str(result_path),
        "test_file": str(Path(__file__).resolve()),
        "sdk_parent": str(sdk.parent),
        "dependency_paths": [str(Path(path).resolve()) for path in sys.path if path and Path(path).is_dir()],
    }
    payload_path = workspace / "runtime-input.json"
    payload_path.write_text(json.dumps(payload, sort_keys=True))
    bootstrap = bytecode_audit_bootstrap(roots, prefix) + (
        "import json, pathlib, runpy, sys\n"
        "payload = json.loads(pathlib.Path(sys.argv[1]).read_text())\n"
        "sys.path.insert(0, payload['sdk_parent'])\n"
        "sys.path.extend(path for path in payload['dependency_paths'] if path not in sys.path)\n"
        "runpy.run_path(payload['test_file'])['_child_control'](payload)\n"
    )
    _run_owned(
        [str(interpreter), "-I", "-B", "-X", f"pycache_prefix={prefix}", "-c", bootstrap, str(payload_path)],
        cwd=workspace,
        deadline=deadline,
        label="control",
    )
    result = json.loads(result_path.read_text())
    assert result["control"] == control and result["case_deadline"] == deadline
    assert installed_module._file(external, deadline) == external_before
    remaining(deadline)
