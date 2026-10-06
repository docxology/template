"""Actual HTTP/cache parity and no-follow nominated-project boundaries."""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

import pytest
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
from pytest_httpserver import HTTPServer

from infrastructure.search.literature import (
    AbstractFetcher,
    FulltextFetcher,
    Paper,
    SearchCache,
    SearchQuery,
    SearchResult,
)
from infrastructure.search.literature.fulltext import write_corpus

ATOM = '<feed xmlns="http://www.w3.org/2005/Atom"><entry><summary>Controlled source abstract.</summary></entry></feed>'


def _pdf() -> bytes:
    writer = PdfWriter()
    page = writer.add_blank_page(width=200, height=200)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})}
    )
    stream = DecodedStreamObject()
    stream.set_data(b"BT /F1 12 Tf 15 150 Td (Controlled source text.) Tj ET")
    page[NameObject("/Contents")] = writer._add_object(stream)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def _search_result() -> SearchResult:
    return SearchResult(
        query=SearchQuery(text="controlled"),
        papers=[Paper(id="arxiv:1", title="Controlled")],
        per_source_counts={"local": 1},
    )


def test_confined_search_cache_payload_hit_expiry_and_clear_parity(tmp_path: Path):
    generic = SearchCache(tmp_path / "ordinary")
    confined = SearchCache("output/cache", confinement_root=tmp_path)
    result = _search_result()
    for cache in (generic, confined):
        assert cache.get(result.query) is None
        path = cache.put(result)
        assert cache.get(result.query).to_dict() == result.to_dict()
        payload = json.loads(path.read_text())
        payload["_cached_at"] = 0
        path.write_text(json.dumps(payload))
        assert (
            SearchCache(path.parent, ttl_seconds=1, confinement_root=cache.confinement_root).get(result.query) is None
        )
        assert cache.clear() == 1
        assert cache.get(result.query) is None
    left = json.loads(generic.put(result).read_text())
    right = json.loads(confined.put(result).read_text())
    assert {k: v for k, v in left.items() if k != "_cached_at"} == {k: v for k, v in right.items() if k != "_cached_at"}


def test_actual_http_abstract_and_pdf_content_and_cache_parity(httpserver: HTTPServer, tmp_path: Path):
    payload = _pdf()
    httpserver.expect_request("/atom").respond_with_data(ATOM, content_type="application/atom+xml")
    httpserver.expect_request("/paper.pdf").respond_with_data(payload, content_type="application/pdf")
    abstracts = []
    fulltexts = []
    for name, root in (("ordinary", None), ("confined", tmp_path)):
        abstract = AbstractFetcher(
            cache_dir=tmp_path / name / "abstract", arxiv_base_url=httpserver.url_for("/atom"), confinement_root=root
        )
        fulltext = FulltextFetcher(cache_dir=tmp_path / name / "fulltext", confinement_root=root)
        paper = Paper(id="arxiv:1", title="Controlled", pdf_url=httpserver.url_for("/paper.pdf"))
        assert abstract.fetch(paper).status == "hit"
        assert fulltext.fetch(paper).status == "hit"
        assert (tmp_path / name / "fulltext/arxiv_1.pdf").read_bytes() == payload
        abstracts.append(paper.abstract)
        fulltexts.append(paper.fulltext)
        httpserver.check_assertions()
        cached = Paper(id="arxiv:1", title="Controlled")
        assert abstract.fetch(cached).status == "cached"
        assert fulltext.fetch(cached).status == "cached"
        assert cached.abstract == paper.abstract
        assert cached.fulltext == paper.fulltext
    assert abstracts == ["Controlled source abstract."] * 2
    assert fulltexts == ["Controlled source text."] * 2
    httpserver.clear()
    assert (
        AbstractFetcher(cache_dir=tmp_path / "confined/abstract", confinement_root=tmp_path)
        .fetch(Paper(id="arxiv:1", title="Cached"))
        .status
        == "cached"
    )
    assert (
        FulltextFetcher(cache_dir=tmp_path / "confined/fulltext", confinement_root=tmp_path)
        .fetch(Paper(id="arxiv:1", title="Cached"))
        .status
        == "cached"
    )


def _linked_boundary(tmp_path: Path, alias: str) -> tuple[Path, Path, Path]:
    real_parent = tmp_path / "actual-parent"
    real_root = real_parent / "project"
    real_root.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "authored.txt").write_text("authored source")
    root = real_root
    if alias == "ancestor":
        linked = tmp_path / "linked-parent"
        linked.symlink_to(real_parent, target_is_directory=True)
        root = linked / "project"
    elif alias == "root":
        root = tmp_path / "linked-project"
        root.symlink_to(real_root, target_is_directory=True)
    elif alias == "output":
        (root / "output").symlink_to(outside, target_is_directory=True)
    else:
        (root / "output").mkdir()
        (root / "output/cache").symlink_to(outside, target_is_directory=True)
    return root, root / "output/cache", outside


