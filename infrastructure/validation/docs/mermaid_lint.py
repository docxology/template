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
import signal

# Required for real mmdc invocation; calls use fixed argv and no shell.
import subprocess  # nosec B404
import tempfile
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from infrastructure.core._optional_deps import psutil
from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering.chrome import resolve_chrome_executable
from infrastructure.validation.docs._io import read_markdown
from infrastructure.validation.docs.scan_scope import iter_markdown_files

logger = get_logger(__name__)

# Match fenced mermaid blocks. Captures the body. Multiline. Non-greedy.
_MERMAID_FENCE = re.compile(
    r"^(?P<fence>`{3,}|~{3,})mermaid[^\n]*\n(?P<body>.*?)\n(?P=fence)",
    re.MULTILINE | re.DOTALL,
)

# Heuristic: first non-empty, non-comment line tells us the diagram kind.
_KIND_RE = re.compile(r"^\s*(?P<kind>[A-Za-z][A-Za-z0-9_-]*)")
_MMDC_TIMEOUT_SECONDS = float(os.environ.get("TEMPLATE_MERMAID_LINT_TIMEOUT", "30"))
_MMDC_TOTAL_TIMEOUT_SECONDS = float(os.environ.get("TEMPLATE_MERMAID_LINT_TOTAL_TIMEOUT", "300"))
_MMDC_BATCH_TIMEOUT_SECONDS = float(os.environ.get("TEMPLATE_MERMAID_LINT_BATCH_TIMEOUT", "60"))
_MMDC_BATCH_SIZE = max(1, int(os.environ.get("TEMPLATE_MERMAID_LINT_BATCH_SIZE", "10")))


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


def resolve_mmdc_executable(repo_root: Path | None = None) -> str | None:
    """Return the pinned Mermaid CLI from PATH or the repository-local install.

    CI adds ``node_modules/.bin`` to ``PATH`` explicitly. Local commands are
    easier to reproduce when the Python gate also recognizes the documented
    repository-local install, even when a caller has not exported that PATH
    entry in its current shell.
    """
    candidate = shutil.which("mmdc")
    if candidate and Path(candidate).exists():
        return candidate
    root = (repo_root or Path.cwd()).resolve()
    local_candidate = root / "node_modules" / ".bin" / "mmdc"
    return str(local_candidate) if local_candidate.exists() else None


def mmdc_available(mmdc_path: str | None = None, repo_root: Path | None = None) -> bool:
    """Return True iff ``mmdc`` is available at an explicit, PATH, or local path."""
    candidate = mmdc_path or resolve_mmdc_executable(repo_root)
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
    (``output/``, the non-rendered typed subfolders ``projects/working|published|archive|other/``,
    etc.) are skipped.

    Blocks containing a ``%% noqa: docs-lint`` mermaid comment are excluded from
    discovery (they will not be validated by :func:`validate_blocks`).
    """
    blocks: list[MermaidBlock] = []
    for md in _iter_markdown_files(roots):
        text = read_markdown(md)
        if text is None:
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
      1. Explicit *chrome_path* argument (returned as given).
      2. The repo's canonical resolver
         (:func:`infrastructure.rendering.chrome.resolve_chrome_executable`):
         ``PUPPETEER_EXECUTABLE_PATH`` / ``CHROME_EXECUTABLE_PATH`` env vars
         (the vars CI exports), the version-sorted puppeteer cache, a system
         browser on ``PATH``, then the macOS system Chrome app for local dev.
    """
    if chrome_path:
        return chrome_path
    resolved = resolve_chrome_executable(include_macos_app=True)
    return str(resolved) if resolved is not None else None


def _puppeteer_config(chrome_path: str | None, user_data_dir: Path) -> dict[str, object]:
    """Build a puppeteer-config.json payload for `mmdc`."""
    cfg: dict[str, object] = {
        "args": ["--no-sandbox"],
        "userDataDir": str(user_data_dir),
    }
    if chrome_path:
        cfg["executablePath"] = chrome_path
    return cfg


