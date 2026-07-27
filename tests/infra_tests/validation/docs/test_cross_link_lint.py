"""Tests for infrastructure.validation.docs.cross_link_lint.

Zero-mocks: tests build a real on-disk Markdown tree and verify resolution.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.validation.docs.cross_link_lint import (
    BrokenLink,
    detect_markdown_link_cycles,
    find_broken_links,
)


def _write(p: Path, body: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")


def test_find_broken_links_resolves_relative_targets(tmp_path: Path) -> None:
    target = tmp_path / "guide.md"
    _write(target, "# guide")
    md = tmp_path / "index.md"
    _write(
        md,
        """[ok](guide.md)
[bad](missing.md)
""",
    )
    broken = find_broken_links([tmp_path])
    assert len(broken) == 1
    assert isinstance(broken[0], BrokenLink)
    assert broken[0].target == "missing.md"
    assert broken[0].file == md


def test_find_broken_links_skips_external_urls(tmp_path: Path) -> None:
    md = tmp_path / "p.md"
    _write(
        md,
        """[home](https://example.com)
[mail](mailto:foo@bar)
[ftp](ftp://example.com/file)
""",
    )
    assert find_broken_links([tmp_path]) == []


def test_find_broken_links_skips_anchor_only_links(tmp_path: Path) -> None:
    """A pure `#anchor` is not a missing FILE (its anchor is checked separately)."""
    md = tmp_path / "p.md"
    _write(md, "[top](#heading)\n\n## Heading\n")
    assert find_broken_links([tmp_path]) == []


def test_find_broken_links_skips_fenced_code_blocks(tmp_path: Path) -> None:
    md = tmp_path / "p.md"
    _write(
        md,
        """Outside link:
```
[fake](nope.md)
```

```python
[also fake](nope2.md)
```
""",
    )
    assert find_broken_links([tmp_path]) == []


def test_find_broken_links_skips_indented_fenced_code_blocks(tmp_path: Path) -> None:
    md = tmp_path / "p.md"
    _write(
        md,
        """A list:

- bullet:

    ```
    [fake](nope.md)
    ```
""",
    )
    assert find_broken_links([tmp_path]) == []


def test_find_broken_links_skips_inline_single_backtick_links(tmp_path: Path) -> None:
    md = tmp_path / "p.md"
    _write(md, "Use `[fake](nope.md)` syntax for links.\n")
    assert find_broken_links([tmp_path]) == []


def test_find_broken_links_skips_inline_double_backtick_links(tmp_path: Path) -> None:
    md = tmp_path / "p.md"
    _write(md, "Use ``[fake](nope.md)`` for `inline` examples.\n")
    assert find_broken_links([tmp_path]) == []


def test_find_broken_links_handles_anchored_targets(tmp_path: Path) -> None:
    """An `#anchor` suffix must not interfere with resolving the FILE part."""
    target = tmp_path / "guide.md"
    _write(target, "# guide\n\n## Heading\n")
    md = tmp_path / "index.md"
    _write(
        md,
        """[good with anchor](guide.md#heading)
[bad with anchor](missing.md#heading)
""",
    )
    broken = find_broken_links([tmp_path])
    assert len(broken) == 1
    assert "missing.md#heading" in broken[0].target


def test_find_broken_links_reports_correct_line_number(tmp_path: Path) -> None:
    md = tmp_path / "p.md"
    _write(
        md,
        """line 1
line 2
[bad](missing.md)
line 4
""",
    )
    broken = find_broken_links([tmp_path])
    assert len(broken) == 1
    assert broken[0].line == 3


def test_find_broken_links_preserves_original_text_in_inline_code(tmp_path: Path) -> None:
    """Even with inline-code stripping, the BrokenLink.text should be the source text."""
    target = tmp_path / "g.md"
    _write(target, "# g")
    md = tmp_path / "p.md"
    _write(md, "Some [`backtick text`](missing.md) here.\n")
    broken = find_broken_links([tmp_path])
    assert len(broken) == 1
    assert broken[0].text == "`backtick text`"


def test_find_broken_links_excludes_default_dirs(tmp_path: Path) -> None:
    bad = tmp_path / "output" / "ignored.md"
    _write(bad, "[bad](nope.md)\n")
    good = tmp_path / "docs" / "live.md"
    _write(good, "# live")
    assert find_broken_links([tmp_path]) == []


def test_find_broken_links_excludes_skill_eval_workspace(tmp_path: Path) -> None:
    """Regenerated eval fixtures under _skill-eval/ are outside link-lint scope."""
    fixture = tmp_path / "docs" / "prompts" / "_skill-eval" / "latest" / "with_skill" / "outputs" / "response.md"
    _write(fixture, "[bad relative link](../../_generated/active_projects.md)\n")
    good = tmp_path / "docs" / "prompts" / "README.md"
    _write(good, "# prompts hub")
    assert find_broken_links([tmp_path]) == []


def test_find_broken_links_skips_public_project_generated_output(tmp_path: Path) -> None:
    md = tmp_path / "projects" / "templates" / "template_code_project" / "manuscript" / "03_results.md"
    _write(md, "![generated](../output/figures/performance_benchmark.png)\n")

    assert find_broken_links([tmp_path]) == []


def test_find_broken_links_reports_missing_public_project_source_link(tmp_path: Path) -> None:
    md = tmp_path / "projects" / "templates" / "template_code_project" / "manuscript" / "03_results.md"
    _write(md, "[missing source](../src/missing.py)\n")

    broken = find_broken_links([tmp_path])

    assert len(broken) == 1
    assert broken[0].target == "../src/missing.py"


def test_find_broken_links_reports_unqualified_public_template_links(tmp_path: Path) -> None:
    """Old ``projects/template_*`` links are stale public-exemplar paths."""
    md = tmp_path / ".github" / "README.md"
    _write(
        md,
        "[stale public exemplar](../projects/template_code_project/README.md)\n",
    )

    broken = find_broken_links([tmp_path])

    assert len(broken) == 1
    assert broken[0].target == "../projects/template_code_project/README.md"


def test_find_broken_links_skips_missing_nonpublic_project_links(tmp_path: Path) -> None:
    """Rotating local-only project references remain absent by design."""
    md = tmp_path / "docs" / "local.md"
    _write(md, "[local only](../projects/private_rotation/README.md)\n")

    assert find_broken_links([tmp_path]) == []


def test_anchor_gate_rejects_dangling_cross_file_fragment(tmp_path: Path) -> None:
    """Positive control: the anchor check must be able to FAIL, not just pass."""
    _write(tmp_path / "guide.md", "# Guide\n\n## Real Section\n")
    md = tmp_path / "index.md"
    _write(md, "[bad](guide.md#no-such-section)\n")
    broken = find_broken_links([tmp_path])
    assert len(broken) == 1
    assert "anchor '#no-such-section'" in broken[0].reason


def test_anchor_gate_accepts_resolving_cross_file_fragment(tmp_path: Path) -> None:
    _write(tmp_path / "guide.md", "# Guide\n\n## Real Section\n")
    _write(tmp_path / "index.md", "[ok](guide.md#real-section)\n")
    assert find_broken_links([tmp_path]) == []


def test_anchor_gate_rejects_dangling_same_file_fragment(tmp_path: Path) -> None:
    md = tmp_path / "p.md"
    _write(md, "# Title\n\n[jump](#missing-heading)\n\n## Present\n")
    broken = find_broken_links([tmp_path])
    assert len(broken) == 1
    assert broken[0].target == "#missing-heading"


def test_emoji_heading_slug_keeps_leading_separator(tmp_path: Path) -> None:
    """GitHub drops the emoji but keeps the space it left, yielding `-quick-start`."""
    md = tmp_path / "p.md"
    _write(md, "# T\n\n[a](#quick-start)\n[b](#-quick-start)\n\n## \N{ROCKET} Quick Start\n")
    broken = find_broken_links([tmp_path])
    assert [b.target for b in broken] == ["#quick-start"]


def test_anchor_slug_preserves_inline_code_and_underscores(tmp_path: Path) -> None:
    """`secure_run.sh` in a heading contributes `secure_runsh`, underscore intact."""
    md = tmp_path / "p.md"
    _write(md, "# T\n\n[a](#secure-pipeline-secure_runsh)\n\n## Secure pipeline (`secure_run.sh`)\n")
    assert find_broken_links([tmp_path]) == []


def test_anchor_gate_honours_explicit_html_id(tmp_path: Path) -> None:
    _write(tmp_path / "guide.md", '# G\n\n<a id="custom-target"></a>\n\n## \N{DIRECT HIT} Section\n')
    _write(tmp_path / "index.md", "[ok](guide.md#custom-target)\n")
    assert find_broken_links([tmp_path]) == []


def test_anchor_gate_skips_glossary_dsl_fragments(tmp_path: Path) -> None:
    """`#gl:` fragments are a textbook glossary DSL, not heading anchors."""
    md = tmp_path / "p.md"
    _write(md, "# T\n\n[term](#gl:entropy)\n")
    assert find_broken_links([tmp_path]) == []


def test_anchor_gate_ignores_fragments_on_non_markdown_targets(tmp_path: Path) -> None:
    """A `#L12` fragment on a source file is a line reference, not an anchor."""
    _write(tmp_path / "mod.py", "x = 1\n")
    _write(tmp_path / "p.md", "[code](mod.py#L1)\n")
    assert find_broken_links([tmp_path]) == []


def test_anchor_gate_respects_noqa(tmp_path: Path) -> None:
    _write(tmp_path / "guide.md", "# Guide\n")
    _write(tmp_path / "p.md", "[x](guide.md#nope) <!-- noqa: docs-lint -->\n")
    assert find_broken_links([tmp_path]) == []


def test_duplicate_headings_get_numeric_anchor_suffixes(tmp_path: Path) -> None:
    _write(tmp_path / "guide.md", "# G\n\n## Notes\n\n## Notes\n")
    _write(tmp_path / "index.md", "[one](guide.md#notes)\n[two](guide.md#notes-1)\n[three](guide.md#notes-2)\n")
    broken = find_broken_links([tmp_path])
    assert [b.target for b in broken] == ["guide.md#notes-2"]


def test_find_broken_links_format_returns_string() -> None:
    bl = BrokenLink(
        file=Path("/x/y.md"),
        line=42,
        text="hi",
        target="nope.md",
        reason="target does not exist on disk",
    )
    s = bl.format()
    assert "/x/y.md:42" in s
    assert "[hi](nope.md)" in s
    assert "target does not exist" in s


def test_detect_markdown_link_cycles_finds_two_node_cycle(tmp_path: Path) -> None:
    a = tmp_path / "a.md"
    b = tmp_path / "b.md"
    _write(a, "[to b](b.md)\n")
    _write(b, "[to a](a.md)\n")
    cycles = detect_markdown_link_cycles([tmp_path])
    assert len(cycles) >= 1
    cycle_nodes = {Path(node).name for node in cycles[0].files}
    assert {"a.md", "b.md"}.issubset(cycle_nodes)
