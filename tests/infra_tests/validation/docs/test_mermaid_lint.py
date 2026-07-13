"""Tests for infrastructure.validation.docs.mermaid_lint.

Zero-mocks: the test creates a real on-disk Markdown tree and (when ``mmdc`` is
available locally) invokes the actual binary. CI installs ``mmdc`` explicitly,
so the gate fails loudly there if it is missing.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from infrastructure.validation.docs.mermaid_lint import (
    MermaidBlock,
    ValidationFailure,
    find_mermaid_blocks,
    mmdc_available,
    validate_blocks,
)


_VALID_MERMAID = """flowchart TB
    A[Start] --> B[End]
"""

_INVALID_MERMAID = """flowchart TB
    A --> B(((( <<<broken syntax>>>>
"""


def _write_md(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_find_mermaid_blocks_discovers_fenced_blocks(tmp_path: Path) -> None:
    md = tmp_path / "page.md"
    _write_md(
        md,
        f"""# Heading

Some text.

```mermaid
{_VALID_MERMAID.strip()}
```

More text.

```mermaid
{_INVALID_MERMAID.strip()}
```
""",
    )
    blocks = find_mermaid_blocks([tmp_path])
    assert len(blocks) == 2
    assert all(isinstance(b, MermaidBlock) for b in blocks)
    assert blocks[0].kind == "flowchart"
    # Line numbers are 1-indexed and point at the opening fence
    assert blocks[0].line == 5
    assert blocks[1].line == 12


def test_find_mermaid_blocks_skips_excluded_dirs(tmp_path: Path) -> None:
    # Generated and local-agent trees are on the shared docs-scan exclude list.
    for bad in (
        tmp_path / "output" / "ignored.md",
        tmp_path / ".claude" / "worktrees" / "ignored.md",
    ):
        _write_md(bad, "```mermaid\nflowchart\n```\n")
    good = tmp_path / "docs" / "live.md"
    _write_md(good, "```mermaid\nflowchart\n```\n")
    blocks = find_mermaid_blocks([tmp_path])
    assert len(blocks) == 1
    assert blocks[0].file == good


def test_find_mermaid_blocks_handles_unicode(tmp_path: Path) -> None:
    md = tmp_path / "u.md"
    _write_md(md, "```mermaid\ngraph LR\n  A --> B\n```\n# heading 文字\n")
    blocks = find_mermaid_blocks([tmp_path])
    assert len(blocks) == 1
    assert blocks[0].kind == "graph"


def test_validate_blocks_raises_when_mmdc_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """If mmdc is on PATH but we point to a non-existent path, a clear error fires."""
    md = tmp_path / "p.md"
    _write_md(md, "```mermaid\nflowchart\n  A-->B\n```\n")
    blocks = find_mermaid_blocks([tmp_path])
    assert blocks
    with pytest.raises(RuntimeError, match="mmdc"):
        validate_blocks(blocks, mmdc_path="/nonexistent/path/to/mmdc")


@pytest.mark.skipif(not mmdc_available(), reason="mmdc (mermaid-cli) not installed")
def test_validate_blocks_passes_valid_diagram(tmp_path: Path) -> None:
    md = tmp_path / "p.md"
    _write_md(md, f"```mermaid\n{_VALID_MERMAID}```\n")
    blocks = find_mermaid_blocks([tmp_path])
    failures = validate_blocks(blocks)
    assert failures == []


@pytest.mark.skipif(not mmdc_available(), reason="mmdc (mermaid-cli) not installed")
def test_validate_blocks_flags_invalid_diagram(tmp_path: Path) -> None:
    md = tmp_path / "p.md"
    # Use clearly-broken mermaid that mmdc rejects.
    body = "flowchart TB\n  A -->\n  --> ?? <<<\n"
    _write_md(md, f"```mermaid\n{body}```\n")
    blocks = find_mermaid_blocks([tmp_path])
    failures = validate_blocks(blocks)
    assert len(failures) == 1
    assert isinstance(failures[0], ValidationFailure)
    assert failures[0].block.file == md
    assert failures[0].returncode != 0
    assert "mermaid" in failures[0].format().lower()


def test_validate_blocks_empty_input_returns_empty_list() -> None:
    assert validate_blocks([]) == []


@pytest.mark.skipif(os.name == "nt", reason="POSIX executable script semantics")
def test_validate_blocks_timeout_kills_mmdc_process_tree(tmp_path: Path) -> None:
    md = tmp_path / "p.md"
    _write_md(md, "```mermaid\nflowchart TB\n  A-->B\n```\n")
    slow_mmdc = tmp_path / "slow_mmdc"
    slow_mmdc.write_text(
        "#!/usr/bin/env python3\n"
        "import subprocess\n"
        "import sys\n"
        "import time\n"
        "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(5)'])\n"
        "try:\n"
        "    time.sleep(5)\n"
        "finally:\n"
        "    child.terminate()\n",
        encoding="utf-8",
    )
    slow_mmdc.chmod(0o755)

    failures = validate_blocks(find_mermaid_blocks([tmp_path]), mmdc_path=str(slow_mmdc), timeout_seconds=0.1)

    assert len(failures) == 1
    assert failures[0].returncode == 124
    assert "timed out" in failures[0].stderr


@pytest.mark.skipif(os.name == "nt", reason="POSIX executable script semantics")
def test_validate_blocks_total_timeout_reports_targeted_block(tmp_path: Path) -> None:
    md = tmp_path / "p.md"
    _write_md(md, "```mermaid\nflowchart TB\n  A-->B\n```\n")
    fake_mmdc = tmp_path / "fake_mmdc"
    fake_mmdc.write_text("#!/usr/bin/env python3\nprint('not reached')\n", encoding="utf-8")
    fake_mmdc.chmod(0o755)

    failures = validate_blocks(
        find_mermaid_blocks([tmp_path]),
        mmdc_path=str(fake_mmdc),
        timeout_seconds=10,
        total_timeout_seconds=0,
    )

    assert len(failures) == 1
    assert failures[0].returncode == 124
    assert "total timeout" in failures[0].stderr
    assert str(md) in failures[0].stderr
    assert str(fake_mmdc) in failures[0].stderr


def test_validate_blocks_flags_exit_zero_with_no_output(tmp_path: Path) -> None:
    """A fake mmdc that exits 0 without writing output must NOT pass silently.

    Guards the batch/individual success path against a swallowed render failure
    (mmdc occasionally exits 0 without producing the requested file).
    """
    md = tmp_path / "p.md"
    _write_md(md, "```mermaid\nflowchart TB\n  A-->B\n```\n")
    # Real executable, no mocks: exits 0 but never writes the -o output file.
    fake_mmdc = tmp_path / "fake_mmdc"
    fake_mmdc.write_text("#!/usr/bin/env python3\nimport sys\nsys.exit(0)\n", encoding="utf-8")
    fake_mmdc.chmod(0o755)

    failures = validate_blocks(find_mermaid_blocks([tmp_path]), mmdc_path=str(fake_mmdc))

    assert len(failures) == 1
    assert failures[0].returncode == 1
    assert "produced no output" in failures[0].stderr
    assert str(md) in failures[0].stderr


def test_mermaid_block_dataclass_is_frozen() -> None:
    block = MermaidBlock(file=Path("/x.md"), line=1, kind="flowchart", body="A-->B")
    with pytest.raises(Exception):  # frozen dataclass
        block.line = 2  # type: ignore[misc]
