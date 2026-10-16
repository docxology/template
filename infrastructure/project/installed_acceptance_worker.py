"""One bounded locked build and outside-source installed-wheel execution."""

from __future__ import annotations

import hashlib
import json
import os
import math
import time
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any

from infrastructure.core.execution_boundary import build_bounded_env
from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined
from infrastructure.core.implementation_custody import bytecode_audit_bootstrap, source_file_bytes
from infrastructure.core.pipeline.fingerprints import tree_records
from infrastructure.core.runtime._tools import find_uv
from infrastructure.core.testing.project_test_matrix import ProjectTestTask, run_project_test_matrix
from infrastructure.project.acceptance_payload import format_acceptance_payload_loader, write_acceptance_payload
from infrastructure.project.installed_acceptance_artifacts import (
    INSTALLED_PROBE,
    freeze_wheel_bytes,
    prepare_export,
    write_binary,
)
from infrastructure.project.public_acceptance_evidence import cell_environment, write_json
from infrastructure.project.installed_acceptance_runtime import (
    MissingProviderWheel,
    freeze_locked_metadata,
    install_runtime,
)
from infrastructure.reporting.readiness_receipts import (
    deliverable_identity,
    project_source_identity,
    source_fingerprint,
)
from infrastructure.reporting.release_readiness_profile import Requirement


class MissingInstalledTool(RuntimeError):
    """An explicitly missing installed interpreter, lock or cached dependency."""


def _environment(interpreter: Path, scratch: Path, *, repo_root: Path | None = None) -> dict[str, str]:
    environment = build_bounded_env(cell_environment(interpreter, scratch, repo_root=repo_root))
    for key in tuple(environment):
        if (key.startswith(("UV_", "PIP_")) and key != "UV_CACHE_DIR") or key in {
            "VIRTUAL_ENV",
            "PYTHONPATH",
            "PYTHONHOME",
        }:
            environment.pop(key)
    # Preserve the prepared wheel-data cache; every installation still uses
    # the source-owned lock and mandatory artifact hashes with networking off.
    environment.update(UV_PYTHON_DOWNLOADS="never", UV_NO_SYNC="1", UV_OFFLINE="1", MPLBACKEND="Agg")
    return environment


def _run(
    command: tuple[str, ...],
    cwd: Path,
    env: dict[str, str],
    deadline: float,
    root: Path,
    directory: Path,
    label: str,
) -> dict[str, Any]:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("total installed-cell deadline exhausted")
    task = ProjectTestTask(0, label, command, cwd, env, max(1, math.ceil(remaining)), True)
    result = run_project_test_matrix([task])[0]
    receipt = {**asdict(result), "command": list(command), "cwd": str(cwd)}
    write_json(root, directory / f"{label}-process.json", receipt)
    if result.timed_out or time.monotonic() > deadline:
        raise TimeoutError(f"installed {label} exceeded the total deadline")
    if result.returncode:
        # Only uv's explicit offline-cache failure is classified as a missing tool.
        if "network is disabled" in result.output_tail or "network connectivity is disabled" in result.output_tail:
            raise MissingInstalledTool(f"{label}: locked dependency is absent from the offline cache")
        raise ValueError(f"{label} child failed (exit {result.returncode}): {result.output_tail}")
    return receipt


