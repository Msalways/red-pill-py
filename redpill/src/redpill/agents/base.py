"""Base agent class for LLM-based agents."""

import json
from abc import ABC, abstractmethod
from typing import Any

from redpill.providers import LLMProvider
from redpill.config.builder import RedpillConfig


class BaseAgent(ABC):
    """Base class for LLM agents."""

    def __init__(self, provider: LLMProvider, config: RedpillConfig) -> None:
        self.provider = provider
        self.config = config
        self.max_retries = config.max_retries

    @abstractmethod
    def run(self, *args: Any, **kwargs: Any) -> Any:
        """Run the agent."""
        pass

    def _parse_json_response(self, response: str) -> dict[str, Any]:
        """Parse JSON from LLM response."""
        response = response.strip()

        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]

        response = response.strip()

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end != 0:
                return json.loads(response[start:end])
            raise ValueError(f"Failed to parse JSON: {e}") from e
