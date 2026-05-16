"""Mermaid block discovery and validation.

Sweeps Markdown files for fenced ```mermaid blocks and validates each one with the
real `mmdc` (mermaid-cli) binary. There is no graceful skip when `mmdc` is missing
in CI: this module raises a clear :class:`RuntimeError` so the gate fails loudly.

For local dev convenience, callers can ``pytest.importorskip``-style probe via
:func:`mmdc_available`.

Public API:
    - :class:`MermaidBlock`
    - :class:`ValidationFailure`
    - :func:`find_mermaid_blocks`
    - :func:`validate_blocks`
    - :func:`mmdc_available`
"""

import json
import os
import re
import shutil
import subprocess  # nosec B404 — required for real mmdc invocation; no shell, fixed args
import tempfile
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.validation.docs.scan_scope import iter_markdown_files

logger = get_logger(__name__)

# Match fenced mermaid blocks. Captures the body. Multiline. Non-greedy.
_MERMAID_FENCE = re.compile(
    r"^(?P<fence>`{3,}|~{3,})mermaid[^\n]*\n(?P<body>.*?)\n(?P=fence)",
    re.MULTILINE | re.DOTALL,
)

# Heuristic: first non-empty, non-comment line tells us the diagram kind.
_KIND_RE = re.compile(r"^\s*(?P<kind>[A-Za-z][A-Za-z0-9_-]*)")


@dataclass(frozen=True)
class MermaidBlock:
    """A single fenced mermaid code block found in a Markdown file."""

    file: Path
    line: int  # 1-indexed line of the opening fence
    kind: str  # e.g. "flowchart", "graph", "sequenceDiagram", "stateDiagram-v2"
    body: str  # raw mermaid source between the fences (no trailing newline)


@dataclass(frozen=True)
class ValidationFailure:
    """Represents a mermaid block that failed `mmdc` rendering."""

    block: MermaidBlock
    stderr: str
    returncode: int

    def format(self) -> str:
        """Return a single-line human-readable summary."""
        rel = self.block.file
        return (
            f"{rel}:{self.block.line}: mermaid {self.block.kind!r} failed "
            f"(exit {self.returncode}): {self.stderr.strip().splitlines()[0] if self.stderr.strip() else 'no stderr'}"
        )


def mmdc_available(mmdc_path: str | None = None) -> bool:
    """Return True iff a `mmdc` binary appears to be on PATH (or at *mmdc_path*)."""
    candidate = mmdc_path or shutil.which("mmdc")
    return bool(candidate and Path(candidate).exists())


def _iter_markdown_files(roots: Iterable[Path]) -> list[Path]:
    """Walk *roots* using the shared documentation scan scope."""
    return iter_markdown_files(roots)


_NOQA_RE = re.compile(r"%%\s*noqa:\s*docs-lint", re.IGNORECASE)


def _block_has_noqa(body: str) -> bool:
    """True if the block body contains a ``%% noqa: docs-lint`` mermaid comment."""
    return bool(_NOQA_RE.search(body))


def find_mermaid_blocks(roots: Iterable[Path]) -> list[MermaidBlock]:
    """Return every fenced ```mermaid block under *roots*.

    *roots* may contain directories or individual ``.md`` files. Excluded directories
    (``output/``, ``projects_archive/``, ``projects_in_progress/``, etc.) are skipped.

    Blocks containing a ``%% noqa: docs-lint`` mermaid comment are excluded from
    discovery (they will not be validated by :func:`validate_blocks`).
    """
    blocks: list[MermaidBlock] = []
    for md in _iter_markdown_files(roots):
        try:
            text = md.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            logger.debug("skipping %s: %s", md, e)
            continue
        for match in _MERMAID_FENCE.finditer(text):
            body = match.group("body")
            if _block_has_noqa(body):
                continue
            # 1-indexed line of the opening fence
            line_no = text[: match.start()].count("\n") + 1
            kind_match = _KIND_RE.match(_first_meaningful_line(body))
            kind = kind_match.group("kind") if kind_match else "unknown"
            blocks.append(
                MermaidBlock(
                    file=md,
                    line=line_no,
                    kind=kind,
                    body=body,
                )
            )
    return blocks


