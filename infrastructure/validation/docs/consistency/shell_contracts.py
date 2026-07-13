"""Shell command convention and bootstrap contract checks."""

from __future__ import annotations

import re
from pathlib import Path

from infrastructure.validation.docs.consistency._shared import (
    Inconsistency,
    SHELL_NOQA_RE,
    blank_fences,
    iter_long_lived_docs,
    line_has_noqa,
    read_markdown,
)

_SHELL_FENCE_RE = re.compile(
    r"^[ \t]*(?P<fence>`{3,}|~{3,})[ \t]*(?P<lang>[A-Za-z0-9_+-]*)[ \t]*\n"
    r"(?P<body>.*?)\n[ \t]*(?P=fence)[ \t]*$",
    re.MULTILINE | re.DOTALL,
)
_SHELL_LANGS: frozenset[str] = frozenset({"bash", "sh", "shell", "console", "zsh"})
_BARE_CMD_RE = re.compile(r"^\s*(?:\$\s+)?(?P<cmd>pytest|python3)(?:\s|$)")
_UV_RUN_PYTHON3_RE = re.compile(r"^\s*(?:\$\s+)?uv\s+run\s+python3(?:\s|$)")
_UVX_RUFF_RE = re.compile(r"\buvx\s+ruff(?:\s|$)")

_EXPORT_PIPELINE_MODE_RE = re.compile(r"\bexport\s+PIPELINE_MODE\b", re.IGNORECASE)
_RUNSH_EXPORTS_PIPELINE_MODE_RE = re.compile(
    r"run\.sh.*PIPELINE_MODE\s*=",
    re.IGNORECASE,
)
_DETERMINISTIC_SHELL_STRIP_RE = re.compile(
    r"secure_run\.sh",
    re.IGNORECASE,
)
_DETERMINISTIC_SHELL_STRIP_ACTION_RE = re.compile(
    r"(strip|stripped|parsed\s+(only\s+)?by\s+(the\s+)?shell|shell\s+(strip|pars))",
    re.IGNORECASE,
)
_DETERMINISTIC_MENTION_RE = re.compile(r"--deterministic|\bdeterministic\b", re.IGNORECASE)


def check_command_conventions(repo_root: Path) -> list[Inconsistency]:
    """Flag stale or unpinned repository commands in shell fences."""
    issues: list[Inconsistency] = []
    for md in iter_long_lived_docs(repo_root):
        raw = read_markdown(md)
        if raw is None:
            continue
        for fence in _SHELL_FENCE_RE.finditer(raw):
            if fence.group("lang").lower() not in _SHELL_LANGS:
                continue
            body_start_line = raw[: fence.start("body")].count("\n") + 1
            for offset, line in enumerate(fence.group("body").splitlines()):
                if _UVX_RUFF_RE.search(line) and not line_has_noqa(line) and not SHELL_NOQA_RE.search(line):
                    issues.append(
                        Inconsistency(
                            file=md,
                            line=body_start_line + offset,
                            category="command-convention",
                            detail=(
                                "uses unpinned `uvx ruff`; repository commands must use "
                                "`uv run ruff` so CI and local hooks share the locked version"
                            ),
                        )
                    )
                    continue
                if _UV_RUN_PYTHON3_RE.match(line) and not line_has_noqa(line) and not SHELL_NOQA_RE.search(line):
                    issues.append(
                        Inconsistency(
                            file=md,
                            line=body_start_line + offset,
                            category="command-convention",
                            detail=(
                                "uses `uv run python3`; repo command examples should use "
                                "`uv run python` so the project-managed interpreter is selected"
                            ),
                        )
                    )
                    continue
                m = _BARE_CMD_RE.match(line)
                if not m or "uv run" in line or line_has_noqa(line) or SHELL_NOQA_RE.search(line):
                    continue
                issues.append(
                    Inconsistency(
                        file=md,
                        line=body_start_line + offset,
                        category="command-convention",
                        detail=(
                            f"command-line `{m.group('cmd')}` without `uv run` — "
                            "COUNTS.md mandates `uv run` (append "
                            "`# noqa: docs-lint` to allow a deliberate counter-example)"
                        ),
                    )
                )
    return issues


def check_stale_shell_contracts(repo_root: Path) -> list[Inconsistency]:
    """Flag stale bash-orchestration claims superseded by ``shell_bootstrap.sh`` + Python CLI."""
    issues: list[Inconsistency] = []
    for md in iter_long_lived_docs(repo_root):
        raw = read_markdown(md)
        if raw is None:
            continue
        text = blank_fences(raw)
        for line_no, raw_line in enumerate(text.splitlines(), start=1):
            if line_has_noqa(raw_line):
                continue
            if _EXPORT_PIPELINE_MODE_RE.search(raw_line):
                issues.append(
                    Inconsistency(
                        file=md,
                        line=line_no,
                        category="shell-contract",
                        detail=(
                            "documents `export PIPELINE_MODE` — run.sh keeps PIPELINE_MODE "
                            "bash-local and does not export it; orchestration lives in "
                            "infrastructure.orchestration"
                        ),
                    )
                )
                continue
            if _RUNSH_EXPORTS_PIPELINE_MODE_RE.search(raw_line) and "not export" not in raw_line.lower():
                issues.append(
                    Inconsistency(
                        file=md,
                        line=line_no,
                        category="shell-contract",
                        detail=(
                            "implies run.sh exports PIPELINE_MODE for downstream tools — "
                            "it is a bash-local variable only"
                        ),
                    )
                )
                continue
            if (
                _DETERMINISTIC_SHELL_STRIP_RE.search(raw_line)
                and _DETERMINISTIC_MENTION_RE.search(raw_line)
                and _DETERMINISTIC_SHELL_STRIP_ACTION_RE.search(raw_line)
                and "not strip" not in raw_line.lower()
                and "does not strip" not in raw_line.lower()
                and "subcommand" not in raw_line.lower()
            ):
                issues.append(
                    Inconsistency(
                        file=md,
                        line=line_no,
                        category="shell-contract",
                        detail=(
                            "claims secure_run.sh strips or parses --deterministic — "
                            "Python `secure` subcommand owns the flag "
                            "(infrastructure.orchestration.cli)"
                        ),
                    )
                )
    return issues
