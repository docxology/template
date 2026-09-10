"""Web/HTML figure alt-text registry wiring tests (split from test_figure_alt_wiring.py)."""

from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path
import pytest
from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.web_renderer import WebRenderer
from ._figure_alt_helpers import (
    _render_figure_html,
)


@pytest.mark.parametrize(
    "registry_payload",
    [
        {
            "fig:dense": {
                "label": "fig:dense",
                "filename": "dense.png",
                "metadata": {
                    "alt_text": (
                        "Three blue trajectories descend at different rates; amber uncertainty bands narrow "
                        "after iteration 40, while the dashed baseline remains flat."
                    )
                },
            }
        },
        {
            "schema_version": "figure-registry-v1",
            "figures": [
                {
                    "label": "fig:dense",
                    "path": "dense.png",
                    "alt": (
                        "Three blue trajectories descend at different rates; amber uncertainty bands narrow "
                        "after iteration 40, while the dashed baseline remains flat."
                    ),
                }
            ],
        },
        {
            "schema_version": "figure-registry-v1",
            "figures": [
                {
                    "label": "fig:dense",
                    "path": "dense.png",
                    "alt_text": (
                        "Three blue trajectories descend at different rates; amber uncertainty bands narrow "
                        "after iteration 40, while the dashed baseline remains flat."
                    ),
                }
            ],
        },
    ],
    ids=["metadata-alt-text", "top-level-alt", "canonical-top-level-alt-text"],
)
def test_source_owned_registry_alt_reaches_real_combined_html(
    tmp_path: Path,
    registry_payload: object,
) -> None:
    rich_alt = (
        "Three blue trajectories descend at different rates; amber uncertainty bands narrow "
        "after iteration 40, while the dashed baseline remains flat."
    )

    rendered = _render_figure_html(tmp_path, registry_payload)

    assert f'alt="{html.escape(rich_alt, quote=True)}"' in rendered
    assert 'src="../figures/dense.png"' in rendered
    expected_caption = "Figure 1: Short visible caption" if shutil.which("pandoc-crossref") else "Short visible caption"
    assert f"<figcaption>{expected_caption}</figcaption>" in re.sub(r"\s+", " ", rendered)
    assert 'alt="Short visible caption"' not in rendered


def test_registry_replacement_uses_exact_alt_and_src_attributes(tmp_path: Path) -> None:
    registry_path = tmp_path / "figure_registry.json"
    rich_alt = "Three blue trajectories descend while amber intervals narrow."
    registry_path.write_text(
        json.dumps({"fig:dense": {"filename": "dense.png", "alt": rich_alt}}),
        encoding="utf-8",
    )
    html_file = tmp_path / "index.html"
    html_file.write_text(
        '<html><body><figure id="fig:dense"><img '
        'data-fig-alt="Preserve this provenance attribute." '
        'data-src="../figures/decoy.png" src="figures/dense.png" '
        'alt="Short visible caption"><figcaption>Visible caption.</figcaption>'
        "</figure></body></html>",
        encoding="utf-8",
    )

    WebRenderer._enhance_accessibility(html_file, registry_path=registry_path)

    rendered = html_file.read_text(encoding="utf-8")
    assert 'data-fig-alt="Preserve this provenance attribute."' in rendered
    assert 'data-src="../figures/decoy.png"' in rendered
    assert f'alt="{rich_alt}"' in rendered
    assert 'src="../figures/dense.png"' in rendered
    assert 'alt="Short visible caption"' not in rendered


def test_registry_long_description_is_associated_escaped_and_idempotent(tmp_path: Path) -> None:
    registry_path = tmp_path / "figure_registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "fig:dense": {
                    "filename": "dense.png",
                    "alt": "A square-marked trajectory rises above a dotted reference.",
                    "long_description": (
                        "Panel A reads from left to right & distinguishes square and circle markers.\n\n"
                        "The bounded fixture does not establish <universal> performance."
                    ),
                }
            }
        ),
        encoding="utf-8",
    )
    html_file = tmp_path / "index.html"
    html_file.write_text(
        '<html><body><figure id="fig:dense"><img src="../figures/dense.png" '
        'alt="Visible caption"><figcaption>Visible caption.</figcaption></figure></body></html>',
        encoding="utf-8",
    )

    WebRenderer._enhance_accessibility(html_file, registry_path=registry_path)
    WebRenderer._enhance_accessibility(html_file, registry_path=registry_path)

    rendered = html_file.read_text(encoding="utf-8")
    assert rendered.count('class="figure-long-description"') == 1
    assert 'id="fig-dense-long-description"' in rendered
    assert 'aria-details="fig-dense-long-description"' in rendered
    assert "aria-describedby" not in rendered
    assert "left to right &amp; distinguishes" in rendered
    assert "&lt;universal&gt; performance" in rendered
    assert rendered.count("<p>") == 2


