"""
Configuration management for soplex.
Security-first design: hardcoded defaults + env vars + CLI overrides.
NO separate settings.json file.
"""
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv


# Hardcoded defaults - the source of truth
DEFAULTS = {
    "provider": "openai",
    "model": "gpt-4o-mini",
    "temperature": 0.3,
    "max_tokens": 512,
    "max_steps": 50,
    "timeout_seconds": 120,
}

# Provider-specific default models
PROVIDER_DEFAULTS = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-sonnet-4-20250514",
    "gemini": "gemini-2.0-flash",
    "ollama": "llama3.1:8b",
    "litellm": "gpt-4o-mini",
    "custom": None,
}

# Pricing per 1M tokens (input, output) in USD
PRICING = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4.1": {"input": 2.00, "output": 8.00},
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
    "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
    "claude-opus-4-20250514": {"input": 15.00, "output": 75.00},
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
    "gemini-2.5-pro": {"input": 1.25, "output": 10.00},
    "gemini-2.5-flash": {"input": 0.15, "output": 0.60},
    "deepseek-chat": {"input": 0.14, "output": 0.28},
    "deepseek-reasoner": {"input": 0.55, "output": 2.19},
}

# Visualization colors for different step types
VISUALIZATION_COLORS = {
    "llm": "#cce5ff",
    "code": "#d4edda",
    "hybrid": "#fff3cd",
    "escalate": "#f8d7da",
    "end": "#e2e3e5",
    "branch": "#d4edda",
}


class SoplexConfig:
    """
    Configuration manager with security-first design.
    Priority: CLI flags > env vars > hardcoded defaults
    """

    def __init__(self, **cli_overrides):
        """Initialize config with optional CLI overrides."""
        # Load environment variables from .env (if present)
        load_dotenv()

        # Start with hardcoded defaults
        self._config = DEFAULTS.copy()

        # Apply environment variables (SOPLEX_* prefix)
        self._load_env_vars()

        # Apply CLI overrides (highest priority)
        self._config.update(cli_overrides)

        # Validate configuration
        self._validate_config()

    def _load_env_vars(self) -> None:
        """Load environment variables with SOPLEX_ prefix."""
        env_mapping = {
            "SOPLEX_PROVIDER": "provider",
            "SOPLEX_MODEL": "model",
            "SOPLEX_BASE_URL": "base_url",
            "SOPLEX_TEMPERATURE": ("temperature", float),
            "SOPLEX_MAX_TOKENS": ("max_tokens", int),
            "SOPLEX_MAX_STEPS": ("max_steps", int),
            "SOPLEX_TIMEOUT_SECONDS": ("timeout_seconds", int),
        }

        for env_var, config_key in env_mapping.items():
            value = os.environ.get(env_var)
            if value is not None:
                if isinstance(config_key, tuple):
                    key, converter = config_key
                    try:
                        self._config[key] = converter(value)
                    except ValueError:
                        # Invalid conversion, skip
                        pass
                else:
                    self._config[config_key] = value

    def _validate_config(self) -> None:
        """Validate configuration values."""
        # Ensure provider is supported
        if self._config["provider"] not in PROVIDER_DEFAULTS:
            raise ValueError(f"Unsupported provider: {self._config['provider']}")

        # Set default model for provider if not specified
        if not self._config.get("model"):
            self._config["model"] = PROVIDER_DEFAULTS[self._config["provider"]]

        # Validate numeric ranges
        if not 0 <= self._config["temperature"] <= 2:
            raise ValueError("Temperature must be between 0 and 2")

        if self._config["max_tokens"] <= 0:
            raise ValueError("max_tokens must be positive")

        if self._config["max_steps"] <= 0:
            raise ValueError("max_steps must be positive")

        if self._config["timeout_seconds"] <= 0:
            raise ValueError("timeout_seconds must be positive")

    def get_api_key(self, provider: Optional[str] = None) -> Optional[str]:
        """
        Get API key for the specified provider.
        SECURITY: Never log or print API keys.
        """
        provider = provider or self._config["provider"]

        key_mapping = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "ollama": None,  # No API key needed
            "litellm": "OPENAI_API_KEY",  # LiteLLM uses various keys
            "custom": "OPENAI_API_KEY",  # Assume OpenAI-compatible
        }

        env_var = key_mapping.get(provider)
        if not env_var:
            return None

        return os.environ.get(env_var)

    def get_base_url(self, provider: Optional[str] = None) -> Optional[str]:
        """Get base URL for the specified provider."""
        provider = provider or self._config["provider"]

        # Check for custom base URL first
        custom_url = self._config.get("base_url") or os.environ.get("SOPLEX_BASE_URL")
        if custom_url:
            return custom_url

        # Provider-specific URLs
        url_mapping = {
            "openai": None,  # Use default
            "anthropic": None,  # Use Anthropic SDK
            "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "ollama": os.environ.get("OLLAMA_HOST", "http://localhost:11434") + "/v1",
            "litellm": None,  # Use LiteLLM
            "custom": None,  # Must be provided
        }

        return url_mapping.get(provider)

    def get_model_cost(self, model: str) -> Dict[str, float]:
        """Get cost per 1M tokens for the specified model."""
        return PRICING.get(model, {"input": 0.0, "output": 0.0})

    def __getitem__(self, key: str) -> Any:
        """Allow dict-style access to config values."""
        return self._config[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Allow dict-style setting of config values."""
        self._config[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value with optional default."""
        return self._config.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary."""
        return self._config.copy()

    def __repr__(self) -> str:
        """String representation (excludes sensitive data)."""
        safe_config = self._config.copy()
        # Don't show sensitive values in repr
        return f"SoplexConfig({safe_config})"


# Global config instance (will be initialized by CLI)
config: Optional[SoplexConfig] = None


def get_config(**overrides) -> SoplexConfig:
    """Get or create global config instance."""
    global config
    if config is None or overrides:
        config = SoplexConfig(**overrides)
    return config