"""Stable output inventory scanning and Git-ignore evaluation."""

from __future__ import annotations

import os
import stat
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

_IGNORED_OUTPUT_PARTS = frozenset(
    {
        ".checkpoints",
        ".history",
        ".pipeline",
        "logs",
        "hitl",
        "snapshots",
        "__pycache__",
        "fulltext",
        "llm",
        "translations",
    }
)
_IGNORED_OUTPUT_FILENAMES = frozenset(
    {
        "artifact_manifest.json",
        "autoresearch_readiness.json",
        "autoresearch_readiness.md",
        "diagnostics.json",
        "evidence_registry.json",
        "evidence_registry_full.json",
        "output_statistics.json",
        "output_statistics.txt",
        "rendered_provenance.json",
        "snapshot_compare.json",
        "snapshot_compare.md",
        "validation_report.json",
        "validation_report.md",
    }
)
OutputInventoryMode = Literal["stable-shippable-output-v1", "stable-local-output-v1"]
_IGNORED_OUTPUT_SUFFIXES = frozenset({".aux", ".log", ".nav", ".snm", ".toc", ".vrb"})
STABLE_OUTPUT_INVENTORY_MODE: OutputInventoryMode = "stable-shippable-output-v1"
STABLE_LOCAL_OUTPUT_INVENTORY_MODE: OutputInventoryMode = "stable-local-output-v1"


@dataclass(frozen=True)
class StableOutputInventory:
    """Canonical stable files discovered below one output tree."""

    files: tuple[Path, ...]
    issues: tuple[str, ...] = ()
    mode: OutputInventoryMode = STABLE_OUTPUT_INVENTORY_MODE


@dataclass(frozen=True)
class _GitIgnoreEvaluation:
    """One batched Git-ignore query, including fail-closed error state."""

    matches: Mapping[Path, tuple[bytes, bytes, bytes]]
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


def parse_output_inventory_mode(value: object) -> OutputInventoryMode:
    """Parse a stable-output inventory mode without silently widening scope."""
    if value == STABLE_OUTPUT_INVENTORY_MODE:
        return STABLE_OUTPUT_INVENTORY_MODE
    if value == STABLE_LOCAL_OUTPUT_INVENTORY_MODE:
        return STABLE_LOCAL_OUTPUT_INVENTORY_MODE
    raise ValueError(f"unsupported stable output inventory mode: {value!r}")


