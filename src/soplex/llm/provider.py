"""
Multi-provider LLM system for soplex.
Supports OpenAI, Anthropic, Gemini, Ollama, LiteLLM, and custom endpoints.
Uses OpenAI SDK as universal client where possible for consistency.
"""
import time
import os
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from ..config import SoplexConfig, get_config, PRICING


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""
    content: str
    usage: Dict[str, int]  # prompt_tokens, completion_tokens, total_tokens
    cost: float  # USD cost for this request
    model: str
    provider: str
    latency_ms: float

    # Optional fields
    finish_reason: Optional[str] = None
    system_fingerprint: Optional[str] = None


class LLMProvider:
    """
    Universal LLM provider that supports multiple backends.
    Uses OpenAI SDK as the primary interface for most providers.
    """

    def __init__(self, config: Optional[SoplexConfig] = None):
        """Initialize provider with configuration."""
        self.config = config or get_config()
        self.provider_name = self.config["provider"]
        self.model = self.config["model"]

        # Initialize the appropriate client
        self._client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the appropriate client based on provider."""
        if self.provider_name == "openai":
            self._init_openai()
        elif self.provider_name == "anthropic":
            self._init_anthropic()
        elif self.provider_name == "gemini":
            self._init_gemini()
        elif self.provider_name == "ollama":
            self._init_ollama()
        elif self.provider_name == "litellm":
            self._init_litellm()
        elif self.provider_name == "custom":
            self._init_custom()
        else:
            raise ValueError(f"Unsupported provider: {self.provider_name}")

    def _init_openai(self):
        """Initialize OpenAI client."""
        try:
            import openai
            api_key = self.config.get_api_key("openai")
            if not api_key:
                raise ValueError("OpenAI API key not found in environment")

            self._client = openai.OpenAI(api_key=api_key)

        except ImportError:
            raise ImportError("OpenAI library not installed. Run: pip install openai")

    def _init_anthropic(self):
        """Initialize Anthropic client."""
        try:
            import anthropic
        except ImportError:
            raise ImportError("Anthropic library not installed. Run: pip install soplex-ai[anthropic]")

        api_key = self.config.get_api_key("anthropic")
        if not api_key:
            raise ValueError("Anthropic API key not found in environment")

        self._client = anthropic.Anthropic(api_key=api_key)

    def _init_gemini(self):
        """Initialize Gemini via OpenAI-compatible interface."""
        try:
            import openai
            api_key = self.config.get_api_key("gemini")
            if not api_key:
                raise ValueError("Gemini API key not found in environment")

            base_url = self.config.get_base_url("gemini")
            self._client = openai.OpenAI(
                api_key=api_key,
                base_url=base_url
            )

        except ImportError:
            raise ImportError("OpenAI library required for Gemini. Run: pip install openai")

    def _init_ollama(self):
        """Initialize Ollama via OpenAI-compatible interface."""
        try:
            import openai
            base_url = self.config.get_base_url("ollama")

            # Ollama doesn't require an API key, but OpenAI client expects one
            self._client = openai.OpenAI(
                api_key="ollama",  # Dummy key
                base_url=base_url
            )

        except ImportError:
            raise ImportError("OpenAI library required for Ollama. Run: pip install openai")

    def _init_litellm(self):
        """Initialize LiteLLM client."""
        try:
            import litellm
        except ImportError:
            raise ImportError("LiteLLM library not installed. Run: pip install soplex-ai[litellm]")

        self._client = litellm

        # Set up API keys for LiteLLM
        # LiteLLM will read from environment variables automatically

    def _init_custom(self):
        """Initialize custom OpenAI-compatible endpoint."""
        try:
            import openai
            api_key = self.config.get_api_key("custom")
            base_url = self.config.get_base_url("custom")

            if not base_url:
                raise ValueError("Custom provider requires base_url to be specified")

            self._client = openai.OpenAI(
                api_key=api_key or "custom",
                base_url=base_url
            )

        except ImportError:
            raise ImportError("OpenAI library required for custom endpoint. Run: pip install openai")

    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response using the configured LLM provider.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            model: Override default model
            **kwargs: Additional provider-specific parameters

        Returns:
            Standardized LLMResponse
        """
        # Use provided parameters or fall back to config
        temperature = temperature or self.config["temperature"]
        max_tokens = max_tokens or self.config["max_tokens"]
        model = model or self.model

        start_time = time.time()

        try:
            if self.provider_name == "anthropic":
                response = self._generate_anthropic(messages, temperature, max_tokens, model, **kwargs)
            elif self.provider_name == "litellm":
                response = self._generate_litellm(messages, temperature, max_tokens, model, **kwargs)
            else:
                # Use OpenAI-compatible interface for openai, gemini, ollama, custom
                response = self._generate_openai_compatible(messages, temperature, max_tokens, model, **kwargs)

            latency_ms = (time.time() - start_time) * 1000
            response.latency_ms = latency_ms

            return response

        except Exception as e:
            raise RuntimeError(f"LLM generation failed ({self.provider_name}): {e}")

    def _generate_openai_compatible(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        model: str,
        **kwargs
    ) -> LLMResponse:
        """Generate using OpenAI-compatible interface."""
        response = self._client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

        usage = {
            "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
            "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            "total_tokens": response.usage.total_tokens if response.usage else 0,
        }

        cost = self._calculate_cost(model, usage)

        return LLMResponse(
            content=response.choices[0].message.content,
            usage=usage,
            cost=cost,
            model=model,
            provider=self.provider_name,
            latency_ms=0,  # Will be set by caller
            finish_reason=response.choices[0].finish_reason,
            system_fingerprint=getattr(response, 'system_fingerprint', None),
        )

    def _generate_anthropic(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        model: str,
        **kwargs
    ) -> LLMResponse:
        """Generate using Anthropic's native interface."""
        # Convert OpenAI-style messages to Anthropic format
        system_message = ""
        anthropic_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        response = self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_message,
            messages=anthropic_messages,
            **kwargs
        )

        usage = {
            "prompt_tokens": response.usage.input_tokens,
            "completion_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
        }

        cost = self._calculate_cost(model, usage)

        return LLMResponse(
            content=response.content[0].text,
            usage=usage,
            cost=cost,
            model=model,
            provider="anthropic",
            latency_ms=0,  # Will be set by caller
            finish_reason=response.stop_reason,
        )

    def _generate_litellm(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        model: str,
        **kwargs
    ) -> LLMResponse:
        """Generate using LiteLLM."""
        response = self._client.completion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

        usage = {
            "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
            "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            "total_tokens": response.usage.total_tokens if response.usage else 0,
        }

        cost = self._calculate_cost(model, usage)

        return LLMResponse(
            content=response.choices[0].message.content,
            usage=usage,
            cost=cost,
            model=model,
            provider="litellm",
            latency_ms=0,  # Will be set by caller
            finish_reason=response.choices[0].finish_reason,
        )

    def _calculate_cost(self, model: str, usage: Dict[str, int]) -> float:
        """Calculate cost for the request based on token usage."""
        pricing = PRICING.get(model, {"input": 0.0, "output": 0.0})

        # For Ollama and unknown models, cost is $0
        if self.provider_name == "ollama" or all(price == 0.0 for price in pricing.values()):
            return 0.0

        input_cost = (usage["prompt_tokens"] / 1_000_000) * pricing["input"]
        output_cost = (usage["completion_tokens"] / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    def build_system_prompt(self, step_action: str, context: Dict[str, Any]) -> str:
        """
        Build a focused system prompt for a specific step.

        Args:
            step_action: The action for this step
            context: Relevant context from previous steps

        Returns:
            System prompt string
        """
        base_prompt = f"""You are an AI assistant helping execute a Standard Operating Procedure (SOP).

Current Step: {step_action}

Context from previous steps:
"""

        # Add relevant context
        if context.get("conversation_history"):
            base_prompt += f"Previous conversation: {context['conversation_history'][-3:]}\n"

        if context.get("data"):
            base_prompt += f"Available data: {context['data']}\n"

        if context.get("tools_used"):
            base_prompt += f"Tools used: {context['tools_used']}\n"

        base_prompt += """
Instructions:
1. Follow the current step exactly as specified
2. Be concise and professional
3. Only perform the action described in the current step
4. If you need specific information, ask for it clearly
5. Do not make assumptions about data not provided

Respond with only what is needed for this specific step."""

        return base_prompt

    def is_available(self) -> bool:
        """Check if the provider is properly configured and available."""
        try:
            # Test with a minimal request
            test_messages = [{"role": "user", "content": "Hi"}]
            response = self.generate(test_messages, max_tokens=1)
            return True
        except Exception:
            return False

    def get_supported_models(self) -> List[str]:
        """Get list of supported models for this provider."""
        model_lists = {
            "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano"],
            "anthropic": ["claude-opus-4-20250514", "claude-sonnet-4-20250514", "claude-haiku-4-5-20251001"],
            "gemini": ["gemini-2.0-flash", "gemini-2.5-pro", "gemini-2.5-flash"],
            "ollama": ["llama3.1:8b", "llama3.1:70b", "codellama:7b", "codellama:13b", "mistral:7b"],
            "litellm": ["Any model supported by LiteLLM"],
            "custom": ["Depends on endpoint"],
        }

        return model_lists.get(self.provider_name, [self.model])


# Convenience functions for common operations

def create_provider(provider: str, model: str, **config_overrides) -> LLMProvider:
    """Create an LLM provider with specific settings."""
    config_overrides.update({"provider": provider, "model": model})
    config = get_config(**config_overrides)
    return LLMProvider(config)


def quick_generate(prompt: str, provider: str = "openai", model: str = "gpt-4o-mini") -> str:
    """Quick generation for simple use cases."""
    llm = create_provider(provider, model)
    messages = [{"role": "user", "content": prompt}]
    response = llm.generate(messages)
    return response.content


def check_provider(provider: str) -> Dict[str, Any]:
    """Check a provider and return status information."""
    try:
        llm = create_provider(provider, "default")
        is_available = llm.is_available()
        models = llm.get_supported_models()

        return {
            "provider": provider,
            "available": is_available,
            "models": models,
            "error": None
        }
    except Exception as e:
        return {
            "provider": provider,
            "available": False,
            "models": [],
            "error": str(e)
        }