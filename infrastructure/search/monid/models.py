"""Response models for the Monid HTTP API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


def _money(data: Mapping[str, Any] | None) -> Money | None:
    if not isinstance(data, Mapping):
        return None
    value = data.get("value")
    currency = data.get("currency")
    if value is None and currency is None:
        return None
    return Money(value=float(value) if value is not None else None, currency=str(currency or "USD"))


@dataclass(frozen=True)
class Money:
    """USD amount wrapper from Monid price/cost fields."""

    value: float | None
    currency: str = "USD"


@dataclass(frozen=True)
class EndpointPrice:
    """Pricing metadata attached to discover/inspect/run responses."""

    type: str
    amount: Money | None = None
    flat_fee: Money | None = None
    notes: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> EndpointPrice | None:
        if not isinstance(data, Mapping):
            return None
        notes_raw = data.get("notes")
        notes: tuple[str, ...] = ()
        if isinstance(notes_raw, list):
            notes = tuple(str(n) for n in notes_raw)
        return cls(
            type=str(data.get("type") or ""),
            amount=_money(data.get("amount") if isinstance(data.get("amount"), Mapping) else None),
            flat_fee=_money(data.get("flatFee") if isinstance(data.get("flatFee"), Mapping) else None),
            notes=notes,
        )

    def estimated_per_call_usd(self) -> float | None:
        """Return a flat per-call estimate when pricing is ``PER_CALL``."""
        if self.type != "PER_CALL" or self.amount is None or self.amount.value is None:
            return None
        return self.amount.value

    def estimated_per_1k_calls_usd(self) -> float | None:
        """Convert a per-call estimate to USD per 1,000 calls."""
        per_call = self.estimated_per_call_usd()
        if per_call is None:
            return None
        return per_call * 1000.0


@dataclass(frozen=True)
class DiscoverHit:
    """One endpoint returned by ``POST /v1/discover``."""

    provider: str
    endpoint: str
    description: str
    score: float
    tags: tuple[str, ...]
    provider_name: str | None = None
    price: EndpointPrice | None = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DiscoverHit:
        tags_raw = data.get("tags")
        tags = tuple(str(t) for t in tags_raw) if isinstance(tags_raw, list) else ()
        return cls(
            provider=str(data.get("provider") or ""),
            endpoint=str(data.get("endpoint") or ""),
            description=str(data.get("description") or ""),
            score=float(data.get("score") or 0.0),
            tags=tags,
            provider_name=str(data["providerName"]) if data.get("providerName") else None,
            price=EndpointPrice.from_dict(data.get("price") if isinstance(data.get("price"), Mapping) else None),
        )


@dataclass(frozen=True)
class DiscoverResponse:
    """Parsed discover response."""

    query: str
    count: int
    results: tuple[DiscoverHit, ...]

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DiscoverResponse:
        raw = data.get("results")
        if isinstance(raw, list):
            results = tuple(DiscoverHit.from_dict(row) for row in raw if isinstance(row, Mapping))
        else:
            results = ()
        return cls(query=str(data.get("query") or ""), count=int(data.get("count") or len(results)), results=results)


@dataclass(frozen=True)
class InspectResponse:
    """Parsed inspect response."""

    provider: str
    endpoint: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)
    price: EndpointPrice | None = None
    provider_name: str | None = None
    summary: str | None = None
    tags: tuple[str, ...] = ()
    doc_url: str | None = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> InspectResponse:
        tags_raw = data.get("tags")
        tags = tuple(str(t) for t in tags_raw) if isinstance(tags_raw, list) else ()
        input_raw = data.get("input")
        input_schema = dict(input_raw) if isinstance(input_raw, Mapping) else {}
        return cls(
            provider=str(data.get("provider") or ""),
            endpoint=str(data.get("endpoint") or ""),
            description=str(data.get("description") or ""),
            input_schema=input_schema,
            price=EndpointPrice.from_dict(data.get("price") if isinstance(data.get("price"), Mapping) else None),
            provider_name=str(data["providerName"]) if data.get("providerName") else None,
            summary=str(data["summary"]) if data.get("summary") else None,
            tags=tags,
            doc_url=str(data["docUrl"]) if data.get("docUrl") else None,
        )


@dataclass(frozen=True)
class RunRecord:
    """Run lifecycle record from ``POST /v1/run`` or ``GET /v1/runs/:id``."""

    run_id: str
    provider: str
    endpoint: str
    status: str
    output: Any = None
    provider_http_status: int | None = None
    price: EndpointPrice | None = None
    cost: Money | None = None
    stoppable: bool | None = None
    reason: str | None = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> RunRecord:
        provider_response = data.get("providerResponse")
        http_status: int | None = None
        if isinstance(provider_response, Mapping) and provider_response.get("httpStatus") is not None:
            http_status = int(provider_response["httpStatus"])
        cost_raw = data.get("cost")
        cost = _money(cost_raw if isinstance(cost_raw, Mapping) else None)
        stoppable_raw = data.get("stoppable")
        return cls(
            run_id=str(data.get("runId") or ""),
            provider=str(data.get("provider") or ""),
            endpoint=str(data.get("endpoint") or ""),
            status=str(data.get("status") or ""),
            output=data.get("output"),
            provider_http_status=http_status,
            price=EndpointPrice.from_dict(data.get("price") if isinstance(data.get("price"), Mapping) else None),
            cost=cost,
            stoppable=bool(stoppable_raw) if stoppable_raw is not None else None,
            reason=str(data["reason"]) if data.get("reason") else None,
        )

    @property
    def is_terminal(self) -> bool:
        """Whether the run reached a terminal lifecycle state."""
        return self.status in {"COMPLETED", "FAILED", "BLOCKED", "STOPPED", "TIMED_OUT"}


@dataclass(frozen=True)
class WalletBalance:
    """Workspace wallet balance."""

    value: float
    currency: str = "USD"

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> WalletBalance:
        balance = data.get("balance")
        if not isinstance(balance, Mapping):
            raise ValueError("wallet response missing balance object")
        return cls(value=float(balance.get("value") or 0.0), currency=str(balance.get("currency") or "USD"))


__all__ = [
    "DiscoverHit",
    "DiscoverResponse",
    "EndpointPrice",
    "InspectResponse",
    "Money",
    "RunRecord",
    "WalletBalance",
]
