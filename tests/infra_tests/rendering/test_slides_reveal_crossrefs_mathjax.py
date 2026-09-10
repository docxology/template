"""Accessible Beamer overflow gate, reveal crossref resolution, and MathJax hardening (split from test_slides_accessibility.py)."""

from __future__ import annotations

import re
from pathlib import Path
import pytest
from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._slides_accessibility import (
    AccessibleSlidePolicy,
    accessible_reveal_output_issues,
    enhance_accessible_reveal,
)
from infrastructure.rendering._slides_reveal_content import (
    ACCESSIBLE_REVEAL_URL,
    activate_hardened_reveal_mathjax,
    promote_display_math_labels,
    resolve_reveal_cross_references,
    reveal_reference_and_math_issues,
)
from infrastructure.rendering._web_postprocess import (
    MATHJAX_URL,
    _MATHJAX_CONFIG_SCRIPT,
    _MATHJAX_INTEGRITY,
    harden_mathjax_script,
)
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.slides_renderer import (
    SlidesRenderer,
    _reject_accessible_beamer_overflow,
)


def test_accessible_beamer_overflow_discards_derivative_with_stable_diagnostic(tmp_path: Path) -> None:
    log_file = tmp_path / "deck.log"
    compiled_pdf = tmp_path / "deck.pdf"
    log_file.write_text("Overfull \\vbox (3.5pt too high) detected at line 42\n", encoding="utf-8")
    compiled_pdf.write_bytes(b"%PDF-1.7\nfailed-layout")

    with pytest.raises(RenderingError, match=r"\[slides\.density\.beamer-overflow\]") as exc_info:
        _reject_accessible_beamer_overflow(log_file, compiled_pdf)

    assert not compiled_pdf.exists()
    assert exc_info.value.context["diagnostic_code"] == "slides.density.beamer-overflow"
    assert exc_info.value.context["finding_count"] == 1


def test_accessible_beamer_overflow_gate_ignores_non_layout_log_findings(tmp_path: Path) -> None:
    log_file = tmp_path / "deck.log"
    compiled_pdf = tmp_path / "deck.pdf"
    log_file.write_text(
        "LaTeX Warning: Reference `fig:other-deck' on page 2 undefined on input line 42.\n",
        encoding="utf-8",
    )
    compiled_pdf.write_bytes(b"%PDF-1.7\nlayout-valid")

    _reject_accessible_beamer_overflow(log_file, compiled_pdf)

    assert compiled_pdf.exists()


def test_accessible_reveal_names_slides_on_opening_headings_and_orders_navigation(tmp_path: Path) -> None:
    """Post-processing produces resolvable names without leaking build identities."""

    reveal = tmp_path / "deck_slides.html"
    reveal.write_text(
        "<!doctype html><html><head>"
        "<title>.deck-random.pandoc.accessible</title>"
        '<link rel="stylesheet" href="https://unpkg.com/reveal.js@5.2.1/dist/theme/white.css">'
        '</head><body><div class="reveal"><div class="slides">'
        '<section class="slide level2"><h2>Evidence <em>boundary</em></h2><p>First.</p></section>'
        '<section class="slide level2"><h2>Evidence <em>boundary</em></h2><p>Second.</p></section>'
        "</div></div><script>Reveal.initialize({keyboard: true});</script></body></html>",
        encoding="utf-8",
    )

    enhance_accessible_reveal(
        reveal,
        policy=AccessibleSlidePolicy(reader_href="../web/index.html"),
        registry_path=None,
    )
    # The transform is intentionally idempotent; rerunning a validation-stage
    # enhancement cannot duplicate document or slide identities.
    enhance_accessible_reveal(
        reveal,
        policy=AccessibleSlidePolicy(reader_href="../web/index.html"),
        registry_path=None,
    )
    rendered = reveal.read_text(encoding="utf-8")

    assert "<title>Evidence boundary — presentation</title>" in rendered
    assert '<h1 id="presentation-title-' in rendered
    assert 'class="visually-hidden">Evidence boundary — presentation</h1>' in rendered
    assert "</h2 id=" not in rendered
    heading_ids = re.findall(r'<h2\b[^>]*\bid="([^"]+)"', rendered)
    labelled_by = re.findall(r'<section\b[^>]*\baria-labelledby="([^"]+)"', rendered)
    assert len(heading_ids) == len(set(heading_ids)) == 2
    assert labelled_by == heading_ids
    assert rendered.index('class="skip-link"') < rendered.index('class="slide-reader-nav"')
    assert accessible_reveal_output_issues(reveal) == ()


