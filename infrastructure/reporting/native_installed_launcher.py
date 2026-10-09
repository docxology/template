"""Prepare a fresh Source4.0.1 wheel and supervise its cold native role.

This outer build/transport harness nominates inputs and retains genuine process
results. Original/native authority is constructed only inside the separately
installed Source controller/reader and the authenticated hosted collector.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.core.implementation_custody import source_file_bytes
from infrastructure.reporting.native_installed_invocation import (
    NativeInstalledInvocationFailure,
    capture_prepared_sdk,
    launch_prepared_native,
)
from infrastructure.reporting.native_installed_preparation import (
    NativePreparationFailure,
    prepare_native_installed_runtime,
)
from infrastructure.reporting.native_prepared_pdfium import prepare_pdfium_nomination
from infrastructure.reporting.native_source_provider_bootstrap import NATIVE_CONTROLLER_MODULE, NATIVE_READER_MODULE
from infrastructure.reporting.native_tool_process import run_native_tool_process
from infrastructure.reporting.native_preparation_resources import PREPARATION_PEAK_BYTES, require_native_capacity
from infrastructure.reporting.native_readiness_input_copy import copy_original_common_readiness, copy_source_mirror_data


def _signed_failure(result: dict[str, object]) -> int:
    actual = result.get("original_exit_code")
    if actual in (130, -2):
        return 130
    if result.get("timed_out") is True:
        return 124
    if type(actual) is int and actual != 0:
        return actual if actual > 0 else 128 - actual
    return 75


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=("original", "reader", "handoff"))
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--source-identity", required=True)
    parser.add_argument("--current-root", required=True, type=Path)
    parser.add_argument("--scratch", required=True, type=Path)
    parser.add_argument("--python", required=True, type=Path)
    parser.add_argument("--uv", required=True, type=Path)
    parser.add_argument("--timeout", type=int, default=14400)
    parser.add_argument("--expected-platform", required=True, choices=("Linux", "Darwin"))
    parser.add_argument("--mermaid-package-root", required=True, type=Path)
    parser.add_argument("--mermaid-dependency-root", required=True, type=Path)
    parser.add_argument("--mermaid-node-executable", required=True, type=Path)
    parser.add_argument("--mermaid-chrome-executable", required=True, type=Path)
    parser.add_argument("--pdfium-wheel", type=Path)
    parser.add_argument("--office-font-file", action="append", default=[], type=Path)
    parser.add_argument("--office-font-directory", action="append", default=[], type=Path)
    parser.add_argument("--epubcheck-jar", type=Path)
    parser.add_argument("--java-executable", type=Path)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--run-id", required=True, type=int)
    parser.add_argument("--receipt", action="append", default=[])
    parser.add_argument("--root-receipt", action="append", default=[])
    parser.add_argument("--auxiliary-receipt", action="append", default=[])
    parser.add_argument("--stage-bundle", action="store_true")
    parser.add_argument("--acceptance-artifact-id", type=int)
    parser.add_argument("--acceptance-receipt-sha256")
    args = parser.parse_args(argv)
    started = time.monotonic()
    if not 0 < args.timeout <= 14400:
        parser.error("native installed launch requires the existing whole-operation budget")
    deadline = started + args.timeout
    source = args.source_root.resolve(strict=True)
    mirror = args.current_root.absolute()
    scratch = args.scratch.absolute()
    if mirror.exists() or mirror.is_symlink() or scratch.exists() or scratch.is_symlink():
        parser.error("native installed launch requires fresh owner-controlled mirror and scratch destinations")
    require_native_capacity(scratch, peak_bytes=PREPARATION_PEAK_BYTES, deadline=deadline)
    scratch.mkdir(parents=True, mode=0o700)
    diagnostics = scratch / "outer-processes"
    diagnostics.mkdir(mode=0o700)
    env = dict(os.environ, UV_LINK_MODE="copy", UV_PYTHON_DOWNLOADS="never")
    for name in ("PYTHONPATH", "PYTHONHOME", "PYTHONPYCACHEPREFIX", "PYTHONDONTWRITEBYTECODE"):
        env.pop(name, None)
    try:
        clone = run_native_tool_process(
            diagnostics,
            "git",
            ["clone", "--no-hardlinks", "--no-local", "--recurse-submodules", str(source), str(mirror)],
            cwd=source,
            env=env,
            deadline=deadline,
            purpose="actual-native-full-git-mirror",
        )
        if clone["accepted"] is not True or clone["original_exit_code"] != 0:
            raise NativeInstalledInvocationFailure(clone)
        copy_source_mirror_data(source, mirror, expected_identity=args.source_identity, deadline=deadline)
        copy_original_common_readiness(source, mirror, deadline=deadline)
        install = scratch / "installed"
        install.mkdir(mode=0o700)
        evidence = mirror / "output/readiness/native-preparation"
        evidence.mkdir(parents=True, mode=0o700)
        prepared = prepare_native_installed_runtime(
            source,
            mirror,
            install,
            evidence,
            python=args.python.absolute(),
            uv=args.uv.absolute(),
            source_commit=args.source_commit,
            source_identity=args.source_identity,
            operation_started=started,
            deadline=deadline,
            env=env,
        )
        env.update(
            TEMPLATE_PUBLIC_REFERENCE_ROOT=str(source),
            TEMPLATE_PUBLIC_REFERENCE_COMMIT=args.source_commit,
            TEMPLATE_PUBLIC_REFERENCE_FINGERPRINT=args.source_identity,
        )
        implementation, raw = capture_prepared_sdk(prepared, environment=env)
        wheel, pdfium_roots, pdfium_sources = prepare_pdfium_nomination(
            prepared, environment=env, nominated=args.pdfium_wheel
        )
        fonts = list(args.office_font_file)
        for directory in args.office_font_directory:
            if not directory.is_absolute() or directory.is_symlink():
                raise ValueError("Office fonts require explicit real nominated directories")
            fonts.extend(
                sorted(path for path in directory.rglob("*") if path.suffix.lower() in {".ttf", ".otf", ".ttc"})
            )
            if len(fonts) > 4096:
                raise ValueError("Office font nomination exceeds its existing bounded census")
        fonts = list(dict.fromkeys(path.absolute() for path in fonts))
        provider_paths: dict[str, Path] = {}
        for scope, admitted in prepared.provider_wheels.items():
            body = source_file_bytes(admitted.path)
            if hashlib.sha256(body).hexdigest() != admitted.sha256:
                raise ValueError("frozen provider wheel changed before current-root DATA retention")
            target = mirror / "output/readiness" / ("native-provider-wheels-" + args.mode) / scope / admitted.path.name
            atomic_write_bytes_confined(mirror, target, body, mode=0o600)
            if source_file_bytes(target) != body:
                raise ValueError("current-root provider DATA differs from the Source-frozen wheel")
            provider_paths[scope] = target
        common = (
            "--sdk-package-root",
            str(prepared.sdk_package_root),
            "--implementation-input",
            str(implementation),
            "--implementation-sha256",
            hashlib.sha256(raw).hexdigest(),
            "--pdfium-site",
            str(prepared.site),
            "--pdfium-wheel",
            str(wheel),
            "--mermaid-package-root",
            str(args.mermaid_package_root),
            "--mermaid-dependency-root",
            str(args.mermaid_dependency_root),
            "--mermaid-node-executable",
            str(args.mermaid_node_executable),
            "--mermaid-chrome-executable",
            str(args.mermaid_chrome_executable),
            *(item for font in fonts for item in ("--office-font-file", str(font))),
            *(item for scope, path in provider_paths.items() for item in ("--provider-wheel", f"{scope}={path}")),
            "--operation-started-monotonic",
            str(started),
            "--timeout",
            str(args.timeout),
        )
        if args.mode == "original":
            arguments = (
                "--repo-root",
                str(mirror),
                "--expected-platform",
                args.expected_platform,
                "--evidence-dir",
                str(mirror / "output/readiness/native"),
                "--hosted-transport-dir",
                str(mirror / "output/readiness/native-transport"),
                "--hosted-repository",
                args.repository,
                "--hosted-run-id",
                str(args.run_id),
                *common,
            )
            if args.epubcheck_jar is not None or args.java_executable is not None:
                if args.epubcheck_jar is None or args.java_executable is None:
                    raise ValueError("actual EPUB tools require both explicit nominations")
                arguments += (
                    "--epubcheck-jar",
                    str(args.epubcheck_jar),
                    "--java-executable",
                    str(args.java_executable),
                )
            role = NATIVE_CONTROLLER_MODULE
        else:
            arguments = (
                "--repo-root",
                str(mirror),
                "--revision",
                args.source_commit,
                "--repository",
                args.repository,
                "--run-id",
                str(args.run_id),
                *common,
                *(item for receipt in args.receipt for item in ("--receipt", receipt)),
                *(item for receipt in args.root_receipt for item in ("--root-receipt", receipt)),
                *(item for receipt in args.auxiliary_receipt for item in ("--auxiliary-receipt", receipt)),
            )
            if args.stage_bundle:
                arguments += ("--stage-bundle",)
            role = NATIVE_READER_MODULE
        if args.mode == "handoff":
            if args.acceptance_artifact_id is None or args.acceptance_receipt_sha256 is None:
                raise ValueError("handoff requires the exact existing run/artifact/receipt identity")
            arguments += (
                "--acceptance-artifact-id",
                str(args.acceptance_artifact_id),
                "--acceptance-receipt-sha256",
                args.acceptance_receipt_sha256,
            )
        result = launch_prepared_native(
            prepared,
            implementation,
            raw,
            role=role,
            arguments=arguments,
            pdfium_roots=pdfium_roots,
            pdfium_sources=pdfium_sources,
            environment=env,
        )
        record = {
            "mode": args.mode,
            "original_started_monotonic": started,
            "original_deadline_monotonic": deadline,
            "current_root": str(mirror),
            "source_commit": args.source_commit,
            "source_identity": args.source_identity,
            "actual_original_result": result,
            "native_transport": str(mirror / "output/readiness/native-transport") if args.mode == "original" else None,
        }
        if args.mode in {"original", "reader"}:
            print(
                "transport_directory="
                + str(
                    mirror
                    / "output/readiness"
                    / ("native-transport" if args.mode == "original" else "candidate-transport")
                )
            )
        atomic_write_bytes_confined(
            scratch,
            scratch / "completed-installed-launch.json",
            (json.dumps(record, sort_keys=True) + "\n").encode(),
            mode=0o600,
        )
        print(
            json.dumps({"original_os_exit": result["original_exit_code"], "current_root": str(mirror)}, sort_keys=True)
        )
        return 0
    except (NativeInstalledInvocationFailure, NativePreparationFailure) as error:
        try:
            atomic_write_bytes_confined(
                scratch,
                scratch / "failed-installed-launch.json",
                (
                    json.dumps(
                        {
                            "mode": args.mode,
                            "actual_original_result": error.result,
                            "original_deadline_monotonic": deadline,
                        },
                        sort_keys=True,
                    )
                    + "\n"
                ).encode(),
                mode=0o600,
            )
        except (OSError, ValueError, TypeError):
            print("failed launch summary could not be retained; original tool files remain", file=sys.stderr)
        print("installed native original refused; genuine process/raw evidence retained", file=sys.stderr)
        return _signed_failure(error.result)
    except KeyboardInterrupt:
        return 130
    except (OSError, ValueError, TypeError, RuntimeError) as error:
        print("installed native Source/Code admission refused: " + str(error), file=sys.stderr)
        return 124 if time.monotonic() >= deadline else 1


if __name__ == "__main__":
    raise SystemExit(main())