def test_registry_v12_exact_values_are_linked_contextually_and_idempotently(
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "figure_registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "schema_version": "1.2",
                "generated_by": "source-owned-test-producer",
                "exact_value_artifact": {
                    "json_path": "output/figures/figure_exact_values.json",
                    "markdown_path": "output/figures/figure_exact_values.md",
                    "identifiers": ["fig-values:dense"],
                },
                "figures": [
                    {
                        "label": "fig:dense",
                        "filename": "dense.png",
                        "alt_text": "A square-marked trajectory rises above a dotted reference.",
                        "long_description": "The panel reads from left to right.",
                        "exact_value_fallback": "fig-values:dense",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    html_file = tmp_path / "index.html"
    html_file.write_text(
        '<html><body><figure id="fig:dense"><img src="../figures/dense.png" '
        'alt="Visible caption"><figcaption>Figure 4: Dense result.</figcaption></figure></body></html>',
        encoding="utf-8",
    )

    WebRenderer._enhance_accessibility(html_file, registry_path=registry_path)
    WebRenderer._enhance_accessibility(html_file, registry_path=registry_path)

    rendered = html_file.read_text(encoding="utf-8")
    assert rendered.count('class="figure-long-description"') == 1
    assert rendered.count('class="figure-exact-values"') == 1
    assert 'href="../figures/figure_exact_values.md#fig-values-dense"' in rendered
    assert "Open exact values for figure dense (fig-values:dense)" in rendered


@pytest.mark.parametrize(
    ("artifact", "fallback", "message"),
    [
        (
            {
                "json_path": "output/figures/figure_exact_values.json",
                "markdown_path": "../../private.md",
                "identifiers": ["fig-values:dense"],
            },
            "fig-values:dense",
            "must remain under output/figures",
        ),
        (
            {
                "json_path": "output/figures/figure_exact_values.json",
                "markdown_path": "output/figures/%2e%2e/private.md",
                "identifiers": ["fig-values:dense"],
            },
            "fig-values:dense",
            "encoded path segments",
        ),
        (
            {
                "json_path": "output/figures/figure_exact_values.json",
                "markdown_path": "output/figures/figure_exact_values.md",
                "identifiers": ["fig-values:other"],
            },
            "fig-values:dense",
            "identifiers do not match",
        ),
    ],
)
def test_registry_v12_rejects_unsafe_or_mismatched_exact_value_artifacts(
    tmp_path: Path,
    artifact: dict[str, object],
    fallback: str,
    message: str,
) -> None:
    registry_path = tmp_path / "figure_registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "schema_version": "1.2",
                "exact_value_artifact": artifact,
                "figures": [
                    {
                        "label": "fig:dense",
                        "filename": "dense.png",
                        "alt_text": "A meaningful concise alternative.",
                        "exact_value_fallback": fallback,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    html_file = tmp_path / "index.html"
    html_file.write_text(
        '<html><body><figure id="fig:dense"><img src="../figures/dense.png" '
        'alt="Visible caption"><figcaption>Caption.</figcaption></figure></body></html>',
        encoding="utf-8",
    )

    with pytest.raises(RenderingError, match=message):
        WebRenderer._enhance_accessibility(html_file, registry_path=registry_path)


def test_registry_rejects_conflicting_long_description_fields(tmp_path: Path) -> None:
    registry_path = tmp_path / "figure_registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "fig:dense": {
                    "filename": "dense.png",
                    "alt": "A meaningful concise alternative.",
                    "long_description": "Top-level reading order.",
                    "metadata": {"long_description": "Different nested reading order."},
                }
            }
        ),
        encoding="utf-8",
    )
    html_file = tmp_path / "index.html"
    html_file.write_text(
        '<html><body><figure id="fig:dense"><img src="../figures/dense.png" '
        'alt="Visible caption"><figcaption>Visible caption.</figcaption></figure></body></html>',
        encoding="utf-8",
    )

    with pytest.raises(RenderingError, match="conflicting long-description fields"):
        WebRenderer._enhance_accessibility(html_file, registry_path=registry_path)


def test_registry_replacement_preserves_latex_backslashes_in_alt(tmp_path: Path) -> None:
    """Registry alt text with LaTeX backslashes must not break re.sub replacement."""
    registry_path = tmp_path / "figure_registry.json"
    rich_alt = r"Phase portrait with \Omega resistance and \delta perturbation."
    registry_path.write_text(
        json.dumps({"fig:dense": {"filename": "dense.png", "alt": rich_alt}}),
        encoding="utf-8",
    )
    html_file = tmp_path / "index.html"
    html_file.write_text(
        '<html><body><figure id="fig:dense"><img src="figures/dense.png" '
        'alt="Short visible caption"><figcaption>Visible caption.</figcaption>'
        "</figure></body></html>",
        encoding="utf-8",
    )

    WebRenderer._enhance_accessibility(html_file, registry_path=registry_path)

    rendered = html_file.read_text(encoding="utf-8")
    assert f'alt="{html.escape(rich_alt, quote=True)}"' in rendered
    assert 'alt="Short visible caption"' not in rendered


def test_labelled_html_figure_rejects_duplicate_registry_filename_owners(tmp_path: Path) -> None:
    registry_path = tmp_path / "figure_registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "fig:dense": {"filename": "shared.png", "alt": "Dense description."},
                "fig:other": {"filename": "shared.png", "alt": "Other description."},
            }
        ),
        encoding="utf-8",
    )
    html_file = tmp_path / "index.html"
    html_file.write_text(
        '<html><body><figure id="fig:dense"><img src="../figures/shared.png" '
        'alt="Authored description."><figcaption>Caption.</figcaption></figure></body></html>',
        encoding="utf-8",
    )

    with pytest.raises(RenderingError, match="multiple registry records"):
        WebRenderer._enhance_accessibility(html_file, registry_path=registry_path)


