"""The cross-reference prefix registry must agree with the shipped formalism filter.

``formalism.lua`` numbers nine block kinds and resolves ``[@prefix:label]``
references to them. Python consumers decide, independently, whether an
``@prefix:label`` key is a cross-reference or a bibliography key: the pre-render
citation validator, the prose-quality citation extractor and the publication
audit's placeholder scan. They used to keep hand-written prefix lists, and those
lists drifted. The validator accepted only ``def``, ``prop`` and ``thm`` of the
formalism kinds, so a manuscript that labelled a remark ``#rem:x`` and cited
``[@rem:x]`` was blocked before Pandoc ran with "Undefined citation key".

The registry in ``infrastructure.rendering._pandoc_filters`` is now the single list. These tests
pin it to the real filter twice: by reading the filter's ``DEFAULT_KINDS`` table
from disk, and by running real pandoc over one block of every registered kind.
A kind added on one side and not the other fails here instead of in a render.

No mocks: every pandoc assertion runs the real binary against the shipped filter,
and each gate carries a negative control showing it can fail.
"""

from __future__ import annotations

import re
import shutil
import subprocess

import pytest

from infrastructure.rendering._pandoc_filters import (
    CROSS_REFERENCE_KEY_PREFIXES,
    CROSS_REFERENCE_PREFIXES,
    EXTERNAL_RESOLVER_PREFIXES,
    FORMALISM_KINDS,
    FORMALISM_LABEL_PREFIXES,
    PANDOC_CROSSREF_PREFIXES,
    FormalismKind,
    formalism_filter_path,
)

PANDOC_FORMAT = "markdown+tex_math_dollars+raw_tex+header_attributes"

_LUA_KINDS_TABLE = re.compile(r"^local DEFAULT_KINDS = \{\n(?P<body>.*?)^\}", re.DOTALL | re.MULTILINE)
_LUA_KIND_ENTRY = re.compile(r'^\s*(?P<css_class>[A-Za-z_]+)\s*=\s*"(?P<title>[^"]*)",?\s*$', re.MULTILINE)


def _lua_default_kinds(source: str) -> dict[str, str]:
    """Return the filter's ``DEFAULT_KINDS`` table as ``{css_class: title}``."""
    table = _LUA_KINDS_TABLE.search(source)
    assert table is not None, "formalism.lua no longer declares a top-level DEFAULT_KINDS table"
    return {entry["css_class"]: entry["title"] for entry in _LUA_KIND_ENTRY.finditer(table["body"])}


def _registry_kinds() -> dict[str, str]:
    return {kind.css_class: kind.title for kind in FORMALISM_KINDS}


def _pandoc(markdown: str, *, to: str = "markdown", extra: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        pytest.skip("pandoc not available on PATH")
    cmd = [pandoc, "--from", PANDOC_FORMAT, "-t", to, f"--lua-filter={formalism_filter_path()}", *(extra or [])]
    return subprocess.run(cmd, input=markdown, text=True, capture_output=True, check=True)


def _kind_id(kind: FormalismKind) -> str:
    return kind.css_class


# ── the registry is the filter's own kind table ──────────────────────────────


def test_registry_matches_the_filter_kind_table() -> None:
    """Every kind the filter numbers is registered, with the same displayed title."""
    lua_kinds = _lua_default_kinds(formalism_filter_path().read_text(encoding="utf-8"))
    # Guard against a parser that silently matches nothing: an empty table on
    # both sides would compare equal.
    assert len(lua_kinds) == len(FORMALISM_KINDS) > 0, lua_kinds
    assert lua_kinds == _registry_kinds()


def test_kind_table_comparison_detects_drift() -> None:
    """NEGATIVE CONTROL — the comparison above fails when the two sides differ."""
    source = formalism_filter_path().read_text(encoding="utf-8")
    dropped = re.sub(r'(?m)^\s*example\s*=\s*"Example",\n', "", source)
    added = source.replace('  example     = "Example",\n', '  example     = "Example",\n  scholium    = "Scholium",\n')
    assert dropped != source and added != source, "fixture edits did not apply to formalism.lua"
    assert _lua_default_kinds(dropped) != _registry_kinds()
    assert _lua_default_kinds(added) != _registry_kinds()


# ── registry shape ───────────────────────────────────────────────────────────


def test_prefix_groups_are_disjoint_and_complete() -> None:
    """A prefix belongs to exactly one resolver, and the union is the published list."""
    groups = (PANDOC_CROSSREF_PREFIXES, FORMALISM_LABEL_PREFIXES, EXTERNAL_RESOLVER_PREFIXES)
    flattened = [prefix for group in groups for prefix in group]
    assert len(flattened) == len(set(flattened)), flattened
    assert CROSS_REFERENCE_PREFIXES == tuple(flattened)
    assert CROSS_REFERENCE_KEY_PREFIXES == tuple(f"{prefix}:" for prefix in flattened)
    assert FORMALISM_LABEL_PREFIXES == tuple(kind.label_prefix for kind in FORMALISM_KINDS)


def test_every_formalism_prefix_is_one_the_filter_can_claim() -> None:
    """The filter recognises a label prefix with Lua's ``^([%a]+):`` — letters only.

    A registered prefix containing a digit, underscore or hyphen would be
    accepted by the Python validators and then never claimed by the filter, so
    its references would reach natbib as undefined citations.
    """
    for prefix in FORMALISM_LABEL_PREFIXES:
        assert re.fullmatch(r"[A-Za-z]+", prefix), prefix


def test_every_formalism_kind_the_issue_named_is_registered() -> None:
    """The kinds that were blocked on 2026-11-24 are now in the shared list."""
    for prefix in ("rem", "lem", "cor", "ax", "claim", "ex"):
        assert prefix in FORMALISM_LABEL_PREFIXES, prefix


# ── behaviour through real pandoc, for every registered kind ─────────────────


@pytest.mark.parametrize("kind", FORMALISM_KINDS, ids=_kind_id)
def test_every_registered_kind_numbers_and_resolves(kind: FormalismKind) -> None:
    """``::: {.<class> #<prefix>:x}`` is numbered and ``[@<prefix>:x]`` resolves to it."""
    label = f"{kind.label_prefix}:central"
    body = f"::: {{.{kind.css_class} #{label}}}\nBody.\n:::\n\nSee [@{label}].\n"

    out = _pandoc(body).stdout
    assert f"**{kind.title} 1.**" in out, out
    assert f"[{kind.title} 1](#{label})" in out, out
    assert "[@" not in out, out

    latex = _pandoc(body, to="latex", extra=["--natbib"]).stdout
    assert f"citep{{{label}}}" not in latex, latex


@pytest.mark.parametrize("kind", FORMALISM_KINDS, ids=_kind_id)
def test_an_undeclared_reference_still_fails_in_the_filter_path(kind: FormalismKind) -> None:
    """NEGATIVE CONTROL — accepting the prefix before Pandoc does not accept every label.

    The validator lets ``@<prefix>:...`` through so the filter can resolve it.
    A label nobody declared must then be reported by the filter, kept visible as
    the author's literal text, and never handed to natbib as a citation.
    """
    missing = f"{kind.label_prefix}:missing"
    body = f"::: {{.{kind.css_class} #{kind.label_prefix}:real}}\nDeclared.\n:::\n\nA typo: [@{missing}].\n"

    result = _pandoc(body, to="latex", extra=["--natbib"])
    assert f"undeclared formalism '{missing}'" in result.stderr, result.stderr
    assert f"citep{{{missing}}}" not in result.stdout, result.stdout
    assert missing in result.stdout, result.stdout