def _kill_process_group(pid: int) -> None:
    """Kill the process group rooted at *pid* when the platform supports it."""
    if os.name == "nt" or pid == os.getpgrp():
        return
    try:
        os.killpg(pid, signal.SIGKILL)
    except (OSError, ProcessLookupError, PermissionError):
        return


def _kill_processes_matching(tokens: Sequence[str], attempts: int = 3) -> None:
    """Kill processes whose command line contains one of *tokens*."""
    if psutil is None:
        return
    for _ in range(max(1, attempts)):
        victims = []
        for candidate in psutil.process_iter(["pid", "cmdline"]):
            try:
                if candidate.pid == os.getpid():
                    continue
                cmdline = " ".join(candidate.info.get("cmdline") or [])
                if cmdline and any(token in cmdline for token in tokens):
                    victims.append(candidate)
            except (OSError, AttributeError, psutil.AccessDenied, psutil.NoSuchProcess):
                continue
        if not victims:
            return
        for victim in victims:
            try:
                victim.kill()
            except (OSError, AttributeError, psutil.AccessDenied, psutil.NoSuchProcess):
                continue
        psutil.wait_procs(victims, timeout=5)
        time.sleep(0.1)


def _close_process_pipes(proc: subprocess.Popen[str]) -> None:
    """Close captured pipes so orphaned descendants cannot block cleanup."""
    for stream in (proc.stdout, proc.stderr):
        if stream is not None:
            stream.close()


def _kill_process_tree(proc: subprocess.Popen[str], tokens: Sequence[str]) -> None:
    """Terminate *proc*, its descendants, and matching detached browser helpers."""
    _kill_process_group(proc.pid)
    if psutil is None:
        try:
            proc.kill()
        except ProcessLookupError:
            pass
        return
    try:
        parent = psutil.Process(proc.pid)
        children = parent.children(recursive=True)
        for child in children:
            child.kill()
        parent.kill()
        psutil.wait_procs([parent, *children], timeout=5)
    except (OSError, AttributeError, psutil.AccessDenied, psutil.NoSuchProcess):
        try:
            proc.kill()
        except ProcessLookupError:
            pass
    _kill_processes_matching(tokens)


def _run_mmdc(
    block: MermaidBlock,
    *,
    mmdc_bin: str,
    puppeteer_cfg_path: Path,
    workdir: Path,
    timeout_seconds: float,
    timeout_description: str | None = None,
) -> tuple[int, str]:
    """Render a single block with `mmdc`. Return (returncode, stderr)."""
    src = workdir / f"block_{block.line}.mmd"
    out = workdir / f"block_{block.line}.svg"
    src.write_text(block.body, encoding="utf-8")
    return _run_mmdc_file(
        src,
        out,
        mmdc_bin=mmdc_bin,
        puppeteer_cfg_path=puppeteer_cfg_path,
        workdir=workdir,
        timeout_seconds=timeout_seconds,
        timeout_description=timeout_description,
        block=block,
    )