def test_reveal_crossrefs_use_aux_numbers_and_preserve_bibliographic_citations() -> None:
    content = (
        '<section id="sec:local"><h2>Local</h2>'
        '<p>See <span class="citation" data-cites="sec:local">'
        "(<strong>sec:local?</strong>)</span>, "
        '<span class="citation" data-cites="eq:foreign">'
        "(<strong>eq:foreign?</strong>)</span>, and "
        '<span class="citation" data-cites="smith2026">(Smith 2026)</span>.</p></section>'
    )

    resolved = resolve_reveal_cross_references(
        content,
        {"sec:local": "2.1", "eq:foreign": "7"},
        strict=True,
    )

    assert '<a class="cross-reference" href="#sec:local">Section 2.1</a>' in resolved
    assert '<span class="cross-reference">Equation (7)</span>' in resolved
    assert '<span class="citation" data-cites="smith2026">(Smith 2026)</span>' in resolved
    assert "sec:local?" not in resolved
    assert "eq:foreign?" not in resolved


def test_reveal_raw_inline_math_references_use_aux_numbers_and_consume_tex_join() -> None:
    content = (
        '<section id="sec:local"><h2>Local</h2>'
        '<p>See Section~<span class="math inline">\\(\\ref{sec:local}\\)</span> '
        'and identity (<span class="math inline">\\(\\ref{eq:foreign}\\)</span>).</p></section>'
    )

    resolved = resolve_reveal_cross_references(
        content,
        {"sec:local": "2.1", "eq:foreign": "7"},
        strict=True,
    )

    assert 'Section\N{NO-BREAK SPACE}<a class="cross-reference" href="#sec:local">2.1</a>' in resolved
    assert 'identity (<span class="cross-reference">7</span>)' in resolved
    assert "~" not in resolved
    assert r"\ref{" not in resolved


def test_reveal_deduplicates_raw_reference_html_fallback_after_crossref_filter() -> None:
    content = (
        '<section id="eq:model"><p>Equation '
        '<span class="math inline">\\(\\ref{eq:model}\\)</span>'
        '<span class="citation formal-reference" data-cites="eq:model">'
        "(<strong>eq:model?</strong>)</span>.</p></section>"
    )

    resolved = resolve_reveal_cross_references(content, {"eq:model": "7"}, strict=True)
    visible = " ".join(re.sub(r"<[^>]+>", "", resolved).split())

    assert visible == "Equation 7."
    assert resolved.count('href="#eq:model"') == 1


def test_reveal_inline_equation_references_have_one_parenthesis_pair() -> None:
    content = (
        '<p>Equation <span class="math inline">\\(\\eqref{eq:model}\\)</span>; '
        'Equation (<span class="math inline">\\(\\eqref{eq:model}\\)</span>); '
        'identity (<span class="math inline">\\(\\ref{eq:model}\\)</span>).</p>'
    )

    resolved = resolve_reveal_cross_references(content, {"eq:model": "7"}, strict=True)
    visible = " ".join(re.sub(r"<[^>]+>", "", resolved).split())

    assert visible == "Equation (7); Equation (7); identity (7)."
    assert "((7))" not in visible


@pytest.mark.parametrize("command", ["ref", "eqref"])
def test_reveal_parenthesized_reference_consumes_tex_join(command: str) -> None:
    content = f'<p>Equation~(<span class="math inline">\\(\\{command}{{eq:model}}\\)</span>).</p>'

    resolved = resolve_reveal_cross_references(content, {"eq:model": "7"}, strict=True)
    visible = re.sub(r"<[^>]+>", "", resolved)

    assert visible == "Equation\N{NO-BREAK SPACE}(7)."
    assert "~" not in visible
    assert "((7))" not in visible
    assert reveal_reference_and_math_issues(resolved) == ()


