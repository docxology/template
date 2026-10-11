"""Filesystem-only identities for effective native executable selections."""

from __future__ import annotations
import hashlib
import os
import re
import shutil
import sys
import tomllib
from collections.abc import Callable, Mapping
from pathlib import Path
from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.core.pipeline.fingerprint_files import anchored_parent

Identity = Callable[[Path], object]
_NAMES = (
    "python",
    "pandoc",
    "xelatex",
    "lualatex",
    "pdflatex",
    "pdftoppm",
    "mmdc",
    "java",
    "lean",
    "lake",
    "elan",
    "ollama",
    "docker",
)
_OVERRIDES = {
    "FORMAL_JAVA_BIN": "formal_java",
    "PANDOC_PATH": "configured_pandoc",
    "LATEX_COMPILER": "configured_latex",
}


def collect_tool_bindings(
    project_dir: Path | None, environment: Mapping[str, str], identify: Identity
) -> dict[str, object]:
    """Bind executable bytes and known launcher backends without running them."""
    rows: dict[str, object] = {}
    unresolved: set[str] = set()

    def bind(label: str, candidate: Path) -> bool:
        selected = candidate.absolute()
        target = selected.resolve()
        if not target.exists():
            rows[label] = "unavailable"
            return False
        rows[label] = {"path": str(target), "content": identify(target)}
        if selected.resolve() != target:
            raise ValueError("Tool selection changed during fingerprint observation")
        return True

    def executable(label: str, command: str) -> Path | None:
        if os.sep in command and not Path(command).is_absolute():
            unresolved.add(label + ".relative-selection")
        selected = shutil.which(command, path=environment.get("PATH", os.defpath))
        if not selected:
            rows[label] = "unavailable"
            return None
        candidate = Path(selected)
        if not candidate.is_absolute():
            unresolved.add(label + ".relative-path")
        bind(label, candidate)
        return candidate.resolve()

    chosen = {name: executable(name, sys.executable if name == "python" else name) for name in _NAMES}
    for key, label in _OVERRIDES.items():
        if environment.get(key):
            chosen[label] = executable(label, environment[key])
    if project_dir is not None:
        from infrastructure.core.runtime.python_binding import AnalysisRuntimeUnavailable, analysis_runtime_binding

        try:
            rows["analysis_runtime"] = analysis_runtime_binding(project_dir)
        except AnalysisRuntimeUnavailable:
            rows["analysis_runtime"] = "unavailable"
            unresolved.add("analysis.runtime")
    java_launchers = {label for label in ("java", "formal_java") if chosen.get(label) == Path("/usr/bin/java")}
    if sys.platform == "darwin" and java_launchers:
        java_home = environment.get("JAVA_HOME")
        if not java_home or not Path(java_home).is_absolute():
            unresolved.update(label + ".launcher" for label in java_launchers)
        else:
            runtime = Path(java_home).resolve()
            present = {
                leaf: bind("java_runtime_" + leaf.replace("/", "_"), runtime / leaf)
                for leaf in (
                    "bin/java",
                    "release",
                    "lib/libjli.dylib",
                    "lib/jli/libjli.dylib",
                    "lib/server/libjvm.dylib",
                    "lib/modules",
                )
            }
            if (
                not present["bin/java"]
                or not (present["lib/libjli.dylib"] or present["lib/jli/libjli.dylib"])
                or not present["lib/server/libjvm.dylib"]
            ):
                unresolved.update(label + ".launcher" for label in java_launchers)
            if Path(java_home).resolve() != runtime:
                raise ValueError("Java runtime selection changed during fingerprint observation")
    if chosen.get("elan") is not None or (chosen.get("lean") is not None and "elan" in str(chosen["lean"])):
        nominated_home = Path(
            environment.get("ELAN_HOME", str(Path(environment.get("HOME", str(Path.home()))) / ".elan"))
        )
        if not nominated_home.is_absolute():
            unresolved.add("lean.relative-home")
        original_home = nominated_home.absolute()
        home = original_home.resolve()
        pins: set[str] = set()
        if project_dir is not None:
            for relative in ("lean/lean-toolchain", "formal/lean/lean-toolchain"):
                path = project_dir / relative
                # A missing project or pin directory is an explicit absent pin,
                # matching the elan settings observation below; symlinked or
                # substituted ancestors are still refused by anchored_parent.
                with anchored_parent(path) as parent:
                    if parent is None:
                        continue
                    try:
                        content = read_bytes_confined(project_dir, path, max_bytes=4096)
                    except FileNotFoundError:
                        continue
                rows["lean_pin_" + relative.replace("/", "_")] = hashlib.sha256(content).hexdigest()
                pins.add(content.decode().strip())
        settings = home / "settings.toml"
        settings_content: bytes | None
        with anchored_parent(settings) as parent:
            if parent is None:
                settings_content = None
            else:
                try:
                    settings_content = read_bytes_confined(home, settings, max_bytes=65536)
                except FileNotFoundError:
                    settings_content = None
        rows["elan_settings"] = (
            "unavailable" if settings_content is None else hashlib.sha256(settings_content).hexdigest()
        )
        if settings_content is not None:
            try:
                parsed = tomllib.loads(settings_content.decode())
                if isinstance(parsed.get("default_toolchain"), str):
                    pins.add(parsed["default_toolchain"])
                overrides = parsed.get("overrides", {})
                if isinstance(overrides, dict) and all(isinstance(value, str) for value in overrides.values()):
                    pins.update(overrides.values())
                else:
                    unresolved.add("lean.selection")
            except (UnicodeError, tomllib.TOMLDecodeError):
                unresolved.add("lean.selection")
        if environment.get("ELAN_TOOLCHAIN"):
            pins.add(environment["ELAN_TOOLCHAIN"])
        if not pins:
            unresolved.add("lean.selection")
        for pin in sorted(pins):
            if re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+:[A-Za-z0-9_.-]+", pin):
                names = (pin.replace("/", "--").replace(":", "---"),)
            elif re.fullmatch(r"(?:stable|nightly(?:-[0-9-]+)?|v?[0-9]+(?:\.[0-9]+){1,2}(?:-[A-Za-z0-9_.-]+)?)", pin):
                names = ("leanprover--lean4---" + pin,)
            elif re.fullmatch(r"[A-Za-z0-9_.-]+", pin) and pin not in {".", ".."}:
                names = (pin,)
            else:
                unresolved.add("lean.selection")
                continue
            key = hashlib.sha256(pin.encode()).hexdigest()[:16]
            for name in names:
                for binary in ("lean", "lake"):
                    bind("elan_backend_" + key + "_" + binary, home / "toolchains" / name / "bin" / binary)
        if original_home.resolve() != home:
            raise ValueError("Elan home selection changed during fingerprint observation")
    rows["unresolved_backends"] = sorted(unresolved)
    return rows
