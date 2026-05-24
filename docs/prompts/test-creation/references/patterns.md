# Test patterns (no mocks)

## HTTP

```python
def test_api(ollama_test_server):  # or pytest-httpserver fixture pattern
    config = OllamaClientConfig(base_url=ollama_test_server.url_for("/"))
    client = LLMClient(config)
    response = client.query("test")
    assert "response" in response.lower()
```

## CLI

```python
import subprocess

def test_cli(tmp_path):
    result = subprocess.run(
        ["uv", "run", "python", "-m", "infrastructure.validation.cli", "markdown", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode in (0, 1)  # document expected
```

## Files

```python
def test_roundtrip(tmp_path):
    p = tmp_path / "data.csv"
    p.write_text("1,2\n")
    assert process(p) is not None
```

## PDF (reportlab)

Create minimal PDF bytes; run real extractor/validator on disk file.

## Forbidden

- `unittest.mock.patch` on code under test
- Asserting on MagicMock call counts