def test_reveal_raw_reference_validation_ignores_code_but_covers_unsupported_reference_family() -> None:
    code = r"<pre><code>Use \ref{sec:example} and \pageref{sec:example} literally.</code></pre>"
    assert "raw TeX cross-reference" not in " ".join(reveal_reference_and_math_issues(code))

    for command in ("pageref", "nameref", "subref"):
        issues = reveal_reference_and_math_issues(rf"<p>Use \{command}{{sec:example}}.</p>")
        assert "Reveal deck contains a raw TeX cross-reference command" in issues


def test_reveal_raw_inline_math_reference_is_strict_and_visible_validation_fails_closed() -> None:
    content = '<p><span class="math inline">\\(\\ref{thm:missing}\\)</span></p>'

    with pytest.raises(RenderingError, match="cannot resolve references") as exc_info:
        resolve_reveal_cross_references(content, {}, strict=True)

    assert exc_info.value.context["unresolved_labels"] == ["thm:missing"]
    assert "Reveal deck contains a raw TeX cross-reference command" in reveal_reference_and_math_issues(content)


def test_reveal_crossrefs_humanize_standalone_and_strict_mode_rejects_missing_aux() -> None:
    content = (
        '<span class="citation" data-cites="sec:results-hierarchical">'
        "(<strong>sec:results-hierarchical?</strong>)</span>"
    )

    standalone = resolve_reveal_cross_references(content)
    assert "results hierarchical section" in standalone
    assert "sec:" not in standalone
    assert "?" not in standalone

    with pytest.raises(RenderingError, match=r"\[slides\.crossref\.reveal-unresolved\]") as exc_info:
        resolve_reveal_cross_references(content, strict=True)
    assert exc_info.value.context["unresolved_labels"] == ["sec:results-hierarchical"]


@pytest.mark.parametrize(
    "body",
    [
        "[@eq:model; @smith2026]",
        "(<strong>eq:model?</strong>; Smith 2026)",
    ],
)
def test_reveal_mixed_crossref_span_resolves_reference_and_preserves_bibliography(body: str) -> None:
    content = f'<span class="citation" data-cites="eq:model smith2026">{body}</span>'

    resolved = resolve_reveal_cross_references(content, {"eq:model": "7"}, strict=True)

    assert "Equation (7)" in resolved
    assert 'data-cites="smith2026"' in resolved
    assert "@smith2026" in resolved or "Smith 2026" in resolved
    assert "eq:model" not in re.sub(r"<[^>]+>", "", resolved)
    assert reveal_reference_and_math_issues(resolved) == ()


def test_reveal_crossref_suppresses_duplicate_authored_kind() -> None:
    content = (
        '<p>See <span class="citation" data-cites="fig:model">(<strong>fig:model?</strong>)</span>. '
        'Figure <span class="citation" data-cites="fig:model">(<strong>fig:model?</strong>)</span>. '
        'Table <span class="citation" data-cites="tbl:values">(<strong>tbl:values?</strong>)</span>.</p>'
    )

    resolved = resolve_reveal_cross_references(
        content,
        {"fig:model": "7", "tbl:values": "3"},
        strict=True,
    )
    visible = " ".join(re.sub(r"<[^>]+>", "", resolved).split())

    assert visible == "See Figure 7. Figure 7. Table 3."
    assert "Figure Figure" not in visible
    assert "Table Table" not in visible