def _run_mmdc_file(
    src: Path,
    out: Path,
    *,
    mmdc_bin: str,
    puppeteer_cfg_path: Path,
    workdir: Path,
    timeout_seconds: float,
    timeout_description: str | None,
    block: MermaidBlock,
) -> tuple[int, str]:
    """Render a Mermaid source file with `mmdc`. Return (returncode, stderr)."""
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
    proc = subprocess.Popen(  # nosec B603
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=(os.name != "nt"),
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        _kill_process_tree(proc, tokens=[str(workdir)])
        try:
            proc.communicate(timeout=1)
        except subprocess.TimeoutExpired:
            _close_process_pipes(proc)
        description = timeout_description or f"mmdc timed out after {timeout_seconds:g}s"
        return (
            124,
            f"{description} for {block.file}:{block.line}; command: {' '.join(cmd)}",
        )
    _kill_process_group(proc.pid)
    _kill_processes_matching([str(workdir)])
    rc = int(proc.returncode)
    # Fail closed on a silent no-op: `mmdc` occasionally exits 0 without writing
    # the requested output (e.g. a Chrome/puppeteer hiccup). Trusting the exit
    # code alone would swallow that as a pass — for a single block and, worse,
    # for a whole batch. Treat "exit 0 but no output file" as a failure so the
    # caller surfaces it (and, for a batch, falls back to per-block diagnosis).
    if rc == 0 and (not out.exists() or out.stat().st_size == 0):
        return (
            1,
            f"mmdc exited 0 but produced no output at {out.name} for "
            f"{block.file}:{block.line}; command: {' '.join(cmd)}",
        )
    return rc, stderr or stdout or ""


def _run_mmdc_batch(
    blocks: Sequence[MermaidBlock],
    *,
    mmdc_bin: str,
    puppeteer_cfg_path: Path,
    workdir: Path,
    timeout_seconds: float,
    timeout_description: str | None,
) -> tuple[int, str]:
    """Render every block in one Markdown input; callers fall back on failure."""
    src = workdir / "batch.md"
    out = workdir / "batch_out.md"
    parts: list[str] = []
    for index, block in enumerate(blocks, start=1):
        parts.append(f"<!-- mermaid-lint block {index}: {block.file}:{block.line} -->")
        parts.append("```mermaid")
        parts.append(block.body)
        parts.append("```")
        parts.append("")
    src.write_text("\n".join(parts), encoding="utf-8")
    return _run_mmdc_file(
        src,
        out,
        mmdc_bin=mmdc_bin,
        puppeteer_cfg_path=puppeteer_cfg_path,
        workdir=workdir,
        timeout_seconds=timeout_seconds,
        timeout_description=timeout_description,
        block=blocks[0],
    )


def _chunks(blocks: Sequence[MermaidBlock], size: int) -> Iterable[Sequence[MermaidBlock]]:
    """Yield non-empty chunks from *blocks*."""
    for index in range(0, len(blocks), size):
        yield blocks[index : index + size]


def validate_blocks(
    blocks: Sequence[MermaidBlock],
    mmdc_path: str | None = None,
    chrome_path: str | None = None,
    timeout_seconds: float = _MMDC_TIMEOUT_SECONDS,
    total_timeout_seconds: float = _MMDC_TOTAL_TIMEOUT_SECONDS,
) -> list[ValidationFailure]:
    """Render each block with `mmdc` and return failures.

    Raises:
        RuntimeError: when `mmdc` is not available. CI must install it; we fail loudly
            rather than skipping silently.
    """
    if not blocks:
        return []
    mmdc_bin = mmdc_path or resolve_mmdc_executable()
    if not mmdc_bin or not Path(mmdc_bin).exists():
        raise RuntimeError(
            "mmdc (mermaid-cli) is unavailable. From the repository root, run "
            "`npm ci`; the Python gate auto-discovers `node_modules/.bin/mmdc` "
            "(prepend that directory to PATH for direct `mmdc` calls); ensure a Chrome/Chromium "
            "binary is reachable via CHROME_EXECUTABLE_PATH or run "
            "`npx --no-install puppeteer browsers install chrome-headless-shell`."
        )
    chrome_resolved = _resolve_chrome(chrome_path)
    failures: list[ValidationFailure] = []
    started_at = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="mermaid_lint_") as tmp:
        tmp_path = Path(tmp)
        cfg_path = tmp_path / "puppeteer-config.json"
        chrome_profile = tmp_path / "chrome-profile"
        cfg_path.write_text(
            json.dumps(_puppeteer_config(chrome_resolved, chrome_profile)),
            encoding="utf-8",
        )
        try:
            for batch in _chunks(blocks, _MMDC_BATCH_SIZE):
                elapsed = time.monotonic() - started_at
                remaining = total_timeout_seconds - elapsed
                if remaining <= 0:
                    failures.append(
                        ValidationFailure(
                            block=batch[0],
                            stderr=(
                                f"mermaid lint total timeout after {total_timeout_seconds:g}s "
                                f"before rendering {batch[0].file}:{batch[0].line}; mmdc: {mmdc_bin}"
                            ),
                            returncode=124,
                        )
                    )
                    return failures
                batch_timeout = min(remaining, _MMDC_BATCH_TIMEOUT_SECONDS)
                batch_timeout_description = (
                    f"mermaid lint total timeout after {total_timeout_seconds:g}s"
                    if remaining <= batch_timeout
                    else f"mmdc batch timed out after {batch_timeout:g}s"
                )
                batch_rc, batch_stderr = _run_mmdc_batch(
                    batch,
                    mmdc_bin=mmdc_bin,
                    puppeteer_cfg_path=cfg_path,
                    workdir=tmp_path,
                    timeout_seconds=batch_timeout,
                    timeout_description=batch_timeout_description,
                )
                if batch_rc == 0:
                    continue
                if batch_rc == 124:
                    failures.extend(
                        _validate_blocks_individually(
                            batch,
                            mmdc_bin=mmdc_bin,
                            puppeteer_cfg_path=cfg_path,
                            workdir=tmp_path,
                            timeout_seconds=timeout_seconds,
                            total_timeout_seconds=total_timeout_seconds,
                            started_at=started_at,
                        )
                    )
                    if failures and failures[-1].returncode == 124:
                        return failures
                    continue
                failures.extend(
                    _validate_blocks_individually(
                        batch,
                        mmdc_bin=mmdc_bin,
                        puppeteer_cfg_path=cfg_path,
                        workdir=tmp_path,
                        timeout_seconds=timeout_seconds,
                        total_timeout_seconds=total_timeout_seconds,
                        started_at=started_at,
                    )
                )
                if failures and failures[-1].returncode == 124:
                    return failures
        finally:
            _kill_processes_matching([str(tmp_path)])
    return failures


