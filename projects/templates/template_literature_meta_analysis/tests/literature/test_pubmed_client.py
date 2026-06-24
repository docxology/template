import xml.etree.ElementTree as ET

import requests
from pytest_httpserver import HTTPServer

from literature.models import Paper
from literature.pubmed_client import _parse_pubmed_article, search_pubmed

SINGLE_ARTICLE_XML = """\
<PubmedArticle>
  <MedlineCitation>
    <Article>
      <ArticleTitle>Predictive processing in active inference</ArticleTitle>
      <Abstract>
        <AbstractText>Active inference links perception and action.</AbstractText>
      </Abstract>
      <AuthorList>
        <Author>
          <ForeName>Karl</ForeName>
          <LastName>Friston</LastName>
        </Author>
        <Author>
          <ForeName>Thomas</ForeName>
          <LastName>Parr</LastName>
        </Author>
      </AuthorList>
      <Journal>
        <JournalIssue>
          <PubDate>
            <Year>2023</Year>
          </PubDate>
        </JournalIssue>
        <Title>Journal of Theoretical Biology</Title>
      </Journal>
    </Article>
  </MedlineCitation>
  <PubmedData>
    <ArticleIdList>
      <ArticleId IdType="doi">10.1000/pubmed.001</ArticleId>
    </ArticleIdList>
  </PubmedData>
</PubmedArticle>
"""

MISSING_DOI_XML = """\
<PubmedArticle>
  <MedlineCitation>
    <Article>
      <ArticleTitle>No DOI record</ArticleTitle>
      <Abstract>
        <AbstractText>Metadata without a DOI.</AbstractText>
      </Abstract>
    </Article>
  </MedlineCitation>
</PubmedArticle>
"""

MISSING_ABSTRACT_XML = """\
<PubmedArticle>
  <MedlineCitation>
    <Article>
      <ArticleTitle>Abstract absent</ArticleTitle>
    </Article>
  </MedlineCitation>
</PubmedArticle>
"""

MULTI_ABSTRACT_XML = """\
<PubmedArticle>
  <MedlineCitation>
    <Article>
      <ArticleTitle>Segmented abstract</ArticleTitle>
      <Abstract>
        <AbstractText>First sentence.</AbstractText>
        <AbstractText>Second sentence.</AbstractText>
      </Abstract>
    </Article>
  </MedlineCitation>
</PubmedArticle>
"""

COLLECTIVE_AUTHOR_XML = """\
<PubmedArticle>
  <MedlineCitation>
    <Article>
      <ArticleTitle>Collective authorship</ArticleTitle>
      <AuthorList>
        <Author>
          <CollectiveName>Active Inference Consortium</CollectiveName>
        </Author>
      </AuthorList>
    </Article>
  </MedlineCitation>
</PubmedArticle>
"""

NON_NUMERIC_YEAR_XML = """\
<PubmedArticle>
  <MedlineCitation>
    <Article>
      <ArticleTitle>Year not a number</ArticleTitle>
      <Journal>
        <JournalIssue>
          <PubDate>
            <Year>Spring</Year>
          </PubDate>
        </JournalIssue>
        <Title>Seasonal Journal</Title>
      </Journal>
    </Article>
  </MedlineCitation>
</PubmedArticle>
"""

EMPTY_SEGMENTS_XML = """\
<PubmedArticle>
  <MedlineCitation>
    <Article>
      <ArticleTitle>Empty inner nodes</ArticleTitle>
      <Abstract>
        <AbstractText></AbstractText>
        <AbstractText>Only real sentence.</AbstractText>
      </Abstract>
      <AuthorList>
        <Author></Author>
        <Author>
          <ForeName>Real</ForeName>
          <LastName>Author</LastName>
        </Author>
      </AuthorList>
    </Article>
  </MedlineCitation>
</PubmedArticle>
"""

PUBMED_ARTICLE_SET_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <Article>
        <ArticleTitle>First PubMed paper</ArticleTitle>
        <Abstract>
          <AbstractText>First abstract.</AbstractText>
        </Abstract>
        <AuthorList>
          <Author>
            <ForeName>Ada</ForeName>
            <LastName>Lovelace</LastName>
          </Author>
        </AuthorList>
        <Journal>
          <JournalIssue>
            <PubDate>
              <Year>2020</Year>
            </PubDate>
          </JournalIssue>
          <Title>Systems Neuroscience</Title>
        </Journal>
      </Article>
    </MedlineCitation>
    <PubmedData>
      <ArticleIdList>
        <ArticleId IdType="doi">10.1000/pubmed.101</ArticleId>
      </ArticleIdList>
    </PubmedData>
  </PubmedArticle>
  <PubmedArticle>
    <MedlineCitation>
      <Article>
        <ArticleTitle>Second PubMed paper</ArticleTitle>
        <Abstract>
          <AbstractText>Second abstract.</AbstractText>
        </Abstract>
        <AuthorList>
          <Author>
            <ForeName>Grace</ForeName>
            <LastName>Hopper</LastName>
          </Author>
        </AuthorList>
        <Journal>
          <JournalIssue>
            <PubDate>
              <Year>2021</Year>
            </PubDate>
          </JournalIssue>
          <Title>Computational Biology Letters</Title>
        </Journal>
      </Article>
    </MedlineCitation>
    <PubmedData>
      <ArticleIdList>
        <ArticleId IdType="doi">10.1000/pubmed.202</ArticleId>
      </ArticleIdList>
    </PubmedData>
  </PubmedArticle>
