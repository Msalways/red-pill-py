"""Intent Parser + Spec Generator agent."""

import json
import sys
from typing import Any

from redpill.config.builder import RedpillConfig, call_llm
from redpill.prompts.intent_spec import (
    INTENT_SPEC_SYSTEM_PROMPT,
    build_intent_spec_prompt,
)
from redpill.spec.schema import ChartSpec, RuntimeParams


class IntentSpecAgent:
    """Agent that parses user intent and generates chart specification."""

    def __init__(self, config: RedpillConfig) -> None:
        self.config = config
        self.max_retries = 3

    def run(
        self,
        prompt: str,
        profile: dict[str, Any],
        sample_data: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Generate chart spec from prompt and data profile.

        Args:
            prompt: User's natural language prompt
            profile: Data profile from processor
            sample_data: Sample flattened data

        Returns:
            Dictionary with 'spec' (ChartSpec) and 'params' (RuntimeParams)
        """
        user_prompt = build_intent_spec_prompt(
            prompt=prompt,
            profile=profile,
            sample_data=sample_data,
            sample_size=self.config.sample_size,
        )

        messages = [
            {"role": "system", "content": INTENT_SPEC_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        for attempt in range(self.max_retries):
            try:
                options = {
                    "temperature": self.config.temperature,
                    "max_tokens": self.config.max_tokens,
                    "model": getattr(self.config, 'model', 'openai/gpt-4o-mini'),
                }
                response = call_llm(self.config.llm, messages, options)
                
                content = response.get("content", "") if isinstance(response, dict) else str(response)
                print(f"[DEBUG] Raw LLM response: {content[:500]}...", file=sys.stderr)
                
                result = self._parse_json_response(content)

                spec_dict = result.get("spec", result)
                params_dict = result.get("params", {})

                spec_dict["params"] = params_dict

                spec = ChartSpec(**spec_dict)
                params = RuntimeParams(**params_dict)

                return {
                    "spec": spec,
                    "params": params,
                }

            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise RuntimeError(
                        f"Failed to generate spec after {self.max_retries} attempts: {e}"
                    ) from e
                continue

        raise RuntimeError("Failed to generate spec: max retries exceeded")

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