def _validate_blocks_individually(
    blocks: Sequence[MermaidBlock],
    *,
    mmdc_bin: str,
    puppeteer_cfg_path: Path,
    workdir: Path,
    timeout_seconds: float,
    total_timeout_seconds: float,
    started_at: float,
) -> list[ValidationFailure]:
    """Validate blocks one at a time after a batch failure for precise errors."""
    failures: list[ValidationFailure] = []
    for block in blocks:
        elapsed = time.monotonic() - started_at
        remaining = total_timeout_seconds - elapsed
        if remaining <= 0:
            failures.append(
                ValidationFailure(
                    block=block,
                    stderr=(
                        f"mermaid lint total timeout after {total_timeout_seconds:g}s "
                        f"before rendering {block.file}:{block.line}; mmdc: {mmdc_bin}"
                    ),
                    returncode=124,
                )
            )
            break
        render_timeout = min(timeout_seconds, remaining)
        timeout_description = (
            None if remaining >= timeout_seconds else f"mermaid lint total timeout after {total_timeout_seconds:g}s"
        )
        rc, stderr = _run_mmdc(
            block,
            mmdc_bin=mmdc_bin,
            puppeteer_cfg_path=puppeteer_cfg_path,
            workdir=workdir,
            timeout_seconds=render_timeout,
            timeout_description=timeout_description,
        )
        if rc != 0:
            failures.append(ValidationFailure(block=block, stderr=stderr, returncode=rc))
        if time.monotonic() - started_at >= total_timeout_seconds:
            break
    return failures


__all__ = [
    "MermaidBlock",
    "ValidationFailure",
    "find_mermaid_blocks",
    "mmdc_available",
    "resolve_mmdc_executable",
    "validate_blocks",
]
