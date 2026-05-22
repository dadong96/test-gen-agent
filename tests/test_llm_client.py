"""Tests for LLM client with mocked API calls."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.core.llm_client import LLMClient


@pytest.fixture
def mock_anthropic():
    """Create a mock Anthropic client."""
    with patch("src.core.llm_client.ANTHROPIC_API_KEY", "sk-ant-test"):
        with patch("src.core.llm_client._make_anthropic_client") as mock_factory:
            mock_client = MagicMock()
            mock_factory.return_value = mock_client

            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Hello from Claude")]
            mock_response.usage.input_tokens = 100
            mock_response.usage.output_tokens = 50
            mock_client.messages.create.return_value = mock_response

            yield mock_client


@pytest.fixture
def mock_openai():
    """Create a mock OpenAI client."""
    with patch("src.core.llm_client.ANTHROPIC_API_KEY", ""):
        with patch("src.core.llm_client.OPENAI_API_KEY", "sk-test"):
            with patch("src.core.llm_client._make_openai_client") as mock_factory:
                mock_client = MagicMock()
                mock_factory.return_value = mock_client

                mock_response = MagicMock()
                mock_response.choices = [MagicMock(message=MagicMock(content="Hello from GPT"))]
                mock_response.usage.prompt_tokens = 80
                mock_response.usage.completion_tokens = 40
                mock_client.chat.completions.create.return_value = mock_response

                yield mock_client


def test_chat_returns_text(mock_anthropic):
    client = LLMClient()
    result = client.chat([{"role": "user", "content": "Hi"}])
    assert result == "Hello from Claude"


def test_chat_tracks_tokens(mock_anthropic):
    client = LLMClient()
    client.chat([{"role": "user", "content": "Hi"}])
    summary = client.token_summary()
    assert summary["input_tokens"] == 100
    assert summary["output_tokens"] == 50
    assert summary["total_calls"] == 1


def test_chat_json_parses_json(mock_anthropic):
    mock_anthropic.messages.create.return_value.content = [
        MagicMock(text='{"key": "value"}')
    ]
    client = LLMClient()
    result = client.chat_json([{"role": "user", "content": "Give me JSON"}])
    assert result == {"key": "value"}


def test_chat_json_strips_markdown_fences(mock_anthropic):
    mock_anthropic.messages.create.return_value.content = [
        MagicMock(text='```json\n{"key": "value"}\n```')
    ]
    client = LLMClient()
    result = client.chat_json([{"role": "user", "content": "Give me JSON"}])
    assert result == {"key": "value"}


def test_openai_fallback(mock_openai):
    client = LLMClient()
    result = client.chat([{"role": "user", "content": "Hi"}])
    assert result == "Hello from GPT"
    assert client.provider == "openai"
