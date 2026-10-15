"""Pinned, bounded Lean builds and complete kernel-axiom audits."""

from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import tempfile
import time
from pathlib import Path

from orchestration.portable_execution import build_bounded_env, run_bounded_subprocess
from orchestration.portable_sources import materialize, snapshot_tree

_AXIOM_WHITELIST = frozenset({"propext", "Classical.choice", "Quot.sound"})
_TOOLCHAIN = "leanprover/lean4:v4.35.0"
_VERSION = _TOOLCHAIN.split(":v", 1)[1]
_DEFAULT_AUDITED_DECLS = (
    "TemplateActiveInference.sophisticated_requires_horizon",
    "TemplateActiveInference.efe_additive_identity_from_relations",
)


def lean_project_present(project_root: Path) -> bool:
    """True when the declared Lake root exists."""
    return (project_root.absolute() / "lean" / "lakefile.lean").is_file()


def _source_snapshot(lean: Path, deadline: float | None = None) -> dict[Path, bytes]:
    """Capture exact declared pins and all Lean implementation sources once."""
    admitted = snapshot_tree(
        lean,
        deadline=deadline if deadline is not None else time.monotonic() + 30,
        exclude=lambda parts: parts[0] == ".lake",
    )
    required = {"lean-toolchain", "lake-manifest.json", "lakefile.lean"}
    if not required <= admitted.keys():
        raise ValueError("Lean project declarations are missing")
    snapshot = {lean / name: content for name, content in admitted.items()}
    if snapshot[lean / "lean-toolchain"].decode().strip() != _TOOLCHAIN:
        raise ValueError(f"Lean toolchain differs from the exact source-owned {_VERSION} pin")
    manifest = json.loads(snapshot[lean / "lake-manifest.json"])
    if (
        not isinstance(manifest, dict)
        or manifest.get("packages") != []
        or manifest.get("name") != "TemplateActiveInference"
    ):
        raise ValueError("Lean manifest differs from the dependency-free project contract")
    return snapshot


def _deadline(timeout: float) -> float:
    """Start the total budget before any declared source admission."""
    if isinstance(timeout, bool) or not math.isfinite(timeout) or not 0 < timeout <= 600:
        raise ValueError("Lean timeout must be finite, positive and at most600 seconds")
    return time.monotonic() + timeout


