"""``/answer`` interface — a grounded answer with citations.

Best for question-first UIs where you want a synthesised answer and do not need
to inspect raw search results. For new structured-search flows that need both
retrieval control and grounded output, prefer ``/search`` + ``output_schema``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Mapping

from infrastructure.search.exa.errors import ExaError
from infrastructure.search.exa.models import AnswerResponse, prune

if TYPE_CHECKING:  # pragma: no cover
    from infrastructure.search.exa.client import ExaClient


class ExaAnswerInterface:
    """Wraps ``POST /answer``."""

    path = "/answer"

    def __init__(self, client: ExaClient) -> None:
        self._client = client

    def answer(
        self,
        query: str,
        *,
        text: bool | None = None,
        system_prompt: str | None = None,
        output_schema: Mapping[str, Any] | None = None,
    ) -> AnswerResponse:
        """Answer ``query`` from grounded sources.

        ``text=True`` asks Exa to include full source text on each citation.
        Raises :class:`ExaError` on an empty query.
        """
        if not query or not query.strip():
            raise ExaError("answer query must be a non-empty string")
        payload = prune(
            {
                "query": query,
                "text": text,
                "systemPrompt": system_prompt,
                "outputSchema": dict(output_schema) if output_schema else None,
            }
        )
        return AnswerResponse.from_dict(self._client.request(self.path, payload))


__all__ = ["ExaAnswerInterface"]
