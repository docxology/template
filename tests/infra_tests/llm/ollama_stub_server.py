"""HTTP handlers for :func:`pytest_httpserver.HTTPServer` Ollama-shaped stubs.

Keeps ``conftest.py`` small; extend response rules here instead of growing the fixture.
"""

from __future__ import annotations

import json
from collections.abc import Callable


def _parse_chat_request(request: object) -> tuple[bool, str, list[dict[str, object]], str | None]:
    """Return ``(is_stream, model, messages, format_type)`` from a POST /api/chat body."""
    try:
        if hasattr(request, "body") and request.body:
            request_data = json.loads(request.body)
        elif hasattr(request, "get_data") and callable(request.get_data):
            request_data = json.loads(request.get_data())
        elif hasattr(request, "data") and request.data:
            request_data = json.loads(request.data)
        else:
            raise ValueError("Cannot access request body")
        is_stream = bool(request_data.get("stream", False))
        model = str(request_data.get("model", "gemma3:4b"))
        messages = list(request_data.get("messages") or [])
        format_type = request_data.get("format")
        if format_type is not None:
            format_type = str(format_type)
        return is_stream, model, messages, format_type
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return False, "gemma3:4b", [], None


def _last_user_prompt(messages: list[dict[str, object]]) -> str:
    for msg in reversed(messages):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            return str(content) if content is not None else ""
    return ""


def _non_stream_payload(model: str, content: str) -> str:
    return json.dumps(
        {
            "model": model,
            "created_at": "2024-01-01T00:00:00Z",
            "message": {"role": "assistant", "content": content},
            "done": True,
        }
    )


def _stream_payload(model: str, response_content: str, *, bad_first_line: bool = False) -> str:
    lines: list[str] = []
    if bad_first_line:
        lines.append("this is not json")
    streaming_chunks = [
        {
            "model": model,
            "created_at": "2024-01-01T00:00:00Z",
            "message": {"role": "assistant", "content": response_content[:10]},
            "done": False,
        },
        {
            "model": model,
            "created_at": "2024-01-01T00:00:01Z",
            "message": {"role": "assistant", "content": response_content[10:]},
            "done": False,
        },
        {
            "model": model,
            "created_at": "2024-01-01T00:00:02Z",
            "message": {"role": "assistant", "content": ""},
            "done": True,
        },
    ]
    for chunk in streaming_chunks:
        lines.append(json.dumps(chunk))
    return "\n".join(lines)


def _empty_stream_payload(model: str) -> str:
    chunk = {
        "model": model,
        "created_at": "2024-01-01T00:00:02Z",
        "message": {"role": "assistant", "content": ""},
        "done": True,
    }
    return json.dumps(chunk)


def build_chat_handler() -> Callable[[object], tuple[str, int] | str]:
    """Build a werkzeug handler for POST /api/chat (returns body or (body, status))."""

    def handle_chat_request(request: object) -> tuple[str, int] | str:
        is_stream, model, messages, format_type = _parse_chat_request(request)
        prompt_text = _last_user_prompt(messages)

        if model == "primary-model":
            return "", 500
        if model == "fallback1":
            return "", 500
        if "invalid json content" in prompt_text:
            response_content = "Some text { invalid json content } more text"
        elif "no json response" in prompt_text:
            response_content = "This is just plain text with no JSON structure"
        elif format_type == "json" or "test structured" in prompt_text.lower():
            response_content = '{"key": "value", "number": 42}'
        else:
            response_content = "Test response"

        if "__OLLAMA_HTTP_EMPTY_STREAM__" in prompt_text:
            if is_stream:
                return _empty_stream_payload(model)
            return _non_stream_payload(model, "")

        if is_stream:
            bad_line = "__OLLAMA_HTTP_BAD_NDJSON_LINE__" in prompt_text
            return _stream_payload(model, response_content, bad_first_line=bad_line)

        return _non_stream_payload(model, response_content)

    return handle_chat_request
