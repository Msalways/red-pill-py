"""Configuration builder for Redpill SDK."""

from dataclasses import dataclass
from typing import Any, Callable


LLM = Any


def call_llm(llm: LLM, messages: list[dict], options: dict | None = None) -> dict:
    """Call LLM - forwards directly to user's function.
    
    The user's function is responsible for:
    - Selecting the model
    - Setting temperature, max_tokens
    - Making the actual API call
    
    Options passed:
    - temperature: float
    - max_tokens: int
    """
    opts = options or {}
    
    if callable(llm):
        return llm(messages, opts)
    
    raise ValueError(
        "LLM must be a callable function. Use .llm(lambda messages, options: your_llm_call(messages, options))"
    )


@dataclass
class RedpillConfig:
    """Configuration for Redpill SDK."""

    temperature: float = 0.1
    max_tokens: int = 4000
    sample_size: int = 100
    debug_mode: bool = False
    max_retries: int = 3
    llm: Callable | None = None


class RedpillConfigBuilder:
    """Fluent builder for Redpill configuration."""

    def __init__(self) -> None:
        self._config = RedpillConfig()

    def temperature(self, temperature: float) -> "RedpillConfigBuilder":
        self._config.temperature = temperature
        return self

    def max_tokens(self, max_tokens: int) -> "RedpillConfigBuilder":
        self._config.max_tokens = max_tokens
        return self

    def sample_size(self, sample_size: int) -> "RedpillConfigBuilder":
        self._config.sample_size = sample_size
        return self

    def debug_mode(self, debug_mode: bool) -> "RedpillConfigBuilder":
        self._config.debug_mode = debug_mode
        return self

    def llm(self, llm_fn: Callable) -> "RedpillConfigBuilder":
        """Set your LLM function.

        The function receives (messages, options) and must return {"content": str}.
        You have full control over model, temperature, max_tokens, etc.

        Example with OpenAI via OpenRouter:
            from openai import OpenAI
            
            def llm(messages, options):
                client = OpenAI(
                    api_key="your-key",
                    base_url="https://openrouter.ai/api/v1"
                )
                response = client.chat.completions.create(
                    model="openai/gpt-4o-mini",
                    messages=messages,
                    temperature=options.get("temperature", 0.7),
                    max_tokens=options.get("max_tokens", 4000),
                )
                return {"content": response.choices[0].message.content}
            
            rp = Redpill().llm(llm).build()

        Example with Anthropic:
            from anthropic import Anthropic
            
            def llm(messages, options):
                client = Anthropic(api_key="your-key")
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    messages=messages,
                    temperature=options.get("temperature", 0.7),
                    max_tokens=options.get("max_tokens", 4000),
                )
                return {"content": response.content[0].text}
            
            rp = Redpill().llm(llm).build()

        Example with Ollama (local):
            import requests
            
            def llm(messages, options):
                response = requests.post(
                    "http://localhost:11434/api/chat",
                    json={
                        "model": "llama3.1",
                        "messages": messages,
                        "options": {
                            "temperature": options.get("temperature", 0.1),
                        }
                    }
                )
                return {"content": response.json()["message"]["content"]}
            
            rp = Redpill().llm(llm).build()
        """
        self._config.llm = llm_fn
        return self

    def build(self) -> RedpillConfig:
        return self._config


def create_client(**kwargs: Any) -> RedpillConfigBuilder:
    """Create a new Redpill configuration builder."""
    builder = RedpillConfigBuilder()
    for key, value in kwargs.items():
        if hasattr(builder, key):
            getattr(builder, key)(value)
    return builder