def collect_stable_output_inventory(
    output_dir: Path,
    *,
    git_ignore_output_dir: Path | None = None,
    git_ignore_path_overrides: Mapping[Path, Path] | None = None,
    inventory_mode: OutputInventoryMode = STABLE_OUTPUT_INVENTORY_MODE,
) -> StableOutputInventory:
    """Collect stable output files using publication and local-output semantics.

    This is the single read-only inventory used by artifact manifests and by
    deterministic statistics. Runtime state, self-referential reports, build
    intermediates, and files below hidden paths are always excluded. Public
    exemplar outputs additionally honor Git ignores so every admitted artifact
    can ship in a fresh clone. An authorized standalone/private lifecycle caller
    may explicitly select ``stable-local-output-v1`` so valid local deliverables
    remain testable without being misrepresented as Git-shippable evidence.
    Shippable mode is always the default and is never relaxed by observing an
    ignored output path. Symlinks are reported as issues rather than silently
    followed. ``git_ignore_output_dir`` maps copied files back to the canonical
    project output tree for Git-ignore evaluation; ``git_ignore_path_overrides``
    records promotions such as Stage 5's copied root PDF whose canonical source
    lives under ``pdf/``.
    """
    output_dir = output_dir.absolute()
    if output_dir.is_symlink():
        raise ValueError(f"refusing to collect through symlink output directory: {output_dir}")
    ignore_output_dir = (git_ignore_output_dir or output_dir).absolute()
    if ignore_output_dir.is_symlink():
        raise ValueError(f"refusing to map Git ignores through symlink output directory: {ignore_output_dir}")
    project_dir = ignore_output_dir.parent
    inventory_mode = parse_output_inventory_mode(inventory_mode)
    files: list[Path] = []
    issues: list[str] = []
    if output_dir.exists():
        snapshot_paths = tuple(sorted(output_dir.rglob("*")))
        candidate_metadata: dict[Path, os.stat_result] = {}
        snapshot_symlinks: set[Path] = set()
        for path in snapshot_paths:
            try:
                metadata = path.lstat()
            except OSError:
                continue
            if stat.S_ISLNK(metadata.st_mode):
                snapshot_symlinks.add(path)
            elif stat.S_ISREG(metadata.st_mode):
                candidate_metadata[path] = metadata
        candidates = tuple(candidate_metadata)
        # Never record an artifact git will not ship — the manifest is committed
        # evidence, and a fresh clone would read the entry as drift. A copied
        # delivery mirror is itself normally ignored, so evaluate each copied
        # relative path at its canonical source-output location when supplied.
        overrides = dict(git_ignore_path_overrides or {})
        git_candidates: dict[Path, list[Path]] = {}
        for path in candidates:
            relative = path.relative_to(output_dir)
            source_relative = overrides.get(relative, relative)
            if source_relative.is_absolute() or ".." in source_relative.parts:
                raise ValueError(f"invalid Git-ignore path override: {relative} -> {source_relative}")
            git_candidates.setdefault(ignore_output_dir / source_relative, []).append(path)
        candidate_evaluation = _git_ignore_matches(tuple(git_candidates), project_dir)
        if not candidate_evaluation.ok and _git_worktree_marker(project_dir) is not None:
            issues.append(f"git ignore evaluation failed: {candidate_evaluation.error}")
            return StableOutputInventory(files=(), issues=tuple(issues), mode=inventory_mode)
        candidate_matches = candidate_evaluation.matches
        blanket_rules: set[tuple[bytes, bytes, bytes]] = set()
        if inventory_mode == STABLE_LOCAL_OUTPUT_INVENTORY_MODE:
            # Local mode bypasses only the caller-authorized packaging ignore
            # covering the complete output tree (including ``output/``,
            # ``output/*``, and ``output/**`` spellings). Project-specific
            # ignores remain authoritative whenever Git can distinguish them.
            probes = (
                ignore_output_dir / "__template_output_inventory_probe__.sentinel-a",
                ignore_output_dir / "__template_output_inventory_probe__" / "artifact.sentinel-b",
                ignore_output_dir / "__template_output_inventory_probe__" / "nested" / "leaf",
            )
            probe_evaluation = _git_ignore_matches(probes, project_dir)
            if not probe_evaluation.ok and _git_worktree_marker(project_dir) is not None:
                issues.append(f"git ignore evaluation failed: {probe_evaluation.error}")
                return StableOutputInventory(files=(), issues=tuple(issues), mode=inventory_mode)
            probe_matches = probe_evaluation.matches
            matched_rules = set(probe_matches.values())
            if len(probe_matches) == len(probes) and len(matched_rules) == 1:
                blanket_rules.update(matched_rules)
        ignored = {
            destination
            for path, rule in candidate_matches.items()
            if path in git_candidates and rule not in blanket_rules
            for destination in git_candidates[path]
        }
        if output_dir.is_symlink():
            raise ValueError(f"refusing to collect through symlink output directory: {output_dir}")
        if ignore_output_dir.is_symlink():
            raise ValueError(f"refusing to map Git ignores through symlink output directory: {ignore_output_dir}")
        symlinks = set(snapshot_symlinks)
        for path in snapshot_paths:
            symlink_component = _first_symlink_component(output_dir, path)
            if symlink_component is not None:
                symlinks.add(symlink_component)
        issues.extend(_symlink_issue(path, output_dir) for path in sorted(symlinks))
        for path in candidates:
            if _first_symlink_component(output_dir, path) is not None:
                continue
            try:
                current_metadata = path.lstat()
            except OSError:
                continue
            initial_metadata = candidate_metadata[path]
            if (
                not stat.S_ISREG(current_metadata.st_mode)
                or current_metadata.st_dev != initial_metadata.st_dev
                or current_metadata.st_ino != initial_metadata.st_ino
                or current_metadata.st_size != initial_metadata.st_size
                or current_metadata.st_mtime_ns != initial_metadata.st_mtime_ns
                or current_metadata.st_ctime_ns != initial_metadata.st_ctime_ns
            ):
                continue
            if _is_ignored_output(path, output_dir) or path in ignored:
                continue
            files.append(path)
    return StableOutputInventory(files=tuple(files), issues=tuple(dict.fromkeys(issues)), mode=inventory_mode)


def _symlink_issue(path: Path, output_dir: Path) -> str:
    try:
        displayed = path.relative_to(output_dir).as_posix()
    except ValueError:
        displayed = path.as_posix()
    return f"symlink artifact forbidden: {displayed}"


def _first_symlink_component(root: Path, target: Path) -> Path | None:
    current = root
    try:
        parts = target.relative_to(root).parts
    except ValueError:
        return target
    for part in parts:
        current = current / part
        if current.is_symlink():
            return current
    return None


