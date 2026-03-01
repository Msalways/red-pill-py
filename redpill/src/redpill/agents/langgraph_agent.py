"""LangGraph agent workflow for spec generation with validation."""

from typing import Any, TypedDict

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from redpill.agents.intent_spec_agent import IntentSpecAgent
from redpill.agents.validator import ValidatorAgent
from redpill.config.builder import RedpillConfig
from redpill.processor.processor import DataProcessor
from redpill.providers import LLMProvider


class AgentState(TypedDict):
    """State flowing through the agent graph."""

    data: Any
    prompt: str
    processed_data: dict[str, Any]
    spec: Any
    params: Any
    profile: dict[str, Any]
    validation_result: Any
    error: str | None
    retry_count: int
    max_retries: int
    is_valid: bool


def create_spec_agent_graph(
    provider: LLMProvider,
    config: RedpillConfig,
    processor: DataProcessor,
) -> StateGraph:
    """Create a LangGraph workflow for spec generation.

    Args:
        provider: LLM provider instance
        config: Configuration
        processor: Data processor instance

    Returns:
        Compiled LangGraph workflow
    """

    intent_agent = IntentSpecAgent(provider, config)
    validator_agent = ValidatorAgent(provider, config)

    def process_data_node(state: AgentState) -> AgentState:
        """Process raw data into flat data + profile."""
        processed = processor.process(
            state["data"], sample_size=config.sample_size
        )
        state["processed_data"] = processed["flat_data"]
        state["profile"] = processed["profile"]
        return state

    def generate_spec_node(state: AgentState) -> AgentState:
        """Generate chart spec using LLM."""
        try:
            result = intent_agent.run(
                prompt=state["prompt"],
                profile=state["profile"],
                sample_data=state["processed_data"],
            )
            state["spec"] = result["spec"]
            state["params"] = result["params"]
            state["error"] = None
        except Exception as e:
            state["error"] = str(e)
            state["spec"] = None
        return state

    def validate_spec_node(state: AgentState) -> AgentState:
        """Validate the generated spec."""
        if state["spec"] is None:
            state["is_valid"] = False
            state["validation_result"] = {"is_valid": False, "error": "No spec generated"}
            return state

        try:
            validation_result = validator_agent.run(
                spec=state["spec"],
                profile=state["profile"],
            )
            state["validation_result"] = {
                "is_valid": validation_result.is_valid,
                "error": validation_result.error,
                "warnings": validation_result.warnings,
            }
            state["is_valid"] = validation_result.is_valid
        except Exception as e:
            state["is_valid"] = False
            state["validation_result"] = {"is_valid": False, "error": str(e)}
        return state

    def check_validation_edge(state: AgentState) -> str:
        """Check if validation passed or retry needed."""
        if state.get("is_valid", False):
            return "valid"

        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", config.max_retries)

        if retry_count < max_retries:
            state["retry_count"] = retry_count + 1
            return "retry"
        else:
            return "failed"

    def retry_spec_node(state: AgentState) -> AgentState:
        """Retry spec generation with error context."""
        error_msg = state.get("validation_result", {}).get("error", "")
        enhanced_prompt = (
            f"{state['prompt']}\n\nPrevious attempt failed with error: {error_msg}\n"
            "Please correct the spec and try again."
        )
        state["prompt"] = enhanced_prompt
        return state

    # Build the graph
    workflow = StateGraph(AgentState)

    workflow.add_node("process_data", process_data_node)
    workflow.add_node("generate_spec", generate_spec_node)
    workflow.add_node("validate_spec", validate_spec_node)
    workflow.add_node("retry_spec", retry_spec_node)

    workflow.set_entry_point("process_data")
    workflow.add_edge("process_data", "generate_spec")
    workflow.add_edge("generate_spec", "validate_spec")

    workflow.add_conditional_edges(
        "validate_spec",
        check_validation_edge,
        {
            "valid": END,
            "retry": "retry_spec",
            "failed": END,
        },
    )

    workflow.add_edge("retry_spec", "generate_spec")

    return workflow.compile()


class LangGraphAgent:
    """LangGraph-based agent for spec generation with built-in validation."""

    def __init__(
        self,
        provider: LLMProvider,
        config: RedpillConfig,
        processor: DataProcessor,
    ) -> None:
        self.provider = provider
        self.config = config
        self.processor = processor
        self.graph = create_spec_agent_graph(provider, config, processor)

    def run(
        self,
        data: Any,
        prompt: str,
    ) -> dict[str, Any]:
        """Run the agent to generate and validate a spec.

        Args:
            data: Raw JSON data
            prompt: User's natural language prompt

        Returns:
            Dictionary with spec, profile, params, and validation result
        """
        initial_state: AgentState = {
            "data": data,
            "prompt": prompt,
            "processed_data": {},
            "spec": None,
            "params": None,
            "profile": {},
            "validation_result": None,
            "error": None,
            "retry_count": 0,
            "max_retries": self.config.max_retries,
            "is_valid": False,
        }

        result = self.graph.invoke(initial_state)

        if result.get("error") and not result.get("spec"):
            raise RuntimeError(f"Failed to generate spec: {result['error']}")

        if not result.get("is_valid"):
            error = result.get("validation_result", {}).get("error", "Validation failed")
            raise ValueError(f"Spec validation failed: {error}")

        return {
            "spec": result["spec"],
            "profile": result["profile"],
            "params": result["params"],
            "validation_result": result["validation_result"],
            "retry_count": result.get("retry_count", 0),
        }
