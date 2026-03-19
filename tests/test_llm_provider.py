"""
Tests for LLM provider functionality.
Tests multi-provider support and response handling.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from soplex.llm.provider import LLMProvider, LLMResponse, create_provider, check_provider
from soplex.config import SoplexConfig


class TestLLMProvider:
    """Test LLM provider functionality."""

    def test_llm_response_creation(self):
        """Test LLMResponse dataclass."""
        response = LLMResponse(
            content="Hello world",
            usage={"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
            cost=0.0001,
            model="test-model",
            provider="test",
            latency_ms=100.0
        )

        assert response.content == "Hello world"
        assert response.usage["total_tokens"] == 8
        assert response.cost == 0.0001
        assert response.model == "test-model"
        assert response.provider == "test"
        assert response.latency_ms == 100.0

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'sk-test'})
    def test_openai_provider_init(self):
        """Test OpenAI provider initialization."""
        config = SoplexConfig(provider="openai", model="gpt-4o-mini")

        with patch('openai.OpenAI') as mock_openai:
            provider = LLMProvider(config)
            assert provider.provider_name == "openai"
            assert provider.model == "gpt-4o-mini"
            mock_openai.assert_called_once()

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-test'})
    def test_anthropic_provider_init(self):
        """Test Anthropic provider initialization."""
        config = SoplexConfig(provider="anthropic", model="claude-sonnet-4-20250514")

        with patch('anthropic.Anthropic') as mock_anthropic:
            provider = LLMProvider(config)
            assert provider.provider_name == "anthropic"
            assert provider.model == "claude-sonnet-4-20250514"
            mock_anthropic.assert_called_once()

    @patch.dict('os.environ', {'GEMINI_API_KEY': 'gemini-test'})
    def test_gemini_provider_init(self):
        """Test Gemini provider initialization."""
        config = SoplexConfig(provider="gemini", model="gemini-2.0-flash")

        with patch('openai.OpenAI') as mock_openai:
            provider = LLMProvider(config)
            assert provider.provider_name == "gemini"
            mock_openai.assert_called_once_with(
                api_key='gemini-test',
                base_url='https://generativelanguage.googleapis.com/v1beta/openai/'
            )

    def test_ollama_provider_init(self):
        """Test Ollama provider initialization."""
        config = SoplexConfig(provider="ollama", model="llama3.1:8b")

        with patch('openai.OpenAI') as mock_openai:
            provider = LLMProvider(config)
            assert provider.provider_name == "ollama"
            mock_openai.assert_called_once_with(
                api_key='ollama',
                base_url='http://localhost:11434/v1'
            )

    @patch.dict('os.environ', {
        'SOPLEX_BASE_URL': 'https://custom.api.com',
        'OPENAI_API_KEY': 'custom-test-key'
    })
    def test_custom_provider_init(self):
        """Test custom provider initialization."""
        config = SoplexConfig(provider="custom", model="custom-model")

        with patch('openai.OpenAI') as mock_openai:
            provider = LLMProvider(config)
            assert provider.provider_name == "custom"
            mock_openai.assert_called_once_with(
                api_key='custom-test-key',
                base_url='https://custom.api.com'
            )

    def test_unsupported_provider_error(self):
        """Test error for unsupported provider."""
        config = SoplexConfig(provider="unsupported", model="test")

        with pytest.raises(ValueError, match="Unsupported provider"):
            LLMProvider(config)

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'sk-test'})
    @patch('openai.OpenAI')
    def test_openai_generate(self, mock_openai):
        """Test OpenAI generation."""
        # Set up mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Generated response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        mock_response.system_fingerprint = "test-fingerprint"

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        config = SoplexConfig(provider="openai", model="gpt-4o-mini")
        provider = LLMProvider(config)

        messages = [{"role": "user", "content": "Hello"}]
        response = provider.generate(messages)

        assert isinstance(response, LLMResponse)
        assert response.content == "Generated response"
        assert response.usage["total_tokens"] == 15
        assert response.finish_reason == "stop"
        assert response.provider == "openai"

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-test'})
    @patch('anthropic.Anthropic')
    def test_anthropic_generate(self, mock_anthropic):
        """Test Anthropic generation."""
        # Set up mock response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Claude response"
        mock_response.stop_reason = "end_turn"
        mock_response.usage.input_tokens = 8
        mock_response.usage.output_tokens = 7

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        config = SoplexConfig(provider="anthropic", model="claude-sonnet-4-20250514")
        provider = LLMProvider(config)

        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"}
        ]
        response = provider.generate(messages)

        assert isinstance(response, LLMResponse)
        assert response.content == "Claude response"
        assert response.usage["prompt_tokens"] == 8
        assert response.usage["completion_tokens"] == 7
        assert response.usage["total_tokens"] == 15
        assert response.provider == "anthropic"

    @patch('litellm.completion')
    def test_litellm_generate(self, mock_litellm):
        """Test LiteLLM generation."""
        # Set up mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "LiteLLM response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 12
        mock_response.usage.completion_tokens = 8
        mock_response.usage.total_tokens = 20

        mock_litellm.return_value = mock_response

        config = SoplexConfig(provider="litellm", model="gpt-4o-mini")
        provider = LLMProvider(config)

        messages = [{"role": "user", "content": "Test"}]
        response = provider.generate(messages)

        assert response.content == "LiteLLM response"
        assert response.provider == "litellm"

    def test_cost_calculation(self):
        """Test cost calculation for different models."""
        config = SoplexConfig(provider="openai", model="gpt-4o-mini")
        provider = LLMProvider(config)

        usage = {"prompt_tokens": 1000, "completion_tokens": 500}
        cost = provider._calculate_cost("gpt-4o-mini", usage)

        # gpt-4o-mini: input=0.15, output=0.60 per 1M tokens
        expected_cost = (1000 * 0.15 + 500 * 0.60) / 1_000_000
        assert abs(cost - expected_cost) < 0.000001

    def test_ollama_zero_cost(self):
        """Test that Ollama has zero cost."""
        config = SoplexConfig(provider="ollama", model="llama3.1:8b")
        provider = LLMProvider(config)

        usage = {"prompt_tokens": 1000, "completion_tokens": 500}
        cost = provider._calculate_cost("llama3.1:8b", usage)

        assert cost == 0.0

    def test_build_system_prompt(self):
        """Test system prompt building."""
        config = SoplexConfig(provider="openai")
        provider = LLMProvider(config)

        context = {
            "conversation_history": [{"role": "user", "content": "Hi"}],
            "data": {"key": "value"},
            "tools_used": ["tool1"]
        }

        prompt = provider.build_system_prompt("Test action", context)

        assert "Test action" in prompt
        assert "conversation" in prompt.lower()
        assert "data" in prompt.lower()
        assert "tools" in prompt.lower()

    def test_get_supported_models(self):
        """Test getting supported models list."""
        config = SoplexConfig(provider="openai")
        provider = LLMProvider(config)

        models = provider.get_supported_models()

        assert isinstance(models, list)
        assert "gpt-4o-mini" in models
        assert "gpt-4o" in models

    def test_create_provider_convenience(self):
        """Test convenience function for creating providers."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'sk-test'}):
            with patch('openai.OpenAI'):
                provider = create_provider("openai", "gpt-4o-mini")
                assert provider.provider_name == "openai"
                assert provider.model == "gpt-4o-mini"

    def test_generation_error_handling(self):
        """Test error handling during generation."""
        config = SoplexConfig(provider="openai")

        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            mock_openai.return_value = mock_client

            provider = LLMProvider(config)

            with pytest.raises(RuntimeError, match="LLM generation failed"):
                provider.generate([{"role": "user", "content": "test"}])

    def test_missing_api_key_error(self):
        """Test error when API key is missing."""
        config = SoplexConfig(provider="openai")

        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key not found"):
                LLMProvider(config)

    def test_provider_status_check(self):
        """Test provider availability checking."""
        provider_status = check_provider("openai")

        assert "provider" in provider_status
        assert "available" in provider_status
        assert "models" in provider_status
        assert provider_status["provider"] == "openai"

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'sk-test'})
    @patch('openai.OpenAI')
    def test_parameter_override(self, mock_openai):
        """Test overriding default parameters."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.completion_tokens = 3
        mock_response.usage.total_tokens = 8

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        config = SoplexConfig(provider="openai", temperature=0.3, max_tokens=100)
        provider = LLMProvider(config)

        messages = [{"role": "user", "content": "test"}]
        provider.generate(messages, temperature=0.7, max_tokens=200, model="gpt-4o")

        # Check that overrides were used
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]["temperature"] == 0.7
        assert call_args[1]["max_tokens"] == 200
        assert call_args[1]["model"] == "gpt-4o"