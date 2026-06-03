"""Resolve snake_case {{token}} placeholders into output/manuscript/."""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

_TOKEN_RE = re.compile(r"\{\{([a-z][a-z0-9_]*)(?::\.(\d+)f)?\}\}")
_SINGLE_BRACE_TOKEN_RE = re.compile(r"(?<!\{)\{([a-z][a-z0-9_]*)\}(?!\})")
_LATEX_FENCE_RE = re.compile(r"```\{=latex\}.*?```", re.DOTALL)

EXCLUDED_DOC_FILENAMES: frozenset[str] = frozenset({"AGENTS.md", "README.md", "SYNTAX.md", "preamble.md"})


def format_variables(raw: dict[str, Any]) -> dict[str, str]:
    """Stringify variable values for manuscript substitution."""
    formatted: dict[str, str] = {}
    for key, value in raw.items():
        if isinstance(value, float):
            formatted[key] = f"{value:.4f}".rstrip("0").rstrip(".")
        elif isinstance(value, bool):
            formatted[key] = str(value).lower()
        elif value is None:
            formatted[key] = ""
        else:
            formatted[key] = str(value)
    entropy = raw.get("si_tmaze_mean_belief_entropy")
    if isinstance(entropy, (int, float)):
        formatted["si_tmaze_mean_belief_entropy_formatted"] = f"{float(entropy):.4f}"
    return formatted


def collect_manuscript_tokens(text: str) -> list[str]:
    """Return token names referenced as {{name}} or {{name:.4f}} in markdown."""
    return [match.group(1) for match in _TOKEN_RE.finditer(text)]


def collect_single_brace_tokens(text: str) -> list[str]:
    """Return snake_case names in single-brace {name} form (likely typos)."""
    return [match.group(1) for match in _SINGLE_BRACE_TOKEN_RE.finditer(text)]


def collect_malformed_token_names(text: str) -> list[str]:
    """Return token-like names that are not valid double-brace placeholders."""
    stripped = _LATEX_FENCE_RE.sub("", text)
    return sorted(set(collect_single_brace_tokens(stripped)))


def collect_tokens_in_directory(manuscript_dir: Path) -> set[str]:
    tokens: set[str] = set()
    for md_file in sorted(manuscript_dir.glob("*.md")):
        if md_file.name in EXCLUDED_DOC_FILENAMES:
            continue
        tokens.update(collect_manuscript_tokens(md_file.read_text(encoding="utf-8")))
    return tokens


def validate_manuscript_tokens(
    manuscript_dir: Path,
    variable_keys: set[str],
) -> list[str]:
    """Return sorted unknown token names referenced under manuscript_dir."""
    unknown = collect_tokens_in_directory(manuscript_dir) - variable_keys
    return sorted(unknown)


def substitute_snake_case_tokens(
    text: str,
    variables: dict[str, str],
) -> tuple[str, list[str]]:
    unresolved: list[str] = []

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        precision = match.group(2)
        if key not in variables:
            unresolved.append(key)
            return match.group(0)
        value = variables[key]
        if precision is not None:
            try:
                return f"{float(value):.{int(precision)}f}"
            except ValueError:
                return value
        return value

    return _TOKEN_RE.sub(_replace, text), unresolved


def write_resolved_manuscript(project_root: Path, variables: dict[str, Any]) -> Path:
    """Write token-substituted markdown copies to output/manuscript/."""
    root = project_root.resolve()
    manuscript_dir = root / "manuscript"
    out_dir = root / "output" / "manuscript"
    out_dir.mkdir(parents=True, exist_ok=True)
    string_vars = format_variables(variables)
    all_unresolved: list[str] = []

    for stale in list(out_dir.glob("*.md")) + list(out_dir.glob("*.bib")):
        stale.unlink(missing_ok=True)
    for stale_name in ("config.yaml", "preamble.md"):
        stale = out_dir / stale_name
        if stale.exists():
            stale.unlink(missing_ok=True)

    for md_file in sorted(manuscript_dir.glob("*.md")):
        if md_file.name in EXCLUDED_DOC_FILENAMES:
            continue
        text = md_file.read_text(encoding="utf-8")
        malformed = collect_malformed_token_names(text)
        if malformed:
            raise ValueError(f"malformed single-brace tokens in {md_file.name}: {', '.join(malformed)}")
        resolved, unresolved = substitute_snake_case_tokens(text, string_vars)
        all_unresolved.extend(unresolved)
        out_dir.joinpath(md_file.name).write_text(resolved, encoding="utf-8")

    for aux in ("config.yaml", "preamble.md"):
        src = manuscript_dir / aux
        if src.is_file():
            shutil.copy2(src, out_dir / aux)

    for bib in sorted(manuscript_dir.glob("*.bib")):
        shutil.copy2(bib, out_dir / bib.name)

    if all_unresolved:
        unique = sorted(set(all_unresolved))
        raise ValueError(f"unresolved manuscript tokens: {', '.join(unique)}")

    return out_dir