@pytest.mark.parametrize("alias", ["ancestor", "root", "output", "cache"])
@pytest.mark.parametrize("family", ["search", "abstract", "fulltext"])
def test_linked_cache_boundary_refuses_before_external_file_side_effect(tmp_path: Path, alias: str, family: str):
    root, cache_dir, outside = _linked_boundary(tmp_path, alias)
    before = {path.name: path.read_bytes() for path in outside.iterdir()}
    with pytest.raises(ValueError, match="[Ss]ymlink|real directory"):
        if family == "search":
            SearchCache(cache_dir, confinement_root=root).put(_search_result())
        elif family == "abstract":
            AbstractFetcher(cache_dir=cache_dir, confinement_root=root).fetch(Paper(id="x", title="No network source"))
        else:
            FulltextFetcher(cache_dir=cache_dir, confinement_root=root).fetch(Paper(id="x", title="No network source"))
    assert {path.name: path.read_bytes() for path in outside.iterdir()} == before
    assert not (outside / "cache").exists()
    assert (
        not (real_output := tmp_path / "actual-parent/project/output").exists()
        or real_output.is_symlink()
        or alias == "cache"
    )


@pytest.mark.parametrize("operation", ["get", "put", "clear"])
def test_search_cache_leaf_symlink_is_not_read_replaced_or_deleted(tmp_path: Path, operation: str):
    cache = SearchCache("output/cache", confinement_root=tmp_path)
    target = cache.path_for(_search_result().query)
    target.parent.mkdir(parents=True)
    authored = tmp_path / "authored.json"
    authored.write_text(_search_result().to_json())
    original = authored.read_bytes()
    target.symlink_to(authored)
    with pytest.raises((ValueError, OSError), match="[Ss]ymlink|symbolic links"):
        if operation == "get":
            cache.get(_search_result().query)
        elif operation == "put":
            cache.put(_search_result())
        else:
            cache.clear()
    assert authored.read_bytes() == original
    assert target.is_symlink()


@pytest.mark.parametrize(
    "family,leaf", [("abstract", "abs_arxiv_1.txt"), ("fulltext", "arxiv_1.txt"), ("fulltext", "arxiv_1.pdf")]
)
@pytest.mark.parametrize("force", [False, True])
def test_actual_http_fetch_refuses_symlink_cache_leaf(
    httpserver: HTTPServer, tmp_path: Path, family: str, leaf: str, force: bool
):
    cache = tmp_path / "output/cache"
    cache.mkdir(parents=True)
    authored = tmp_path / "authored.bin"
    authored.write_bytes(b"authored exact bytes")
    (cache / leaf).symlink_to(authored)
    httpserver.expect_request("/atom").respond_with_data(ATOM)
    httpserver.expect_request("/paper.pdf").respond_with_data(_pdf(), content_type="application/pdf")
    with pytest.raises((ValueError, OSError), match="[Ss]ymlink|symbolic links"):
        if family == "abstract":
            AbstractFetcher(
                cache_dir=cache, confinement_root=tmp_path, arxiv_base_url=httpserver.url_for("/atom")
            ).fetch(Paper(id="arxiv:1", title="Controlled"), force=force)
        else:
            FulltextFetcher(cache_dir=cache, confinement_root=tmp_path).fetch(
                Paper(id="arxiv:1", title="Controlled", pdf_url=httpserver.url_for("/paper.pdf")), force=force
            )
    assert authored.read_bytes() == b"authored exact bytes"
    assert (cache / leaf).is_symlink()


@pytest.mark.parametrize("factory", [SearchCache, AbstractFetcher, FulltextFetcher])
def test_cache_nomination_rejects_lexical_escape_before_io(tmp_path: Path, factory):
    with pytest.raises(ValueError, match="escapes nominated"):
        factory(cache_dir=tmp_path.parent / "outside", confinement_root=tmp_path)
    with pytest.raises(ValueError, match="escapes nominated"):
        factory(cache_dir="output/../outside", confinement_root=tmp_path)


def test_confined_corpus_writer_exact_bytes_and_linked_parent_refusal(tmp_path: Path):
    path = tmp_path / "output/corpus.json"
    write_corpus(_search_result().papers, path, confinement_root=tmp_path)
    assert json.loads(path.read_text())["papers"] == [paper.to_dict() for paper in _search_result().papers]
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "linked").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="[Ss]ymlink"):
        write_corpus([], tmp_path / "linked/corpus.json", confinement_root=tmp_path)
    assert not list(outside.iterdir())