def test_unlabelled_figure_without_registry_match_preserves_authored_alt(tmp_path: Path) -> None:
    registry_path = tmp_path / "figure_registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "fig:canonical": {
                    "filename": "canonical.png",
                    "alt": "Canonical figure description.",
                }
            }
        ),
        encoding="utf-8",
    )
    html_file = tmp_path / "index.html"
    html_file.write_text(
        '<html><body><figure><img src="../figures/authored.png" '
        'alt="Authored figure description."><figcaption>Authored figure.</figcaption>'
        "</figure></body></html>",
        encoding="utf-8",
    )

    WebRenderer._enhance_accessibility(html_file, registry_path=registry_path)

    rendered = html_file.read_text(encoding="utf-8")
    assert 'alt="Authored figure description."' in rendered
    assert "Canonical figure description." not in rendered
    assert 'id="fig:' not in rendered


def test_registry_alt_reaches_combined_html_from_hydrated_manuscript_tree(tmp_path: Path) -> None:
    project = tmp_path / "project"
    manuscript_dir = project / "output" / "manuscript"
    figures_dir = project / "output" / "figures"
    web_dir = project / "output" / "web"
    manuscript_dir.mkdir(parents=True)
    figures_dir.mkdir(parents=True)
    source = manuscript_dir / "03_results.md"
    source.write_text(
        "# Results\n\n![Short caption](../figures/dense.png){#fig:dense}\n",
        encoding="utf-8",
    )
    (figures_dir / "dense.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    rich_alt = "Three blue trajectories descend while amber uncertainty bands narrow after iteration 40."
    (figures_dir / "figure_registry.json").write_text(
        json.dumps(
            {
                "fig:dense": {
                    "filename": "dense.png",
                    "metadata": {"alt_text": rich_alt},
                }
            }
        ),
        encoding="utf-8",
    )
    renderer = WebRenderer(
        RenderingConfig(
            output_dir=str(project / "output"),
            figures_dir=str(figures_dir),
            web_dir=str(web_dir),
        )
    )

    rendered = renderer.render_combined([source], manuscript_dir, "test").read_text(encoding="utf-8")

    assert f'alt="{rich_alt}"' in rendered
    assert 'src="../figures/dense.png"' in rendered
    assert "output/output/figures" not in rendered


def test_present_registry_label_with_mismatched_path_fails_render(tmp_path: Path) -> None:
    registry = {
        "fig:dense": {
            "label": "fig:dense",
            "filename": "different.png",
            "metadata": {"alt_text": "A meaningful description."},
        }
    }

    with pytest.raises(RenderingError, match="path does not match"):
        _render_figure_html(tmp_path, registry)


def test_registry_filename_match_without_rendered_label_fails(tmp_path: Path) -> None:
    registry_path = tmp_path / "figure_registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "fig:dense": {
                    "filename": "dense.png",
                    "metadata": {"alt_text": "A meaningful description."},
                }
            }
        ),
        encoding="utf-8",
    )
    html_file = tmp_path / "index.html"
    html_file.write_text(
        '<html><body><figure><img src="../figures/dense.png" alt="Authored description.">'
        "<figcaption>Visible caption.</figcaption></figure></body></html>",
        encoding="utf-8",
    )

    with pytest.raises(RenderingError, match="label/path mismatch"):
        WebRenderer._enhance_accessibility(html_file, registry_path=registry_path)