</PubmedArticleSet>
"""


class TestParsePubMedArticle:
    def test_parse_complete_record(self):
        article = ET.fromstring(SINGLE_ARTICLE_XML)

        paper = _parse_pubmed_article(article)

        assert isinstance(paper, Paper)
        assert paper.title == "Predictive processing in active inference"
        assert paper.abstract == "Active inference links perception and action."
        assert len(paper.authors) == 2
        assert paper.authors[0].name == "Karl Friston"
        assert paper.authors[1].name == "Thomas Parr"
        assert paper.year == 2023
        assert paper.venue == "Journal of Theoretical Biology"
        assert paper.doi == "10.1000/pubmed.001"
        assert paper.canonical_id == "doi:10.1000/pubmed.001"

    def test_parse_missing_doi(self):
        article = ET.fromstring(MISSING_DOI_XML)

        paper = _parse_pubmed_article(article)

        assert paper.doi is None

    def test_parse_missing_abstract(self):
        article = ET.fromstring(MISSING_ABSTRACT_XML)

        paper = _parse_pubmed_article(article)

        assert paper.abstract == ""

    def test_parse_multiple_abstract_segments(self):
        article = ET.fromstring(MULTI_ABSTRACT_XML)

        paper = _parse_pubmed_article(article)

        assert paper.abstract == "First sentence. Second sentence."

    def test_parse_collective_name_author(self):
        article = ET.fromstring(COLLECTIVE_AUTHOR_XML)

        paper = _parse_pubmed_article(article)

        assert [author.name for author in paper.authors] == ["Active Inference Consortium"]

    def test_parse_non_numeric_year_yields_none(self):
        """A PubDate/Year that is not an integer leaves year unset (None)."""
        article = ET.fromstring(NON_NUMERIC_YEAR_XML)

        paper = _parse_pubmed_article(article)

        assert paper.year is None
        # The rest of the record still parses.
        assert paper.title == "Year not a number"
        assert paper.venue == "Seasonal Journal"

    def test_parse_skips_empty_segments_and_authors(self):
        """Empty AbstractText and Author nodes are dropped, not emitted as blanks."""
        article = ET.fromstring(EMPTY_SEGMENTS_XML)

        paper = _parse_pubmed_article(article)

        # Empty <AbstractText></AbstractText> contributes nothing; only the real one remains.
        assert paper.abstract == "Only real sentence."
        # Empty <Author></Author> yields no usable name and is skipped.
        assert [author.name for author in paper.authors] == ["Real Author"]


class TestSearchPubMed:
    def test_search_pubmed_happy_path(self, httpserver: HTTPServer):
        httpserver.expect_request("/esearch").respond_with_json({"esearchresult": {"idlist": ["11111111", "22222222"]}})
        httpserver.expect_request("/efetch").respond_with_data(PUBMED_ARTICLE_SET_XML, content_type="application/xml")

        papers = search_pubmed(
            "active inference",
            esearch_url=httpserver.url_for("/esearch"),
            efetch_url=httpserver.url_for("/efetch"),
            delay_override=lambda _: None,
        )

        assert len(papers) == 2
        assert papers[0].title == "First PubMed paper"
        assert papers[0].abstract == "First abstract."
        assert papers[0].authors[0].name == "Ada Lovelace"
        assert papers[0].year == 2020
        assert papers[0].venue == "Systems Neuroscience"
        assert papers[0].doi == "10.1000/pubmed.101"
        assert papers[1].title == "Second PubMed paper"
        assert papers[1].abstract == "Second abstract."
        assert papers[1].authors[0].name == "Grace Hopper"
        assert papers[1].year == 2021
        assert papers[1].venue == "Computational Biology Letters"
        assert papers[1].doi == "10.1000/pubmed.202"

    def test_search_pubmed_batches_large_idlists(self, httpserver: HTTPServer, monkeypatch):
        """efetch is GET-batched so a large idlist does not overrun the URI limit (HTTP 414).

        With the batch size forced to 1, three PMIDs must produce three separate efetch
        requests (a single un-batched request would jam all ids into one URL).
        """
        from literature import pubmed_client

        monkeypatch.setattr(pubmed_client, "EFETCH_BATCH_SIZE", 1)
        one_article = (
            '<?xml version="1.0"?><PubmedArticleSet><PubmedArticle><MedlineCitation>'
            "<Article><ArticleTitle>Batched record</ArticleTitle></Article>"
            "</MedlineCitation></PubmedArticle></PubmedArticleSet>"
        )
        httpserver.expect_request("/esearch").respond_with_json(
            {"esearchresult": {"idlist": ["1", "2", "3"]}}
        )
        httpserver.expect_request("/efetch").respond_with_data(
            one_article, content_type="application/xml"
        )
        papers = search_pubmed(
            "modafinil",
            esearch_url=httpserver.url_for("/esearch"),
            efetch_url=httpserver.url_for("/efetch"),
            delay_override=lambda _: None,
        )
        assert len(papers) == 3  # 3 batches of 1 -> 3 single-article responses
        efetch_calls = sum(1 for req, _ in httpserver.log if "efetch" in req.path)
        assert efetch_calls == 3

    def test_search_pubmed_empty_idlist(self, httpserver: HTTPServer):
        httpserver.expect_request("/esearch").respond_with_json({"esearchresult": {"idlist": []}})

        papers = search_pubmed(
            "no results",
            esearch_url=httpserver.url_for("/esearch"),
            efetch_url=httpserver.url_for("/efetch"),
            delay_override=lambda _: None,
        )

        assert papers == []

    def test_search_pubmed_esearch_http_500(self, httpserver: HTTPServer):
        httpserver.expect_request("/esearch").respond_with_data("Server Error", status=500)
        httpserver.expect_request("/esearch").respond_with_data("Server Error", status=500)

        papers = search_pubmed(
            "broken esearch",
            esearch_url=httpserver.url_for("/esearch"),
            efetch_url=httpserver.url_for("/efetch"),
            delay_override=lambda _: None,
        )

        assert papers == []

    def test_search_pubmed_esearch_invalid_json(self, httpserver: HTTPServer):
        """esearch returning non-JSON body is handled gracefully -> []."""
        httpserver.expect_request("/esearch").respond_with_data("not json at all", content_type="text/plain")

        papers = search_pubmed(
            "bad json",
            esearch_url=httpserver.url_for("/esearch"),
            efetch_url=httpserver.url_for("/efetch"),
            delay_override=lambda _: None,
        )

        assert papers == []

    def test_search_pubmed_esearch_payload_not_object(self, httpserver: HTTPServer):
        """esearch JSON that is a list (not an object) -> []."""
        httpserver.expect_request("/esearch").respond_with_json([1, 2, 3])

        papers = search_pubmed(
            "json array",
            esearch_url=httpserver.url_for("/esearch"),
            efetch_url=httpserver.url_for("/efetch"),
            delay_override=lambda _: None,
        )

        assert papers == []

    def test_search_pubmed_esearch_missing_result_key(self, httpserver: HTTPServer):
        """esearch payload without 'esearchresult' -> []."""
        httpserver.expect_request("/esearch").respond_with_json({"header": {}})

        papers = search_pubmed(
            "missing result",
            esearch_url=httpserver.url_for("/esearch"),
            efetch_url=httpserver.url_for("/efetch"),
            delay_override=lambda _: None,
        )

        assert papers == []

    def test_search_pubmed_esearch_idlist_not_list(self, httpserver: HTTPServer):
        """esearchresult.idlist of the wrong type -> []."""
        httpserver.expect_request("/esearch").respond_with_json({"esearchresult": {"idlist": "11111111"}})

        papers = search_pubmed(
            "idlist wrong type",
            esearch_url=httpserver.url_for("/esearch"),
            efetch_url=httpserver.url_for("/efetch"),
            delay_override=lambda _: None,
        )

        assert papers == []

    def test_search_pubmed_efetch_http_500(self, httpserver: HTTPServer):
        httpserver.expect_request("/esearch").respond_with_json({"esearchresult": {"idlist": ["11111111"]}})
        httpserver.expect_request("/efetch").respond_with_data("Server Error", status=500)
        httpserver.expect_request("/efetch").respond_with_data("Server Error", status=500)

        papers = search_pubmed(
            "broken efetch",
            esearch_url=httpserver.url_for("/esearch"),
            efetch_url=httpserver.url_for("/efetch"),
            delay_override=lambda _: None,
        )

        assert papers == []

    def test_search_pubmed_efetch_malformed_xml(self, httpserver: HTTPServer):
        httpserver.expect_request("/esearch").respond_with_json({"esearchresult": {"idlist": ["11111111"]}})
        httpserver.expect_request("/efetch").respond_with_data(
            "<PubmedArticleSet><PubmedArticle>", content_type="application/xml"
        )

        papers = search_pubmed(
            "malformed xml",
            esearch_url=httpserver.url_for("/esearch"),
            efetch_url=httpserver.url_for("/efetch"),
            delay_override=lambda _: None,
        )

        assert papers == []

    def test_search_pubmed_with_custom_session(self, httpserver: HTTPServer):
        httpserver.expect_request("/esearch").respond_with_json({"esearchresult": {"idlist": ["11111111", "22222222"]}})
        httpserver.expect_request("/efetch").respond_with_data(PUBMED_ARTICLE_SET_XML, content_type="application/xml")

        session = requests.Session()
        try:
            papers = search_pubmed(
                "session test",
                esearch_url=httpserver.url_for("/esearch"),
                efetch_url=httpserver.url_for("/efetch"),
                session=session,
                delay_override=lambda _: None,
            )
        finally:
            session.close()

        assert len(papers) == 2