def test_reveal_citation_crossrefs_handle_authored_parentheses_and_tex_join() -> None:
    content = (
        '<p>Equation (<span class="citation" data-cites="eq:model">'
        "(<strong>eq:model?</strong>)</span>); "
        'identity (<span class="citation" data-cites="eq:model">'
        "(<strong>eq:model?</strong>)</span>); "
        'Figure (<span class="citation" data-cites="fig:model">'
        "(<strong>fig:model?</strong>)</span>); "
        'Section~<span class="citation" data-cites="sec:model">'
        "(<strong>sec:model?</strong>)</span>.</p>"
    )

    resolved = resolve_reveal_cross_references(
        content,
        {"eq:model": "7", "fig:model": "2", "sec:model": "3"},
        strict=True,
    )
    visible = " ".join(re.sub(r"<[^>]+>", "", resolved).split(" "))

    assert visible == "Equation (7); identity (7); Figure (2); Section\N{NO-BREAK SPACE}3."
    assert "Equation Equation" not in visible
    assert "Figure Figure" not in visible
    assert "Section Section" not in visible
    assert "((7))" not in visible
    assert "~" not in visible
    assert reveal_reference_and_math_issues(resolved) == ()


@pytest.mark.parametrize(
    ("identifiers", "body", "expected"),
    [
        (
            "fig:model eq:model",
            "(<strong>fig:model?</strong>; <strong>eq:model?</strong>)",
            "See (Figure 2; Equation 7).",
        ),
        (
            "eq:model eq:second",
            "(<strong>eq:model?</strong>; <strong>eq:second?</strong>)",
            "See (7; 8).",
        ),
    ],
)
def test_reveal_parenthesized_multi_reference_citations_keep_types_unambiguous(
    identifiers: str,
    body: str,
    expected: str,
) -> None:
    content = f'<p>See (<span class="citation" data-cites="{identifiers}">{body}</span>).</p>'

    resolved = resolve_reveal_cross_references(
        content,
        {"fig:model": "2", "eq:model": "7", "eq:second": "8"},
        strict=True,
    )
    visible = re.sub(r"<[^>]+>", "", resolved)

    assert visible == expected
    assert reveal_reference_and_math_issues(resolved) == ()


def test_reveal_mathjax_validation_requires_one_exact_sri_loader() -> None:
    marker = _MATHJAX_CONFIG_SCRIPT
    exact = f'<script src="{MATHJAX_URL}" integrity="{_MATHJAX_INTEGRITY}" crossorigin="anonymous"></script>'
    wrong = f'<script src="{MATHJAX_URL}" integrity="sha384-AAAA" crossorigin="anonymous"></script>'

    assert reveal_reference_and_math_issues(marker + exact) == ()
    assert "exact pinned SRI" in " ".join(reveal_reference_and_math_issues(marker + wrong))
    assert "exactly one pinned MathJax loader" in " ".join(reveal_reference_and_math_issues(marker + exact + exact))
    legacy = (
        f'<script src="{ACCESSIBLE_REVEAL_URL}/plugin/math/math.js"></script>'
        "<script>Reveal.initialize({plugins: [ RevealMath ]});</script>"
    )
    assert "competing legacy RevealMath" in " ".join(reveal_reference_and_math_issues(marker + exact + legacy))

    empty_config = "<script data-template-mathjax-config></script>"
    assert "one canonical MathJax configuration" in " ".join(reveal_reference_and_math_issues(empty_config + exact))
    assert "one canonical MathJax configuration" in " ".join(reveal_reference_and_math_issues(exact + marker))


def test_reveal_mathjax_validation_rejects_nonempty_duplicate_loader_body() -> None:
    exact = f'<script src="{MATHJAX_URL}" integrity="{_MATHJAX_INTEGRITY}" crossorigin="anonymous"></script>'
    competing = f'<script src="{MATHJAX_URL}">ignored</script>'

    issues = reveal_reference_and_math_issues(_MATHJAX_CONFIG_SCRIPT + exact + competing)

    assert "exactly one pinned MathJax loader" in " ".join(issues)

    query_loader = f'<script src="{MATHJAX_URL}?bypass=1"></script>'
    query_issues = reveal_reference_and_math_issues(_MATHJAX_CONFIG_SCRIPT + exact + query_loader)
    assert "exactly one pinned MathJax loader" in " ".join(query_issues)

    duplicate_attribute = exact.replace(
        f'integrity="{_MATHJAX_INTEGRITY}"',
        f'integrity="{_MATHJAX_INTEGRITY}" integrity="sha384-AAAA"',
    )
    attribute_issues = reveal_reference_and_math_issues(_MATHJAX_CONFIG_SCRIPT + duplicate_attribute)
    assert "exact pinned SRI" in " ".join(attribute_issues)