def run_installed_cell(
    root: Path,
    requirement: Requirement,
    runtime: str,
    interpreter: Path | None,
    scratch: Path,
    directory: Path,
    *,
    timeout_seconds: int = 600,
    provider_wheels: dict[str, tuple[dict[str, str], Requirement]] | None = None,
) -> dict[str, Any]:
    """Build only with locked tools; install into a fresh unique dependency environment."""
    started = time.monotonic()
    result: dict[str, Any] = {"scope": requirement.scope, "python_version": runtime, "status": "fail"}
    export_details: dict[str, Any] = {}
    try:
        if type(timeout_seconds) is not int or timeout_seconds <= 0:
            raise ValueError("installed-cell deadline must be a positive integer")
        deadline = started + timeout_seconds
        uv = find_uv()
        if uv is None or interpreter is None or not interpreter.is_file():
            raise MissingInstalledTool("uv or the explicitly selected installed interpreter is unavailable")
        interpreter = interpreter.absolute()
        selected_binary = interpreter.resolve(strict=True)
        selected_identity = tree_records(selected_binary)
        selected_sha = selected_identity[0][2]
        scratch.mkdir()
        environment = _environment(interpreter, scratch, repo_root=root)
        source, export_details = prepare_export(root, requirement, scratch, directory, deadline_monotonic=deadline)
        if not (source / "uv.lock").is_file():
            raise MissingInstalledTool("standalone source has no locked dependency environment")
        metadata = freeze_locked_metadata(root, scratch)
        metadata_binding = write_json(
            root,
            directory / "locked-metadata.json",
            dict((name, digest) for name, kind, digest in metadata.records if kind == "file"),
        )
        build_requirements = scratch / "build-requirements.txt"
        # The build group belongs to the platform's source-owned lock, not a fresh resolver.
        _run(
            (
                uv,
                "export",
                "--directory",
                str(metadata.root),
                "--locked",
                "--offline",
                "--only-group",
                "installed-build",
                "--no-emit-project",
                "--no-header",
                "--no-annotate",
                "--output-file",
                str(build_requirements),
            ),
            scratch,
            environment,
            deadline,
            root,
            directory,
            "build-lock",
        )
        if not metadata.unchanged():
            raise ValueError("private locked metadata changed during build-tool export")
        write_binary(root, directory / "build-requirements.txt", build_requirements.read_bytes())
        build_env = scratch / "build-environment"
        _run(
            (uv, "venv", "--no-project", "--no-python-downloads", "--python", str(interpreter), str(build_env)),
            scratch,
            environment,
            deadline,
            root,
            directory,
            "build-venv",
        )
        build_python = build_env / "bin/python"
        _run(
            (
                uv,
                "pip",
                "sync",
                "--offline",
                "--no-config",
                "--no-build",
                "--require-hashes",
                "--python",
                str(build_python),
                str(build_requirements),
            ),
            scratch,
            environment,
            deadline,
            root,
            directory,
            "build-tools",
        )
        wheel_dir = scratch / "wheels"
        _run(
            (
                uv,
                "build",
                "--wheel",
                "--offline",
                "--no-config",
                "--no-python-downloads",
                "--no-build-isolation",
                "--python",
                str(build_python),
                "--out-dir",
                str(wheel_dir),
                str(source),
            ),
            scratch,
            environment,
            deadline,
            root,
            directory,
            "wheel-build",
        )
        wheels = tuple(wheel_dir.glob("*.whl"))
        if len(wheels) != 1:
            raise ValueError("fresh wheel build did not produce exactly one artifact")
        wheel = wheels[0]
        admitted_wheel = freeze_wheel_bytes(
            root, requirement, read_bytes_confined(scratch, wheel, max_bytes=64 * 1024 * 1024), scratch, wheel.name
        )
        targets, members = admitted_wheel.targets, admitted_wheel.members
        wheel_binding = write_binary(root, directory / wheel.name, admitted_wheel.content)
        installed_python, provider = install_runtime(
            root,
            requirement,
            scratch,
            directory,
            interpreter,
            admitted_wheel,
            uv,
            lambda command, label: _run(command, scratch, environment, deadline, root, directory, label),
            provider_wheels=provider_wheels or {},
            metadata=metadata,
        )
        outside = scratch / "outside-source"
        outside.mkdir()
        spec = {
            "scope": requirement.scope,
            "package": requirement.package,
            "version": requirement.version,
            "targets": targets,
            "wheel_members": members,
            "forbidden_roots": [str(root), str(source)],
            "dependency_providers": provider["providers"],
            "python_version": runtime,
            "run_nonce": uuid.uuid4().hex,
        }
        if requirement.scope == "templates/template_autopoiesis":
            spec["domain_inputs"] = {"project_root": str(source)}
        observation = outside / "probe.json"
        bytecode = scratch / "fresh-bytecode"
        bytecode.mkdir()
        environment_root = installed_python.parent.parent
        site = (
            environment_root / "Lib/site-packages"
            if os.name == "nt"
            else environment_root / "lib" / f"python{runtime}" / "site-packages"
        )
        if requirement.scope == "root" or any(item["scope"] == "root" for item in provider["providers"]):
            audit_path = site / "infrastructure/core/bytecode_audit.py"
        else:
            # A standalone project does not gain a fictional platform provider.
            # Its trusted launcher carries this exact admitted audit tool in
            # private scratch, separate from all installed-package evidence.
            audit_path = outside / "bytecode_audit.py"
            from infrastructure.core import bytecode_audit

            assert bytecode_audit.__file__ is not None
            atomic_write_bytes_confined(scratch, audit_path, source_file_bytes(Path(bytecode_audit.__file__)))
        admitted = dict(members)
        namespace_targets = list(targets)
        for selected_provider in provider["providers"]:
            admitted.update(selected_provider["wheel_members"])
            namespace_targets.extend(selected_provider["targets"])
        audit_roots = tuple(site / name for name in admitted if name.endswith(".py")) + tuple(
            site / target for target in namespace_targets if not (site / (target + ".py")).is_file()
        )
        audit = bytecode_audit_bootstrap(audit_roots, bytecode, audit_path=audit_path)
        spec["audit"] = {
            "roots": [str(path.absolute()) for path in audit_roots],
            "path": str(audit_path.absolute()),
            "prefix": str(bytecode.absolute()),
            "sha256": hashlib.sha256(source_file_bytes(audit_path)).hexdigest(),
        }
        payload_bytes = (audit + "\n" + INSTALLED_PROBE).encode()
        payload = write_acceptance_payload(
            scratch, outside / "installed-probe-payload.py", payload_bytes, forbidden_roots=(root, source)
        )
        payload_binding = write_binary(root, directory / "installed-probe-payload.py", payload_bytes)
        spec["probe_payload"] = payload
        spec_bytes = json.dumps(spec, sort_keys=True).encode()
        atomic_write_bytes_confined(scratch, outside / "probe-spec.json", spec_bytes, mode=0o400)
        spec_binding = write_binary(root, directory / "probe-spec.json", spec_bytes)
        command = (
            str(installed_python),
            "-I",
            "-X",
            f"pycache_prefix={bytecode}",
            "-c",
            format_acceptance_payload_loader(payload),
            str(outside / "probe-spec.json"),
            str(observation),
        )
        process = _run(command, outside, environment, deadline, root, directory, "installed-probe")
        details = json.loads(observation.read_text())
        if details.get("build_policy") != {
            name: environment[name]
            for name in ("SOURCE_DATE_EPOCH", "TEMPLATE_BUILD_EPOCH_SOURCE", "TEMPLATE_EXECUTION_MODE")
        }:
            raise ValueError("installed probe did not consume the nominated candidate build policy")
        if details.get("python_version") != runtime or details.get("interpreter") != str(installed_python):
            raise ValueError("installed probe used a different interpreter than the selected runtime")
        if (
            installed_python.resolve(strict=True) != selected_binary
            or details.get("interpreter_sha256") != selected_sha
            or tree_records(selected_binary) != selected_identity
        ):
            raise ValueError("selected installed interpreter identity changed or differs from the actual runtime")
        details["selected_interpreter"] = str(interpreter)
        details["selected_interpreter_sha256"] = selected_sha
        if details.get("imported_modules") != list(targets):
            raise ValueError("installed probe omitted the admitted wheel's import surface")
        if requirement.scope == "root":
            if source_fingerprint(root) != requirement.source_identity:
                raise ValueError("root source changed during installed acceptance")
        elif (
            project_source_identity(root, requirement.scope) != requirement.source_identity
            or deliverable_identity(root, requirement.scope) != requirement.deliverables_identity
        ):
            raise ValueError("project source/deliverables changed during installed acceptance")
        if not metadata.unchanged():
            raise ValueError("private locked metadata changed during installed acceptance")
        # Build backends/dependency tools may write caches, but cannot change an admitted input.
        manifest = json.loads((root / export_details["manifest_artifact"]["path"]).read_text())
        if any(
            not (source / name).is_file() or hashlib.sha256((source / name).read_bytes()).hexdigest() != digest
            for name, digest in manifest["files"].items()
        ):
            raise ValueError("exported source input changed during wheel execution")
        details.update(
            wheel_artifact=wheel_binding,
            locked_metadata_artifact=metadata_binding,
            command=list(command),
            process_artifact=write_json(root, directory / "installed-process.json", process),
            probe_spec_artifact=spec_binding,
            probe_payload_artifact=payload_binding,
            runtime_artifact=write_json(root, directory / "installed-probe.json", details),
        )
        if time.monotonic() >= deadline:
            raise TimeoutError("total installed-cell deadline exhausted after source and export custody")
        result.update(status="pass", details=details)
    except (MissingInstalledTool, MissingProviderWheel) as error:
        result.update(
            status="blocked",
            diagnostic=str(error),
            blockers=[{"tool": "installed package/runtime", "reason": str(error)}],
        )
    except (OSError, ValueError, KeyError, TypeError, TimeoutError) as error:
        result.update(status="fail", diagnostic=str(error))
    result.update(export=export_details, duration_seconds=round(time.monotonic() - started, 3))
    write_json(root, directory / "installed-cell.json", result)
    return result