def _first_meaningful_line(body: str) -> str:
    """Return the first non-blank, non-comment (`%%`) line."""
    for raw in body.splitlines():
        line = raw.strip()
        if not line or line.startswith("%%"):
            continue
        return line
    return ""


def _resolve_chrome(chrome_path: str | None) -> str | None:
    """Resolve the Chrome/Chromium binary path used by puppeteer.

    Priority:
      1. Explicit *chrome_path* argument.
      2. ``CHROME_EXECUTABLE_PATH`` env var.
      3. Detected ``chrome-headless-shell`` from ``puppeteer browsers install``.
      4. macOS system Chrome at ``/Applications/Google Chrome.app``.
    """
    if chrome_path:
        return chrome_path
    env = os.environ.get("CHROME_EXECUTABLE_PATH")
    if env:
        return env
    home = Path.home()
    candidates: list[Path] = []
    cache = home / ".cache" / "puppeteer" / "chrome-headless-shell"
    if cache.is_dir():
        for sub in sorted(cache.iterdir()):
            for name in ("chrome-headless-shell", "chrome-headless-shell.exe"):
                hits = list(sub.rglob(name))
                candidates.extend(hits)
    macos_chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    if macos_chrome.exists():
        candidates.append(macos_chrome)
    for c in candidates:
        if c.exists():
            return str(c)
    return None


def _puppeteer_config(chrome_path: str | None) -> dict[str, object]:
    """Build a puppeteer-config.json payload for `mmdc`."""
    cfg: dict[str, object] = {"args": ["--no-sandbox"]}
    if chrome_path:
        cfg["executablePath"] = chrome_path
    return cfg


def _run_mmdc(
    block: MermaidBlock,
    *,
    mmdc_bin: str,
    puppeteer_cfg_path: Path,
    workdir: Path,
) -> tuple[int, str]:
    """Render a single block with `mmdc`. Return (returncode, stderr)."""
    src = workdir / f"block_{block.line}.mmd"
    out = workdir / f"block_{block.line}.svg"
    src.write_text(block.body, encoding="utf-8")
    cmd = [
        mmdc_bin,
        "-i",
        str(src),
        "-o",
        str(out),
        "-p",
        str(puppeteer_cfg_path),
        "-q",  # quiet
    ]
    try:
        proc = subprocess.run(  # nosec B603 — fixed argv, no shell
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        return 124, f"mmdc timed out for {block.file}:{block.line}"
    return proc.returncode, proc.stderr or proc.stdout or ""


def validate_blocks(
    blocks: Sequence[MermaidBlock],
    mmdc_path: str | None = None,
    chrome_path: str | None = None,
) -> list[ValidationFailure]:
    """Render each block with `mmdc` and return failures.

    Raises:
        RuntimeError: when `mmdc` is not available. CI must install it; we fail loudly
            rather than skipping silently.
    """
    if not blocks:
        return []
    mmdc_bin = mmdc_path or shutil.which("mmdc")
    if not mmdc_bin or not Path(mmdc_bin).exists():
        raise RuntimeError(
            "mmdc (mermaid-cli) is not on PATH. Install with: "
            "`npm install -g @mermaid-js/mermaid-cli` and ensure a Chrome/Chromium "
            "binary is reachable via CHROME_EXECUTABLE_PATH or `puppeteer browsers "
            "install chrome-headless-shell`."
        )
    chrome_resolved = _resolve_chrome(chrome_path)
    failures: list[ValidationFailure] = []
    with tempfile.TemporaryDirectory(prefix="mermaid_lint_") as tmp:
        tmp_path = Path(tmp)
        cfg_path = tmp_path / "puppeteer-config.json"
        cfg_path.write_text(
            json.dumps(_puppeteer_config(chrome_resolved)),
            encoding="utf-8",
        )
        for block in blocks:
            rc, stderr = _run_mmdc(
                block,
                mmdc_bin=mmdc_bin,
                puppeteer_cfg_path=cfg_path,
                workdir=tmp_path,
            )
            if rc != 0:
                failures.append(ValidationFailure(block=block, stderr=stderr, returncode=rc))
    return failures


__all__ = [
    "MermaidBlock",
    "ValidationFailure",
    "find_mermaid_blocks",
    "mmdc_available",
    "validate_blocks",
]