def test_reveal_mathjax_activation_normalizes_existing_loaders(tmp_path: Path) -> None:
    html_file = tmp_path / "deck.html"
    raw = (
        "<html><head>"
        f'<script src="{MATHJAX_URL}" integrity="sha384-AAAA"></script>'
        f'<script defer src="{MATHJAX_URL}?bypass=1"></script>'
        "</head><body></body></html>"
    )
    html_file.write_text(activate_hardened_reveal_mathjax(raw), encoding="utf-8")

    harden_mathjax_script(html_file)

    hardened = html_file.read_text(encoding="utf-8")
    assert hardened.count(MATHJAX_URL) == 1
    assert hardened.count(_MATHJAX_INTEGRITY) == 1
    assert hardened.count("data-template-mathjax-config") == 1
    assert reveal_reference_and_math_issues(hardened) == ()


def test_reveal_mathjax_activation_removes_standalone_plugin_line_without_whitespace_residue() -> None:
    raw = (
        "<html><head>"
        f'<script src="{MATHJAX_URL}"></script>'
        "</head><body>\n"
        f'  <script src="{ACCESSIBLE_REVEAL_URL}/plugin/math/math.js"></script>\n'
        "  <script>Reveal.initialize({plugins: [ RevealMath ]});</script>\n"
        "</body></html>\n"
    )

    activated = activate_hardened_reveal_mathjax(raw)

    assert re.search(r"(?m)^[ \t]+$", activated) is None
    assert "/plugin/math/math.js" not in activated


def test_reveal_math_label_promotion_and_integrity_checks_reject_raw_derivatives() -> None:
    raw = (
        '<span class="math display">$$\\begin{aligned}x&amp;=1\\end{aligned}$$</span> '
        "{#eq:model} "
        '<span class="citation" data-cites="eq:model">(<strong>eq:model?</strong>)</span>'
    )

    promoted = promote_display_math_labels(raw)
    assert 'id="eq:model"' in promoted
    assert "{#eq:model}" not in promoted
    issues = reveal_reference_and_math_issues(promoted)
    assert "Reveal deck contains an unresolved cross-reference placeholder" in issues
    assert "Reveal display math retains literal $$ delimiters" in issues
    assert "Reveal display math contains an unrendered TeX environment without an executable math backend" in issues


def test_accessible_reveal_renderer_discards_output_that_fails_post_render_validation(tmp_path: Path) -> None:
    source = tmp_path / "deck.json"
    source.write_text("{}", encoding="utf-8")
    output = tmp_path / "deck.html"

    def write_invalid_reveal(command: list[str], **_kwargs: object) -> None:
        target = Path(command[command.index("-o") + 1])
        target.write_text(
            "<!doctype html><html><head><title>Invalid</title>"
            '<link rel="stylesheet" href="https://unpkg.com/reveal.js@5.2.1/dist/theme/white.css">'
            '</head><body><div class="reveal"><div class="slides">'
            '<section class="slide level2"><h2>Invalid math</h2><p>\\begin{aligned}x=1\\end{aligned}</p>'
            "</section></div></div><script>Reveal.initialize({keyboard: true});</script></body></html>",
            encoding="utf-8",
        )

    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path),
            slides_dir=str(tmp_path),
            slides_profile="accessible",
        ),
        process_runner=write_invalid_reveal,
    )

    with pytest.raises(RenderingError, match=r"\[slides\.accessibility\.reveal-output\]") as exc_info:
        renderer._render_revealjs(source, output)

    assert "Reveal deck contains a TeX display environment outside a math span" in exc_info.value.context["issues"]
    assert not output.exists()
