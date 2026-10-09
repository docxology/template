"""Actual installed-SDK original four Office cells and Textbook seven controls.

This is a thin Source-owned supervisor. Every child has its own original 120s
phase inside the unchanged caller deadline; custody starts before its inputs
and bootstrap are prepared and ends only after actual guardian cleanup and
exact artifact retention. No tag, release or native command runs on import.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_format_acceptance_checks import native_tool_record
from infrastructure.reporting.native_format_acceptance_contracts import (
    create_private_native_directory,
    native_artifact_contract,
)
from infrastructure.reporting.native_office_control_custody import (
    SCHEMA,
    WORKER,
    NativeOfficeControlOriginal,
    _capture_original,
)
from infrastructure.reporting.native_office_diagram_controls import CONTROL_CODES
from infrastructure.reporting.native_office_diagram_runtime import (
    PDFiumRuntimeAdmission,
)
from infrastructure.reporting.native_source_external_admission import (
    NativeSourceContext,
)
from infrastructure.reporting.native_source_provider_bootstrap import (
    format_selected_sdk_native_bootstrap,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SCOPES = ("templates/template_code_project", "templates/template_textbook")
KINDS = ("docx", "epub")


@dataclass(frozen=True)
class OfficeNativeDependencies:
    """Explicit actual prepared tools; Source factories independently admit them."""

    package_root: Path
    mermaid_dependency_root: Path | None
    node_executable: Path
    chrome_executable: Path
    font_files: tuple[Path, ...]
    pdfium_site: Path
    pdfium_wheel: Path
    epubcheck_jar: Path | None
    java_executable: Path | None
    frozen_epub_engine: Path | None

    def observation(self) -> dict[str, Any]:
        return {
            key: [str(item) for item in value] if isinstance(value, tuple) else None if value is None else str(value)
            for key, value in asdict(self).items()
        }


def supervise_office_original_cells(
    root: Path,
    directory: Path,
    source: NativeSourceContext,
    pdfium_runtime: PDFiumRuntimeAdmission,
    dependencies: OfficeNativeDependencies,
    *,
    interpreter: Path,
    env: dict[str, str],
    deadline: float,
) -> tuple[NativeOfficeControlOriginal, ...]:
    """Execute all four actual native cells, then genuine 0/1 diagram controls."""
    from infrastructure.reporting.native_tool_producer import (
        current_native_producer_operation,
    )

    producer = current_native_producer_operation()
    if (
        producer is None
        or producer.source is not source
        or source.bindings.current_root != root
        or producer.deadline != deadline
    ):
        raise ValueError("Office original launcher requires this actual live Source/tool owner and unchanged clock")
    if dependencies.pdfium_site != pdfium_runtime.site or dependencies.pdfium_wheel != pdfium_runtime.wheel:
        raise ValueError("Office original dependency nomination differs from genuinely admitted provider")
    expected_runtime = json.loads(source.bindings.expected_implementation_bytes).get("runtime_environment", {})
    if not interpreter.is_absolute() or str(interpreter.resolve(strict=True)) != expected_runtime.get(
        "python_executable"
    ):
        raise ValueError("Office selected interpreter differs from actual admitted Source SDK runtime")
    create_private_native_directory(root, directory)
    cases = [(scope, kind, "office-cell") for scope in SCOPES for kind in KINDS]
    cases.extend((SCOPES[1], kind, control) for kind in KINDS for control in ("baseline", *CONTROL_CODES))
    originals = []
    for ordinal, (scope, kind, control) in enumerate(cases):
        remaining(deadline)
        # Admission, bootstrap, child, cleanup and final custody share this cap.
        phase_deadline = min(deadline, time.monotonic() + 120.0)
        child = directory / f"original-{ordinal:02d}-{kind}-{control}"
        if child.exists() or child.is_symlink():
            raise ValueError("Office original child evidence directory must be fresh")
        create_private_native_directory(root, child)
        create_private_native_directory(root, child / "closure")
        source.verify_correspondence(source.reference, root, SnapshotReader(root), phase_deadline)
        pdfium_runtime.verify()
        contracts = native_artifact_contract(root, scope, (kind,), SnapshotReader(root))
        selected = [value for value in contracts if value.id == f"manuscript:{kind}"]
        if len(selected) != 1:
            raise ValueError("Office original child requires one exact Source-declared combined artifact")
        candidate = SnapshotReader(root).read(selected[0].path) if control == "office-cell" else None
        implementation = write_json(
            root,
            child / "implementation.json",
            json.loads(source.bindings.expected_implementation_bytes),
        )
        if SnapshotReader(root).read(implementation["path"]).content != source.bindings.expected_implementation_bytes:
            # Preserve the exact original bytes rather than normalize them.
            from infrastructure.core.files.secure_write import (
                atomic_write_bytes_confined,
            )

            atomic_write_bytes_confined(
                root,
                child / "implementation.json",
                source.bindings.expected_implementation_bytes,
                mode=0o600,
            )
            implementation = {
                "path": implementation["path"],
                "sha256": hashlib.sha256(source.bindings.expected_implementation_bytes).hexdigest(),
            }
        mermaid_selection = None
        if dependencies.mermaid_dependency_root is not None:
            from infrastructure.reporting.native_mermaid_runtime_selection import (
                NativeMermaidSelection,
                admit_source_mermaid_selection,
            )

            selection = NativeMermaidSelection(
                dependencies.package_root,
                dependencies.mermaid_dependency_root,
                dependencies.node_executable,
                dependencies.chrome_executable,
            )
            admitted = admit_source_mermaid_selection(
                selection, source, deadline=phase_deadline, directory=child / "parent-mermaid-runtime", env=env
            )
            mermaid_selection = admitted.spec_data()
        descriptor = json.loads(source.descriptor(scope, deadline=phase_deadline))
        closure_identity = (child / "closure").stat()
        specification = {
            "schema_version": SCHEMA,
            "run_id": source.bindings.run_id,
            "scope": scope,
            "kind": kind,
            "control": control,
            "expected_exit": 1 if control in CONTROL_CODES else 0,
            "blocked_exit": 2,
            "directory": child.relative_to(root).as_posix(),
            "source": descriptor,
            "artifact": asdict(selected[0]),
            "candidate": None if candidate is None else {"path": candidate.relative, "sha256": candidate.sha256},
            "implementation": implementation,
            "dependencies": dependencies.observation(),
            "mermaid_selection": mermaid_selection,
            "pdfium_wheel_sha256": pdfium_runtime.wheel_observation["sha256"],
            "original_deadline_monotonic": phase_deadline,
            "caller_deadline_monotonic": deadline,
            "closure_identity": [closure_identity.st_dev, closure_identity.st_ino],
        }
        spec = write_json(root, child / "specification.json", specification)
        sdk = source.bindings.selected_sdk_package_root
        hook = source.current_source_reader.read("infrastructure/core/bytecode_audit.py").content
        expected = json.loads(source.bindings.expected_implementation_bytes)["files"]
        if expected["infrastructure/core/bytecode_audit.py"] != hashlib.sha256(hook).hexdigest():
            raise ValueError("Office child raw hook differs from selected admitted SDK")
        bootstrap = format_selected_sdk_native_bootstrap(
            hook,
            sdk,
            tuple(dependencies.pdfium_site / name for name in ("pypdfium2", "pypdfium2_raw")),
            root / implementation["path"],
            implementation["sha256"],
            child / "closure",
            (closure_identity.st_dev, closure_identity.st_ino),
            phase_deadline,
            required_worker_module=WORKER,
        )
        command: tuple[str, ...] = (
            str(interpreter),
            "-I",
            "-c",
            bootstrap,
            "--root",
            str(root),
            "--specification",
            spec["path"],
            "--specification-sha256",
            spec["sha256"],
            "--implementation-sha256",
            implementation["sha256"],
            "--deadline",
            repr(phase_deadline),
            "--run-id",
            source.bindings.run_id,
        )
        if dependencies.mermaid_dependency_root is not None:
            command += (
                "--mermaid-package-root",
                str(dependencies.package_root),
                "--mermaid-dependency-root",
                str(dependencies.mermaid_dependency_root),
                "--mermaid-node",
                str(dependencies.node_executable),
                "--mermaid-chrome",
                str(dependencies.chrome_executable),
            )
        source.verify_correspondence(source.reference, root, SnapshotReader(root), phase_deadline)
        # The explicit venv launcher must be preserved, while resolved body/OS
        # identity is observed by the same generic guardian/process API.
        actual = native_tool_record(
            root,
            child,
            str(interpreter),
            list(command[1:]),
            env=env,
            deadline=phase_deadline,
            run_id=source.bindings.run_id,
            purpose="office-original-child",
            preserve_nominated_launcher=True,
        )
        expected_code = {
            str(sdk / name.removeprefix("infrastructure/")): digest
            for name, digest in expected.items()
            if name.startswith("infrastructure/") and name.endswith(".py")
        }
        expected_code.update(
            {
                str(dependencies.pdfium_site / name): hashlib.sha256(content).hexdigest()
                for name, content in pdfium_runtime.members.items()
                if name.endswith(".py")
            }
        )
        original = _capture_original(
            source,
            child,
            specification,
            command,
            actual["artifact"],
            expected_code=expected_code,
            deadline=phase_deadline,
        )
        observed = SnapshotReader(root).read(original.observation_relative).json_object()
        if (
            observed["oracle_exit_code"] != specification["expected_exit"]
            or observed["control"] != control
            or observed["scope"] != scope
            or observed["kind"] != kind
        ):
            raise ValueError("Office actual original child failed its exact Source-declared oracle")
        originals.append(original)
        source.verify_correspondence(source.reference, root, SnapshotReader(root), deadline)
    pdfium_runtime.verify()
    source.verify_correspondence(source.reference, root, SnapshotReader(root), deadline)
    remaining(deadline)
    return tuple(originals)
