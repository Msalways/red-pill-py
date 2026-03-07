"""Main Redpill client for chart generation."""

import json
from typing import Any

from redpillx.agents.intent_spec_agent import IntentSpecAgent
from redpillx.config.builder import RedpillConfig, RedpillConfigBuilder
from redpillx.executor.polars_executor import PolarsExecutor
from redpillx.processor.processor import DataProcessor
from redpillx.spec.schema import ChartSpec, ChartDataResult


class Redpill:
    """Main client for the Redpill SDK.

    Usage:
        # Initialize with your LLM function
        def my_llm(messages, options=None):
            from openai import OpenAI
            client = OpenAI(api_key="sk-...")
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=options.get("temperature", 0.7) if options else 0.7,
                max_tokens=options.get("max_tokens", 4000) if options else 4000,
            )
            return {"content": response.choices[0].message.content}

        rp = Redpill().llm(my_llm).build()

        # Generate spec
        result = rp.generate_spec(
            data={"tickets": [...]},
            prompt="show me tickets by status"
        )

        # Execute spec
        chart_data = rp.execute(spec=result.spec, data=data)
    """

    def __init__(self) -> None:
        self._builder = RedpillConfigBuilder()
        self._config: RedpillConfig | None = None
        self._processor: DataProcessor | None = None
        self._executor: PolarsExecutor | None = None
        self._llm_fn: Any = None

    def llm(self, llm_fn: Any) -> "Redpill":
        """Set your LLM function.

        Args:
            llm_fn: A function that takes (messages, options) and returns {"content": str}

        Example:
            def my_llm(messages, options=None):
                from openai import OpenAI
                client = OpenAI(api_key="sk-...")
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    temperature=options.get("temperature", 0.7) if options else 0.7,
                )
                return {"content": response.choices[0].message.content}

            rp = Redpill().llm(my_llm).build()
        """
        self._llm_fn = llm_fn
        return self

    def temperature(self, temperature: float) -> "Redpill":
        """Set temperature for LLM generation."""
        self._builder.temperature(temperature)
        return self

    def max_tokens(self, max_tokens: int) -> "Redpill":
        """Set max tokens for LLM generation."""
        self._builder.max_tokens(max_tokens)
        return self

    def sample_size(self, sample_size: int) -> "Redpill":
        """Set number of rows to sample for LLM analysis."""
        self._builder.sample_size(sample_size)
        return self

    def debug_mode(self, debug_mode: bool) -> "Redpill":
        """Enable or disable debug mode."""
        self._builder.debug_mode(debug_mode)
        return self

    def build(self) -> "Redpill":
        """Build and return the configured client."""
        if self._llm_fn is None:
            raise ValueError(
                "Please provide an LLM function using .llm(your_function). "
                "Example: Redpill().llm(lambda msgs, opts: your_llm_call(msgs, opts)).build()"
            )

        self._config = self._builder.build()
        self._config.llm = self._llm_fn

        self._processor = DataProcessor()
        self._executor = PolarsExecutor()
        self._intent_spec_agent = IntentSpecAgent(self._config)

        return self

    def generate_spec(
        self,
        data: Any,
        prompt: str,
    ) -> "GenerateSpecOutput":
        """Generate a chart specification from data and prompt.

        Args:
            data: Raw JSON data (dict, list, or JSON string)
            prompt: User's natural language prompt for chart

        Returns:
            GenerateSpecOutput with spec

        Example:
            result = rp.generate_spec(
                data={"tickets": [...]},
                prompt="show me tickets by status with priority breakdown"
            )
        """
        if self._config is None or self._intent_spec_agent is None:
            self.build()

        processed = self._processor.process(data, sample_size=self._config.sample_size)
        profile = processed.get("profile", {})
        flat_data = processed.get("flat_data", [])

        spec_result = self._intent_spec_agent.run(
            prompt=prompt,
            profile=profile,
            sample_data=flat_data,
        )

        return GenerateSpecOutput(
            spec=spec_result["spec"],
            profile=profile,
        )

    def execute(
        self,
        spec: ChartSpec | dict,
        data: Any,
    ) -> ChartDataResult:
        """Execute a chart specification on data.

        Args:
            spec: Chart specification (ChartSpec or dict)
            data: Raw JSON data

        Returns:
            ChartDataResult with transformed data

        Example:
            result = rp.execute(spec=spec_dict, data=data)
        """
        if self._executor is None:
            self._executor = PolarsExecutor()

        if isinstance(spec, dict):
            spec = ChartSpec(**spec)

        return self._executor.execute(spec=spec, data=data)


class GenerateSpecOutput:
    """Output from generate_spec method."""

    def __init__(
        self,
        spec: ChartSpec,
        profile: dict[str, Any],
    ) -> None:
        self.spec = spec
        self.profile = profile
