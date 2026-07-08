"""``ExaClient`` — the facade that ties the per-endpoint interfaces together.

Each search interface (``search``, ``contents``, ``answer``, ``find_similar``)
lives in its own subpackage and receives the client so it can issue a request
through one shared, audited transport path (:meth:`ExaClient.request`). Construct
with an explicit :class:`~infrastructure.search.exa.config.ExaConfig`, or use
:meth:`ExaClient.from_env` for the ``EXA_API_KEY`` happy path.
"""

from __future__ import annotations

from functools import cached_property
from typing import Any, Mapping

from infrastructure.search.exa.config import ExaConfig
from infrastructure.search.exa.errors import ExaError
from infrastructure.search.exa.http import ExaHttpClient, ExaResponse, UrllibExaHttpClient


class ExaClient:
    """Thin, dependency-injected client for the Exa REST API.

    Args:
        config: API key + host + defaults. Required.
        http_client: Transport override. Defaults to the stdlib client; tests
            inject a ``pytest-httpserver``-backed one via ``config.base_url``.
    """

    def __init__(self, config: ExaConfig, *, http_client: ExaHttpClient | None = None) -> None:
        self.config = config
        self.http: ExaHttpClient = http_client or UrllibExaHttpClient()

    @classmethod
    def from_env(cls, *, base_url: str | None = None, http_client: ExaHttpClient | None = None) -> ExaClient:
        """Construct from ``EXA_API_KEY``; raises :class:`ExaError` if unset."""
        return cls(ExaConfig.from_env(base_url=base_url), http_client=http_client)

    def request(self, path: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        """POST ``payload`` to ``base_url + path`` and return the parsed JSON.

        Raises:
            ExaError: on non-2xx status (with ``status``/``body`` attached) or a
                non-JSON body.
        """
        url = f"{self.config.base_url}/{path.lstrip('/')}"
        resp: ExaResponse = self.http.post(
            url,
            json=dict(payload),
            headers=self.config.auth_headers(),
            timeout=self.config.timeout,
        )
        if not 200 <= resp.status_code < 300:
            raise ExaError(
                f"Exa {path} returned HTTP {resp.status_code}",
                status=resp.status_code,
                body=resp.text[:1000],
            )
        data = resp.json()
        if not isinstance(data, dict):
            raise ExaError(f"Exa {path} returned a non-object JSON body", status=resp.status_code)
        return data

    # -- Per-interface facades (lazy so unused endpoints cost nothing) --------

    @cached_property
    def search_interface(self) -> Any:
        """Process search interface."""
        from infrastructure.search.exa.search import ExaSearchInterface

        return ExaSearchInterface(self)

    @cached_property
    def contents_interface(self) -> Any:
        """Process contents interface."""
        from infrastructure.search.exa.contents import ExaContentsInterface

        return ExaContentsInterface(self)

    @cached_property
    def answer_interface(self) -> Any:
        """Process answer interface."""
        from infrastructure.search.exa.answer import ExaAnswerInterface

        return ExaAnswerInterface(self)

    @cached_property
    def find_similar_interface(self) -> Any:
        """Process find similar interface."""
        from infrastructure.search.exa.find_similar import ExaFindSimilarInterface

        return ExaFindSimilarInterface(self)

    # Convenience pass-throughs so callers can use ``client.search(...)`` etc.
    def search(self, query: str, **kwargs: Any) -> Any:
        """Search for results matching a query."""
        return self.search_interface.search(query, **kwargs)

    def contents(self, urls: Any, **kwargs: Any) -> Any:
        """Process contents."""
        return self.contents_interface.get(urls, **kwargs)

    def answer(self, query: str, **kwargs: Any) -> Any:
        """Process answer."""
        return self.answer_interface.answer(query, **kwargs)

    def find_similar(self, url: str, **kwargs: Any) -> Any:
        """Process find similar."""
        return self.find_similar_interface.find_similar(url, **kwargs)


__all__ = ["ExaClient"]
