"""Real offline controls for the prepared untrusted rendering boundary."""

import shutil
import time
from pathlib import Path

import pytest

from infrastructure.core.exceptions import CompilationError, RenderingError
from infrastructure.rendering._untrusted_web import _pandoc
from infrastructure.rendering._web_source_context import source_context_tokens, split_canonical_html
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.pdf_renderer import PDFRenderer
from infrastructure.rendering.pipeline import execute_render_pipeline
from infrastructure.rendering.web_renderer import WebRenderer

_CONFIG = """render:
  formats:
    html: true
    pdf: false
    slides: false
    docx: false
    epub: false
"""


def _project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    root = tmp_path.resolve()
    project = root / "projects" / "template_test"
    manuscript = project / "manuscript"
    manuscript.mkdir(parents=True)
    (manuscript / "config.yaml").write_text(_CONFIG, encoding="utf-8")
    (project / "output").mkdir()
    monkeypatch.setenv("RENDER_SECURITY_PROFILE", "untrusted")
    monkeypatch.setenv("RENDER_UNTRUSTED_TEMP_ROOT", str(project / "output"))
    for name in ("PDF", "HTML", "SLIDES", "DOCX", "EPUB"):
        monkeypatch.delenv(f"ENABLE_{name}", raising=False)
    return root, project


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="real Pandoc is required")
def test_untrusted_stage_three_renders_regular_prepared_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, project = _project(tmp_path, monkeypatch)
    manuscript = project / "manuscript"
    (manuscript / "01 Result.md").write_text(
        "# Opening\n\nPrepared **Markdown** with [a link](https://example.org/) and $x^2$.\n\nSee [@local].\n",
        encoding="utf-8",
    )
    (manuscript / "01-result.md").write_text("# Closing\n\nA second section.\n", encoding="utf-8")
    (manuscript / "local.bib").write_text(
        "@book{local, title={Local Bibliography Fixture}, author={Example, Alex}, year={2026}}\n",
        encoding="utf-8",
    )

    assert execute_render_pipeline("template_test", repo_root=root, skip_manuscript_hydration=True) == 0

    web = project / "output" / "web"
    combined = (web / "index.html").read_text(encoding="utf-8")
    assert "<strong>Markdown</strong>" in combined
    assert 'href="https://example.org/"' in combined
    assert "Local Bibliography Fixture" in combined
    assert "A second section." in combined
    pages = {page: page.read_text(encoding="utf-8") for page in web.glob("*.html") if page.name != "index.html"}
    opening = [page for page, body in pages.items() if "<strong>Markdown</strong>" in body]
    closing = [page for page, body in pages.items() if "A second section." in body]
    assert len(opening) == len(closing) == 1
    assert opening[0].name.casefold() != closing[0].name.casefold()
    assert all("<script" not in body for body in pages.values())
    assert "<math " in combined
    assert "<script" not in combined


@pytest.mark.parametrize("filename", ("01_linked.md", "config.yaml", "linked.bib"))
def test_untrusted_stage_three_refuses_linked_inputs_before_output_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, filename: str
) -> None:
    root, project = _project(tmp_path, monkeypatch)
    manuscript = project / "manuscript"
    (manuscript / "02_regular.md").write_text("# Prepared text\n", encoding="utf-8")
    outside = root / "benign.txt"
    outside.write_text("This fixture is outside the selected manuscript directory.\n", encoding="utf-8")
    linked = manuscript / filename
    linked.unlink(missing_ok=True)
    linked.symlink_to(outside)
    web = project / "output" / "web"
    web.mkdir()
    existing = web / "index.html"
    existing.write_text("prior edition", encoding="utf-8")

    assert execute_render_pipeline("template_test", repo_root=root, skip_manuscript_hydration=True) == 1

    assert existing.read_text(encoding="utf-8") == "prior edition"
    assert list(web.iterdir()) == [existing]


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="real Pandoc is required")
@pytest.mark.parametrize("body", ("<details>Plain text</details>\n", "[Unknown destination](custom:reference)\n"))
def test_direct_untrusted_web_refuses_unsupported_document_before_replacing_output(tmp_path: Path, body: str) -> None:
    root = tmp_path.resolve()
    manuscript = root / "manuscript"
    manuscript.mkdir()
    source = manuscript / "page.md"
    source.write_text(body, encoding="utf-8")
    web = root / "web"
    web.mkdir()
    prior = web / "manuscript__page.html"
    prior.write_text("prior edition", encoding="utf-8")
    renderer = WebRenderer(
        RenderingConfig(
            manuscript_dir=str(manuscript),
            web_dir=str(web),
            security_profile="untrusted",
            untrusted_temp_root=str(root),
        )
    )

    with pytest.raises(RenderingError, match="Untrusted HTML"):
        renderer.render(source)

    assert prior.read_text(encoding="utf-8") == "prior edition"
    assert list(web.iterdir()) == [prior]


