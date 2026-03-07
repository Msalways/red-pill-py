"""Intent Parser + Spec Generator agent."""

import json
import sys
import time
from typing import Any

from redpillx.config.builder import RedpillConfig, call_llm
from redpillx.prompts.intent_spec import (
    INTENT_SPEC_SYSTEM_PROMPT,
    build_intent_spec_prompt,
)
from redpillx.spec.schema import ChartSpec, RuntimeParams


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
        """Generate chart spec from prompt and data profile."""
        if not prompt or not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")
        if not profile:
            raise ValueError("profile must not be empty — call DataProcessor.process() first")
        if not isinstance(sample_data, list):
            raise TypeError("sample_data must be a list of dicts")

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
                if getattr(self.config, 'debug_mode', False):
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
                error_str = str(e).lower()
                is_rate_limit = any(k in error_str for k in ("429", "rate limit", "too many requests", "quota"))
                is_last_attempt = attempt == self.max_retries - 1

                if is_last_attempt:
                    raise RuntimeError(
                        f"Failed to generate spec after {self.max_retries} attempts: {type(e).__name__}: {e}"
                    ) from e

                # Exponential backoff: 1s, 2s, 4s…
                backoff = 2 ** attempt
                if is_rate_limit:
                    backoff = max(backoff, 5)  # rate-limit: wait at least 5s
                    if getattr(self.config, 'debug_mode', False):
                        print(f"[DEBUG] Rate limit hit, retrying in {backoff}s (attempt {attempt + 1}/{self.max_retries})", file=sys.stderr)
                time.sleep(backoff)
                continue

        raise RuntimeError("Failed to generate spec: max retries exceeded - LLM may be returning invalid responses")

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