def git_ignored_paths(paths: "Sequence[Path]", project_dir: Path) -> frozenset[Path]:
    """Return paths Git ignores, failing closed on worktree query errors.

    A committed artifact manifest is publication evidence, so it must only
    reference files that can actually ship. The static suffix list below cannot
    express path-scoped rules like ``output/slides/**/*.tex``, so it drifted from
    ``.gitignore`` and the committed manifest for ``template_code_project`` came
    to list 15 LaTeX intermediates (``.bbl``, ``.blg``, ``_combined_manuscript.tex``,
    ``references.bib``) that exist after a local render but are absent from any
    fresh clone. CI failed on all four Python versions and both platforms while
    the same tests passed locally, because locally those files were present.

    Asking git removes the second source of truth. One batched
    ``git check-ignore --stdin`` call covers the whole candidate set; when git is
    absent and the tree is genuinely not a repository (unit tests build trees
    under ``tmp_path``), this returns empty and the static lists still apply. A
    detected worktree with unavailable or malformed Git output returns every
    candidate, so callers cannot mislabel unevaluated files as shippable.
    """
    evaluation = _git_ignore_matches(paths, project_dir)
    if evaluation.ok:
        return frozenset(evaluation.matches)
    if _git_worktree_marker(project_dir) is not None:
        return frozenset(paths)
    return frozenset()


def _git_ignore_matches(
    paths: "Sequence[Path]",
    project_dir: Path,
    *,
    command: Sequence[str] = ("git",),
) -> _GitIgnoreEvaluation:
    """Return ignored paths with the exact Git rule that selected each path."""
    if not paths:
        return _GitIgnoreEvaluation(matches={})
    payload = b"\0".join(os.fsencode(path) for path in paths) + b"\0"
    try:
        proc = subprocess.run(  # noqa: S603 - fixed argv, no shell
            [*command, "-C", str(project_dir), "check-ignore", "-v", "-z", "--stdin"],
            input=payload,
            capture_output=True,
            check=False,
        )
    except OSError:
        return _GitIgnoreEvaluation(matches={}, error="git check-ignore unavailable")
    except ValueError:
        return _GitIgnoreEvaluation(matches={}, error="git check-ignore invocation invalid")
    # 0 = some paths ignored, 1 = none ignored; anything else means git could not
    # answer. The collector decides whether a genuine non-repository tree may
    # use static fallback or a detected worktree must fail closed.
    if proc.returncode not in {0, 1}:
        return _GitIgnoreEvaluation(
            matches={},
            error=f"git check-ignore exited with status {proc.returncode}",
        )
    fields = proc.stdout.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()
    if len(fields) % 4 != 0 or (proc.returncode == 0 and not fields) or (proc.returncode == 1 and fields):
        return _GitIgnoreEvaluation(matches={}, error="git check-ignore returned malformed output")
    matches: dict[Path, tuple[bytes, bytes, bytes]] = {}
    for index in range(0, len(fields), 4):
        source, line_number, pattern, raw_path = fields[index : index + 4]
        # Verbose check-ignore reports the final negation pattern for an
        # explicitly re-included path. Such a path is shippable and must not be
        # returned as ignored.
        if pattern.startswith(b"!"):
            continue
        matches[Path(os.fsdecode(raw_path))] = (source, line_number, pattern)
    return _GitIgnoreEvaluation(matches=matches)


def _git_worktree_marker(project_dir: Path) -> Path | None:
    """Return the nearest ancestor Git marker without invoking Git itself."""
    current = project_dir.absolute()
    for candidate in (current, *current.parents):
        marker = candidate / ".git"
        if marker.is_dir() or marker.is_file():
            return marker
    return None


def _is_ignored_output(path: Path, output_dir: Path) -> bool:
    return _is_ignored_output_relative(path.relative_to(output_dir))


def _is_ignored_output_relative(relative: Path) -> bool:
    """Return whether an output-relative path is outside stable evidence."""
    rel_parts = relative.parts
    # Hidden paths under output are local caches, atomic-write leftovers, or
    # workspace markers rather than publication evidence. Reject every hidden
    # component, not only a hidden leaf: ``data/.private-cache/token`` and
    # ``.git/config`` are just as non-public as ``.partial.png``.
    if any(part.startswith(".") for part in rel_parts):
        return True
    # These are renderer-owned build inputs/intermediates even when a private
    # project blanket-ignores output/ and therefore authorizes local mode.
    # Mirror the path-scoped public .gitignore rules without excluding authored
    # TeX or bibliography deliverables in unrelated output categories.
    category = rel_parts[0] if len(rel_parts) > 1 else "root"
    if category == "pdf" and (
        relative.name.startswith("_combined_manuscript.")
        or (relative.name.startswith("references") and relative.suffix == ".bib")
    ):
        return True
    if category == "slides" and relative.suffix in {
        ".aux",
        ".bbl",
        ".blg",
        ".log",
        ".nav",
        ".out",
        ".snm",
        ".tex",
        ".toc",
        ".vrb",
    }:
        return True
    if relative == Path("fulltext/fulltext_inventory.json"):
        return False
    return (
        any(part in _IGNORED_OUTPUT_PARTS for part in rel_parts)
        or relative.name in _IGNORED_OUTPUT_FILENAMES
        or relative.suffix in _IGNORED_OUTPUT_SUFFIXES
    )
