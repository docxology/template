"""Pinned, bounded formal-tool acceptance with actual proof-of-detection.

Lean checks the independent phase model; TLC explores the declared finite
models. Neither establishes universal correctness of the Python protocol.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import tempfile
import time
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path

from template_formal._tool_execution import build_bounded_env, run_bounded_subprocess
from ._tool_sources import materialize, snapshot_file, snapshot_tree

LEAN_TOOLCHAIN = "leanprover/lean4:v4.28.0"
TLC_URL = "https://github.com/tlaplus/tlaplus/releases/download/v1.8.0/tla2tools.jar"
# Official asset 635357747 length/digest matched to full bytes on 2026-10-13 UTC.
# Mutable v1.8.0 locator; TLC 2.0 build from 5737c4758703f9fc4ef4ce1ff5dd912fe37d78d3.
TLC_BYTES = 4501961
TLC_SHA256 = "baf125a62e192f8d9df38035b8283b9d05f08dbf01860b2df40af489b894563d"


@dataclass(frozen=True)
class ToolCheck:
    """One actual tool invocation and its expected outcome."""

    name: str
    status: str
    argv: tuple[str, ...]
    exit_code: int | None
    stdout: str = ""
    stderr: str = ""
    diagnostic: str = ""
    consumed_tlc_sha256: str = ""
    consumed_source_sha256: dict[str, str] = field(default_factory=dict)


def _source_bytes(root: Path, deadline: float) -> dict[str, bytes]:
    """Bind complete project source without runtime state or acquired binaries."""
    runtime_roots = {
        ".git",
        ".venv",
        "output",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        ".hypothesis",
        "htmlcov",
        "node_modules",
    }

    def omit(parts: tuple[str, ...]) -> bool:
        return (
            parts[0] in runtime_roots
            or "__pycache__" in parts
            or parts[:3] == ("formal", "lean", ".lake")
            or (len(parts) == 1 and (parts[0].startswith(".coverage") or parts[0] == "coverage_project.json"))
            or (len(parts) == 2 and parts[0] == "src" and parts[1].endswith(".egg-info"))
            or "/".join(parts) == "formal/tla/tla2tools.jar"
        )

    return snapshot_tree(root, deadline=deadline, exclude=omit)


def _sources(root: Path) -> dict[str, str]:
    return {
        path: hashlib.sha256(content).hexdigest()
        for path, content in _source_bytes(root, time.monotonic() + 30).items()
    }


def _pins(snapshot: dict[str, bytes]) -> None:
    """Refuse missing, changed or dependency-bearing formal tool declarations."""
    if (
        not {
            "formal/lean/lean-toolchain",
            "formal/lean/lake-manifest.json",
            "formal/lean/lakefile.lean",
            "formal/lean/AntProtocol.lean",
        }
        <= snapshot.keys()
    ):
        raise ValueError("formal Lean declarations are missing")
    if snapshot["formal/lean/lean-toolchain"].decode().strip() != LEAN_TOOLCHAIN:
        raise ValueError("Lean toolchain differs from the exact source-owned pin")
    manifest = json.loads(snapshot["formal/lean/lake-manifest.json"])
    if not isinstance(manifest, dict) or manifest.get("packages") != [] or manifest.get("name") != "ant_protocol":
        raise ValueError("formal Lake manifest must retain its dependency-free exact project")


def _jar_snapshot(path: Path, deadline: float | None = None) -> bytes:
    """Read bounded regular cache bytes with every ancestor held and checked."""
    return snapshot_file(
        path, deadline=deadline if deadline is not None else time.monotonic() + 30, max_bytes=64 * 1024 * 1024
    )


def _run(name: str, argv: list[str], cwd: Path, deadline: float, *, violation: bool = False) -> ToolCheck:
    """Consume a single total deadline and validate real semantic tool output."""
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        return ToolCheck(name, "timed_out", tuple(argv), None, diagnostic="total formal-tool deadline exhausted")
    try:
        result = run_bounded_subprocess(argv, cwd=cwd, env=build_bounded_env(), timeout=remaining)
    except OSError as error:
        return ToolCheck(name, "blocked", tuple(argv), None, diagnostic=str(error))
    output = result.stdout + result.stderr
    valid = result.returncode == 0
    if violation:
        valid = result.returncode == 12 and "Invariant NoFalseEstablishment is violated" in output
    elif name.startswith("tlc-AntProtocol"):
        valid = valid and "Model checking completed. No error has been found." in output
    elif name == "lean-build":
        declarations = re.findall(r"(?:depends on axioms: \[([^\]]*)\]|does not depend on any axioms)", output)
        axioms = {token.strip() for group in declarations for token in group.split(",") if token.strip()}
        valid = valid and len(declarations) >= 7 and axioms <= {"propext", "Classical.choice", "Quot.sound"}
    late = time.monotonic() >= deadline
    status = "timed_out" if result.timed_out or late else "passed" if valid else "failed"
    diagnostic = result.command_error or ("total formal-tool deadline exhausted after child cleanup" if late else "")
    return ToolCheck(name, status, tuple(argv), result.returncode, result.stdout, result.stderr, diagnostic)


def _acquire_jar(root: Path, deadline: float) -> ToolCheck:
    """Acquire only the pinned release, atomically admitting verified bytes."""
    target = root / "formal" / "tla" / "tla2tools.jar"
    if target.is_symlink():
        return ToolCheck("tlc-acquire", "failed", (), None, diagnostic="TLC cache refuses symlinks")
    with tempfile.TemporaryDirectory(prefix="template-tlc-acquire-", dir=target.parent) as directory:
        temporary = Path(directory) / "tla2tools.jar"
        check = _run(
            "tlc-acquire",
            [
                "curl",
                "--fail",
                "--location",
                "--proto",
                "=https",
                "--proto-redir",
                "=https",
                "--connect-timeout",
                "15",
                "--max-time",
                str(max(1, int(deadline - time.monotonic()))),
                "--output",
                str(temporary),
                TLC_URL,
            ],
            root,
            deadline,
        )
        # Acquisition is an HTTP byte transfer, not a model check.
        if check.exit_code != 0 or check.status == "timed_out":
            return ToolCheck(
                check.name,
                "timed_out" if check.status == "timed_out" else "blocked",
                check.argv,
                check.exit_code,
                check.stdout,
                check.stderr,
                check.diagnostic,
            )
        content = _jar_snapshot(temporary, deadline)
        if len(content) != TLC_BYTES:
            return ToolCheck(
                check.name,
                "failed",
                check.argv,
                check.exit_code,
                diagnostic=f"pinned TLC byte length mismatch: expected {TLC_BYTES}, got {len(content)}",
            )
        if hashlib.sha256(content).hexdigest() != TLC_SHA256:
            return ToolCheck(check.name, "failed", check.argv, check.exit_code, diagnostic="pinned TLC SHA256 mismatch")
        os.replace(temporary, target)
        return ToolCheck(check.name, "passed", check.argv, check.exit_code)


def _selected_jar(root: Path) -> Path:
    """Select a local cache or an explicit prepared external regular-file input."""
    local = root / "formal" / "tla" / "tla2tools.jar"
    if local.exists() or local.is_symlink():
        return local
    provider = os.environ.get("TEMPLATE_FORMAL_TLC_JAR")
    if not provider:
        return local
    selected = Path(provider)
    if not selected.is_absolute():
        raise ValueError("prepared external TLC provider must be an absolute path")
    return selected


def run_formal_tools(root: Path, *, timeout: float = 300, acquire: bool = False) -> dict[str, object]:
    """Run all declared models with stable pins, total budget and final custody."""
    if not math.isfinite(timeout) or isinstance(timeout, bool) or not 0 < timeout <= 600:
        raise ValueError("formal tool timeout must be finite, positive and at most600 seconds")
    deadline = time.monotonic() + timeout
    root = root.absolute()
    snapshot = _source_bytes(root, deadline)
    _pins(snapshot)
    with tempfile.TemporaryDirectory(prefix="template-formal-inputs-") as directory:
        frozen = Path(directory).resolve()
        declared = {
            path: content for path, content in snapshot.items() if path.startswith(("formal/lean/", "formal/tla/"))
        }
        materialize(declared, frozen)
        receipt = _execute_formal_tools(root, frozen, snapshot, deadline, timeout, acquire)
    if time.monotonic() >= deadline:
        if receipt["status"] == "passed":
            receipt["status"] = "timed_out"
        checks = receipt["checks"]
        assert isinstance(checks, list)
        checks.append(
            asdict(
                ToolCheck(
                    "private-input-cleanup",
                    "timed_out",
                    (),
                    None,
                    diagnostic="total deadline exhausted after private input cleanup",
                )
            )
        )
    return receipt


def _execute_formal_tools(
    root: Path, frozen: Path, snapshot: dict[str, bytes], deadline: float, timeout: float, acquire: bool
) -> dict[str, object]:
    """Run tools only on the frozen admitted declarations and model bytes."""
    before = {path: hashlib.sha256(content).hexdigest() for path, content in snapshot.items()}
    checks = []
    elan = shutil.which("elan")
    lean = frozen / "formal" / "lean"
    if elan is None:
        checks.append(ToolCheck("lean-build", "blocked", (), None, diagnostic="elan is not installed"))
    else:
        probe = _run("lean-version", [elan, "run", LEAN_TOOLCHAIN, "lean", "--version"], lean, deadline)
        if acquire and probe.status == "failed":
            checks.append(_run("lean-acquire", [elan, "toolchain", "install", LEAN_TOOLCHAIN], lean, deadline))
            probe = _run("lean-version", [elan, "run", LEAN_TOOLCHAIN, "lean", "--version"], lean, deadline)
        if probe.status != "passed" or "version 4.28.0" not in probe.stdout:
            checks.append(
                ToolCheck(
                    "lean-build",
                    "timed_out" if probe.status == "timed_out" else "blocked",
                    probe.argv,
                    probe.exit_code,
                    probe.stdout,
                    probe.stderr,
                    "pinned Lean4.28.0 is unavailable",
                )
            )
        else:
            checks.append(probe)
            # Force elaboration rather than reusing an old Lake build log.
            checks.append(
                _run(
                    "lean-build",
                    [elan, "run", LEAN_TOOLCHAIN, "lake", "env", "lean", "AntProtocol.lean"],
                    lean,
                    deadline,
                )
            )
    tla = frozen / "formal" / "tla"
    jar = _selected_jar(root)
    java = shutil.which(os.environ.get("FORMAL_JAVA_BIN", "java"))
    if java:
        java_probe = _run("java-version", [java, "-version"], tla, deadline)
        checks.append(
            java_probe
            if java_probe.status in {"passed", "timed_out"}
            else ToolCheck(
                java_probe.name,
                "blocked",
                java_probe.argv,
                java_probe.exit_code,
                java_probe.stdout,
                java_probe.stderr,
                "selected Java runtime is unavailable",
            )
        )
        if java_probe.status != "passed":
            java = None
    if jar == root / "formal" / "tla" / "tla2tools.jar" and not jar.is_file() and not jar.is_symlink() and acquire:
        checks.append(_acquire_jar(root, deadline))
    jar_timed_out = False
    try:
        jar_bytes = _jar_snapshot(jar, deadline)
        jar_valid = len(jar_bytes) == TLC_BYTES and hashlib.sha256(jar_bytes).hexdigest() == TLC_SHA256
    except TimeoutError:
        jar_bytes, jar_valid, jar_timed_out = b"", False, True
    except (OSError, ValueError):
        jar_bytes, jar_valid = b"", False
    if jar_timed_out:
        checks.append(
            ToolCheck(
                "tlc", "timed_out", (), None, diagnostic="total deadline exhausted before verified TLC input admission"
            )
        )
    elif not java or not jar_valid:
        corrupt_cache = jar.is_symlink() or (jar.exists() and not jar_valid)
        checks.append(
            ToolCheck(
                "tlc",
                "failed" if corrupt_cache else "blocked",
                (),
                None,
                diagnostic="Java or the exact verified TLC jar is unavailable",
            )
        )
    else:
        project_id = hashlib.sha256(str(root).encode()).hexdigest()[:12]
        with tempfile.TemporaryDirectory(prefix=f"template-tlc-verified-{project_id}-") as directory:
            frozen_jar = Path(directory) / "tla2tools.jar"
            frozen_jar.write_bytes(jar_bytes)
            frozen_jar.chmod(0o400)
            for model in ("AntProtocol", "AntProtocolFaulty", "AntProtocolFaultyNegControl"):
                with tempfile.TemporaryDirectory(prefix="template-tlc-state-") as states:
                    check = _run(
                        "tlc-" + model,
                        [
                            java,
                            "-XX:+UseSerialGC",
                            "-jar",
                            str(frozen_jar),
                            "-noGenerateSpecTE",
                            "-workers",
                            "1",
                            "-metadir",
                            states,
                            "-config",
                            model + ".cfg",
                            model + ".tla",
                        ],
                        tla,
                        deadline,
                        violation=model.endswith("NegControl"),
                    )
                    checks.append(replace(check, consumed_tlc_sha256=TLC_SHA256 if check.exit_code is not None else ""))
    for index, check in enumerate(checks):
        prefix = (
            "formal/lean/"
            if check.name == "lean-build"
            else "formal/tla/"
            if check.name.startswith("tlc-AntProtocol")
            else ""
        )
        if prefix and check.exit_code is not None:
            checks[index] = replace(
                check, consumed_source_sha256={path: value for path, value in before.items() if path.startswith(prefix)}
            )
    custody_timed_out = False
    try:
        after = _source_bytes(root, deadline)
        unchanged = snapshot == after
    except TimeoutError:
        unchanged = False
        custody_timed_out = True
    except (OSError, ValueError) as error:
        unchanged = False
        checks.append(ToolCheck("final-custody", "failed", (), None, diagnostic=str(error)))
    if jar_valid:
        try:
            unchanged = unchanged and _jar_snapshot(jar, deadline) == jar_bytes
        except TimeoutError:
            unchanged = False
            custody_timed_out = True
        except (OSError, ValueError):
            unchanged = False
    if custody_timed_out or time.monotonic() >= deadline:
        checks.append(
            ToolCheck(
                "final-custody",
                "timed_out",
                (),
                None,
                diagnostic="final source/pin custody exhausted the total deadline",
            )
        )
    statuses = {check.status for check in checks}
    status = (
        "failed"
        if (not unchanged and not custody_timed_out) or "failed" in statuses
        else "timed_out"
        if "timed_out" in statuses
        else "blocked"
        if "blocked" in statuses
        else "passed"
    )
    return {
        "schema_version": "template-formal/tool-acceptance/1",
        "status": status,
        "execution_kind": "actual",
        "capabilities": ["lean", "tlc"],
        "paid": False,
        "timeout_seconds": timeout,
        "lean_toolchain": LEAN_TOOLCHAIN,
        "tlc_sha256": TLC_SHA256,
        "source_unchanged": unchanged,
        "source_sha256": before,
        "checks": [asdict(check) for check in checks],
    }


def main(argv: list[str] | None = None) -> int:
    """Expose the canonical wrapper with honest failure and blocker exits."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument("--acquire", action="store_true")
    parser.add_argument("--receipt", type=Path)
    arguments = parser.parse_args(argv)
    try:
        receipt = run_formal_tools(arguments.project_root, timeout=arguments.timeout, acquire=arguments.acquire)
    except TimeoutError as error:
        print(f"formal acceptance timed out: {error}")
        return 124
    except (OSError, ValueError) as error:
        print(f"formal acceptance: {error}")
        return 2
    output = json.dumps(receipt, indent=2, sort_keys=True)
    if arguments.receipt:
        arguments.receipt.parent.mkdir(parents=True, exist_ok=True)
        arguments.receipt.write_text(output + "\n")
    print(output)
    return {"passed": 0, "failed": 1, "blocked": 75, "timed_out": 124}[str(receipt["status"])]


if __name__ == "__main__":
    raise SystemExit(main())