def _execute(lean: Path, arguments: list[str], snapshot: dict[Path, bytes], deadline: float) -> tuple[int, str]:
    """Use a total deadline, forbid implicit acquisition, and recheck source bytes."""
    elan = shutil.which("elan")
    if elan is None:
        return 75, "blocked: elan is unavailable; install the declared toolchain explicitly"
    # `elan run` does not acquire unless its explicit `--install` flag is supplied.
    command = [elan, "run", _TOOLCHAIN]
    environment = build_bounded_env()
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        return 124, "total Lean deadline exhausted before tool launch"
    probe = run_bounded_subprocess(command + ["lean", "--version"], cwd=lean, env=environment, timeout=remaining)
    if probe.timed_out:
        return 124, probe.stdout + probe.stderr + probe.command_error
    if probe.returncode or re.search(rf"\bversion {re.escape(_VERSION)}(?:,|\))", probe.stdout) is None:
        return 75, f"blocked: exact Lean {_VERSION} unavailable\n" + probe.stdout + probe.stderr
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        return 124, "total Lean deadline exhausted"
    with tempfile.TemporaryDirectory(prefix="template-active-lean-inputs-") as directory:
        frozen = Path(directory).resolve()
        materialize({path.relative_to(lean).as_posix(): content for path, content in snapshot.items()}, frozen)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return 124, "total Lean deadline exhausted while freezing inputs"
        result = run_bounded_subprocess(command + arguments, cwd=frozen, env=environment, timeout=remaining)
    output = result.stdout + result.stderr + result.command_error
    try:
        if snapshot != _source_snapshot(lean, deadline):
            return 1, "Lean source/pins changed during verification\n" + output
    except TimeoutError as error:
        return 124, str(error) + "\n" + output
    except (OSError, ValueError) as error:
        return 1, f"Lean source/pins changed during verification: {error}\n" + output
    if time.monotonic() >= deadline:
        return 124, "total Lean deadline exhausted after child cleanup and source custody\n" + output
    if result.returncode == 0 and re.search(r"\bsorry\b|\bsorryAx\b", output):
        return 1, "Lean reported an unproved declaration\n" + output
    identity = hashlib.sha256(
        json.dumps(
            {
                path.relative_to(lean).as_posix(): hashlib.sha256(content).hexdigest()
                for path, content in sorted(snapshot.items())
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    if time.monotonic() >= deadline:
        return 124, "total Lean deadline exhausted after consumed-source identity\n" + output
    return result.returncode, f"consumed frozen Lean source SHA256 {identity}\n" + output


def build_lean(project_root: Path, *, timeout: float = 180) -> tuple[int, str]:
    """Build the exact installed toolchain; missing declarations/tools are blocked."""
    try:
        deadline = _deadline(timeout)
        lean = project_root.absolute() / "lean"
        if not (lean / "lakefile.lean").exists():
            return 75, "blocked: Lean project declarations are absent"
        snapshot = _source_snapshot(lean, deadline)
        return _execute(lean, ["lake", "build", "TemplateActiveInference"], snapshot, deadline)
    except TimeoutError as error:
        return 124, str(error)
    except (OSError, ValueError) as error:
        return 2, f"invalid Lean declaration: {error}"


def lean_axioms_clean(
    project_root: Path,
    declarations: tuple[str, ...] = _DEFAULT_AUDITED_DECLS,
    *,
    timeout: float = 180,
) -> tuple[bool, str]:
    """Require every requested declaration's actual audit with only kernel axioms."""
    if (
        not declarations
        or len(set(declarations)) != len(declarations)
        or any(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_'.]*", name) is None for name in declarations)
    ):
        return False, "invalid Lean audit declarations"
    try:
        deadline = _deadline(timeout)
        lean = project_root.absolute() / "lean"
        if not (lean / "lakefile.lean").exists():
            return False, "blocked: Lean project declarations are absent"
        snapshot = _source_snapshot(lean, deadline)
        sources = [
            content.decode()
            for path, content in sorted(snapshot.items())
            if path.parent == lean / "TemplateActiveInference" and path.suffix == ".lean"
        ]
        body = "\n".join(
            line
            for source in sources
            for line in source.splitlines()
            if not line.lstrip().startswith("import TemplateActiveInference")
        )
        body += "\n" + "\n".join(f"#print axioms {name}" for name in declarations) + "\n"
        with tempfile.TemporaryDirectory(prefix="template-active-axioms-") as directory:
            checker = Path(directory).resolve() / "AxiomCheck.lean"
            checker.write_text(body)
            code, output = _execute(lean, ["lake", "env", "lean", str(checker)], snapshot, deadline)
    except TimeoutError as error:
        return False, f"#print axioms run failed (exit124): {error}"
    except (OSError, ValueError) as error:
        return False, f"invalid Lean audit: {error}"
    if code:
        return False, f"#print axioms run failed (exit{code}):\n{output}"
    audited: set[str] = set()
    found: set[str] = set()
    for match in re.finditer(r"'([^']+)' (?:depends on axioms:\s*\[([^\]]*)\]|does not depend on any axioms)", output):
        audited.add(match.group(1))
        found.update(token.strip() for token in (match.group(2) or "").split(",") if token.strip())
    if not set(declarations) <= audited:
        return False, f"#print axioms omitted requested declarations:\n{output}"
    if found - _AXIOM_WHITELIST:
        return False, f"non-whitelisted Lean axioms {sorted(found - _AXIOM_WHITELIST)}:\n{output}"
    identity = hashlib.sha256(body.encode()).hexdigest()
    if time.monotonic() >= deadline:
        return (
            False,
            f"#print axioms run failed (exit124): total Lean deadline exhausted after axiom validation\n{output}",
        )
    return True, f"audited source SHA256 {identity}\n{output}"