def test_present_registry_path_with_mismatched_label_fails_render(tmp_path: Path) -> None:
    registry = {
        "fig:other": {
            "label": "fig:other",
            "filename": "dense.png",
            "metadata": {"alt_text": "A meaningful description."},
        }
    }

    with pytest.raises(RenderingError, match="label/path mismatch"):
        _render_figure_html(tmp_path, registry)


def test_present_registry_record_with_blank_alt_fails_render(tmp_path: Path) -> None:
    registry = {
        "fig:dense": {
            "label": "fig:dense",
            "filename": "dense.png",
            "metadata": {"alt_text": "   "},
        }
    }

    with pytest.raises(RenderingError, match="missing accessibility alt text"):
        _render_figure_html(tmp_path, registry)


@pytest.mark.parametrize(
    "filename",
    [
        "../secret.png",
        "/tmp/secret.png",
        "../figures/../secret.png",
        "figures/nested/../../secret.png",
        "dense.png?download=1",
        "dense.png#fragment",
    ],
)
def test_unsafe_registry_figure_path_fails_render(tmp_path: Path, filename: str) -> None:
    registry = {
        "fig:dense": {
            "label": "fig:dense",
            "filename": filename,
            "metadata": {"alt_text": "A meaningful description."},
        }
    }

    with pytest.raises(RenderingError, match="safe relative filename/path"):
        _render_figure_html(tmp_path, registry)


@pytest.mark.parametrize(
    "registry",
    [
        {"figures": {"label": "fig:dense"}},
        {"figures": [None]},
        [{"filename": "dense.png", "alt": "A description."}],
        {"not-a-figure": {"filename": "dense.png", "alt": "A description."}},
        {"fig:dense": {"label": "fig:dense", "alt": "A description."}},
    ],
)
def test_malformed_present_registry_fails_instead_of_degrading_to_authored_alt(
    tmp_path: Path,
    registry: object,
) -> None:
    with pytest.raises(RenderingError):
        _render_figure_html(tmp_path, registry)


def test_unregistered_figure_retains_nonblank_authored_alt_instead_of_caption(tmp_path: Path) -> None:
    html_file = tmp_path / "index.html"
    html_file.write_text(
        '<html><body><figure id="fig:authored"><img src="../figures/authored.png" '
        'alt="Author describes a steep blue curve."><figcaption>'
        "Figure 7: A short publication caption.</figcaption></figure></body></html>",
        encoding="utf-8",
    )

    WebRenderer._enhance_accessibility(html_file, registry_path=tmp_path / "missing-registry.json")

    rendered = html_file.read_text(encoding="utf-8")
    assert 'alt="Author describes a steep blue curve."' in rendered
    assert 'alt="Figure 7: A short publication caption."' not in rendered


def test_unregistered_cross_referenced_figure_with_blank_authored_alt_fails(tmp_path: Path) -> None:
    html_file = tmp_path / "index.html"
    html_file.write_text(
        '<html><body><figure id="fig:blank"><img src="../figures/blank.png" alt="">'
        "<figcaption>A non-decorative, cross-referenced result.</figcaption></figure></body></html>",
        encoding="utf-8",
    )

    with pytest.raises(RenderingError, match="blank authored alt text"):
        WebRenderer._enhance_accessibility(html_file, registry_path=tmp_path / "missing-registry.json")


def test_unlabelled_registry_reuse_gets_explicit_decorative_empty_alt(tmp_path: Path) -> None:
    registry_path = tmp_path / "figure_registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "fig:dense": {
                    "filename": "dense.png",
                    "metadata": {"alt_text": "Canonical long description for the labelled occurrence."},
                }
            }
        ),
        encoding="utf-8",
    )
    html_file = tmp_path / "index.html"
    html_file.write_text(
        '<html><body><p><img src="figures/dense.png"></p>'
        '<p><em>Reproduced from <a href="#fig:dense">Figure 2</a>.</em></p></body></html>',
        encoding="utf-8",
    )

    WebRenderer._enhance_accessibility(html_file, registry_path=registry_path)

    rendered = html_file.read_text(encoding="utf-8")
    assert '<img src="../figures/dense.png" alt=""' in rendered
    assert "Canonical long description" not in rendered


def test_unregistered_image_without_alt_fails_instead_of_becoming_decorative(tmp_path: Path) -> None:
    html_file = tmp_path / "index.html"
    html_file.write_text(
        '<html><body><p><img src="../figures/unknown.png"></p></body></html>',
        encoding="utf-8",
    )

    with pytest.raises(RenderingError, match="missing authored alt text"):
        WebRenderer._enhance_accessibility(html_file, registry_path=tmp_path / "missing-registry.json")