@pytest.mark.parametrize(("suffix", "error"), ((".tex", CompilationError), (".md", RenderingError)))
def test_direct_untrusted_pdf_requires_os_sandbox_before_source_read(
    tmp_path: Path, suffix: str, error: type[Exception]
) -> None:
    root = tmp_path.resolve()
    renderer = PDFRenderer(
        RenderingConfig(
            pdf_dir=str(root / "pdf"),
            security_profile="untrusted",
            untrusted_temp_root=str(root),
        )
    )

    with pytest.raises(error, match="operating-system filesystem sandbox"):
        renderer.render(root / f"not-opened{suffix}")

    assert not (root / "pdf").exists()


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="real Pandoc is required")
def test_untrusted_stage_three_refuses_one_unsupported_section_before_publishing_any_page(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, project = _project(tmp_path, monkeypatch)
    manuscript = project / "manuscript"
    (manuscript / "01_regular.md").write_text("# Prepared text\n", encoding="utf-8")
    (manuscript / "02_unsupported.md").write_text("<details>Plain text</details>\n", encoding="utf-8")
    web = project / "output" / "web"
    web.mkdir()
    existing = web / "index.html"
    existing.write_text("prior edition", encoding="utf-8")

    assert execute_render_pipeline("template_test", repo_root=root, skip_manuscript_hydration=True) == 1

    assert existing.read_text(encoding="utf-8") == "prior edition"
    assert list(web.iterdir()) == [existing]


@pytest.mark.parametrize("reason", ("aggregate-bytes", "unresolved-config"))
def test_untrusted_stage_three_refuses_unready_input_roster(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, reason: str
) -> None:
    root, project = _project(tmp_path, monkeypatch)
    manuscript = project / "manuscript"
    if reason == "aggregate-bytes":
        for index in range(9):
            (manuscript / f"{index:02d}_chapter.md").write_bytes(b"p" * (1024 * 1024))
    else:
        (manuscript / "01_regular.md").write_text("# Prepared text\n", encoding="utf-8")
        (manuscript / "config.yaml").write_text(_CONFIG + 'paper:\n  title: "{{PAPER_TITLE}}"\n', encoding="utf-8")

    assert execute_render_pipeline("template_test", repo_root=root, skip_manuscript_hydration=True) == 1
    assert not (project / "output" / "web").exists()


def test_untrusted_stage_three_refuses_project_slot_alias(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, peer = _project(tmp_path, monkeypatch)
    monkeypatch.setenv("RENDER_UNTRUSTED_TEMP_ROOT", str(root))
    (peer / "manuscript" / "01_regular.md").write_text("# A peer project\n", encoding="utf-8")
    (peer.parent / "alias").symlink_to(peer, target_is_directory=True)

    assert execute_render_pipeline("alias", repo_root=root, skip_manuscript_hydration=True) == 1
    assert not (peer / "output" / "web").exists()
    assert list((peer / "output").iterdir()) == []


def test_untrusted_html_refuses_temporary_root_with_linked_ancestor(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    manuscript = root / "manuscript"
    manuscript.mkdir()
    source = manuscript / "page.md"
    source.write_text("# Prepared text\n", encoding="utf-8")
    real = root / "real"
    (real / "scratch").mkdir(parents=True)
    alias = root / "alias"
    alias.symlink_to(real, target_is_directory=True)
    renderer = WebRenderer(
        RenderingConfig(
            manuscript_dir=str(manuscript),
            web_dir=str(alias / "scratch" / "web"),
            security_profile="untrusted",
            untrusted_temp_root=str(alias / "scratch"),
        )
    )

    with pytest.raises(ValueError, match="symlink component"):
        renderer.render(source)
    assert list((real / "scratch").iterdir()) == []


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="real Pandoc is required")
def test_untrusted_pandoc_output_limit_is_applied_to_live_stream(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    config = RenderingConfig(security_profile="untrusted", untrusted_temp_root=str(root))
    with pytest.raises(RenderingError, match="output exceeds its byte budget"):
        _pandoc(
            config,
            ["--from=markdown", "--to=json"],
            b"# Prepared heading\n" * 2000,
            root,
            deadline=time.monotonic() + 20,
            output_limit=128,
        )
    assert list(root.iterdir()) == []


def test_untrusted_html_split_budget_counts_repeated_utf8_shell() -> None:
    bodies = (b"First.", b"Second.")
    (start_one, end_one), (start_two, end_two) = source_context_tokens(bodies)
    rendered = (
        f"<html><head><title>{'é' * 256}</title></head><body>"
        f"<!--{start_one}--><p>First.</p><!--{end_one}-->"
        f"<!--{start_two}--><p>Second.</p><!--{end_two}--></body></html>"
    )
    combined, split = split_canonical_html(rendered, bodies)
    exact = len(combined.encode()) + sum(len(page.encode()) for page in split)
    assert split_canonical_html(rendered, bodies, byte_limit=exact) == (combined, split)
    with pytest.raises(RenderingError, match="publication exceeds its aggregate byte budget"):
        split_canonical_html(rendered, bodies, byte_limit=exact - 1)
