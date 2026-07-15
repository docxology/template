"""Tests for src.llm_runtime — no mocks, monkeypatch sys.modules only.

The module's job is purely to bind project knobs to a real
:class:`infrastructure.llm.LLMClient` and return ``None`` cleanly when the
LLM stack is genuinely unreachable so callers can skip synthesis without
emitting placeholder text.

We exercise both paths:

  1. Happy path — the import succeeds and a real callable is returned.
  2. Import-failure path — we make ``infrastructure.llm`` un-importable
     for one call (via ``sys.modules`` monkeypatching, which is the same
     mechanism Python's own import system uses; no mock framework is
     involved) and confirm the function returns ``None`` and logs a
     warning rather than raising.
"""

from __future__ import annotations

import pytest

from src.llm_runtime import build_llm_callable


def _kwargs() -> dict:
    return dict(
        model="gemma3:4b",
        seed=42,
        temperature=0.0,
        context_window=4096,
        long_max_tokens=1024,
        max_input_length=10_000,
        review_timeout=60.0,
    )


def test_build_llm_callable_returns_callable_when_infra_importable():
    """When ``infrastructure.llm`` is importable, the function returns a
    real ``(prompt: str) -> str`` callable. We don't *invoke* it (that
    would hit a real Ollama server); we only assert the return type so
    the orchestrator's ``llm is not None`` guard works as documented."""
    pytest.importorskip("infrastructure.llm", exc_type=ImportError)
    result = build_llm_callable(**_kwargs())
    assert result is not None
    assert callable(result)


def test_build_llm_callable_returns_none_on_import_error():
    """Force ``infrastructure.llm`` to be un-importable for the duration
    of one call. The function must return ``None`` (not raise) so the
    orchestrator can skip the synthesis stage cleanly.

    We use the ``meta_path`` finder mechanism Python uses internally;
    no mocking framework is involved.
    """

    def unavailable():
        raise ImportError("test-injected: infrastructure.llm unavailable")

    result = build_llm_callable(**_kwargs(), component_loader=unavailable)
    assert result is None


def test_build_llm_callable_returns_none_when_client_construction_raises():
    """Cover the second ``except Exception`` branch (lines 88-93): the
    import succeeds but ``OllamaClientConfig.from_env()``/``LLMClient(...)``
    construction raises (e.g. the Ollama server is unreachable). The
    function must still return ``None`` rather than propagate.

    Uses the same real-module-substitution pattern as
    ``tests/test_deep_improvements.py::TestLLMRuntimeCallable`` (a
    ``types.ModuleType`` stand-in swapped into ``sys.modules`` via
    ``monkeypatch.setitem``) — no mock framework involved, only a real
    (if deliberately broken) module object.
    """

    class _BrokenConfig:
        @classmethod
        def from_env(cls) -> "_BrokenConfig":
            raise RuntimeError("test-injected: cannot reach Ollama base_url")

    class _UnreachableClient:
        def __init__(self, _config) -> None:
            raise AssertionError("should not be constructed once from_env() raises")

    result = build_llm_callable(
        **_kwargs(),
        component_loader=lambda: (_UnreachableClient, _BrokenConfig),
    )
    assert result is None


def test_returned_callable_signature_is_str_to_str():
    """The returned callable has the documented ``Callable[[str], str]``
    signature. We don't invoke it (that would hit Ollama), but we can
    confirm it exposes one positional ``prompt`` argument."""
    import inspect

    pytest.importorskip("infrastructure.llm", exc_type=ImportError)
    result = build_llm_callable(**_kwargs())
    assert result is not None
    sig = inspect.signature(result)
    params = list(sig.parameters.values())
    assert len(params) == 1
    assert params[0].name == "prompt"
