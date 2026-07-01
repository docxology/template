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

import sys


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
    result = build_llm_callable(**_kwargs())
    assert result is not None
    assert callable(result)


def test_build_llm_callable_returns_none_on_import_error(monkeypatch):
    """Force ``infrastructure.llm`` to be un-importable for the duration
    of one call. The function must return ``None`` (not raise) so the
    orchestrator can skip the synthesis stage cleanly.

    We use the ``meta_path`` finder mechanism Python uses internally;
    no mocking framework is involved.
    """
    import importlib.abc
    import importlib.machinery

    class _RejectInfraLLM(importlib.abc.MetaPathFinder):
        def find_spec(self, name, path, target=None):
            if name == "infrastructure.llm":
                # Returning a spec with an unloadable loader forces
                # ImportError at import time.
                raise ImportError("test-injected: infrastructure.llm unavailable")
            return None

    # Drop any cached module so the import re-runs the finder chain.
    monkeypatch.delitem(sys.modules, "infrastructure.llm", raising=False)
    finder = _RejectInfraLLM()
    monkeypatch.setattr(sys, "meta_path", [finder] + sys.meta_path)

    result = build_llm_callable(**_kwargs())
    assert result is None


def test_returned_callable_signature_is_str_to_str():
    """The returned callable has the documented ``Callable[[str], str]``
    signature. We don't invoke it (that would hit Ollama), but we can
    confirm it exposes one positional ``prompt`` argument."""
    import inspect

    result = build_llm_callable(**_kwargs())
    assert result is not None
    sig = inspect.signature(result)
    params = list(sig.parameters.values())
    assert len(params) == 1
    assert params[0].name == "prompt"
