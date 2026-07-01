"""Regression test: every default documented in the project README must
match the value the loader actually returns from ``manuscript/config.yaml``.

This test is the safety net for the failure mode that triggered the
audit which produced this file: the README was left behind when the
default config was retuned (e.g. ``max_results: 25 → 12``,
``llm.enabled: true → false``), and downstream readers were getting
factually-wrong defaults from the README.

The test intentionally checks **defaults** (i.e. the values that ship in
the bundled config) rather than scanning every possible config the
loader could emit — that scan is covered by ``test_config.py``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Documented (Section, Key, expected default) tuples. The loader is
# imported lazily so the test surfaces a clear ImportError if `src/` is
# misconfigured.


def _load_config():
    from src.config import load_project_config

    return load_project_config(PROJECT_ROOT / "manuscript" / "config.yaml")


def _readme_text() -> str:
    return (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")


# Each tuple: (markdown row pattern that must appear, expected truthy assertion).
# The pattern is a Pandoc table row containing the key + the documented
# default, written as the README does (back-tick quoted code spans).
@pytest.mark.parametrize(
    "section,key,attr_path,expected_repr",
    [
        # search:
        ("search", "query", "search.query", '`"reproducible research optimization"`'),
        ("search", "max_results", "search.max_results", "`100`"),
        ("search", "sources", "search.sources", "`[local]`"),
        ("search", "local_corpus", "search.local_corpus", "`data/corpus.json`"),
        ("search", "crossref_mailto", "search.crossref_mailto", "`you@example.org`"),
        ("search", "paperclip", "search.paperclip", "`false`"),
        ("search", "cache_dir", "search.cache_dir", "`output/search/cache`"),
        # enrichment:
        ("enrichment", "fetch_abstracts", "enrichment.fetch_abstracts", "`true`"),
        ("enrichment", "fetch_fulltext", "enrichment.fetch_fulltext", "`false`"),
        ("enrichment", "abstract_cache_dir", "enrichment.abstract_cache_dir", "`output/cache/abs`"),
        ("enrichment", "fulltext_cache_dir", "enrichment.fulltext_cache_dir", "`output/cache/pdf`"),
        ("enrichment", "max_fulltext_chars", "enrichment.max_fulltext_chars", "`400000`"),
        # llm:
        ("llm", "enabled", "llm.enabled", "`false`"),
        ("llm", "model", "llm.model", "`gemma3:4b`"),
        ("llm", "temperature", "llm.temperature", "`0.0`"),
        ("llm", "seed", "llm.seed", "`42`"),
        ("llm", "per_paper", "llm.per_paper", "`true`"),
        ("llm", "corpus_synthesis", "llm.corpus_synthesis", "`true`"),
        ("llm", "output_dir", "llm.output_dir", "`output/llm`"),
        ("llm", "context_window", "llm.context_window", "`131072`"),
        ("llm", "long_max_tokens", "llm.long_max_tokens", "`16384`"),
        ("llm", "max_input_length", "llm.max_input_length", "`600000`"),
        ("llm", "review_timeout", "llm.review_timeout", "`600.0`"),
        # report:
        ("report", "output_path", "report.output_path", "`output/reading_report.md`"),
        ("report", "include_per_paper", "report.include_per_paper", "`true`"),
        ("report", "include_corpus_synthesis", "report.include_corpus_synthesis", "`true`"),
        # deep_search:
        ("deep_search", "enabled", "deep_search.enabled", "`true`"),
        ("deep_search", "max_results_per_keyword", "deep_search.max_results_per_keyword", "`100`"),
        ("deep_search", "fetch_abstracts", "deep_search.fetch_abstracts", "`true`"),
        ("deep_search", "fetch_fulltext", "deep_search.fetch_fulltext", "`true`"),
        ("deep_search", "max_fulltext_chars", "deep_search.max_fulltext_chars", "`400000`"),
        ("deep_search", "llm_per_paper", "deep_search.llm_per_paper", "`true`"),
        ("deep_search", "llm_model", "deep_search.llm_model", "`gemma3:4b`"),
        ("deep_search", "output_dir", "deep_search.output_dir", "`output/deep_search`"),
        ("deep_search", "write_unified_bibtex", "deep_search.write_unified_bibtex", "`true`"),
        ("deep_search", "unified_bibtex_path", "deep_search.unified_bibtex_path", "`manuscript/references_deep.bib`"),
        # top-level
        ("top", "references_path", "references_path", "`manuscript/references.bib`"),
    ],
)
def test_readme_documented_default_matches_loader(section: str, key: str, attr_path: str, expected_repr: str) -> None:
    """The README cell for ``key`` must literally contain the value the
    loader returns for the matching attribute on the ``ProjectConfig``.

    This catches drift in either direction (README updated but loader
    not, or loader retuned but README forgotten).
    """
    cfg = _load_config()
    obj = cfg
    for piece in attr_path.split("."):
        obj = getattr(obj, piece)

    # Render the live value into the same surface form the README uses.
    if isinstance(obj, bool):
        live_repr = f"`{str(obj).lower()}`"
    elif isinstance(obj, list):
        live_repr = f"`[{', '.join(obj)}]`"
    elif isinstance(obj, str) and obj == "reproducible research optimization":
        live_repr = '`"reproducible research optimization"`'
    else:
        live_repr = f"`{obj}`"

    assert live_repr == expected_repr, (
        f"Loader returned {live_repr} for {attr_path}, but the test "
        f"expected {expected_repr}. Update the test parametrisation OR "
        f"update the bundled config; the README and the loader must agree."
    )

    readme = _readme_text()
    # The README should mention `key` and `expected_repr` on the same line.
    pattern = re.compile(
        r"^\|\s*`" + re.escape(key) + r"`\s*\|\s*" + re.escape(expected_repr) + r"\s*\|",
        re.MULTILINE,
    )
    assert pattern.search(readme), (
        f"README.md is missing a config-table row for `{key}` with default "
        f"{expected_repr}. Add a row of the form:\n"
        f"  | `{key}` | {expected_repr} | <description> |\n"
    )


def test_readme_does_not_advertise_obsolete_defaults() -> None:
    """Catch the historical drift where the README claimed defaults that
    the loader has since changed."""
    readme = _readme_text()
    obsolete_strings = [
        # The historic but now-incorrect defaults.
        "`max_results` | `25`",  # was 25, now 12
        "`sources` | `[arxiv, crossref]`",  # was [arxiv, crossref], now [local]
    ]
    for needle in obsolete_strings:
        assert needle not in readme, (
            f"README.md still contains the obsolete default {needle!r}; "
            f"update the config table to match `manuscript/config.yaml`."
        )
    # `llm.enabled` is `false` by default — guard against the stale
    # `enabled | true` claim returning under the `llm:` heading. We
    # locate the `llm:` subsection of the table and only flag that scope
    # (the `deep_search:` table also has an `enabled` row whose default
    # IS `true`, which is correct).
    llm_section = re.split(r"^### `[a-z_]+:`", readme, flags=re.MULTILINE)
    # llm_section[i] is the body that follows the i-th heading; we want
    # the body that begins with the `enabled` row inherited from the
    # `llm:` heading, identified by the presence of `model | `gemma3:4b``.
    llm_bodies = [body for body in llm_section if "`gemma3:4b`" in body and "Ollama-local" in body]
    if llm_bodies:
        llm_body = llm_bodies[0]
        assert "| `enabled` | `true` |" not in llm_body, (
            "README.md still claims `llm.enabled` defaults to `true`; the "
            "bundled config has `enabled: false` for CI safety."
        )
