"""Exa search interface — neural/keyword web search via the Exa REST API.

A second search interface under :mod:`infrastructure.search`, sibling to
:mod:`infrastructure.search.literature`. Where ``literature`` discovers academic
papers across arXiv/Crossref/local corpora, ``exa`` is a general web search,
content-extraction, and grounded-answer interface backed by https://exa.ai.

Each Exa endpoint lives in its own subpackage:

* :mod:`infrastructure.search.exa.search` — ``POST /search`` (neural/keyword + structured output)
* :mod:`infrastructure.search.exa.contents` — ``POST /contents`` (parsed content for known URLs)
* :mod:`infrastructure.search.exa.answer` — ``POST /answer`` (grounded answer + citations)
* :mod:`infrastructure.search.exa.find_similar` — ``POST /findSimilar`` (similar pages for a seed URL)

The shared core (:class:`ExaClient`, :class:`ExaConfig`, models, transport) sits
at the package root. Construction never reads the environment, so importing this
package is side-effect free; use :meth:`ExaClient.from_env` to pull ``EXA_API_KEY``.

Canonical API reference (source of truth):
https://docs.exa.ai/reference/search-api-guide-for-coding-agents

Quick start::

    from infrastructure.search.exa import ExaClient

    client = ExaClient.from_env()
    resp = client.search("Next.js route handler authentication example", num_results=10)
    for result in resp.results:
        print(result.title, result.url)
"""

from infrastructure.search.exa.answer import ExaAnswerInterface
from infrastructure.search.exa.client import ExaClient
from infrastructure.search.exa.config import (
    API_KEY_ENV,
    DEFAULT_BASE_URL,
    DEFAULT_SEARCH_TYPE,
    VALID_SEARCH_TYPES,
    ExaConfig,
)
from infrastructure.search.exa.contents import ExaContentsInterface
from infrastructure.search.exa.errors import ExaError
from infrastructure.search.exa.find_similar import ExaFindSimilarInterface
from infrastructure.search.exa.http import ExaHttpClient, ExaResponse, UrllibExaHttpClient
from infrastructure.search.exa.models import (
    AnswerResponse,
    ContentsResponse,
    ExaResult,
    Grounding,
    SearchOutput,
    SearchResponse,
)
from infrastructure.search.exa.search import ExaSearchInterface

__all__ = [
    "API_KEY_ENV",
    "DEFAULT_BASE_URL",
    "DEFAULT_SEARCH_TYPE",
    "VALID_SEARCH_TYPES",
    "AnswerResponse",
    "ContentsResponse",
    "ExaAnswerInterface",
    "ExaClient",
    "ExaConfig",
    "ExaContentsInterface",
    "ExaError",
    "ExaFindSimilarInterface",
    "ExaHttpClient",
    "ExaResponse",
    "ExaResult",
    "ExaSearchInterface",
    "Grounding",
    "SearchOutput",
    "SearchResponse",
    "UrllibExaHttpClient",
]
