"""Tests for infrastructure.llm.core.response_saver — coverage."""


from infrastructure.llm.core.response_saver import (
    ResponseMetadata,
    save_response,
    save_streaming_response,
)


def _make_metadata(**overrides):
    defaults = {
        "timestamp": "2025-01-15T12:00:00",
        "model": "llama3",
        "prompt": "What is AI?",
        "prompt_length": 10,
        "response_length": 50,
        "response_tokens_est": 12,
    }
    defaults.update(overrides)
    return ResponseMetadata(**defaults)


class TestResponseMetadata:
    def test_to_dict(self):
        meta = _make_metadata()
        d = meta.to_dict()
        assert d["model"] == "llama3"
        assert d["prompt"] == "What is AI?"
        assert d["streaming"] is False
        assert d["error_occurred"] is False

    def test_to_dict_with_options(self):
        meta = _make_metadata(options={"temperature": 0.7})
        d = meta.to_dict()
        assert d["options"]["temperature"] == 0.7

    def test_streaming_metadata(self):
        meta = _make_metadata(
            streaming=True,
            chunk_count=15,
            streaming_time_seconds=5.2,
        )
        d = meta.to_dict()
        assert d["streaming"] is True
        assert d["chunk_count"] == 15

    def test_partial_response(self):
        meta = _make_metadata(error_occurred=True, partial_response=True)
        d = meta.to_dict()
        assert d["error_occurred"] is True
        assert d["partial_response"] is True


class TestSaveResponse:
    def test_markdown_format(self, tmp_path):
        meta = _make_metadata(generation_time_seconds=1.5)
        path = save_response("AI is awesome.", tmp_path / "resp.md", meta, format="markdown")
        assert path.exists()
        content = path.read_text()
        assert "# LLM Response" in content
        assert "AI is awesome." in content
        assert "1.50s" in content

    def test_markdown_no_gen_time(self, tmp_path):
        meta = _make_metadata()
        path = save_response("Response text", tmp_path / "resp.md", meta, format="markdown")
        content = path.read_text()
        assert "N/A" in content

    def test_json_format(self, tmp_path):
        meta = _make_metadata()
        path = save_response("AI response", tmp_path / "resp.json", meta, format="json")
        assert path.exists()
        import json
        data = json.loads(path.read_text())
        assert data["response"] == "AI response"
        assert data["metadata"]["model"] == "llama3"

    def test_txt_format(self, tmp_path):
        meta = _make_metadata()
        path = save_response("Plain text response", tmp_path / "resp.txt", meta, format="txt")
        assert path.exists()
        content = path.read_text()
        assert "Plain text response" in content
        assert "LLM Response" in content

    def test_auto_extension_markdown(self, tmp_path):
        meta = _make_metadata()
        path = save_response("text", tmp_path / "resp", meta, format="markdown")
        assert path.suffix == ".md"

    def test_auto_extension_json(self, tmp_path):
        meta = _make_metadata()
        path = save_response("text", tmp_path / "resp", meta, format="json")
        assert path.suffix == ".json"

    def test_auto_extension_txt(self, tmp_path):
        meta = _make_metadata()
        path = save_response("text", tmp_path / "resp", meta, format="txt")
        assert path.suffix == ".txt"

    def test_creates_parent_dirs(self, tmp_path):
        meta = _make_metadata()
        path = save_response("text", tmp_path / "deep" / "dir" / "resp.md", meta)
        assert path.exists()


class TestSaveStreamingResponse:
    def test_streaming_with_metadata(self, tmp_path):
        meta = _make_metadata(
            streaming=True,
            chunk_count=20,
            streaming_time_seconds=3.5,
        )
        path = save_streaming_response("Streamed text", tmp_path / "stream.md", meta)
        assert path.exists()
        content = path.read_text()
        assert "Streamed text" in content

    def test_streaming_partial(self, tmp_path):
        meta = _make_metadata(
            streaming=True,
            chunk_count=5,
            streaming_time_seconds=1.0,
            partial_response=True,
            error_occurred=True,
        )
        path = save_streaming_response("Partial", tmp_path / "partial.md", meta)
        assert path.exists()

    def test_non_streaming_metadata(self, tmp_path):
        meta = _make_metadata(streaming=False)
        path = save_streaming_response("Non-stream", tmp_path / "out.md", meta)
        assert path.exists()

    def test_json_format_streaming(self, tmp_path):
        meta = _make_metadata(streaming=True, chunk_count=10, streaming_time_seconds=2.0)
        path = save_streaming_response("json data", tmp_path / "out.json", meta, format="json")
        assert path.suffix == ".json"
