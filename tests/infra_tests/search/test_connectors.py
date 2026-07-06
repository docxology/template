"""Tests for infrastructure.search.connectors.

Covers: types, registry, HTTP client (offline), config, connector hit
serialisation, and all 8 built-in connectors (parsing logic, no network).
"""

from __future__ import annotations

import json
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from infrastructure.search.connectors import (
    ArxivConnector,
    BiorxivConnector,
    ConnectorDomain,
    ConnectorError,
    ConnectorHit,
    ConnectorRegistry,
    CrossrefConnector,
    EuropePMCConnector,
    OpenAlexConnector,
    PDBConnector,
    SearchOptions,
    SemanticScholarConnector,
    UniProtConnector,
    get_registry,
    list_connectors,
    reset_registry,
    search_connector,
)
from infrastructure.search.connectors.config import (
    ConnectorSearchConfig,
    load_connector_search_config,
)
from infrastructure.search.connectors.http import ConnectorHttpClient, ConnectorHttpError
from infrastructure.search.connectors.types import (
    CatalogEntry,
    FetchOptions,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_server(handler_cls: type) -> tuple[HTTPServer, str]:
    """Start a throwaway HTTP server on localhost and return (server, base_url)."""
    server = HTTPServer(("127.0.0.1", 0), handler_cls)
    port = server.server_address[1]
    t = threading.Thread(target=server.handle_request, daemon=True)
    t.start()
    return server, f"http://127.0.0.1:{port}"


# ---------------------------------------------------------------------------
# types.py
# ---------------------------------------------------------------------------

class TestConnectorDomain:
    def test_values(self):
        domains = {d.value for d in ConnectorDomain}
        assert "biology" in domains
        assert "physics" in domains
        assert "general" in domains

    def test_str_enum(self):
        assert ConnectorDomain.chemistry == "chemistry"


class TestConnectorHit:
    def test_defaults(self):
        h = ConnectorHit(id="x:1", title="Test")
        assert h.authors == ()
        assert h.year is None
        assert h.score == 0.0
        assert h.source == ""

    def test_to_dict(self):
        h = ConnectorHit(id="arxiv:1234", title="Foo", year=2022, source="arxiv", score=0.9)
        d = h.to_dict()
        assert d["id"] == "arxiv:1234"
        assert d["year"] == 2022
        assert d["score"] == 0.9
        assert isinstance(d["authors"], list)

    def test_frozen(self):
        h = ConnectorHit(id="a", title="b")
        with pytest.raises((AttributeError, TypeError)):
            h.title = "c"  # type: ignore[misc]


class TestCatalogEntry:
    def test_to_dict(self):
        e = CatalogEntry(
            name="test",
            domain=ConnectorDomain.general,
            description="desc",
            base_url="https://example.com",
        )
        d = e.to_dict()
        assert d["domain"] == "general"
        assert d["supports_fetch"] is False


class TestSearchOptions:
    def test_defaults(self):
        o = SearchOptions()
        assert o.max_results == 10
        assert o.year_min is None

    def test_custom(self):
        o = SearchOptions(max_results=50, year_min=2020, year_max=2023)
        assert o.year_min == 2020


class TestFetchOptions:
    def test_defaults(self):
        o = FetchOptions()
        assert o.include_abstract is True


# ---------------------------------------------------------------------------
# registry.py
# ---------------------------------------------------------------------------

class TestConnectorRegistry:
    def _make_connector(self, name: str = "test", domain: ConnectorDomain = ConnectorDomain.general):
        class C:
            def __init__(self, n, d):
                self.name = n
                self.domain = d
                self.description = "A test connector"
            def search(self, q, opts=None):
                return []
        return C(name, domain)

    def test_register_and_get(self):
        reg = ConnectorRegistry()
        c = self._make_connector("myconn")
        reg.register(c)
        assert reg.get("myconn") is c

    def test_has(self):
        reg = ConnectorRegistry()
        assert not reg.has("nope")
        reg.register(self._make_connector("x"))
        assert reg.has("x")

    def test_duplicate_raises(self):
        reg = ConnectorRegistry()
        reg.register(self._make_connector("dup"))
        with pytest.raises(ValueError, match="already registered"):
            reg.register(self._make_connector("dup"))

    def test_deregister(self):
        reg = ConnectorRegistry()
        reg.register(self._make_connector("rem"))
        reg.deregister("rem")
        assert not reg.has("rem")

    def test_deregister_missing_raises(self):
        reg = ConnectorRegistry()
        with pytest.raises(KeyError):
            reg.deregister("ghost")

    def test_all(self):
        reg = ConnectorRegistry()
        reg.register(self._make_connector("a"))
        reg.register(self._make_connector("b"))
        names = [c.name for c in reg.all()]
        assert "a" in names and "b" in names

    def test_by_domain(self):
        reg = ConnectorRegistry()
        reg.register(self._make_connector("bio", ConnectorDomain.biology))
        reg.register(self._make_connector("chem", ConnectorDomain.chemistry))
        bio = reg.by_domain(ConnectorDomain.biology)
        assert len(bio) == 1
        assert bio[0].name == "bio"

    def test_catalog(self):
        reg = ConnectorRegistry()
        reg.register(self._make_connector("cat_test"))
        entries = reg.catalog()
        assert any(e.name == "cat_test" for e in entries)

    def test_get_missing_raises(self):
        reg = ConnectorRegistry()
        with pytest.raises(KeyError, match="cat_test2"):
            reg.get("cat_test2")

    def test_len(self):
        reg = ConnectorRegistry()
        assert len(reg) == 0
        reg.register(self._make_connector("one"))
        assert len(reg) == 1

    def test_iter(self):
        reg = ConnectorRegistry()
        reg.register(self._make_connector("iter1"))
        reg.register(self._make_connector("iter2"))
        names = {c.name for c in reg}
        assert names == {"iter1", "iter2"}


# ---------------------------------------------------------------------------
# http.py
# ---------------------------------------------------------------------------

class _JsonHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass
    def do_GET(self):
        body = json.dumps({"ok": True}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class _ErrorHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass
    def do_GET(self):
        self.send_response(404)
        self.end_headers()


class TestConnectorHttpClient:
    def test_get_json_success(self):
        server, base = _make_server(_JsonHandler)
        client = ConnectorHttpClient(ttl=0, max_retries=0)
        data = client.get_json(base)
        assert data == {"ok": True}

    def test_get_text_success(self):
        class TextHandler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_GET(self):
                body = b"hello world"
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        server, base = _make_server(TextHandler)
        client = ConnectorHttpClient(ttl=0, max_retries=0)
        text = client.get_text(base)
        assert "hello" in text

    def test_404_raises(self):
        server, base = _make_server(_ErrorHandler)
        client = ConnectorHttpClient(ttl=0, max_retries=0)
        with pytest.raises(ConnectorHttpError, match="HTTP 404"):
            client.get_json(base)

    def test_cache_hit(self):
        calls = []

        class CountHandler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_GET(self):
                calls.append(1)
                body = json.dumps({"n": len(calls)}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        # Use a server that handles multiple requests
        server2 = HTTPServer(("127.0.0.1", 0), CountHandler)
        port2 = server2.server_address[1]
        base2 = f"http://127.0.0.1:{port2}"
        t = threading.Thread(target=lambda: [server2.handle_request() for _ in range(5)], daemon=True)
        t.start()

        client = ConnectorHttpClient(ttl=60.0, max_retries=0)
        d1 = client.get_json(base2)
        d2 = client.get_json(base2)
        assert d1 == d2  # cache hit returns same data
        assert len(calls) == 1  # only one real request

    def test_clear_cache(self):
        client = ConnectorHttpClient(ttl=60.0)
        client._cache["fake_key"] = None  # type: ignore[assignment]
        n = client.clear_cache()
        assert n == 1
        assert len(client._cache) == 0

    def test_build_url_with_params(self):
        client = ConnectorHttpClient()
        url = client._build_url("https://example.com/api", {"q": "test", "n": "5"})
        assert "q=test" in url
        assert "n=5" in url


# ---------------------------------------------------------------------------
# config.py
# ---------------------------------------------------------------------------

class TestConnectorSearchConfig:
    def test_defaults(self, tmp_path):
        cfg = load_connector_search_config(tmp_path)
        assert cfg.enabled_connectors == []
        assert cfg.default_max_results == 10
        assert cfg.cache_ttl == 300.0
        assert cfg.mailto == "team@example.org"

    def test_load_from_yaml(self, tmp_path):
        (tmp_path / "connector_search.yaml").write_text(
            "enabled_connectors: [openalex, arxiv]\n"
            "default_max_results: 20\n"
            "cache_ttl: 600\n"
            "mailto: test@example.com\n"
        )
        cfg = load_connector_search_config(tmp_path)
        assert cfg.enabled_connectors == ["openalex", "arxiv"]
        assert cfg.default_max_results == 20
        assert cfg.cache_ttl == 600.0
        assert cfg.mailto == "test@example.com"

    def test_unknown_key_raises(self, tmp_path):
        (tmp_path / "connector_search.yaml").write_text("bogus_key: 123\n")
        with pytest.raises(ValueError, match="unknown connector_search"):
            load_connector_search_config(tmp_path)

    def test_invalid_max_results_raises(self, tmp_path):
        (tmp_path / "connector_search.yaml").write_text("default_max_results: -1\n")
        with pytest.raises(ValueError):
            load_connector_search_config(tmp_path)

    def test_to_dict(self):
        cfg = ConnectorSearchConfig(enabled_connectors=["openalex"])
        d = cfg.to_dict()
        assert d["enabled_connectors"] == ["openalex"]


# ---------------------------------------------------------------------------
# Global registry convenience
# ---------------------------------------------------------------------------

class TestGlobalRegistry:
    def setup_method(self):
        reset_registry()

    def teardown_method(self):
        reset_registry()

    def test_get_registry_has_8_connectors(self):
        reg = get_registry()
        assert len(reg) == 8

    def test_list_connectors_returns_catalog(self):
        entries = list_connectors()
        names = [e.name for e in entries]
        assert "openalex" in names
        assert "arxiv" in names
        assert "pdb" in names

    def test_search_connector_unknown_raises(self):
        with pytest.raises(KeyError):
            search_connector("nonexistent", "query")

    def test_search_connector_known_calls_connector(self):
        # patch the underlying connector to avoid network
        reg = get_registry()
        oa = reg.get("openalex")
        original_search = oa.search
        results_holder = []

        def fake_search(q, opts=None):
            results_holder.append(q)
            return []

        oa.search = fake_search  # type: ignore[method-assign]
        try:
            hits = search_connector("openalex", "CRISPR")
            assert results_holder == ["CRISPR"]
            assert hits == []
        finally:
            oa.search = original_search  # type: ignore[method-assign]

    def test_reset_registry(self):
        get_registry()  # populate
        reset_registry()
        # After reset, a fresh registry is built
        reg2 = get_registry()
        assert len(reg2) == 8


# ---------------------------------------------------------------------------
# Connector parsing (offline, no network)
# ---------------------------------------------------------------------------

class TestOpenAlexConnector:
    def test_parse_work(self):
        item = {
            "id": "https://openalex.org/W1234567",
            "title": "Test Paper",
            "authorships": [{"author": {"display_name": "Alice"}}, {"author": {"display_name": "Bob"}}],
            "publication_year": 2021,
            "doi": "https://doi.org/10.1234/test",
            "relevance_score": 0.85,
            "abstract_inverted_index": {"Hello": [0], "world": [1]},
        }
        hit = OpenAlexConnector._parse_work(item)
        assert hit.id == "openalex:W1234567"
        assert hit.title == "Test Paper"
        assert "Alice" in hit.authors
        assert hit.year == 2021
        assert hit.doi == "10.1234/test"
        assert hit.abstract == "Hello world"
        assert hit.score == 0.85

    def test_reconstruct_abstract(self):
        from infrastructure.search.connectors.impl.openalex import _reconstruct_abstract
        abstract = _reconstruct_abstract({"The": [0], "cat": [1], "sat": [2]})
        assert abstract == "The cat sat"

    def test_empty_abstract_index(self):
        item = {"id": "https://openalex.org/W9", "title": "X", "authorships": [], "publication_year": None}
        hit = OpenAlexConnector._parse_work(item)
        assert hit.abstract is None


class TestArxivConnector:
    _ATOM_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2501.12948v1</id>
    <title>Attention Is All You Need</title>
    <author><name>Vaswani et al</name></author>
    <published>2023-01-15T00:00:00Z</published>
    <summary>A novel architecture.</summary>
    <arxiv:doi>10.9999/test</arxiv:doi>
  </entry>
</feed>"""

    def test_parse_feed(self):
        conn = ArxivConnector()
        hits = conn._parse_feed(self._ATOM_FEED, SearchOptions(max_results=5))
        assert len(hits) == 1
        h = hits[0]
        assert h.id == "arxiv:2501.12948v1"
        assert "Attention" in h.title
        assert h.year == 2023
        assert h.doi == "10.9999/test"

    def test_parse_entry_missing_id(self):
        import xml.etree.ElementTree as ET
        conn = ArxivConnector()
        xml = '<entry xmlns="http://www.w3.org/2005/Atom"><title>X</title></entry>'
        entry = ET.fromstring(xml)
        result = conn._parse_entry(entry)
        assert result is None

    def test_year_filter(self):
        conn = ArxivConnector()
        hits = conn._parse_feed(
            self._ATOM_FEED,
            SearchOptions(max_results=10, year_min=2024),
        )
        assert hits == []


class TestSemanticScholarConnector:
    def test_parse_paper(self):
        item = {
            "paperId": "abc123",
            "title": "Neural Scaling Laws",
            "authors": [{"name": "Kaplan"}, {"name": "McCandlish"}],
            "year": 2020,
            "externalIds": {"DOI": "10.5555/test"},
            "citationCount": 5000,
        }
        hit = SemanticScholarConnector._parse_paper(item, 0)
        assert hit.id == "semantic_scholar:abc123"
        assert hit.year == 2020
        assert hit.doi == "10.5555/test"
        assert hit.score > 0


class TestCrossrefConnector:
    def test_parse_item(self):
        item = {
            "DOI": "10.1234/abc",
            "title": ["A Great Paper"],
            "author": [{"given": "Jane", "family": "Doe"}],
            "published": {"date-parts": [[2022, 3, 1]]},
            "URL": "https://doi.org/10.1234/abc",
            "score": 12.5,
        }
        hit = CrossrefConnector._parse_item(item)
        assert hit.id == "crossref:10.1234/abc"
        assert hit.doi == "10.1234/abc"
        assert hit.year == 2022
        assert "Jane Doe" in hit.authors

    def test_parse_item_no_date(self):
        item = {"DOI": "10.x/y", "title": ["T"], "author": []}
        hit = CrossrefConnector._parse_item(item)
        assert hit.year is None


class TestEuropePMCConnector:
    def test_parse_result(self):
        item = {
            "pmid": "12345678",
            "title": "A Biology Paper.",
            "authorList": {"author": [{"fullName": "Smith J"}]},
            "pubYear": "2019",
            "doi": "10.3456/bio",
        }
        hit = EuropePMCConnector._parse_result(item)
        assert hit.id == "europepmc:12345678"
        assert hit.year == 2019
        assert "Smith J" in hit.authors
        # trailing period stripped
        assert not hit.title.endswith(".")


class TestBiorxivConnector:
    def test_parse_item(self):
        item = {
            "doi": "10.1101/2021.01.01.425004",
            "title": "A Cool Preprint",
            "authors": "Smith J; Doe A",
            "date": "2021-01-01",
            "abstract": "We found something.",
            "category": "bioinformatics",
        }
        hit = BiorxivConnector._parse_item(item)
        assert hit.id.startswith("biorxiv:")
        assert hit.year == 2021
        assert "Smith J" in hit.authors

    def test_parse_item_no_doi(self):
        item = {"title": "No DOI paper", "authors": "X"}
        hit = BiorxivConnector._parse_item(item)
        assert "biorxiv:" in hit.id


class TestUniProtConnector:
    def test_parse_entry_swissprot(self):
        item = {
            "primaryAccession": "P12345",
            "proteinDescription": {
                "recommendedName": {"fullName": {"value": "Hemoglobin subunit alpha"}}
            },
            "genes": [{"geneName": {"value": "HBA1"}}],
            "organism": {"scientificName": "Homo sapiens"},
            "reviewed": True,
        }
        hit = UniProtConnector._parse_entry(item)
        assert hit.id == "uniprot:P12345"
        assert hit.title == "Hemoglobin subunit alpha"
        assert "HBA1" in hit.authors  # gene names mapped to authors field
        assert hit.score == 1.0

    def test_parse_entry_trembl(self):
        item = {"primaryAccession": "A0A000", "reviewed": False}
        hit = UniProtConnector._parse_entry(item)
        assert hit.score == 0.5


class TestPDBConnector:
    def test_minimal_hit(self):
        hit = PDBConnector._minimal_hit("1ABC", 0.75)
        assert hit.id == "pdb:1ABC"
        assert hit.score == 0.75
        assert "rcsb.org" in (hit.url or "")

    def test_parse_entry(self):
        data = {
            "rcsb_id": "1XYZ",
            "struct": {"title": "Crystal structure of Hemoglobin"},
            "citation": [{"rcsb_authors": ["Perutz MF"], "year": 1960}],
        }
        hit = PDBConnector._parse_entry(data)
        assert hit.id == "pdb:1XYZ"
        assert hit.year == 1960
        assert "Perutz MF" in hit.authors
