import pytest
import requests
from unittest.mock import MagicMock, patch
from infrastructure.llm.core import LLMClient
from infrastructure.core.exceptions import LLMConnectionError

def test_query_success(mock_client, mock_requests_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"message": {"content": "Response"}}
    mock_requests_post.return_value = mock_response

    response = mock_client.query("Hello")
    assert response == "Response"
    assert len(mock_client.context.messages) == 2 # User + Assistant

def test_query_connection_error(mock_client, mock_requests_post):
    mock_requests_post.side_effect = requests.exceptions.RequestException("Connection refused")
    
    with pytest.raises(LLMConnectionError):
        mock_client.query("Hello")

def test_fallback_models(mock_client, mock_requests_post):
    # Fail first model, succeed second
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"message": {"content": "Fallback Response"}}
    
    mock_requests_post.side_effect = [
        requests.exceptions.RequestException("Primary failed"),
        mock_response
    ]
    
    response = mock_client.query("Hello")
    assert response == "Fallback Response"
    assert mock_requests_post.call_count == 2

def test_apply_template(mock_client, mock_requests_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"message": {"content": "Summary"}}
    mock_requests_post.return_value = mock_response
    
    response = mock_client.apply_template("summarize_abstract", text="Abstract")
    assert response == "Summary"
    
    # Check prompt contains template text
    call_args = mock_requests_post.call_args
    payload = call_args[1]['json']
    last_msg = payload['messages'][-1]['content']
    assert "Please summarize" in last_msg
    assert "Abstract" in last_msg

def test_stream_query(mock_client, mock_requests_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    # Mock streaming lines
    lines = [
        b'{"message": {"content": "Part 1"}}',
        b'{"message": {"content": "Part 2"}}'
    ]
    mock_response.iter_lines.return_value = lines
    # Context manager mock
    mock_requests_post.return_value.__enter__.return_value = mock_response
    
    chunks = list(mock_client.stream_query("Hello"))
    assert chunks == ["Part 1", "Part 2"]
    assert mock_client.context.messages[-1].content == "Part 1Part 2"

def test_query_short_mode(mock_client, mock_requests_post):
    """Test short response mode (< 150 tokens)."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"message": {"content": "Brief answer"}}
    mock_requests_post.return_value = mock_response
    
    result = mock_client.query_short("What is X?")
    assert result == "Brief answer"
    
    # Check that short mode instruction was added
    call_args = mock_requests_post.call_args
    payload = call_args[1]['json']
    last_msg = payload['messages'][-1]['content']
    assert "concise" in last_msg.lower()

def test_query_long_mode(mock_client, mock_requests_post):
    """Test long response mode (> 500 tokens)."""
    mock_response = MagicMock()
    long_response = "Detailed answer " * 50
    mock_response.json.return_value = {"message": {"content": long_response}}
    mock_requests_post.return_value = mock_response
    
    result = mock_client.query_long("Explain in detail...")
    assert "answer" in result.lower()
    
    # Check that long mode instruction was added
    call_args = mock_requests_post.call_args
    payload = call_args[1]['json']
    last_msg = payload['messages'][-1]['content']
    assert "comprehensive" in last_msg.lower()

def test_query_structured_mode(mock_client, mock_requests_post):
    """Test structured JSON response mode."""
    test_json = '{"summary": "test", "items": [1, 2, 3]}'
    mock_response = MagicMock()
    mock_response.json.return_value = {"message": {"content": test_json}}
    mock_requests_post.return_value = mock_response
    
    schema = {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "items": {"type": "array"}
        }
    }
    result = mock_client.query_structured("Extract data", schema=schema)
    assert isinstance(result, dict)
    assert result["summary"] == "test"
    assert result["items"] == [1, 2, 3]

def test_query_structured_markdown_json(mock_client, mock_requests_post):
    """Test structured response with markdown-wrapped JSON."""
    markdown_json = "```json\n{\"key\": \"value\"}\n```"
    mock_response = MagicMock()
    mock_response.json.return_value = {"message": {"content": markdown_json}}
    mock_requests_post.return_value = mock_response
    
    result = mock_client.query_structured("Get data")
    assert isinstance(result, dict)
    assert result["key"] == "value"

def test_stream_short_mode(mock_client, mock_requests_post):
    """Test streaming short response mode."""
    mock_response = MagicMock()
    lines = [
        b'{"message": {"content": "Part "}}',
        b'{"message": {"content": "1"}}'
    ]
    mock_response.iter_lines.return_value = lines
    mock_requests_post.return_value.__enter__.return_value = mock_response
    
    chunks = list(mock_client.stream_short("What?"))
    assert len(chunks) == 2

def test_stream_long_mode(mock_client, mock_requests_post):
    """Test streaming long response mode."""
    mock_response = MagicMock()
    lines = [
        b'{"message": {"content": "Detailed "}}',
        b'{"message": {"content": "answer"}}'
    ]
    mock_response.iter_lines.return_value = lines
    mock_requests_post.return_value.__enter__.return_value = mock_response
    
    chunks = list(mock_client.stream_long("Explain"))
    assert len(chunks) == 2

def test_get_available_models(mock_client, mock_requests_post):
    """Test fetching available models from Ollama."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "models": [
            {"name": "llama3:latest"},
            {"name": "mistral:latest"},
            {"name": "llama3:7b"}
        ]
    }
    
    with patch('requests.get', return_value=mock_response):
        models = mock_client.get_available_models()
        assert len(models) >= 2  # Deduplicated

def test_check_connection_success(mock_client, mock_requests_post):
    """Test successful connection check."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    
    with patch('requests.get', return_value=mock_response):
        result = mock_client.check_connection()
        assert result is True

def test_check_connection_failure():
    """Test failed connection check."""
    client = LLMClient()
    with patch('infrastructure.llm.core.requests.get', side_effect=requests.exceptions.RequestException("Connection error")):
        result = client.check_connection()
        assert result is False

