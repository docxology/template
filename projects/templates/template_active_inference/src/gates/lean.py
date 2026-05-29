"""Lean toolchain validation helpers."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

# `#print axioms` permits only the standard, sound Lean kernel axioms. Anything
# else -- most importantly `sorryAx` (from `sorry`) or `Lean.ofReduceBool` (from
# `native_decide`) -- means the proof is not closed by the kernel alone.
_AXIOM_WHITELIST = frozenset({"propext", "Classical.choice", "Quot.sound"})

_DEFAULT_AUDITED_DECLS = ("TemplateActiveInference.sophisticated_requires_horizon",)


def lean_project_present(project_root: Path) -> bool:
    """True when this project ships a Lake root (``lean/lakefile.lean``)."""
    return (project_root.resolve() / "lean" / "lakefile.lean").is_file()


def build_lean(project_root: Path) -> tuple[int, str]:
    """Build the Lean package when present; skip cleanly when absent."""
    if not lean_project_present(project_root):
        return 0, "lean project absent -- skipped"
    lean_dir = project_root.resolve() / "lean"
    proc = subprocess.run(
        ["lake", "build"],
        cwd=lean_dir,
        capture_output=True,
        text=True,
    )
    output = proc.stdout + proc.stderr
    if proc.returncode != 0:
        return proc.returncode, output
    return 0, output


def lean_axioms_clean(
    project_root: Path,
    declarations: tuple[str, ...] = _DEFAULT_AUDITED_DECLS,
) -> tuple[bool, str]:
    """Audit declarations with ``#print axioms``; True iff only whitelisted axioms appear.

    Catches what an exit-code-only ``lake build`` and a ``\\bsorry\\b`` text scan miss:
    ``sorryAx`` (from ``sorry``) and ``Lean.ofReduceBool`` (from ``native_decide``)
    surface here as non-whitelisted axioms even though the build exits 0. The boundary
    modules are self-contained (no imports), so we elaborate their concatenated source
    directly -- robust to a vacuous ``lake build`` that emits no oleans. Skips cleanly
    (returns ``True``) when the Lean project is absent.
    """
    if not lean_project_present(project_root):
        return True, "lean project absent -- skipped"
    lean_dir = project_root.resolve() / "lean"
    module_dir = lean_dir / "TemplateActiveInference"
    sources: list[str] = []
    for path in sorted(module_dir.glob("*.lean")):
        text = path.read_text(encoding="utf-8")
        sources.extend(
            line for line in text.splitlines() if not line.lstrip().startswith("import TemplateActiveInference")
        )
    body = "\n".join(sources) + "\n" + "\n".join(f"#print axioms {d}" for d in declarations) + "\n"

    checker = lean_dir / "_AxiomCheck.lean"
    try:
        checker.write_text(body, encoding="utf-8")
        proc = subprocess.run(
            ["lake", "env", "lean", str(checker)],
            cwd=lean_dir,
            capture_output=True,
            text=True,
        )
    finally:
        checker.unlink(missing_ok=True)

    output = proc.stdout + proc.stderr
    if proc.returncode != 0:
        return False, f"#print axioms run failed:\n{output}"
    if "sorryAx" in output:
        return False, f"declaration depends on sorryAx (unproved):\n{output}"

    found: set[str] = set()
    for match in re.finditer(r"depends on axioms:\s*\[([^\]]*)\]", output):
        found.update(token.strip() for token in match.group(1).split(",") if token.strip())
    offending = sorted(found - _AXIOM_WHITELIST)
    if offending:
        return False, f"non-whitelisted Lean axioms {offending} in {declarations}:\n{output}"
    return True, output or "no non-whitelisted axioms"
